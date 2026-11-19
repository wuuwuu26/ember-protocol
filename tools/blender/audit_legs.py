"""逐台检查腿部几何是否"首尾相接" —— 用圆柱轴向端点，不用质心。

对每个圆柱：取顶点中距离局部 Z 轴最远的两组（即两端端面），
再用各自的质心作为端点。这样斜置圆柱也能得到真实端点。
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

TOL = 6.0  # cm


def flat(objs):
    out = []
    for o in objs:
        if isinstance(o, (list, tuple)):
            out.extend(o)
        else:
            out.append(o)
    return out


def axis_ends(ob):
    """圆柱两端面中心（世界坐标）。对角：取距轴最远端 -> 沿轴分两簇。"""
    mw = ob.matrix_world
    # 局部坐标下圆柱沿 Z
    loc = [v.co for v in ob.data.vertices]
    zmin = min(p.z for p in loc)
    zmax = max(p.z for p in loc)
    lo = [p for p in loc if p.z < (zmin + zmax) * 0.5]
    hi = [p for p in loc if p.z >= (zmin + zmax) * 0.5]
    def c(ps):
        s = mathutils.Vector((0, 0, 0))
        for p in ps:
            s += p
        return s / len(ps)
    return mw @ c(lo), mw @ c(hi)


def center(ob):
    """几何中心：用包围盒中心（球/方块都准；圆柱斜置时包围盒中心也等于形心）。"""
    mw = ob.matrix_world
    pts = [mw @ v.co for v in ob.data.vertices]
    mn = mathutils.Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = mathutils.Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return (mn + mx) * 0.5


CASES = [
    ("hauler", True, False, ("LF", "LB", "RF", "RB")),
    ("colossus", False, True, ("L1", "L2", "R1", "R2")),
    ("gardener", True, False, ("L", "R")),
    ("weather", True, False, ("L", "R")),
    ("guard", True, False, ("L", "R")),
]

for code, split_legs, split_quad, tags in CASES:
    fn = getattr(B, code)
    R.new_scene()
    R.SPLIT_LEGS = split_legs
    R.SPLIT_QUAD = split_quad
    pal = R.Palette((0.6, 0.4, 0.2), (1.0, 0.6, 0.3), "a2_%s" % code)
    objs, label, h = fn(pal)
    flat(objs)
    bpy.context.view_layer.update()
    print("\n=== %s" % code)
    for tag in tags:
        thigh = bpy.data.objects.get("part_leg_%s" % tag)
        shin = bpy.data.objects.get("leg_shin_%s" % tag)
        knee = bpy.data.objects.get("leg_knee_%s" % tag)
        foot = bpy.data.objects.get("part_foot_%s" % tag)
        if not (thigh and shin and knee and foot):
            print("  [%s] 缺件" % tag)
            continue
        t_lo, t_hi = axis_ends(thigh)
        s_lo, s_hi = axis_ends(shin)
        kc = center(knee)
        fc = center(foot)
        # 大腿下端应贴近膝；小腿上端应贴近膝
        d1 = min((t_lo - kc).length, (t_hi - kc).length) * 100
        d2 = min((s_lo - kc).length, (s_hi - kc).length) * 100
        # 小腿远端（离膝最远的那端）应落在脚的正上方
        far = s_lo if (s_lo - kc).length > (s_hi - kc).length else s_hi
        d3 = mathutils.Vector((far.x - fc.x, far.y - fc.y, 0)).length * 100
        fzmin = min((foot.matrix_world @ v.co).z for v in foot.data.vertices) * 100
        flags = []
        if d1 > TOL:
            flags.append("thigh-knee=%.0f" % d1)
        if d2 > TOL:
            flags.append("shin-knee=%.0f" % d2)
        if d3 > TOL:
            flags.append("shin-foot=%.0f" % d3)
        if abs(fzmin) > 3.0:
            flags.append("footZ=%.0f" % fzmin)
        print("  [%-3s] %s" % (tag, "OK" if not flags else "!! " + ", ".join(flags)))
print("\n[LEGAUDIT] DONE")
