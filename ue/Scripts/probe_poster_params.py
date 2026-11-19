import unreal

MAT = "/Game/RobotGame/Art/Materials/M_Poster"
MI = "/Game/RobotGame/Art/Materials/PosterMI/MI_poster_sector7"

out = []
if not unreal.EditorAssetLibrary.does_asset_exist(MAT):
    out.append("M_Poster MISSING")
else:
    mat = unreal.EditorAssetLibrary.load_asset(MAT)
    out.append("M_Poster blend=%s shading=%s" % (
        mat.get_editor_property("blend_mode"),
        mat.get_editor_property("shading_model")))
    exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat)
    for e in exprs:
        cls = e.get_class().get_name()
        nm = ""
        try:
            nm = e.get_editor_property("parameter_name")
        except Exception:
            pass
        out.append("   expr %-40s param=%s" % (cls, nm))
    out.append("   tex params: %s" % [str(p) for p in
                                     unreal.MaterialEditingLibrary
                                     .get_texture_parameter_names(mat)])
    out.append("   scalar params: %s" % [str(p) for p in
                                        unreal.MaterialEditingLibrary
                                        .get_scalar_parameter_names(mat)])

if unreal.EditorAssetLibrary.does_asset_exist(MI):
    mi = unreal.EditorAssetLibrary.load_asset(MI)
    try:
        t = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(
            mi, "PosterTex")
        out.append("MI PosterTex = %s" % (t.get_name() if t else "None"))
    except Exception as e:
        out.append("MI tex err %s" % str(e)[:60])
    try:
        v = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(
            mi, "Brightness")
        out.append("MI Brightness = %s" % v)
    except Exception as e:
        out.append("MI scalar err %s" % str(e)[:60])
else:
    out.append("MI MISSING")

open(r"C:\Users\25227\AppData\Local\Temp\opencode\params.txt", "w",
     encoding="utf-8").write("\n".join(out))
unreal.log("PARAMS_OK")
