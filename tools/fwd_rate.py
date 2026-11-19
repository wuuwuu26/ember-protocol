"""C_9：拆解 支撑期脚后移速度 = 2*Half / (Duty*T)。
Half = Stride/2*MoveBlend，Stride = GaitSpeed*Duty*T。
所以理论后移速度 = GaitSpeed * MoveBlend * (dFwd/dU 的比例)。
实际测得 49.4 而 GaitSpeed=108。差在哪个环节？
"""
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

for key in [("BP_RobotCharacter_C_0", "L"), ("BP_Enemy_C_9", "L"), ("BP_Enemy_C_8", "L")]:
    seq = [r for r in rows[key] if 2 < float(r["t"]) < 6 and r["st"] == "1"]
    # 取一个完整支撑段，算 dfwd/dt
    segs, cur = [], []
    for r in seq:
        cur.append(r)
    # 直接算整段
    dfwd = []
    for i in range(1, len(seq)):
        dt = float(seq[i]["t"]) - float(seq[i - 1]["t"])
        if dt <= 0 or dt > 0.05:
            continue
        dfwd.append((float(seq[i]["fwd"]) - float(seq[i - 1]["fwd"])) / dt)
    dfwd.sort()
    act = statistics.median([float(r["act"]) for r in seq])
    hf = statistics.median([float(r["half"]) for r in seq])
    print("%-22s act=%6.1f half=%5.1f dfwd/dt=%7.1f  (should be -act)"
          % (key[0], act, hf, statistics.median(dfwd)))
