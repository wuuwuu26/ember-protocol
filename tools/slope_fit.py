"""用实测数据线性拟合 php = a * fwd + b，斜率 a（度/厘米）。
这是与帧率无关的纯几何量。玩家（行走正常）是基准。"""
import re
import sys
import collections

p = sys.argv[1]
rows = collections.defaultdict(list)
for ln in open(p, "rb").read().decode("utf-8", "replace").splitlines():
    if "FootCSV" not in ln:
        continue
    s = ln[ln.find("[FootCSV]"):]
    m = dict(re.findall(r"(\w+)=(-?[\d.]+)", s))
    m["leg"] = re.search(r"leg=(\S+)", s).group(1)
    rows[(re.search(r"owner=(\S+)", s).group(1), m["leg"])].append(m)

print("%-22s %-3s %8s %8s %8s" % ("owner", "leg", "slope", "r2", "n"))
print("-" * 52)
for k in sorted(rows):
    seq = rows[k]
    xs = [float(r["fwd"]) for r in seq]
    ys = [float(r["php"]) for r in seq]
    n = len(xs)
    if n < 10:
        continue
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx < 1e-6:
        continue
    sxy = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    a = sxy / sxx
    syy = sum((y - my) ** 2 for y in ys)
    r2 = (sxy * sxy) / (sxx * syy) if syy > 1e-9 else 0
    print("%-22s %-3s %8.3f %8.2f %8d" % (k[0], k[1], a, r2, n))
