# -*- coding: utf-8 -*-
"""为 SK_Pilot_Maya 绑定高品质材质"""
import unreal

CHAR_DIR = "/Game/RobotGame/Art/Characters"
sk = unreal.EditorAssetLibrary.load_asset(f"{CHAR_DIR}/SK_Pilot_Maya")

MAT_MAPPINGS = {
    "M_SteelLight": f"{CHAR_DIR}/M_SteelLight",
    "M_Steel": f"{CHAR_DIR}/M_Steel",
    "M_Joint": f"{CHAR_DIR}/M_Joint",
    "M_Core": f"{CHAR_DIR}/M_Core_medium",
    "M_Visor": f"{CHAR_DIR}/M_Visor_medium",
    "M_Accent": f"{CHAR_DIR}/M_Accent_medium",
}

mats = sk.get_editor_property("materials")
for idx, sm in enumerate(mats):
    slot_name = str(sm.get_editor_property("material_slot_name"))
    target_mat_path = f"{CHAR_DIR}/M_SteelLight"
    for k, v in MAT_MAPPINGS.items():
        if k in slot_name:
            target_mat_path = v
            break
    mi = unreal.EditorAssetLibrary.load_asset(target_mat_path)
    if mi:
        sm.set_editor_property("material_interface", mi)
        unreal.log(f"Slot {idx} ({slot_name}) -> {target_mat_path}")

sk.set_editor_property("materials", mats)
unreal.EditorAssetLibrary.save_loaded_asset(sk)
unreal.log("SK_Pilot_Maya 材质成功关联并保存！")

with open(r"C:\Users\25227\Documents\robot_game\docs\maya_mats_assigned.txt", "w", encoding="utf-8") as f:
    f.write("MAYA_MATS_ASSIGNED_DONE\n")
