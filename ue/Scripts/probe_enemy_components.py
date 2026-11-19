"""列出关卡里 BP_Enemy actor 的所有组件，找多出来的腿/占位网格。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)

for a in ELL.get_all_level_actors():
    if a.get_actor_label() != "BP_Enemy":
        continue
    print("[pc] actor %s class=%s" % (a.get_actor_label(), a.get_class().get_name()))
    for c in a.get_components():
        mesh = ""
        for attr in ("static_mesh", "skeletal_mesh"):
            try:
                v = c.get_editor_property(attr)
                if v:
                    mesh = v.get_path_name()
            except Exception:
                pass
        print("[pc]   %-34s %-28s %s" % (c.get_name(), c.get_class().get_name(), mesh))
print("ENEMY_COMP_OK")
