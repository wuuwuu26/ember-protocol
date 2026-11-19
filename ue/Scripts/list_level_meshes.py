# -*- coding: utf-8 -*-
"""遍历关卡内所有网格资产，列出其命名、网格、包围盒与材质。"""
import unreal

unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
actors = unreal.EditorLevelLibrary.get_all_level_actors()

out = []
for a in actors:
    if not isinstance(a, unreal.StaticMeshActor):
        continue
    comp = a.static_mesh_component
    if not comp or not comp.static_mesh:
        continue
    loc = a.get_actor_location()
    origin, box = a.get_actor_bounds(False)
    mats = [comp.get_material(i).get_path_name() if comp.get_material(i) else "None"
            for i in range(comp.get_num_materials())]
    out.append("%-30s mesh=%-35s loc=(%6.0f,%6.0f,%6.0f) box=(%5.0f,%5.0f,%5.0f) mats=%s" % (
        a.get_actor_label(), comp.static_mesh.get_name(),
        loc.x, loc.y, loc.z, box.x, box.y, box.z, mats))

with open(r"C:\Users\25227\Documents\robot_game\docs\level_static_meshes.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(sorted(out)))
    f.write("\nALL_MESHES_DONE\n")
