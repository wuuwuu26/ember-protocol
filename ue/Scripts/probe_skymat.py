# -*- coding: utf-8 -*-
import unreal
L = "[天空材质]"
MEL = unreal.MaterialEditingLibrary
m = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/M_SkyDome")
if not m:
    unreal.log("%s ❌ 找不到 M_SkyDome" % L)
else:
    for e in MEL.get_material_expressions(m):
        cn = e.get_class().get_name()
        if cn not in ("MaterialExpressionConstant3Vector",
                      "MaterialExpressionConstant"):
            continue
        try:
            v = e.get_editor_property("constant")
        except Exception:
            continue
        if hasattr(v, "r"):
            unreal.log("%s %-14s (%.3f, %.3f, %.3f)"
                       % (L, cn.replace("MaterialExpression", ""), v.r, v.g, v.b))
        else:
            unreal.log("%s %-14s %.3f" % (L, cn.replace("MaterialExpression", ""), v))
