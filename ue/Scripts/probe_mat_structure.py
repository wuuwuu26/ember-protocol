import unreal

MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

CANDIDATES = [
    "/Game/RobotGame/Art/Characters/M_Steel",
    "/Game/RobotGame/Art/Characters/M_SteelLight",
    "/Game/RobotGame/Art/Characters/M_Joint",
    "/Game/RobotGame/Art/Characters/M_Copper",
    "/Game/RobotGame/Art/Environment/M_Steel",
    "/Game/RobotGame/Art/Environment/M_SteelLight",
    "/Game/RobotGame/Art/Props/M_Steel",
]

out = []
seen = set()


def describe(m, label):
    out.append("=== %s  class=%s" % (label, m.get_class().get_name()))
    try:
        out.append("   shading=%s blend=%s" % (
            m.get_editor_property("shading_model"),
            m.get_editor_property("blend_mode")))
    except Exception:
        pass
    out.append("   TEX params: %s" % [str(x) for x in MEL.get_texture_parameter_names(m)])
    out.append("   SCALAR params: %s" % [str(x) for x in MEL.get_scalar_parameter_names(m)])
    out.append("   VECTOR params: %s" % [str(x) for x in MEL.get_vector_parameter_names(m)])
    exprs = MEL.get_material_expressions(m)
    out.append("   expressions=%d" % len(exprs))
    for e in exprs:
        cls = e.get_class().get_name()
        nm = ""
        try:
            p = e.get_editor_property("parameter_name")
            nm = " param=%s" % p
        except Exception:
            pass
        out.append("      %-44s%s" % (cls, nm))


for p in CANDIDATES:
    if not EAL.does_asset_exist(p):
        out.append("%s MISSING" % p)
        continue
    a = EAL.load_asset(p)
    # MI -> 取父材质
    if isinstance(a, unreal.MaterialInstanceConstant):
        parent = a.get_editor_property("parent")
        key = parent.get_path_name() if parent else p
        if key in seen:
            continue
        seen.add(key)
        describe(parent, p + "  (parent of MI)")
    else:
        key = a.get_path_name()
        if key in seen:
            continue
        seen.add(key)
        describe(a, p)

open(r"C:\Users\25227\AppData\Local\Temp\opencode\matstruct.txt", "w",
     encoding="utf-8").write("\n".join(out))
unreal.log("MATSTRUCT_OK")
