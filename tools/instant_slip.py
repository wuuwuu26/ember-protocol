"""支撑段内逐帧：脚在世界里的瞬时速度。
理想情况应当≈0（钉地）。平均值对得上但瞬时值大 = 支撑期内有加速/减速。"""
import re
import sys
import collections
import statistics

p = sys.argv[1]
who = sys.argv[2] if len(sys.argv) > 2 else "BP_Enemy_C_7"
leg = sys.argv[3] if len(sys.argv) > 3 else "L"

rows = []
for ln in open(p, "rb").read().decode("utf-8", "replace").splitlines():
    if "FootCSV" not in ln:
        continue
    s = ln[ln.find("[FootCSV]"):]
    if who not in s or ("leg=" + leg + " ") not in s:
        continue
    rows.append(dict(re.findall(r"(\w+)=(-?[\d.]+)", s)))

segs, cur = [], []
for r in rows:
    if r["st"] == "1":
        cur.append(r)
    else:
        if len(cur) >= 8:
            segs.append(cur)
        cur = []
if len(cur) >= 8:
    segs.append(cur)

seg = max(segs, key=len) if segs else []
print("%s %s  frames=%d" % (who, leg, len(seg)))
print("%6s %6s %8s %9s %9s" % ("t", "ph", "fwd", "foot_v", "body_v"))
for i in range(1, len(seg)):
    dt = float(seg[i]["t"]) - float(seg[i - 1]["t"])
    if dt <= 0:
        continue
    fx0, fy0 = float(seg[i - 1]["fx"]), float(seg[i - 1]["fy"])
    fx1, fy1 = float(seg[i]["fx"]), float(seg[i]["fy"])
    fv = (((fx1 - fx0) ** 2 + (fy1 - fy0) ** 2) ** 0.5) / dt
    cx0, cy0 = float(seg[i - 1]["cx"]), float(seg[i - 1]["cy"])
    cx1, cy1 = float(seg[i]["cx"]), float(seg[i]["cy"])
    bv = (((cx1 - cx0) ** 2 + (cy1 - cy0) ** 2) ** 0.5) / dt
    print("%6.3f %6.2f %8.1f %9.1f %9.1f"
          % (float(seg[i]["t"]), float(seg[i]["ph"]), float(seg[i]["fwd"]), fv, bv))
