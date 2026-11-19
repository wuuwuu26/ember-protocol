# -*- coding: utf-8 -*-
"""检查 M_Bolt_Player / M_Bolt_Enemy 是否真的是 Unlit + Emissive 已连接。"""
import unreal

OUT = r"C:\Users\25227\Documents\robot_game\docs\bolt_probe.txt"
lines = []

for name in ("M_Bolt_Player", "M_Bolt_Enemy"):
    path = "/Game/RobotGame/Art/Materials/%s" % name
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        lines.append("%s MISSING" % name)
        continue
    mat = unreal.EditorAssetLibrary.load_asset(path)
    lines.append("== %s ==" % name)
    for prop in ("shading_model", "blend_mode", "two_sided",
                 "used_with_static_lighting", "emissive_color"):
        try:
            lines.append("  %s = %s" % (prop, mat.get_editor_property(prop)))
        except Exception as e:
            lines.append("  %s read fail: %s" % (prop, str(e)[:80]))
    exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat)
    lines.append("  expressions = %d" % len(exprs))
    for e in exprs:
        row = "    %s (%s)" % (e.get_name(), e.get_class().get_name())
        try:
            row += " name=%s" % e.get_editor_property("parameter_name")
        except Exception:
            pass
        try:
            row += " val=%s" % e.get_editor_property("default_value")
        except Exception:
            pass
        lines.append(row)
    # 是否有输出连到 Emissive
    try:
        inputs = unreal.MaterialEditingLibrary.get_inputs_for_material_expression(mat, exprs[0]) if exprs else []
        lines.append("  outputs->%s" % inputs)
    except Exception as e:
        lines.append("  outputs read fail: %s" % str(e)[:80])

with open(OUT, "w") as f:
    f.write("\n".join(lines))
    f.write("\nBOLTPROBE_DONE\n")
