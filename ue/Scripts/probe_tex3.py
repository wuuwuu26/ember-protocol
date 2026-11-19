# -*- coding: utf-8 -*-
import unreal
L = "[贴图状态]"
MEL = unreal.MaterialEditingLibrary
for n in ("T_MechDetail", "T_MechDetail_N", "T_EnvDetail", "T_EnvDetail_N"):
    p = "/Game/RobotGame/Art/Materials/%s" % n
    t = unreal.EditorAssetLibrary.load_asset(p)
    if not t:
        unreal.log("%s ❌ 不存在 %s" % (L, n)); continue
    try:
        w, h = t.blueprint_get_size_x(), t.blueprint_get_size_y()
    except Exception:
        w = h = -1
    try:
        srgb = t.get_editor_property("srgb")
    except Exception:
        srgb = "?"
    try:
        comp = t.get_editor_property("compression_settings")
    except Exception:
        comp = "?"
    try:
        mx = t.get_editor_property("max_texture_size")
    except Exception:
        mx = "?"
    unreal.log("%s %-16s %dx%d  sRGB=%s  压缩=%s  最大尺寸=%s"
               % (L, n, w, h, srgb, comp, mx))

# 母材质里的贴图参数节点是否真的绑了纹理
m = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/M_RobotSurface")
if m:
    for e in MEL.get_material_expressions(m):
        cn = e.get_class().get_name()
        if "TextureSample" not in cn:
            continue
        pn = ""
        try:
            pn = str(e.get_editor_property("parameter_name"))
        except Exception:
            pass
        tex = None
        try:
            tex = e.get_editor_property("texture")
        except Exception:
            pass
        unreal.log("%s 采样节点 %-22s 参数=%-12s 纹理=%s"
                   % (L, cn, pn, tex.get_name() if tex else "❌ 空"))
