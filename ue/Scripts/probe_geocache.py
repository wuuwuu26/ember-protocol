"""诊断 GeoCacheWater_Coolant：位置、包围盒、组件状态。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)

for a in ELL.get_all_level_actors():
    if a.get_actor_label() != "GeoCacheWater_Coolant":
        continue
    loc = a.get_actor_location()
    sc = a.get_actor_scale3d()
    print("[gc] loc=%s scale=%s" % (loc, sc))
    print("[gc] hidden_in_game=%s" % a.is_hidden_ed())
    comp = a.get_component_by_class(unreal.GeometryCacheComponent)
    if not comp:
        print("[gc] 无 GeometryCacheComponent!")
        continue
    print("[gc] comp visible=%s" % comp.is_visible())
    for prop in ("geometry_cache", "play_mode", "playing", "start_time",
                 "play_rate", "looping"):
        try:
            print("[gc]   %s = %s" % (prop, comp.get_editor_property(prop)))
        except Exception as e:
            print("[gc]   %s 读取失败 %s" % (prop, e))
    print("[gc]   num_materials=%d" % comp.get_num_materials())
    bb = comp.bounds
    print("[gc]   bounds origin=%s extent=%s" % (bb.origin, bb.box_extent))
print("GC_PROBE_OK")
