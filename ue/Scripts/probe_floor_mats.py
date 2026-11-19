# -*- coding: utf-8 -*-
"""检查地板材质 M_SteelLight 和 M_Steel 的参数与基础颜色。"""
import unreal

MATS = [
    "/Game/RobotGame/Art/Environment/M_SteelLight",
    "/Game/RobotGame/Art/Environment/M_Steel",
    "/Game/RobotGame/Art/Environment/M_Joint",
    "/Game/RobotGame/Art/Environment/M_Copper",
]

out = []
for p in MATS:
    if not unreal.EditorAssetLibrary.does_asset_exist(p):
        out.append("%s 不存在" % p)
        continue
    m = unreal.EditorAssetLibrary.load_asset(p)
    out.append("=== %s (class=%s) ===" % (p, m.get_class().get_name()))
    if isinstance(m, unreal.MaterialInstance):
        out.append("  parent = %s" % (m.parent.get_path_name() if m.parent else "None"))
        for sp in m.get_editor_property("scalar_parameter_values"):
            out.append("  scalar: %s = %f" % (sp.get_editor_property("parameter_info").name, sp.get_editor_property("parameter_value")))
        for vp in m.get_editor_property("vector_parameter_values"):
            out.append("  vector: %s = %s" % (vp.get_editor_property("parameter_info").name, vp.get_editor_property("parameter_value")))
    elif isinstance(m, unreal.Material):
        out.append("  Base Material, shading_model=%s" % m.get_editor_property("shading_model"))

with open(r"C:\Users\25227\Documents\robot_game\docs\floor_mats.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
    f.write("\nFLOOR_MATS_DONE\n")
