# -*- coding: utf-8 -*-
import unreal
L = "[贴图检查]"
for p in ("/Game/RobotGame/Art/Materials/T_MechDetail",
          "/Game/RobotGame/Art/Materials/T_MechDetail_N"):
    t = unreal.EditorAssetLibrary.load_asset(p)
    if not t:
        unreal.log("%s 找不到 %s" % (L, p)); continue
    try:
        unreal.log("%s %s 尺寸=%s sRGB=%s 压缩=%s" % (
            L, p, t.blueprint_get_size_x() if hasattr(t,'blueprint_get_size_x') else '?',
            t.get_editor_property("srgb"), t.get_editor_property("compression_settings")))
    except Exception as e:
        unreal.log("%s %s 读属性失败 %s" % (L, p, str(e)[:80]))
mi = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Characters/M_Steel")
if mi:
    for it in mi.get_editor_property("texture_parameter_values"):
        try:
            n = it.get_editor_property("parameter_info").get_editor_property("name")
            v = it.get_editor_property("parameter_value")
            unreal.log("%s MI参数 %s = %s" % (L, n, v.get_name() if v else "空"))
        except Exception as e:
            unreal.log("%s 读贴图参数失败 %s" % (L, str(e)[:60]))
    for it in mi.get_editor_property("scalar_parameter_values"):
        try:
            n = it.get_editor_property("parameter_info").get_editor_property("name")
            if n in ("TextureSize", "DetailAmount", "SeamDarken", "WearAmount"):
                unreal.log("%s MI标量 %s = %.3f" % (L, n, it.get_editor_property("parameter_value")))
        except Exception:
            pass
