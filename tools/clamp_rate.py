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

print("%-22s %10s %10s %10s" % ("owner", "d_max", "clamp%", "fz_std"))
print("-" * 56)
for key in [("BP_RobotCharacter_C_0", "L"), ("BP_Enemy_C_5", "L"),
            ("BP_Enemy_C_8", "L"), ("BP_Enemy_C_9", "L"), ("BP_Enemy_C_7", "L")]:
    seq = [r for r in rows[key] if r["st"] == "1" and 2 < float(r["t"]) < 8]
    if not seq:
        continue
    dmax = max(float(r["d"]) for r in seq)
    clamp = sum(1 for r in seq if abs(float(r["d"]) - float(r["dc"])) > 1.0) / len(seq) * 100
    fz = statistics.pstdev([float(r["fz"]) for r in seq])
    print("%-22s %10.1f %9.1f%% %10.2f" % (key[0], dmax, clamp, fz))
