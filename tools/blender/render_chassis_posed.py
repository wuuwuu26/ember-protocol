"""把玩家底盘 FBX 的左臂抬起约 45°，渲染正面，暴露抬手时肩部的断开与缺件。"""
import bpy
import sys
import math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
fbx, out_png = argv[0], argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)

arm = None
for ob in bpy.context.scene.objects:
    if ob.type == 'ARMATURE':
        arm = ob
        break

if arm:
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    for bn, deg in (("shoulder_L", -35), ("upperarm_L", -25), ("forearm_L", -20)):
        pb = arm.pose.bones.get(bn)
        if pb:
            pb.rotation_mode = 'XYZ'
            pb.rotation_euler = (math.radians(deg), 0, 0)
    bpy.ops.object.mode_set(mode='OBJECT')

for ob in bpy.context.scene.objects:
    if ob.type == 'MESH':
        if ob.name.endswith(("_LOD1", "_LOD2")):
            ob.hide_render = True
        ob.data.materials.clear()

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
scene.render.resolution_x = 700
scene.render.resolution_y = 900

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 50
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
cam.location = (center[0] + span * 2.4, center[1], center[2])
cam.rotation_euler = (math.radians(90), 0, math.radians(90))
scene.camera = cam
scene.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print("CHASSIS_POSED_OK", out_png)
