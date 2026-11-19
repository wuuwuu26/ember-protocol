# -*- coding: utf-8 -*-
"""诊断水渠/水池的材质与网格（第一百一十二轮）。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

out = []

for a in sub.get_all_level_actors():
    cls = a.get_class().get_name()
    if cls not in ("RobotBasin", "GeometryCacheActor"):
        continue
    label = a.get_actor_label()
    loc = a.get_actor_location()
    out.append("═══ %s  %s  (%.0f,%.0f,%.0f) ═══" % (cls, label, loc.x, loc.y, loc.z))

    # 所有组件
    try:
        comps = a.get_components_by_class(unreal.PrimitiveComponent)
        for c in comps:
            cname = c.get_name()
            ccls = c.get_class().get_name()
            out.append("  组件 %-22s (%s)" % (cname, ccls))
            # 材质
            try:
                n = c.get_num_materials()
                for i in range(n):
                    mat = c.get_material(i)
                    if mat:
                        # 是否 DynamicMaterialInstance
                        mcls = mat.get_class().get_name()
                        parent = ""
                        if mcls == "MaterialInstanceDynamic":
                            try:
                                parent = mat.get_editor_property("parent")
                                parent = parent.get_name() if parent else "?"
                            except Exception:
                                parent = "?"
                        out.append("      slot%d = %s (%s)%s" % (
                            i, mat.get_name(), mcls,
                            (" <- parent: " + parent) if parent else ""))
                        if mcls == "Material":
                            MEL = unreal.MaterialEditingLibrary
                            exprs = MEL.get_material_expressions(mat)
                            for e in exprs:
                                ec = e.get_class().get_name()
                                if "TextureSample" in ec:
                                    t = e.get_editor_property("texture")
                                    out.append("         贴图: %s" % (t.get_name() if t else "None"))
                    else:
                        out.append("      slot%d = None  <<< 缺材质" % i)
            except Exception as e:
                out.append("      材质读取失败: %s" % str(e)[:60])
            # 可见性
            try:
                out.append("      visible=%s hidden_in_game=%s" % (
                    c.is_visible(), c.get_editor_property("hidden_in_game")))
            except Exception:
                pass
    except Exception as e:
        out.append("  组件读取失败: %s" % str(e)[:60])
    out.append("")

with open(r"C:\Users\25227\Documents\robot_game\docs\basin_diag.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("BASIN_DIAG_DONE")
