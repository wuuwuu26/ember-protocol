"""比较：脚到**自己的髋**的距离 vs 目标到髋的距离。
若脚离自己髋的距离≈静止腿长，说明 IK 把腿伸到了极限；
若远小于，说明脚根本不在腿的末端（骨骼链或累积计算出错）。"""
import re
import statistics
import sys
from collections import defaultdict

path = sys.argv[1]
pat = re.compile(
    r"\[FootCSV\] owner=(\S+) leg=(\S+) t=([\d.]+) st=(\d) ph=(-?[\d.]+) "
    r"fwd=(-?[\d.]+) lift=(-?[\d.]+) fz=(-?[\d.]+) fx=(-?[\d.]+) fy=(-?[\d.]+) "
    r"cx=(-?[\d.]+) cy=(-?[\d.]+) ly=(-?[\d.]+)")

g = defaultdict(list)
for ln in open(path, "rb").read().decode("utf-8", "replace").splitlines():
    m = pat.search(ln)
    if m:
        g[m.group(1)].append(tuple(float(x) for x in m.groups()[2:]))

print("%-22s %8s %8s %8s %8s" % ("owner", "foot_dx", "foot_dz", "tgt_dx", "tgt_dz"))
print("-" * 60)
for o in sorted(g):
    rows = [r for r in g[o] if r[1] == 1]
    if not rows:
        continue
    mx = statistics.median([r[5] - r[7] for r in rows])
    mz = statistics.median([r[5] - r[12] for r in rows])  # 注意：脚Z不在行内
    print("%-22s %8.1f %8.1f" % (o, mx, mz))
