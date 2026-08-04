# RF Passive Device Tools / 射频无源器件设计工具集

This repository stores engineering tools, scripts, examples, and notes for RF passive device design and parameter extraction.

本仓库用于存放射频无源器件设计、参数提取、模型验证相关的工程工具、脚本、示例数据和说明文档。

## Repository Layout / 仓库存储层次

The first-level folders are organized by project. Each project folder contains its relevant runnable tools, scripts, examples when applicable, and documentation.

仓库第一级目录按照项目分类。每个项目文件夹内部再存放该项目相关的可运行工具、脚本、适用时提供的示例数据和文档。这样同一项目的所有材料集中在一起，后续维护和迁移更清晰。

```text
rf-passive-device-tools/
  README.md

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

  future-project-name/
    README.md
    web/
    matlab/
    examples/
    docs/
```

## Directory Guide / 目录说明

`<project-name>/`

A complete project package. One independent engineering task or tool should correspond to one first-level project folder.

一个完整的项目包。一个可以独立使用、独立维护的工程工具或研究任务，对应一个第一级项目文件夹。

`<project-name>/README.md`

Project-level introduction, usage guide, input/output description, and file map.

项目级说明文件，用于说明该项目的用途、使用方法、输入输出格式和文件结构。

`<project-name>/web/`

Browser-based tools, usually standalone HTML/CSS/JavaScript files.

网页版工具目录，通常存放可直接用浏览器打开的 HTML/CSS/JavaScript 文件。

`<project-name>/matlab/`

MATLAB scripts or functions related to the project.

MATLAB 脚本或函数目录，用于算法验证、批量处理或与网页版工具交叉检查。

`<project-name>/python/`

Python scripts for EDA automation, parameter extraction, batch processing, or data conversion.

Python 脚本目录，用于 EDA 自动化、参数提取、批量处理或数据转换。

`<project-name>/examples/`

Example input files and test datasets.

示例输入文件和测试数据目录。

`<project-name>/docs/`

Model equations, derivations, design notes, and usage explanations.

模型公式、推导过程、设计笔记和使用说明目录。

## Current Projects / 当前项目

### Single-Pi Inductor Extractor / 电感单 π 模型参数提取工具

Project path / 项目路径: `single-pi-inductor-extractor/`

Web tool / 网页工具: `single-pi-inductor-extractor/web/index.html`

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

### ADS Tapped-Inductor Extractor / ADS 抽头电感提取工具

Project path / 项目路径: `ads-tapped-inductor-extractor/`

Python script / Python 脚本: `ads-tapped-inductor-extractor/python/tapped_inductor_ads2020.py`

A Linux ADS 2020 Python Datalink tool for extracting N tapped-inductor segment contributions from an `(N+1) x (N+1)` swept S-parameter matrix. It compares the segment sum with the directly extracted total inductance and compares every segment with `L_total/N`. A Touchstone command-line fallback is also included.

这是一个面向 Linux ADS 2020 Python Datalink 的多抽头电感提取工具。脚本从 `(N+1) x (N+1)` 扫频 S 参数矩阵中自动提取 N 段电感贡献，比较分段求和与总电感，并比较各段与 `L_total/N` 均分值；同时提供 Touchstone 命令行备用方式。

## Suggested Management Rules / 后续管理建议

- Use one first-level folder for each independent project.
- Keep each project's runnable tool, scripts, examples, and docs inside that project folder.
- Use `web/` for browser tools, `matlab/` for MATLAB scripts, `python/` for Python scripts, `examples/` for input data, and `docs/` for equations and notes.
- If a project becomes large enough to maintain independently, it can be moved out as a separate GitHub repository with minimal restructuring.
- Avoid putting raw measurement data, process-confidential files, layout files, or unpublished research data in this public repository.
- Use clear English folder and file names so paths remain portable across GitHub, ADS, MATLAB, and operating systems.

中文建议：

- 每个独立项目使用一个第一级文件夹。
- 同一项目的网页工具、MATLAB/Python 脚本、示例数据和说明文档都放在该项目文件夹内部。
- `web/` 放网页版工具，`matlab/` 放 MATLAB 脚本，`python/` 放 Python 脚本，`examples/` 放输入样例，`docs/` 放公式和笔记。
- 如果某个项目后续变得很大，可以直接把整个项目文件夹拆分成单独仓库。
- 该仓库是 public，不建议上传真实工艺数据、测试原始数据、版图文件或未公开研究数据。
- 文件夹和文件名尽量使用英文，方便 GitHub、ADS、MATLAB 和不同操作系统稳定识别。
