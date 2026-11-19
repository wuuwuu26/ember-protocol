# -*- coding: utf-8 -*-
import unreal
L = "[平行光]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "DirectionalLight":
        continue
    n += 1
    c = a.get_editor_property("light_component")
    for pn in ("intensity", "affects_world", "visible", "cast_shadows",
               "mobility", "light_channel", "indirect_lighting_intensity",
               "atmosphere_sun_light", "use_temperature", "temperature",
               "light_color", "specular_scale", "diffuse_scale"):
        try:
            v = c.get_editor_property(pn)
            if hasattr(v, "r"):
                v = "(%d,%d,%d)" % (v.r, v.g, v.b)
            unreal.log("%s #%d %-28s = %s" % (L, n, pn, v))
        except Exception as e:
            unreal.log("%s #%d %-28s ❌ %s" % (L, n, pn, str(e)[:40]))
unreal.log("%s 共 %d 盏平行光" % (L, n))
