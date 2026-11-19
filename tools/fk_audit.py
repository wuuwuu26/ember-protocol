"""C_9 的脚比静止低 18cm。检查 d (髋到目标距离) 与踝的竖直落差是否被压缩。
腿长 L1+L2=176.7，若 d=166.2，则竖直落差 = sqrt(166.2^2 - fwd^2) ≈ 165.8。
但实际 hipz-ankz = 206.8 - 41.0 = 165.8 —— 一致。
所以目标高度是对的，是**实际脚位**低了 18cm。即 IK 施加的角度没把脚放到目标。
→ 用正解验证：p.Hip/p.Knee 施加后脚落到哪。"""
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

for key in [("BP_RobotCharacter_C_0", "L"), ("BP_Enemy_C_8", "L"),
            ("BP_Enemy_C_9", "L"), ("BP_Enemy_C_5", "L")]:
    seq = [r for r in rows[key] if 2 < float(r["t"]) < 2.1]
    r = seq[0]
    print("%-20s A=%5.1f K=%5.1f base=%6.1f d2=%7.2f fke=%6.2f trk=%5.2f fz-ankz=%6.2f"
          % (key[0][-16:], float(r["A"]), float(r["K"]), float(r["base"]),
             float(r["d2"]), float(r["fke"]), float(r["trk"]),
             float(r["fz"]) - float(r["ankz"])))
