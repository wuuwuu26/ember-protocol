# -*- coding: utf-8 -*-
"""删除 SkyAtmosphere 并保存所有脏关卡。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
log = unreal.log

w = unreal.EditorLevelLibrary.get_editor_world()
log("[大气修复] world=%s" % w.get_name())

count = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() == "SkyAtmosphere":
        log("[大气修复] 删除 %s (outer=%s)" % (a.get_actor_label(), a.get_outer().get_name()))
        unreal.EditorLevelLibrary.destroy_actor(a)
        count += 1
log("[大气修复] 删除 %d 个" % count)
les.save_all_dirty_levels()
log("[大气修复] 已保存所有脏关卡")

for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() == "SkyAtmosphere":
        log("[大气修复] ⚠️ 仍存在 %s" % a.get_actor_label())
    if a.get_actor_label() == "SkyDome":
        c = a.static_mesh_component
        log("[大气修复] SkyDome 材质=%s visible=%s" % (
            [m.get_name() if m else "None" for m in c.get_materials()], c.is_visible()))
log("[大气修复] 完成")