"""定位 GeoCacheWater 网格的世界包围盒，判断它到底落在哪。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
EAL = unreal.EditorAssetLibrary
ELL.load_level(LEVEL)

for a in ELL.get_all_level_actors():
    if a.get_actor_label() != "GeoCacheWater_Coolant":
        continue
    origin, ext = a.get_actor_bounds(False)
    print("[gcb] actor_bounds origin=%s extent=%s" % (origin, ext))
    print("[gcb]   -> min=(%.0f,%.0f,%.0f) max=(%.0f,%.0f,%.0f)"
          % (origin.x - ext.x, origin.y - ext.y, origin.z - ext.z,
             origin.x + ext.x, origin.y + ext.y, origin.z + ext.z))
    comp = a.get_component_by_class(unreal.GeometryCacheComponent)
    try:
        lo, hi = comp.get_local_bounds()
        print("[gcb] comp local_bounds min=%s max=%s" % (lo, hi))
    except Exception as e:
        print("[gcb] local_bounds 失败: %s" % e)

gc = EAL.load_asset("/Game/RobotGame/Art/Fluids/flip_channel_full")
try:
    print("[gcb] asset bounds_origin=%s bounds_extent=%s"
          % (gc.bounds_origin, gc.bounds_extent))
except Exception as e:
    print("[gcb] asset bounds 失败: %s" % e)
print("GC_BOUNDS_OK")
