#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tapped-inductor extraction for ADS 2020 Linux.

The default execution path is Keysight ADS 2020 Datalink:

    TI = dl_python("tapped_inductor_ads2020.py", "columnformat", S)

The same file can also process a Touchstone file from a Linux terminal:

    python3 tapped_inductor_ads2020.py --touchstone model.s5p --segments 4

The extraction intentionally follows the single-ended, port-j-shorted
definition requested by the user:

    Ls(i,j) = sign * imag(Zii - Zij*Zji/Zjj) / (2*pi*f)

where sign defaults to -1.
"""

from __future__ import print_function

import argparse
import csv
import itertools
import json
import math
import os
import re
import sys
import tempfile
import traceback

import numpy as np


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(SCRIPT_DIR, "tapped_inductor_config.json")


def load_config(path):
    defaults = {
        "segments": 4,
        "input_kind": "S",
        "reference_impedance_ohm": 50.0,
        "inductance_sign": -1.0,
        "output_unit": "nH",
        "results_directory": "tapped_inductor_results",
        "write_csv": True,
        "write_plots": True,
        "denominator_relative_tolerance": 1.0e-12,
    }
    if path and os.path.isfile(path):
        with open(path, "r") as stream:
            user = json.load(stream)
        defaults.update(user)

    defaults["segments"] = int(defaults["segments"])
    if defaults["segments"] < 1:
        raise ValueError("segments must be at least 1")
    defaults["input_kind"] = str(defaults["input_kind"]).upper()
    if defaults["input_kind"] not in ("S", "Z"):
        raise ValueError("input_kind must be S or Z")
    defaults["reference_impedance_ohm"] = float(
        defaults["reference_impedance_ohm"]
    )
    defaults["inductance_sign"] = float(defaults["inductance_sign"])
    defaults["denominator_relative_tolerance"] = float(
        defaults["denominator_relative_tolerance"]
    )
    return defaults


def unit_scale(unit):
    scales = {
        "H": 1.0,
        "mH": 1.0e3,
        "uH": 1.0e6,
        "nH": 1.0e9,
        "pH": 1.0e12,
    }
    if unit not in scales:
        raise ValueError("output_unit must be one of H, mH, uH, nH, pH")
    return scales[unit]


def s_to_z(s_matrix, z0_ohm):
    """Convert equal-reference-impedance S matrices to Z matrices."""
    s_matrix = np.asarray(s_matrix, dtype=np.complex128)
    if s_matrix.ndim != 3 or s_matrix.shape[1] != s_matrix.shape[2]:
        raise ValueError("S data must have shape (frequency, port, port)")
    ports = s_matrix.shape[1]
    identity = np.eye(ports, dtype=np.complex128)
    result = np.empty_like(s_matrix)
    for index, s_value in enumerate(s_matrix):
        left = identity - s_value
        right = z0_ohm * (identity + s_value)
        try:
            result[index] = np.linalg.solve(left.T, right.T).T
        except np.linalg.LinAlgError:
            result[index] = np.nan + 1j * np.nan
    return result


def path_inductances(freq_hz, z_matrix, sign=-1.0, relative_tolerance=1.0e-12):
    """Return all Ls(i,j) values using the requested single-ended formula."""
    freq_hz = np.asarray(freq_hz, dtype=float).reshape(-1)
    z_matrix = np.asarray(z_matrix, dtype=np.complex128)
    if z_matrix.ndim != 3 or z_matrix.shape[1] != z_matrix.shape[2]:
        raise ValueError("Z data must have shape (frequency, port, port)")
    if z_matrix.shape[0] != freq_hz.size:
        raise ValueError("frequency count does not match matrix sweep length")
    if np.any(freq_hz <= 0.0):
        raise ValueError("all frequency values must be greater than zero")

    points, ports, _ = z_matrix.shape
    omega = 2.0 * np.pi * freq_hz
    path = np.zeros((points, ports, ports), dtype=float)
    path[:] = np.nan
    for port in range(ports):
        path[:, port, port] = 0.0

    reference = np.nanmax(np.abs(z_matrix), axis=(1, 2))
    reference = np.maximum(reference, 1.0)

    for i in range(ports - 1):
        for j in range(i + 1, ports):
            denominator = z_matrix[:, j, j]
            valid = np.abs(denominator) > relative_tolerance * reference
            equivalent_z = np.full(points, np.nan + 1j * np.nan, dtype=np.complex128)
            equivalent_z[valid] = (
                z_matrix[valid, i, i]
                - z_matrix[valid, j, i]
                * z_matrix[valid, i, j]
                / denominator[valid]
            )
            path[:, i, j] = sign * np.imag(equivalent_z) / omega
            path[:, j, i] = path[:, i, j]
    return path


def mutual_from_path(path):
    """Recover segment self/mutual values from all contiguous path values."""
    path = np.asarray(path, dtype=float)
    if path.ndim != 3 or path.shape[1] != path.shape[2]:
        raise ValueError("path array must have shape (frequency, tap, tap)")
    points, ports, _ = path.shape
    segments = ports - 1
    self_l = np.empty((points, segments), dtype=float)
    mutual = np.zeros((points, segments, segments), dtype=float)

    for i in range(segments):
        self_l[:, i] = path[:, i, i + 1]
        mutual[:, i, i] = self_l[:, i]

    for i in range(segments - 1):
        for j in range(i + 1, segments):
            value = 0.5 * (
                path[:, i, j + 1]
                - path[:, i, j]
                - path[:, i + 1, j + 1]
                + path[:, i + 1, j]
            )
            mutual[:, i, j] = value
            mutual[:, j, i] = value
    return self_l, mutual


def extract_inductance(freq_hz, matrix, config):
    """Run S/Z conversion, path extraction, and segment comparisons."""
    freq_hz = np.asarray(freq_hz, dtype=float).reshape(-1)
    matrix = np.asarray(matrix, dtype=np.complex128)
    expected_ports = config["segments"] + 1
    if matrix.ndim != 3 or matrix.shape[1:] != (expected_ports, expected_ports):
        raise ValueError(
            "expected a {0}x{0} matrix for {1} segments, received shape {2}".format(
                expected_ports, config["segments"], matrix.shape
            )
        )

    if config["input_kind"] == "S":
        z_matrix = s_to_z(matrix, config["reference_impedance_ohm"])
    else:
        z_matrix = matrix

    path = path_inductances(
        freq_hz,
        z_matrix,
        sign=config["inductance_sign"],
        relative_tolerance=config["denominator_relative_tolerance"],
    )
    self_l, mutual = mutual_from_path(path)
    segment_l = np.sum(mutual, axis=2)
    total_l = path[:, 0, -1]
    sum_l = np.sum(segment_l, axis=1)
    average_l = total_l / float(config["segments"])
    deviation_l = segment_l - average_l[:, np.newaxis]
    with np.errstate(divide="ignore", invalid="ignore"):
        deviation_pct = 100.0 * deviation_l / average_l[:, np.newaxis]
        sum_error_pct = 100.0 * (sum_l - total_l) / total_l

    return {
        "freq_hz": freq_hz,
        "z": z_matrix,
        "path": path,
        "self": self_l,
        "mutual": mutual,
        "segment": segment_l,
        "total": total_l,
        "sum": sum_l,
        "average": average_l,
        "deviation": deviation_l,
        "deviation_pct": deviation_pct,
        "sum_error": sum_l - total_l,
        "sum_error_pct": sum_error_pct,
    }


def result_table(result, config):
    """Build the numeric matrix returned to ADS and its column labels."""
    scale = unit_scale(config["output_unit"])
    unit = config["output_unit"]
    segments = config["segments"]
    ports = segments + 1

    columns = [
        result["freq_hz"],
        result["total"] * scale,
        result["sum"] * scale,
        result["sum_error"] * scale,
        result["sum_error_pct"],
        result["average"] * scale,
    ]
    labels = [
        "freq_Hz",
        "L_total_{0}".format(unit),
        "L_sum_{0}".format(unit),
        "L_sum_minus_total_{0}".format(unit),
        "L_sum_error_pct",
        "L_average_{0}".format(unit),
    ]

    for i in range(segments):
        columns.append(result["segment"][:, i] * scale)
        labels.append("L{0}_{1}".format(i + 1, unit))
    for i in range(segments):
        columns.append(result["deviation"][:, i] * scale)
        labels.append("L{0}_minus_average_{1}".format(i + 1, unit))
    for i in range(segments):
        columns.append(result["deviation_pct"][:, i])
        labels.append("L{0}_deviation_pct".format(i + 1))
    for i in range(segments):
        columns.append(result["self"][:, i] * scale)
        labels.append("Ls{0}{1}_{2}".format(i + 1, i + 2, unit))

    for i in range(segments - 1):
        for j in range(i + 1, segments):
            columns.append(result["mutual"][:, i, j] * scale)
            labels.append("M{0}{1}_{2}".format(i + 1, j + 1, unit))

    for i in range(ports - 1):
        for j in range(i + 1, ports):
            columns.append(result["path"][:, i, j] * scale)
            labels.append("Ls{0}{1}_{2}".format(i + 1, j + 1, unit))

    return np.column_stack(columns), labels


def ensure_result_directory(config):
    path = config["results_directory"]
    if not os.path.isabs(path):
        path = os.path.join(SCRIPT_DIR, path)
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def write_results(result, config):
    table, labels = result_table(result, config)
    output_dir = ensure_result_directory(config)

    if config.get("write_csv", True):
        csv_path = os.path.join(output_dir, "tapped_inductor_results.csv")
        with open(csv_path, "w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(labels)
            writer.writerows(table)

        map_path = os.path.join(output_dir, "ads_result_columns.txt")
        with open(map_path, "w") as stream:
            for index, label in enumerate(labels):
                stream.write("{0}: {1}\n".format(index, label))

    if config.get("write_plots", True):
        write_plots(result, config, output_dir)

    return table, labels, output_dir


def write_plots(result, config, output_dir):
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return

    scale = unit_scale(config["output_unit"])
    unit = config["output_unit"]
    freq_ghz = result["freq_hz"] / 1.0e9
    segments = config["segments"]

    fig, axes = plt.subplots(3, 1, figsize=(9.0, 10.5), sharex=True)
    for i in range(segments):
        axes[0].plot(
            freq_ghz,
            result["segment"][:, i] * scale,
            label="L{0}".format(i + 1),
        )
    axes[0].plot(
        freq_ghz,
        result["average"] * scale,
        "k--",
        linewidth=1.5,
        label="Ltotal/N",
    )
    axes[0].set_ylabel("Segment inductance ({0})".format(unit))
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(ncol=min(4, segments + 1), fontsize=8)

    axes[1].plot(
        freq_ghz, result["total"] * scale, label="Direct Ltotal", linewidth=2.0
    )
    axes[1].plot(
        freq_ghz,
        result["sum"] * scale,
        "--",
        label="Sum of segment contributions",
    )
    axes[1].set_ylabel("Total inductance ({0})".format(unit))
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(fontsize=8)

    for i in range(segments):
        axes[2].plot(
            freq_ghz,
            result["deviation_pct"][:, i],
            label="L{0}".format(i + 1),
        )
    axes[2].axhline(0.0, color="black", linewidth=0.8)
    axes[2].set_xlabel("Frequency (GHz)")
    axes[2].set_ylabel("Deviation from Ltotal/N (%)")
    axes[2].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "tapped_inductor_summary.png"), dpi=180)
    plt.close(fig)


def _is_contiguous_index(values, expected_ports):
    values = np.real(np.asarray(values))
    if not np.all(np.isfinite(values)):
        return False
    rounded = np.rint(values)
    if not np.allclose(values, rounded, rtol=0.0, atol=1.0e-8):
        return False
    unique = np.unique(rounded.astype(int))
    if unique.size != expected_ports:
        return False
    zero_based = np.arange(expected_ports)
    one_based = np.arange(1, expected_ports + 1)
    return np.array_equal(unique, zero_based) or np.array_equal(unique, one_based)


def _remove_datalink_sentinel_rows(array):
    array = np.asarray(array)
    while array.ndim == 2 and array.shape[0] > 1:
        last = array[-1]
        if np.all(np.isfinite(last)) and np.allclose(last, 0.0):
            array = array[:-1]
        else:
            break
    return array


def parse_datalink_swept_matrix(raw_data, expected_ports):
    """Reconstruct a frequency-swept matrix exported by ADS Datalink.

    ADS 2020 normally exports a swept matrix as a tabular array containing
    frequency, two matrix-index columns, and one complex dependent column.
    A few alternate layouts are accepted to make the script tolerant of
    update-level differences.
    """
    array = np.asarray(raw_data)
    array = np.squeeze(array)

    if array.ndim == 3:
        if array.shape[1:] == (expected_ports, expected_ports):
            raise ValueError(
                "Datalink supplied matrix values without a frequency column; "
                "pass the swept S matrix, not a single-frequency matrix"
            )
        if array.shape[:2] == (expected_ports, expected_ports):
            raise ValueError(
                "Datalink supplied matrix values without a frequency column; "
                "pass the swept S matrix, not a single-frequency matrix"
            )

    if array.ndim != 2:
        raise ValueError(
            "unsupported Datalink array shape {0}; expected a swept matrix".format(
                array.shape
            )
        )

    array = _remove_datalink_sentinel_rows(array)
    rows, cols = array.shape

    # Common ADS Datalink layout: dependency columns + complex dependent value.
    if cols >= 4:
        value_col = cols - 1
        index_candidates = [
            col
            for col in range(value_col)
            if _is_contiguous_index(array[:, col], expected_ports)
        ]
        if len(index_candidates) >= 2:
            row_col, column_col = index_candidates[-2:]
            remaining = [
                col
                for col in range(value_col)
                if col not in (row_col, column_col)
            ]
            if len(remaining) != 1:
                raise ValueError(
                    "only a frequency sweep is supported; extra sweep dependencies "
                    "were found in the Datalink matrix"
                )
            frequency_col = remaining[0]
            freq_values = np.real(array[:, frequency_col]).astype(float)
            if not np.allclose(np.imag(array[:, frequency_col]), 0.0):
                raise ValueError("frequency dependency is unexpectedly complex")

            frequencies = np.unique(freq_values)
            frequencies.sort()
            matrix = np.full(
                (frequencies.size, expected_ports, expected_ports),
                np.nan + 1j * np.nan,
                dtype=np.complex128,
            )
            row_values = np.rint(np.real(array[:, row_col])).astype(int)
            column_values = np.rint(np.real(array[:, column_col])).astype(int)
            if row_values.min() == 1:
                row_values = row_values - 1
            if column_values.min() == 1:
                column_values = column_values - 1

            for row in range(rows):
                f_index = int(np.searchsorted(frequencies, freq_values[row]))
                matrix[f_index, row_values[row], column_values[row]] = array[
                    row, value_col
                ]

            if np.isnan(matrix.real).any() or np.isnan(matrix.imag).any():
                raise ValueError(
                    "Datalink matrix reconstruction is incomplete; verify that the "
                    "whole S matrix was passed to dl_python()"
                )
            return frequencies, matrix

    # Alternate flattened layout: one row per frequency.
    flattened_width = expected_ports * expected_ports
    if cols == flattened_width + 1:
        frequencies = np.real(array[:, 0]).astype(float)
        matrix = array[:, 1:].reshape(
            rows, expected_ports, expected_ports
        ).astype(np.complex128)
        return frequencies, matrix

    raise ValueError(
        "could not identify frequency and matrix indices in Datalink array shape "
        "{0}; see tapped_inductor_error.log".format(array.shape)
    )


def _touchstone_ports_from_path(path):
    match = re.search(r"\.s(\d+)p$", path, flags=re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def read_touchstone(path):
    """Read full-matrix S-parameter Touchstone 1.x or simple 2.0 files."""
    ports = _touchstone_ports_from_path(path)
    frequency_unit = "GHZ"
    data_format = "MA"
    parameter_kind = "S"
    z0 = 50.0
    version_2 = False
    in_network_data = True
    matrix_format = "FULL"
    two_port_order = "21_12"
    numeric_tokens = []

    with open(path, "r") as stream:
        for original_line in stream:
            line = original_line.split("!", 1)[0].strip()
            if not line:
                continue
            upper = line.upper()
            if upper.startswith("#"):
                options = upper[1:].split()
                if len(options) >= 3:
                    frequency_unit, parameter_kind, data_format = options[:3]
                if "R" in options:
                    r_index = options.index("R")
                    if r_index + 1 < len(options):
                        z0 = float(options[r_index + 1])
                continue
            if upper.startswith("["):
                version_2 = True
                in_network_data = False
                if upper.startswith("[NUMBER OF PORTS]"):
                    ports = int(line.split("]", 1)[1].strip())
                elif upper.startswith("[MATRIX FORMAT]"):
                    matrix_format = line.split("]", 1)[1].strip().upper()
                elif upper.startswith("[TWO-PORT DATA ORDER]"):
                    two_port_order = line.split("]", 1)[1].strip().upper()
                elif upper.startswith("[NETWORK DATA]"):
                    in_network_data = True
                elif upper.startswith("[END]"):
                    in_network_data = False
                continue
            if version_2 and not in_network_data:
                continue
            numeric_tokens.extend(line.split())

    if ports is None:
        raise ValueError("could not determine Touchstone port count")
    if parameter_kind != "S":
        raise ValueError("Touchstone input must contain S parameters")
    if matrix_format != "FULL":
        raise ValueError("only full Touchstone matrices are supported")

    units = {
        "HZ": 1.0,
        "KHZ": 1.0e3,
        "MHZ": 1.0e6,
        "GHZ": 1.0e9,
    }
    if frequency_unit not in units:
        raise ValueError("unsupported Touchstone frequency unit: " + frequency_unit)
    values_per_point = 1 + 2 * ports * ports
    if len(numeric_tokens) % values_per_point:
        raise ValueError(
            "Touchstone numeric data length is not compatible with {0} ports".format(
                ports
            )
        )

    raw = np.asarray([float(token) for token in numeric_tokens], dtype=float)
    raw = raw.reshape((-1, values_per_point))
    frequencies = raw[:, 0] * units[frequency_unit]
    pairs = raw[:, 1:].reshape((-1, ports * ports, 2))
    if data_format == "RI":
        complex_values = pairs[:, :, 0] + 1j * pairs[:, :, 1]
    elif data_format == "MA":
        complex_values = pairs[:, :, 0] * np.exp(
            1j * np.deg2rad(pairs[:, :, 1])
        )
    elif data_format == "DB":
        complex_values = 10.0 ** (pairs[:, :, 0] / 20.0) * np.exp(
            1j * np.deg2rad(pairs[:, :, 1])
        )
    else:
        raise ValueError("unsupported Touchstone data format: " + data_format)

    matrix = complex_values.reshape((-1, ports, ports))
    if ports == 2 and two_port_order == "21_12":
        # Version 1 convention: 11, 21, 12, 22.
        ordered = np.empty_like(matrix)
        ordered[:, 0, 0] = complex_values[:, 0]
        ordered[:, 1, 0] = complex_values[:, 1]
        ordered[:, 0, 1] = complex_values[:, 2]
        ordered[:, 1, 1] = complex_values[:, 3]
        matrix = ordered
    return frequencies, matrix, z0


def write_error_log(raw_data, error):
    path = os.path.join(SCRIPT_DIR, "tapped_inductor_error.log")
    with open(path, "w") as stream:
        stream.write("Tapped-inductor ADS 2020 error\n")
        stream.write("Exception: {0}\n".format(error))
        try:
            array = np.asarray(raw_data)
            stream.write("Raw Datalink shape: {0}\n".format(array.shape))
            stream.write("Raw Datalink dtype: {0}\n".format(array.dtype))
            stream.write("First rows:\n{0}\n".format(array[:10]))
        except Exception:
            stream.write("Could not inspect raw Datalink data.\n")
        stream.write("\nTraceback:\n")
        stream.write(traceback.format_exc())
    return path


def run_datalink(config_path):
    import ads

    config = load_config(config_path)
    raw_data, _raw_strings = ads.get()
    try:
        frequencies, matrix = parse_datalink_swept_matrix(
            raw_data, config["segments"] + 1
        )
        result = extract_inductance(frequencies, matrix, config)
        table, _labels, _output_dir = write_results(result, config)
    except Exception as error:
        write_error_log(raw_data, error)
        raise
    ads.send(table)


def _build_path_from_known_model(self_l, mutual):
    self_l = np.asarray(self_l, dtype=float)
    mutual = np.asarray(mutual, dtype=float)
    segments = self_l.size
    matrix = mutual.copy()
    np.fill_diagonal(matrix, self_l)
    path = np.zeros((1, segments + 1, segments + 1), dtype=float)
    for i in range(segments):
        for j in range(i + 1, segments + 1):
            block = matrix[i:j, i:j]
            path[0, i, j] = np.sum(block)
            path[0, j, i] = path[0, i, j]
    return path


def self_test():
    self_l = np.asarray([1.0, 1.1, 0.9, 1.2]) * 1.0e-9
    mutual = np.zeros((4, 4), dtype=float)
    known = {
        (0, 1): 0.08e-9,
        (0, 2): 0.04e-9,
        (0, 3): 0.02e-9,
        (1, 2): 0.07e-9,
        (1, 3): 0.03e-9,
        (2, 3): 0.06e-9,
    }
    for (i, j), value in known.items():
        mutual[i, j] = value
        mutual[j, i] = value
    path = _build_path_from_known_model(self_l, mutual)
    recovered_self, recovered_matrix = mutual_from_path(path)
    if not np.allclose(recovered_self[0], self_l):
        raise AssertionError("self-inductance recovery failed")
    if not np.allclose(recovered_matrix[0], mutual + np.diag(self_l)):
        raise AssertionError("mutual-inductance recovery failed")
    expected_m24 = mutual[1, 3]
    recovered_m24 = 0.5 * (
        path[0, 1, 4]
        - path[0, 1, 3]
        - path[0, 2, 4]
        + path[0, 2, 3]
    )
    if not np.isclose(recovered_m24, expected_m24):
        raise AssertionError("M24 formula check failed")

    config = load_config(None)
    test_freq = np.asarray([1.0e9, 2.0e9, 3.0e9])
    test_s = np.empty((test_freq.size, 5, 5), dtype=np.complex128)
    for index in range(test_freq.size):
        diagonal = (-0.25 + 0.04j * (index + 1)) * np.eye(5)
        coupling = (0.01 + 0.005j) * (np.ones((5, 5)) - np.eye(5))
        test_s[index] = diagonal + coupling
    extracted = extract_inductance(test_freq, test_s, config)
    if not np.allclose(
        extracted["sum"], extracted["total"], rtol=1.0e-9, atol=1.0e-18
    ):
        raise AssertionError("segment-sum consistency check failed")
    table, labels = result_table(extracted, config)
    if table.shape[0] != test_freq.size:
        raise AssertionError("result-table row count failed")
    if "M24_nH" not in labels or "Ls25_nH" not in labels:
        raise AssertionError("four-segment result labels are incomplete")
    with tempfile.TemporaryDirectory() as output_dir:
        output_config = config.copy()
        output_config["results_directory"] = output_dir
        output_config["write_plots"] = False
        written_table, written_labels, written_dir = write_results(
            extracted, output_config
        )
        if not os.path.isfile(
            os.path.join(written_dir, "tapped_inductor_results.csv")
        ):
            raise AssertionError("CSV result writing failed")
        if not os.path.isfile(os.path.join(written_dir, "ads_result_columns.txt")):
            raise AssertionError("column-map writing failed")
        if written_labels != labels or not np.allclose(
            written_table, table, equal_nan=True
        ):
            raise AssertionError("written result table differs from in-memory result")

    frequencies = np.asarray([1.0e9, 2.0e9])
    sample = np.empty((2 * 4 * 4, 4), dtype=np.complex128)
    row = 0
    source = np.empty((2, 4, 4), dtype=np.complex128)
    for f_index, frequency in enumerate(frequencies):
        for i in range(4):
            for j in range(4):
                value = (f_index + 1) + 1j * (10 * i + j)
                source[f_index, i, j] = value
                sample[row] = [frequency, i + 1, j + 1, value]
                row += 1
    parsed_f, parsed_matrix = parse_datalink_swept_matrix(sample, 4)
    if not np.array_equal(parsed_f, frequencies):
        raise AssertionError("Datalink frequency parsing failed")
    if not np.array_equal(parsed_matrix, source):
        raise AssertionError("Datalink matrix parsing failed")

    with tempfile.NamedTemporaryFile(suffix=".s3p", mode="w", delete=False) as stream:
        touchstone_path = stream.name
        stream.write("# GHz S RI R 50\n")
        numbers = [1.0]
        for i in range(3):
            for j in range(3):
                numbers.extend([10.0 * i + j, -(10.0 * i + j)])
        stream.write(" ".join(str(value) for value in numbers) + "\n")
    try:
        parsed_freq, parsed_s, parsed_z0 = read_touchstone(touchstone_path)
        if not np.isclose(parsed_freq[0], 1.0e9) or parsed_z0 != 50.0:
            raise AssertionError("Touchstone header parsing failed")
        if parsed_s[0, 2, 1] != 21.0 - 21.0j:
            raise AssertionError("Touchstone row-major parsing failed")
    finally:
        os.remove(touchstone_path)


def parse_arguments(argv):
    parser = argparse.ArgumentParser(
        description="Extract N tapped-inductor segment values from ADS S parameters."
    )
    parser.add_argument("--touchstone", help="input .sNp Touchstone file")
    parser.add_argument(
        "--config", default=DEFAULT_CONFIG, help="JSON configuration file"
    )
    parser.add_argument("--segments", type=int, help="override segment count")
    parser.add_argument("--self-test", action="store_true", help="run built-in tests")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_arguments(sys.argv[1:] if argv is None else argv)
    if args.self_test:
        self_test()
        print("Self-test passed.")
        return 0

    if args.touchstone:
        config = load_config(args.config)
        if args.segments is not None:
            config["segments"] = args.segments
        frequencies, s_matrix, touchstone_z0 = read_touchstone(args.touchstone)
        config["input_kind"] = "S"
        config["reference_impedance_ohm"] = touchstone_z0
        result = extract_inductance(frequencies, s_matrix, config)
        _table, _labels, output_dir = write_results(result, config)
        print("Results written to: " + output_dir)
        return 0

    try:
        run_datalink(args.config)
    except ImportError:
        raise SystemExit(
            "The ADS Datalink 'ads' module is unavailable. Run this script from "
            "ADS 2020 dl_python(), or use --touchstone from a terminal."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
