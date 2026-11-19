"""检查四足机前后腿的膝盖是否真的朝相反方向弯（骨骼层面）。"""
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
R.SPLIT_LEGS = False
R.SPLIT_QUAD = True
pal = R.Palette((0.62, 0.34, 0.30), (1.0, 0.42, 0.32), "bendchk")
objs, label, h = B.colossus(pal)

flat = []
for o in objs:
    if isinstance(o, (list, tuple)):
        flat.extend(o)
    else:
        flat.append(o)

mesh, arm, lods = R.auto_rig(objs, "Enemy_Colossus")
bpy.context.view_layer.update()

out = []
for side in ("L1", "L2", "R1", "R2"):
    hip = bpy.data.objects.get("leg_hip_%s" % side)
    knee = bpy.data.objects.get("leg_knee_%s" % side)
    thigh = bpy.data.objects.get("part_leg_%s" % side)
    if not (hip and knee and thigh):
        out.append("%s missing" % side)
        continue
    hc = sum((hip.matrix_world @ v.co for v in hip.data.vertices), mathutils.Vector()) / len(hip.data.vertices)
    kc = sum((knee.matrix_world @ v.co for v in knee.data.vertices), len(knee.data.vertices) and len(knee.data.vertices) or 1)
    out.append("%-4s hip=(%.2f,%.2f,%.2f) knee=(%.2f,%.2f,%.2f) dx=%.2f dy=%.2f"
               % (side, hc.x, hc.y, hc.z, kc.x, kc.y, kc.z, kc.x - hc.x, kc.y - hc.y))

# 骨骼层面
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
for b in arm.data.bones:
    if b.name.startswith(("thigh", "shin", "foot")):
        out.append("bone %-10s head=(%.2f,%.2f,%.2f) tail=(%.2f,%.2f,%.2f) parent=%s"
                   % (b.name, b.head_local.x, b.head_local.y, b.head_local.z,
                      b.tail_local.x, b.tail_local.y, b.tail_local.z,
                      b.parent.name if b.parent else "-"))

open(r"C:\Users\25227\AppData\Local\Temp\opencode\bendchk.txt", "w", encoding="utf-8").write("\n".join(out))
print("[BENDCHK] DONE")
