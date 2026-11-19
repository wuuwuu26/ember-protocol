# -*- coding: utf-8 -*-
"""用官方接口把材质函数的真实引脚名枚举出来。

【为什么必须用接口而不是"试着连"】上一步已经证明：
    connect_material_expressions 对**不存在的引脚名不会报错**，
    它会静默成功、但什么都不连。所以"试着连一遍看哪个成功"完全无效 ——
    最后会得到一个空壳材质，还以为是好的。这是最难查的一类坑。

正确做法：
    · 输入引脚 → MaterialEditingLibrary.get_inputs_for_material_function_expression()
    · 输出引脚 → 遍历材质函数内部的 MaterialExpressionFunctionOutput 节点，
                读它的 output_name

用法: bash tools/ue_py.sh ue/Scripts/probe_fn_pins.py "函数引脚"
"""
import unreal

FUNCS = [
    ("/Engine/Functions/Engine_MaterialFunctions01/Texturing/"
     "/WorldAlignedTexture", "WorldAlignedTexture"),
    ("/Engine/Functions/Engine_MaterialFunctions01/Texturing/"
     "/WorldAlignedNormal", "WorldAlignedNormal"),
]

MAT_DIR = "/Game/RobotGame/Art/Materials"
TEST = MAT_DIR + "/_FnPinProbe"

unreal.log("[函数引脚] 脚本已开始执行")


def log(m):
    unreal.log("[函数引脚] %s" % m)


def main():
    at = unreal.AssetToolsHelpers.get_asset_tools()
    mel = unreal.MaterialEditingLibrary
    if unreal.EditorAssetLibrary.does_asset_exist(TEST):
        unreal.EditorAssetLibrary.delete_asset(TEST)
    mat = at.create_asset("_FnPinProbe", MAT_DIR, unreal.Material,
                          unreal.MaterialFactoryNew())

    for path, tag in FUNCS:
        log("=" * 50)
        fn = unreal.EditorAssetLibrary.load_asset(path)
        if not fn:
            log("❌ 找不到 %s" % path)
            continue
        log("%s (%s)" % (tag, fn.get_class().get_name()))

        # ── 输出引脚：遍历函数内部的 FunctionOutput 节点 ──
        try:
            inner = mel.get_material_function_expressions(fn)
            log("  内部表达式 %d 个" % len(inner))
            outs = []
            for e in inner:
                cn = e.get_class().get_name()
                if "FunctionOutput" in cn:
                    try:
                        on = e.get_editor_property("output_name")
                    except Exception:
                        on = "?"
                    outs.append(str(on))
            log("  ✅ 输出引脚: %s" % outs)
        except Exception as e:
            log("  读内部表达式失败: %s" % str(e)[:100])

        # ── 输入引脚：官方接口 ──
        fc = mel.create_material_expression(
            mat, unreal.MaterialExpressionMaterialFunctionCall, 0, 0)
        try:
            fc.set_material_function(fn)
        except Exception as e:
            log("  set_material_function 失败: %s" % str(e)[:80])
            continue
        # ── 输入引脚：同样遍历函数内部的 FunctionInput 节点 ──
        # （和输出引脚对称，不依赖 API 签名，最稳）
        try:
            inner = mel.get_material_function_expressions(fn)
            ins2 = []
            for e in inner:
                cn = e.get_class().get_name()
                if "FunctionInput" in cn:
                    try:
                        on = e.get_editor_property("input_name")
                    except Exception:
                        on = "?"
                    ins2.append(str(on))
            log("  ✅ 输入引脚(遍历内部): %s" % ins2)
        except Exception as e:
            log("  遍历内部失败: %s" % str(e)[:100])

        try:
            ins = mel.get_inputs_for_material_function_expression(fn, fc)
            log("  get_inputs... 返回 %s，共 %d 项"
                % (type(ins).__name__, len(ins)))
            for it in ins:
                try:
                    nm = it.get_editor_property("input_name")
                except Exception:
                    nm = str(it)
                log("      ✅ 输入引脚: %s" % nm)
        except Exception as e:
            log("  get_inputs 失败: %s" % str(e)[:120])

    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    log("完成")


main()
