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

for key in [("BP_Enemy_C_7", "L"), ("BP_Enemy_C_9", "L"), ("BP_RobotCharacter_C_0", "L")]:
    seq = [r for r in rows[key] if 2 < float(r["t"]) < 5]
    ts = [float(r["t"]) for r in seq]
    vs = []
    for i in range(1, len(ts)):
        dt = ts[i] - ts[i - 1]
        if dt <= 0 or dt > 0.05:
            continue
        dx = float(seq[i]["cx"]) - float(seq[i - 1]["cx"])
        dy = float(seq[i]["cy"]) - float(seq[i - 1]["cy"])
        vs.append(((dx * dx + dy * dy) ** 0.5) / dt)
    vs.sort()
    print("%-22s n=%3d v_med=%6.1f v_min=%6.1f v_max=%6.1f v_std=%5.1f"
          % (key[0], len(vs), statistics.median(vs), vs[0], vs[-1],
             statistics.pstdev(vs) if len(vs) > 1 else 0))
