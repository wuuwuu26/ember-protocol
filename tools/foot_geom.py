import re
import statistics
import sys
from collections import defaultdict

path = sys.argv[1]


def kv(line):
    return dict(re.findall(r"(\w+)=(-?[\d.]+)", line))


g = defaultdict(list)
for ln in open(path, "rb").read().decode("utf-8", "replace").splitlines():
    if "[FootCSV]" not in ln:
        continue
    d = kv(ln[ln.find("[FootCSV]"):])
    if not d:
        continue
    owner = re.search(r"owner=(\S+)", ln).group(1)
    g[owner].append(d)

print("%-22s %9s %9s %9s %9s" % ("owner", "foot_dx", "foot_dz", "footdist", "tgtx"))
print("-" * 66)
for o in sorted(g):
    rows = [r for r in g[o] if r.get("st") == "1"]
    if not rows:
        continue
    dx = [float(r["fx"]) - float(r["cx"]) - float(r["hipx"]) for r in rows]
    dz = [float(r["fz"]) - float(r["hipz"]) for r in rows]
    hyp = [(a * a + b * b) ** 0.5 for a, b in zip(dx, dz)]
    tgx = [float(r["tgx"]) for r in rows]
    print("%-22s %9.1f %9.1f %9.1f %9.1f"
          % (o, statistics.median(dx), statistics.median(dz),
             statistics.median(hyp), statistics.median(tgx)))
