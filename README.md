# RF Passive Device Tools

RF 无源器件设计工具集。

This repository stores small engineering tools, scripts, examples, and notes for RF passive device design and parameter extraction.

本仓库用于存放射频无源器件设计、参数提取、模型验证相关的小工具、脚本、示例数据和说明文档。

## Repository Layout / 仓库存储层次

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

## Directory Guide / 目录说明

`tools/`

Stores browser-based or executable engineering tools. Each independent tool should have its own subfolder. For example, the single-pi inductor extractor is stored under `tools/single-pi-inductor-extractor/`.

用于存放可以直接运行的工程工具，例如网页工具、可执行脚本或小型应用。每一个独立工具都应放在单独子文件夹中，例如电感单 π 模型参数提取工具放在 `tools/single-pi-inductor-extractor/`。

`examples/`

Stores example input files and test datasets. Keep examples separated by tool name so that each tool can be tested independently.

用于存放示例输入文件和测试数据。建议按照工具名建立子文件夹，方便每个工具独立测试和复现实例。

`matlab/`

Stores MATLAB scripts or helper functions related to each tool. The folder structure should mirror `tools/` when possible.

用于存放 MATLAB 版本的算法脚本或辅助函数。建议目录结构尽量与 `tools/` 保持一致，便于查找同一工具的网页版和 MATLAB 版。

`docs/`

Stores derivations, model equations, notes, and usage explanations. Documentation should be separated by project or tool name.

用于存放模型公式、推导过程、使用说明和设计笔记。建议按照项目或工具名称分类存放。

## Current Tools / 当前工具

### Single-Pi Inductor Extractor / 电感单 π 模型参数提取工具

Path / 路径: `tools/single-pi-inductor-extractor/index.html`

A standalone HTML tool for extracting eight compact single-pi inductor model parameters from multi-frequency S-parameter magnitude and phase data.

这是一个单文件 HTML 网页工具，可根据多频点 S 参数的幅值和相位，自动拟合电感单 π 等效模型中的 8 个参数。

Extracted parameters / 提取参数:

- `Cox`: oxide capacitance / 氧化层电容
- `Csi`: silicon substrate capacitance / 硅衬底电容
- `Rsi`: silicon substrate resistance / 硅衬底电阻
- `Ls`: series inductance / 串联电感
- `Co`: overlap or feed-through capacitance / 端口间耦合或交叠电容
- `rs(DC)`: DC series resistance / 直流串联电阻
- `Lp1`: auxiliary inductance in the frequency-dependent branch / 频率相关支路中的辅助电感
- `Rp1`: auxiliary resistance in the frequency-dependent branch / 频率相关支路中的辅助电阻

The tool supports reciprocal/symmetric S-parameter input and supports `0 GHz` as a DC point for directly constraining `rs(DC)`.

该工具支持对称互易网络输入模式，可以只输入 `S11` 和 `S21`。工具也支持 `0 GHz` 直流频点；在直流条件下，电容开路、电感短路，模型只通过 `rs(DC)` 计算 S 参数，因此直流点可用于精确约束直流串联电阻。

## Suggested Management Rules / 后续管理建议

- One independent engineering tool should live in one subfolder under `tools/`.
- Put example input data under `examples/<tool-name>/`.
- Put MATLAB or Python scripts under `matlab/<tool-name>/` or `scripts/<tool-name>/`.
- Put equations and design notes under `docs/<tool-name>/`.
- Avoid putting raw measurement data or process-confidential files in this public repository.
- Use clear file names in English so paths remain portable across EDA tools and operating systems.

中文建议：

- 一个可以独立使用的工程工具，对应 `tools/` 下的一个独立子文件夹。
- 示例 S 参数、CSV 输入文件等放在 `examples/<tool-name>/`。
- MATLAB 或 Python 版本算法放在 `matlab/<tool-name>/` 或 `scripts/<tool-name>/`。
- 公式推导、模型解释和使用说明放在 `docs/<tool-name>/`。
- 该仓库是 public，不建议上传真实工艺数据、测试原始数据、版图文件或任何涉密内容。
- 文件夹和文件名尽量使用英文，方便 GitHub、ADS、MATLAB 和不同操作系统稳定识别。