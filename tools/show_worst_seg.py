"""打印最差支撑段（单一）的逐帧明细，看清脚到底怎么动的。"""
import re
import sys
from collections import defaultdict

path = sys.argv[1]
want_owner = sys.argv[2] if len(sys.argv) > 2 else "BP_Enemy_C_5"

pat = re.compile(
    r"\[FootCSV\] owner=(\S+) leg=(\S+) t=([\d.]+) st=(\d) "
    r"fz=(-?[\d.]+) fx=(-?[\d.]+) fy=(-?[\d.]+) cx=(-?[\d.]+) cy=(-?[\d.]+)")

rows = defaultdict(list)
with open(path, "rb") as f:
    for ln in f.read().decode("latin-1", "replace").splitlines():
        m = pat.search(ln)
        if m and m.group(1) == want_owner:
            rows[m.group(2)].append((float(m.group(3)), int(m.group(4)),
                                     float(m.group(6)), float(m.group(7))))

best = None
for leg, seq in rows.items():
    seq.sort()
    cur = []
    for t, st, fx, fy in seq:
        if st == 1:
            cur.append((t, fx, fy))
        else:
            if len(cur) >= 5:
                dur = cur[-1][0] - cur[0][0]
                worst = max(((x - cur[0][1]) ** 2 + (y - cur[0][2]) ** 2) ** 0.5
                            for _, x, y in cur)
                slip = worst / max(dur, 1e-4)
                if best is None or slip > best[0]:
                    best = (slip, leg, list(cur))
            cur = []

if not best:
    print("no segment")
    raise SystemExit

slip, leg, seg = best
print("owner=%s leg=%s slip=%.1fcm/s frames=%d dur=%.3f"
      % (want_owner, leg, slip, len(seg), seg[-1][0] - seg[0][0]))
print("%8s %10s %10s %10s %10s" % ("t", "fx", "fy", "dx_from0", "step"))
t0, x0, y0 = seg[0]
prev = None
for t, x, y in seg:
    d = ((x - x0) ** 2 + (y - y0) ** 2) ** 0.5
    step = 0.0 if prev is None else ((x - prev[0]) ** 2 + (y - prev[1]) ** 2) ** 0.5
    print("%8.3f %10.1f %10.1f %10.1f %10.2f" % (t, x, y, d, step))
    prev = (x, y)
