"""GeometryCache 水面：真实感水材质（深青基础色 + 低粗糙度镜面 + 沿流向平移的双层涟漪法线）。

要点：
- Alembic 网格无 UV，法线采样用世界坐标 XY，避免整片只采一个纹素。
- 不加白色自发光；反射靠 Fresnel 镜面 + 天空环境，水体色来自深青基础色。
- 不透明：半透明在这个零厚度薄片上渲染不出（见迭代报告第三十轮）。
"""
import unreal

MAT_DIR = "/Game/RobotGame/Art/Materials"
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
ELL = unreal.EditorLevelLibrary

name = "M_GeoCache_Water"
path = f"{MAT_DIR}/{name}"
if EAL.does_asset_exist(path):
    EAL.delete_asset(path)
mat = TOOLS.create_asset(name, MAT_DIR, unreal.Material,
                         unreal.MaterialFactoryNew())
mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
mat.set_editor_property("shading_model",
                        unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
mat.set_editor_property("two_sided", True)
# 关键：不勾 GeometryCache 用途，引擎会把材质替换成默认材质（白板的真正原因）
mat.set_editor_property("used_with_geometry_cache", True)


def ex(cls, px, py):
    return MEL.create_material_expression(mat, cls, px, py)


def c1(v, px, py):
    n = ex(unreal.MaterialExpressionConstant, px, py)
    n.set_editor_property("r", v)
    return n


def c3(r, g, b, px, py):
    n = ex(unreal.MaterialExpressionConstant3Vector, px, py)
    n.set_editor_property("constant", unreal.LinearColor(r, g, b, 1.0))
    return n


def layer(name_tex, tiling, speed_x, speed_y, px, py):
    wp = ex(unreal.MaterialExpressionWorldPosition, px - 760, py)
    sc = c1(tiling, px - 640, py + 120)
    mul = ex(unreal.MaterialExpressionMultiply, px - 520, py)
    MEL.connect_material_expressions(wp, "", mul, "A")
    MEL.connect_material_expressions(sc, "", mul, "B")
    pan = ex(unreal.MaterialExpressionPanner, px - 340, py)
    pan.set_editor_property("speed_x", speed_x)
    pan.set_editor_property("speed_y", speed_y)
    MEL.connect_material_expressions(mul, "", pan, "Coordinate")
    tex = EAL.load_asset(f"{MAT_DIR}/{name_tex}")
    samp = ex(unreal.MaterialExpressionTextureSample, px - 160, py)
    samp.set_editor_property("texture", tex)
    MEL.connect_material_expressions(pan, "", samp, "UVs")
    return samp


# 两层涟漪：Alembic 网格无 UV/切线，切线空间法线没有正确基去扰动反射，
# 水面会退化成对亮天空的均匀镜面（白板）。改用涟漪调制粗糙度制造波光，
# 这条不依赖切线，对无 UV 网格稳健。
def c2(x, y, px, py):
    n = ex(unreal.MaterialExpressionConstant2Vector, px, py)
    # UE 5.8 的 MaterialExpressionConstant2Vector 暴露的是 r/g 两个 float，
    # 没有 "constant" 属性（写成 constant 会抛 Failed to find property）。
    n.set_editor_property("r", float(x))
    n.set_editor_property("g", float(y))
    return n


def ripple_mask(tiling, speed_x, speed_y, px, py):
    wp = ex(unreal.MaterialExpressionWorldPosition, px - 900, py)
    # WorldPosition 是 float3，Panner 要 float2：先取 XY
    xy = ex(unreal.MaterialExpressionComponentMask, px - 780, py)
    xy.set_editor_property("r", True)
    xy.set_editor_property("g", True)
    xy.set_editor_property("b", False)
    xy.set_editor_property("a", False)
    MEL.connect_material_expressions(wp, "", xy, "")
    sc = c2(tiling, tiling, px - 640, py + 120)
    mul = ex(unreal.MaterialExpressionMultiply, px - 520, py)
    MEL.connect_material_expressions(xy, "", mul, "A")
    MEL.connect_material_expressions(sc, "", mul, "B")
    pan = ex(unreal.MaterialExpressionPanner, px - 340, py)
    pan.set_editor_property("speed_x", speed_x)
    pan.set_editor_property("speed_y", speed_y)
    MEL.connect_material_expressions(mul, "", pan, "Coordinate")
    tex = EAL.load_asset(f"{MAT_DIR}/T_WaterRipple_N")
    samp = ex(unreal.MaterialExpressionTextureSample, px - 160, py)
    samp.set_editor_property("texture", tex)
    MEL.connect_material_expressions(pan, "", samp, "UVs")
    return samp


r_big = ripple_mask(0.0060, 0.050, 0.004, -300, 0)
r_small = ripple_mask(0.0200, 0.085, -0.010, -300, 320)
# 取两层 R 通道平均成 0..1 的涟漪强度
mR = ex(unreal.MaterialExpressionComponentMask, -40, 80)
mR.set_editor_property("r", True)
MEL.connect_material_expressions(r_big, "", mR, "")
mR2 = ex(unreal.MaterialExpressionComponentMask, -40, 240)
mR2.set_editor_property("r", True)
MEL.connect_material_expressions(r_small, "", mR2, "")
addm = ex(unreal.MaterialExpressionAdd, 120, 160)
MEL.connect_material_expressions(mR, "", addm, "A")
MEL.connect_material_expressions(mR2, "", addm, "B")
half = ex(unreal.MaterialExpressionMultiply, 260, 160)
MEL.connect_material_expressions(addm, "", half, "A")
MEL.connect_material_expressions(c1(0.5, 180, 220), "", half, "B")

# 粗糙度 = 0.10 + 涟漪*0.18：波峰波谷反射强弱不同 -> 波光
rgh = ex(unreal.MaterialExpressionLinearInterpolate, 420, 160)
MEL.connect_material_expressions(c1(0.10, 340, 120), "", rgh, "A")
MEL.connect_material_expressions(c1(0.28, 340, 220), "", rgh, "B")
MEL.connect_material_expressions(half, "", rgh, "Alpha")
MEL.connect_material_property(rgh, "", unreal.MaterialProperty.MP_ROUGHNESS)

# 法线：仍接上（切线正常时锦上添花，异常时不影响粗糙度波光）
blend = ex(unreal.MaterialExpressionLinearInterpolate, 80, 420)
MEL.connect_material_expressions(r_big, "", blend, "A")
MEL.connect_material_expressions(r_small, "", blend, "B")
MEL.connect_material_expressions(c1(0.5, 0, 460), "", blend, "Alpha")
MEL.connect_material_property(blend, "", unreal.MaterialProperty.MP_NORMAL)

# 水体色：深青暗水体 + 微弱青光（冷却液感）；粗糙度随涟漪出波光
MEL.connect_material_property(c3(0.020, 0.080, 0.110, 80, -200), "",
                              unreal.MaterialProperty.MP_BASE_COLOR)
MEL.connect_material_property(c1(0.30, 80, -40), "",
                              unreal.MaterialProperty.MP_SPECULAR)
MEL.connect_material_property(c3(0.020, 0.090, 0.120, 80, -320), "",
                              unreal.MaterialProperty.MP_EMISSIVE_COLOR)

MEL.recompile_material(mat)
EAL.save_loaded_asset(mat)
unreal.log("[gcwater] 材质 %s 重建完成" % name)

# 关键：把材质写进 GeometryCache 资产的 materials 数组（持久化）。
# 组件层的 set_material 是运行时覆盖，不随关卡保存，游戏一启动就回退成
# WorldGridMaterial（白板根因，见迭代报告第三十一轮）。
gc = EAL.load_asset("/Game/RobotGame/Art/Fluids/flip_channel_full")
if gc:
    gc.set_editor_property("materials", [mat])
    EAL.save_loaded_asset(gc)
    unreal.log("[gcwater] 已写入资产 materials")

ELL.load_level(LEVEL)
for a in ELL.get_all_level_actors():
    if a.get_actor_label() != "GeoCacheWater_Coolant":
        continue
    comp = a.get_component_by_class(unreal.GeometryCacheComponent)
    if comp:
        comp.set_material(0, mat)
        unreal.log("[gcwater] 已赋材质到 %s" % a.get_actor_label())

ELL.save_current_level()
print("GC_WATER_MAT_OK")
