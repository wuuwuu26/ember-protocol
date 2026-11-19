"""用三种不同的方式算"脚在组件坐标系里的位置"，看哪一种才是对的。
A: 引擎 GetBoneMatrix（组件空间，引擎自己算的）
B: InverseTransformPosition(FW)（我之前的 trk 用的）
C: FW - CompLoc（只减平移）
另外打印组件缩放。"""
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
    seq = [r for r in rows[key] if 2 < float(r["t"]) < 2.3]
    if not seq:
        continue
    print(key[0])
    print("   t     bmx-cx   (fx-cx)   bx      ankx   tgx")
    for r in seq[:6]:
        print("%5.3f %9.1f %9.1f %7.1f %6.1f %6.1f"
              % (float(r["t"]), float(r["bmx"]) - float(r["cx"]),
                 float(r["fx"]) - float(r["cx"]),
                 float(r["bx"]), float(r["ankx"]), float(r["tgx"])))
