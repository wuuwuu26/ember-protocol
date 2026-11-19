"""把导入的 GeometryCache 水面放进冷却液水渠：生成 actor、循环播放、按渠缩放。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
GC_PATH = "/Game/RobotGame/Art/Fluids/flip_channel_full"
ELL = unreal.EditorLevelLibrary
EAL = unreal.EditorAssetLibrary

ELL.load_level(LEVEL)

gc = EAL.load_asset(GC_PATH)
if not gc:
    raise RuntimeError("找不到 GeometryCache: " + GC_PATH)

# 幂等：删旧的
for a in list(ELL.get_all_level_actors()):
    if a.get_actor_label().startswith("GeoCacheWater_"):
        ELL.destroy_actor(a)

# 渠：world 中心 (450,300)，内壁 760(X)x200(Y)，水面 z=7。
# 实测：Alembic 按 ~1 Blender米≈1 UE厘米 导入（未×100），scale=1 时网格仅
# 5.49x1.125x0.45cm、局部中心 z≈0.41cm。反推缩放填满渠、波高压到 ~5cm、中心对 z=7。
loc = unreal.Vector(450.0, 300.0, 2.4)
rot = unreal.Rotator(0.0, 0.0, 0.0)
scale = unreal.Vector(138.0, 178.0, 11.0)

cls = unreal.load_class(None, "/Script/GeometryCache.GeometryCacheActor")
actor = ELL.spawn_actor_from_class(cls, loc, rot)
actor.set_actor_label("GeoCacheWater_Coolant")
actor.set_actor_scale3d(scale)

comp = actor.get_component_by_class(unreal.GeometryCacheComponent)
if comp:
    comp.set_geometry_cache(gc)
    try:
        comp.set_editor_property("play_mode",
                                 unreal.GeometryCachePlaybackMode.LOOPING)
    except Exception as e:
        unreal.log_warning("[gc] play_mode 设置失败: %s" % e)
    try:
        comp.set_editor_property("playing", True)
        comp.set_editor_property("start_time", 0.0)
        comp.set_editor_property("play_rate", 1.0)
    except Exception as e:
        unreal.log_warning("[gc] 播放属性设置失败: %s" % e)
    unreal.log("[gc] 组件材质槽数: %d" % comp.get_num_materials())

ELL.save_current_level()
print("[gc] actor=%s scale=%s" % (actor.get_actor_label(), scale))
print("GEOCACHE_PLACED_OK")
