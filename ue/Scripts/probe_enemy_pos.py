"""列出关卡里所有敌人 actor 的位置与标签，便于对准近景相机。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)
n = 0
for a in ELL.get_all_level_actors():
    lbl = a.get_actor_label()
    cls = a.get_class().get_name()
    if "Enemy" in cls or "enemy" in lbl.lower():
        loc = a.get_actor_location()
        print("[ep] %-22s %-18s (%.0f, %.0f, %.0f)" % (lbl, cls, loc.x, loc.y, loc.z))
        n += 1
print("ENEMY_POS_OK n=%d" % n)
