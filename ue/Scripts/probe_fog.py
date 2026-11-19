# -*- coding: utf-8 -*-
import unreal
L = "[雾属性]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    cn = a.get_class().get_name()
    if "Fog" not in cn:
        continue
    for pn in ("component", "height_fog_component", "exponential_height_fog_component"):
        try:
            comp = a.get_editor_property(pn)
        except Exception:
            comp = None
        if comp:
            unreal.log("%s 组件属性名 = %s" % (L, pn))
            break
    else:
        unreal.log("%s ❌ 找不到雾组件" % L)
        continue
    names = [p for p in dir(comp) if "fog" in p.lower() or "inscatt" in p.lower()]
    for n in sorted(names):
        try:
            v = comp.get_editor_property(n)
        except Exception:
            v = "<不可读>"
        unreal.log("%s   %-42s = %s" % (L, n, v))
