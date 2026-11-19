import unreal

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
actors = unreal.EditorLevelLibrary.get_all_level_actors()

print("[验证] === 关卡里网格体的 Mobility ===")
counts = {}
sample = []
for a in actors:
    if not isinstance(a, unreal.StaticMeshActor):
        continue
    comp = a.static_mesh_component
    if not comp:
        continue
    try:
        m = comp.get_editor_property("mobility")
        key = str(m)
        counts[key] = counts.get(key, 0) + 1
        if len(sample) < 3:
            mesh = comp.static_mesh
            sample.append("%s mobility=%s mesh=%s" % (
                a.get_name(), key, mesh.get_name() if mesh else "无"))
    except Exception as e:
        counts["读取失败"] = counts.get("读取失败", 0) + 1

for k, v in counts.items():
    print("[验证]   %s : %d 个" % (k, v))
for s in sample:
    print("[验证]   样例 %s" % s)

print("[验证] === 灯光 ===")
for a in actors:
    cn = a.get_class().get_name()
    if "DirectionalLight" in cn or "SkyLight" in cn:
        for p in ("light_component", "sky_light_component"):
            try:
                lc = a.get_editor_property(p)
            except Exception:
                continue
            if not lc:
                continue
            print("[验证]   %s mobility=%s intensity=%s" % (
                cn, lc.get_editor_property("mobility"),
                lc.get_editor_property("intensity")))
            break
