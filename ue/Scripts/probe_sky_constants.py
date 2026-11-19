# -*- coding: utf-8 -*-
"""列出天空材质里的颜色常量，便于精确改色。"""
import unreal

mat = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/M_SkyDome")
unreal.log("[天空常量] mat=%s is_sky=%s" % (mat.get_name(), mat.get_editor_property("is_sky")))
for e in mat.get_editor_property("expressions"):
    if e.get_class().get_name() == "MaterialExpressionConstant3Vector":
        try:
            c = e.get_editor_property("constant")
            unreal.log("[天空常量] %s pos=(%d,%d) rgb=(%.3f,%.3f,%.3f)" % (
                e.get_name(), e.get_editor_property("material_expression_editor_x"),
                e.get_editor_property("material_expression_editor_y"), c.r, c.g, c.b))
        except Exception as ex:
            unreal.log("[天空常量] 读取失败 %s" % ex)
    elif e.get_class().get_name() == "MaterialExpressionConstant":
        try:
            unreal.log("[天空常量] %s pos=(%d,%d) r=%.3f" % (
                e.get_name(), e.get_editor_property("material_expression_editor_x"),
                e.get_editor_property("material_expression_editor_y"),
                e.get_editor_property("r")))
        except Exception:
            pass
unreal.log("[天空常量] 完成")