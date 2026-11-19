"""验证 trk 的计算：如果 FW 是相对机体的位置（不是世界），
InverseTransformPosition 会把它再减一次 compLoc。"""
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
    r = [x for x in rows[key] if 2 < float(x["t"]) < 2.3][3]
    fx, fy, cx, cy = float(r["fx"]), float(r["fy"]), float(r["cx"]), float(r["cy"])
    bmx, bmy = float(r["bmx"]), float(r["bmy"])
    ankx, ankz = float(r["ankx"]), float(r["ankz"])
    tgx, tgy = float(r["tgx"]), float(r["tgy"])
    trk = float(r["trk"])
    # 假设 FW 确实是世界坐标：组件空间 x = fx - cx（无旋转）
    comp_x = fx - cx
    print("%-22s fx=%.1f cx=%.1f comp_x=%.1f bmx=%.1f" % (key[0], fx, cx, comp_x, bmx))
    print("   ankx=%.1f tgx=%.1f  |comp-anchor|=%.1f  trk=%.2f"
          % (ankx, tgx, abs(comp_x - ankx), trk))
    # 若 trk 真的等于 |comp - DbgTarget|，那 comp 应当≈tgx+hipx
    print("   |comp - (ankx+??)|: comp-ankx=%.1f  (trk 说 %.2f)"
          % (comp_x - ankx, trk))
