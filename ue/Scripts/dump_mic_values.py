# -*- coding: utf-8 -*-
"""列出 M_RobotSurface 的所有材质实例及其关键参数值。

重点确认 DetailTex / NormalTex 是否真的被设上了 —— 如果它们是 None，
WorldAlignedTexture 会采样默认白图，缝遮罩恒为 1，整个表面就是一块平板。
这正是"表面纹理看不出来"的典型原因。
"""
import unreal

LOG = "[MIC 值]"


def log(s):
    unreal.log("%s %s" % (LOG, s))


ar = unreal.AssetRegistryHelpers.get_asset_registry()
rows = []
for root in ("/Game/RobotGame/Art",):
    for ad in ar.get_assets_by_path(root, recursive=True):
        if str(ad.asset_class_path.asset_name) != "MaterialInstanceConstant":
            continue
        m = ad.get_asset()
        if not m:
            continue
        par = m.get_editor_property("parent")
        pname = par.get_name() if par else "?"
        if pname != "M_RobotSurface":
            continue
        vals = {}
        for p in m.get_editor_property("scalar_parameter_values"):
            vals[str(p.get_editor_property("parameter_info").get_editor_property("name"))] = \
                round(float(p.get_editor_property("parameter_value")), 3)
        texs = {}
        for p in m.get_editor_property("texture_parameter_values"):
            nm = str(p.get_editor_property("parameter_info").get_editor_property("name"))
            t = p.get_editor_property("parameter_value")
            texs[nm] = t.get_name() if t else "None"
        cols = {}
        for p in m.get_editor_property("vector_parameter_values"):
            nm = str(p.get_editor_property("parameter_info").get_editor_property("name"))
            c = p.get_editor_property("parameter_value")
            cols[nm] = (round(c.r, 3), round(c.g, 3), round(c.b, 3))
        rows.append((str(ad.asset_name), pname, vals, texs, cols))

log("共 %d 个 MIC" % len(rows))
for nm, pname, vals, texs, cols in sorted(rows, key=lambda r: r[0]):
    log("── %s" % nm)
    log("    贴图: %s" % texs)
    log("    颜色: %s" % cols)
    log("    标量: %s" % vals)
