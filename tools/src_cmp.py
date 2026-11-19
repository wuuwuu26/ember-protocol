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

for key in [("BP_RobotCharacter_C_0", "L"), ("BP_Enemy_C_8", "L"), ("BP_Enemy_C_9", "L")]:
    seq = [r for r in rows[key] if r["st"] == "1" and 3.0 < float(r["t"]) < 3.8]
    print(key[0])
    # 用引擎 bmx（组件空间）算脚相对机体的位移范围
    bm = [float(r["bmx"]) for r in seq]
    fx = [float(r["fx"]) for r in seq]
    tg = [float(r["tgx"]) for r in seq]
    print("   engine bmx range=%.1f   fx(localaccum) range=%.1f   tgx range=%.1f"
          % (max(bm) - min(bm), max(fx) - min(fx), max(tg) - min(tg)))
