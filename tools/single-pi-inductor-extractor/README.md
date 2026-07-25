# Single-Pi Inductor Extractor

`index.html` is a standalone browser tool for extracting compact single-pi inductor model parameters from multi-frequency S-parameter data.

## Input

The input table uses frequency in GHz.

Required columns in full mode:

```text
freq_GHz, S11_dB, S11_deg, S21_dB, S21_deg, S12_dB, S12_deg, S22_dB, S22_deg
```

For reciprocal and symmetric networks, enable the reciprocal mode in the page and only enter `S11` and `S21`; the tool mirrors them internally as `S22 = S11` and `S12 = S21`.

`freq_GHz = 0` is supported as the DC point. At DC, capacitors are treated as open circuits and inductors as short circuits, so the model uses only `rs(DC)` to calculate S-parameters.

## Output Parameters

- `Cox`: oxide capacitance
- `Csi`: silicon substrate capacitance
- `Rsi`: silicon substrate resistance
- `Ls`: series inductance
- `Co`: overlap or feed-through capacitance
- `rs(DC)`: DC series resistance
- `Lp1`: auxiliary inductance in the frequency-dependent branch
- `Rp1`: auxiliary resistance in the frequency-dependent branch

## Usage

Open `index.html` directly in a browser. No build step or server is required.

After fitting, use `导出TXT文件` to export the extracted parameter batch result.