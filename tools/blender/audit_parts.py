"""全局部件连接检查：找出悬空 / 断开 / 孤立的部件。

判据不靠肉眼：把每台机体的所有部件当成空间中的实体，
两两求包围盒距离；一个部件如果与最近邻居也有明显间隙，就是悬空的。

⚠️ 包围盒是保守近似：斜圆柱的盒子会偏大，因此可能漏报（不会误报）。
要更精确时用 PART_AUDIT_MESH=1 走网格顶点最近距离，但慢很多。
"""
import bpy
import sys
import mathutils

_HERE = r"C:\Users\25227\Documents\robot_game\tools\blender"
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import robotlib as R
import build_enemies as B
import importlib
importlib.reload(R)
importlib.reload(B)

TOUCH = 0.012   # 允许的间隙（米）

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


def bbox(ob):
    mw = ob.matrix_world
    pts = [mw @ v.co for v in ob.data.vertices]
    mn = mathutils.Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = mathutils.Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


def gap(a, b):
    amn, amx = a
    bmn, bmx = b
    d = 0.0
    for i in range(3):
        if amx[i] < bmn[i]:
            d += (bmn[i] - amx[i]) ** 2
        elif bmx[i] < amn[i]:
            d += (amn[i] - bmx[i]) ** 2
    return d ** 0.5


report = []
for code, split_legs, split_quad in CASES:
    fn = getattr(B, code)
    R.new_scene()
    R.SPLIT_LEGS = split_legs
    R.SPLIT_QUAD = split_quad
    pal = R.Palette((0.6, 0.4, 0.2), (1.0, 0.6, 0.3), "iso_%s" % code)
    objs, label, h = fn(pal)
    items = flat(objs)
    bpy.context.view_layer.update()

    boxes = []
    for ob in items:
        try:
            boxes.append((ob.name, bbox(ob)))
        except Exception:
            pass

    n = len(boxes)
    if n < 2:
        report.append("=== %s: 部件过少" % code)
        continue

    nearest = []
    for i in range(n):
        best = 1e9
        best_j = -1
        for j in range(n):
            if i == j:
                continue
            g = gap(boxes[i][1], boxes[j][1])
            if g < best:
                best = g
                best_j = j
        nearest.append((best, boxes[i][0], boxes[best_j][0] if best_j >= 0 else "-"))

    isolated = [x for x in nearest if x[0] > TOUCH]
    isolated.sort(key=lambda t: -t[0])

    report.append("=== %-9s parts=%d  floating=%d" % (code, n, len(isolated)))
    for g, nm, nb in isolated[:20]:
        report.append("    ! %-26s nearest=%-24s gap=%.3f m" % (nm, nb, g))

open(r"C:\Users\25227\AppData\Local\Temp\opencode\isolated.txt", "w",
     encoding="utf-8").write("\n".join(report))
print("[ISO] DONE")
