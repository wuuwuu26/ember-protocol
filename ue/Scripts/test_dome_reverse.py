# -*- coding: utf-8 -*-
"""测试：负缩放 + reverse culling，排查球面剔除。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "SkyDome":
        a.set_actor_scale3d(unreal.Vector(-20, -20, -20))
        c = a.static_mesh_component
        for name in ("reverse_culling", "b_reverse_culling", "bReverseCulling"):
            try:
                c.set_editor_property(name, True)
                unreal.log("[反向剔除] 设置成功: %s" % name)
            except Exception as e:
                unreal.log("[反向剔除] 设置失败: %s -> %s" % (name, str(e)[:80]))
        for name in ("reverse_culling", "b_reverse_culling", "bReverseCulling"):
            try:
                unreal.log("[反向剔除] 回读 %s = %s" % (name, c.get_editor_property(name)))
            except Exception:
                pass
        unreal.log("[反向剔除] 穹顶缩放=(-20,-20,-20)")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()
unreal.log("[反向剔除] 完成")