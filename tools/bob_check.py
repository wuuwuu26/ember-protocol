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

print("%-22s %12s %12s" % ("owner", "hipz_std", "hipz_range"))
print("-" * 50)
for key in [("BP_RobotCharacter_C_0", "L"), ("BP_Enemy_C_5", "L"),
            ("BP_Enemy_C_8", "L"), ("BP_Enemy_C_9", "L"), ("BP_Enemy_C_7", "L")]:
    seq = [r for r in rows[key] if 2 < float(r["t"]) < 8]
    if not seq:
        continue
    h = [float(r["hipz"]) for r in seq]
    print("%-22s %12.2f %12.2f" % (key[0], statistics.pstdev(h), max(h) - min(h)))
