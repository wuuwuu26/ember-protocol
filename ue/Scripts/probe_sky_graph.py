# -*- coding: utf-8 -*-
"""打印 M_SkyDome 的表达式常量与连线，确认天空材质真的按预期构建。

为什么需要：调完天空强度后实测天空像素几乎没变（B 0.056 → 0.059），
说明"看到的天空"可能根本不是这个材质。这个探针把材质图原样打出来，
用事实排除"材质没生效"这一层。
"""
import unreal

MAT = "/Game/RobotGame/Art/Materials/M_SkyDome"
L = "[天空探针]"

mat = unreal.EditorAssetLibrary.load_asset(MAT)
if not mat:
    unreal.log("%s ❌ 找不到 %s" % (L, MAT))
    raise SystemExit(1)

mel = unreal.MaterialEditingLibrary
exprs = mel.get_material_expressions(mat)
unreal.log("%s 表达式数量 = %d" % (L, len(exprs)))

for e in exprs:
    cls = e.get_class().get_name()
    name = ""
    try:
        name = e.get_editor_property("parameter_name")
    except Exception:
        pass
    val = ""
    if cls == "MaterialExpressionConstant":
        try:
            val = "R=%.4f" % e.get_editor_property("r")
        except Exception:
            pass
    elif cls == "MaterialExpressionConstant3Vector":
        try:
            c = e.get_editor_property("constant")
            val = "(%.3f, %.3f, %.3f)" % (c.r, c.g, c.b)
        except Exception:
            pass
    unreal.log("%s   %s %s %s" % (L, cls, name, val))

unreal.log("%s emissive 输入是否已接 = %s"
           % (L, mel.get_material_property_input_node(mat, unreal.MaterialProperty.MP_EMISSIVE_COLOR)))
unreal.log("%s 完成" % L)
