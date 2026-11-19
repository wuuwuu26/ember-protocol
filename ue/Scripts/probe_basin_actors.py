import unreal

ELL = unreal.EditorLevelLibrary
lines = []

for a in ELL.get_all_level_actors():
    label = a.get_actor_label()
    if not label.startswith("Basin_"):
        continue
    lines.append(f"actor={label}")
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        pass
    # ProceduralMeshComponent
    try:
        comps = a.get_components_by_class(unreal.ProceduralMeshComponent)
        lines.append(f"  procmesh comps={len(comps)}")
        for c in comps:
            mats = []
            for i in range(4):
                m = c.get_material(i)
                mats.append(m.get_name() if m else "None")
            lines.append(f"    materials={mats}")
            lines.append(f"    num_sections={c.get_num_sections()}")
    except Exception as e:
        lines.append(f"  procmesh err {e}")
    # 属性
    for prop in ("rim_material", "b_channel", "channel", "water_z", "top_z"):
        try:
            v = a.get_editor_property(prop)
            lines.append(f"  {prop}={v}")
        except Exception:
            pass

open(r"C:\Users\25227\AppData\Local\Temp\opencode\basin_actors.txt", "w", encoding="utf-8").write("\n".join(lines))
unreal.log("BASIN_ACTORS_OK")
