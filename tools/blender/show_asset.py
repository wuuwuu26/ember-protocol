# -*- coding: utf-8 -*-
"""Hunyuan3D 资产「带贴图展示图」渲染器（第一百一十八轮）。

加载带投影贴图的 GLB（*_tex.glb），用三点柔光 + 深色背景 + 展示地台，
渲染一张用于交付展示的 PNG。相比 verify_hy3d_glb.py 的白模预览，
这里强调贴图表现：足够的照度、纹理可见的角度、干净的背景。

用法（Blender 执行）：
  blender -b --factory-startup --python show_asset.py -- <glb> <out.png> [yaw角度]

⚠️ 必须传 *_tex.glb（含贴图）。白模 GLB 没有 UV 贴图，渲染出来是灰的。
"""
import bpy
import sys
import os
import math
import mathutils

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
GLB = argv[0] if argv else r"C:\AI\Hunyuan3D\output\airlock_tex.glb"
OUT = argv[1] if len(argv) > 1 else r"C:\Users\25227\AppData\Local\Temp\opencode\show.png"
YAW = float(argv[2]) if len(argv) > 2 else 35.0     # 展示角度（度）

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not meshes:
    print("!! 没有网格")
    raise SystemExit(1)

# ── 包围盒 / 居中 ──
mn = [1e9] * 3
mx = [-1e9] * 3
for o in meshes:
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], w[i])
            mx[i] = max(mx[i], w[i])
size = [mx[i] - mn[i] for i in range(3)]
center = mathutils.Vector([(mn[i] + mx[i]) / 2 for i in range(3)])
radius = max(size) * 0.5
print("ASSET=%s  TRIS=%d  SIZE=(%.2f, %.2f, %.2f)" % (
    os.path.basename(GLB),
    sum(len(o.data.polygons) for o in meshes),
    size[0], size[1], size[2]))

# 把模型整体移到原点附近（Z 底对齐 0），方便构图
floor_z = mn[2]
for o in meshes:
    o.location -= mathutils.Vector((center.x, center.y, floor_z))

# ── 展示地台（深色圆盘，接住阴影）──
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=radius * 1.35,
                                    depth=radius * 0.06,
                                    location=(0, 0, -radius * 0.03))
stage = bpy.context.active_object
stage.name = "Stage"
sm = bpy.data.materials.new("M_Stage")
sm.diffuse_color = (0.05, 0.06, 0.08, 1.0)
sm.use_nodes = True
bsdf = sm.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.05, 0.06, 0.08, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.7
stage.data.materials.append(sm)
# ── 三点柔光 ──
def area(name, loc, energy, size, color):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = energy
    d.size = size
    d.color = color
    o = bpy.data.objects.new(name, d)
    o.location = loc
    bpy.context.collection.objects.link(o)
    # 指向模型中心
    target = mathutils.Vector((0, 0, radius * 0.5))
    o.rotation_euler = (target - o.location).to_track_quat("-Z", "Y").to_euler()
    return o

D = radius * 3.2
area("Key", (D * 0.8, -D * 0.9, D * 1.1), 2600, D * 1.2, (1.0, 0.96, 0.90))
area("Fill", (-D * 1.0, -D * 0.4, D * 0.6), 1300, D * 1.0, (0.75, 0.85, 1.0))
area("Rim", (0.0, D * 1.1, D * 0.8), 2000, D * 0.8, (0.85, 0.92, 1.0))

# ── 深色渐变背景 ──
world = bpy.data.worlds.new("W")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.045, 0.055, 0.075, 1.0)
    bg.inputs[1].default_value = 1.0

# ── 相机：3/4 俯视 ──
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 55
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
a = math.radians(YAW)
dist = radius * 4.6
cam.location = (math.cos(a) * dist, -math.sin(a) * dist, radius * 1.5 + radius * 1.3)
look = mathutils.Vector((0, 0, radius * 0.45))
cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()

# ── 渲染设置 ──
sc = bpy.context.scene
sc.render.resolution_x = 900
sc.render.resolution_y = 900
sc.render.resolution_percentage = 100
sc.render.film_transparent = False
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH"):
    try:
        sc.render.engine = eng
        break
    except Exception:
        continue
try:
    sc.view_settings.view_transform = "AgX"
except Exception:
    try:
        sc.view_settings.view_transform = "Filmic"
    except Exception:
        pass
sc.render.filepath = OUT
# 环境光遮蔽 / 软阴影
try:
    sc.eevee.use_gtao = True
except Exception:
    pass
sc.render.image_settings.file_format = "PNG"
bpy.ops.render.render(write_still=True)
print("SHOW=" + OUT)
print("SHOW_ASSET_DONE")
