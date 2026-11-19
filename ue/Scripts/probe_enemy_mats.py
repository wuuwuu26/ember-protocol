# -*- coding: utf-8 -*-
"""检查 5 种敌人的骨骼网格材质槽与材质实例参数"""
import unreal

ENEMIES = [
    "SK_Enemy_Guard",
    "SK_Enemy_Patrol",
    "SK_Enemy_Hauler",
    "SK_Enemy_Gardener",
    "SK_Enemy_Colossus"
]

out = []
for name in ENEMIES:
    path = f"/Game/RobotGame/Art/Characters/{name}"
    sk = unreal.EditorAssetLibrary.load_asset(path)
    if not sk:
        out.append(f"{name}: NOT FOUND")
        continue
    mats = sk.get_editor_property("materials")
    out.append(f"=== {name} (slots={len(mats)}) ===")
    for idx, sm in enumerate(mats):
        slot_name = sm.get_editor_property("material_slot_name")
        mi = sm.get_editor_property("material_interface")
        mi_name = mi.get_path_name() if mi else "None"
        out.append(f"  [{idx}] slot={slot_name} mat={mi_name}")
        if mi and isinstance(mi, unreal.MaterialInstance):
            diff = "None"
            emiss = "None"
            for vp in mi.get_editor_property("vector_parameter_values"):
                pname = vp.get_editor_property("parameter_info").name
                if pname == "DiffuseColor":
                    diff = str(vp.get_editor_property("parameter_value"))
                elif pname == "EmissiveColor":
                    emiss = str(vp.get_editor_property("parameter_value"))
            out.append(f"       diffuse={diff} emissive={emiss}")

with open(r"C:\Users\25227\Documents\robot_game\docs\enemy_mats_probe.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
    f.write("\nENEMY_MATS_DONE\n")
