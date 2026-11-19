# -*- coding: utf-8 -*-
"""列出核心/面罩材质的关键参数颜色，用于给弹丸分阵营配色。"""
import unreal

PATHS = [
    "/Game/RobotGame/Art/Characters/M_Core_medium",
    "/Game/RobotGame/Art/Characters/M_Core_light",
    "/Game/RobotGame/Art/Characters/M_Visor_medium",
    "/Game/RobotGame/Art/Characters/M_Core_enemy_guard",
    "/Game/RobotGame/Art/Characters/M_Accent_medium",
]

out = []
for p in PATHS:
    mi = unreal.EditorAssetLibrary.load_asset(p)
    if not mi:
        out.append("%s  MISSING" % p)
        continue
    base = mi.get_editor_property("parent") if isinstance(
        mi, unreal.MaterialInstanceConstant) else mi
    props = {}
    for key in ("base_color", "emissive_color", "color", "emissive"):
        try:
            props[key] = str(mi.get_editor_property(key))
        except Exception:
            pass
    try:
        sv = mi.get_editor_property("vector_parameter_values")
        for v in sv:
            props[str(v.get_editor_property("parameter_info"))] = str(
                v.get_editor_property("parameter_value"))
    except Exception as e:
        props["vec_err"] = str(e)[:50]
    out.append("%s\n   class=%s parent=%s\n   %s" % (
        p, mi.get_class().get_name(),
        base.get_name() if base else "-", props))

with open(r"C:\Users\25227\Documents\robot_game\docs\proj_mats.txt", "w") as f:
    f.write("\n".join(out))
    f.write("\nPROJMATS_DONE\n")
