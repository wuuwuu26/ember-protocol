# -*- coding: utf-8 -*-
import unreal
L = "[碰撞检查]"
unreal.log(L + " 开始")
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for nm in ("SM_Env_Wall", "SM_Env_Floor", "SM_Env_Pillar", "SM_Env_Catwalk"):
    sm = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Environment/%s" % nm)
    if not sm:
        unreal.log("%s 找不到 %s" % (L, nm))
        continue
    bs = sm.get_editor_property("body_setup")
    info = []
    if bs:
        try:
            info.append("agg=%s" % bs.get_editor_property("collision_trace_flag"))
        except Exception as e:
            info.append("agg?")
        try:
            info.append("type=%s" % bs.get_editor_property("collision_type"))
        except Exception:
            pass
    try:
        info.append("complex_as_simple=%s" % sm.get_editor_property("complex_collision_as_simple"))
    except Exception:
        pass
    try:
        info.append("has_simple=%s" % sm.get_editor_property("has_simple_collision"))
    except Exception:
        pass
    try:
        bnd = sm.get_bounds_box()
        info.append("bounds=%s" % bnd)
    except Exception:
        pass
    unreal.log("%s %-16s %s" % (L, nm, "  ".join(info)))
