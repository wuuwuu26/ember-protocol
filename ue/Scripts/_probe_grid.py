# -*- coding: utf-8 -*-
import unreal

def L(s): print("[棋盘] %s" % s)

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")

bad = []
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        c = a.static_mesh_component
    except Exception:
        continue
    if not c or not c.static_mesh:
        continue
    mesh = c.static_mesh.get_name()
    loc = a.get_actor_location()
    # 取第 0 槽材质
    m0 = "?"
    try:
        mats = c.get_materials()
        if len(mats) > 0 and mats[0]:
            m0 = mats[0].get_name()
        elif len(mats) == 0:
            m0 = "(无槽)"
        else:
            m0 = "空"
    except Exception as e:
        m0 = "?%s" % str(e)[:30]
    if m0 in ("WorldGridMaterial", "空", "(无槽)"):
        bad.append((a.get_name(), mesh, m0, loc))

L("用默认材质的静态网格：%d 个" % len(bad))
for n, mesh, m0, loc in bad[:25]:
    L("  %-22s %-24s 材质0=%-16s @(%.0f,%.0f,%.0f)" % (n, mesh, m0, loc.x, loc.y, loc.z))
