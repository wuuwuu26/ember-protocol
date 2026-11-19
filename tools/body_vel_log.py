import re
import statistics
import sys
from collections import defaultdict

p = sys.argv[1]
txt = open(p, "rb").read().decode("utf-8", "replace")


def get(l, k):
    m = re.search(k + r"=(-?[\d.]+)", l)
    return float(m.group(1)) if m else 0.0


rows = defaultdict(dict)
for l in txt.splitlines():
    if "FootCSV" not in l:
        continue
    o = re.search(r"owner=(\S+)", l).group(1)
    rows[o][round(get(l, "t"), 3)] = (get(l, "cx"), get(l, "cy"))

out = []
for o in sorted(rows):
    ts = sorted(rows[o])
    v = []
    for i in range(1, len(ts)):
        dt = ts[i] - ts[i - 1]
        if dt <= 0:
            continue
        dx = rows[o][ts[i]][0] - rows[o][ts[i - 1]][0]
        dy = rows[o][ts[i]][1] - rows[o][ts[i - 1]][1]
        v.append(((dx * dx + dy * dy) ** 0.5) / dt)
    if not v:
        continue
    v.sort()
    out.append("%-22s n=%3d v_med=%6.1f v_p90=%6.1f v_max=%7.1f"
               % (o, len(ts), statistics.median(v), v[int(len(v) * 0.9)], v[-1]))
print("\n".join(out))
