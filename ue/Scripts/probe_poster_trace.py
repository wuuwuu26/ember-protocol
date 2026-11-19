import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)
W = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

CAMS = [
    ("back", unreal.Vector(-900.0, -380.0, 200.0)),
    ("far", unreal.Vector(1400.0, 240.0, 200.0)),
]
TARGETS = [
    ("POSTER_back_1", unreal.Vector(-1239.0, -380.0, 200.0)),
    ("POSTER_back_3", unreal.Vector(-1239.0, 660.0, 210.0)),
    ("POSTER_far_7", unreal.Vector(1769.2, 240.0, 200.0)),
]

out = []
for cam_name, cam in CAMS:
    for tname, tgt in TARGETS:
        d = tgt - cam
        if d.length() > 3000:
            continue
        hit = unreal.SystemLibrary.line_trace_single(
            W, cam, tgt, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            False, [], unreal.DrawDebugTrace.NONE, True)
        if hit:
            a = hit.get_editor_property("actor")
            out.append("%-6s -> %-16s dist=%6.0f  blocked_by=%s" % (
                cam_name, tname, d.length(),
                a.get_actor_label() if a else "?"))
        else:
            out.append("%-6s -> %-16s dist=%6.0f  clear" % (cam_name, tname, d.length()))

open(r"C:\Users\25227\AppData\Local\Temp\opencode\trace.txt", "w",
     encoding="utf-8").write("\n".join(out))
unreal.log("TRACE_OK")
