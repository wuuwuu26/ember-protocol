# -*- coding: utf-8 -*-
"""查 PostProcessVolume 的范围（是否无限、是否覆盖新区域 X 2400..5400）。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)

out = []
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if a.get_class().get_name() != "PostProcessVolume":
        continue
    loc = a.get_actor_location()
    try:
        unbound = a.get_editor_property("unbound")
    except Exception as e:
        unbound = "err %s" % e
    try:
        st = a.get_editor_property("settings")
        method = st.get_editor_property("auto_exposure_method")
        bias = st.get_editor_property("auto_exposure_bias")
        ovm = st.get_editor_property("override_auto_exposure_method")
    except Exception as e:
        method, bias, ovm = "err", "err", "err"
    out.append("PPV %s  loc=(%.0f,%.0f,%.0f)  unbound=%s"
               % (a.get_actor_label(), loc.x, loc.y, loc.z, unbound))
    out.append("   method=%s bias=%s override=%s" % (method, bias, ovm))

with open(r"C:\Users\25227\Documents\robot_game\docs\ext_ppv.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("EXTPPV_DONE")
