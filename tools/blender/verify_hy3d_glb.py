# -*- coding: utf-8 -*-
"""验证 Hunyuan3D 生成的 GLB：几何/尺寸/面数，并渲染一张预览。

用法（Blender）：
  blender -b --factory-startup --python verify_hy3d_glb.py -- <glb路径> <预览png路径>
"""
import bpy
import sys
import os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
GLB = argv[0] if argv else r"C:\AI\Hunyuan3D\output\pipe_junction.glb"
PREVIEW = argv[1] if len(argv) > 1 else r"C:\Users\25227\AppData\Local\Temp\opencode\hy3d_preview.png"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)

import mathutils
import math

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
tris = 0
mn = [1e9] * 3
mx = [-1e9] * 3
for o in meshes:
    o.data.calc_loop_triangles()
    tris += len(o.data.loop_triangles)
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], w[i])
            mx[i] = max(mx[i], w[i])
size = [mx[i] - mn[i] for i in range(3)]
center = [(mn[i] + mx[i]) / 2 for i in range(3)]
print("MESHES=%d TRIS=%d" % (len(meshes), tris))
print("SIZE=(%.3f, %.3f, %.3f)" % tuple(size))
print("MIN=(%.3f, %.3f, %.3f) MAX=(%.3f, %.3f, %.3f)" % (tuple(mn) + tuple(mx)))

# 灯光 + 相机 + 渲染
def add_light(loc, energy):
    d = bpy.data.lights.new("L", "AREA")
    d.energy = energy
    d.size = 4
    o = bpy.data.objects.new("L", d)
    o.location = loc
    bpy.context.collection.objects.link(o)
    return o

radius = max(size) * 1.8
add_light((center[0] + radius, center[1] - radius, center[2] + radius), 3000)
add_light((center[0] - radius, center[1] - radius * 0.5, center[2] + radius * 0.6), 1500)

world = bpy.data.worlds.new("W")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.3, 0.3, 0.32, 1.0)

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 50
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
t = mathutils.Vector((center[0] + radius * 0.9, center[1] - radius * 0.9,
                      center[2] + radius * 0.5))
cam.location = t
cam.rotation_euler = (mathutils.Vector(center) - t).to_track_quat("-Z", "Y").to_euler()

sc = bpy.context.scene
sc.render.resolution_x = 640
sc.render.resolution_y = 640
# 5.3 起 EEVEE 标识符改为 "BLENDER_EEVEE"，逐级回退兼容 5.2/5.3
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH"):
    try:
        sc.render.engine = eng
        break
    except Exception:
        continue
sc.render.filepath = PREVIEW
bpy.ops.render.render(write_still=True)
print("PREVIEW=" + PREVIEW)
print("HY3D_VERIFY_DONE")
