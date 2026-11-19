# -*- coding: utf-8 -*-
import unreal
L = "[地面射线]"
unreal.log(L + " 开始")
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
world = unreal.EditorLevelLibrary.get_editor_world()
start = unreal.Vector(0, 0, 300)
end = unreal.Vector(0, 0, -300)
hit = unreal.SystemLibrary.line_trace_single(
    world, start, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False,
    [], unreal.DrawDebugTrace.NONE, True)
unreal.log("%s hit=%s actor=%s comp=%s" % (
    L, hit[0], hit[1].get_name() if hit[1] else "无",
    hit[2].get_name() if hit[2] else "无"))
if hit[1]:
    smc = hit[1]
    try:
        mesh = smc.get_editor_property("static_mesh")
        mats = mesh.get_editor_property("static_materials")
        for i, m in enumerate(mats):
            mi = m.get_editor_property("material_interface")
            unreal.log("%s   槽%d = %s" % (L, i, mi.get_name() if mi else "空"))
    except Exception as e:
        unreal.log("%s   读材质失败 %s" % (L, e))
