"""最终判据：目标点在**世界里**的移动速度，应当等于机体速度（方向相反）。
IK 无误差时，脚的世界速度 = 目标的世界速度 + 机体速度 = 0。
这里直接算 目标相对机体 的位移速度，与机体速度比较。"""
import re
import sys
import collections
import statistics

p = sys.argv[1]
rows = collections.defaultdict(list)
for ln in open(p, "rb").read().decode("utf-8", "replace").splitlines():
    if "FootCSV" not in ln:
        continue
    s = ln[ln.find("[FootCSV]"):]
    m = dict(re.findall(r"(\w+)=(-?[\d.]+)", s))
    m["leg"] = re.search(r"leg=(\S+)", s).group(1)
    rows[(re.search(r"owner=(\S+)", s).group(1), m["leg"])].append(m)

print("%-22s %-3s %9s %9s %8s" % ("owner", "leg", "body_v", "rel_v", "ratio"))
print("-" * 56)
for k in sorted(rows):
    seq = [r for r in rows[k] if r["st"] == "1" and 2 < float(r["t"]) < 8]
    bv, rv = [], []
    for i in range(1, len(seq)):
        dt = float(seq[i]["t"]) - float(seq[i - 1]["t"])
        if dt <= 0 or dt > 0.05:
            continue
        bdx = float(seq[i]["cx"]) - float(seq[i - 1]["cx"])
        bdy = float(seq[i]["cy"]) - float(seq[i - 1]["cy"])
        bv.append(((bdx * bdx + bdy * bdy) ** 0.5) / dt)
        rx0 = float(seq[i - 1]["fx"]) - float(seq[i - 1]["cx"])
        ry0 = float(seq[i - 1]["fy"]) - float(seq[i - 1]["cy"])
        rx1 = float(seq[i]["fx"]) - float(seq[i]["cx"])
        ry1 = float(seq[i]["fy"]) - float(seq[i]["cy"])
        rv.append((((rx1 - rx0) ** 2 + (ry1 - ry0) ** 2) ** 0.5) / dt)
    if not bv:
        continue
    mb, mr = statistics.median(bv), statistics.median(rv)
    print("%-22s %-3s %9.1f %9.1f %8.2f" % (k[0], k[1], mb, mr, mr / mb if mb else 0))
