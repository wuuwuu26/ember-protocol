"""在 Blender 里渲染模型的四个方向，确定哪一面是"正面"。

为什么要在这里做：UE 截图一次要跑几分钟，而 Blender 后台渲染只需几秒。
判定正面后，再回到 UE 里设一个 yaw 就定了。
"""
import bpy
import math
import os

GLB = r"C:\Users\25227\Documents\robot_game\art_src\idol\IdolMech.glb"
OUT_DIR = r"C:\Users\25227\Documents\robot_game\docs\idol_views"

os.makedirs(OUT_DIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)

# 计算整体包围盒
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
mn = [1e9] * 3
mx = [-1e9] * 3
for o in objs:
    for c in o.bound_box:
        w = o.matrix_world @ __import__("mathutils").Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], w[i])
            mx[i] = max(mx[i], w[i])
center = [(mn[i] + mx[i]) / 2 for i in range(3)]
size = [mx[i] - mn[i] for i in range(3)]
radius = max(size) * 1.6
print("center=%s size=%s" % (center, size))

# 灯光：三点光，保证能看清朝向与细节
def add_light(loc, energy, kind="AREA", size_=2.0):
    d = bpy.data.lights.new("L", kind)
    d.energy = energy
    if kind == "AREA":
        d.size = size_
    o = bpy.data.objects.new("L", d)
    o.location = loc
    bpy.context.collection.objects.link(o)
    return o

add_light((center[0] + radius, center[1] - radius, center[2] + radius * 0.8), 3000, "AREA", radius)
add_light((center[0] - radius, center[1] - radius * 0.6, center[2] + radius * 0.5), 1200, "AREA", radius)
add_light((center[0], center[1] + radius, center[2] + radius * 0.6), 1500, "AREA", radius)

# 世界背景（浅灰，便于看轮廓）
world = bpy.data.worlds.new("W")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.18, 0.20, 0.24, 1.0)
    bg.inputs[1].default_value = 1.0

# 相机
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 60
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam

scene = bpy.context.scene
scene.render.resolution_x = 640
scene.render.resolution_y = 640
scene.render.film_transparent = False
# Blender 5.3 起 EEVEE 引擎标识符从 "BLENDER_EEVEE_NEXT" 改回
# "BLENDER_EEVEE"；这里按"新名 -> 旧名 -> Workbench"逐级回退，
# 同时兼容 5.2 与 5.3。
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH"):
    try:
        scene.render.engine = eng
        break
    except Exception:
        continue

# 四个方向：+X / -X / +Y / -Y（俯视角度看模型）
views = [
    ("front_posX", (1, 0)),
    ("back_negX", (-1, 0)),
    ("side_posY", (0, 1)),
    ("side_negY", (0, -1)),
]

import mathutils

for name, (dx, dy) in views:
    t = mathutils.Vector((center[0] + dx * radius, center[1] + dy * radius,
                          center[2] + radius * 0.18))
    cam.location = t
    direction = mathutils.Vector(center) - t
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(OUT_DIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("rendered", name)

print("IDOL_VIEWS_DONE")
