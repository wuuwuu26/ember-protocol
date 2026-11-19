"""隐藏旧的冷却液高度场水，只留 GeometryCache 模拟水面，便于单独验收。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)

for a in ELL.get_all_level_actors():
    if a.get_actor_label() == "CoolantSpill_0":
        a.set_actor_hidden_in_game(True)
        try:
            a.set_editor_property("b_hidden_ed", True)
        except Exception:
            pass
        unreal.log("[gc] 隐藏旧冷却液水场 CoolantSpill_0")

ELL.save_current_level()
print("HIDE_OLD_WATER_OK")
