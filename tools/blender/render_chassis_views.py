"""渲染玩家底盘 FBX 的正面 / 侧面两张图（Workbench，纯几何），用于核对肩部与缺件。"""
import bpy
import sys
import math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
fbx, out_prefix = argv[0], argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)

meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for ob in meshes:
    if ob.name.endswith(("_LOD1", "_LOD2")):
        ob.hide_render = True
    ob.data.materials.clear()

for ob in bpy.context.scene.objects:
    if ob.type == 'ARMATURE':
        ob.hide_render = True

all_mesh = [o for o in meshes if not o.name.endswith(("_LOD1", "_LOD2"))]
mn = [1e9] * 3
mx = [-1e9] * 3
for ob in all_mesh:
    for c in ob.bound_box:
        w = ob.matrix_world @ Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], w[i])
            mx[i] = max(mx[i], w[i])
center = [(mn[i] + mx[i]) * 0.5 for i in range(3)]
span = max(mx[i] - mn[i] for i in range(3))

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'OBJECT'
scene.render.resolution_x = 700
scene.render.resolution_y = 900

views = {
    "front": (0.0, -span * 2.6, 0.0, 90.0, 0.0, 0.0),
    "side": (span * 2.6, 0.0, 0.0, 90.0, 0.0, 90.0),
}
for name, (dx, dy, dz, rx, ry, rz) in views.items():
    cam_data = bpy.data.cameras.new("Cam_" + name)
    cam_data.lens = 50
    cam = bpy.data.objects.new("Cam_" + name, cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (center[0] + dx, center[1] + dy, center[2] + dz)
    cam.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))
    scene.camera = cam
    scene.render.filepath = "%s_%s.png" % (out_prefix, name)
    bpy.ops.render.render(write_still=True)
    print("CHASSIS_VIEW_OK", name)
