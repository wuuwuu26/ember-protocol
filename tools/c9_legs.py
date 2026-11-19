"""关键：C_9 组件缩放 0.5。InverseTransformPosition 会除以 0.5（放大 2 倍）。
所以 trk 里 (FW - 目标) 的量级被放大了 2 倍，但依然是同一个向量。
如果 trk 真的 0.01，那 FW 换算后必须≈目标。
但 fx-cx 显示脚在动、目标也在动，两者之差 6.9cm。
→ 检查 trk 用的是不是**别的骨骼**。C_9 的 L 与 BL 同相；
  若 trk 用了 BL 的目标去比 L 的脚，就会错位。"""
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

for leg in ["L", "R", "BL", "BR"]:
    seq = [r for r in rows[("BP_Enemy_C_9", leg)] if r["st"] == "1" and 3.0 < float(r["t"]) < 3.4]
    if not seq:
        continue
    fwd = [float(r["fwd"]) for r in seq]
    relx = [float(r["fx"]) - float(r["cx"]) for r in seq]
    print("%-3s fwd %.1f→%.1f (Δ%.1f)   relx %.1f→%.1f (Δ%.1f)  trk=%.2f"
          % (leg, fwd[0], fwd[-1], fwd[-1] - fwd[0], relx[0], relx[-1],
             relx[-1] - relx[0], float(seq[-1]["trk"])))
