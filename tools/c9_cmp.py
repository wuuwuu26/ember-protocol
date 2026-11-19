"""C_9 与玩家：同样的东西，逐项对照。目标是找出 5 倍差异的来源。"""
import re
import statistics
from collections import defaultdict

p = r"C:\Users\25227\Documents\robot_game\ue\shot_r590_OK.log"
rows = defaultdict(list)
for ln in open(p, "rb").read().decode("utf-8", "replace").splitlines():
    if "FootCSV" not in ln:
        continue
    s = ln[ln.find("[FootCSV]"):]
    m = dict(re.findall(r"(\w+)=(-?[\d.]+)", s))
    m["leg"] = re.search(r"leg=(\S+)", s).group(1)
    rows[(re.search(r"owner=(\S+)", s).group(1), m["leg"])].append(m)

fields = ["fwd", "lift", "d", "dc", "A", "K", "trk", "half", "act", "mb"]
for key in [("BP_RobotCharacter_C_0", "L"), ("BP_Enemy_C_9", "L"), ("BP_Enemy_C_8", "L")]:
    seq = [r for r in rows[key] if 2 < float(r["t"]) < 6]
    st = [r for r in seq if r["st"] == "1"]
    sw = [r for r in seq if r["st"] == "0"]
    line = "%-20s stance=%d swing=%d | " % (key[0][-14:], len(st), len(sw))
    for f in ["fwd", "lift", "d", "A", "K"]:
        line += "%s=%.1f " % (f, statistics.median([float(r[f]) for r in st]))
    print(line)
    print("   swing lift med=%.1f max=%.1f"
          % (statistics.median([float(r["lift"]) for r in sw]) if sw else -1,
             max(float(r["lift"]) for r in sw) if sw else -1))
