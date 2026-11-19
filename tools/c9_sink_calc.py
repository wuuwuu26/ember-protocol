"""C_9 的腿长 176.7、静止落差 165.8、可达水平半径只有 60.9。
步幅 22.6（±11.3）。要达到 ±11.3 的水平行程且保持腿部弯曲，
需要 p = 腿长*0.985 = 174.0，则 dz = sqrt(174^2 - 11.3^2) = 173.6。
当前 dz = 165.8 < 173.6，说明腿已伸直。
→ 骨盆必须**升高** 7.8cm 才能让步幅完全可达，但关节就会接近伸直；
  或者接受更小的步幅。
计算各种下沉量下的 A 与可得步幅。
"""
import math
L1, L2 = 100.2, 76.5
L = L1 + L2
rest_dz = 165.8
stride_half = 11.3
print("%8s %8s %8s %8s %8s" % ("sink", "dz", "d_at_edge", "A_edge", "reach"))
print("-" * 50)
for sink in [0, -5, -10, -15, -20, -25, -30]:
    dz = rest_dz + sink
    d = math.hypot(stride_half, dz)
    cosA = (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)
    A = math.degrees(math.acos(max(-1, min(1, cosA))))
    reach = math.sqrt(max(L * L * 0.985 ** 2 - dz * dz, 1))
    print("%8d %8.1f %8.1f %8.1f %8.1f" % (sink, dz, d, A, reach))
