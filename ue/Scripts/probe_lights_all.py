# -*- coding: utf-8 -*-
import unreal
L = "[全部灯光]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
cnt = {}
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    cn = a.get_class().get_name()
    if "Light" not in cn:
        continue
    cnt[cn] = cnt.get(cn, 0) + 1
    if cn in ("PointLight", "SpotLight", "RectLight"):
        c = a.get_editor_property("light_component")
        col = c.get_editor_property("light_color")
        loc = a.get_actor_location()
        unreal.log("%s %-10s %-14s 强度=%8.0f 色=(%3d,%3d,%3d) 位置=(%.0f,%.0f,%.0f)"
                   % (L, cn, a.get_actor_label()[:14],
                      c.get_editor_property("intensity"),
                      col.r, col.g, col.b, loc.x, loc.y, loc.z))
unreal.log("%s 统计: %s" % (L, cnt))
