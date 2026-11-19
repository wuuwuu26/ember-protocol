# -*- coding: utf-8 -*-
"""在 L_TestArena 关卡中战略布设 9 个战术爆炸燃料桶 ARobotExplosiveBarrel。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)

sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
barrel_cls = unreal.load_class(None, "/Script/RobotGame.RobotExplosiveBarrel")
if not barrel_cls:
    raise RuntimeError("无法加载 RobotExplosiveBarrel 类")

# 先清理已存在的旧爆炸桶
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
removed = 0
for a in actors:
    if a.get_class().get_name() == "RobotExplosiveBarrel":
        sub.destroy_actor(a)
        removed += 1
unreal.log(f"清理了 {removed} 个旧爆炸桶")

# 战略布设点（涵盖西北侧脚手架、北侧集装箱群、中场掩体旁、南侧通道与东侧防线）
LOCATIONS = [
    (-750.0,  600.0, 0.0,  15.0),
    (-300.0,  950.0, 0.0, -45.0),
    ( 550.0,  950.0, 0.0,  30.0),
    ( 300.0,  350.0, 0.0,  60.0),
    ( 600.0, -250.0, 0.0, -20.0),
    (-600.0, -900.0, 0.0,  10.0),
    ( 450.0, -850.0, 0.0, -35.0),
    (1100.0, -400.0, 0.0,  45.0),
    (1050.0,  500.0, 0.0, -75.0),
]

count = 0
for x, y, z, yaw in LOCATIONS:
    loc = unreal.Vector(x, y, z)
    rot = unreal.Rotator(0.0, yaw, 0.0)
    barrel = sub.spawn_actor_from_class(barrel_cls, loc, rot)
    if barrel:
        barrel.set_actor_label(f"ExplosiveBarrel_{count}")
        count += 1

unreal.log(f"成功布设 {count} 个战术爆炸燃料桶！正在保存关卡...")
unreal.EditorLevelLibrary.save_current_level()
unreal.log("关卡已保存！")

with open(r"C:\Users\25227\Documents\robot_game\docs\barrels_spawned.txt", "w", encoding="utf-8") as f:
    f.write(f"Spawned {count} explosive barrels\nBARRELS_SPAWNED_DONE\n")
