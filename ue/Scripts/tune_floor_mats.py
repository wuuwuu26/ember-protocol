# -*- coding: utf-8 -*-
"""调暗地板反照率（M_SteelLight 与 M_Steel），让地面真正呈现工业夜景的明暗落差与光池节奏。"""
import unreal

mel = unreal.MaterialEditingLibrary

UPDATES = [
    (
        "/Game/RobotGame/Art/Environment/M_SteelLight",
        {
            "Roughness": 0.46,
            "Shininess": 24.0,
            "Metallic": 0.12,
        },
        {
            "DiffuseColor": (0.065, 0.072, 0.082, 1.0),
            "BaseTint": (0.075, 0.080, 0.090, 1.0),
            "WearTint": (0.130, 0.138, 0.150, 1.0),
            "SpecularColor": (0.020, 0.022, 0.025, 1.0),
        }
    ),
    (
        "/Game/RobotGame/Art/Environment/M_Steel",
        {
            "Roughness": 0.58,
            "Shininess": 20.0,
        },
        {
            "DiffuseColor": (0.040, 0.045, 0.052, 1.0),
            "BaseTint": (0.048, 0.052, 0.060, 1.0),
            "WearTint": (0.085, 0.092, 0.105, 1.0),
            "SpecularColor": (0.012, 0.014, 0.016, 1.0),
        }
    ),
]

out = []
for path, scalars, vectors in UPDATES:
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        out.append("%s 不存在" % path)
        continue
    mi = unreal.EditorAssetLibrary.load_asset(path)
    out.append("调优 %s" % path)
    for k, v in scalars.items():
        mel.set_material_instance_scalar_parameter_value(mi, k, float(v))
        out.append("  scalar %s = %s" % (k, v))
    for k, v in vectors.items():
        mel.set_material_instance_vector_parameter_value(
            mi, k, unreal.LinearColor(v[0], v[1], v[2], v[3]))
        out.append("  vector %s = %s" % (k, v))
    mel.update_material_instance(mi)
    unreal.EditorAssetLibrary.save_asset(path)

with open(r"C:\Users\25227\Documents\robot_game\docs\floor_tune_result.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
    f.write("\nFLOOR_TUNE_DONE\n")
