import unreal
mat = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/M_SkyDome")
mel = unreal.MaterialEditingLibrary
unreal.log("[表达式] 方法: %s" % [m for m in dir(mel) if "expression" in m.lower()])
try:
    exprs = mel.get_material_expressions(mat)
    unreal.log("[表达式] 数量=%d" % len(exprs))
    for e in exprs:
        if e.get_class().get_name() in ("MaterialExpressionConstant3Vector", "MaterialExpressionConstant"):
            try:
                c = e.get_editor_property("constant")
                unreal.log("[表达式] %s %s pos=(%d,%d) rgb=(%.3f,%.3f,%.3f)" % (
                    e.get_class().get_name(), e.get_name(),
                    e.get_editor_property("material_expression_editor_x"),
                    e.get_editor_property("material_expression_editor_y"), c.r, c.g, c.b))
            except Exception:
                unreal.log("[表达式] %s %s r=%.3f" % (e.get_class().get_name(), e.get_name(), e.get_editor_property("r")))
except Exception as e:
    unreal.log("[表达式] 失败: %s" % e)
unreal.log("[表达式] 完成")