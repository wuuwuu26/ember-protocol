# -*- coding: utf-8 -*-
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())

out = []
for a in actors:
    if isinstance(a, unreal.StaticMeshActor):
        comp = a.static_mesh_component
        mesh_name = comp.static_mesh.get_name() if (comp and comp.static_mesh) else "None"
        out.append(f"{a.get_name()} -> {mesh_name} loc={a.get_actor_location()}")

with open(r"C:\Users\25227\Documents\robot_game\docs\all_sm_actors.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
    f.write("\nALL_SM_DONE\n")
