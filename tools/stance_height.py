"""按"支撑期 / 摆动期"分别统计脚底的绝对高度（相对机体原点的 Z 差）。
支撑期高度若显著高于静止值，说明脚没贴地 —— 从侧面一眼就能看出来。"""
import re
import statistics
import sys
from collections import defaultdict

path = sys.argv[1]
pat = re.compile(
    r"\[FootCSV\] owner=(\S+) leg=(\S+) t=([\d.]+) st=(\d) ph=(-?[\d.]+) "
    r"fwd=(-?[\d.]+) lift=(-?[\d.]+) fz=(-?[\d.]+)")

stance = defaultdict(list)
swing_lo = defaultdict(list)
for ln in open(path, "rb").read().decode("utf-8", "replace").splitlines():
    m = pat.search(ln)
    if not m:
        continue
    key = m.group(1)
    fz = float(m.group(8))
    if m.group(4) == "1":
        stance[key].append(fz)
    elif float(m.group(7)) < 0.5:
        swing_lo[key].append(fz)

print("%-22s %10s %10s %10s" % ("owner", "stance_lo", "stance_med", "lift_lo"))
print("-" * 56)
for k in sorted(stance):
    sl = sorted(stance[k])
    lo = statistics.median(sl[:max(1, len(sl) // 5)])
    print("%-22s %10.1f %10.1f %10.1f"
          % (k, lo, statistics.median(sl),
             statistics.median(swing_lo[k]) if swing_lo[k] else -1))
