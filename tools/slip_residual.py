"""用"支撑段中点"衡量滑移：支撑期脚在世界里的位移应当≈机体位移（脚钉地）。
滑移 = |脚位移 - 机体位移| / 时长。这才是不受相位与对齐影响的量。"""
import re
import statistics
import sys
from collections import defaultdict

path = sys.argv[1]


def kv(line):
    d = dict(re.findall(r"(\w+)=(-?[\d.]+)", line))
    m = re.search(r"leg=(\S+)", line)
    if m:
        d["leg"] = m.group(1)
    return d


rows = defaultdict(list)
for ln in open(path, "rb").read().decode("utf-8", "replace").splitlines():
    if "[FootCSV]" not in ln:
        continue
    d = kv(ln[ln.find("[FootCSV]"):])
    if not d or "st" not in d:
        continue
    o = re.search(r"owner=(\S+)", ln).group(1)
    rows[(o, d.get("leg"))].append(d)

slip = defaultdict(list)
for key, seq in rows.items():
    seq.sort(key=lambda r: float(r["t"]))
    segs, cur = [], []
    for r in seq:
        if r["st"] == "1":
            cur.append(r)
        else:
            if len(cur) >= 6:
                segs.append(cur)
            cur = []
    if len(cur) >= 6:
        segs.append(cur)
    for s in segs:
        a, b = s[0], s[-1]
        dt = float(b["t"]) - float(a["t"])
        if dt <= 0.02:
            continue
        fdx = float(b["fx"]) - float(a["fx"])
        fdy = float(b["fy"]) - float(a["fy"])
        bdx = float(b["cx"]) - float(a["cx"])
        bdy = float(b["cy"]) - float(a["cy"])
        ex, ey = fdx - bdx, fdy - bdy
        slip[key[0]].append(((ex * ex + ey * ey) ** 0.5) / dt)

print("%-22s %6s %10s %10s" % ("owner", "segs", "resid_med", "resid_p90"))
print("-" * 52)
for o in sorted(slip):
    v = sorted(slip[o])
    print("%-22s %6d %10.1f %10.1f"
          % (o, len(v), v[len(v) // 2], v[min(len(v) - 1, int(len(v) * 0.9))]))
