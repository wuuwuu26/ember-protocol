"""逐帧验证：支撑期脚在**组件坐标系**里的位移速度，应当与机体世界速度相等
（这样才能在世界里静止）。这里直接算两者，比较。"""
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

print("%-22s %9s %9s %9s" % ("owner", "body_v", "foot_rel_v", "ratio"))
print("-" * 54)
for key in [("BP_RobotCharacter_C_0", "L"), ("BP_Enemy_C_5", "L"),
            ("BP_Enemy_C_8", "L"), ("BP_Enemy_C_9", "L"), ("BP_Enemy_C_7", "L")]:
    seq = [r for r in rows[key] if 2 < float(r["t"]) < 6 and r["st"] == "1"]
    fv, bv = [], []
    for i in range(1, len(seq)):
        dt = float(seq[i]["t"]) - float(seq[i - 1]["t"])
        if dt <= 0 or dt > 0.05:
            continue
        # 脚相对机体的位移速度
        rx0 = float(seq[i - 1]["fx"]) - float(seq[i - 1]["cx"])
        ry0 = float(seq[i - 1]["fy"]) - float(seq[i - 1]["cy"])
        rx1 = float(seq[i]["fx"]) - float(seq[i]["cx"])
        ry1 = float(seq[i]["fy"]) - float(seq[i]["cy"])
        fv.append((((rx1 - rx0) ** 2 + (ry1 - ry0) ** 2) ** 0.5) / dt)
        # 机体速度
        bdx = float(seq[i]["cx"]) - float(seq[i - 1]["cx"])
        bdy = float(seq[i]["cy"]) - float(seq[i - 1]["cy"])
        bv.append(((bdx * bdx + bdy * bdy) ** 0.5) / dt)
    if not fv:
        continue
    mf, mb = statistics.median(fv), statistics.median(bv)
    print("%-22s %9.1f %9.1f %9.2f" % (key[0], mb, mf, mf / mb if mb else 0))
