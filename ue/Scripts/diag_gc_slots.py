"""验证推断：GC 区段材质索引回退到默认白。把前 4 个槽都设成红色诊断材质并显示 actor。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
EAL = unreal.EditorAssetLibrary
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)

red = EAL.load_asset("/Game/RobotGame/Art/Materials/M_Diag_Red")
for a in ELL.get_all_level_actors():
    if a.get_actor_label() != "GeoCacheWater_Coolant":
        continue
    a.set_actor_hidden_in_game(False)
    comp = a.get_component_by_class(unreal.GeometryCacheComponent)
    for i in range(4):
        comp.set_material(i, red)
    print("[slots] 槽 0..3 已设红色，当前数量=%d" % comp.get_num_materials())

ELL.save_current_level()
print("SLOTS_OK")
