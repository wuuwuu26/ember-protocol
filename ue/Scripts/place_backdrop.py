# -*- coding: utf-8 -*-
"""
摆放场外远景（烟囱 / 桁架 / 储罐）
================================================================
导入 build_backdrop.py 的三个资产，按一张固定表摆到围墙外。

为什么用固定表而不是随机：远景是**构图**的一部分 —— 哪一侧该有高塔、
哪一侧要留空（避免挡住玩家的视线主轴），是设计决定，不是随机能碰出来的。
表格改动一次，之后每次重建都一致。

用法: bash tools/ue_py.sh ue/Scripts/place_backdrop.py "远景"
"""
import os
import unreal

ENV = "/Game/RobotGame/Art/Environment"
FBX_DIR = r"C:\Users\25227\Documents\robot_game\assets\out"
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
L = "[远景]"

# (资产, X, Y, Yaw, 缩放)
#
# 场地：x ∈ [-1300, 1800]，y ∈ ±1380，围墙高 3.8m。
# 远景放在墙外 5500~10500cm 处。
# ⚠️ 第一版放在 3000cm 处，结果 34m 高的塔在画面里比玩家还大，
#    整个右侧被一座储罐占满 —— 远景必须"小、淡、退到后面"。
#    放到 7000cm 之后正好落在雾的过渡带里，是剪影而不是实体。
#
# ⚠️ 东侧（+X）是玩家的默认朝向，视线主轴不能挡 ——
#    两座都偏到 y=±3000 以外。
LAYOUT = [
    # ── 北侧（+Y）：主天际线，四座错落 ──
    ("sm_bg_stack",  -2600.0,  5400.0,  12.0, 1.75),
    ("sm_bg_gantry",   900.0,  6200.0, -22.0, 1.50),
    ("sm_bg_silo",    4200.0,  5200.0,  40.0, 1.60),
    ("sm_bg_gantry",  -600.0,  8200.0,  65.0, 1.15),
    # ── 南侧（-Y）：两座矮的，给背后留呼吸 ──
    ("sm_bg_silo",   -1800.0, -5200.0, 155.0, 1.40),
    ("sm_bg_stack",   2600.0, -6000.0, 195.0, 1.25),
    # ── 东侧（+X）：**避开正前方主轴**（玩家朝 +X，视线不能被挡）──
    ("sm_bg_gantry",  6200.0,  -3000.0, -85.0, 1.60),
    ("sm_bg_silo",    5800.0,   3200.0, -60.0, 1.35),
    # ── 西侧（-X）：压住画面左缘 ──
    ("sm_bg_stack",  -5400.0,  -1800.0,  80.0, 1.45),
    ("sm_bg_gantry", -5000.0,   2100.0,  95.0, 1.10),
]


def log(m):
    unreal.log("%s %s" % (L, m))


def ensure_import(name):
    path = "%s/%s" % (ENV, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    task = unreal.AssetImportTask()
    task.filename = os.path.join(FBX_DIR, name + ".fbx")
    task.destination_path = ENV
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True
    ui = unreal.FbxImportUI()
    ui.import_mesh = True
    ui.import_materials = True
    ui.import_textures = False
    ui.import_animations = False
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    task.options = ui
    tools.import_asset_tasks([task])
    log("导入 %s" % name)
    return unreal.EditorAssetLibrary.load_asset(path)


def main():
    unreal.EditorLevelLibrary.load_level(LEVEL)
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # 先清掉旧的远景（名字以 BG_ 开头）
    removed = 0
    for a in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        if a.get_actor_label().startswith("BG_"):
            sub.destroy_actor(a)
            removed += 1
    log("清理旧远景 %d 个" % removed)

    # 远景用 M_Joint（albedo 0.045）而不是 M_Steel（0.15）——
    # 7000cm 外的东西本来就该是深色剪影，用主体材质会显得比场地还亮，
    # 空间关系立刻反过来（远的东西看着比近的还清楚 = 视觉错误）。
    mat = unreal.EditorAssetLibrary.load_asset("%s/M_Joint" % ENV)
    if not mat:
        mat = unreal.EditorAssetLibrary.load_asset("%s/M_Steel" % ENV)
    if not mat:
        log("⚠️ 找不到材质，远景将用默认材质")

    # ── 外围地面 ──
    #
    # 墙外原本是空的：远景塔摆在 z=0，但脚下没有地，
    # 从场地里看过去它们全"浮"在地平线上（第一版就是这样）。
    # 铺一块 280m × 280m 的深色板，把所有远景接回地面。
    ground = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
    gmat = None
    for gp in ("%s/M_Joint" % ENV, "%s/M_Steel" % ENV):
        gmat = unreal.EditorAssetLibrary.load_asset(gp)
        if gmat:
            log("外围地面材质 = %s" % gp)
            break
    for a in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        if a.get_actor_label() == "BG_Ground":
            sub.destroy_actor(a)
    if ground:
        g = sub.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(250.0, 0.0, -45.0),
            unreal.Rotator(0.0, 0.0, 0.0))
        if g:
            g.set_actor_label("BG_Ground")
            # Cube 原始边长 100 → 缩放 280 = 28000cm
            # 顶面压到 z=-20（低于场地地板），厚度 0.5 → 只在远处露出来
            g.set_actor_scale3d(unreal.Vector(280.0, 280.0, 0.5))
            gsmc = g.get_editor_property("static_mesh_component")
            gsmc.set_editor_property("static_mesh", ground)
            gsmc.set_mobility(unreal.ComponentMobility.STATIC)
            if gmat:
                gsmc.set_material(0, gmat)
            log("外围地面 280m × 280m 已铺")

    cache = {}
    placed = 0
    for name, x, y, yaw, scale in LAYOUT:
        if name not in cache:
            cache[name] = ensure_import(name)
        mesh = cache[name]
        if not mesh:
            log("❌ 缺资产 %s" % name)
            continue

        a = sub.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(x, y, 0.0),
            unreal.Rotator(0.0, yaw, 0.0))
        if not a:
            log("❌ 生成失败 %s" % name)
            continue
        a.set_actor_label("BG_%s_%d" % (name.replace("sm_bg_", ""), placed))
        a.set_actor_scale3d(unreal.Vector(scale, scale, scale))

        smc = a.get_editor_property("static_mesh_component")
        smc.set_editor_property("static_mesh", mesh)
        smc.set_mobility(unreal.ComponentMobility.STATIC)
        if mat:
            smc.set_material(0, mat)
        placed += 1

    log("摆放 %d 个远景" % placed)
    unreal.EditorLevelLibrary.save_current_level()
    log("已保存关卡")


main()
