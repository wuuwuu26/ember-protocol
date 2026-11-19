# -*- coding: utf-8 -*-
"""诊断玩家机体网格：LOD 数量、材质槽混合模式。"""
import unreal

L = "ChassisDiag"
OUT = r"C:\Users\25227\Documents\robot_game\docs\chassis_lod_diag.txt"
lines = []


def log(s):
    unreal.log(f"[{L}] {s}")
    lines.append(s)


sk = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Characters/SK_Chassis_Light")
if sk:
    names = [n for n in dir(sk) if "lod" in n.lower() or "bounds" in n.lower()]
    log("apis: " + ", ".join(names))
    try:
        info = sk.get_editor_property("lod_info")
        log(f"lod_info count = {len(info)}")
        for i, li in enumerate(info):
            log(f"  LOD{i}: screen_size={li.get_editor_property('screen_size')}")
    except Exception as e:
        log("lod_info err: " + str(e))
    try:
        skel = sk.get_editor_property("skeleton")
        log(f"skeleton={skel.get_name() if skel else None}")
    except Exception as e:
        log("skeleton err: " + str(e))
    mats = sk.get_editor_property("materials")
    for idx, m in enumerate(mats):
        mi = m.get_editor_property("material_interface")
        if mi:
            blend = mi.get_editor_property("blend_mode")
            two = mi.get_editor_property("two_sided")
            log(f"  slot{idx} {m.get_editor_property('material_slot_name')} -> {mi.get_name()} blend={blend} two_sided={two}")
        else:
            log(f"  slot{idx} {m.get_editor_property('material_slot_name')} -> None")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\nDIAG_DONE\n")
