# ADS 2020 Linux 多抽头螺旋电感提取脚本

## 1. 功能与采用的定义

本工具用于具有 `N` 段绕组、`N+1` 个按绕组物理顺序编号的抽头端口的螺旋电感。公共地引脚在原理图中直接接 `GND`，不接 `Term`；S 参数控制器只看到 `N+1` 个接有 `Term` 的信号端口。

脚本严格采用当前论文方法中的单端、端口 `j` 短路等效定义，不改用差分阻抗：

```text
Ls(i,j) = -imag(Z(i,i)-Z(j,i)*Z(i,j)/Z(j,j))/(2*pi*freq)
```

任意两段 `i<j` 的互感由下式提取：

```text
M(i,j)=(Ls(i,j+1)-Ls(i,j)-Ls(i+1,j+1)+Ls(i+1,j))/2
```

每段对总电感的综合贡献为：

```text
L(i)=Ls(i,i+1)+sum(M(i,j), j!=i)
```

脚本输出：

- 所有连续抽头路径的 `Ls(i,j)`；
- 所有段间互感 `M(i,j)`；
- 每段自感 `Ls(i,i+1)`；
- 每段综合贡献 `L(i)`；
- `sum(L(i))`、外侧端口直接提取的 `Ls(1,N+1)` 及两者误差；
- `Ls(1,N+1)/N` 均分值、各段绝对偏差和百分比偏差；
- CSV、列编号文件和 PNG 汇总图。

## 2. 文件放置位置

把以下两个文件复制到 ADS 工作区的 `data/python` 目录：

```text
你的工作区_wrk/
└── data/
    └── python/
        ├── tapped_inductor_ads2020.py
        └── tapped_inductor_config.json
```

如果 `data/python` 不存在，可以手动创建；ADS Datalink 第一次运行时通常也会创建它。

Linux 版 ADS 2020 已包含 Python Datalink，不需要另装 Windows 版的 Datalink 插件。

## 3. 配置抽头数

编辑 `tapped_inductor_config.json`：

```json
{
  "segments": 4,
  "input_kind": "S",
  "reference_impedance_ohm": 50.0,
  "inductance_sign": -1.0,
  "output_unit": "nH",
  "results_directory": "tapped_inductor_results",
  "write_csv": true,
  "write_plots": true,
  "denominator_relative_tolerance": 1e-12
}
```

主要参数：

- `segments`：绕组段数 `N`。四段绕组填写 `4`，此时脚本要求 S 矩阵为 `5x5`。
- `input_kind`：推荐保持为 `S`，脚本内部完成 `S -> Z` 转换。
- `reference_impedance_ohm`：所有信号端口的参考阻抗，当前为 `50` 欧姆。
- `inductance_sign`：保持为 `-1`，与现有论文公式的 `-imag(...)` 一致。
- `output_unit`：可选 `H`、`mH`、`uH`、`nH` 或 `pH`。

## 4. 原理图设置检查

以四段、五抽头为例：

1. 五个抽头信号端口依次连接 `Term1`～`Term5`，每个 `Z=50 Ohm`。
2. EM symbol 的公共地引脚直接连接 ADS `GND`，不要再放置 `Term6`。
3. 放置 S 参数仿真控制器并完成扫频仿真。
4. 打开生成的数据集，确认存在 `S(5,5)`，不存在 `S(6,6)`。
5. 端口 1～5 必须沿绕组从一端到另一端连续编号。

如果数据集中存在 `S(6,6)`，说明地也被当成独立 S 端口；此脚本不能直接处理，需要先重新设置端口或进行端口参考变换。

## 5. 在 Data Display 中运行

建议在仿真完成后从 Data Display 调用，不要把 Datalink 放入原理图 `MeasEqn`，否则每次仿真都会额外启动 Python，增加仿真时间。

1. 打开仿真数据对应的 Data Display 页面。
2. 选择 `Insert > Equation`，或点击 Equation 图标。
3. 输入：

```text
TI=dl_python("tapped_inductor_ads2020.py","columnformat",S)
```

4. 点击 Apply 或重新计算 Equation。
5. 插入一个 List，先直接显示 `TI`，确认返回的是数值矩阵而不是错误字符串。

说明：`columnformat` 对多维扫频矩阵本身没有副作用，主要用于避免不同 ADS 2020 Update 对一维数据的排布差异。

### 如果希望仍由 ADS 执行 `stoz`

也可以在 Data Display 中写：

```text
Z=stoz(S)
TI=dl_python("tapped_inductor_ads2020.py","columnformat",Z)
```

同时把配置文件中的：

```json
"input_kind": "Z"
```

此时 `reference_impedance_ohm` 不再参与转换。

## 6. 四段绕组返回列编号

当 `segments=4`、`output_unit=nH` 时，`TI` 的列定义如下。编号从 `0` 开始，和 Python/ADS Datalink 返回矩阵的列号一致。

| 列号 | 含义 |
|---:|---|
| 0 | `freq_Hz` |
| 1 | `L_total_nH=Ls15` |
| 2 | `L_sum_nH=L1+L2+L3+L4` |
| 3 | `L_sum_minus_total_nH` |
| 4 | `L_sum_error_pct` |
| 5 | `L_average_nH=L_total/4` |
| 6～9 | `L1_nH`～`L4_nH`，四段综合贡献 |
| 10～13 | `L1-Laverage`～`L4-Laverage`，单位 nH |
| 14～17 | 四段相对均分值的百分比偏差 |
| 18～21 | `Ls12`、`Ls23`、`Ls34`、`Ls45` |
| 22～27 | `M12`、`M13`、`M14`、`M23`、`M24`、`M34` |
| 28～37 | `Ls12`、`Ls13`、`Ls14`、`Ls15`、`Ls23`、`Ls24`、`Ls25`、`Ls34`、`Ls35`、`Ls45` |

其中：

```text
Ls25=-imag(Z(2,2)-Z(5,2)*Z(2,5)/Z(5,5))/(2*pi*freq)
M24=(Ls25-Ls24-Ls35+Ls34)/2
```

脚本每次运行后还会生成完整的列映射文件，所以 `N` 改变后不需要自己计算列号：

```text
data/python/tapped_inductor_results/ads_result_columns.txt
```

## 7. 在 Data Display 中画曲线

可以先尝试用以下形式取返回矩阵的某一列：

```text
TI_freq=real(TI[::,0])
TI_Ltotal=real(TI[::,1])
TI_Lsum=real(TI[::,2])
TI_L1=real(TI[::,6])
TI_L2=real(TI[::,7])
TI_L3=real(TI[::,8])
TI_L4=real(TI[::,9])
```

然后建立矩形图，以 `TI_freq` 为横轴，绘制需要的列。若当前 ADS 2020 Update 不接受省略首尾索引的 `::` 写法，直接在 List 中查看 `TI`，并使用脚本自动生成的 PNG 和 CSV；不同 Update 的切片显示语法可能略有差异，但不影响提取计算。

## 8. 自动生成的文件

默认输出目录：

```text
data/python/tapped_inductor_results/
```

包括：

- `tapped_inductor_results.csv`：所有频率点及全部提取结果；
- `ads_result_columns.txt`：ADS 返回矩阵的列号与变量名；
- `tapped_inductor_summary.png`：三幅汇总图，分别为各段与均分值、总和与总电感、各段百分比偏差。

由于 `M(i,j)` 是由同一组 `Ls(i,j)` 差分构造的，`sum(L(i))` 与 `Ls(1,N+1)` 在代数上应基本一致。因此二者误差主要用于检查端口顺序、无效频点和数值异常，不是完全独立的物理验证。

## 9. Touchstone 备用运行方式

如果某个 ADS 2020 Update 的 Datalink 无法正确传递完整扫频矩阵，可从 ADS/Momentum 导出标准全矩阵 `.sNp` 文件，然后在 Linux 终端运行：

```bash
cd /path/to/your_workspace_wrk/data/python
python3 tapped_inductor_ads2020.py \
  --touchstone /path/to/model.s5p \
  --segments 4
```

该模式支持常见的 Touchstone `RI`、`MA`、`DB` 格式以及 `Hz/kHz/MHz/GHz` 单位，要求完整矩阵。运行结果写入同一个 `tapped_inductor_results` 目录。

如果系统的 `python3` 缺少 NumPy，可使用 ADS Datalink 自带的 Python，或者在自己的 Python 环境中安装：

```bash
python3 -m pip install numpy matplotlib
```

其中 Matplotlib 只负责 PNG 绘图；没有 Matplotlib 时，核心计算和 CSV 输出仍可工作。

## 10. 自检与故障诊断

在 Linux 终端运行内置自检：

```bash
python3 tapped_inductor_ads2020.py --self-test
```

正常输出：

```text
Self-test passed.
```

如果 `dl_python()` 返回错误字符串，检查：

```text
data/python/tapped_inductor_error.log
```

该文件会记录 ADS 实际传入的数组形状、前十行数据和 Python traceback。常见原因包括：

- `segments=N` 与 S 矩阵端口数 `N+1` 不一致；
- 传入了 `S(1,1)` 等单个元素，而不是完整的 `S`；
- 除频率外还存在参数扫描；当前版本只接受单一频率扫描；
- 地端口也接了 `Term`，导致 S 矩阵多出一个端口；
- 某些频点的 `Z(j,j)` 接近零，相关 `Ls` 会变为 `NaN`；
- 频率接近或超过自谐振区，单端等效电感可能出现很大、负值或突变，这属于模型定义和寄生效应，不一定是脚本错误。

## 11. 建议的结果检查顺序

1. 先在低于自谐振频率的频段检查结果。
2. 检查 `Ls12`、`Ls23` 等相邻段是否与原手算结果一致。
3. 用四段模型检查 `Ls25` 与 `M24`。
4. 检查 `L_sum_minus_total` 是否接近数值零。
5. 最后查看各段相对 `L_total/N` 的百分比偏差。
