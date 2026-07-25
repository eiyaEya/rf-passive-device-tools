# RF Passive Device Tools

This repository stores small engineering tools, scripts, examples, and notes for RF passive device design and parameter extraction.

## Repository Layout

```text
rf-passive-device-tools/
  README.md
  tools/
    single-pi-inductor-extractor/
      index.html
      README.md
  examples/
    single-pi-inductor-extractor/
      sample_sparams.csv
  matlab/
    single-pi-inductor-extractor/
      extract_single_pi_inductor.m
  docs/
    single-pi-inductor-extractor/
      model_equations.md
```

## Directory Guide

`tools/`

Stores browser-based or executable engineering tools. Each independent tool should have its own subfolder. For example, the single-pi inductor extractor is stored under `tools/single-pi-inductor-extractor/`.

`examples/`

Stores example input files and test datasets. Keep examples separated by tool name so that each tool can be tested independently.

`matlab/`

Stores MATLAB scripts or helper functions related to each tool. The folder structure should mirror `tools/` when possible.

`docs/`

Stores derivations, model equations, notes, and usage explanations. Documentation should be separated by project or tool name.

## Current Tools

### Single-Pi Inductor Extractor

Path: `tools/single-pi-inductor-extractor/index.html`

A standalone HTML tool for extracting eight compact single-pi inductor model parameters from multi-frequency S-parameter magnitude and phase data.

Extracted parameters:

- `Cox`
- `Csi`
- `Rsi`
- `Ls`
- `Co`
- `rs(DC)`
- `Lp1`
- `Rp1`

The tool supports reciprocal/symmetric S-parameter input and supports `0 GHz` as a DC point for directly constraining `rs(DC)`.

## Management Rules

- One independent engineering tool should live in one subfolder under `tools/`.
- Put example input data under `examples/<tool-name>/`.
- Put MATLAB or Python scripts under `matlab/<tool-name>/` or `scripts/<tool-name>/`.
- Put equations and design notes under `docs/<tool-name>/`.
- Avoid putting raw measurement data or process-confidential files in this public repository.
- Use clear file names in English so paths remain portable across EDA tools and operating systems.