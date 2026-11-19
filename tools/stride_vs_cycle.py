"""检查每个实体：机体一个步态周期前进多少 vs 步幅是多少。
若「周期位移」≈ 2×步幅，说明脚被拖动；若 ≈ 步幅，说明钉住了。"""
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

for key in [("BP_RobotCharacter_C_0", "L"), ("BP_Enemy_C_8", "L"),
            ("BP_Enemy_C_9", "L"), ("BP_Enemy_C_7", "L")]:
    seq = [r for r in rows[key] if 3.0 < float(r["t"]) < 3.6]
    if len(seq) < 10:
        continue
    t0, t1 = float(seq[0]["t"]), float(seq[-1]["t"])
    # 机体在周期里的平均速度
    cx0, cy0 = float(seq[0]["cx"]), float(seq[0]["cy"])
    cx1, cy1 = float(seq[-1]["cx"]), float(seq[-1]["cy"])
    v = ((cx1 - cx0) ** 2 + (cy1 - cy0) ** 2) ** 0.5 / (t1 - t0)
    fwd = [float(r["fwd"]) for r in seq]
    stride = max(fwd) - min(fwd)
    print("%-22s v=%6.1f stride=%5.1f  phase_span=%.2f"
          % (key[0], v, stride, float(seq[-1]["ph"]) - float(seq[0]["ph"]) + 1.0))
