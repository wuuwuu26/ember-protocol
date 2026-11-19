"""打掉双足敌人（园丁）左腿，用于验证独腿支撑补偿。在 PIE 运行中由控制台执行不方便，
改为：给 ARobotEnemy 加调试参数 -EnemyBreakLeg=<L/R>，BeginPlay 时直接打断指定腿。
本脚本只负责确认园丁的出生位置，实际打断由启动参数完成。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)

for a in ELL.get_all_level_actors():
    if "BP_Enemy" in a.get_class().get_name():
        loc = a.get_actor_location()
        print("[bpos] %-12s (%.0f,%.0f,%.0f)" % (a.get_actor_label(), loc.x, loc.y, loc.z))
print("BIPED_BREAK_POS_OK")
