# -*- coding: utf-8 -*-
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)

sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
barrel_cls = unreal.load_class(None, "/Script/RobotGame.RobotExplosiveBarrel")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
targets = []

for a in actors:
    if isinstance(a, unreal.StaticMeshActor):
        comp = a.static_mesh_component
        if comp and comp.static_mesh:
            mname = comp.static_mesh.get_name()
            if "FuelBarrel" in mname:
                targets.append((a.get_actor_label(), a.get_actor_location(), a.get_actor_rotation(), a))
    elif a.get_class().get_name() == "RobotExplosiveBarrel":
        sub.destroy_actor(a)

unreal.log(f"找到 {len(targets)} 个燃油桶网格，开始替换为战术爆炸燃料桶...")

count = 0
for lbl, loc, rot, old_actor in targets:
    sub.destroy_actor(old_actor)
    new_barrel = sub.spawn_actor_from_class(barrel_cls, loc, rot)
    if new_barrel:
        new_barrel.set_actor_label(f"ExplosiveBarrel_{count}")
        count += 1

unreal.log(f"成功布设 {count} 个战术爆炸燃料桶！正在保存关卡...")
unreal.EditorLevelLibrary.save_current_level()
unreal.log("关卡已保存！")

with open(r"C:\Users\25227\Documents\robot_game\docs\barrels_placed.txt", "w", encoding="utf-8") as f:
    f.write(f"Placed {count} explosive barrels\nBARRELS_DONE\n")
