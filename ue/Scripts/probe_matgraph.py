# -*- coding: utf-8 -*-
"""检查 M_RobotSurface 的图：三平面函数的 WorldPosition 引脚到底接没接。"""
import unreal

LOG = "[材质图]"


def log(s):
    unreal.log("%s %s" % (LOG, s))


mat = unreal.EditorAssetLibrary.load_asset(
    "/Game/RobotGame/Art/Materials/M_RobotSurface")
if not mat:
    log("❌ 材质不存在")
    raise SystemExit(1)

mel = unreal.MaterialEditingLibrary
exprs = mel.get_material_expressions(mat)
log("表达式 %d 个" % len(exprs))

by_name = {}
for e in exprs:
    by_name[e.get_name()] = e

# 找 MaterialFunctionCall，看它的输入连接
for e in exprs:
    cn = e.get_class().get_name()
    if "MaterialFunctionCall" not in cn:
        continue
    fn = None
    try:
        fn = e.get_editor_property("material_function")
    except Exception:
        pass
    log("函数调用 %s  →  %s" % (e.get_name(), fn.get_name() if fn else "?"))
    try:
        for p in e.get_editor_property("function_inputs"):
            nm = p.get_editor_property("input_name")
            # 该输入是否被外部连上：查 input 的 Expression
            try:
                src = p.get_editor_property("input")
                src_expr = src.get_editor_property("expression") if src else None
            except Exception:
                src_expr = None
            log("    引脚 %-28s ← %s"
                % (nm, src_expr.get_name() if src_expr else "（未连接）"))
    except Exception as ex:
        log("    读引脚失败 %s" % str(ex)[:90])

# 顺带确认贴图参数
for e in exprs:
    cn = e.get_class().get_name()
    if "TextureObjectParameter" in cn:
        log("贴图参数 %s 默认值=%s"
            % (e.get_editor_property("parameter_name"),
               e.get_editor_property("texture")))
