import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
MAT_DIR = "/Game/RobotGame/Art/Materials"
lines = []


def safe(obj, prop):
    try:
        return obj.get_editor_property(prop)
    except Exception as e:
        return f"<err {e}>"


mi = EAL.load_asset(f"{MAT_DIR}/MI_Basin_Coolant")
parent = safe(mi, "parent")
lines.append(f"MI parent = {parent.get_name() if hasattr(parent, 'get_name') else parent}")

try:
    for p in safe(mi, "scalar_parameter_values"):
        lines.append(f"  scalar {safe(p, 'parameter_name')} = {safe(p, 'parameter_value')}")
except Exception as e:
    lines.append(f"  scalar err {e}")

mat = EAL.load_asset(f"{MAT_DIR}/M_Basin_Concrete")
lines.append(f"mat two_sided = {safe(mat, 'two_sided')}")
lines.append(f"mat shading = {safe(mat, 'shading_model')}")
lines.append(f"mat blend = {safe(mat, 'blend_mode')}")

try:
    exprs = MEL.get_material_expressions(mat)
    lines.append(f"expr count = {len(exprs)}")
    for e in exprs:
        cn = e.get_class().get_name()
        if "Constant3Vector" in cn or cn == "MaterialExpressionConstant":
            lines.append(f"  {cn}: {safe(e, 'constant') if cn == 'MaterialExpressionConstant' else safe(e, 'constant')}")
except Exception as e:
    lines.append(f"expr err {e}")

open(r"C:\Users\25227\AppData\Local\Temp\opencode\mi_probe.txt", "w", encoding="utf-8").write("\n".join(lines))
unreal.log("MI_PROBE_OK")
