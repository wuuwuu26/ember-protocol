# -*- coding: utf-8 -*-
"""把海报贴到竞技场两面长墙的内侧。

坐标依据（probe_wall_box.py 实测世界包围盒）：
    背墙  worldX -1329.8..-1240.0  → 内侧贴面 X = -1240.0，法线 +X
    远墙  worldX  1770.2..1860.0   → 内侧贴面 X =  1770.2，法线 -X
    两墙均沿 Y 连续，Y 范围 -1406..1406，高 0..396
    （侧墙段是 412cm 长的板块沿 X 排成梳状，不是连续墙，不贴）

几何：用 Engine 的 Cube（100³，每面都是完整 0-1 UV）压成 2cm 薄板。
      这样 ±X 面天然正对玩家、贴图正向，不需要猜 Plane 的旋转。

用法: bash tools/ue_py.sh ue/Scripts/place_posters.py "POSTERS_OK"
"""
import os
import unreal

SRC = r"C:\Users\25227\Documents\robot_game\art_src\posters"
MAT_DIR = "/Game/RobotGame/Art/Materials"
TEX_DIR = MAT_DIR + "/Posters"
MI_DIR = MAT_DIR + "/PosterMI"
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
L = "[海报]"

X_BACK_FACE = -1240.0      # 背墙内侧（法线 +X）
X_FAR_FACE = 1770.2        # 远墙内侧（法线 -X）
THICK = 2.0                # 海报板厚 cm

sub = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

POSTERS = [
    "poster_sector7", "poster_no_entry", "poster_pressure", "poster_shift",
    "poster_highvoltage", "poster_runoff", "poster_bay07", "poster_evac",
    "poster_toolcrib", "poster_roster",
]


def log(m):
    unreal.log("%s %s" % (L, m))


def ensure_dir(d):
    if not unreal.EditorAssetLibrary.does_directory_exist(d):
        unreal.EditorAssetLibrary.make_directory(d)


def import_tex(name):
    src = os.path.join(SRC, name + ".png")
    path = "%s/%s" % (TEX_DIR, name)
    if not os.path.exists(src):
        log("缺源图 %s" % src)
        return None
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        sub.delete_asset(path)
    task = unreal.AssetImportTask()
    task.filename = src
    task.destination_path = TEX_DIR
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True
    tools.import_asset_tasks([task])
    t = unreal.EditorAssetLibrary.load_asset(path)
    if not t:
        log("导入失败 %s" % name)
        return None
    t.set_editor_property("srgb", True)
    unreal.EditorAssetLibrary.save_asset(path)
    return t


def make_mi(tex, name):
    base = "%s/M_Poster" % MAT_DIR
    if not unreal.EditorAssetLibrary.does_asset_exist(base):
        log("缺材质 M_Poster")
        return None
    mi_path = "%s/%s" % (MI_DIR, name)
    if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
        sub.delete_asset(mi_path)
    factory = unreal.MaterialInstanceConstantFactoryNew()
    mi = tools.create_asset(name, MI_DIR, unreal.MaterialInstanceConstant, factory)
    if not mi:
        log("建实例失败 %s" % name)
        return None
    mel.set_material_instance_parent(mi,
                                     unreal.EditorAssetLibrary.load_asset(base))
    mel.set_material_instance_texture_parameter_value(mi, "PosterTex", tex)
    unreal.EditorAssetLibrary.save_asset(mi_path)
    return mi


# (海报索引, 墙面侧, y, z, 宽, 高)
#   side: "back" = 背墙（朝 +X）；"far" = 远墙（朝 -X）
# 排布：两面墙各 9 张，沿 Y 每 300cm 一张，高度略微错落（避免"一排邮票"）。
PLACEMENTS = [
    # ── 背墙（X=-1240，朝 +X）：玩家出生 (-200,0) 朝 +X，回头可见 ──
    (0, "back", -1200, 205, 190, 107),
    (4, "back", -900, 200, 185, 104),
    (1, "back", -600, 208, 190, 107),
    (6, "back", -300, 198, 175, 98),
    (3, "back", 0, 205, 180, 101),
    (5, "back", 300, 200, 185, 104),
    (2, "back", 600, 208, 200, 112),
    (8, "back", 900, 198, 175, 98),
    (7, "back", 1200, 205, 190, 107),

    # ── 远墙（X=1770.2，朝 -X）：正对玩家主视方向 ──
    (9, "far", -1200, 200, 195, 110),
    (2, "far", -900, 208, 190, 107),
    (5, "far", -600, 198, 175, 98),
    (0, "far", -300, 205, 190, 107),
    (6, "far", 0, 202, 180, 101),
    (4, "far", 300, 208, 200, 112),
    (1, "far", 600, 198, 175, 98),
    (7, "far", 900, 205, 190, 107),
    (3, "far", 1200, 200, 185, 104),
]


def main():
    ensure_dir(TEX_DIR)
    ensure_dir(MI_DIR)
    unreal.EditorLevelLibrary.load_level(LEVEL)
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    removed = 0
    for a in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        if a.get_actor_label().startswith("POSTER_"):
            actor_sub.destroy_actor(a)
            removed += 1
    log("清理旧海报 %d" % removed)

    mis = []
    for name in POSTERS:
        tex = import_tex(name)
        if not tex:
            mis.append(None)
            continue
        mis.append(make_mi(tex, "MI_" + name))
        log("%s -> %s" % (name, mis[-1].get_name() if mis[-1] else "None"))

    cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
    if not cube:
        log("缺 Cube 基础网格")
        return

    placed = 0
    for idx, side, y, z, w, h in PLACEMENTS:
        mi = mis[idx] if idx < len(mis) else None
        if not mi:
            continue
        if side == "back":
            # 内侧面在 -1240，板厚 2 → 中心 -1240 + 1，前表面 -1238
            x = X_BACK_FACE + THICK * 0.5
        else:
            x = X_FAR_FACE - THICK * 0.5

        a = actor_sub.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(x, y, z),
            unreal.Rotator(0.0, 0.0, 0.0))
        if not a:
            log("spawn 失败 %d" % placed)
            continue
        a.set_actor_label("POSTER_%s_%d" % (side, placed))
        # Cube 是 100³：X=厚度、Y=宽、Z=高
        a.set_actor_scale3d(unreal.Vector(THICK / 100.0, w / 100.0, h / 100.0))
        smc = a.get_editor_property("static_mesh_component")
        smc.set_editor_property("static_mesh", cube)
        smc.set_mobility(unreal.ComponentMobility.STATIC)
        smc.set_material(0, mi)
        smc.set_collision_profile_name("NoCollision")
        placed += 1

    log("摆放 %d 张海报" % placed)
    unreal.EditorLevelLibrary.save_current_level()
    log("已保存关卡")


main()
unreal.log("POSTERS_OK")
