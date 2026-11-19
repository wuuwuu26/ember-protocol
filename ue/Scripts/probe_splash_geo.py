# -*- coding: utf-8 -*-
"""确定性诊断：查 Splash_Foam* 圆盘的网格、UV、以及当前实际材质。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

out = []
for a in sub.get_all_level_actors():
    label = a.get_actor_label()
    if "Splash_Foam" not in label and "Splash_Spray" not in label and "Jet_Coolant" not in label:
        continue
    cls = a.get_class().get_name()
    loc = a.get_actor_location()
    out.append("═══ %s (%s) (%.0f,%.0f,%.1f) ═══" % (label, cls, loc.x, loc.y, loc.z))
    if cls == "StaticMeshActor":
        c = a.static_mesh_component
        m = c.get_editor_property("static_mesh")
        out.append("  mesh = %s" % (m.get_path_name() if m else "None"))
        ov = c.get_editor_property("override_materials")
        out.append("  override = %s" % [x.get_name() if x else "None" for x in ov])
        # 实际材质
        for i in range(c.get_num_materials()):
            mm = c.get_material(i)
            out.append("  material[%d] = %s (%s)" % (
                i, mm.get_name() if mm else "None",
                mm.get_class().get_name() if mm else "?"))
        # 网格 UV 信息
        if m:
            try:
                lods = m.get_editor_property("get_num_lods") if False else None
            except Exception:
                pass
            try:
                # 用 MeshDescription 查 UV
                md = m.get_mesh_description(0)
                if md:
                    uvs = unreal.StaticMeshOperations.get_vertex_instance_uvs(md)
                    out.append("  UV count = %d" % len(uvs))
                    if len(uvs) > 0:
                        vals = []
                        for i in range(min(6, len(uvs))):
                            uv = uvs[i]
                            vals.append("(%.2f,%.2f)" % (uv.x, uv.y))
                        out.append("  UV samples = %s" % vals)
                else:
                    out.append("  mesh description = None")
            except Exception as e:
                out.append("  UV 查询失败: %s" % str(e)[:70])
        # 缩放/可见
        sc = a.get_actor_scale3d()
        out.append("  scale = (%.2f,%.2f,%.2f) visible=%s" % (
            sc.x, sc.y, sc.z, c.is_visible()))
    out.append("")

with open(r"C:\Users\25227\Documents\robot_game\docs\splash_geo.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("SPLASH_GEO_DONE")
