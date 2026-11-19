"""核对 -EnemyAt / -EnemyAtIndex 是否生效：读关卡 actor 的位置（编辑器视角看不到运行时位移，
这里改为直接在游戏里打印）。本脚本只打印编辑器里的原始位置作参照。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)
for a in ELL.get_all_level_actors():
    if "BP_Enemy" in a.get_class().get_name():
        loc = a.get_actor_location()
        print("[orig] %-12s (%.0f,%.0f,%.0f)" % (a.get_actor_label(), loc.x, loc.y, loc.z))
print("ORIG_POS_OK")
