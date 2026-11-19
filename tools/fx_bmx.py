"""C_9 的 fx 与 bmx 差 1432cm —— 量级完全不对。
检查是否 C_9 的骨骼世界位置算错（乘了几次变换）。"""
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

for key in [("BP_RobotCharacter_C_0", "L"), ("BP_Enemy_C_5", "L"),
            ("BP_Enemy_C_8", "L"), ("BP_Enemy_C_9", "L"), ("BP_Enemy_C_7", "L")]:
    seq = [r for r in rows[key] if 2 < float(r["t"]) < 2.3]
    if not seq:
        continue
    r = seq[3]
    fx, fy, bmx, bmy = (float(r[k]) for k in ("fx", "fy", "bmx", "bmy"))
    cx, cy = float(r["cx"]), float(r["cy"])
    print("%-22s fx-bmx=%8.1f fy-bmy=%8.1f  (fx=%.1f bmx=%.1f cx=%.1f)"
          % (key[0], fx - bmx, fy - bmy, fx, bmx, cx))
