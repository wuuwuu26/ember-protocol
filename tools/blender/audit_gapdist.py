"""统计各机体部件之间的间隙分布：判断"普遍不贴合"还是"少数断开"。

对主连通块内的部件，统计每个部件到最近邻居的距离分布。
如果中位数就很大，说明是普遍性不贴合（尺寸/位置各自估算），
不是个别部件放错。
"""
import bpy
import sys
import mathutils
from mathutils.kdtree import KDTree

_HERE = r"C:\Users\25227\Documents\robot_game\tools\blender"
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import robotlib as R
import build_enemies as B
import importlib
importlib.reload(R)
importlib.reload(B)

CASES = [("colossus", False, True), ("hauler", False, True),
         ("gardener", True, False), ("guard", True, False),
         ("weather", True, False), ("patrol", False, False)]


def flat(objs):
    out = []
    for o in objs:
        if isinstance(o, (list, tuple)):
            out.extend(o)
        else:
            out.append(o)
    return out


for code, sl, sq in CASES:
    fn = getattr(B, code)
    R.new_scene()
    R.SPLIT_LEGS = sl
    R.SPLIT_QUAD = sq
    pal = R.Palette((0.6, 0.4, 0.2), (1.0, 0.6, 0.3), "d_%s" % code)
    objs, label, h = fn(pal)
    items = [o for o in flat(objs) if len(o.data.vertices) >= 3]
    bpy.context.view_layer.update()

    pts = []
    trees = []
    names = []
    for ob in items:
        mw = ob.matrix_world
        p = [mw @ v.co for v in ob.data.vertices]
        names.append(ob.name)
        pts.append(p)
        kd = KDTree(len(p))
        for i, q in enumerate(p):
            kd.insert(q, i)
        kd.balance()
        trees.append(kd)

    n = len(names)
    nearest = []
    for i in range(n):
        best = 1e9
        for j in range(n):
            if i == j:
                continue
            for q in pts[i]:
                co, idx, d = trees[j].find(q)
                if d < best:
                    best = d
                    break
        nearest.append(best)

    s = sorted(nearest)
    med = s[len(s) // 2]
    print("%-9s parts=%3d  nearest-gap: med=%6.3f  p25=%6.3f  p75=%6.3f  max=%6.3f  "
          "<=1.5cm:%d  >5cm:%d"
          % (code, n, med, s[len(s) // 4], s[3 * len(s) // 4], s[-1],
             sum(1 for x in s if x <= 0.015), sum(1 for x in s if x > 0.05)))

print("[DIST] DONE")
