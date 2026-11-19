# -*- coding: utf-8 -*-
import unreal
L = "[天空]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
MEL = unreal.MaterialEditingLibrary
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    cn = a.get_class().get_name()
    if cn != "StaticMeshActor":
        continue
    lbl = a.get_actor_label()
    if "Sky" not in lbl and "Dome" not in lbl:
        continue
    smc = a.static_mesh_component
    for i in range(4):
        try:
            m = smc.get_material(i)
        except Exception:
            break
        if not m:
            continue
        unreal.log("%s %s 槽%d → %s" % (L, lbl, i, m.get_name()))
        if not isinstance(m, unreal.MaterialInstance):
            continue
        for pn in ("ScalarParameters", "VectorParameters"):
            pass
        try:
            vs = m.get_editor_property("vector_parameter_values")
            for it in vs:
                nm = it.get_editor_property("parameter_info").get_editor_property("name")
                v = it.get_editor_property("parameter_value")
                unreal.log("%s   %-16s = (%.3f, %.3f, %.3f)"
                           % (L, nm, v.r, v.g, v.b))
        except Exception as e:
            unreal.log("%s   vector 读取失败 %s" % (L, str(e)[:60]))
        try:
            ss = m.get_editor_property("scalar_parameter_values")
            for it in ss:
                nm = it.get_editor_property("parameter_info").get_editor_property("name")
                unreal.log("%s   %-16s = %.3f"
                           % (L, nm, it.get_editor_property("parameter_value")))
        except Exception as e:
            unreal.log("%s   scalar 读取失败 %s" % (L, str(e)[:60]))
