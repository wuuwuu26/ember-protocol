"""修注水与渠水一致性 + 表面接触 + 落点水花。

1. 水柱改深青（与渠水同色），下延插入水面（接触）。
2. 落点加泡沫环 + 溅起水花锥 + 扩散薄沫盘。
"""
import unreal

MAT_DIR = "/Game/RobotGame/Art/Materials"
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
ELL = unreal.EditorLevelLibrary

IMPACT = (120.0, 300.0)


def new_mat(name, blend, two_sided=True):
    path = f"{MAT_DIR}/{name}"
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    m = TOOLS.create_asset(name, MAT_DIR, unreal.Material,
                           unreal.MaterialFactoryNew())
    m.set_editor_property("blend_mode", blend)
    m.set_editor_property("two_sided", two_sided)
    return m


def ex(m, cls, px, py):
    return MEL.create_material_expression(m, cls, px, py)


def c1(m, v, px, py):
    n = ex(m, unreal.MaterialExpressionConstant, px, py)
    n.set_editor_property("r", v)
    return n


def c3(m, r, g, b, px, py):
    n = ex(m, unreal.MaterialExpressionConstant3Vector, px, py)
    n.set_editor_property("constant", unreal.LinearColor(r, g, b, 1.0))
    return n


# ---- 水柱：深青同色 + 竖向流动条纹 ----
jet = new_mat("M_Jet_Coolant_Stream", unreal.BlendMode.BLEND_OPAQUE)
uv = ex(jet, unreal.MaterialExpressionTextureCoordinate, -900, 0)
pan = ex(jet, unreal.MaterialExpressionPanner, -720, 0)
pan.set_editor_property("speed_x", 0.0)
pan.set_editor_property("speed_y", -0.70)   # 向下流
MEL.connect_material_expressions(uv, "", pan, "Coordinate")
bub = EAL.load_asset(f"{MAT_DIR}/T_Toxic_Bub")
bs = ex(jet, unreal.MaterialExpressionTextureSample, -540, 0)
bs.set_editor_property("texture", bub)
MEL.connect_material_expressions(pan, "", bs, "UVs")
mr = ex(jet, unreal.MaterialExpressionComponentMask, -360, 0)
mr.set_editor_property("r", True)
MEL.connect_material_expressions(bs, "", mr, "")
# 自发光 = 深青底 + 条纹提亮 -> 流动的冷却液柱
em_base = c3(jet, 0.020, 0.090, 0.120, -360, 160)
em_add = ex(jet, unreal.MaterialExpressionMultiply, -180, 80)
MEL.connect_material_expressions(mr, "", em_add, "A")
MEL.connect_material_expressions(c3(jet, 0.10, 0.30, 0.36, -300, 240), "", em_add, "B")
em = ex(jet, unreal.MaterialExpressionAdd, 0, 120)
MEL.connect_material_expressions(em_base, "", em, "A")
MEL.connect_material_expressions(em_add, "", em, "B")
MEL.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.connect_material_property(c3(jet, 0.030, 0.110, 0.150, -180, -160), "",
                              unreal.MaterialProperty.MP_BASE_COLOR)
MEL.connect_material_property(c1(jet, 0.12, -180, -80), "",
                              unreal.MaterialProperty.MP_ROUGHNESS)
MEL.connect_material_property(c1(jet, 0.4, -180, 0), "",
                              unreal.MaterialProperty.MP_SPECULAR)
MEL.recompile_material(jet)
EAL.save_loaded_asset(jet)

# ---- 泡沫材质（白沫，带气泡纹理） ----
foam = new_mat("M_Splash_Foam", unreal.BlendMode.BLEND_OPAQUE)
fuv = ex(foam, unreal.MaterialExpressionTextureCoordinate, -700, 0)
fbub = EAL.load_asset(f"{MAT_DIR}/T_Toxic_Bub")
fs = ex(foam, unreal.MaterialExpressionTextureSample, -520, 0)
fs.set_editor_property("texture", fbub)
MEL.connect_material_expressions(fuv, "", fs, "UVs")
fm = ex(foam, unreal.MaterialExpressionComponentMask, -340, 0)
fm.set_editor_property("r", True)
MEL.connect_material_expressions(fs, "", fm, "")
fem = ex(foam, unreal.MaterialExpressionMultiply, -160, 60)
MEL.connect_material_expressions(fm, "", fem, "A")
MEL.connect_material_expressions(c3(foam, 0.55, 0.75, 0.80, -300, 140), "", fem, "B")
MEL.connect_material_property(fem, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.connect_material_property(c3(foam, 0.55, 0.72, 0.78, -160, -120), "",
                              unreal.MaterialProperty.MP_BASE_COLOR)
MEL.connect_material_property(c1(foam, 0.6, -160, -40), "",
                              unreal.MaterialProperty.MP_ROUGHNESS)
MEL.recompile_material(foam)
EAL.save_loaded_asset(foam)

# ---- 溅起水花（半透明白） ----
spray = new_mat("M_Splash_Spray", unreal.BlendMode.BLEND_TRANSLUCENT)
MEL.connect_material_property(c3(spray, 0.70, 0.85, 0.90, -300, 0), "",
                              unreal.MaterialProperty.MP_BASE_COLOR)
MEL.connect_material_property(c1(spray, 0.55, -300, 100), "",
                              unreal.MaterialProperty.MP_OPACITY)
MEL.connect_material_property(c1(spray, 0.3, -300, 200), "",
                              unreal.MaterialProperty.MP_ROUGHNESS)
MEL.connect_material_property(c3(spray, 0.25, 0.40, 0.45, -300, 300), "",
                              unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.recompile_material(spray)
EAL.save_loaded_asset(spray)

# ---- 关卡：清旧水花、改水柱、加新水花 ----
ELL.load_level(LEVEL)
for a in list(ELL.get_all_level_actors()):
    if a.get_actor_label().startswith("Splash_"):
        ELL.destroy_actor(a)


def spawn(shape_op, label, loc, scale, mat, rot=None):
    shape_op(location=unreal.Vector(*loc))
    a = ELL.get_all_level_actors()[-1]
    a = unreal.EditorLevelLibrary.get_all_level_actors()[-1]
    a.set_actor_label(label)
    if rot:
        a.set_actor_rotation(unreal.Rotator(*rot), False)
    a.set_actor_scale3d(unreal.Vector(*scale))
    comp = a.get_component_by_class(unreal.StaticMeshComponent)
    if comp:
        comp.set_material(0, mat)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return a


ix, iy = IMPACT
# 水柱下延插入水面：底到 z=4（水面顶约9.4），顶接竖管口 z=42
for a in ELL.get_all_level_actors():
    if a.get_actor_label() == "Jet_CoolantSpill_0":
        a.set_actor_location(unreal.Vector(ix, iy, 23.0), False, False)
        a.set_actor_scale3d(unreal.Vector(0.07, 0.07, 0.38))
        comp = a.get_component_by_class(unreal.StaticMeshComponent)
        if comp:
            comp.set_material(0, jet)
        unreal.log("[splash] 水柱改深青并下延插入水面")

# 用 StaticMeshActor + 基本网格
def add_mesh(mesh_path, label, loc, scale, mat, rot=None):
    a = ELL.spawn_actor_from_class(unreal.StaticMeshActor,
                                   unreal.Vector(*loc),
                                   unreal.Rotator(*(rot or (0, 0, 0))))
    a.set_actor_label(label)
    a.set_actor_scale3d(unreal.Vector(*scale))
    comp = a.get_component_by_class(unreal.StaticMeshComponent)
    if comp:
        comp.set_static_mesh(EAL.load_asset(mesh_path))
        comp.set_material(0, mat)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return a


CUBE = "/Engine/BasicShapes/Cube.Cube"
CYL = "/Engine/BasicShapes/Cylinder.Cylinder"
CONE = "/Engine/BasicShapes/Cone.Cone"

# 泡沫环：扁圆柱
add_mesh(CYL, "Splash_FoamRing", (ix, iy, 8.0), (0.52, 0.52, 0.05), foam)
# 扩散薄沫盘
add_mesh(CYL, "Splash_FoamDisc", (ix, iy, 7.7), (0.90, 0.90, 0.02), foam)
# 溅起水花锥（尖朝上）
add_mesh(CONE, "Splash_SprayCone", (ix, iy, 9.0), (0.34, 0.34, 0.22), spray)

ELL.save_current_level()
print("JET_SPLASH_OK")
