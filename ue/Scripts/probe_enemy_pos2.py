"""按外观找到双足敌人（园丁/气象/护卫）的实际位置，供相机对准。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)
for a in ELL.get_all_level_actors():
    if "BP_Enemy" not in a.get_class().get_name():
        continue
    loc = a.get_actor_location()
    print("[pos] %-14s (%.0f, %.0f, %.0f)" % (a.get_actor_label(), loc.x, loc.y, loc.z))
print("ENEMY_POS2_OK")
