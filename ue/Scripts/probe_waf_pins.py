# -*- coding: utf-8 -*-
"""探明 WorldAlignedTexture 材质函数调用节点的**真实引脚名**。

为什么要探：MaterialExpressionMaterialFunctionCall 没有 function_inputs /
function_outputs 这两个 editor property（踩过，报
"Failed to find property 'function_inputs'"）。引脚名写死又很危险 ——
引擎版本之间会改，写错时 connect_material_expressions 只会抛异常，
拿到的就是一个"看着建好了、其实是空壳"的材质。

这里用"试着连"的办法把可用引脚名试出来，顺便看 MaterialEditingLibrary
有没有现成的枚举接口。

用法: bash tools/ue_py.sh ue/Scripts/probe_waf_pins.py "引脚探测"
"""
import unreal

WAF = ("/Engine/Functions/Engine_MaterialFunctions01/Texturing/"
       "/WorldAlignedTexture")
MAT_DIR = "/Game/RobotGame/Art/Materials"
TEST = MAT_DIR + "/_PinProbe"

unreal.log("[引脚探测] 脚本已开始执行")


def log(m):
    unreal.log("[引脚探测] %s" % m)


def main():
    # ── 1. MaterialEditingLibrary 里有没有现成的枚举接口 ──
    api = [n for n in dir(unreal.MaterialEditingLibrary)
           if not n.startswith("_")]
    log("MaterialEditingLibrary 共 %d 个接口" % len(api))
    for n in api:
        if "function" in n.lower() or "pin" in n.lower():
            log("    %s" % n)

    # ── 2. 也看看表达式类自己暴露了什么 ──
    props = [n for n in dir(unreal.MaterialExpressionMaterialFunctionCall)
             if not n.startswith("_")]
    log("MaterialExpressionMaterialFunctionCall 属性: %s" % props)

    # ── 3. 建测试材质，挂上 WAF，逐个试引脚名 ──
    at = unreal.AssetToolsHelpers.get_asset_tools()
    if unreal.EditorAssetLibrary.does_asset_exist(TEST):
        unreal.EditorAssetLibrary.delete_asset(TEST)
    mat = at.create_asset("_PinProbe", MAT_DIR, unreal.Material,
                          unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    fc = mel.create_material_expression(
        mat, unreal.MaterialExpressionMaterialFunctionCall, 0, 0)
    waf = unreal.EditorAssetLibrary.load_asset(WAF)
    log("WAF 资产 = %s" % (waf.get_name() if waf else "None"))
    try:
        ok = fc.set_material_function(waf)
        log("set_material_function -> %s" % ok)
    except Exception as e:
        log("set_material_function 抛异常: %s" % str(e)[:120])

    const = mel.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -400, 0)
    const.set_editor_property("r", 1.0)

    in_cands = ["TextureObject", "Texture", "Tex", "WorldPositionScale",
                "PositionScale", "Scale", "TextureSize", "Size",
                "WorldPosition", "WorldPositionOffset", "Normal",
                "Blend", "TextureSize1", "DefaultTextureSize"]
    for n in in_cands:
        try:
            mel.connect_material_expressions(const, "", fc, n)
            log("  ✅ 输入引脚存在: %s" % n)
        except Exception as e:
            log("  ❌ 输入引脚 %s: %s" % (n, str(e)[:70]))

    out_cands = ["XYZ", "XY", "XZ", "YZ", "X", "Y", "Z", "RGB", "R", "G",
                 "B", "Out", "Result", "Output"]
    for n in out_cands:
        try:
            mel.connect_material_property(fc, n, unreal.MaterialProperty.MP_BASE_COLOR)
            log("  ✅ 输出引脚存在: %s" % n)
        except Exception as e:
            log("  ❌ 输出引脚 %s: %s" % (n, str(e)[:70]))

    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    log("探测材质已保存")


main()
