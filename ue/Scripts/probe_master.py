# -*- coding: utf-8 -*-
import unreal
L = "[母材质]"
m = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/M_RobotSurface")
unreal.log("%s 母材质=%s" % (L, m))
if m:
    try:
        unreal.log("%s 表达式数=%d" % (L, len(unreal.MaterialEditingLibrary.get_material_expressions(m))))
    except Exception as e:
        unreal.log("%s 读表达式失败 %s" % (L, e))
    try:
        unreal.log("%s 编译结果=%s" % (L, unreal.MaterialEditingLibrary.recompile_material(m)))
    except Exception as e:
        unreal.log("%s 编译异常 %s" % (L, e))
for p in ("/Game/RobotGame/Art/Environment/M_Steel",
          "/Game/RobotGame/Art/Characters/M_Steel"):
    mi = unreal.EditorAssetLibrary.load_asset(p)
    if not mi:
        unreal.log("%s 找不到 %s" % (L, p))
        continue
    par = mi.get_editor_property("parent")
    unreal.log("%s %s 父=%s" % (L, p, par.get_name() if par else "空"))
