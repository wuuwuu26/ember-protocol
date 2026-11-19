"""检查腿部三段（大腿/小腿/脚）在各机体里的连接情况，用网格顶点真实距离。"""
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


def flat(objs):
    out = []
    for o in objs:
        if isinstance(o, (list, tuple)):
            out.extend(o)
        else:
            out.append(o)
    return out


def gap(a, b):
    pa = [a.matrix_world @ v.co for v in a.data.vertices]
    pb = [b.matrix_world @ v.co for v in b.data.vertices]
    kd = KDTree(len(pb))
    for i, p in enumerate(pb):
        kd.insert(p, i)
    kd.balance()
    best = 1e9
    for p in pa:
        co, idx, d = kd.find(p)
        if d < best:
            best = d
    return best


CASES = [
    ("colossus", False, True, [("part_leg_L1", "leg_shin_L1", "thigh-shin"),
                               ("leg_shin_L1", "part_foot_L1", "shin-foot"),
                               ("leg_shin_L1", "foot_toe_L1", "shin-toe")]),
    ("hauler", False, True, [("part_leg_LF", "leg_shin_LF", "thigh-shin"),
                             ("leg_shin_LF", "part_foot_LF", "shin-foot")]),
    ("gardener", True, False, [("part_leg_L", "leg_shin_L", "thigh-shin"),
                               ("leg_shin_L", "part_foot_L", "shin-foot")]),
    ("guard", True, False, [("part_leg_L", "leg_shin_L", "thigh-shin"),
                            ("leg_shin_L", "part_foot_L", "shin-foot")]),
    ("weather", True, False, [("part_leg_L", "leg_shin_L", "thigh-shin"),
                              ("leg_shin_L", "part_foot_L", "shin-foot")]),
]

out = []
for code, sl, sq, pairs in CASES:
    fn = getattr(B, code)
    R.new_scene()
    R.SPLIT_LEGS = sl
    R.SPLIT_QUAD = sq
    pal = R.Palette((0.6, 0.4, 0.2), (1.0, 0.6, 0.3), "lg_%s" % code)
    objs, label, h = fn(pal)
    flat(objs)
    bpy.context.view_layer.update()
    out.append("=== %s" % code)
    for a, b, desc in pairs:
        oa = bpy.data.objects.get(a)
        ob = bpy.data.objects.get(b)
        if not oa or not ob:
            out.append("   %-14s MISSING(%s/%s)" % (desc, a, b))
            continue
        g = gap(oa, ob)
        flag = "  <<< GAP" if g > 0.015 else ""
        out.append("   %-14s gap=%6.3f m%s" % (desc, g, flag))

open(r"C:\Users\25227\AppData\Local\Temp\opencode\legs_gap.txt", "w",
     encoding="utf-8").write("\n".join(out))
print("[LG] DONE")
