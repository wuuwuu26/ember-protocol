"""支撑段内，脚在世界里的位移方向与机体前进方向的关系。
理想：脚世界位移 ≈ 0（钉地）。若脚位移 ≈ 机体位移，说明完全被拖动。
输出 relative = 脚位移 / 机体位移 的比值与方向夹角。"""
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
    seq = rows[key]
    segs, cur = [], []
    for r in seq:
        if float(r["t"]) < 2.0:
            continue
        if r["st"] == "1":
            cur.append(r)
        else:
            if len(cur) >= 8:
                segs.append(cur)
            cur = []
    if len(cur) >= 8:
        segs.append(cur)
    if not segs:
        continue
    s = max(segs, key=len)
    a, b = s[0], s[-1]
    fdx, fdy = float(b["fx"]) - float(a["fx"]), float(b["fy"]) - float(a["fy"])
    bdx, bdy = float(b["cx"]) - float(a["cx"]), float(b["cy"]) - float(a["cy"])
    fl = (fdx * fdx + fdy * fdy) ** 0.5
    bl = (bdx * bdx + bdy * bdy) ** 0.5
    print("%-22s %d frames body=%.1f foot=%.1f ratio=%.2f"
          % (key[0], len(s), bl, fl, fl / bl if bl > 1e-6 else -1))
