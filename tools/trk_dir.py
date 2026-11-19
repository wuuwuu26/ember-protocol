"""trk 偏高时，看误差落在哪个方向。
用 fx-cx（世界差值）和 tgx（组件空间目标）比较 —— 但 C_9 缩放 0.5，
所以先按缩放还原。只做定性判断：误差大不大、是否集中在某条腿。"""
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

print("%-22s %-3s %8s %9s %9s %9s"
      % ("owner", "leg", "trk", "d(Draw)", "hipZ-ankZ", "fz-ankZ"))
print("-" * 70)
for k in sorted(rows):
    seq = [r for r in rows[k] if r["st"] == "1" and 3.0 < float(r["t"]) < 3.4]
    if not seq:
        continue
    r = seq[len(seq) // 2]
    print("%-22s %-3s %8.1f %9.1f %9.1f %9.1f"
          % (k[0], k[1], float(r["trk"]), float(r["Draw"]),
             float(r["hipz"]) - float(r["ankz"]),
             float(r["fz"]) - float(r["ankz"])))
