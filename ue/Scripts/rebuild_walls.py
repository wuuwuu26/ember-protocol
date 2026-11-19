# -*- coding: utf-8 -*-
"""
重建竞技场围墙（用 build_walls.py 产出的新资产）。
================================================================

为什么重做：
    原来的围墙是 4m 一段的 `SM_Env_Wall` —— 一块 46cm 厚、带两块面板的方板，
    顶上没有压顶、脚下没有基座、墙面没有扶壁。远看就是一排灰盒子，
    既不像"建筑"，也不像"翻不过去"。用户反馈"要真实的墙体"。

新墙（SM_Wall_Segment / SM_Wall_Corner）：
    基座 → 墙体（带凹板 / 扶壁 / 检修口 / 通风格栅）→ 外挑圆角压顶 → 顶部管线
    + 底部安全色带 + 转角圆柱包角 + 顶部警示灯。

摆法：
    · 段长 412cm，按 400cm 间距摆放，相邻两段重叠 12cm（不留缝）
    · 内侧朝向场地：背墙 yaw=90、远墙 yaw=-90、南墙 yaw=180、北墙 yaw=0
    · 四个角放转角柱，正好盖住两段墙的接缝

用法: bash tools/ue_py.sh ue/Scripts/rebuild_walls.py "围墙重建"
"""
import os
import unreal

ENV = "/Game/RobotGame/Art/Environment"
FBX_DIR = r"C:\Users\25227\Documents\robot_game\assets\out"
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
L = "[围墙重建]"

# 墙体中心线（和原关卡一致，不改变可玩区域）
X_BACK = -1300.0
X_FAR = 1800.0
Y_SIDE = 1380.0
STEP = 400.0
SEG_LEN = 412.0

log_lines = []


def log(m):
    unreal.log("%s %s" % (L, m))
    log_lines.append(m)


def ensure_import(name):
    path = "%s/%s" % (ENV, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    task = unreal.AssetImportTask()
    task.filename = os.path.join(FBX_DIR, name.lower() + ".fbx")
    task.destination_path = ENV
    task.destination_name = name.lower()
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
    log("导入 %s -> %s" % (task.filename, task.imported_object_paths))
    return unreal.EditorAssetLibrary.load_asset(path)


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(LEVEL)
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    seg = ensure_import("SM_Wall_Segment")
    corner = ensure_import("SM_Wall_Corner")
    if not seg or not corner:
        log("❌ 资产缺失")
        return

    # ── 清掉旧墙（旧 SM_Env_Wall 与新墙都删，幂等）──
    killed = 0
    for a in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        if a.get_class().get_name() != "StaticMeshActor":
            continue
        c = a.static_mesh_component
        mesh = c.get_editor_property("static_mesh") if c else None
        nm = mesh.get_name() if mesh else ""
        if nm in ("SM_Env_Wall", "sm_wall_segment", "SM_Wall_Segment",
                  "sm_wall_corner", "SM_Wall_Corner"):
            actor_sub.destroy_actor(a)
            killed += 1
    log("清掉旧墙 %d 段" % killed)

    def place(mesh, loc, yaw):
        a = actor_sub.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(*loc),
            unreal.Rotator(0.0, yaw, 0.0))
        if not a:
            return None
        c = a.static_mesh_component
        try:
            c.set_mobility(unreal.ComponentMobility.STATIC)
        except Exception:
            pass
        c.set_static_mesh(mesh)
        return a

    n = 0
    # 背墙（x=-1300，朝 +X 看场地）：沿 Y 铺 7 段
    for i in range(-3, 4):
        if place(seg, (X_BACK, i * STEP, 0.0), 90.0):
            n += 1
    # 远墙（x=1800，朝 -X）
    for i in range(-3, 4):
        if place(seg, (X_FAR, i * STEP, 0.0), -90.0):
            n += 1
    # 南墙 / 北墙：沿 X 铺 8 段
    for i in range(-3, 5):
        if place(seg, (i * STEP, -Y_SIDE, 0.0), 180.0):
            n += 1
        if place(seg, (i * STEP, Y_SIDE, 0.0), 0.0):
            n += 1
    log("墙段：%d 段（4.12m/段，400cm 间距）" % n)

    # 四个转角柱
    nc = 0
    for x in (X_BACK, X_FAR):
        for y in (-Y_SIDE, Y_SIDE):
            if place(corner, (x, y, 0.0), 0.0):
                nc += 1
    log("转角柱：%d 个" % nc)

    les.save_current_level()
    log("完成并保存关卡")
    print("\n".join("%s %s" % (L, m) for m in log_lines))


main()
