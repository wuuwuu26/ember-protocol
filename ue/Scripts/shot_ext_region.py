# -*- coding: utf-8 -*-
"""在编辑器里把视口移到新区域并截图，确认几何是否正确。

不依赖游戏视角：直接用 LevelEditorSubsystem 的视口 API 设定机位。
"""
import unreal

OUT_DIR = r"C:\Users\25227\Documents\robot_game\docs\ext_shots"
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)

# 统计扩建 actor
region = []
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        continue
    if "ExtRegion" in tags:
        region.append(a)

xs = [a.get_actor_location().x for a in region]
ys = [a.get_actor_location().y for a in region]
unreal.log("[ExtShot] region actors=%d  X %.0f..%.0f  Y %.0f..%.0f"
           % (len(region), min(xs), max(xs), min(ys), max(ys)))


def shot(name, loc, rot):
    try:
        les.set_level_viewport_camera_info(
            unreal.Vector(*loc), unreal.Rotator(*rot), "")
        unreal.SystemLibrary.execute_console_command(
            None, 'HighResShot 1280x720 filename="%s/%s.png"' % (OUT_DIR, name))
        unreal.log("[ExtShot] took %s" % name)
    except Exception as e:
        unreal.log("[ExtShot] fail %s: %s" % (name, e))


# 俯视新区域
shot("top_new", (3800.0, 0.0, 2600.0), (-89.9, 0.0, 0.0))
# 从通道口看新区域
shot("from_tunnel", (2300.0, 0.0, 200.0), (0.0, 0.0, 0.0))
# 从新区域远端回看通道
shot("from_far", (5100.0, 0.0, 200.0), (0.0, 180.0, 0.0))

unreal.log("EXT_SHOT_DONE")
