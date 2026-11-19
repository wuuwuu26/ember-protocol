"""与帧率无关的判据：每一步里，髋关节角变化量 / 步幅变化量。
这个比值只取决于几何（腿长、落差），与采样率无关。
玩家是基准（行走正常），其余机体与之比较。"""
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

print("%-22s %-3s %8s %8s %8s %8s" % ("owner", "leg", "fwd_pp", "php_rng", "deg/cm", "stride/L"))
print("-" * 66)
for k in sorted(rows):
    seq = rows[k]
    if len(seq) < 8:
        continue
    fw = [float(r["fwd"]) for r in seq]
    php = [float(r["php"]) for r in seq]
    pp = max(fw) - min(fw)
    rng = max(php) - min(php)
    L = abs(float(seq[0]["hipz"]) - float(seq[0]["ankz"]))
    print("%-22s %-3s %8.1f %8.1f %8.2f %8.1f%%"
          % (k[0], k[1], pp, rng, rng / pp if pp > 0.1 else 0,
             max(fw) - min(fw)) )
