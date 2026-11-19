import unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = unreal.EditorLevelLibrary.get_all_level_actors()

print("[检查] 关卡 Actor 总数: %d" % len(actors))
counts = {}
no_mesh = 0
with_mesh = 0
sample = []
for a in actors:
    n = a.get_class().get_name()
    counts[n] = counts.get(n, 0) + 1
    if isinstance(a, unreal.StaticMeshActor):
        try:
            m = a.static_mesh_component.static_mesh
        except Exception as e:
            m = None
            print("[检查] 读 static_mesh 失败: %s" % e)
        if m:
            with_mesh += 1
            if len(sample) < 3:
                sample.append("%s @ (%.0f,%.0f,%.0f)" % (m.get_name(),
                    a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z))
        else:
            no_mesh += 1

print("[检查] StaticMeshActor: 有网格 %d, 无网格 %d" % (with_mesh, no_mesh))
for s in sample:
    print("[检查]   样例: %s" % s)
print("[检查] 各类 Actor:")
for k, v in sorted(counts.items(), key=lambda x: -x[1])[:10]:
    print("[检查]   %-28s %d" % (k, v))

# 光照
for a in actors:
    cn = a.get_class().get_name()
    if "DirectionalLight" in cn:
        try:
            lc = a.get_editor_property("light_component")
            print("[检查] 平行光: 强度=%s 大气太阳光=%s 可见=%s" % (
                lc.get_editor_property("intensity"),
                lc.get_editor_property("atmosphere_sun_light"),
                lc.get_editor_property("visible")))
        except Exception as e:
            print("[检查] 平行光读取失败: %s" % e)
    if "SkyLight" in cn:
        try:
            lc = a.get_editor_property("light_component")
            print("[检查] 天光: 强度=%s 实时捕获=%s" % (
                lc.get_editor_property("intensity"),
                lc.get_editor_property("real_time_capture")))
        except Exception as e:
            print("[检查] 天光读取失败: %s" % e)
