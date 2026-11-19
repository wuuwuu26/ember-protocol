"""支撑段内脚相对机体的位移，分解到机体前向 / 侧向。
理想情况：支撑期脚相对机体匀速后退（前向分量 = -步幅/2 → +步幅/2），侧向≈0。
侧向分量大 = 转向滑移；前向分量不对 = 步幅/相位问题。
"""
import re
import statistics
import sys
from collections import defaultdict

path = sys.argv[1]
pat = re.compile(
    r"\[FootCSV\] owner=(\S+) leg=(\S+) t=([\d.]+) st=(\d) ph=(-?[\d.]+) "
    r"fwd=(-?[\d.]+) lift=(-?[\d.]+) fz=(-?[\d.]+) fx=(-?[\d.]+) fy=(-?[\d.]+) "
    r"cx=(-?[\d.]+) cy=(-?[\d.]+)")

rows = defaultdict(list)
for ln in open(path, "rb").read().decode("utf-8", "replace").splitlines():
    m = pat.search(ln)
    if m:
        rows[(m.group(1), m.group(2))].append(
            tuple(float(x) for x in m.groups()[2:]))

out = []
agg = defaultdict(list)
for key, seq in sorted(rows.items()):
    seq.sort()
    segs, cur = [], []
    for r in seq:
        if r[1] == 1:
            cur.append(r)
        else:
            if len(cur) >= 5:
                segs.append(cur)
            cur = []
    if len(cur) >= 5:
        segs.append(cur)

    for s in segs:
        r0, r1 = s[0], s[-1]
        # 机体位移方向
        bx, by = r1[8] - r0[8], r1[9] - r0[9]
        bl = (bx * bx + by * by) ** 0.5
        if bl < 1e-3:
            continue
        bx, by = bx / bl, by / bl
        # 脚相对机体的位移
        dx = (r1[6] - r1[8]) - (r0[6] - r0[8])
        dy = (r1[7] - r1[9]) - (r0[7] - r0[9])
        along = dx * bx + dy * by
        across = -dx * by + dy * bx
        agg[key[0]].append((along, across, bl, r1[5] - r0[5]))

for owner in sorted(agg):
    v = agg[owner]
    fwd = statistics.median([x[2] for x in v])
    out.append("%-22s body_step=%6.1f  rel_along=%6.1f  rel_across=%6.1f  fwd_delta=%6.1f"
               % (owner, fwd,
                  statistics.median([x[0] for x in v]),
                  statistics.median([abs(x[1]) for x in v]),
                  statistics.median([x[3] for x in v])))
print("\n".join(out))
