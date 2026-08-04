# ADS Tapped-Inductor Extractor / ADS 抽头电感提取工具

This project extracts the inductance contributions of an N-segment tapped spiral inductor from a frequency-swept S-parameter matrix. It targets Keysight ADS 2020 on Linux through Python Datalink and also provides a Touchstone command-line fallback.

本项目用于从扫频 S 参数矩阵中提取 N 段抽头螺旋电感的各段电感贡献。主要运行环境为 Linux 版 Keysight ADS 2020 Python Datalink，同时提供 Touchstone 命令行备用方式。

## Project Layout / 项目目录

```text
ads-tapped-inductor-extractor/
  README.md
  .gitignore
  python/
    tapped_inductor_ads2020.py
    tapped_inductor_config.json
    datalink_echo_test.py
  docs/
    ADS2020_Linux_User_Guide_zh-CN.md
    Create_Scripts_on_Linux_zh-CN.md
```

## Extraction Definition / 提取定义

For `N` winding segments, connect `N+1` signal taps in physical winding order. The common ground pin is connected directly to ADS `GND` and is not terminated as an additional S-parameter port.

对于 `N` 段绕组，按绕组物理顺序连接 `N+1` 个信号抽头。公共地引脚直接连接 ADS `GND`，不作为额外的 S 参数端口放置 Term。

The script intentionally follows the single-ended, port-`j`-shorted definition used by the referenced extraction method:

```text
Ls(i,j) = -imag(Z(i,i) - Z(j,i)*Z(i,j)/Z(j,j)) / (2*pi*freq)
M(i,j)  = (Ls(i,j+1) - Ls(i,j) - Ls(i+1,j+1) + Ls(i+1,j)) / 2
L(i)    = Ls(i,i+1) + sum(M(i,j), j != i)
```

This is not a differential-inductance definition.

脚本严格保留当前采用的单端、端口 `j` 短路等效定义，不改用差分电感定义。

## Quick Start / 快速开始

1. Copy the three files in `python/` into the ADS workspace `data/python/` directory.
2. Set `segments` in `tapped_inductor_config.json` to the number of winding segments.
3. Run the built-in test:

```bash
python3 tapped_inductor_ads2020.py --self-test
```

4. After an ADS S-parameter simulation, add this equation in Data Display:

```text
TI=dl_python("tapped_inductor_ads2020.py","columnformat",S)
```

中文完整操作步骤、返回列定义和故障诊断见：

- [ADS 2020 Linux 使用说明](docs/ADS2020_Linux_User_Guide_zh-CN.md)
- [公司 Linux 电脑新建脚本与首次运行说明](docs/Create_Scripts_on_Linux_zh-CN.md)

## Touchstone Fallback / Touchstone 备用方式

```bash
python3 tapped_inductor_ads2020.py \
  --touchstone /path/to/model.s5p \
  --segments 4
```

The parser accepts full-matrix Touchstone RI, MA, and DB data in Hz, kHz, MHz, or GHz. The port count must equal `segments + 1`.

解析器支持完整矩阵的 Touchstone RI、MA、DB 数据以及 Hz、kHz、MHz、GHz 频率单位；端口数必须等于 `segments + 1`。

## Outputs / 输出

The tool returns or writes:

- all contiguous-path `Ls(i,j)` values;
- segment self-inductances and mutual inductances;
- each segment's total inductance contribution;
- direct total inductance, summed segment contribution, and their error;
- comparison of every segment with `L_total/N`;
- CSV results, a column map, and optional PNG plots.

工具会返回或生成全部路径电感、各段自感和互感、各段综合电感贡献、分段求和与总电感对比、各段与均分值 `L_total/N` 的偏差，以及 CSV、列映射和可选 PNG 图。

## Validation Status / 验证状态

The built-in numerical self-test passes in a standard Python environment with NumPy. ADS 2020 Datalink integration must be verified on a machine where ADS 2020 is installed.

内置数值自检已在带 NumPy 的标准 Python 环境通过。ADS 2020 Datalink 联调仍需在实际安装 ADS 2020 的电脑上完成。

## References / 参考资料

- [Keysight ADS 2020: ADS and Python Integration Using Datalink](https://edadownload.software.keysight.com/eedl/ads/2020/pdf/ADS_and_Python_Integration_Using_Datalink.pdf)
- [IBIS Open Forum: Touchstone File Format Specification 2.0](https://ibis.org/touchstone_ver2.0/touchstone_ver2_0.pdf)
