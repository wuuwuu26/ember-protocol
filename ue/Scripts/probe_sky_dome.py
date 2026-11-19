# -*- coding: utf-8 -*-
"""天空穹顶二分开：检查材质连接，并临时替换成纯品红自发光材质。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
MAT_DIR = "/Game/RobotGame/Art/Materials"
TEST_PATH = MAT_DIR + "/M_SkyDomeTest"
unreal.EditorLevelLibrary.load_level(LEVEL)


def g(o, a, d=None):
    try:
        return o.get_editor_property(a)
    except Exception:
        return d


def log(m):
    unreal.log("[天空诊断] %s" % m)

mel = unreal.MaterialEditingLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()

# 1) 现有关卡里的天空相关 Actor
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    cn = a.get_class().get_name()
    lbl = a.get_actor_label()
    if cn in ("SkyAtmosphere", "SkyLight", "ExponentialHeightFog", "StaticMeshActor") and (
            "sky" in lbl.lower() or "dome" in lbl.lower() or cn in ("SkyAtmosphere", "SkyLight", "ExponentialHeightFog")):
        loc = a.get_actor_location()
        log("Actor %-22s %-24s @ (%.0f,%.0f,%.0f) hiddenGame=%s" % (
            lbl, cn, loc.x, loc.y, loc.z, g(a, "hidden_in_game")))
        if cn == "StaticMeshActor":
            c = a.static_mesh_component
            b = a.get_actor_bounds(False)
            log("  mesh=%s mats=%s visible=%s boundsOrigin=%s boundsExtent=%s" % (
                c.static_mesh.get_name() if c.static_mesh else "None",
                [m.get_name() if m else "None" for m in c.get_materials()],
                c.is_visible(), b[0], b[1]))

# 2) 现有天空材质连接检查
mat = unreal.EditorAssetLibrary.load_asset(MAT_DIR + "/M_SkyDome")
log("M_SkyDome 存在=%s" % (mat is not None))
if mat:
    for attr in ("shading_model", "two_sided", "used_with_sky", "blend_mode", "material_domain"):
        log("  %s = %s" % (attr, g(mat, attr)))
    try:
        node = mel.get_material_property_input_node(mat, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        log("  自发光输入节点 = %s" % (node.get_name() if node else "None"))
    except Exception as e:
        log("  读取自发光节点失败: %s" % str(e)[:100])

# 3) 纯色测试材质
if unreal.EditorAssetLibrary.does_asset_exist(TEST_PATH):
    unreal.EditorAssetLibrary.delete_asset(TEST_PATH)
tm = at.create_asset("M_SkyDomeTest", MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
if not tm:
    log("测试材质创建失败")
else:
    tm.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    tm.set_editor_property("two_sided", True)
    node = mel.create_material_expression(tm, unreal.MaterialExpressionConstant3Vector, 0, 0)
    node.set_editor_property("constant", unreal.LinearColor(0.8, 0.1, 0.8, 1.0))
    try:
        mel.connect_material_property(node, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        log("测试材质自发光已连接")
    except Exception as e:
        log("测试材质连接失败: %s" % str(e)[:100])
    mel.recompile_material(tm)
    unreal.EditorAssetLibrary.save_loaded_asset(tm)
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_actor_label() == "SkyDome":
            a.static_mesh_component.set_material(0, tm)
            log("SkyDome 已换成纯品红测试材质")

unreal.EditorLevelLibrary.save_current_level()
log("完成")