# -*- coding: utf-8 -*-
import unreal
L = "[灯光状态]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    cn = a.get_class().get_name()
    if cn == "DirectionalLight":
        c = a.get_editor_property("light_component")
        unreal.log("%s 太阳 intensity=%.0f mobility=%s" % (L, c.get_editor_property("intensity"), c.get_editor_property("mobility")))
    elif cn == "SkyLight":
        c = a.get_editor_property("light_component")
        unreal.log("%s 天光 intensity=%.2f realtime=%s mobility=%s" % (
            L, c.get_editor_property("intensity"),
            c.get_editor_property("real_time_capture"),
            c.get_editor_property("mobility")))
    elif cn == "PostProcessVolume":
        s = a.get_editor_property("settings")
        try:
            unreal.log("%s 后处理 方法=%s 曝光min=%.2f max=%.2f" % (
                L, s.get_editor_property("auto_exposure_method"),
                s.get_editor_property("auto_exposure_min_brightness"),
                s.get_editor_property("auto_exposure_max_brightness")))
        except Exception as e:
            unreal.log("%s 后处理读取失败 %s" % (L, e))
