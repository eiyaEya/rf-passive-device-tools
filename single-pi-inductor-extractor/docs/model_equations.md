# Single-Pi Inductor Model Equations

The compact inductor model is implemented as an engineering piecewise model.

本工具采用工程分段模型：`f > 0` 时使用 AC 单 π 公式；`f = 0` 时使用单独的 DC 极限公式，只约束 `rs(DC)`。

Reference impedance:

```text
Z0 = 50 ohm by default
```

## AC Model (`f > 0`)

Series branch:

```text
Zs = (rs(DC) + jwLs) || (Rp1 + jwLp1) || [1 / (jwCo)]
```

Shunt branch:

```text
Zp = [1 / (jwCox)] + ([1 / (jwCsi)] || Rsi)
```

S-parameters:

```text
S11 = S22 = [(Zs/Z0) - ((2Zp + Zs)Z0 / Zp^2)] /
            [2(1 + Zs/Zp) + Zs/Z0 + ((2Zp + Zs)Z0 / Zp^2)]

S21 = S12 = 2 /
            [2(1 + Zs/Zp) + Zs/Z0 + ((2Zp + Zs)Z0 / Zp^2)]
```

## DC Model (`f = 0`)

At DC, capacitors are treated as open circuits and inductors are treated as short circuits. In this extraction tool, the DC point is used only to constrain the DC series resistance `rs(DC)`:

```text
S11 = rs(DC) / (2Z0 + rs(DC))
S21 = 2Z0 / (2Z0 + rs(DC))
S12 = S21
S22 = S11
```

This is a deliberate piecewise engineering definition. The tool does not require the AC expression as `f -> 0+` to be continuous with the exact `f = 0` branch.

这是有意采用的工程分段定义：`0 GHz` 直流点用于提取 `rs(DC)`；非零频点用于拟合完整 AC 单 π 模型。本工具不假设 `f -> 0+` 的 AC 公式必须与 `f = 0` 的 DC 公式连续。
