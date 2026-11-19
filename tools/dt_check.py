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

for key in [("BP_RobotCharacter_C_0", "L"), ("BP_Enemy_C_9", "L")]:
    seq = [r for r in rows[key] if 2 < float(r["t"]) < 2.3]
    print(key[0])
    prev = None
    for r in seq:
        t = float(r["t"])
        if prev is not None:
            dt = t - prev
            print("  t=%.3f dt=%.4f ph=%.3f fwd=%.1f  dfwd/dt=%.0f"
                  % (t, dt, float(r["ph"]), float(r["fwd"]),
                     (float(r["fwd"]) - float(prev_fwd)) / dt if dt > 0 else 0))
        prev = t
        prev_fwd = r["fwd"]
