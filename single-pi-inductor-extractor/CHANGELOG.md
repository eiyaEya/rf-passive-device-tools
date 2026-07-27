# Changelog / 更新日志

## v0.2.0 - 2026-07-27

### Changed / 修改

- 网页版在检测到 `freq_GHz = 0` 的 DC 频点时，先从 DC S 参数单独解析 `rs(DC)`，并在后续拟合中固定该参数。
- MATLAB 版同步网页版逻辑：支持 DC 点单独解析 `rs(DC)`，有 DC 点时仅使用非 DC 频点拟合其余 7 个参数。
- MATLAB 版新增 `freq_GHz` / `frequency_GHz` 输入列支持，同时保留 `freq_Hz` / `frequency_Hz` 兼容。
- MATLAB 版 `singlePiSparams` 增加 DC 特判，避免在 `f = 0` 时计算 `1/(jwC)` 导致 `Inf` / `NaN`。
- MATLAB 版绘图时跳过 0 Hz 点，避免 `semilogx` 处理 DC 频点造成坐标异常。
- MATLAB 版 S 参数 dB 误差计算增加极小值保护，避免 `log10(0)` 导致无限值污染误差指标。
- 网页版导出 TXT 时记录 `rs(DC)` 是否来自 DC 点并在拟合前固定。

### Notes / 说明

- DC `rs(DC)` 反解优先使用 `S21`，无有效 `S21` 时使用 `S11`。
- 如果 DC `S21` 与 `S11` 反解出的 `rs(DC)` 差异较大，工具会给出提示并优先采用 `S21`。
- 示例文件中的 DC 行 `S21_dB = 0` 会反解出 `rs(DC) = 0 ohm`；真实使用时应填入与实际直流电阻一致的 DC S 参数。

## v0.1.0 - 2026-07-26

### Added / 新增

- 初始版本：包含 single-pi 电感模型参数提取网页版工具、MATLAB 脚本、示例 S 参数数据和模型公式说明。
- 支持提取 `Cox`、`Csi`、`Rsi`、`Ls`、`Co`、`rs(DC)`、`Lp1`、`Rp1` 八个参数。
