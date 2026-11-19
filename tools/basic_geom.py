"""最基础、最无可争议的判据：脚到**自己的髋**的距离。
- 用引擎的骨骼世界矩阵（bmx/bmy/bmz）和髋的组件空间位置换算。
- 若距离 ≈ 腿长 → 腿伸直、正常。
- 若 > 腿长 → 不可能，说明 IK 与骨骼不一致。
同时输出脚到髋的矢状分量（前/后），判断腿伸向哪边。
"""
import re
from collections import defaultdict

p = r"C:\Users\25227\Documents\robot_game\ue\shot_r599_ankleside.log"
rows = defaultdict(list)
for ln in open(p, "rb").read().decode("utf-8", "replace").splitlines():
    if "FootCSV" not in ln:
        continue
    s = ln[ln.find("[FootCSV]"):]
    m = dict(re.findall(r"(\w+)=(-?[\d.]+)", s))
    m["leg"] = re.search(r"leg=(\S+)", s).group(1)
    o = re.search(r"owner=(\S+)", s).group(1)
    rows[(o, m["leg"])].append(m)

print("%-22s %-4s %8s %8s %8s %8s" % ("owner", "leg", "hipx", "fwd_off", "feet_off", "ankx"))
print("-" * 64)
for key in [("BP_RobotCharacter_C_0", "L"), ("BP_Enemy_C_5", "L"),
            ("BP_Enemy_C_7", "L"), ("BP_Enemy_C_7", "BL"),
            ("BP_Enemy_C_8", "L"), ("BP_Enemy_C_9", "L"), ("BP_Enemy_C_9", "BL")]:
    seq = [r for r in rows[key] if 3.0 < float(r["t"]) < 3.2]
    if not seq:
        continue
    r = seq[0]
    hipx = float(r["hipx"])
    ankx = float(r["ankx"])
    # 脚相对机体的世界 X（用 fx-cx），再除以组件缩放还原到组件空间
    scale = float(r["sc"])
    feet = (float(r["fx"]) - float(r["cx"])) / scale if scale else 0
    print("%-22s %-4s %8.1f %8.1f %8.1f %8.1f"
          % (key[0], key[1], hipx, ankx - hipx, feet - hipx, ankx))
