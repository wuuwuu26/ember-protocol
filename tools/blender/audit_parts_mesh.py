"""用真实网格顶点验证 greeble 是否真的悬空。

对每个可疑部件，求它的顶点到"其余所有部件顶点"的最近距离。
这个距离 > 阈值就是真的飘在外面。
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

TOUCH = 0.02


def flat(objs):
    out = []
    for o in objs:
        if isinstance(o, (list, tuple)):
            out.extend(o)
        else:
            out.append(o)
    return out


for code, sl, sq in [("colossus", False, True), ("hauler", False, True),
                     ("weather", True, False)]:
    fn = getattr(B, code)
    R.new_scene()
    R.SPLIT_LEGS = sl
    R.SPLIT_QUAD = sq
    pal = R.Palette((0.6, 0.4, 0.2), (1.0, 0.6, 0.3), "mesh_%s" % code)
    objs, label, h = fn(pal)
    items = flat(objs)
    bpy.context.view_layer.update()

    # 建立"全部顶点"的 KD 树（世界坐标）
    allpts = []
    owner = []
    for idx, ob in enumerate(items):
        mw = ob.matrix_world
        for v in ob.data.vertices:
            allpts.append(mw @ v.co)
            owner.append(idx)

    kd = KDTree(len(allpts))
    for i, p in enumerate(allpts):
        kd.insert(p, i)
    kd.balance()

    print("\n=== %s parts=%d verts=%d" % (code, len(items), len(allpts)))
    bad = 0
    for idx, ob in enumerate(items):
        mw = ob.matrix_world
        worst = 0.0
        for v in ob.data.vertices:
            p = mw @ v.co
            # 找最近的非自身顶点
            found = None
            for co, i2, d in kd.find_n(p, 8):
                if owner[i2] != idx:
                    found = d
                    break
            if found is not None and found > worst:
                worst = found
        if worst > TOUCH:
            bad += 1
            if bad <= 25:
                print("   ! %-26s 最远顶点间隙=%.3f m" % (ob.name, worst))
    print("   --> floating(real mesh) = %d / %d" % (bad, len(items)))

print("[MESHISO] DONE")
