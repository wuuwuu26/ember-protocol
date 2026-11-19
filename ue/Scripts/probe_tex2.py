# -*- coding: utf-8 -*-
import unreal
L = "[贴图细节]"
t = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/T_MechDetail")
if t:
    for attr in ("imported_size", "source_file", "never_stream", "lod_group",
                 "max_texture_size", "srgb", "compression_settings",
                 "lod_bias", "virtual_texture_streaming"):
        try:
            unreal.log("%s %s = %s" % (L, attr, t.get_editor_property(attr)))
        except Exception as e:
            unreal.log("%s %s 读取失败" % (L, attr))
    try:
        unreal.log("%s 实际尺寸 %dx%d" % (L, t.blueprint_get_size_x(), t.blueprint_get_size_y()))
    except Exception:
        pass
    try:
        unreal.log("%s 资源尺寸 %dx%d" % (L, t.get_surface_width(), t.get_surface_height()))
    except Exception as e:
        unreal.log("%s get_surface 不可用" % L)
