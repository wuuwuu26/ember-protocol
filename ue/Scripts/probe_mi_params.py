# -*- coding: utf-8 -*-
"""打印各目录下材质实例的名字与关键参数（配色 / 金属度 / 粗糙度）。

用法: bash tools/ue_py.sh ue/Scripts/probe_mi_params.py "材质参数"
"""
import unreal

ROOTS = [
    "/Game/RobotGame/Art/Characters",
    "/Game/RobotGame/Art/Environment",
    "/Game/RobotGame/Art/Props",
]

def log(m):
    unreal.log("[材质参数] %s" % m)

ar = unreal.AssetRegistryHelpers.get_asset_registry()
for root in ROOTS:
    log("==== %s ====" % root)
    rows = []
    for ad in ar.get_assets_by_path(root, recursive=True):
        if str(ad.asset_class_path.asset_name) != "MaterialInstanceConstant":
            continue
        mic = ad.get_asset()
        if not mic:
            continue
        vals = {}
        for it in mic.get_editor_property("vector_parameter_values"):
            try:
                n = it.get_editor_property("parameter_info").get_editor_property("name")
                v = it.get_editor_property("parameter_value")
                vals[str(n)] = (round(v.r, 3), round(v.g, 3), round(v.b, 3))
            except Exception:
                pass
        scal = {}
        for it in mic.get_editor_property("scalar_parameter_values"):
            try:
                n = it.get_editor_property("parameter_info").get_editor_property("name")
                scal[str(n)] = round(it.get_editor_property("parameter_value"), 3)
            except Exception:
                pass
        rows.append((str(ad.asset_name), vals.get("DiffuseColor"),
                     vals.get("BaseTint"), scal.get("Metallic"), scal.get("Roughness")))
    rows.sort()
    for n, dc, bt, m, r in rows:
        log("  %-34s diffuse=%s base=%s M=%s R=%s" % (n, dc, bt, m, r))
