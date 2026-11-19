# -*- coding: utf-8 -*-
"""检查关卡内 BG_ 开头的远景物体当前位置与状态。"""
import unreal

unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
actors = unreal.EditorLevelLibrary.get_all_level_actors()

out = []
for a in actors:
    lbl = a.get_actor_label()
    if lbl.startswith("BG_"):
        loc = a.get_actor_location()
        scale = a.get_actor_scale3d()
        smc = a.get_editor_property("static_mesh_component") if hasattr(a, "get_editor_property") else None
        mesh = smc.static_mesh.get_name() if (smc and smc.static_mesh) else "None"
        out.append("%-20s mesh=%-20s loc=(%6.0f,%6.0f,%6.0f) scale=(%.2f,%.2f,%.2f)" % (
            lbl, mesh, loc.x, loc.y, loc.z, scale.x, scale.y, scale.z))

with open(r"C:\Users\25227\Documents\robot_game\docs\bg_check.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(sorted(out)))
    f.write("\nBG_CHECK_DONE\n")
