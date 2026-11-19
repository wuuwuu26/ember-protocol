"""把支撑段内的脚位移按"段内进度"归一化，看脚是均匀后退还是只在某一段偏。

对每个支撑段，计算每帧脚相对段首的位移占段总位移的比例，
再按进度分桶平均。如果曲线是直线 0→1，说明脚被稳定拖动；
如果在某一段特别平、某一段特别陡，说明是换相瞬间的问题。
同时打印脚相对机体的位置（fx-cx），看支撑期是否真的在从前往后扫。
"""
import re
import sys
from collections import defaultdict

path = sys.argv[1]
want = sys.argv[2] if len(sys.argv) > 2 else None

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
                 float(m.group(6)), float(m.group(7)),
                 float(m.group(8)), float(m.group(9))))

for key, seq in sorted(rows.items()):
    if want and want not in key[0]:
        continue
    seq.sort()
    segs = []
    cur = []
    for row in seq:
        if row[1] == 1:
            cur.append(row)
        else:
            if len(cur) >= 4:
                segs.append(cur)
            cur = []
    if len(cur) >= 4:
        segs.append(cur)
    if not segs:
        continue
    # 选最"典型"的段（帧数最多）
    seg = max(segs, key=len)
    print("== %s %s  frames=%d dur=%.3f" % (key[0], key[1], len(seg),
                                            seg[-1][0] - seg[0][0]))
    print("%6s %8s %8s %10s %10s %8s" %
          ("u", "rel_fx", "rel_fy", "worldmove", "bodymove", "fz"))
    t0 = seg[0][0]
    x0, y0 = seg[0][2], seg[0][3]
    c0x, c0y = seg[0][4], seg[0][5]
    dur = max(seg[-1][0] - t0, 1e-4)
    for r in seg:
        u = (r[0] - t0) / dur
        wm = ((r[2] - x0) ** 2 + (r[3] - y0) ** 2) ** 0.5
        bm = ((r[4] - c0x) ** 2 + (r[5] - c0y) ** 2) ** 0.5
        print("%6.2f %8.1f %8.1f %10.1f %10.1f %8.1f"
              % (u, r[2] - r[4], r[3] - r[5], wm, bm, r[6] if len(r) > 6 else 0))
    print()
