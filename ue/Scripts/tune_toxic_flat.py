# -*- coding: utf-8 -*-
"""隔离实验：把毒液场高度场压平（max_height=0），判断近景斜纹来自几何还是材质。"""
import unreal

EAL = unreal.EditorAssetLibrary
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label().startswith("ToxicFluid_"):
        a.set_editor_property("max_height", 0.0)
        n += 1
unreal.EditorLevelLibrary.save_current_level()
unreal.log("TOXIC_FLAT_TEST_OK n=%d" % n)
