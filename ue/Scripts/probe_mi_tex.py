# -*- coding: utf-8 -*-
import unreal
L = "[MI贴图]"
for p in ("/Game/RobotGame/Art/Characters/M_Steel",
          "/Game/RobotGame/Art/Environment/M_Steel",
          "/Game/RobotGame/Art/Environment/M_Joint"):
    mi = unreal.EditorAssetLibrary.load_asset(p)
    if not mi:
        unreal.log("%s ❌ %s" % (L, p)); continue
    try:
        tps = mi.get_editor_property("texture_parameter_values")
    except Exception as e:
        unreal.log("%s %s 读不到 texture_parameter_values: %s" % (L, p, str(e)[:60]))
        continue
    if not tps:
        unreal.log("%s %-40s ❌ 没有任何贴图参数覆盖" % (L, p))
        continue
    for it in tps:
        try:
            n = it.get_editor_property("parameter_info").get_editor_property("name")
            v = it.get_editor_property("parameter_value")
            unreal.log("%s %-40s %s = %s" % (L, p, n, v.get_name() if v else "空"))
        except Exception as e:
            unreal.log("%s 读取失败 %s" % (L, str(e)[:60]))
