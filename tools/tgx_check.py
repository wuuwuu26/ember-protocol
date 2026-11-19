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
    seq = [r for r in rows[key] if 2 < float(r["t"]) < 4]
    print(key[0])
    print("   t    ph   fwd   tgx   tgy   hipx  ankx  trk   fx-cx")
    for r in seq[:20]:
        print("%5.3f %5.2f %6.1f %6.1f %6.1f %6.1f %6.1f %5.2f %7.1f"
              % (float(r["t"]), float(r["ph"]), float(r["fwd"]), float(r["tgx"]),
                 float(r["tgy"]), float(r["hipx"]), float(r["ankx"]), float(r["trk"]),
                 float(r["fx"]) - float(r["cx"])))
