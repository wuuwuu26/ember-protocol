"""诊断 GeoCacheWater：当前槽位材质、法线朝向、高度起伏。
然后把槽位临时换成纯红不透明材质 M_Diag_Red，用来验证"我们的材质是否真的在渲染"。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
MAT_DIR = "/Game/RobotGame/Art/Materials"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)

gc = EAL.load_asset("/Game/RobotGame/Art/Fluids/flip_channel_full")
for a in ELL.get_all_level_actors():
    if a.get_actor_label() != "GeoCacheWater_Coolant":
        continue
    comp = a.get_component_by_class(unreal.GeometryCacheComponent)
    cur = comp.get_material(0)
    print("[diag] 当前槽位0材质: %s" % (cur.get_path_name() if cur else "None"))
    print("[diag] 组件 geometry_cache: %s" % comp.get_editor_property("geometry_cache"))
    o, e = a.get_actor_bounds(False)
    print("[diag] 世界包围盒 z 范围 %.2f .. %.2f (厚度 %.2f cm)"
          % (o.z - e.z, o.z + e.z, 2 * e.z))

    name = "M_Diag_Red"
    path = f"{MAT_DIR}/{name}"
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    m = TOOLS.create_asset(name, MAT_DIR, unreal.Material,
                           unreal.MaterialFactoryNew())
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    m.set_editor_property("two_sided", True)
    c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -300, 0)
    c.set_editor_property("constant", unreal.LinearColor(1.0, 0.0, 0.0, 1.0))
    MEL.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    comp.set_material(0, m)
    print("[diag] 已临时换成红色诊断材质")

ELL.save_current_level()
print("DIAG_GC_OK")
