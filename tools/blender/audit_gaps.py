"""精确测量关键结构连接处的间隙（用网格顶点真实距离）。

对每组"应该相连"的部件，求两者顶点集合之间的最短距离。
距离 > 1.5cm 就说明真的没接上。
标签全部用 ASCII，避免中文在日志管道里变成乱码看不出来。
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

LIMIT = 0.015


def flat(objs):
    out = []
    for o in objs:
        if isinstance(o, (list, tuple)):
            out.extend(o)
        else:
            out.append(o)
    return out


def mesh_gap(obA, obB):
    a = [obA.matrix_world @ v.co for v in obA.data.vertices]
    b = [obB.matrix_world @ v.co for v in obB.data.vertices]
    kd = KDTree(len(b))
    for i, p in enumerate(b):
        kd.insert(p, i)
    kd.balance()
    best = 1e9
    for p in a:
        co, idx, d = kd.find(p)
        if d < best:
            best = d
    return best


PAIRS = {
    "colossus": (False, True, [
        ("part_torso", "chassis_pelvis", "torso-pelvis"),
        ("chassis_pelvis", "leg_hip_L1", "pelvis-hipL1_FRONT"),
        ("chassis_pelvis", "leg_hip_L2", "pelvis-hipL2_BACK"),
        ("part_torso", "shoulder_L", "torso-shoulderL"),
        ("part_torso", "shoulder_R", "torso-shoulderR"),
        ("shoulder_L", "part_arm_L", "shoulderL-armL"),
        ("part_torso", "chassis_head", "torso-head"),
        ("part_torso", "chassis_stack_L", "torso-stackL"),
        ("part_torso", "chassis_stack_R", "torso-stackR"),
    ]),
    "guard": (True, False, [
        ("part_torso", "chassis_head", "torso-head"),
        ("part_torso", "shoulder_L", "torso-shoulderL"),
        ("part_torso", "shoulder_R", "torso-shoulderR"),
        ("part_torso", "part_arm_L", "torso-armL"),
        ("part_torso", "part_arm_R", "torso-armR"),
        ("part_torso", "leg_hip_L", "torso-hipL"),
    ]),
    "gardener": (True, False, [
        ("part_torso", "chassis_head", "torso-head"),
        ("part_torso", "shoulder_L", "torso-shoulderL"),
        ("part_torso", "part_arm_L", "torso-armL"),
        ("part_torso", "leg_hip_L", "torso-hipL"),
    ]),
    "weather": (True, False, [
        ("part_torso", "chassis_head", "torso-head"),
        ("chassis_head", "head_dishpost", "head-dishpost"),
        ("head_dishpost", "head_dish", "dishpost-dish"),
        ("part_torso", "part_arm_L", "torso-armL"),
    ]),
    "hauler": (False, True, [
        ("part_torso", "leg_hip_LF", "cargo-hipLF"),
        ("part_torso", "leg_hip_LB", "cargo-hipLB"),
        ("part_torso", "chassis_cabin", "cargo-cabin"),
    ]),
    "patrol": (False, False, [
        ("part_torso", "chassis_dome", "hull-dome"),
        ("part_torso", "part_core", "hull-core"),
    ]),
}

out = []
for code in ("colossus", "guard", "gardener", "weather", "hauler", "patrol"):
    sl, sq, pairs = PAIRS[code]
    fn = getattr(B, code)
    R.new_scene()
    R.SPLIT_LEGS = sl
    R.SPLIT_QUAD = sq
    pal = R.Palette((0.6, 0.4, 0.2), (1.0, 0.6, 0.3), "gap_%s" % code)
    objs, label, h = fn(pal)
    flat(objs)
    bpy.context.view_layer.update()
    out.append("=== %s" % code)
    for a, b, desc in pairs:
        oa = bpy.data.objects.get(a)
        ob = bpy.data.objects.get(b)
        if not oa or not ob:
            out.append("   %-22s MISSING(%s/%s)" % (desc, a, b))
            continue
        g = mesh_gap(oa, ob)
        flag = "  <<< NOT-CONNECTED" if g > LIMIT else ""
        out.append("   %-22s gap=%6.3f m%s" % (desc, g, flag))

open(r"C:\Users\25227\AppData\Local\Temp\opencode\gaps.txt", "w",
     encoding="utf-8").write("\n".join(out))
print("[GAP] DONE")
