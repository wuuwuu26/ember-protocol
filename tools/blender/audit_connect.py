"""部件连通性检查：判断整台机体是不是一个整体，哪些部件是孤立岛。

做法：把部件当成图上的节点，两两求网格顶点最近距离；
距离 <= TOUCH 就认为它们物理相接，连一条边。
最后求连通分量 —— 不在主连通分量里的部件就是"悬空"的。

这比"某两个部件之间有没有缝"正确：中间有连接件也算连通。
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

TOUCH = 0.015

CASES = [
    ("patrol", False, False),
    ("hauler", False, True),
    ("colossus", False, True),
    ("gardener", True, False),
    ("weather", True, False),
    ("guard", True, False),
]


def flat(objs):
    out = []
    for o in objs:
        if isinstance(o, (list, tuple)):
            out.extend(o)
        else:
            out.append(o)
    return out


def min_dist(ka, a, kb, b):
    best = 1e9
    for p in a:
        co, idx, d = kb.find(p)
        if d < best:
            best = d
            if best <= TOUCH:
                return best
    return best


report = []
for code, sl, sq in CASES:
    fn = getattr(B, code)
    R.new_scene()
    R.SPLIT_LEGS = sl
    R.SPLIT_QUAD = sq
    pal = R.Palette((0.6, 0.4, 0.2), (1.0, 0.6, 0.3), "conn_%s" % code)
    objs, label, h = fn(pal)
    items = flat(objs)
    bpy.context.view_layer.update()

    names = []
    pts = []
    trees = []
    for ob in items:
        mw = ob.matrix_world
        p = [mw @ v.co for v in ob.data.vertices]
        if len(p) < 3:
            continue
        names.append(ob.name)
        pts.append(p)
        kd = KDTree(len(p))
        for i, q in enumerate(p):
            kd.insert(q, i)
        kd.balance()
        trees.append(kd)

    n = len(names)
    # 只在小零件之间跳过大件两两比较会很慢；n 最多 140，可接受
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(n):
        for j in range(i + 1, n):
            if find(i) == find(j):
                continue
            d = min_dist(trees[i], pts[i], trees[j], pts[j])
            if d <= TOUCH:
                union(i, j)

    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    comps = sorted(groups.values(), key=len, reverse=True)

    report.append("=== %-9s parts=%d  islands=%d" % (code, n, len(comps)))
    for k, comp in enumerate(comps):
        tag = "MAIN" if k == 0 else "ISLAND"
        sample = ", ".join(names[i] for i in comp[:6])
        if len(comp) > 6:
            sample += " ..."
        report.append("   %-7s size=%3d  %s" % (tag, len(comp), sample))

open(r"C:\Users\25227\AppData\Local\Temp\opencode\connect.txt", "w",
     encoding="utf-8").write("\n".join(report))
print("[CONN] DONE")
