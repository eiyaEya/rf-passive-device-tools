# RF Passive Device Tools / 射频无源器件设计工具集

Engineering tools for RF passive-device parameter extraction, model verification, and EDA data processing.

用于射频无源器件参数提取、模型验证和 EDA 数据处理的工程工具集。仓库中的工具面向研究与设计辅助；使用结果前，应结合公式、仿真或测量数据进行独立核对。

## Project Overview / 项目导航

| Project / 项目 | Use / 用途 | Runtime / 运行环境 | Main input / 主要输入 | Main output / 主要输出 |
|---|---|---|---|---|
| [Single-Pi Inductor Extractor](single-pi-inductor-extractor/README.md) | Extract an eight-parameter compact single-π inductor model / 提取电感单 π 八参数紧凑模型 | Standalone browser or MATLAB / 浏览器或 MATLAB | Multi-frequency two-port S parameters / 多频点二端口 S 参数 | `Cox`, `Csi`, `Rsi`, `Ls`, `Co`, `rs(DC)`, `Lp1`, `Rp1` |
| [ADS Tapped-Inductor Extractor](ads-tapped-inductor-extractor/README.md) | Extract N segment contributions from an N-segment tapped inductor / 提取 N 段抽头电感的分段贡献 | Linux ADS 2020 Python Datalink or Python CLI / Linux ADS 2020 Datalink 或 Python 命令行 | Swept `(N+1) × (N+1)` S matrix or Touchstone / 扫频 S 矩阵或 Touchstone | Segment inductances, mutual terms, total/sum/average comparisons / 分段电感、互感及总和与均分对比 |

Choose the Single-Pi project when the goal is compact-model parameter fitting. Choose the ADS project when the goal is to analyze how a multi-tap winding contributes to total inductance.

需要拟合紧凑模型参数时选择 Single-Pi；需要分析多抽头绕组各段对总电感的贡献时选择 ADS 抽头电感工具。

### Direct Links / 快速入口

Single-Pi:

- [Project guide / 项目说明](single-pi-inductor-extractor/README.md)
- [Standalone web tool / 单文件网页工具](single-pi-inductor-extractor/web/index.html)
- [MATLAB extractor](single-pi-inductor-extractor/matlab/extract_single_pi_inductor.m)
- [Example S-parameter table / 示例数据](single-pi-inductor-extractor/examples/sample_sparams.csv)
- [Model equations / 模型公式](single-pi-inductor-extractor/docs/model_equations.md)
- [Changelog / 更新日志](single-pi-inductor-extractor/CHANGELOG.md)

ADS tapped-inductor:

- [Project guide / 项目说明](ads-tapped-inductor-extractor/README.md)
- [Main Python extractor / 主提取脚本](ads-tapped-inductor-extractor/python/tapped_inductor_ads2020.py)
- [Configuration / 配置文件](ads-tapped-inductor-extractor/python/tapped_inductor_config.json)
- [ADS 2020 Linux user guide / 中文使用说明](ads-tapped-inductor-extractor/docs/ADS2020_Linux_User_Guide_zh-CN.md)
- [First-run setup on Linux / Linux 首次运行说明](ads-tapped-inductor-extractor/docs/Create_Scripts_on_Linux_zh-CN.md)

## Repository Layout / 仓库目录

```text
rf-passive-device-tools/
├── README.md
├── single-pi-inductor-extractor/
│   ├── README.md
│   ├── CHANGELOG.md
│   ├── web/
│   │   └── index.html
│   ├── matlab/
│   │   └── extract_single_pi_inductor.m
│   ├── examples/
│   │   └── sample_sparams.csv
│   └── docs/
│       └── model_equations.md
└── ads-tapped-inductor-extractor/
    ├── README.md
    ├── .gitignore
    ├── python/
    │   ├── tapped_inductor_ads2020.py
    │   ├── tapped_inductor_config.json
    │   └── datalink_echo_test.py
    └── docs/
        ├── ADS2020_Linux_User_Guide_zh-CN.md
        └── Create_Scripts_on_Linux_zh-CN.md
```

Each first-level folder is an independently usable and maintainable engineering project. Detailed formulas, inputs, outputs, and troubleshooting remain in the project-level README and documentation.

每个一级目录对应一个可独立使用和维护的工程项目。完整公式、输入输出格式和故障排查保留在各项目自己的 README 与文档中。

## Single-Pi Inductor Extractor / 电感单 π 模型参数提取

This project fits the following compact-model parameters:

- `Cox`: oxide capacitance / 氧化层电容
- `Csi`: silicon substrate capacitance / 硅衬底电容
- `Rsi`: silicon substrate resistance / 硅衬底电阻
- `Ls`: series inductance / 串联电感
- `Co`: overlap or feed-through capacitance / 端口间耦合或交叠电容
- `rs(DC)`: DC series resistance / 直流串联电阻
- `Lp1`: auxiliary inductance / 频率相关支路辅助电感
- `Rp1`: auxiliary resistance / 频率相关支路辅助电阻

### Input and DC behavior / 输入与 DC 处理

The full input format is:

```text
freq_GHz,S11_dB,S11_deg,S21_dB,S21_deg,S12_dB,S12_deg,S22_dB,S22_deg
```

For reciprocal and symmetric devices, the web tool can accept only `S11` and `S21` and internally use `S22 = S11` and `S12 = S21`.

对于对称互易器件，网页工具可以只输入 `S11` 和 `S21`，内部按 `S22 = S11`、`S12 = S21` 处理。

- With no DC row, all eight parameters are fitted from AC data.
- With a `0 Hz` or `0 GHz` row, `rs(DC)` is first derived from the DC S parameters and fixed; the remaining seven parameters are fitted only from non-DC points.
- `freq_GHz` and `frequency_GHz` are interpreted as GHz.
- `freq_Hz`, `frequency_Hz`, and the compatibility names `freq`, `frequency`, and `f` are interpreted as Hz.

- 不含 DC 行时，八个参数全部由 AC 数据拟合。
- 含 `0 Hz` 或 `0 GHz` 行时，工具先从 DC S 参数反解并固定 `rs(DC)`，其余七个参数仅使用非 DC 频点拟合。
- `freq_GHz`、`frequency_GHz` 按 GHz 解释；`freq_Hz`、`frequency_Hz` 及兼容列名 `freq`、`frequency`、`f` 按 Hz 解释。

Magnitude-only fitting is supported, but an eight-parameter complex model is generally not unique when phase data is absent. Phase data and physically meaningful parameter bounds are strongly recommended.

工具支持仅使用幅值拟合，但缺少相位时，八参数复数网络的解通常不唯一。建议提供相位并结合工艺知识设置合理边界。

### Quick Start / 快速开始

Web version:

1. Open or download [`web/index.html`](single-pi-inductor-extractor/web/index.html).
2. Paste S-parameter table data, or start with [the sample CSV](single-pi-inductor-extractor/examples/sample_sparams.csv).
3. Set initial values and bounds, then run the fit and export the result.

MATLAB version, from the repository root:

```matlab
addpath("single-pi-inductor-extractor/matlab");
result = extract_single_pi_inductor( ...
    "single-pi-inductor-extractor/examples/sample_sparams.csv");
```

The Optimization Toolbox is used when available; otherwise the script falls back to bounded-penalty `fminsearch`.

## ADS Tapped-Inductor Extractor / ADS 抽头电感提取

For an inductor with `N` winding segments, the input must contain `N+1` signal ports numbered in physical winding order. Connect the common ground pin directly to ADS `GND`; do not add another `Term` for ground.

对于 `N` 段绕组，输入必须包含沿绕组物理顺序编号的 `N+1` 个信号端口。公共地引脚直接连接 ADS `GND`，不要为地端再放置一个 `Term`。

The extractor intentionally uses the selected single-ended, port-`j`-shorted definition. It is not a differential-inductance extractor. Full formulas are documented in the [project guide](ads-tapped-inductor-extractor/README.md).

脚本采用当前选定的单端、端口 `j` 短路等效定义，不是差分电感提取器。完整公式见[项目说明](ads-tapped-inductor-extractor/README.md)。

### Requirements / 运行要求

- ADS path: Linux Keysight ADS 2020 with Python Datalink.
- Touchstone path: Python 3 with NumPy.
- Matplotlib is optional and is used only for PNG plots.
- Touchstone input must contain a full S-parameter matrix with `segments + 1` ports.

### Quick Start / 快速开始

Run the built-in numerical test:

```bash
cd ads-tapped-inductor-extractor/python
python3 tapped_inductor_ads2020.py --self-test
```

For ADS Data Display:

```text
TI=dl_python("tapped_inductor_ads2020.py","columnformat",S)
```

For a Touchstone file:

```bash
python3 tapped_inductor_ads2020.py \
  --touchstone /path/to/model.s5p \
  --segments 4
```

The extractor reports all path inductances `Ls(i,j)`, segment self-inductances, mutual terms, each segment's total contribution, direct total inductance, summed contribution, `L_total/N`, deviations, CSV output, a column map, and optional PNG plots.

脚本输出全部路径电感、分段自感、互感、各段综合贡献、直接提取的总电感、分段求和、`L_total/N` 均分值与偏差，并可生成 CSV、列映射和 PNG 图。

## Validation Status and Limits / 验证状态与限制

These are manual validation results, not continuous-integration guarantees.

以下为人工验证结果，并非持续集成保证。

| Component / 组件 | Current status / 当前状态 |
|---|---|
| Single-Pi web tool | Inline JavaScript syntax check passed on 2026-08-04 / 内嵌 JavaScript 语法检查已于 2026-08-04 通过 |
| Single-Pi MATLAB extractor | DC regression with known `rs(DC) = 2 Ω` passed on 2026-08-04; bare `freq` was verified as Hz / 已通过已知 `rs(DC)=2 Ω` 的 DC 回归，并确认裸 `freq` 按 Hz 读取 |
| ADS Python core | Built-in `--self-test` passed in a standard Python environment with NumPy on 2026-08-04 / 内置数值自检已通过 |
| ADS 2020 Datalink | First integration run is still required on a machine with ADS 2020 installed / 仍需在实际安装 ADS 2020 的电脑上完成首次联调 |

Additional limits:

- Parameter extraction is model-dependent; numerical agreement does not by itself prove physical validity.
- The ADS segment-sum comparison is algebraically related to the same extracted path inductances and is not a fully independent physical validation.
- Results near or above self-resonance may become large, negative, or discontinuous.
- Always confirm port order, frequency units, reference impedance, and model assumptions.

其他限制：

- 参数提取依赖模型定义；数值一致不等于已经完成独立的物理验证。
- ADS 的分段求和比较由同一组路径电感构造，不是完全独立的物理验证。
- 接近或超过自谐振频率时，等效电感可能出现大值、负值或突变。
- 使用前必须确认端口顺序、频率单位、参考阻抗和模型假设。

## Repository Conventions / 仓库维护约定

- Use one first-level English-named folder for each independent project.
- Keep runnable tools, scripts, examples, and documentation inside the corresponding project folder.
- Use `web/` for browser tools, `matlab/` for MATLAB code, `python/` for Python code, `examples/` for public or synthetic samples, and `docs/` for equations and guides.
- Update the project README and changelog when behavior changes; update this root README when a project is added or its public status changes.
- Do not upload raw measurement data, process-confidential files, layout files, credentials, or unpublished research data to this public repository.

- 每个独立项目使用一个英文一级目录。
- 可运行工具、脚本、示例和文档放在对应项目目录内。
- `web/`、`matlab/`、`python/`、`examples/`、`docs/` 分别存放相应类型的内容。
- 行为发生变化时同步更新项目 README 和更新日志；新增项目或公开状态改变时同步更新本主 README。
- 本仓库公开，禁止上传原始测量数据、工艺机密、版图文件、凭据或未公开研究数据。

## References / 参考资料

Project-specific formulas and references are maintained with each tool:

- [Single-Pi model equations](single-pi-inductor-extractor/docs/model_equations.md)
- [ADS extraction formulas and official references](ads-tapped-inductor-extractor/README.md)
