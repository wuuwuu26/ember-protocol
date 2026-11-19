# -*- coding: utf-8 -*-
"""把天空穹顶裁掉，改为纯大气天空，并把天光强度按实测调到可用。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if "SkyDome" in a.get_actor_label():
        unreal.EditorLevelLibrary.destroy_actor(a)
        unreal.log("[收尾] 删除残留穹顶 %s" % a.get_actor_label())
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()
unreal.log("[收尾] 完成")