# -*- coding: utf-8 -*-
"""
敌人检阅：把 6 种敌人并排摆到关卡里，从正面拍一张。
================================================================
用途：敌人模型重做之后，需要在**引擎里**看一遍 —— Blender 的预览渲染
和 UE 的 PBR + 布光差别很大（尤其金属度、粗糙度、自发光）。

摆位：沿 Y 轴排开（敌人正面朝 +X），相机在 +X 侧看向 -X。
截完图立刻把临时 Actor 删掉，关卡保持干净。
"""

import unreal

L = "[敌人检阅]"
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"

NAMES = [
    ("Patrol", "巡逻机"),
    ("Hauler", "运输机"),
    ("Colossus", "维修巨像"),
    ("Gardener", "园丁机"),
    ("Weather", "气象机"),
    ("Guard", "重型护卫"),
]
GAP = 3.4


def log(s):
    unreal.log("%s %s" % (L, s))


unreal.EditorLevelLibrary.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# 先清掉上一次失败残留的临时 Actor
for a in list(unreal.EditorLevelLibrary.get_all_level_actors()):
    if a.get_actor_label().startswith("Review_"):
        sub.destroy_actor(a)

spawned = []
n = len(NAMES)
for i, (code, label) in enumerate(NAMES):
    mesh = unreal.EditorAssetLibrary.load_asset(
        "/Game/RobotGame/Art/Characters/SK_Enemy_%s" % code)
    if not mesh:
        log("❌ 找不到 SK_Enemy_%s" % code)
        continue
    y = (i - (n - 1) * 0.5) * GAP
    a = sub.spawn_actor_from_class(
        unreal.SkeletalMeshActor, unreal.Vector(0.0, y, 0.0),
        unreal.Rotator(0.0, 0.0, 0.0))
    if not a:
        log("❌ 生成失败 %s" % code)
        continue
    a.set_actor_label("Review_%s" % code)
    smc = a.get_editor_property("skeletal_mesh_component")
    # set_skeletal_mesh 已废弃但可用；新名字太长，这里直接用属性
    smc.set_editor_property("skeletal_mesh", mesh)
    spawned.append(a)
    log("摆放 %s 在 y=%.1f" % (label, y))

log("共摆放 %d 个" % len(spawned))

# 相机：站在 +X 侧，略微俯视
cam_loc = unreal.Vector(1900.0, 0.0, 260.0)
cam_rot = unreal.Rotator(0.0, -8.0, 180.0)
# ⚠️ EditorLevelLibrary 里没有这个函数（5.8 已迁到 LevelEditorSubsystem）
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.set_level_viewport_camera_info(cam_loc, cam_rot, "")
log("相机 → (%.0f, %.0f, %.0f)" % (cam_loc.x, cam_loc.y, cam_loc.z))

# 高分辨率截图：走控制台命令，比 AutomationLibrary 稳（后者在某些构建里没绑定）
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "HighResShot 1600x900")
log("已请求截图 HighResShot")

# 不在这里删临时 Actor —— 截图是下一帧才渲染，删早了会拍空场景。
# 下次运行本脚本时会在开头统一清理（见上）。
log("临时 Actor 保留至下次运行（关卡不保存，不会污染）")
