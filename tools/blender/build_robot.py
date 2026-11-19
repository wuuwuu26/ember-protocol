"""
余火协议 · 程序化机体建模脚本  v2
================================================
用 Blender 的 Python API 生成模块化机器人机体，输出 UE5 可直接导入的资产。

用法（无头运行）:
    blender --background --python build_robot.py -- --chassis medium --out ../out
    blender --background --python build_robot.py -- --chassis all

参数:
    --chassis   机型: light | medium | heavy | all   (默认 medium)
    --out       输出目录                            (默认 ./out)
    --no-render 跳过预览渲染（加快批量生成）

输出:
    <out>/robot_<variant>.blend          工程文件
    <out>/robot_<variant>.fbx            UE5 导入用（单位已换算为 cm）
    <out>/robot_<variant>.glb            通用交换格式
    <out>/preview_robot_<variant>.png    预览渲染

坐标约定:
    Blender 中 -Y 为机体正面，Z 轴向上（Blender 标准正面视图约定）。
    经 FBX 导出后在 UE5 中为 +X 朝前、Z 朝上，符合项目规范。

设计约束（对应制作计划 3.1）:
    质量 / 供电 / 散热 三条约束在几何上的体现 ——
    轻型机窄、薄、散热鳍多；重型机宽、厚、散热鳍少而小。
"""

import bpy
import mathutils
import math
import os
import sys

# ─────────────────────────────────────────────────────────
# 参数解析
# ─────────────────────────────────────────────────────────

def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    args = {"chassis": "medium", "out": "./out", "no-render": False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--chassis" and i + 1 < len(argv):
            args["chassis"] = argv[i + 1]; i += 2
        elif a == "--out" and i + 1 < len(argv):
            args["out"] = argv[i + 1]; i += 2
        elif a == "--no-render":
            args["no-render"] = True; i += 1
        else:
            i += 1
    return args


# ─────────────────────────────────────────────────────────
# 机型参数（单位：米）
# ─────────────────────────────────────────────────────────

def variant_params(v):
    if v == "light":
        # 轻型侦察：窄、薄、高。散热鳍最多，装甲最薄。
        return dict(
            name="轻型侦察", code="light",
            accent=(0.24, 0.72, 0.62),
            core_glow=(0.30, 0.95, 0.82),
            torso=(0.62, 0.42, 0.56), pelvis=(0.46, 0.36, 0.30), head=(0.28, 0.30, 0.26),
            shoulder=(0.26, 0.38, 0.26), upper_arm=(0.16, 0.18, 0.38),
            forearm=(0.15, 0.17, 0.32), thruster=(0.24, 0.32, 0.78),
            foot=(0.30, 0.50, 0.18), backpack=(0.40, 0.22, 0.42),
            z_torso=1.66, z_pelvis=1.20, z_head=2.16, z_shoulder=1.84,
            z_upper=1.50, z_fore=1.16, z_thruster=0.60, z_foot=0.11, z_backpack=1.74,
            x_shoulder=0.42, x_arm=0.54, x_thruster=0.24,
            fin_count=5, fin_scale=1.15,
            height_note="约 2.45 m",
        )
    if v == "heavy":
        # 重型攻坚：宽、厚、矮。散热鳍少而短，装甲最厚。
        return dict(
            name="重型攻坚", code="heavy",
            accent=(0.88, 0.58, 0.18),
            core_glow=(1.0, 0.68, 0.26),
            torso=(0.94, 0.64, 0.66), pelvis=(0.72, 0.54, 0.38), head=(0.34, 0.36, 0.28),
            shoulder=(0.40, 0.54, 0.40), upper_arm=(0.28, 0.30, 0.46),
            forearm=(0.26, 0.28, 0.40), thruster=(0.44, 0.50, 0.78),
            foot=(0.50, 0.74, 0.26), backpack=(0.68, 0.30, 0.56),
            z_torso=1.52, z_pelvis=1.04, z_head=2.00, z_shoulder=1.72,
            z_upper=1.38, z_fore=1.02, z_thruster=0.50, z_foot=0.13, z_backpack=1.60,
            x_shoulder=0.60, x_arm=0.78, x_thruster=0.36,
            fin_count=2, fin_scale=0.70,
            height_note="约 2.32 m",
        )
    # medium（默认）
    return dict(
        name="中型通用", code="medium",
        accent=(0.28, 0.56, 0.82),
        core_glow=(0.52, 0.45, 0.92),
        torso=(0.76, 0.52, 0.62), pelvis=(0.58, 0.44, 0.32), head=(0.32, 0.34, 0.28),
        shoulder=(0.32, 0.46, 0.30), upper_arm=(0.20, 0.22, 0.40),
        forearm=(0.18, 0.20, 0.34), thruster=(0.30, 0.38, 0.82),
        foot=(0.38, 0.60, 0.22), backpack=(0.52, 0.24, 0.46),
        z_torso=1.62, z_pelvis=1.14, z_head=2.10, z_shoulder=1.80,
        z_upper=1.46, z_fore=1.12, z_thruster=0.55, z_foot=0.12, z_backpack=1.70,
        x_shoulder=0.48, x_arm=0.63, x_thruster=0.28,
        fin_count=3, fin_scale=1.0,
        height_note="约 2.38 m",
    )


# ─────────────────────────────────────────────────────────
# 场景与材质工具
# ─────────────────────────────────────────────────────────

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.armatures,
                  bpy.data.lights, bpy.data.cameras):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def make_material(name, color, metallic=0.85, roughness=0.42,
                  emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = None
    for n in mat.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            bsdf = n
            break
    if bsdf is None:
        return mat

    def setv(names, value):
        for sn in names:
            if sn in bsdf.inputs:
                bsdf.inputs[sn].default_value = value
                return True
        return False

    setv(["Base Color"], (color[0], color[1], color[2], 1.0))
    setv(["Metallic"], metallic)
    setv(["Roughness"], roughness)
    if emission is not None:
        setv(["Emission Color", "Emission"],
             (emission[0], emission[1], emission[2], 1.0))
        setv(["Emission Strength"], emission_strength)
    return mat


def assign_mat(ob, mat):
    if ob.data and hasattr(ob.data, "materials"):
        ob.data.materials.clear()
        ob.data.materials.append(mat)


def bevel(ob, width, segments=2, angle_deg=38.0):
    if width <= 0:
        return
    bpy.context.view_layer.objects.active = ob
    m = ob.modifiers.new("bevel", 'BEVEL')
    m.width = width
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle_deg)
    try:
        bpy.ops.object.modifier_apply(modifier=m.name)
    except Exception as e:
        print("  [warn] bevel failed on %s: %s" % (ob.name, e))


def add_box(name, size, loc, rot=(0.0, 0.0, 0.0), mat=None,
            bev=0.016, segments=2):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (size[0], size[1], size[2])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel(ob, min(bev, min(size) * 0.24), segments)
    if mat:
        assign_mat(ob, mat)
    return ob


def add_cyl(name, radius, depth, loc, rot=(0.0, 0.0, 0.0), mat=None,
            verts=20, bev=0.007):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth,
                                        vertices=verts, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    bevel(ob, min(bev, radius * 0.28), 2)
    if mat:
        assign_mat(ob, mat)
    return ob


def add_socket(name, loc, size=0.09):
    bpy.ops.object.empty_add(type='ARROWS', location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.empty_display_size = size
    return ob


# ─────────────────────────────────────────────────────────
# 机体构建
# ─────────────────────────────────────────────────────────

def build_robot(P, mats):
    """构建一台完整机体。部件保持独立对象，对应游戏中可独立摧毁的部位。"""
    parts, sockets = [], []
    steel, accent, joint = mats["steel"], mats["accent"], mats["joint"]
    core_m, visor_m = mats["core"], mats["visor"]

    TW, TD, TH = P["torso"]          # 躯干宽 / 厚 / 高
    PW, PD, PH = P["pelvis"]
    HW, HD, HH = P["head"]
    SW, SD, SH = P["shoulder"]
    UA, FA = P["upper_arm"], P["forearm"]
    TG, FT, BP = P["thruster"], P["foot"], P["backpack"]

    zT, zP, zH = P["z_torso"], P["z_pelvis"], P["z_head"]
    zS, zU, zF = P["z_shoulder"], P["z_upper"], P["z_fore"]
    zG, zFt, zB = P["z_thruster"], P["z_foot"], P["z_backpack"]
    xS, xA, xG = P["x_shoulder"], P["x_arm"], P["x_thruster"]

    front_y = -TD * 0.5

    # ── 躯干 ────────────────────────────────────────────
    parts.append(add_box("chassis_torso", (TW, TD, TH), (0.0, 0.0, zT), mat=steel))
    # 胸口装甲板（配色）
    parts.append(add_box("chassis_chestplate",
                         (TW * 0.80, 0.09, TH * 0.66),
                         (0.0, front_y - 0.045, zT + 0.04),
                         mat=accent, bev=0.010))
    # 核心（可摧毁部位，自发光）
    parts.append(add_cyl("part_core", TW * 0.15, 0.10,
                         (0.0, front_y - 0.13, zT + 0.02),
                         rot=(math.radians(90), 0.0, 0.0),
                         mat=core_m, verts=24, bev=0.006))
    # 核心护环
    parts.append(add_cyl("part_corering", TW * 0.21, 0.05,
                         (0.0, front_y - 0.09, zT + 0.02),
                         rot=(math.radians(90), 0.0, 0.0),
                         mat=joint, verts=24, bev=0.005))
    # 胸口散热格栅
    for i in range(3):
        parts.append(add_box("chassis_vent_%02d" % (i + 1),
                             (TW * 0.34, 0.045, 0.028),
                             (-TW * 0.30, front_y - 0.055,
                              zT - TH * 0.22 - i * 0.055),
                             mat=joint, bev=0.004))
    # 腰关节
    parts.append(add_box("chassis_waist",
                         (PW * 0.60, PD * 0.70, 0.13),
                         (0.0, 0.0, zP + PH * 0.5 + 0.03), mat=joint, bev=0.008))
    # 骨盆
    parts.append(add_box("chassis_pelvis", (PW, PD, PH), (0.0, 0.0, zP), mat=steel))
    # 髋关节
    for side, sx in (("L", -1.0), ("R", 1.0)):
        parts.append(add_cyl("part_hip_%s" % side, PD * 0.34, PW * 0.30,
                             (sx * (PW * 0.5 + PW * 0.12), 0.0, zP),
                             rot=(0.0, math.radians(90), 0.0),
                             mat=joint, verts=16, bev=0.005))

    # ── 头部 ────────────────────────────────────────────
    parts.append(add_box("chassis_head", (HW, HD, HH),
                         (0.0, -0.015, zH), mat=steel, bev=0.013))
    parts.append(add_box("chassis_visor",
                         (HW * 0.76, 0.035, HH * 0.22),
                         (0.0, -HD * 0.5 - 0.015, zH + HH * 0.06),
                         mat=visor_m, bev=0.004))
    # 头部天线
    parts.append(add_cyl("chassis_antenna", 0.014, 0.24,
                         (HW * 0.32, HD * 0.30, zH + HH * 0.5 + 0.11),
                         mat=joint, verts=8, bev=0.003))
    parts.append(add_cyl("chassis_neck", HW * 0.34, 0.10,
                         (0.0, 0.0, zH - HH * 0.5 - 0.03),
                         mat=joint, verts=14, bev=0.004))

    # ── 手臂（左右镜像）────────────────────────────────
    for side, sx in (("L", -1.0), ("R", 1.0)):
        # 肩关节
        parts.append(add_cyl("part_shoulderjoint_%s" % side, SD * 0.26, SW * 0.52,
                             (sx * (xS - SW * 0.30), 0.0, zS),
                             rot=(0.0, math.radians(90), 0.0),
                             mat=joint, verts=16, bev=0.005))
        # 肩甲（配色，略微外倾）
        parts.append(add_box("part_shoulder_%s" % side, (SW, SD, SH),
                             (sx * xS, 0.0, zS + SH * 0.16),
                             rot=(0.0, math.radians(-8.0 * sx), 0.0),
                             mat=accent, bev=0.015))
        # 上臂
        parts.append(add_box("part_upperarm_%s" % side, (UA[0], UA[1], UA[2]),
                             (sx * xA, 0.0, zU), mat=steel, bev=0.013))
        # 肘关节
        parts.append(add_cyl("part_elbow_%s" % side, UA[0] * 0.44, UA[0] * 0.86,
                             (sx * xA, 0.0, zU - UA[2] * 0.5 - 0.01),
                             rot=(0.0, math.radians(90), 0.0),
                             mat=joint, verts=14, bev=0.005))
        # 前臂
        parts.append(add_box("part_forearm_%s" % side, (FA[0], FA[1], FA[2]),
                             (sx * xA, 0.0, zF), mat=steel, bev=0.013))
        # 前臂装甲条（配色）
        parts.append(add_box("part_forearmplate_%s" % side,
                             (FA[0] * 1.14, FA[1] * 0.42, FA[2] * 0.60),
                             (sx * xA, -FA[1] * 0.5 - 0.02, zF + FA[2] * 0.08),
                             mat=accent, bev=0.008))
        # 武器炮口（朝前 -Y）
        parts.append(add_cyl("part_muzzle_%s" % side, FA[0] * 0.34, FA[1] * 1.05,
                             (sx * xA, -FA[1] * 0.5 - FA[1] * 0.52, zF + FA[2] * 0.06),
                             rot=(math.radians(90), 0.0, 0.0),
                             mat=joint, verts=16, bev=0.005))
        parts.append(add_cyl("part_barrel_%s" % side, FA[0] * 0.16, FA[1] * 0.9,
                             (sx * xA, -FA[1] * 0.5 - FA[1] * 1.30, zF + FA[2] * 0.06),
                             rot=(math.radians(90), 0.0, 0.0),
                             mat=steel, verts=12, bev=0.003))

    # ── 推进器 / 腿部（左右镜像）───────────────────────
    for side, sx in (("L", -1.0), ("R", 1.0)):
        parts.append(add_box("part_thruster_%s" % side, (TG[0], TG[1], TG[2]),
                             (sx * xG, 0.0, zG), mat=steel, bev=0.017))
        # 膝关节
        parts.append(add_cyl("part_knee_%s" % side, TG[0] * 0.40, TG[0] * 1.06,
                             (sx * xG, -TG[1] * 0.10, zG + TG[2] * 0.22),
                             rot=(0.0, math.radians(90), 0.0),
                             mat=joint, verts=16, bev=0.006))
        # 散热鳍（数量与尺寸随机型变化 —— 对应散热约束）
        n_fin = P["fin_count"]
        for i in range(n_fin):
            fh = 0.05 * P["fin_scale"]
            parts.append(add_box("part_fin_%s_%02d" % (side, i + 1),
                                 (TG[0] * 1.10, fh, TG[2] * 0.66),
                                 (sx * xG,
                                  TG[1] * 0.5 + 0.015 + i * (fh * 1.7),
                                  zG + TG[2] * 0.06),
                                 mat=accent, bev=0.005))
        # 足部
        parts.append(add_box("part_foot_%s" % side, (FT[0], FT[1], FT[2]),
                             (sx * xG, -FT[1] * 0.10, zFt), mat=joint, bev=0.015))
        # 踝关节
        parts.append(add_cyl("part_ankle_%s" % side, TG[0] * 0.34, TG[0] * 0.94,
                             (sx * xG, 0.0, zFt + FT[2] * 0.5 + 0.02),
                             rot=(0.0, math.radians(90), 0.0),
                             mat=joint, verts=14, bev=0.005))

    # ── 背包 ────────────────────────────────────────────
    by = TD * 0.5 + BP[1] * 0.5 + 0.02
    parts.append(add_box("part_backpack", (BP[0], BP[1], BP[2]),
                         (0.0, by, zB), mat=steel, bev=0.015))
    parts.append(add_box("part_backpackplate",
                         (BP[0] * 0.72, 0.05, BP[2] * 0.62),
                         (0.0, by + BP[1] * 0.5 + 0.02, zB),
                         mat=accent, bev=0.008))
    for i, sx in enumerate((-1.0, 1.0)):
        parts.append(add_cyl("part_vent_%02d" % (i + 1), 0.052, 0.15,
                             (sx * BP[0] * 0.30, by + BP[1] * 0.5 + 0.07,
                              zB + BP[2] * 0.28),
                             rot=(math.radians(90), 0.0, 0.0),
                             mat=joint, verts=14, bev=0.004))

    # ── 挂点 ────────────────────────────────────────────
    sockets.append(add_socket("socket_head", (0.0, 0.0, zH + HH * 0.5 + 0.09)))
    sockets.append(add_socket("socket_arm_L", (-xA, 0.0, zF - FA[2] * 0.5 - 0.05)))
    sockets.append(add_socket("socket_arm_R", (xA, 0.0, zF - FA[2] * 0.5 - 0.05)))
    sockets.append(add_socket("socket_back", (0.0, by + BP[1] * 0.5 + 0.13, zB)))
    sockets.append(add_socket("socket_aux_01", (-xS, 0.0, zS + SH * 0.5 + 0.06)))
    sockets.append(add_socket("socket_aux_02", (xS, 0.0, zS + SH * 0.5 + 0.06)))
    sockets.append(add_socket("socket_core", (0.0, front_y - 0.26, zT + 0.02)))
    sockets.append(add_socket("socket_root", (0.0, 0.0, 0.0), size=0.16))

    return parts, sockets


# ─────────────────────────────────────────────────────────
# 导出与渲染
# ─────────────────────────────────────────────────────────

def export_fbx(path):
    """global_scale=100 把 Blender 的米换算成 UE 的厘米。"""
    kw = dict(
        filepath=path, use_selection=False,
        apply_unit_scale=True, global_scale=100.0,
        apply_scale_options='FBX_SCALE_NONE',
        object_types={'MESH', 'EMPTY'},
        use_mesh_modifiers=True, mesh_smooth_type='FACE',
        bake_space_transform=False, path_mode='AUTO', embed_textures=False,
    )
    valid = set(bpy.ops.export_scene.fbx.get_rna_type().properties.keys())
    bpy.ops.export_scene.fbx(**{k: v for k, v in kw.items() if k in valid})


def export_glb(path):
    kw = dict(filepath=path, export_format='GLB',
              use_selection=False, export_apply=True)
    try:
        valid = set(bpy.ops.export_scene.gltf.get_rna_type().properties.keys())
        bpy.ops.export_scene.gltf(**{k: v for k, v in kw.items() if k in valid})
    except Exception as e:
        print("  [warn] GLB 导出跳过: %s" % e)


def set_engine():
    for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'CYCLES'):
        try:
            bpy.context.scene.render.engine = eng
            return eng
        except Exception:
            continue
    return bpy.context.scene.render.engine


def setup_render(out_png, target_z, distance=5.4):
    scene = bpy.context.scene
    eng = set_engine()
    print("  渲染引擎: %s" % eng)

    if eng == 'CYCLES':
        scene.cycles.samples = 64
        scene.cycles.use_denoising = True
    elif hasattr(scene, "eevee"):
        for attr, val in (("taa_render_samples", 64),
                          ("use_raytracing", True)):
            if hasattr(scene.eevee, attr):
                try:
                    setattr(scene.eevee, attr, val)
                except Exception:
                    pass

    # 相机目标
    tgt = bpy.data.objects.new("cam_target", None)
    bpy.context.collection.objects.link(tgt)
    tgt.location = (0.0, 0.0, target_z)

    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_data.lens = 70.0
    cam = bpy.data.objects.new("PreviewCam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = (distance * 0.58, -distance * 0.80, target_z + distance * 0.26)
    con = cam.constraints.new('TRACK_TO')
    con.target = tgt
    con.track_axis = 'TRACK_NEGATIVE_Z'
    con.up_axis = 'UP_Y'
    scene.camera = cam

    # 灯光：能量经过校准，避免高光过曝把配色洗白
    def add_light(name, loc, energy, color=(1, 1, 1), size=3.0):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = energy
        ld.color = color
        ld.size = size
        lo = bpy.data.objects.new(name, ld)
        bpy.context.collection.objects.link(lo)
        lo.location = loc
        c = lo.constraints.new('TRACK_TO')
        c.target = tgt
        c.track_axis = 'TRACK_NEGATIVE_Z'
        c.up_axis = 'UP_Y'

    add_light("KeyLight",  (3.8, -4.0, 4.8), 340.0, (1.00, 0.96, 0.90), 4.0)
    add_light("FillLight", (-4.4, -2.6, 2.2),  95.0, (0.70, 0.82, 1.00), 5.5)
    add_light("RimLight",  (-1.8, 4.6, 3.8),  210.0, (1.00, 0.80, 0.60), 3.0)

    # 世界背景
    world = bpy.data.worlds.new("PreviewWorld")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.042, 0.048, 0.060, 1.0)
        bg.inputs[1].default_value = 0.9
    scene.world = world

    scene.render.resolution_x = 1280
    scene.render.resolution_y = 1280
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = out_png
    # 曝光与色彩管理
    try:
        scene.view_settings.view_transform = 'AgX'
        scene.view_settings.look = 'AgX - Base Contrast'
        scene.view_settings.exposure = -0.35
    except Exception:
        pass
    return eng


# ─────────────────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────────────────

def world_bounds(objs):
    """返回一组物体的世界空间包围盒 (min_xyz, max_xyz)。

    用 bound_box 角点而非物体中心 —— 否则高度统计会漏掉部件自身的厚度，
    得到偏小的数字，导入 UE 后对不上。
    """
    mn = [1e9, 1e9, 1e9]
    mx = [-1e9, -1e9, -1e9]
    for ob in objs:
        for corner in ob.bound_box:
            w = ob.matrix_world @ mathutils.Vector(corner)
            for i in range(3):
                if w[i] < mn[i]:
                    mn[i] = w[i]
                if w[i] > mx[i]:
                    mx[i] = w[i]
    return mn, mx


def build_variant(variant, out_dir, do_render):
    print("\n" + "=" * 56)
    print("构建机型: %s" % variant)
    print("=" * 56)

    clear_scene()
    P = variant_params(variant)

    mats = {
        "steel": make_material("M_Robot_Steel",
                               (0.085, 0.095, 0.112), metallic=0.88, roughness=0.46),
        # 涂装装甲是电介质，metallic 必须低，否则高光会把颜色洗成白色
        "accent": make_material("M_Robot_Accent_%s" % P["code"],
                                P["accent"], metallic=0.18, roughness=0.40),
        "joint": make_material("M_Robot_Joint",
                               (0.032, 0.035, 0.042), metallic=0.50, roughness=0.70),
        # 自发光强度需克制：AgX 色彩管理下超过约 3.0 会直接削顶成纯白，
        # 颜色信息全部丢失，核心就变成一个白色圆盘。
        "core": make_material("M_Robot_Core",
                              (0.05, 0.05, 0.08), metallic=0.25, roughness=0.20,
                              emission=P["core_glow"], emission_strength=2.6),
        "visor": make_material("M_Robot_Visor",
                               (0.04, 0.05, 0.07), metallic=0.30, roughness=0.16,
                               emission=P["core_glow"], emission_strength=1.7),
    }

    parts, sockets = build_robot(P, mats)
    print("  部件: %d 个   挂点: %d 个" % (len(parts), len(sockets)))

    for col_name, objs in (("Robot_Parts", parts), ("Robot_Sockets", sockets)):
        col = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(col)
        for ob in objs:
            for c in list(ob.users_collection):
                c.objects.unlink(ob)
            col.objects.link(ob)

    mn, mx = world_bounds(parts)
    print("  包围盒: 高 %.2f m  宽 %.2f m  深 %.2f m   （设计标注 %s）"
          % (mx[2] - mn[2], mx[0] - mn[0], mx[1] - mn[1], P["height_note"]))
    print("  脚底 z=%.3f m（应为 0，导入 UE 后作为角色原点基准）" % mn[2])

    base = os.path.join(out_dir, "robot_%s" % variant)
    bpy.ops.wm.save_as_mainfile(filepath=base + ".blend")
    print("  [ok] robot_%s.blend" % variant)

    try:
        export_fbx(base + ".fbx")
        print("  [ok] robot_%s.fbx" % variant)
    except Exception as e:
        print("  [FAIL] FBX 导出: %s" % e)
    export_glb(base + ".glb")

    if do_render:
        png = os.path.join(out_dir, "preview_robot_%s.png" % variant)
        try:
            setup_render(png, (mn[2] + mx[2]) * 0.5)
            bpy.ops.render.render(write_still=True)
            print("  [ok] preview_robot_%s.png" % variant)
        except Exception as e:
            print("  [warn] 渲染失败: %s" % e)

    return base


def main():
    args = parse_args()
    out_dir = os.path.abspath(args["out"])
    os.makedirs(out_dir, exist_ok=True)
    print("Blender %s" % bpy.app.version_string)
    print("输出目录: %s" % out_dir)

    variants = ["light", "medium", "heavy"] if args["chassis"] == "all" \
        else [args["chassis"]]
    for v in variants:
        build_variant(v, out_dir, not args["no-render"])
    print("\n完成。")


if __name__ == "__main__":
    main()
