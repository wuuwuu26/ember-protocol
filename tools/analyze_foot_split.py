"""区分两种滑移：
  step_max  支撑段内**相邻帧**脚的最大位移（cm）—— 瞬移/跳变
  drift     支撑段内脚的总位移 / 时长（cm/s）—— 稳态拖动
如果一个段 step_max 很小而 drift 很大，说明脚在稳定地跟着机体走（相位错）
如果一个段 step_max 很大，说明某帧目标点跳了（换腿/落地）
"""
import re
import statistics
import sys
from collections import defaultdict

path = sys.argv[1]
pat = re.compile(
    r"\[FootCSV\] owner=(\S+) leg=(\S+) t=([\d.]+) st=(\d) "
    r"fz=(-?[\d.]+) fx=(-?[\d.]+) fy=(-?[\d.]+) cx=(-?[\d.]+) cy=(-?[\d.]+)")

rows = defaultdict(list)
with open(path, "rb") as f:
    for ln in f.read().decode("latin-1", "replace").splitlines():
        m = pat.search(ln)
        if m:
            rows[(m.group(1), m.group(2))].append(
                (float(m.group(3)), int(m.group(4)),
                 float(m.group(6)), float(m.group(7))))

segs = []
for key, seq in sorted(rows.items()):
    seq.sort()
    cur = []
    for t, st, fx, fy in seq:
        if st == 1:
            cur.append((t, fx, fy))
        else:
            if len(cur) >= 3:
                segs.append((key, cur))
            cur = []
    if len(cur) >= 3:
        segs.append((key, cur))

print("%-22s %-4s %6s %9s %9s" % ("owner", "leg", "segs", "step_med", "drift_med"))
print("-" * 60)
by = defaultdict(list)
for key, seg in segs:
    steps = []
    for i in range(1, len(seg)):
        dt = seg[i][0] - seg[i - 1][0]
        if dt <= 1e-4:
            continue
        d = ((seg[i][1] - seg[i - 1][1]) ** 2 +
             (seg[i][2] - seg[i - 1][2]) ** 2) ** 0.5
        steps.append(d)
    dur = seg[-1][0] - seg[0][0]
    if not steps or dur <= 0.02:
        continue
    drift = ((seg[-1][1] - seg[0][1]) ** 2 +
             (seg[-1][2] - seg[0][2]) ** 2) ** 0.5 / dur
    by[key].append((max(steps), drift))

for key in sorted(by):
    v = by[key]
    print("%-22s %-4s %6d %9.2f %9.1f"
          % (key[0], key[1], len(v),
             statistics.median([x[0] for x in v]),
             statistics.median([x[1] for x in v])))
