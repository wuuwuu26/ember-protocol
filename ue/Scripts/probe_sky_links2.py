# -*- coding: utf-8 -*-
"""检查天空材质节点连线（正确读取输入）。"""
import unreal

mat = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/M_SkyDome")
mel = unreal.MaterialEditingLibrary
exprs = mel.get_material_expressions(mat)
unreal.log("[连线2] 节点数=%d" % len(exprs))
for e in exprs:
    try:
        ins = mel.get_inputs_for_material_expression(mat, e)
        if not ins:
            unreal.log("[连线2] %-38s <- (无)" % e.get_name())
            continue
        for i in ins:
            try:
                # 输入对象本身是 MaterialExpression，带 input_name / output_name / expression
                names = [p for p in dir(i) if not p.startswith("_")]
                src = i.get_editor_property("expression") if "expression" in names else None
                inp = i.get_editor_property("input_name") if "input_name" in names else "?"
                out = i.get_editor_property("output_name") if "output_name" in names else "?"
                unreal.log("[连线2] %-38s <- %s [%s] src=%s" % (
                    e.get_name(), inp, out, src.get_name() if src else "None"))
            except Exception as ex:
                unreal.log("[连线2] %s 项读取失败: %s" % (e.get_name(), str(ex)[:120]))
    except Exception as ex:
        unreal.log("[连线2] %s 读取失败: %s" % (e.get_name(), str(ex)[:120]))
unreal.log("[连线2] 完成")