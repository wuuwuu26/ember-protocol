"""断言式校验：同一帧里
  目标点相对髋 = DbgTarget - DbgHip   （组件空间）
  实际脚相对髋 = 脚组件空间 - 髋组件空间
两者应当相等（IK 就是干这个的）。
这里用踝的静止值 + Fwd 重建目标，与实测脚位比较。"""
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

print("%-22s %-3s %9s %9s %9s %9s" % ("owner", "leg", "tgt_rel", "foot_rel", "diff", "trk"))
print("-" * 66)
for k in sorted(rows):
    seq = [r for r in rows[k] if r["st"] == "1" and 3.0 < float(r["t"]) < 3.4]
    if not seq:
        continue
    r = seq[len(seq) // 2]
    # 目标点相对髋（x 分量）
    tgt = float(r["tgx"]) - float(r["hipx"])
    # 实际脚相对髋：脚在组件空间的 x。C_9 缩放 0.5，fx-cx 已是世界差值，
    # 引擎 bmx 是组件空间骨骼原点 —— 但两者坐标系不同，这里只用 fx-cx 的相对值
    foot = float(r["fx"]) - float(r["cx"])
    print("%-22s %-3s %9.1f %9.1f %9.1f %9.1f"
          % (k[0], k[1], tgt, foot, foot - tgt, float(r["trk"])))
