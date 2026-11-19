import unreal

EAL = unreal.EditorAssetLibrary
MAT_DIR = "/Game/RobotGame/Art/Materials"
lines = []

for n in ("T_ConcreteDetail", "T_ConcreteDetail_N"):
    a = EAL.load_asset(f"{MAT_DIR}/{n}")
    try:
        w = unreal.Texture2D.get_editor_property(a, "blueprint_get_size_x")
    except Exception:
        w = None
    # 用另一种方式拿尺寸
    try:
        sx = a.get_editor_property("imported_size_x")
        sy = a.get_editor_property("imported_size_y")
        lines.append(f"{n}: imported={sx}x{sy}")
    except Exception as e:
        lines.append(f"{n}: size err {e}")

# 列出材质里的贴图与 tiling 参数
mat = EAL.load_asset(f"{MAT_DIR}/M_Basin_Concrete")
try:
    exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat)
    for e in exprs:
        cn = e.get_class().get_name()
        if "TextureCoordinate" in cn:
            lines.append(f"TexCoord: u={e.get_editor_property('u_tiling')} v={e.get_editor_property('v_tiling')}")
        if "TextureSample" in cn:
            try:
                pn = e.get_editor_property("parameter_name")
            except Exception:
                pn = "?"
            lines.append(f"TextureSample param={pn}")
except Exception as e:
    lines.append(f"expr err {e}")

open(r"C:\Users\25227\AppData\Local\Temp\opencode\basin_probe2.txt", "w", encoding="utf-8").write("\n".join(lines))
unreal.log("BASIN_PROBE2_OK")
