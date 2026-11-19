# -*- coding: utf-8 -*-
"""
摆放场地道具（集装箱 / 油桶 / 货架 / 废料 / 终端 …）
================================================================
背景：`build_props.py` 早就产出了 10 种道具并导进了
`/Game/RobotGame/Art/Props`，但**关卡里一个都没摆** ——
184 个 Actor 里 150 个是地面/墙/天桥/立柱，场地是空的。
这就是"场景不够精细"最直接的原因：不是缺资产，是缺摆放。

摆法：按"堆场"生成 —— 每个堆场给一个区域和道具类型，
在里面按网格 + 固定抖动铺开。用固定种子，每次重建结果一致
（否则每次跑一遍场景都变，没法迭代）。

避开玩家主通路：出生点在 (-200, 0) 朝 +X，
所以 |y| < 600 的走廊里不放东西。

用法: bash tools/ue_py.sh ue/Scripts/place_props.py "摆道具"
"""
import math
import os
import random
import unreal

PROP_DIR = "/Game/RobotGame/Art/Props"
FBX_DIR = r"C:\Users\25227\Documents\robot_game\assets\out"
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
L = "[道具]"

# 堆场定义: (中心X, 中心Y, 半宽X, 半宽Y, 道具列表, 密度, 是否允许叠放)
YARDS = [
    # ── 北侧靠墙堆场：集装箱 + 货架（最显眼的"有人在这里干活"）──
    (-780.0, 1090.0, 320.0, 150.0,
     ["container", "container", "container", "shelf", "scrapcrate"], 3, True),
    (420.0, 1150.0, 300.0, 130.0,
     ["container", "supplybox", "fuelbarrel", "fuelbarrel"], 3, False),
    (1240.0, 1080.0, 260.0, 140.0,
     ["shelf", "supplybox", "scrapcrate", "debris"], 3, False),

    # ── 南侧靠墙：油桶群 + 废料 ──
    (-900.0, -1080.0, 300.0, 150.0,
     ["fuelbarrel", "fuelbarrel", "fuelbarrel", "debris"], 3, False),
    (300.0, -1120.0, 340.0, 140.0,
     ["scrapcrate", "debris", "debris", "fuelbarrel"], 3, False),
    (1180.0, -1050.0, 260.0, 150.0,
     ["container", "scrapcrate", "debris"], 2, False),

    # ── 远墙（+X）内侧：终端 + 供应箱（"作业区"）──
    (1600.0, -420.0, 120.0, 220.0,
     ["terminal", "supplybox", "pipesegment"], 2, False),
    (1600.0, 520.0, 120.0, 200.0,
     ["terminal", "shelf", "fuelbarrel"], 2, False),

    # ── 背墙（-X）内侧：管道 + 救援舱 ──
    (-1120.0, -520.0, 120.0, 240.0,
     ["pipesegment", "pipesegment", "debris"], 2, False),
    (-1120.0, 480.0, 120.0, 220.0,
     ["salvagepod", "pipesegment", "supplybox"], 2, False),

    # ── 场地中部的孤立小堆（打破"四周靠墙"的规律）──
    (-260.0, 760.0, 90.0, 90.0, ["fuelbarrel", "scrapcrate"], 1, False),
    (700.0, -780.0, 90.0, 90.0, ["supplybox", "debris"], 1, False),
]

MATS = {
    "container": "M_Steel",
    "shelf": "M_SteelLight",
    "scrapcrate": "M_Rust",
    "debris": "M_Rust",
    "fuelbarrel": "M_Copper",
    "supplybox": "M_SteelLight",
    "pipesegment": "M_Steel",
    "salvagepod": "M_SteelLight",
    "terminal": "M_Joint",
}


def log(m):
    unreal.log("%s %s" % (L, m))


def ensure_import(kind):
    name = "sm_prop_%s" % kind
    path = "%s/%s" % (PROP_DIR, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    fbx = os.path.join(FBX_DIR, "prop_%s.fbx" % kind)
    if not os.path.exists(fbx):
        log("❌ 缺 FBX: %s" % fbx)
        return None
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    task = unreal.AssetImportTask()
    task.filename = fbx
    task.destination_path = PROP_DIR
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

    removed = 0
    for a in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        if a.get_actor_label().startswith("PROP_"):
            sub.destroy_actor(a)
            removed += 1
    log("清理旧道具 %d 个" % removed)

    # 固定种子：每次重建摆放一致
    rng = random.Random(20261023)

    cache = {}
    mat_cache = {}
    placed = 0

    for cx, cy, hx, hy, kinds, density, allow_stack in YARDS:
        cols = max(1, int(hx * 2 / 130.0))
        rows = max(1, int(hy * 2 / 130.0))
        for r in range(rows):
            for c in range(cols):
                if rng.random() > density / 3.0:
                    continue
                kind = rng.choice(kinds)
                if kind not in cache:
                    cache[kind] = ensure_import(kind)
                mesh = cache[kind]
                if not mesh:
                    continue

                # 网格 + 抖动（±22cm，避免一眼看出阵列）
                x = cx - hx + (c + 0.5) * (hx * 2.0 / cols) + rng.uniform(-22, 22)
                y = cy - hy + (r + 0.5) * (hy * 2.0 / rows) + rng.uniform(-22, 22)
                yaw = rng.uniform(0.0, 360.0)
                sc = rng.uniform(0.92, 1.08)

                z = 0.0
                if allow_stack and rng.random() < 0.30:
                    # 叠一层：集装箱堆起来才像堆场
                    z = 0.0
                    layers = rng.choice([1, 2])

                    for k in range(layers):
                        a = sub.spawn_actor_from_class(
                            unreal.StaticMeshActor,
                            unreal.Vector(x, y, k * 118.0),
                            unreal.Rotator(0.0, yaw + rng.uniform(-6, 6), 0.0))
                        if not a:
                            continue
                        a.set_actor_label("PROP_%s_%d" % (kind, placed))
                        a.set_actor_scale3d(unreal.Vector(sc, sc, sc))
                        smc = a.get_editor_property("static_mesh_component")
                        smc.set_editor_property("static_mesh", mesh)
                        smc.set_mobility(unreal.ComponentMobility.STATIC)
                        mname = MATS.get(kind, "M_Steel")
                        if mname not in mat_cache:
                            mat_cache[mname] = unreal.EditorAssetLibrary.load_asset(
                                "%s/%s" % (PROP_DIR, mname))
                        if mat_cache[mname]:
                            smc.set_material(0, mat_cache[mname])
                        placed += 1
                    continue

                a = sub.spawn_actor_from_class(
                    unreal.StaticMeshActor, unreal.Vector(x, y, z),
                    unreal.Rotator(0.0, yaw, 0.0))
                if not a:
                    continue
                a.set_actor_label("PROP_%s_%d" % (kind, placed))
                a.set_actor_scale3d(unreal.Vector(sc, sc, sc))
                smc = a.get_editor_property("static_mesh_component")
                smc.set_editor_property("static_mesh", mesh)
                smc.set_mobility(unreal.ComponentMobility.STATIC)
                mname = MATS.get(kind, "M_Steel")
                if mname not in mat_cache:
                    mat_cache[mname] = unreal.EditorAssetLibrary.load_asset(
                        "%s/%s" % (PROP_DIR, mname))
                if mat_cache[mname]:
                    smc.set_material(0, mat_cache[mname])
                placed += 1

    log("摆放 %d 个道具" % placed)
    unreal.EditorLevelLibrary.save_current_level()
    log("已保存关卡")


main()
