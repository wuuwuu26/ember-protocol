"""彻底诊断 GC 材质覆盖：数 actor、读回设置前后、强制重注册。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
MAT_DIR = "/Game/RobotGame/Art/Materials"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)

# 数所有相关 actor
gc_actors = [a for a in ELL.get_all_level_actors()
             if "GeoCache" in a.get_actor_label() or "flip" in a.get_actor_label().lower()]
print("[gcm] 相关 actor 数=%d" % len(gc_actors))
for a in gc_actors:
    print("[gcm]   %s hidden=%s" % (a.get_actor_label(), a.is_hidden_ed()))

# 亮品红自发光测试材质
name = "M_Diag_Magenta"
path = f"{MAT_DIR}/{name}"
if EAL.does_asset_exist(path):
    EAL.delete_asset(path)
m = TOOLS.create_asset(name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
m.set_editor_property("two_sided", True)
m.set_editor_property("used_with_geometry_cache", True)
c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -300, 0)
c.set_editor_property("constant", unreal.LinearColor(1.0, 0.0, 1.0, 1.0))
MEL.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.recompile_material(m)
EAL.save_loaded_asset(m)

for a in gc_actors:
    if a.get_actor_label() != "GeoCacheWater_Coolant":
        continue
    a.set_actor_hidden_in_game(False)
    comp = a.get_component_by_class(unreal.GeometryCacheComponent)
    before = comp.get_material(0)
    print("[gcm] 设置前 slot0=%s" % (before.get_name() if before else "None"))
    comp.set_material(0, m)
    after = comp.get_material(0)
    print("[gcm] 设置后 slot0=%s" % (after.get_name() if after else "None"))
    print("[gcm] 材质槽数=%d" % comp.get_num_materials())
    try:
        comp.reregister_component()
        print("[gcm] 已 reregister")
    except Exception as e:
        print("[gcm] reregister 失败: %s" % e)

ELL.save_current_level()
print("GCM_DIAG_OK")
