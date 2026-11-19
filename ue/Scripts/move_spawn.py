# -*- coding: utf-8 -*-
"""临时把 PlayerStart 挪到指定位置（验证围栏用）。参数从环境变量读。"""
import os
import unreal

L = "[出生点]"
X = float(os.environ.get("SPAWN_X", "-200"))
Y = float(os.environ.get("SPAWN_Y", "0"))
Z = float(os.environ.get("SPAWN_Z", "130"))
YAW = float(os.environ.get("SPAWN_YAW", "0"))

unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() == "PlayerStart":
        a.set_actor_location_and_rotation(
            unreal.Vector(X, Y, Z), unreal.Rotator(0, YAW, 0), False, False)
        n += 1
        unreal.log("%s PlayerStart → (%.0f,%.0f,%.0f) yaw=%.0f" % (L, X, Y, Z, YAW))
unreal.EditorLevelLibrary.save_current_level()
unreal.log("%s 共移动 %d 个出生点" % (L, n))
