# -*- coding: utf-8 -*-
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
unreal.log(f"Total actors in level: {len(actors)}")

meshes = {}
for a in actors:
    cname = a.get_class().get_name()
    meshes[cname] = meshes.get(cname, 0) + 1

unreal.log(f"Actor class counts: {meshes}")

# 查看所有含有 Barrel 或 Fuel 的 actor
for a in actors:
    if "barrel" in a.get_name().lower() or "fuel" in a.get_name().lower():
        unreal.log(f"Found name match: {a.get_name()} ({a.get_class().get_name()})")

with open(r"C:\Users\25227\Documents\robot_game\docs\level_actor_debug.txt", "w", encoding="utf-8") as f:
    f.write(f"Total: {len(actors)}\nClasses: {meshes}\nACTOR_DEBUG_DONE\n")
