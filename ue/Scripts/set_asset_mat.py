"""把水材质写进 GeometryCache 资产的 materials 数组（持久化，不依赖运行时覆盖）。"""
import unreal

MAT_DIR = "/Game/RobotGame/Art/Materials"
EAL = unreal.EditorAssetLibrary
gc = EAL.load_asset("/Game/RobotGame/Art/Fluids/flip_channel_full")
water = EAL.load_asset(f"{MAT_DIR}/M_GeoCache_Water")

print("[am] 改前 materials=%s" % gc.get_editor_property("materials"))
gc.set_editor_property("materials", [water])
print("[am] 改后 materials=%s" % gc.get_editor_property("materials"))
EAL.save_loaded_asset(gc)
print("ASSET_MAT_SET_OK")
