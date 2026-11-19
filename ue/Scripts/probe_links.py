# -*- coding: utf-8 -*-
import unreal
L = "[连线检查]"
m = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/M_RobotSurface")
mel = unreal.MaterialEditingLibrary
for e in mel.get_material_expressions(m):
    cn = e.get_class().get_name()
    if "MaterialFunctionCall" not in cn:
        continue
    try:
        fn = e.get_editor_property("material_function")
        unreal.log("%s 函数节点 = %s" % (L, fn.get_name() if fn else "空"))
    except Exception as ex:
        unreal.log("%s 读 material_function 失败 %s" % (L, str(ex)[:60]))
    try:
        fis = e.get_editor_property("function_inputs")
        for i, fi in enumerate(fis):
            src = fi.get_editor_property("input")
            se = None
            try:
                se = src.get_editor_property("expression")
            except Exception:
                pass
            unreal.log("%s   输入%d %s <- %s" % (
                L, i, fi.get_editor_property("input_name"),
                se.get_class().get_name() if se else "空"))
    except Exception as ex:
        unreal.log("%s 读 function_inputs 失败 %s" % (L, str(ex)[:80]))
