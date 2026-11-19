# -*- coding: utf-8 -*-
import unreal
L = "[灯光]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    cn = a.get_class().get_name()
    if cn == "DirectionalLight":
        c = a.get_editor_property("light_component")
        r = a.get_actor_rotation()
        col = c.get_editor_property("light_color")
        unreal.log("%s 太阳 rot(%.0f,%.0f) 强度=%.0f 色=(%.2f,%.2f,%.2f) 用色温=%s 温度=%.0f"
                   % (L, r.pitch, r.yaw, c.get_editor_property("intensity"),
                      col.r, col.g, col.b,
                      c.get_editor_property("use_temperature"),
                      c.get_editor_property("temperature")))
    elif cn == "SkyLight":
        c = a.get_editor_property("light_component")
        col = c.get_editor_property("light_color")
        unreal.log("%s 天光 强度=%.2f 色=(%.2f,%.2f,%.2f) 实时捕获=%s"
                   % (L, c.get_editor_property("intensity"), col.r, col.g, col.b,
                      c.get_editor_property("real_time_capture")))
    elif cn == "ExponentialHeightFog":
        c = a.get_editor_property("component")
        ins = c.get_editor_property("fog_inscattering_color")
        unreal.log("%s 雾 密度=%.5f 散射色=(%.3f,%.3f,%.3f) 散射光=%.2f 高度衰减=%.3f"
                   % (L, c.get_editor_property("fog_density"), ins.r, ins.g, ins.b,
                      c.get_editor_property("directional_inscattering_luminance"),
                      c.get_editor_property("fog_height_falloff")))
    elif cn == "PostProcessVolume":
        s = a.get_editor_property("settings")
        def g(n, d=0.0):
            try:
                return getattr(s, n)
            except Exception:
                return d
        unreal.log("%s PPV 曝光方式=%s bias=%.2f 白平衡温度=%.0f 色相=%.2f"
                   % (L, g("auto_exposure_method"), g("auto_exposure_bias"),
                      g("white_temp"), g("white_tint")))
