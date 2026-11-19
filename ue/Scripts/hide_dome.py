# -*- coding: utf-8 -*-
import sys
import unreal
L = "[穹顶开关]"
hide = (sys.argv[1] == "1") if len(sys.argv) > 1 else True
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    if "SkyDome" not in a.get_actor_label():
        continue
    a.set_editor_property("is_temporarily_hidden_in_editor", hide)
    smc = a.static_mesh_component
    smc.set_editor_property("visible", not hide)
    n += 1
    unreal.log("%s %s 隐藏=%s" % (L, a.get_actor_label(), hide))
# 顺便查一下 Lumen 与穹顶材质
try:
    m = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/M_SkyDome")
    if m:
        for p in ("shading_model", "two_sided", "blend_mode"):
            try:
                unreal.log("%s 材质 %s=%s" % (L, p, m.get_editor_property(p)))
            except Exception:
                pass
except Exception:
    pass
unreal.EditorLevelLibrary.save_current_level()
unreal.log("%s 处理 %d 个穹顶" % (L, n))
