# -*- coding: utf-8 -*-
"""判定测试：把两个泡沫圆盘的 override 换成高对比的 M_Copper（有明显纹理/颜色），保存。

若浅色半圆变成铜色有纹理 -> 就是这两个圆盘，问题在材质；
若仍是浅色 -> 是别的几何（RobotCoolantField/GeoCache）。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary

copper = EAL.load_asset("/Game/RobotGame/Art/Environment/M_Copper")
n = 0
for a in sub.get_all_level_actors():
    if a.get_actor_label() not in ("Splash_FoamRing", "Splash_FoamDisc"):
        continue
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    c = a.static_mesh_component
    c.set_editor_property("override_materials", [copper])
    c.set_visibility(True)   # 确保可见
    n += 1
les.save_current_level()
unreal.log("SPLASH_COPPER_DONE n=%d" % n)
