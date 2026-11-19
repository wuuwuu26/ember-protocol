# -*- coding: utf-8 -*-
"""确认 M_Bolt_* 的 Emissive 输入到底连了什么（这是"弹丸全黑"的关键）。"""
import unreal

OUT = r"C:\Users\25227\Documents\robot_game\docs\bolt_probe2.txt"
lines = []


def describe(node):
    if not node:
        return "None"
    s = "%s (%s)" % (node.get_name(), node.get_class().get_name())
    for prop in ("parameter_name", "default_value", "r", "g", "b"):
        try:
            s += " %s=%s" % (prop, node.get_editor_property(prop))
        except Exception:
            pass
    return s


for name in ("M_Bolt_Player", "M_Bolt_Enemy"):
    path = "/Game/RobotGame/Art/Materials/%s" % name
    mat = unreal.EditorAssetLibrary.load_asset(path)
    lines.append("== %s ==" % name)
    for pin in ("MP_EMISSIVE_COLOR", "MP_BASE_COLOR", "MP_OPACITY"):
        prop = getattr(unreal.MaterialProperty, pin)
        try:
            node = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, prop)
            lines.append("  %s <- %s" % (pin, describe(node)))
        except Exception as e:
            lines.append("  %s query fail: %s" % (pin, str(e)[:100]))
    try:
        lines.append("  recompile=%s" % unreal.MaterialEditingLibrary.recompile_material(mat))
    except Exception as e:
        lines.append("  recompile fail: %s" % str(e)[:100])

# 顺带把一个已知渲染正常的自发光材质当参照
ref = "/Game/RobotGame/Art/Characters/M_Core_enemy_guard"
if unreal.EditorAssetLibrary.does_asset_exist(ref):
    m = unreal.EditorAssetLibrary.load_asset(ref)
    lines.append("== REF %s shading=%s ==" % (ref, m.get_editor_property("shading_model")))
    try:
        node = unreal.MaterialEditingLibrary.get_material_property_input_node(
            m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        lines.append("  EMISSIVE <- %s" % describe(node))
    except Exception as e:
        lines.append("  query fail: %s" % str(e)[:100])

with open(OUT, "w") as f:
    f.write("\n".join(lines))
    f.write("\nBOLTPROBE2_DONE\n")
