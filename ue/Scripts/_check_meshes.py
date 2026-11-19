import unreal

MESHES = [
    "/Game/RobotGame/Art/Environment/SM_Env_Floor",
    "/Game/RobotGame/Art/Props/SM_Prop_Container",
    "/Game/RobotGame/Art/Characters/SK_Chassis_Light",
    "/Engine/BasicShapes/Cube",
]

print("[网格] === 网格资产检查 ===")
for p in MESHES:
    m = unreal.EditorAssetLibrary.load_asset(p)
    if not m:
        print("[网格] ❌ 加载失败: %s" % p)
        continue
    name = p.split("/")[-1]
    cls = m.get_class().get_name()
    print("[网格] --- %s (%s) ---" % (name, cls))
    # 包围盒
    try:
        b = m.get_bounds()
        print("[网格]   包围盒 origin=(%.0f,%.0f,%.0f) extent=(%.0f,%.0f,%.0f)" % (
            b.origin.x, b.origin.y, b.origin.z,
            b.box_extent.x, b.box_extent.y, b.box_extent.z))
    except Exception as e:
        print("[网格]   包围盒读取失败: %s" % str(e)[:50])
    # 材质
    try:
        n = m.get_num_materials(0) if cls == "StaticMesh" else 0
        print("[网格]   材质槽数(LOD0): %d" % n)
        for i in range(n):
            mm = m.get_material(i)
            print("[网格]     槽%d: %s" % (i, mm.get_name() if mm else "None"))
    except Exception as e:
        print("[网格]   材质读取失败: %s" % str(e)[:50])
    # 三角形数 / Nanite
    for prop in ("nanite_enabled", "num_triangles", "lod_group",
                 "never_stream", "complex_collision"):
        try:
            v = m.get_editor_property(prop)
            print("[网格]   %s = %s" % (prop, v))
        except Exception:
            pass
