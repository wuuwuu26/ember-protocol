"""在 analyze_foot_csv 的基础上，判断"打滑"与"速度突变"是否相关。

对每段连续支撑期，同时记录：
  slip      段内脚在世界里的最大位移 / 时长
  v_mean    段内机体平均速度
  v_std     段内机体速度标准差（突变程度）
然后按 v_std 分桶看 slip，直接验证因果。
"""
import re
import statistics
import sys
from collections import defaultdict

path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\25227\Documents\robot_game\ue\shot_r545_csv.log"

pat = re.compile(
    r"\[FootCSV\] owner=(\S+) leg=(\S+) t=([\d.]+) st=(\d) "
    r"fz=(-?[\d.]+) fx=(-?[\d.]+) fy=(-?[\d.]+) cx=(-?[\d.]+) cy=(-?[\d.]+)")

rows = defaultdict(list)
with open(path, "rb") as f:
    for ln in f.read().decode("latin-1", "replace").splitlines():
        m = pat.search(ln)
        if not m:
            continue
        rows[(m.group(1), m.group(2))].append((
            float(m.group(3)), int(m.group(4)),
            float(m.group(6)), float(m.group(7)),
            float(m.group(8)), float(m.group(9))))

segs_all = []
for (owner, leg), seq in sorted(rows.items()):
    seq.sort()
    cur = []
    for t, st, fx, fy, cx, cy in seq:
        if st == 1:
            cur.append((t, fx, fy, cx, cy))
        else:
            if len(cur) >= 5:
                segs_all.append((owner, leg, cur))
            cur = []
    if len(cur) >= 5:
        segs_all.append((owner, leg, cur))

print("%-22s %-4s %8s %8s %8s" % ("owner", "leg", "slip", "v_mean", "v_std"))
print("-" * 56)

buckets = defaultdict(list)
for owner, leg, seg in segs_all:
    t0, fx0, fy0, cx0, cy0 = seg[0]
    t1, fx1, fy1, cx1, cy1 = seg[-1]
    dur = t1 - t0
    if dur < 0.02:
        continue
    worst = 0.0
    for t, fx, fy, cx, cy in seg:
        worst = max(worst, ((fx - fx0) ** 2 + (fy - fy0) ** 2) ** 0.5)
    slip = worst / dur

    vs = []
    for i in range(1, len(seg)):
        dt = seg[i][0] - seg[i - 1][0]
        if dt > 1e-4:
            d = ((seg[i][3] - seg[i - 1][3]) ** 2 +
                 (seg[i][4] - seg[i - 1][4]) ** 2) ** 0.5
            vs.append(d / dt)
    if not vs:
        continue
    v_mean = statistics.mean(vs)
    v_std = statistics.pstdev(vs) if len(vs) > 1 else 0.0
    buckets[owner].append((slip, v_mean, v_std))

for owner, lst in sorted(buckets.items()):
    lst.sort(key=lambda x: -x[0])
    for slip, vm, vs in lst[:4]:
        print("%-22s     %8.1f %8.0f %8.1f" % (owner, slip, vm, vs))
    print("   ^ 最差的 4 段；该实体共 %d 段，slip 中位 %.1f"
          % (len(lst), statistics.median([s for s, _, _ in lst])))
