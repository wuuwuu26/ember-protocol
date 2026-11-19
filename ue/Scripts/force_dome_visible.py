# -*- coding: utf-8 -*-
"""检查/强制 SkyDome 可见，并打印相机相关位置。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)
log = lambda m: unreal.log("[穹顶可见] %s" % m)

for a in unreal.EditorLevelLibrary.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl == "SkyDome":
        c = a.static_mesh_component
        log("actor class=%s outer=%s" % (a.get_class().get_name(), a.get_outer().get_name()))
        for attr in ("hidden", "bHidden", "is_editor_only_actor", "tags", "loc"):
            try:
                log("  actor.%s = %s" % (attr, a.get_editor_property(attr)))
            except Exception:
                pass
        for attr in ("hidden_in_game", "visible", "visible_in_real_time_sky_captures", "mobility", "cast_shadow"):
            try:
                log("  comp.%s = %s" % (attr, c.get_editor_property(attr)))
            except Exception as e:
                log("  comp.%s 读取失败" % attr)
        try:
            a.set_actor_hidden_in_game(False)
            c.set_editor_property("hidden_in_game", False)
            c.set_visibility(True, True)
            c.set_editor_property("visible_in_real_time_sky_captures", True)
            log("已强制 actor/component 可见")
        except Exception as e:
            log("强制可见失败: %s" % str(e)[:120])
    elif a.get_class().get_name() == "PlayerStart":
        p = a.get_actor_location()
        r = a.get_actor_rotation()
        log("PlayerStart @ (%.0f,%.0f,%.0f) yaw=%.0f" % (p.x, p.y, p.z, r.yaw))

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()
log("完成")