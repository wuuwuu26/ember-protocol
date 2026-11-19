# -*- coding: utf-8 -*-
"""查 M_Toxic_Fluid / M_Coolant_Fluid 各 MP_* 属性连接的表达式链，
定位金色反射/自发光的来源（Fresnel / ReflectionVector / 暖色常量）。"""
import unreal

MAT_DIR = "/Game/RobotGame/Art/Materials"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
lines = []


def log(s):
    unreal.log("[MatLinks] %s" % s)
    lines.append(str(s))


def find_input(expr, prop):
    """取表达式某输入引脚连的上游表达式类名。"""
    try:
        ins = MEL.get_material_property_input_node  # noqa
    except Exception:
        pass
    # 用 get_inputs 反射（可能不可用）
    try:
        for pin in ("A", "B", "Alpha", "Base", "Exponent", "Coordinate", "UVs"):
            try:
                up = MEL.get_material_property_input_node  # placeholder
            except Exception:
                pass
    except Exception:
        pass


for name in ("M_Toxic_Fluid", "M_Coolant_Fluid"):
    m = EAL.load_asset("%s/%s" % (MAT_DIR, name))
    log("===== %s =====" % name)
    log("  roughness/specular/metallic 连接：")
    for prop_name, prop in (("BaseColor", unreal.MaterialProperty.MP_BASE_COLOR),
                            ("Emissive", unreal.MaterialProperty.MP_EMISSIVE_COLOR),
                            ("Opacity", unreal.MaterialProperty.MP_OPACITY),
                            ("Roughness", unreal.MaterialProperty.MP_ROUGHNESS),
                            ("Specular", unreal.MaterialProperty.MP_SPECULAR),
                            ("Normal", unreal.MaterialProperty.MP_NORMAL),
                            ("Metallic", unreal.MaterialProperty.MP_METALLIC)):
        try:
            node = MEL.get_material_property_input_node(m, prop)
            log("    %-10s <- %s" % (prop_name,
                node.get_class().get_name() if node else "None(常量/默认)"))
        except Exception as e:
            log("    %-10s err %s" % (prop_name, str(e)[:50]))
    # 材质级属性
    for p in ("roughness", "metallic", "specular"):
        try:
            log("  material.%s default -> (见节点)" % p)
        except Exception:
            pass

with open(r"C:\Users\25227\Documents\robot_game\docs\mat_links.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("MAT_LINKS_DONE")
