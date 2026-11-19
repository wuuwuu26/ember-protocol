"""用完整的一次运行，统计每个实体：
- fwd 在支撑期的变化率 dFwd/dt（应当等于 -机体速度）
- 脚相对机体的位移速度 |d(rel)/dt|（应当等于 机体速度）
两者的比值直接说明"脚有没有跟上步态"。"""
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

print("%-22s %9s %9s %9s %7s" % ("owner", "body_v", "dfwd/dt", "drel/dt", "ratio"))
print("-" * 62)
for key in [("BP_RobotCharacter_C_0", "L"), ("BP_Enemy_C_5", "L"),
            ("BP_Enemy_C_8", "L"), ("BP_Enemy_C_9", "L"), ("BP_Enemy_C_7", "L")]:
    seq = [r for r in rows[key] if r["st"] == "1" and 2 < float(r["t"]) < 6]
    dfwd, drel, bv = [], [], []
    for i in range(1, len(seq)):
        dt = float(seq[i]["t"]) - float(seq[i - 1]["t"])
        if dt <= 0 or dt > 0.05:
            continue
        dfwd.append((float(seq[i]["fwd"]) - float(seq[i - 1]["fwd"])) / dt)
        rx0 = float(seq[i - 1]["fx"]) - float(seq[i - 1]["cx"])
        ry0 = float(seq[i - 1]["fy"]) - float(seq[i - 1]["cy"])
        rx1 = float(seq[i]["fx"]) - float(seq[i]["cx"])
        ry1 = float(seq[i]["fy"]) - float(seq[i]["cy"])
        drel.append((((rx1 - rx0) ** 2 + (ry1 - ry0) ** 2) ** 0.5) / dt)
        bdx = float(seq[i]["cx"]) - float(seq[i - 1]["cx"])
        bdy = float(seq[i]["cy"]) - float(seq[i - 1]["cy"])
        bv.append(((bdx * bdx + bdy * bdy) ** 0.5) / dt)
    if not dfwd:
        continue
    mb_ = statistics.median(bv)
    print("%-22s %9.1f %9.1f %9.1f %7.2f"
          % (key[0], mb_, statistics.median(dfwd), statistics.median(drel),
             statistics.median(drel) / mb_ if mb_ else 0))
