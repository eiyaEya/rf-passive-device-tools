# 公司 Linux 电脑：从零新建 ADS 2020 脚本

这份说明只讲公司电脑上的文件创建、Datalink 检查和首次运行。完整公式、结果列和故障解释见 `ADS2020_Linux_User_Guide_zh-CN.md`。

## 一、需要带到公司电脑的文件

从当前电脑复制以下四个文件：

```text
tapped_inductor_ads2020.py
tapped_inductor_config.json
datalink_echo_test.py
ADS2020_Linux_User_Guide_zh-CN.md
```

推荐直接复制文件，不要从聊天窗口逐段重敲 700 多行 Python，以免缩进、引号或字符编码发生变化。可采用公司允许的 U 盘、内网盘、代码仓库或文件传输方式。

## 二、找到 ADS 工作区目录

ADS 工作区通常以 `_wrk` 结尾，例如：

```text
/home/username/ADS_projects/spiral_inductor_wrk
```

以下说明把它记作：

```bash
/path/to/spiral_inductor_wrk
```

请替换成公司的真实路径，不要原样输入示例路径。

## 三、方法 A：用 Linux 终端新建目录并复制文件（推荐）

打开终端，执行：

```bash
cd /path/to/spiral_inductor_wrk
mkdir -p data/python
```

将四个文件复制进该目录。复制完成后检查：

```bash
cd /path/to/spiral_inductor_wrk/data/python
ls -l
```

至少应看到：

```text
tapped_inductor_ads2020.py
tapped_inductor_config.json
datalink_echo_test.py
ADS2020_Linux_User_Guide_zh-CN.md
```

脚本由 ADS Python 解释器读取，不强制要求可执行权限；为了也能从终端运行，可以执行：

```bash
chmod u+x tapped_inductor_ads2020.py datalink_echo_test.py
```

## 四、方法 B：在 ADS 2020 的 Spyder 中新建脚本

如果不能直接复制 `.py` 文件，可在 ADS 中创建：

1. 打开目标工作区。
2. 在 ADS 主窗口或 Data Display 中选择 `Tools > Spyder`。
3. 在 Spyder 选择 `File > New File`。
4. 把提供的 `tapped_inductor_ads2020.py` 完整内容粘贴进去。
5. 选择 `File > Save As`。
6. 保存为：

```text
/path/to/spiral_inductor_wrk/data/python/tapped_inductor_ads2020.py
```

7. 再新建一个文件，把配置内容粘贴并保存为：

```text
/path/to/spiral_inductor_wrk/data/python/tapped_inductor_config.json
```

注意事项：

- 文件名必须完全一致，Linux 区分大小写。
- Python 文件建议使用 UTF-8 编码。
- 不要保存成 `.py.txt` 或 `.json.txt`。
- Python 代码的缩进必须保留为一致的四个空格。
- 如果 `Tools > Spyder` 不存在，仍可使用 `gedit`、VS Code、Vim 或其他纯文本编辑器；保存目录不变。

## 五、手工创建配置文件

如果配置文件需要在公司电脑上重新建立，可在终端运行：

```bash
cd /path/to/spiral_inductor_wrk/data/python
nano tapped_inductor_config.json
```

粘贴下面内容：

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

按 `Ctrl+O` 保存、Enter 确认文件名、`Ctrl+X` 退出。以后只需修改 `segments`：

- 四段绕组、五个信号端口：`"segments": 4`
- 六段绕组、七个信号端口：`"segments": 6`

## 六、先检查 Datalink 是否正常

在运行正式脚本前，先用 ADS 自带测试函数检查环境。

1. 完成一次普通 S 参数仿真并打开 Data Display。
2. 插入 Equation。
3. 输入：

```text
DL_install_test=dl_datalink_test()
```

4. 用 List 显示 `DL_install_test`。

如果结果报告 Datalink 正常，再检查 ADS 找到的 Python：

```text
DL_python_path=dl_get_py_executable()
```

用 List 显示 `DL_python_path`，应得到一个实际 Python 路径，而不是函数未定义错误。

Linux 版 ADS 2020 正常安装时已经包含 Datalink。如果这里报 `dl_datalink_test` 未定义，应先检查 ADS 安装、启动环境和当前使用的 ADS 版本，而不是修改电感脚本。

## 七、新建最小回传测试脚本

如果没有复制 `datalink_echo_test.py`，可在 Spyder 或文本编辑器中新建该文件，内容只有：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ads

data, _strings = ads.get()
ads.send(data)
```

保存到：

```text
/path/to/spiral_inductor_wrk/data/python/datalink_echo_test.py
```

然后在 Data Display 插入 Equation：

```text
DL_echo=dl_python("datalink_echo_test.py","columnformat",freq)
```

用 List 显示 `DL_echo`。若返回的数据与 `freq` 对应，说明以下链路均正常：

```text
Data Display -> dl_python -> ADS Python -> ads.get -> ads.send -> Data Display
```

只有这个最小测试通过后，再运行正式脚本。

## 八、运行脚本自检

可以从 ADS 的 `Tools > Spyder` 打开 `tapped_inductor_ads2020.py`，但不要直接点击 Run，因为没有 `--touchstone` 参数时它会尝试进入 Datalink 模式。更清楚的办法是在终端中使用 ADS Datalink 的 Python 路径。

先在 Data Display 中通过：

```text
DL_python_path=dl_get_py_executable()
```

取得路径。假设返回：

```text
/opt/Keysight/ADS2020/tools/python/bin/python3
```

则在终端运行：

```bash
cd /path/to/spiral_inductor_wrk/data/python
/opt/Keysight/ADS2020/tools/python/bin/python3 tapped_inductor_ads2020.py --self-test
```

正常输出：

```text
Self-test passed.
```

实际路径以 `dl_get_py_executable()` 返回值为准，不要照抄示例 `/opt/...`。

## 九、运行正式提取

确认配置文件中的段数后，在 Data Display 插入 Equation：

```text
TI=dl_python("tapped_inductor_ads2020.py","columnformat",S)
```

用 List 显示 `TI`。四段绕组应满足：

- 配置 `segments=4`；
- 原理图只有 `Term1`～`Term5`；
- 公共地引脚直接接 `GND`；
- 数据集中有 `S(5,5)`，没有 `S(6,6)`。

成功后检查目录：

```bash
ls -l /path/to/spiral_inductor_wrk/data/python/tapped_inductor_results
```

应看到：

```text
tapped_inductor_results.csv
ads_result_columns.txt
tapped_inductor_summary.png
```

## 十、首次运行失败时收集哪些信息

不要立即改公式。请依次保留：

1. `DL_install_test` 的显示内容；
2. `DL_python_path` 的显示内容；
3. `DL_echo` 是否正常返回；
4. `TI` 返回的完整错误字符串；
5. 以下日志：

```text
/path/to/spiral_inductor_wrk/data/python/tapped_inductor_error.log
```

6. 数据集矩阵维数，例如是否存在 `S(5,5)`；
7. ADS 的完整版本号，例如 ADS 2020、Update 1 或 Update 2.x。

由于当前编写脚本的电脑没有安装 ADS，正式 Datalink 调用必须在公司电脑上完成这一次首次联调。脚本已经对常见的 ADS 2020 扫频矩阵布局做了兼容；若某个 Update 的实际布局不同，错误日志会记录原始数组形状和前十行，可据此做针对性调整。
