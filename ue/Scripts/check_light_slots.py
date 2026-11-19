# -*- coding: utf-8 -*-
import unreal

sk = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Characters/SK_Chassis_Light")
mats = sk.get_editor_property("materials")
for i, m in enumerate(mats):
    mi = m.get_editor_property("material_interface")
    sname = m.get_editor_property("material_slot_name")
    unreal.log(f"SK_Chassis_Light Slot {i}: {sname} -> {mi.get_name() if mi else 'None'}")

# 检查动画网格 PoseableMesh 的材质槽同步逻辑
with open(r"C:\Users\25227\Documents\robot_game\docs\light_slots.txt", "w") as f:
    f.write(f"Total slots: {len(mats)}\n")
    for i, m in enumerate(mats):
        mi = m.get_editor_property("material_interface")
        sname = m.get_editor_property("material_slot_name")
        f.write(f"Slot {i}: {sname} -> {mi.get_path_name() if mi else 'None'}\n")
    f.write("SLOTS_DONE\n")
