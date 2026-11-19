# -*- coding: utf-8 -*-
"""把天空穹顶材质设为双面，并恢复穹顶使用它。

穹顶是一个球，法线朝外；从内部看是被**背面剔除**的 —— 所以整个天空
其实一直是"空"的（渲染出来是近黑的 void），之前看到的蓝色天空
是 SkyAtmosphere 画出来的。大气层一关，天空就黑了。
"""
import unreal
L = "[穹顶双面]"
m = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/M_SkyDome")
if m:
    try:
        m.set_editor_property("two_sided", True)
        unreal.MaterialEditingLibrary.recompile_material(m)
        unreal.EditorAssetLibrary.save_loaded_asset(m)
        unreal.log("%s M_SkyDome 双面=%s" % (L, m.get_editor_property("two_sided")))
    except Exception as e:
        unreal.log("%s ⚠️ 设置失败: %s" % (L, str(e)[:70]))

unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    if "SkyDome" not in a.get_actor_label():
        continue
    smc = a.static_mesh_component
    if m:
        smc.set_material(0, m)
    smc.set_editor_property("visible", True)
    n += 1
unreal.EditorLevelLibrary.save_current_level()
unreal.log("%s 恢复 %d 个穹顶材质" % (L, n))
