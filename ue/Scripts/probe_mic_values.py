# -*- coding: utf-8 -*-
"""把材质实例上真正生效的参数值读出来（含继承自父类的默认值）。

为什么要读：这批材质全是 FBX 导入器生成的 MaterialInstanceConstant，
父类是 FBXLegacyPhongSurfaceMaterial。颜色不在"参数覆盖"里就藏在
父类默认值里，两条路都要走一遍才能拿到真正的 BaseColor。

用法: bash tools/ue_py.sh ue/Scripts/probe_mic_values.py "MIC 参数"
"""
import unreal

PATHS = [
    "/Game/RobotGame/Art/Characters/M_Steel",
    "/Game/RobotGame/Art/Characters/M_SteelLight",
    "/Game/RobotGame/Art/Characters/M_Joint",
    "/Game/RobotGame/Art/Characters/M_Copper",
    "/Game/RobotGame/Art/Props/M_Rust",
    "/Game/RobotGame/Art/Characters/M_Accent_light",
    "/Game/RobotGame/Art/Characters/M_Accent_medium",
    "/Game/RobotGame/Art/Characters/M_Accent_heavy",
    "/Game/RobotGame/Art/Props/M_Accent_prop",
    "/Game/RobotGame/Art/Environment/M_Accent_landmark",
    "/Game/RobotGame/Art/Modules/M_Accent_module",
    "/Game/RobotGame/Art/Characters/M_Core_medium",
    "/Game/RobotGame/Art/Characters/M_Visor_medium",
]

unreal.log("[MIC 参数] 脚本已开始执行")


def log(m):
    unreal.log("[MIC 参数] %s" % m)


def show_array(obj, prop):
    try:
        arr = obj.get_editor_property(prop)
    except Exception as e:
        log("    %s 读不到: %s" % (prop, str(e)[:60]))
        return
    log("    %s: %d 项" % (prop, len(arr)))
    for it in arr:
        try:
            info = it.get_editor_property("parameter_info")
            name = info.get_editor_property("name")
        except Exception:
            name = "?"
        try:
            val = it.get_editor_property("parameter_value")
        except Exception:
            val = "?"
        if isinstance(val, unreal.LinearColor):
            val = "(%.4f, %.4f, %.4f, %.4f)" % (val.r, val.g, val.b, val.a)
        log("        %s = %s" % (name, val))


def main():
    for p in PATHS:
        m = unreal.EditorAssetLibrary.load_asset(p)
        log("=== %s" % p)
        if not m:
            log("    加载失败")
            continue
        try:
            parent = m.get_editor_property("parent")
            log("    父类 = %s" % (parent.get_name() if parent else "-"))
        except Exception:
            pass
        for prop in ("scalar_parameter_values", "vector_parameter_values",
                     "texture_parameter_values"):
            show_array(m, prop)


main()
