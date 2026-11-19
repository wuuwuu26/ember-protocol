# -*- coding: utf-8 -*-
"""检查 M_Bolt_* 的 EmissiveColor 输入到底连没连上。"""
import unreal

OUT = r"C:\Users\25227\Documents\robot_game\docs\bolt_probe2.txt"
lines = []

for name in ("M_Bolt_Player", "M_Bolt_Enemy"):
    path = "/Game/RobotGame/Art/Materials/%s" % name
    mat = unreal.EditorAssetLibrary.load_asset(path)
    lines.append("== %s ==" % name)
    if not mat:
        lines.append("  MISSING")
        continue
    for prop in (unreal.MaterialProperty.MP_EMISSIVE_COLOR,
                 unreal.MaterialProperty.MP_BASE_COLOR):
        try:
            n = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, prop)
            lines.append("  %s -> %s" % (prop, (n.get_name() + " (" + n.get_class().get_name() + ")") if n else "None"))
        except Exception as e:
            lines.append("  %s read fail: %s" % (prop, str(e)[:120]))

    # 重新连一次，看看是否有报错
    exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat)
    if exprs:
        try:
            unreal.MaterialEditingLibrary.connect_material_property(
                exprs[0], "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
            lines.append("  reconnect('') ok")
        except Exception as e:
            lines.append("  reconnect('') fail: %s" % str(e)[:200])
        try:
            n = unreal.MaterialEditingLibrary.get_material_property_input_node(
                mat, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
            lines.append("  after reconnect -> %s" % ((n.get_name() + " (" + n.get_class().get_name() + ")") if n else "None"))
        except Exception as e:
            lines.append("  after reconnect read fail: %s" % str(e)[:120])
        try:
            ok = unreal.MaterialEditingLibrary.recompile_material(mat)
            lines.append("  recompile=%s" % ok)
            unreal.EditorAssetLibrary.save_asset(path)
            lines.append("  saved")
        except Exception as e:
            lines.append("  recompile fail: %s" % str(e)[:200])

with open(OUT, "w") as f:
    f.write("\n".join(lines))
    f.write("\nBOLTPROBE2_DONE\n")
