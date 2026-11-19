"""检查导出的 FBX 里到底有没有肩甲。

用法:
    blender -b --python inspect_fbx.py -- assets/out/chassis_light.fbx docs/tmp/fbx_light_front.png
"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
fbx = os.path.abspath(argv[0])
out = os.path.abspath(argv[1]) if len(argv) > 1 else os.path.abspath(
    "docs/tmp/fbx_light_front.png")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx, global_scale=1.0, use_anim=False)

meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
print("FBX_MESHES %d" % len(meshes))
for ob in meshes:
    vg = [g.name for g in ob.vertex_groups]
    idx = {g.index for g in ob.vertex_groups
           if "shoulder" in g.name.lower()}
    cnt = 0
    if idx:
        for v in ob.data.vertices:
            if any(g.group in idx and g.weight > 0.0 for g in v.groups):
                cnt += 1
    print("FBX_MESH %-34s verts=%-7d tris=%-7d groups=%-3d shoulder_verts=%d"
          % (ob.name, len(ob.data.vertices), len(ob.data.polygons), len(vg), cnt))
    sh = [n for n in vg if "shoulder" in n.lower() or "arm" in n.lower()]
    if sh:
        print("FBX_GROUPS %s" % ",".join(sh))

# 只框 LOD0
lod0 = [o for o in meshes if "LOD" not in o.name.upper()]
if not lod0:
    lod0 = meshes
mn = Vector((1e18, 1e18, 1e18))
mx = Vector((-1e18, -1e18, -1e18))
for ob in lod0:
    for c in ob.bound_box:
        w = ob.matrix_world @ Vector(c)
        mn = Vector((min(mn[i], w[i]) for i in range(3)))
        mx = Vector((max(mx[i], w[i]) for i in range(3)))
center = (mn + mx) * 0.5
height = max(mx.z - mn.z, 1e-3)
print("FBX_BOUNDS min=%s max=%s height=%.3f" % (mn, mx, height))

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 50
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
dist = height * 2.6
view = argv[2].lower() if len(argv) > 2 else "side"
if view in ("front", "back"):
    # 机体面向 +X；front 相机在 +X 侧，back 在 -X 侧。
    sx = 1.0 if view == "front" else -1.0
    cam.location = (center.x + sx * dist, center.y, center.z + height * 0.02)
    cam.rotation_euler = (math.radians(90), 0, math.radians(90) * sx)
else:
    cam.location = (center.x, center.y - dist, center.z + height * 0.02)
    cam.rotation_euler = (math.radians(90), 0, 0)
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (0.62, 0.65, 0.70)
sc.display.shading.background_type = 'VIEWPORT'
sc.display.shading.background_color = (0.035, 0.04, 0.05)
sc.display.shading.show_cavity = True
sc.display.shading.cavity_type = 'BOTH'
sc.render.resolution_x = 760
sc.render.resolution_y = 760
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = out
os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.ops.render.render(write_still=True)
print("FBX_RENDER %s" % out)
