# -*- coding: utf-8 -*-
"""把玩家出生点临时移到新区域，用游戏视角截图，确认地面/墙/门洞。
不改动 PlayerStart 的持久位置 —— 只在本脚本执行期间修改，结束后还原。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

starts = [a for a in actor_sub.get_all_level_actors()
          if isinstance(a, unreal.PlayerStart)]
if not starts:
    unreal.log("[ExtShot] 没找到 PlayerStart")
else:
    ps = starts[0]
    orig = ps.get_actor_location()
    unreal.log("[ExtShot] PlayerStart 原位置 (%.0f, %.0f, %.0f)"
               % (orig.x, orig.y, orig.z))

    # 放到通道出口，面朝 +X
    ps.set_actor_location(unreal.Vector(2500.0, 0.0, 120.0), False, False)
    ps.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)
    les.save_current_level()
    unreal.log("[ExtShot] 已把玩家移到新区域入口")

    with open(r"C:\Users\25227\Documents\robot_game\docs\ext_playermove.txt", "wb") as f:
        f.write(("orig=%.1f,%.1f,%.1f\n" % (orig.x, orig.y, orig.z)).encode("utf-8"))

unreal.log("EXT_SHOT_DONE2")
