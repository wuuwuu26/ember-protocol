"""tgx 应当 = (Ankle + Fwd + Lift + FwdLat) - Hip 的矢状分量。
即 tgx = (ankx - hipx) + fwd。
逐帧验证这条恒等式。若不成立，说明 DbgTarget 的构造有问题。"""
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

print("%-22s %-3s %9s %9s %9s %9s" % ("owner", "leg", "tgx", "expect", "resid", "fwd"))
print("-" * 66)
for k in sorted(rows):
    seq = [r for r in rows[k] if r["st"] == "1" and 3.0 < float(r["t"]) < 3.3]
    if not seq:
        continue
    r = seq[len(seq) // 2]
    expect = (float(r["ankx"]) - float(r["hipx"])) + float(r["fwd"])
    print("%-22s %-3s %9.1f %9.1f %9.1f %9.1f"
          % (k[0], k[1], float(r["tgx"]), expect,
             float(r["tgx"]) - expect, float(r["fwd"])))
