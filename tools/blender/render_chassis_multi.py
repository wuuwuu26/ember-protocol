"""渲染底盘 FBX 的侧面 / 3-4 视角（高清、Studio 光），用于检查肩部与各关节的间隙、悬空件。"""
import bpy
import sys
import math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
fbx, out_prefix = argv[0], argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)

for ob in bpy.context.scene.objects:
    if ob.type == 'MESH':
        if ob.name.endswith(("_LOD1", "_LOD2")):
            ob.hide_render = True
        ob.data.materials.clear()
    if ob.type == 'ARMATURE':
        ob.hide_render = True

meshes = [o for o in bpy.context.scene.objects
          if o.type == 'MESH' and not o.name.endswith(("_LOD1", "_LOD2"))]
mn = [1e9] * 3
mx = [-1e9] * 3
for ob in meshes:
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
scene.render.resolution_x = 900
scene.render.resolution_y = 1000

# 机体朝 X 轴：side=沿Y看（侧面），threeq=斜45°
views = {
    "side": (0.0, -span * 2.2, 0.0, 90.0, 0.0, 0.0),
    "threeq": (span * 1.7, -span * 1.7, span * 0.3, 78.0, 0.0, 45.0),
}
for name, (dx, dy, dz, rx, ry, rz) in views.items():
    cam_data = bpy.data.cameras.new("Cam_" + name)
    cam_data.lens = 60
    cam = bpy.data.objects.new("Cam_" + name, cam_data)
    scene.collection.objects.link(cam)
    cam.location = (center[0] + dx, center[1] + dy, center[2] + dz)
    cam.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))
    scene.camera = cam
    scene.render.filepath = "%s_%s.png" % (out_prefix, name)
    bpy.ops.render.render(write_still=True)
    print("MULTI_OK", name)
