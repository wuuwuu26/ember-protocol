# -*- coding: utf-8 -*-
import unreal
L = "[材质图]"
m = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/M_RobotSurface")
mel = unreal.MaterialEditingLibrary
exprs = mel.get_material_expressions(m)
unreal.log("%s 共 %d 个节点" % (L, len(exprs)))
for e in exprs:
    cn = e.get_class().get_name()
    nm = ""
    try:
        nm = e.get_editor_property("parameter_name")
    except Exception:
        pass
    try:
        nm2 = e.get_editor_property("function_name") if "Function" in cn else ""
    except Exception:
        nm2 = ""
    if cn in ("MaterialExpressionMaterialFunctionCall", "MaterialExpressionTextureObjectParameter",
              "MaterialExpressionTextureSampleParameter2D", "MaterialExpressionComponentMask",
              "MaterialExpressionLinearInterpolate", "MaterialExpressionMultiply"):
        ins = mel.get_inputs_for_material_expression(m, e)
        desc = ", ".join("%s<-%s" % (i.input_name, i.expression.get_class().get_name() if i.expression else "空")
                         for i in ins)
        unreal.log("%s %-46s %s %s | 输入: %s" % (L, cn, nm, nm2, desc))
