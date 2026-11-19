# -*- coding: utf-8 -*-
"""检查 M_SkyDome 的实际节点、编译状态与双面设置。"""
import unreal

MAT_PATH = "/Game/RobotGame/Art/Materials/M_SkyDome"
mat = unreal.EditorAssetLibrary.load_asset(MAT_PATH)
mel = unreal.MaterialEditingLibrary
log = lambda m: unreal.log("[材质状态] %s" % m)
log("expressions=%d" % mel.get_num_material_expressions(mat))
for e in mel.get_material_expressions(mat):
    log("  expr=%s class=%s" % (e.get_name(), e.get_class().get_name()))
    for attr in ("constant", "r", "g", "b", "a"):
        try:
            log("    %s=%s" % (attr, e.get_editor_property(attr)))
        except Exception:
            pass
for attr in ("is_sky", "two_sided", "blend_mode", "shading_model", "material_domain", "used_with_static_mesh"):
    try:
        log("%s=%s" % (attr, mat.get_editor_property(attr)))
    except Exception as e:
        log("%s 读取失败" % attr)
try:
    root = mel.get_material_property_input_node(mat, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    log("emissive_root=%s" % (root.get_name() if root else "None"))
except Exception as e:
    log("emissive_root 读取失败 %s" % e)
for p in [p for p in dir(mat) if "compile" in p.lower() or "error" in p.lower() or "status" in p.lower()]:
    try:
        log("%s=%s" % (p, mat.get_editor_property(p)))
    except Exception:
        pass
log("完成")