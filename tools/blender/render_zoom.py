"""放大渲染指定区域，确认悬空件身份。argv: fbx out_png cx cy cz radius"""
import bpy
import sys
import math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
fbx, out_png = argv[0], argv[1]
cx, cy, cz, rad = [float(x) for x in argv[2:6]]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
for ob in bpy.context.scene.objects:
    if ob.type == 'MESH':
        if ob.name.endswith(("_LOD1", "_LOD2")):
            ob.hide_render = True
        ob.data.materials.clear()
    if ob.type == 'ARMATURE':
        ob.hide_render = True

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'OBJECT'
scene.render.resolution_x = 800
scene.render.resolution_y = 800

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 80
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
cam.location = (cx + rad * 1.6, cy - rad * 1.6, cz + rad * 0.6)
# 指向目标点
direction = Vector((cx, cy, cz)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print("ZOOM_OK", out_png)
