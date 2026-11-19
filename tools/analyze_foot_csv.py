"""离线统计"支撑脚真实滑移"。

输入：游戏日志里的 [FootCSV] 行（每帧每条腿一行）。
判据：
  把同一条腿的**连续支撑帧**切成一段（stance segment），
  这一段里脚的世界 XY 位置应当几乎不动。
  segment_slip = max(段内相对于段首的位移) / 段时长
  这样得到的是"支撑期脚在地上蹭了多快"，与窗口/相位无关。
"""
import re
import statistics
import sys
from collections import defaultdict

path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\25227\Documents\robot_game\ue\shot_r545_csv.log"

pat = re.compile(
    r"\[FootCSV\] owner=(\S+) leg=(\S+) t=([\d.]+) st=(\d) ph=(-?[\d.]+) "
    r"fwd=(-?[\d.]+) lift=(-?[\d.]+) fz=(-?[\d.]+) fx=(-?[\d.]+) fy=(-?[\d.]+) "
    r"cx=(-?[\d.]+) cy=(-?[\d.]+)")

rows = defaultdict(list)   # (owner, leg) -> [(t, stance, fx, fy)]
with open(path, "rb") as f:
    for ln in f.read().decode("latin-1", "replace").splitlines():
        m = pat.search(ln)
        if not m:
            continue
        owner, leg = m.group(1), m.group(2)
        rows[(owner, leg)].append((
            float(m.group(3)), int(m.group(4)),
            float(m.group(9)), float(m.group(10))))

print("%-24s %-4s %6s %8s %8s %8s" % ("owner", "leg", "segs", "slip_med", "slip_p90", "dur_med"))
print("-" * 68)

for (owner, leg), seq in sorted(rows.items()):
    seq.sort()
    segs = []
    cur = []
    for t, st, fx, fy in seq:
        if st == 1:
            cur.append((t, fx, fy))
        else:
            if len(cur) >= 5:
                segs.append(cur)
            cur = []
    if len(cur) >= 5:
        segs.append(cur)

    slips = []
    durs = []
    for seg in segs:
        x0, y0 = seg[0][1], seg[0][2]
        worst = 0.0
        for t, x, y in seg:
            d = ((x - x0) ** 2 + (y - y0) ** 2) ** 0.5
            worst = max(worst, d)
        dur = seg[-1][0] - seg[0][0]
        if dur > 0.02:
            slips.append(worst / dur)
            durs.append(dur)

    if not slips:
        print("%-24s %-4s %6d %8s %8s %8s" % (owner, leg, 0, "-", "-", "-"))
        continue
    slips.sort()
    p90 = slips[int(len(slips) * 0.9)] if len(slips) > 1 else slips[0]
    print("%-24s %-4s %6d %8.1f %8.1f %8.3f"
          % (owner, leg, len(slips), statistics.median(slips), p90,
             statistics.median(durs)))
