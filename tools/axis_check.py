import re
from collections import defaultdict

p = r"C:\Users\25227\Documents\robot_game\ue\shot_r592_ang.log"
rows = defaultdict(list)
for ln in open(p, "rb").read().decode("utf-8", "replace").splitlines():
    if "FootCSV" not in ln:
        continue
    s = ln[ln.find("[FootCSV]"):]
    m = dict(re.findall(r"(\w+)=(-?[\d.]+)", s))
    m["leg"] = re.search(r"leg=(\S+)", s).group(1)
    rows[(re.search(r"owner=(\S+)", s).group(1), m["leg"])].append(m)

for key in [("BP_RobotCharacter_C_0", "L"), ("BP_Enemy_C_9", "L"),
            ("BP_Enemy_C_8", "L"), ("BP_Enemy_C_5", "L")]:
    seq = [r for r in rows[key] if 3.0 < float(r["t"]) < 3.3]
    if not seq:
        continue
    r = seq[0]
    print("%-22s AxisFwd=(%.2f,%.2f,%.2f)  hipx=%.1f ankx=%.1f  tgx=%.1f"
          % (key[0], float(r["ax"]), float(r["ay"]), float(r["az"]),
             float(r["hipx"]), float(r["ankx"]), float(r["tgx"])))
