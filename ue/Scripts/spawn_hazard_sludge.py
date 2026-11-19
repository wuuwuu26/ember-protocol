# -*- coding: utf-8 -*-
"""在 L_TestArena 关卡战术要道布设 4 个剧毒动态废液池 ARobotHazardSludge。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)

sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sludge_cls = unreal.load_class(None, "/Script/RobotGame.RobotHazardSludge")
if not sludge_cls:
    raise RuntimeError("无法加载 RobotHazardSludge 类")

# 先清理已存在的旧废液池
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
removed = 0
for a in actors:
    if a.get_class().get_name() == "RobotHazardSludge":
        sub.destroy_actor(a)
        removed += 1
unreal.log(f"清理了 {removed} 个旧废液池")

# 4 个战术要道点位（略微高于地板 Z=0.5，贴地微凹陷）
SLUDGE_SPOTS = [
    ( -200.0,   350.0, 0.5,   25.0),  # 中场掩体前侧
    (  800.0,  -150.0, 0.5,  -45.0),  # 东侧通道开阔处
    ( -650.0,  -450.0, 0.5,   60.0),  # 西南脚手架盲区
    (  400.0,   750.0, 0.5, -120.0),  # 东北集装箱群咽喉
]

count = 0
for x, y, z, yaw in SLUDGE_SPOTS:
    loc = unreal.Vector(x, y, z)
    rot = unreal.Rotator(0.0, yaw, 0.0)
    pool = sub.spawn_actor_from_class(sludge_cls, loc, rot)
    if pool:
        pool.set_actor_label(f"HazardSludge_{count}")
        count += 1

unreal.log(f"成功布设 {count} 个战术剧毒废液池！正在保存关卡...")
unreal.EditorLevelLibrary.save_current_level()
unreal.log("关卡已保存！")

with open(r"C:\Users\25227\Documents\robot_game\docs\sludge_spawned.txt", "w", encoding="utf-8") as f:
    f.write(f"Spawned {count} hazard sludge pools\nSLUDGE_SPAWNED_DONE\n")
