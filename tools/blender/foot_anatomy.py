"""读园丁骨架里脚部骨骼的世界坐标与脚部部件的包围盒，确认"踝骨"到"脚底"的距离。"""
import bpy
import sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
fbx = argv[0]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)

arm = None
for ob in bpy.context.scene.objects:
    if ob.type == 'ARMATURE':
        arm = ob
        break

if arm:
    for bn in ("foot_L", "foot_R", "shin_L", "thigh_L"):
        b = arm.data.bones.get(bn)
        if b:
            hw = arm.matrix_world @ b.head_local
            tw = arm.matrix_world @ b.tail_local
            print("BONE %-8s head=(%.3f,%.3f,%.3f) tail=(%.3f,%.3f,%.3f)"
                  % (bn, hw.x, hw.y, hw.z, tw.x, tw.y, tw.z))

mesh = None
for ob in bpy.context.scene.objects:
    if ob.type == 'MESH' and not ob.name.endswith(("_LOD1", "_LOD2")):
        mesh = ob
        break
if mesh:
    mn = [1e9] * 3
    mx = [-1e9] * 3
    for c in mesh.bound_box:
        w = mesh.matrix_world @ Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], w[i])
            mx[i] = max(mx[i], w[i])
    print("MESH_BOUNDS min_z=%.3f max_z=%.3f" % (mn[2], mx[2]))
print("FOOT_ANATOMY_OK")
