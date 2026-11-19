"""C_9: fz-ankz = -18.3 说明脚沉到静止高度以下 18cm。
而 trk=0.01 说脚在目标点上。矛盾只能来自：目标点本身就在静止高度以下。
检查 DbgTarget 的 Z（I-K 用的目标）。"""
import re
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

for key in [("BP_RobotCharacter_C_0", "L"), ("BP_Enemy_C_9", "L"), ("BP_Enemy_C_8", "L")]:
    seq = [r for r in rows[key] if 2 < float(r["t"]) < 2.1]
    r = seq[0]
    print("%-22s lift=%.2f  fz=%.2f  ankz=%.2f  hipz=%.2f  ez=%.1f"
          % (key[0], float(r["lift"]), float(r["fz"]), float(r["ankz"]),
             float(r["hipz"]), float(r["ez"])))
