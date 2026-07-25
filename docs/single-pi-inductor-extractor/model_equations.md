# Single-Pi Inductor Model Equations

The compact inductor model uses a symmetric single-pi network.

Reference impedance:

```text
Z0 = 50 ohm by default
```

Series branch:

```text
Zs = [rs(DC) + jwLs || (Rp1 + jwLp1)] || [1 / (jwCo)]
```

Shunt branch:

```text
Zp = 1 / (jwCox) + [1 / (jwCsi) || Rsi]
```

S-parameters:

```text
S11 = S22 = [(Zs/Z0) - ((2Zp + Zs)Z0 / Zp^2)] /
            [2(1 + Zs/Zp) + Zs/Z0 + ((2Zp + Zs)Z0 / Zp^2)]

S21 = S12 = 2 /
            [2(1 + Zs/Zp) + Zs/Z0 + ((2Zp + Zs)Z0 / Zp^2)]
```

At DC (`f = 0`), all capacitors are open circuits and all inductors are short circuits. The model therefore reduces to a two-port with only the DC series resistance `rs(DC)`:

```text
S11 = rs(DC) / (2Z0 + rs(DC))
S21 = 2Z0 / (2Z0 + rs(DC))
S12 = S21
S22 = S11
```