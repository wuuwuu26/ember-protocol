# -*- coding: utf-8 -*-
"""布设冷却液泄漏池 + 断管 + 冷光；并修正倾斜道具插进地板的问题。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# ── 1. 清理旧的冷却液池与断管 ──
for a in list(unreal.EditorLevelLibrary.get_all_level_actors()):
    cls = a.get_class().get_name()
    label = a.get_actor_label()
    if cls == "RobotCoolantField" or label.startswith("CoolantPipe") or label.startswith("CoolantGlow"):
        sub.destroy_actor(a)

# ── 2. 冷却液池 ──
pool_cls = unreal.load_class(None, "/Script/RobotGame.RobotCoolantField")
if not pool_cls:
    raise RuntimeError("RobotCoolantField 类未找到")
pool = sub.spawn_actor_from_class(pool_cls, unreal.Vector(450.0, 300.0, 2.0), unreal.Rotator(0.0, 0.0, 0.0))
pool.set_actor_label("CoolantSpill_0")
pool.set_editor_property("pool_radius", 400.0)
pool.set_editor_property("grid_cells", 72)
unreal.log("COOLANT_POOL_SPAWNED")

# ── 3. 断管（池边叙事道具，管口正对水体入水点）──
pipe_cls = unreal.StaticMeshActor
pipe_mesh = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Props/SM_Prop_PipeSegment")
# 入水点：池心 (450,300) + 局部 (-0.68R, +0.34R) = (178, 436)
pipe = sub.spawn_actor_from_class(pipe_cls, unreal.Vector(178.0, 560.0, 4.0), unreal.Rotator(0.0, 0.0, 0.0))
if pipe:
    pipe.static_mesh_component.set_static_mesh(pipe_mesh)
    pipe.set_actor_scale3d(unreal.Vector(0.9, 0.9, 0.9))
    pipe.set_actor_label("CoolantPipe_0")

# ── 4. 入水口冷光 ──
light = sub.spawn_actor_from_class(unreal.PointLight, unreal.Vector(178.0, 436.0, 70.0), unreal.Rotator(0, 0, 0))
if light:
    comp = light.get_component_by_class(unreal.PointLightComponent)
    if comp:
        comp.set_intensity(4500.0)
        comp.set_attenuation_radius(420.0)
        comp.set_light_color(unreal.LinearColor(0.1, 0.85, 1.0, 1.0))
        comp.set_cast_shadows(False)
    light.set_actor_label("CoolantGlow_0")

# 池面主补光：让涟漪有高光可抓，否则暗场景里水面几乎看不见
pool_light = sub.spawn_actor_from_class(unreal.PointLight, unreal.Vector(450.0, 300.0, 190.0), unreal.Rotator(0, 0, 0))
if pool_light:
    pcomp = pool_light.get_component_by_class(unreal.PointLightComponent)
    if pcomp:
        pcomp.set_intensity(2400.0)
        pcomp.set_attenuation_radius(900.0)
        pcomp.set_light_color(unreal.LinearColor(0.16, 0.78, 1.0, 1.0))
        pcomp.set_cast_shadows(False)
    pool_light.set_actor_label("CoolantGlow_1")

# ── 5. 修正倾斜道具扎进地板：把包围盒最低点抬到地面 ──
FLOOR_TOP = 0.2
fixed = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    label = a.get_actor_label()
    if label.startswith("BG_") or label == "SkyDome":
        continue
    try:
        smc = a.static_mesh_component
        mesh = smc.get_editor_property("static_mesh")
        mname = mesh.get_name() if mesh else ""
    except Exception:
        mname = ""
    if not mname.startswith("SM_Prop_"):
        continue
    origin, extent = a.get_actor_bounds(False)
    bottom = origin.z - extent.z
    if bottom < FLOOR_TOP - 0.5:
        loc = a.get_actor_location()
        a.set_actor_location(unreal.Vector(loc.x, loc.y, loc.z + (FLOOR_TOP - bottom)), False, False)
        fixed += 1

unreal.log(f"PROPS_LIFTED {fixed}")
unreal.EditorLevelLibrary.save_current_level()

with open(r"C:\Users\25227\Documents\robot_game\docs\coolant_scene.txt", "w", encoding="utf-8") as f:
    f.write(f"pool=spawned props_lifted={fixed}\nCOOLANT_SCENE_OK\n")
unreal.log("COOLANT_SCENE_OK")
