# -*- coding: utf-8 -*-
"""只读探针：统计关卡里的点光/聚光灯。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)


def g(o, a, d=None):
    try:
        return o.get_editor_property(a)
    except Exception:
        return d


spots = []
points = []
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    cn = a.get_class().get_name()
    if cn not in ("SpotLight", "PointLight"):
        continue
    comp = None
    for p in ("spot_light_component", "point_light_component", "light_component"):
        comp = g(a, p)
        if comp:
            break
    loc = a.get_actor_location()
    row = (a.get_actor_label(), loc.x, loc.y, loc.z,
           g(comp, "intensity"), g(comp, "attenuation_radius"),
           g(comp, "temperature"), g(comp, "use_temperature"),
           g(comp, "cast_shadows"))
    (spots if cn == "SpotLight" else points).append(row)

unreal.log("[灯光清单] 聚光灯 %d 盏" % len(spots))
for r in spots:
    unreal.log("[灯光清单]   %-18s @ (%.0f,%.0f,%.0f) I=%.0f R=%.0f T=%.0f useT=%s shadow=%s" % r)
unreal.log("[灯光清单] 点光 %d 盏" % len(points))
for r in points:
    unreal.log("[灯光清单]   %-18s @ (%.0f,%.0f,%.0f) I=%.0f R=%.0f T=%.0f useT=%s shadow=%s" % r)
unreal.log("[灯光清单] 完成")