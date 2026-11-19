# -*- coding: utf-8 -*-
"""曝光-灯光平衡：太阳减半，曝光 +1 档，局部补光等效翻倍。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)
log = lambda m: unreal.log("[曝光平衡] %s" % m)


def g(o, a, d=None):
    try:
        return o.get_editor_property(a)
    except Exception:
        return d


def setp(o, a, v, tag=""):
    try:
        o.set_editor_property(a, v)
        return True
    except Exception as e:
        log("  ❌ %s%s: %s" % (tag, a, str(e)[:90]))
        return False

for a in unreal.EditorLevelLibrary.get_all_level_actors():
    cn = a.get_class().get_name()
    if cn == "DirectionalLight":
        c = g(a, "directional_light_component") or g(a, "light_component")
        setp(c, "intensity", 11000.0, "Sun.")
        setp(c, "temperature", 5600.0, "Sun.")
        setp(c, "atmosphere_sun_light", True, "Sun.")
        log("太阳：11000 lux")
    elif cn == "SkyLight":
        c = g(a, "sky_light_component") or g(a, "light_component")
        setp(c, "intensity", 3.0, "Sky.")
        c.recapture_sky()
        log("天光：3.0")
    elif cn == "PostProcessVolume":
        st = g(a, "settings")
        if not st:
            continue
        setp(st, "override_auto_exposure_method", True, "PP.")
        setp(st, "auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL, "PP.")
        setp(st, "override_auto_exposure_bias", True, "PP.")
        setp(st, "auto_exposure_bias", 1.0, "PP.")
        setp(st, "override_color_saturation", True, "PP.")
        setp(st, "color_saturation", unreal.Vector4(0.90, 0.90, 0.92, 1.0), "PP.")
        setp(st, "override_color_contrast", True, "PP.")
        setp(st, "color_contrast", unreal.Vector4(1.08, 1.08, 1.10, 1.0), "PP.")
        log("PPV：bias=1 / 饱和 0.90 / 对比 1.08")

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()
log("完成")