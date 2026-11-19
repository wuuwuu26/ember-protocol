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

R.new_scene()
R.SPLIT_LEGS = True
pal = R.Palette((0.36, 0.62, 0.86), (0.45, 0.78, 1.0), "wchk")
objs, label, h = B.weather(pal)
bpy.context.view_layer.update()

def ctr(ob):
    mw = ob.matrix_world
    pts = [mw @ v.co for v in ob.data.vertices]
    mn = mathutils.Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = mathutils.Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return (mn + mx) * 0.5

out = []
for nm in ("leg_hip_L", "leg_knee_L", "part_foot_L"):
    ob = bpy.data.objects.get(nm)
    if ob:
        c = ctr(ob)
        out.append("%-14s (%.3f, %.3f, %.3f)" % (nm, c.x, c.y, c.z))
    else:
        out.append("%-14s MISSING" % nm)

# 膝偏移量
hip = ctr(bpy.data.objects.get("leg_hip_L"))
knee = ctr(bpy.data.objects.get("leg_knee_L"))
ank = ctr(bpy.data.objects.get("part_foot_L"))
out.append("knee_off applied = %.3f m (y offset)" % (knee.y - hip.y))
out.append("drop = %.3f m" % (hip.z - ank.z))
open(r"C:\Users\25227\AppData\Local\Temp\opencode\wchk.txt", "w", encoding="utf-8").write("\n".join(out))
print("[WCHK] DONE")
