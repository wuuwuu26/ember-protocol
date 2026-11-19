"""C_9: 检查 SwingBone 施加的角度 vs fwd 变化。
若 P.Hip 在变，但脚没跟上，说明 fwd 被别的项抵消了。
注意 C_9 是四足，L 腿的相位与 BL 同相 —— 检查是否 L 的 fwd 被 BL 覆盖。"""
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

seq = [r for r in rows[("BP_Enemy_C_9", "L")] if r["st"] == "1" and 3.0 < float(r["t"]) < 3.5]
print("C_9 L: t, ph, fwd, fx-cx, hipx, ankx, A, K, base, trk")
for r in seq:
    print("%5.3f %5.2f %6.1f %7.1f %6.1f %6.1f %5.1f %5.1f %5.1f %5.2f"
          % (float(r["t"]), float(r["ph"]), float(r["fwd"]),
             float(r["fx"]) - float(r["cx"]), float(r["hipx"]), float(r["ankx"]),
             float(r["A"]), float(r["K"]), float(r["base"]), float(r["trk"])))
