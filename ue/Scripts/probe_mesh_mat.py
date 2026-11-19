# -*- coding: utf-8 -*-
import unreal
L = "[网格材质]"
for p in ("/Game/RobotGame/Art/Characters/SK_Chassis_Medium",
          "/Game/RobotGame/Art/Characters/SK_Chassis_Light"):
    m = unreal.EditorAssetLibrary.load_asset(p)
    if not m:
        unreal.log("%s ❌ %s" % (L, p))
        continue
    try:
        mats = m.get_editor_property("materials")
    except Exception:
        mats = []
    unreal.log("%s %s 材质槽 %d 个" % (L, p.split("/")[-1], len(mats)))
    for i, it in enumerate(mats):
        try:
            mi = it.get_editor_property("material_interface")
            unreal.log("%s   槽%d → %s" % (L, i, mi.get_name() if mi else "空"))
        except Exception as e:
            unreal.log("%s   槽%d 读取失败 %s" % (L, i, str(e)[:50]))
