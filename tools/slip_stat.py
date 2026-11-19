"""一站式的支撑脚滑移统计。
slip = 支撑段内脚在世界里的最大位移 / 时长（不依赖与机体位移的对齐）。"""
import re
import sys
from collections import defaultdict

path = sys.argv[1]
rows = defaultdict(list)
for ln in open(path, "rb").read().decode("utf-8", "replace").splitlines():
    if "[FootCSV]" not in ln:
        continue
    s = ln[ln.find("[FootCSV]"):]
    d = dict(re.findall(r"(\w+)=(-?[\d.]+)", s))
    if "t" not in d:
        continue
    d["leg"] = re.search(r"leg=(\S+)", s).group(1)
    o = re.search(r"owner=(\S+)", s).group(1)
    rows[(o, d["leg"])].append(d)

res = defaultdict(list)
for key, seq in sorted(rows.items()):
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
        mv = max(((float(r["fx"]) - float(a["fx"])) ** 2 +
                  (float(r["fy"]) - float(a["fy"])) ** 2) ** 0.5 for r in s)
        res[key[0]].append(mv / dt)

print("%-22s %6s %10s %10s" % ("owner", "segs", "slip_med", "slip_p90"))
print("-" * 52)
for o in sorted(res):
    v = sorted(res[o])
    print("%-22s %6d %10.1f %10.1f"
          % (o, len(v), v[len(v) // 2], v[min(len(v) - 1, int(len(v) * 0.9))]))
