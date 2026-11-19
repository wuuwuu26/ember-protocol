"""直接比较：C_9 的 cx 和组件原点的关系。
若 fx 是"骨骼世界位置 - 组件原点"（即组件空间），那么 cx 应当≈0。
但 cx=1418，说明 cx 是世界坐标，而 fx 是组件空间。
即：LocalAccumWorldPos 返回的不是世界坐标。"""
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

for key in [("BP_RobotCharacter_C_0", "L"), ("BP_Enemy_C_9", "L")]:
    seq = [r for r in rows[key] if 2 < float(r["t"]) < 2.1]
    r = seq[0]
    print(key[0])
    for f in ("fx", "fy", "fz", "cx", "cy", "bmx", "bmy", "bmz", "bx", "by", "bz", "hipx", "hipz", "ankx", "ankz"):
        print("   %-5s %10.2f" % (f, float(r[f])))
