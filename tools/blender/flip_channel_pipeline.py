"""FLIP Fluids 管线验证：水渠形域 -> 无头烘焙 -> 导 Alembic -> 渲 3 帧。

目的：证明"FLIP 流体 -> 烘焙 -> UE 可用数据(Alembic 网格序列) + 可视"整条链路
在 Blender 5.2.2 + FLIP Fluids demo 下跑得通。水印只影响最终成品，不影响验证。
"""
import bpy
import addon_utils
import os
import math

OUT = r"C:\Users\25227\AppData\Local\Temp\opencode"
CACHE = os.path.join(OUT, "flip_cache")
BLEND = os.path.join(OUT, "flip_channel.blend")
ABC = os.path.join(OUT, "flip_channel_v2.abc")
if os.path.isdir(CACHE):
    import shutil
    shutil.rmtree(CACHE, ignore_errors=True)
os.makedirs(CACHE, exist_ok=True)

addon_utils.enable("flip_fluids_addon", default_set=True, persistent=True)

# 清场
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 60


def add_box(name, loc, dim):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (dim[0], dim[1], dim[2])
    bpy.ops.object.transform_apply(scale=True)
    return ob


def make_flip(ob, otype):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.flip_fluid_operators.flip_fluid_add()
    ob.flip_fluid.object_type = otype
    return ob


# ---- 域：6m(X) x 1.5m(Y) x 1.0m(Z)，底面 z=0 ----
domain = add_box("ChannelDomain", (0.0, 0.0, 0.5), (6.0, 1.5, 1.0))
make_flip(domain, 'TYPE_DOMAIN')

# ---- 初始水体：渠底一层薄水 ----
fluid = add_box("Fluid", (0.0, 0.0, 0.10), (5.6, 1.2, 0.18))
make_flip(fluid, 'TYPE_FLUID')

# ---- 入水口：-X 端，持续向 +X 注水 ----
inflow = add_box("Inflow", (-2.55, 0.0, 0.30), (0.25, 1.1, 0.5))
make_flip(inflow, 'TYPE_INFLOW')
ip = inflow.flip_fluid.get_property_group()
ip.inflow_velocity = (2.2, 0.0, 0.0)
ip.is_enabled = True
inflow.keyframe_insert(data_path="flip_fluid.inflow.is_enabled", frame=1)
inflow.keyframe_insert(data_path="flip_fluid.inflow.is_enabled", frame=60)

# ---- 出水口：+X 端，删水形成贯通流 ----
outflow = add_box("Outflow", (2.75, 0.0, 0.30), (0.3, 1.3, 0.7))
make_flip(outflow, 'TYPE_OUTFLOW')

# ---- 障碍：渠中一根立柱，制造湍流/尾流 ----
WITH_PILLAR = False
if WITH_PILLAR:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=0.9,
                                        location=(0.4, 0.0, 0.45))
    obs = bpy.context.active_object
    obs.name = "Pillar"
    make_flip(obs, 'TYPE_OBSTACLE')

# ---- 域参数 ----
dprops = scene.flip_fluid.get_domain_properties()
dprops.cache.cache_directory = CACHE
dprops.simulation.resolution = 48
dprops.simulation.frame_start = 1
dprops.simulation.frame_end = 60
try:
    dprops.materials.surface_material = 'FF Water (ocean volumetric)'
except Exception as e:
    print("[ff] 表面材质设置跳过:", e)

bpy.ops.object.select_all(action='DESELECT')
domain.select_set(True)
bpy.context.view_layer.objects.active = domain

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("[ff] 场景已保存", BLEND)

# ---- 烘焙（同步、非模态） ----
print("[ff] 开始烘焙 ...")
res = bpy.ops.flip_fluid_operators.bake_fluid_simulation_cmd()
print("[ff] 烘焙返回", res)
print("[ff] 已烘帧数", dprops.bake.num_baked_frames)

# ---- 导出 Alembic（只导流体表面） ----
surf = dprops.mesh_cache.surface.get_cache_object()
print("[ff] 表面对象", surf.name if surf else None)
if surf:
    bpy.ops.object.select_all(action='DESELECT')
    surf.select_set(True)
    bpy.context.view_layer.objects.active = surf
    exported = False
    for kw in ({"selected_objects_only": True}, {"use_selection": True},
               {"selected": True}):
        try:
            bpy.ops.wm.alembic_export(filepath=ABC, start=1, end=60, **kw)
            exported = True
            print("[ff] Alembic 导出成功 kw=", kw)
            break
        except TypeError as e:
            print("[ff] alembic kw 不匹配", kw, e)
    print("[ff] ALEMBIC_EXPORTED", exported, os.path.exists(ABC))

# ---- 渲染 3 帧（Cycles CPU，低采样） ----
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
cam.location = (-4.2, 2.4, 1.7)
target = bpy.data.objects.new("CamTarget", None)
scene.collection.objects.link(target)
target.location = (1.2, 0.0, 0.25)
con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam

sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 4.0
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0, math.radians(30))

world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.05, 0.07, 0.10, 1.0)
    bg.inputs[1].default_value = 1.0

scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24
scene.render.resolution_x = 640
scene.render.resolution_y = 360

rendered = []
for f in (12, 32, 55):
    scene.frame_set(f)
    scene.render.filepath = os.path.join(OUT, "flipv2_frame_%03d.png" % f)
    try:
        bpy.ops.render.render(write_still=True)
        rendered.append(f)
    except Exception as e:
        print("[ff] 渲染帧 %d 失败: %s" % (f, e))
print("[ff] RENDERED", rendered)

print("FLIP_PIPELINE_OK baked=%d abc=%s rendered=%s"
      % (dprops.bake.num_baked_frames, os.path.exists(ABC), rendered))
