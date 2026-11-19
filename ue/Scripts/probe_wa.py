# -*- coding: utf-8 -*-
"""探测 WorldAlignedTexture / TextureObjectParameter 的引脚与属性名。"""
import unreal
L = "[世界对齐]"
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
P = "/Game/_Probe"
N = "M_ProbeWA"
if unreal.EditorAssetLibrary.does_asset_exist("%s/%s" % (P, N)):
    unreal.EditorAssetLibrary.delete_asset("%s/%s" % (P, N))
mat = AT.create_asset(N, P, unreal.Material, unreal.MaterialFactoryNew())
if not mat:
    unreal.log("%s ❌ 无法创建测试材质" % L)
else:
    wa = MEL.create_material_expression(
        mat, unreal.MaterialExpressionWorldAlignedTexture, 0, 0)
    unreal.log("%s WorldAlignedTexture 属性: %s"
               % (L, [x for x in dir(wa) if not x.startswith("_")
                      and "input" in x.lower() or "output" in x.lower()]))
    for pn in ("texture_size", "texture_scale", "world_space_normal_blend_contrast",
               "output_uv_in_world_space"):
        try:
            unreal.log("%s   %-40s = %s" % (L, pn, wa.get_editor_property(pn)))
        except Exception as e:
            unreal.log("%s   %-40s ❌" % (L, pn))
    top = MEL.create_material_expression(
        mat, unreal.MaterialExpressionTextureObjectParameter, -400, 0)
    unreal.log("%s TextureObjectParameter 类=%s" % (L, top.get_class().get_name()))
    # 试着连接，逐个候选引脚名
    for pin in ("TextureObject", "Texture Size", "TextureSize"):
        try:
            MEL.connect_material_expressions(top, "", wa, pin)
            unreal.log("%s   ✓ 可连到 %s" % (L, pin))
            break
        except Exception as e:
            unreal.log("%s   ✗ %s : %s" % (L, pin, str(e)[:60]))
    # 输出引脚候选
    for out in ("Texture", "RGB", "XYZ", "RGBA", ""):
        try:
            c = MEL.create_material_expression(
                mat, unreal.MaterialExpressionConstant, -200, 400)
            MEL.connect_material_expressions(wa, out, c, "")
            unreal.log("%s   ✓ 输出引脚 '%s' 可用" % (L, out))
        except Exception as e:
            unreal.log("%s   ✗ 输出 '%s': %s" % (L, out, str(e)[:60]))
