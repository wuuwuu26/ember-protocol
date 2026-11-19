"""对比 静止参考 与 实际脚位（用引擎骨骼矩阵 bx/by，这是可靠的）。
C_9: bx = bmx - cx，是相对组件（未旋转时）的 X。
若 bx 与 ankx 差很多，说明 IK 的目标基准（Rest.Ankle）与实际静止姿势不一致。"""
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
    o = re.search(r"owner=(\S+)", s).group(1)
    rows[(o, m["leg"])].append(m)

print("%-24s %8s %8s %8s %8s" % ("owner/leg", "ankx", "bx", "hipx", "bx-hipx"))
print("-" * 60)
for key in [("BP_RobotCharacter_C_0", "L"), ("BP_Enemy_C_5", "L"),
            ("BP_Enemy_C_8", "L"), ("BP_Enemy_C_9", "L"),
            ("BP_Enemy_C_9", "BL"), ("BP_Enemy_C_7", "L"), ("BP_Enemy_C_7", "BL")]:
    seq = [r for r in rows[key] if 2 < float(r["t"]) < 2.1]
    if not seq:
        continue
    r = seq[0]
    bx, hipx = float(r["bx"]), float(r["hipx"])
    print("%-24s %8.1f %8.1f %8.1f %8.1f"
          % (key[0][-14:] + "/" + key[1], float(r["ankx"]), bx, hipx, bx - hipx))
