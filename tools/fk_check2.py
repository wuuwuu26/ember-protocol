"""给定 P.Hip / P.Knee 和静止腿形，正解算脚最终落在哪。
与目标对比。这是唯一不依赖任何坐标系的判据。"""
import re
import sys
import collections
import math

p = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\25227\Documents\robot_game\ue\shot_r602_restore.log"
rows = collections.defaultdict(list)
for ln in open(p, "rb").read().decode("utf-8", "replace").splitlines():
    if "FootCSV" not in ln:
        continue
    s = ln[ln.find("[FootCSV]"):]
    m = dict(re.findall(r"(\w+)=(-?[\d.]+)", s))
    m["leg"] = re.search(r"leg=(\S+)", s).group(1)
    rows[(re.search(r"owner=(\S+)", s).group(1), m["leg"])].append(m)

print("%-22s %-3s %7s %7s %7s %8s %8s %8s"
      % ("owner", "leg", "php", "pkn", "tgx", "fk_x", "fk_z", "err"))
print("-" * 78)
for k in sorted(rows):
    seq = [r for r in rows[k] if r["st"] == "1" and 3.0 < float(r["t"]) < 3.3]
    if not seq:
        continue
    r = seq[len(seq) // 2]
    hipx, hipz = float(r["hipx"]), float(r["hipz"])
    ankx, ankz = float(r["ankx"]), float(r["ankz"])
    php, pkn = float(r["php"]), float(r["pkn"])
    # 静止向量（组件 x,z）
    v1 = (ankx - hipx, 0)  # 占位
    # 用 knee 位置不可得，用简化：假设大腿长 = 骨长比例
    # 直接用 A/K/d 重建
    d = float(r["Draw"])
    base = float(r["base"])
    A = float(r["A"])
    K = float(r["K"])
    bs = float(r["bs"])
    th1 = base + A * bs
    th2 = th1 - K * bs
    # 腿总长
    L = math.hypot(ankx - hipx, ankz - hipz)
    fx = hipx + L * math.sin(math.radians(th1)) + 0
    fz = hipz - L * math.cos(math.radians(th1))
    print("%-22s %-3s %7.1f %7.1f %7.1f %8.1f %8.1f"
          % (k[0], k[1], php, pkn, float(r["tgx"]), fx, fz))
