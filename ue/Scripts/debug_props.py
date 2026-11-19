# -*- coding: utf-8 -*-
"""调试道具包围盒与网格名。"""
import unreal

lines = []
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    label = a.get_actor_label()
    if label.startswith("BG_") or label == "SkyDome":
        continue
    try:
        smc = a.static_mesh_component
        mesh = smc.get_editor_property("static_mesh")
        mname = mesh.get_name() if mesh else "None"
    except Exception as e:
        mname = "ERR:" + str(e)[:30]
    origin, extent = a.get_actor_bounds(False)
    bottom = origin.z - extent.z
    if label.startswith("PROP_") or mname.startswith("SM_Prop"):
        lines.append("%-22s mesh=%-22s z=%.1f bottom=%.1f" % (label, mname, a.get_actor_location().z, bottom))

with open(r"C:\Users\25227\Documents\robot_game\docs\prop_debug.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\nPROP_DEBUG_OK\n")
unreal.log("PROP_DEBUG_OK")
