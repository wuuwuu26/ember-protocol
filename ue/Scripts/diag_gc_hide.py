"""定位白板来源：隐藏 GeoCacheWater_Coolant，看渠内白板是否消失。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)

for a in ELL.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl == "GeoCacheWater_Coolant":
        a.set_actor_hidden_in_game(True)
        comp = a.get_component_by_class(unreal.GeometryCacheComponent)
        mats = comp.get_materials()
        print("[hide] GC 组件材质数=%d" % len(mats))
        for i, m in enumerate(mats):
            print("[hide]   slot%d = %s" % (i, m.get_path_name() if m else "None"))
        print("[hide] 已隐藏 GeoCacheWater_Coolant")

ELL.save_current_level()
print("HIDE_GC_OK")
