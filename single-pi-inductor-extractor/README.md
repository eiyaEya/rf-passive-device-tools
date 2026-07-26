# Single-Pi Inductor Extractor / 电感单 π 模型参数提取工具

This project contains a standalone web tool, MATLAB script, examples, and model notes for extracting compact single-pi inductor model parameters from multi-frequency S-parameter data.

本项目用于从多频点 S 参数幅值和相位中提取电感单 π 等效模型的 8 个参数。项目内包含网页版工具、MATLAB 脚本、示例数据和模型公式说明。

## Project Layout / 项目目录

```text
single-pi-inductor-extractor/
  README.md
  web/
    index.html
  matlab/
    extract_single_pi_inductor.m
  examples/
    sample_sparams.csv
  docs/
    model_equations.md
```

## Files / 文件说明

`web/index.html`

Standalone browser version. Open this file directly in Edge, Chrome, or another modern browser. No server or installation is required.

网页版参数提取工具。可直接用 Edge、Chrome 等现代浏览器打开，不需要安装依赖，也不需要启动服务器。

`matlab/extract_single_pi_inductor.m`

MATLAB version of the extraction workflow, useful for algorithm verification, batch processing, or comparison with the web tool. It supports `freq_GHz`, `frequency_GHz`, `freq_Hz`, and `frequency_Hz` input columns. Generic `freq`, `frequency`, and `f` columns are treated as Hz for backward compatibility.

MATLAB 版本参数提取脚本，适合做算法验证、批量处理，或与网页版结果进行对照。脚本支持 `freq_GHz`、`frequency_GHz`、`freq_Hz`、`frequency_Hz` 频率列；为兼容旧格式，`freq`、`frequency`、`f` 按 Hz 处理。

`examples/sample_sparams.csv`

Example AC S-parameter input table. Frequency is expressed in GHz. The default sample intentionally does not include a DC row.

AC S 参数输入示例文件。频率单位为 GHz。默认样例有意不包含 DC 行，避免使用不自洽的直流示例数据。

`docs/model_equations.md`

Model equations, S-parameter expressions, and DC-limit explanation.

模型公式、S 参数表达式和直流分段模型解释。

## Input / 输入

Full S-parameter mode:

```text
freq_GHz, S11_dB, S11_deg, S21_dB, S21_deg, S12_dB, S12_deg, S22_dB, S22_deg
```

For reciprocal and symmetric networks, enable reciprocal mode in the page and enter only `S11` and `S21`; the tool mirrors them internally as `S22 = S11` and `S12 = S21`.

对于对称互易网络，可在网页中启用互易模式，只输入 `S11` 和 `S21`，程序会自动按 `S22 = S11`、`S12 = S21` 处理。

`freq_GHz = 0` is supported as a DC point. At DC, capacitors are open circuits and inductors are short circuits, so the model uses only `rs(DC)` to calculate S-parameters. For `f > 0`, the AC single-pi formula is used. This is a deliberate piecewise engineering model.

支持 `freq_GHz = 0` 的直流频点。直流时电容开路、电感短路，因此模型只通过 `rs(DC)` 计算 S 参数。非零频点继续使用 AC 单 π 公式；这是有意采用的工程分段模型。

## Output Parameters / 输出参数

- `Cox`: oxide capacitance / 氧化层电容
- `Csi`: silicon substrate capacitance / 硅衬底电容
- `Rsi`: silicon substrate resistance / 硅衬底电阻
- `Ls`: series inductance / 串联电感
- `Co`: overlap or feed-through capacitance / 端口间耦合或交叠电容
- `rs(DC)`: DC series resistance / 直流串联电阻
- `Lp1`: auxiliary inductance in the frequency-dependent branch / 频率相关支路中的辅助电感
- `Rp1`: auxiliary resistance in the frequency-dependent branch / 频率相关支路中的辅助电阻
