# -*- coding: utf-8 -*-
import unreal
L = "[地面槽位]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    lbl = a.get_actor_label()
    if lbl not in ("StaticMeshActor25", "StaticMeshActor26"):
        continue
    c = a.static_mesh_component
    mesh = c.get_editor_property("static_mesh")
    unreal.log("%s %s mesh=%s" % (L, lbl, mesh.get_name() if mesh else "无"))
    for i in range(6):
        m = c.get_material(i)
        if not m:
            continue
        base = None
        try:
            for it in m.get_editor_property("vector_parameter_values"):
                if str(it.get_editor_property("parameter_info").get_editor_property("name")) == "BaseTint":
                    v = it.get_editor_property("parameter_value")
                    base = (round(v.r,3), round(v.g,3), round(v.b,3))
        except Exception:
            pass
        unreal.log("%s   槽%d = %-22s base=%s" % (L, i, m.get_name(), base))
