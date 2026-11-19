"""清掉所有诊断用 actor（DiagPatrol / DiagFill），让关卡回到正式状态。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)

removed = 0
for a in list(ELL.get_all_level_actors()):
    if a.get_actor_label() in ("DiagPatrol", "DiagFill"):
        ELL.destroy_actor(a)
        removed += 1

ELL.save_current_level()
print("CLEAR_DIAG_OK removed=%d" % removed)
