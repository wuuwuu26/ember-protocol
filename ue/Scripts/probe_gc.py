import unreal

ELL = unreal.EditorLevelLibrary
EAL = unreal.EditorAssetLibrary
lines = []

# 关卡里所有 GeometryCache actor
count = 0
for a in ELL.get_all_level_actors():
    cls = a.get_class().get_name()
    if "GeometryCache" in cls or "Alembic" in cls:
        count += 1
        loc = a.get_actor_location()
        scl = a.get_actor_scale3d()
        lines.append(f"actor={a.get_actor_label()} cls={cls} loc=({loc.x:.0f},{loc.y:.0f},{loc.z:.0f}) scale=({scl.x:.3f},{scl.y:.3f},{scl.z:.3f})")
        try:
            comps = a.get_components_by_class(unreal.GeometryCacheComponent)
            for c in comps:
                m = c.get_material(0)
                lines.append(f"   mat0={m.get_name() if m else 'None'}")
                lines.append(f"   visible={c.is_visible()}")
        except Exception as e:
            lines.append(f"   comp err {e}")

lines.append(f"total geometrycache actors = {count}")

gc = EAL.load_asset("/Game/RobotGame/Art/Fluids/flip_channel_full")
lines.append(f"asset exists = {gc is not None}")
if gc:
    try:
        lines.append(f"  frames = {gc.get_editor_property('end_frame')} - {gc.get_editor_property('start_frame')}")
    except Exception as e:
        lines.append(f"  frame err {e}")

open(r"C:\Users\25227\AppData\Local\Temp\opencode\gc_probe.txt", "w", encoding="utf-8").write("\n".join(lines))
unreal.log("GC_PROBE_OK")
