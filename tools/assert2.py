"""正确的断言：静止时目标点相对机体 = ankx；实际脚相对机体也应当 = ankx。
（两者都是"组件空间相对原点"的量，可以比。）
注意：C_9 缩放 0.5，fx-cx 是世界差值，必须除以缩放才回到组件空间。
"""
import re
import sys
import collections

p = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\25227\Documents\robot_game\ue\shot_r602_restore.log"
rows = collections.defaultdict(list)
for ln in open(p, "rb").read().decode("utf-8", "replace").splitlines():
    if "FootCSV" not in ln:
        continue
    s = ln[ln.find("[FootCSV]"):]
    m = dict(re.findall(r"(\w+)=(-?[\d.]+)", s))
    m["leg"] = re.search(r"leg=(\S+)", s).group(1)
    rows[(re.search(r"owner=(\S+)", s).group(1), m["leg"])].append(m)

print("%-22s %-3s %6s %8s %8s %8s %8s"
      % ("owner", "leg", "ph", "tgt_x", "foot_x", "diff", "fz/ankz"))
print("-" * 70)
for k in sorted(rows):
    seq = [r for r in rows[k] if r["st"] == "1" and 3.0 < float(r["t"]) < 3.3]
    if not seq:
        continue
    r = seq[len(seq) // 2]
    sc = float(r["sc"]) or 1.0
    tgt = float(r["tgx"])
    foot = (float(r["fx"]) - float(r["cx"])) / sc
    print("%-22s %-3s %6.2f %8.1f %8.1f %8.1f %8.2f"
          % (k[0], k[1], float(r["ph"]), tgt, foot, foot - tgt,
             float(r["fz"]) / max(float(r["ankz"]), 1e-3)))
