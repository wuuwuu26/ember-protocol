# -*- coding: utf-8 -*-
"""检查天空材质节点连线。"""
import unreal

mat = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/M_SkyDome")
mel = unreal.MaterialEditingLibrary
exprs = mel.get_material_expressions(mat)
unreal.log("[材质连线] 节点数=%d" % len(exprs))
for e in exprs:
    try:
        ins = mel.get_inputs_for_material_expression(mat, e)
        if ins:
            for i in ins:
                try:
                    expr = i.get_editor_property("expression")
                    out = i.get_editor_property("output_name")
                    inp = i.get_editor_property("input_name")
                    unreal.log("[材质连线] %-38s [%s] <- %s.%s" % (
                        e.get_name(), e.get_class().get_name(),
                        expr.get_name() if expr else "None", out))
                except Exception as ex:
                    unreal.log("[材质连线]   %s 项读取失败: %s" % (e.get_name(), str(ex)[:100]))
        else:
            unreal.log("[材质连线] %-38s [%s] <- (无)" % (e.get_name(), e.get_class().get_name()))
    except Exception as ex:
        unreal.log("[材质连线] %s 读取失败: %s" % (e.get_name(), str(ex)[:120]))
unreal.log("[材质连线] 完成")