"""C_9 的 fx-cx = -12.6 但 tgx = 20.9。若机体有 yaw 旋转，
组件空间 X 和世界 X 就不是同一个轴。
用 AxisFwd 在**世界空间**里的表示来反推 yaw。"""
import re
from collections import defaultdict

p = r"C:\Users\25227\Documents\robot_game\ue\shot_r592_ang.log"
rows = defaultdict(list)
for ln in open(p, "rb").read().decode("utf-8", "replace").splitlines():
    if "FootCSV" not in ln:
        continue
    s = ln[ln.find("[FootCSV]"):]
    m = dict(re.findall(r"(\w+)=(-?[\d.]+)", s))
    m["leg"] = re.search(r"leg=(\S+)", s).group(1)
    rows[(re.search(r"owner=(\S+)", s).group(1), m["leg"])].append(m)

for key in [("BP_RobotCharacter_C_0", "L"), ("BP_Enemy_C_9", "L"), ("BP_Enemy_C_8", "L")]:
    seq = [r for r in rows[key] if r["st"] == "1" and 3.0 < float(r["t"]) < 3.4]
    print(key[0])
    for r in seq[:8]:
        print("   ph=%.2f fwd=%6.1f fx-cx=%7.1f fy-cy=%7.1f tgx=%6.1f tgy=%6.1f"
              % (float(r["ph"]), float(r["fwd"]),
                 float(r["fx"]) - float(r["cx"]), float(r["fy"]) - float(r["cy"]),
                 float(r["tgx"]), float(r["tgy"])))
