"""最差支撑段的逐帧明细，同时给出机体的运动方向，用于判断脚相对机体的
位移到底落在"前向"还是"侧向"。"""
import re
import sys
from collections import defaultdict

path = sys.argv[1]
want = sys.argv[2]

pat = re.compile(
    r"\[FootCSV\] owner=(\S+) leg=(\S+) t=([\d.]+) st=(\d) ph=(-?[\d.]+) "
    r"fwd=(-?[\d.]+) lift=(-?[\d.]+) fz=(-?[\d.]+) fx=(-?[\d.]+) fy=(-?[\d.]+) "
    r"cx=(-?[\d.]+) cy=(-?[\d.]+) ly=(-?[\d.]+)")

rows = defaultdict(list)
with open(path, "rb") as f:
    for ln in f.read().decode("latin-1", "replace").splitlines():
        m = pat.search(ln)
        if m and m.group(1) == want:
            rows[(m.group(1), m.group(2))].append(tuple(float(x) for x in m.groups()[2:]))

for key, seq in sorted(rows.items()):
    seq.sort()
    segs, cur = [], []
    for r in seq:
        if r[1] == 1:
            cur.append(r)
        else:
            if len(cur) >= 4:
                segs.append(cur)
            cur = []
    if len(cur) >= 4:
        segs.append(cur)
    if not segs:
        continue
    def slip(s):
        dur = s[-1][0] - s[0][0]
        w = max(((r[7] - s[0][7]) ** 2 + (r[8] - s[0][8]) ** 2) ** 0.5 for r in s)
        return w / max(dur, 1e-4)
    seg = max(segs, key=slip)
    # 机体速度方向
    bx = seg[-1][9] - seg[0][9]
    by = seg[-1][10] - seg[0][10]
    bl = max((bx * bx + by * by) ** 0.5, 1e-6)
    bx, by = bx / bl, by / bl
    print("== %s %s slip=%.1f frames=%d dur=%.3f  body_dir=(%.2f,%.2f)"
          % (key[0], key[1], slip(seg), len(seg), seg[-1][0] - seg[0][0], bx, by))
    print("%6s %6s %7s %7s %8s %8s %8s" %
          ("t", "ph", "fwd", "lift", "along", "across", "relmag"))
    r0 = seg[0]
    for r in seg:
        ax = (r[7] - r0[7])
        ay = (r[8] - r0[8])
        along = ax * bx + ay * by
        across = -ax * by + ay * bx
        rel = ((r[7] - r[9]) ** 2 + (r[8] - r[10]) ** 2) ** 0.5
        print("%6.3f %6.3f %7.2f %7.2f %8.1f %8.1f %8.1f"
              % (r[0], r[2], r[3], r[4], along, across, rel))
    print()
