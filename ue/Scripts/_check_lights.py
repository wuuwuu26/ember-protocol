import unreal

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
actors = unreal.EditorLevelLibrary.get_all_level_actors()

print("[灯光] === 关卡灯光检查 ===")
found = 0
for a in actors:
    cn = a.get_class().get_name()
    if "Light" not in cn and "Atmosphere" not in cn:
        continue
    found += 1
    print("[灯光] --- %s ---" % cn)
    for prop in ("light_component", "directional_light_component",
                 "sky_light_component"):
        try:
            lc = a.get_editor_property(prop)
        except Exception:
            continue
        if not lc:
            continue
        # Mobility
        try:
            print("[灯光]   mobility = %s" % lc.get_editor_property("mobility"))
        except Exception as e:
            print("[灯光]   mobility 读取失败: %s" % str(e)[:40])
        for p in ("intensity", "atmosphere_sun_light", "real_time_capture",
                  "visible", "affects_world"):
            try:
                print("[灯光]   %s = %s" % (p, lc.get_editor_property(p)))
            except Exception:
                pass
        break

print("[灯光] 共找到 %d 个灯光/大气 Actor" % found)
