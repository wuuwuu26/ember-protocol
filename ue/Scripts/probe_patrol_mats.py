"""列出 SK_Enemy_Patrol 的材质槽及其材质名，判断哪些部件可能因深色材质在夜间消失。"""
import unreal

EAL = unreal.EditorAssetLibrary
m = EAL.load_asset("/Game/RobotGame/Art/Characters/SK_Enemy_Patrol")
mats = m.get_editor_property("materials")
for i, sm in enumerate(mats):
    mi = sm.get_editor_property("material_interface")
    slot = sm.get_editor_property("material_slot_name")
    print("[pmat] slot%d %-22s -> %s" % (i, slot, mi.get_path_name() if mi else "None"))
print("PATROL_MATS_OK")
