# -*- coding: utf-8 -*-
import unreal
L = "[穹顶]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    if "SkyDome" not in a.get_actor_label():
        continue
    smc = a.static_mesh_component
    smc.set_editor_property("visible", True)
    a.set_editor_property("is_temporarily_hidden_in_editor", False)
    try:
        smc.set_editor_property("cast_shadow", False)
    except Exception:
        pass
    n += 1
    mat = smc.get_material(0)
    unreal.log("%s %s 材质=%s" % (L, a.get_actor_label(), mat.get_name() if mat else "空"))
# 打印穹顶材质的关键常量
MEL = unreal.MaterialEditingLibrary
m = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/M_SkyDome")
if m:
    for e in MEL.get_material_expressions(m):
        cn = e.get_class().get_name()
        if cn != "MaterialExpressionConstant3Vector":
            continue
        try:
            v = e.get_editor_property("constant")
            if hasattr(v, "r") and (v.r > 0.05 or v.g > 0.05 or v.b > 0.05):
                unreal.log("%s   常量 (%.3f, %.3f, %.3f)" % (L, v.r, v.g, v.b))
        except Exception:
            pass
unreal.EditorLevelLibrary.save_current_level()
unreal.log("%s 显示 %d 个穹顶" % (L, n))
