import unreal
def L(s): print("[近处] %s" % s)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
# 用**相机**位置做参考（玩家 -600,0,121；相机在其后上方约 520cm）
cx, cy = -983.0, 0.0
rows = []
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    loc = a.get_actor_location()
    d = ((loc.x - cx) ** 2 + (loc.y - cy) ** 2) ** 0.5
    if d > 3200:
        continue
    mesh = ""
    try:
        c = a.static_mesh_component
        if c and c.static_mesh:
            mesh = c.static_mesh.get_name()
    except Exception:
        continue
    if not mesh or mesh == "SM_Env_Floor":
        continue
    rows.append((d, mesh, loc))
rows.sort(key=lambda r: r[0])
L("  非地板构件（按到相机的距离）:")
for d, mesh, loc in rows[:22]:
    L("    %6.0fcm  %-26s @ (%.0f,%.0f,%.0f)" % (d, mesh, loc.x, loc.y, loc.z))
L("  共 %d 个非地板构件在 3200cm 内" % len(rows))
