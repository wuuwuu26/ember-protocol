"""把源 FBX 巡逻机用正面相机渲染一张图，与 UE 近景对比，判断两条腿是否来自源模型。"""
import bpy
import sys
import math

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
fbx, out_png = argv[0], argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)

for ob in bpy.context.scene.objects:
    if ob.type == 'MESH' and ob.name != "SK_Enemy_Patrol":
        ob.hide_render = True
    if ob.type == 'ARMATURE':
        ob.hide_render = True

target = bpy.data.objects.get("SK_Enemy_Patrol")
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location = (0.0, -4.0, 0.9)
cam.rotation_euler = (math.radians(88), 0.0, 0.0)
bpy.context.scene.camera = cam

sun = bpy.data.lights.new("Sun", 'SUN')
sun.energy = 3.0
sun_ob = bpy.data.objects.new("Sun", sun)
bpy.context.scene.collection.objects.link(sun_ob)
sun_ob.rotation_euler = (math.radians(50), 0, math.radians(30))

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 800
scene.render.resolution_y = 800
scene.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print("PATROL_FRONT_OK", out_png)
