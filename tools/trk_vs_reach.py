"""找出 C_5 的 trk（跟踪误差）在什么条件下大。
把 trk 与 IK 可解因子 P = 2·L1·L2 / d 放一起看，验证"θ2 减两次导致 d 不可解"
这个假设：P 越接近 1，说明需要的膝弯越接近"腿伸直"的奇异点。"""
import re
import statistics
import sys
from collections import defaultdict

path = sys.argv[1]


def kv(line):
    return dict(re.findall(r"(\w+)=(-?[\d.]+)", line))


rows = defaultdict(list)
for ln in open(path, "rb").read().decode("utf-8", "replace").splitlines():
    if "[FootCSV]" not in ln:
        continue
    d = kv(ln[ln.find("[FootCSV]"):])
    if d.get("st") != "1":
        continue
    o = re.search(r"owner=(\S+)", ln).group(1)
    rows[o].append(d)

L1, L2 = 54.0, 48.0  # C_5 大致
for o in sorted(rows):
    rs = rows[o]
    trk = [float(r["trk"]) for r in rs]
    dd = [float(r["d"]) for r in rs]
    P = [2 * L1 * L2 / max(x, 1.0) - 1.0 for x in dd]
    z = list(zip(trk, P))
    z.sort()
    lo = [p for t, p in z[:len(z) // 3]]
    hi = [p for t, p in z[-len(z) // 3:]]
    print("%-22s n=%4d trk_med=%6.1f  P(worst)=%.2f  P(best)=%.2f"
          % (o, len(rs), statistics.median(trk),
             statistics.median(hi), statistics.median(lo)))
