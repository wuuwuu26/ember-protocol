"""部件连接检查 v2：用射线判断"是否嵌进/贴住邻居"，避免顶点间距的误报。

对每个部件，取它的顶点；从每个顶点沿"朝最近邻部件中心"的方向反打一条射线，
如果能命中邻居的三角面，说明该顶点在邻居内部或紧贴 —— 视为连接。

判据：一个部件只要**有一个顶点落在别的部件内部**，就认为它是接上的。
这能正确处理"互相插入"的情况（顶点间距很大但实际是嵌合的）。
"""
import bpy
import sys
import mathutils
from mathutils.bvhtree import BVHTree

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


def is_inside(pt, bvh):
    """射线穿越数判定：从 pt 向 +X 打射线，穿过的面数为奇数则在内部。"""
    hits = 0
    origin = pt.copy()
    direction = mathutils.Vector((1.0, 0.0, 0.0))
    for _ in range(64):
        loc, nrm, idx, dist = bvh.ray_cast(origin, direction)
        if loc is None:
            break
        hits += 1
        origin = loc + direction * 0.0005
    return hits % 2 == 1


out = []
for code, sl, sq in CASES:
    fn = getattr(B, code)
    R.new_scene()
    R.SPLIT_LEGS = sl
    R.SPLIT_QUAD = sq
    pal = R.Palette((0.6, 0.4, 0.2), (1.0, 0.6, 0.3), "ins_%s" % code)
    objs, label, h = fn(pal)
    items = [o for o in flat(objs) if len(o.data.polygons) >= 4]
    bpy.context.view_layer.update()

    names = [o.name for o in items]
    pts = []
    bvhs = []
    for ob in items:
        mw = ob.matrix_world
        p = [mw @ v.co for v in ob.data.vertices]
        pts.append(p)
        verts = p
        polys = [list(f.vertices) for f in ob.data.polygons]
        bvhs.append(BVHTree.FromPolygons(verts, polys, all_triangles=False))

    n = len(names)
    connected = [False] * n
    connected[0] = True  # 随便挑一个当种子；后面做连通性

    # 全图边
    edges = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            hit = False
            # 抽样：最多取 60 个顶点
            step = max(1, len(pts[i]) // 60)
            for k in range(0, len(pts[i]), step):
                if is_inside(pts[i][k], bvhs[j]):
                    hit = True
                    break
            if hit:
                edges.append((i, j))

    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    comps = sorted(groups.values(), key=len, reverse=True)

    out.append("=== %-9s parts=%d edges=%d islands=%d  MAIN=%d" % (
        code, n, len(edges), len(comps), len(comps[0])))
    for k, comp in enumerate(comps):
        if k == 0:
            continue
        sample = ", ".join(names[i] for i in comp[:5])
        out.append("   ISLAND size=%3d  %s" % (len(comp), sample))

open(r"C:\Users\25227\AppData\Local\Temp\opencode\ins.txt", "w",
     encoding="utf-8").write("\n".join(out))
print("[INS] DONE")
