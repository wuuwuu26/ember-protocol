# -*- coding: utf-8 -*-
import unreal
L = "[太阳]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "DirectionalLight":
        continue
    r = a.get_actor_rotation()
    c = a.get_editor_property("light_component")
    unreal.log("%s rot=(pitch=%.1f yaw=%.1f roll=%.1f) 强度=%.0f 色温=%s mob=%s"
               % (L, r.pitch, r.yaw, r.roll, c.get_editor_property("intensity"),
                  c.get_editor_property("temperature"),
                  c.get_editor_property("mobility")))
