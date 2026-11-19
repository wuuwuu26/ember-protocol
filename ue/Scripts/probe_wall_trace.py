# -*- coding: utf-8 -*-
import unreal
L = "[墙体射线]"
unreal.log(L + " 开始")
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
world = unreal.EditorLevelLibrary.get_editor_world()
r = unreal.SystemLibrary.line_trace_single(
    world, unreal.Vector(1700, 0, 100), unreal.Vector(1900, 0, 100),
    unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [],
    unreal.DrawDebugTrace.NONE, True)
unreal.log("%s 类型=%s" % (L, type(r)))
for a in dir(r):
    if a.startswith("_"):
        continue
    try:
        v = getattr(r, a)
        if not callable(v):
            unreal.log("%s   %s = %s" % (L, a, v))
    except Exception:
        pass
