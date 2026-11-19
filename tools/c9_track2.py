import re
from collections import defaultdict

p = r"C:\Users\25227\Documents\robot_game\ue\shot_r591_upc.log"
rows = defaultdict(list)
for ln in open(p, "rb").read().decode("utf-8", "replace").splitlines():
    if "FootCSV" not in ln:
        continue
    s = ln[ln.find("[FootCSV]"):]
    m = dict(re.findall(r"(\w+)=(-?[\d.]+)", s))
    m["leg"] = re.search(r"leg=(\S+)", s).group(1)
    rows[(re.search(r"owner=(\S+)", s).group(1), m["leg"])].append(m)

for key in [("BP_RobotCharacter_C_0", "L"), ("BP_Enemy_C_8", "L"), ("BP_Enemy_C_9", "L")]:
    seq = [r for r in rows[key] if r["st"] == "1" and 3.0 < float(r["t"]) < 3.6]
    print(key[0], len(seq))
    print("   t    ph    fwd   bmx-cx  bmy-cy   ankx   trk")
    for r in seq[:14]:
        print("%5.3f %5.2f %6.1f %7.1f %7.1f %7.1f %6.2f"
              % (float(r["t"]), float(r["ph"]), float(r["fwd"]),
                 float(r["bmx"]) - float(r["cx"]),
                 float(r["bmy"]) - float(r["cy"]),
                 float(r["ankx"]), float(r["trk"])))
