# -*- coding: utf-8 -*-
"""检查玩家机体网格与材质"""
import unreal

CHASSIS = [
    "SK_Chassis_Medium",
    "SK_Chassis_Light",
    "SK_Chassis_Heavy"
]

out = []
for name in CHASSIS:
    path = f"/Game/RobotGame/Art/Characters/{name}"
    sk = unreal.EditorAssetLibrary.load_asset(path)
    if not sk:
        # 搜一下真实路径
        for p in unreal.EditorAssetLibrary.list_assets("/Game/RobotGame", recursive=True):
            if p.split("/")[-1].startswith(name):
                path = p
                sk = unreal.EditorAssetLibrary.load_asset(p)
                break
    if not sk:
        out.append(f"{name}: NOT FOUND")
        continue
    mats = sk.get_editor_property("materials")
    out.append(f"=== {name} path={path} (slots={len(mats)}) ===")
    for idx, sm in enumerate(mats):
        slot_name = sm.get_editor_property("material_slot_name")
        mi = sm.get_editor_property("material_interface")
        mi_name = mi.get_path_name() if mi else "None"
        out.append(f"  [{idx}] slot={slot_name} mat={mi_name}")
        if mi and isinstance(mi, unreal.MaterialInstance):
            diff = "None"
            for vp in mi.get_editor_property("vector_parameter_values"):
                pname = vp.get_editor_property("parameter_info").name
                if pname in ("DiffuseColor", "BaseTint"):
                    diff += f" {pname}={vp.get_editor_property('parameter_value')}"
            out.append(f"       {diff}")

with open(r"C:\Users\25227\Documents\robot_game\docs\player_mats_probe.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
    f.write("\nPLAYER_MATS_DONE\n")
