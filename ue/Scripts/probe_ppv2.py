# -*- coding: utf-8 -*-
import unreal
L = "[PPV调色]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
ATTRS = ["override_color_gain", "color_gain", "override_color_saturation",
         "color_saturation", "override_color_contrast", "color_contrast",
         "override_color_gamma", "color_gamma", "override_white_temp",
         "white_temp", "override_white_tint", "white_tint",
         "override_auto_exposure_bias", "auto_exposure_bias",
         "override_bloom_intensity", "bloom_intensity",
         "override_scene_fringe_intensity", "scene_fringe_intensity",
         "override_vignette_intensity", "vignette_intensity"]
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "PostProcessVolume":
        continue
    s = a.get_editor_property("settings")
    unreal.log("%s ── %s 无界=%s 优先级=%.0f ──"
               % (L, a.get_actor_label(), a.get_editor_property("unbound"),
                  a.get_editor_property("priority")))
    for n in ATTRS:
        try:
            v = s.get_editor_property(n)
            if isinstance(v, unreal.LinearColor) or isinstance(v, unreal.Vector4):
                txt = "(%.3f, %.3f, %.3f, %.3f)" % (v.r, v.g, v.b, v.a)
            else:
                txt = str(v)
            unreal.log("%s   %-32s = %s" % (L, n, txt))
        except Exception:
            pass
