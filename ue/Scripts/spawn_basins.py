# -*- coding: utf-8 -*-
"""给液体加"容器"与持续注水：圆形池壁 + 供水立管 + 可见落水柱。

为什么：液体直接摊在地板上，材质怎么调都像"倒了一地的果冻"。一圈有厚度的
池壁给出硬水线、容器感、以及水位附近的湿润带；立管 + 落水柱 + 持续注水给出
流动性（连续外扩的涟漪 + 入水口泡沫 + 顺流漂移）。

用法：先跑 build_water_materials_v3.py，再跑本脚本，最后截图。
重复执行是幂等的：会先删掉旧的 Basin_* / Inlet_* / Pipe_* / Jet_*。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
MAT_DIR = "/Game/RobotGame/Art/Materials"
BASIN_MAT = f"{MAT_DIR}/M_Basin_Concrete"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
ELL = unreal.EditorLevelLibrary


def load_tex(name):
    return EAL.load_asset(f"{MAT_DIR}/{name}")


def _helpers(mat):
    def ex(cls, px, py):
        return MEL.create_material_expression(mat, cls, px, py)

    def link(a, b, b_in=""):
        MEL.connect_material_expressions(a, "", b, b_in)

    def c1(v, px, py):
        e = ex(unreal.MaterialExpressionConstant, px, py)
        e.set_editor_property("r", float(v))
        return e

    def c3(rgb, px, py):
        e = ex(unreal.MaterialExpressionConstant3Vector, px, py)
        e.set_editor_property("constant",
                              unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
        return e

    def op(cls, a, b, px, py):
        e = ex(cls, px, py)
        link(a, e, "A")
        link(b, e, "B")
        return e

    def lerp(a, b, alpha, px, py):
        e = ex(unreal.MaterialExpressionLinearInterpolate, px, py)
        link(a, e, "A")
        link(b, e, "B")
        link(alpha, e, "Alpha")
        return e

    return ex, link, c1, c3, op, lerp


def make_basin_material():
    """池壁材质：干水泥 ↔ 水位附近的湿水泥。

    湿区用**世界高度**判定（Basin_WetZ 标量参数），不用顶点色 ——
    顶点色依赖 OnConstruction 的执行时序，改参数后网格不重建就会整圈发黑。
    """
    if EAL.does_asset_exist(BASIN_MAT):
        EAL.delete_asset(BASIN_MAT)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mat = tools.create_asset("M_Basin_Concrete", MAT_DIR, unreal.Material,
                             unreal.MaterialFactoryNew())
    mat.set_editor_property("shading_model",
                            unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    mat.set_editor_property("two_sided", True)
    ex, link, c1, c3, op, lerp = _helpers(mat)

    # 世界高度 → 湿区遮罩（1 = 水下/湿，0 = 干）
    wp = ex(unreal.MaterialExpressionWorldPosition, -1500, 200)
    try:
        wp.set_editor_property(
            "world_position_shader_offset",
            unreal.WorldPositionIncludedOffsets.WPT_ABSOLUTE_WORLD_POSITION)
    except Exception:
        pass
    zmask = ex(unreal.MaterialExpressionComponentMask, -1320, 200)
    zmask.set_editor_property("r", False)
    zmask.set_editor_property("g", False)
    zmask.set_editor_property("b", True)
    zmask.set_editor_property("a", False)
    link(wp, zmask, "")

    wetz = ex(unreal.MaterialExpressionScalarParameter, -1320, 380)
    wetz.set_editor_property("parameter_name", "Basin_WetZ")
    wetz.set_editor_property("default_value", 5.5)

    above = op(unreal.MaterialExpressionSubtract, zmask, wetz, -1120, 280)
    above = op(unreal.MaterialExpressionDivide, above,
               c1(2.5, -1120, 420), -960, 300)
    sat = ex(unreal.MaterialExpressionSaturate, -820, 300)
    link(above, sat, "")
    wet_mask = ex(unreal.MaterialExpressionOneMinus, -660, 300)
    link(sat, wet_mask, "")

    # 只让内壁变湿：顶点色 R 是"内壁"标记（1=内壁，0=顶面/外墙）
    vc = ex(unreal.MaterialExpressionVertexColor, -660, 470)
    vcr = ex(unreal.MaterialExpressionComponentMask, -500, 470)
    vcr.set_editor_property("r", True)
    vcr.set_editor_property("g", False)
    vcr.set_editor_property("b", False)
    vcr.set_editor_property("a", False)
    link(vc, vcr, "")
    wet_mask = op(unreal.MaterialExpressionMultiply, wet_mask, vcr, -380, 380)

    # 细节贴图：去饱和后只当明暗噪声用
    # ⚠️ 网格 UV 是**以米为单位**（RobotBasin 里 U = 弧长/100），
    #    水渠 7.6m 长、水池周长 8.6m。旧值 tiling=6 会让纹理沿长度重复
    #    45~52 次，每个周期在屏幕上只有几像素 → 糊成一片纯色
    #    （这就是"水渠纹理有问题"的根因：看起来像没贴图的白边）。
    #    改成 1.5 → 每米 1.5 个周期，即约 67cm 一个周期，肉眼可辨。
    uv = ex(unreal.MaterialExpressionTextureCoordinate, -1500, -200)
    uv.set_editor_property("u_tiling", 1.5)
    uv.set_editor_property("v_tiling", 1.5)
    detail = ex(unreal.MaterialExpressionTextureSampleParameter2D, -1300, -200)
    detail.set_editor_property("parameter_name", "Basin_ConcreteDetail")
    detail.set_editor_property("texture", load_tex("T_ConcreteDetail"))
    link(uv, detail, "UVs")

    desat = ex(unreal.MaterialExpressionDesaturation, -1100, -200)
    link(detail, desat, "")

    detail_scale = op(unreal.MaterialExpressionMultiply, desat,
                      c1(0.55, -900, -120), -780, -160)
    detail_scale = op(unreal.MaterialExpressionAdd, detail_scale,
                      c1(0.72, -900, -260), -640, -180)

    dry = c3((0.105, 0.110, 0.104), -900, 380)
    wet = c3((0.013, 0.016, 0.014), -900, 480)
    base = lerp(dry, wet, wet_mask, -700, 420)
    base = op(unreal.MaterialExpressionMultiply, base, detail_scale, -480, 300)
    MEL.connect_material_property(base, "",
                                  unreal.MaterialProperty.MP_BASE_COLOR)

    rough = lerp(c1(0.92, -700, 600), c1(0.32, -700, 700), wet_mask, -520, 640)
    MEL.connect_material_property(rough, "",
                                  unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(c1(0.30, -520, 780), "",
                                  unreal.MaterialProperty.MP_SPECULAR)

    nrm = ex(unreal.MaterialExpressionTextureSampleParameter2D, -700, 900)
    nrm.set_editor_property("parameter_name", "Basin_ConcreteDetailN")
    nrm.set_editor_property("texture", load_tex("T_ConcreteDetail_N"))
    uv2 = ex(unreal.MaterialExpressionTextureCoordinate, -950, 900)
    uv2.set_editor_property("u_tiling", 1.5)
    uv2.set_editor_property("v_tiling", 1.5)
    link(uv2, nrm, "UVs")
    MEL.connect_material_property(nrm, "", unreal.MaterialProperty.MP_NORMAL)

    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    unreal.log("[水池] 重建 M_Basin_Concrete")
    return mat


def make_jet_material(name, rgb, emissive):
    """落水柱材质：半透明、沿 V 方向滚动气泡纹理，读起来是"在流的水"。"""
    path = f"{MAT_DIR}/{name}"
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mat = tools.create_asset(name, MAT_DIR, unreal.Material,
                             unreal.MaterialFactoryNew())
    mat.set_editor_property("blend_mode",
                            unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("two_sided", True)
    ex, link, c1, c3, op, lerp = _helpers(mat)

    uv = ex(unreal.MaterialExpressionTextureCoordinate, -1200, 0)
    uv.set_editor_property("u_tiling", 1.5)
    uv.set_editor_property("v_tiling", 5.0)
    pan = ex(unreal.MaterialExpressionPanner, -1000, 0)
    pan.set_editor_property("speed_x", 0.0)
    pan.set_editor_property("speed_y", -3.5)
    link(uv, pan, "Coordinate")

    tex = ex(unreal.MaterialExpressionTextureSampleParameter2D, -780, 0)
    tex.set_editor_property("parameter_name", "Jet_Bubbles")
    tex.set_editor_property("texture", load_tex("T_Toxic_Bub"))
    link(pan, tex, "UVs")

    mask = ex(unreal.MaterialExpressionComponentMask, -560, 0)
    mask.set_editor_property("r", True)
    mask.set_editor_property("g", False)
    mask.set_editor_property("b", False)
    mask.set_editor_property("a", False)
    link(tex, mask, "")

    # 不透明度：0.30 + 0.45 × 气泡 → 水柱有疏密，不是一根玻璃棍
    opacity = op(unreal.MaterialExpressionMultiply, mask,
                 c1(0.45, -380, -80), -260, -60)
    opacity = op(unreal.MaterialExpressionAdd, opacity,
                 c1(0.30, -380, 60), -100, -40)
    MEL.connect_material_property(opacity, "",
                                  unreal.MaterialProperty.MP_OPACITY)

    MEL.connect_material_property(c3(rgb, -560, 300), "",
                                  unreal.MaterialProperty.MP_BASE_COLOR)
    emis = op(unreal.MaterialExpressionMultiply, c3(rgb, -560, 460),
              c1(emissive, -380, 460), -260, 460)
    MEL.connect_material_property(emis, "",
                                  unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(c1(0.12, -100, 300), "",
                                  unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(c1(1.0, -100, 420), "",
                                  unreal.MaterialProperty.MP_SPECULAR)

    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    unreal.log("[水池] 重建 %s" % name)
    return mat


def spawn_actor(cls, loc, rot, label):
    a = ELL.spawn_actor_from_class(cls, loc, rot)
    a.set_actor_label(label)
    return a


def make_pipe(radius, length, loc, yaw, mat, label):
    """竖管（Cylinder，100cm 高、直径 100cm）+ 横臂（Cube）。"""
    a = spawn_actor(unreal.StaticMeshActor, loc, unreal.Rotator(0, 0, yaw),
                    label)
    a.set_actor_scale3d(unreal.Vector(radius / 50.0, radius / 50.0,
                                      length / 100.0))
    comp = a.get_component_by_class(unreal.StaticMeshComponent)
    if comp:
        comp.set_static_mesh(EAL.load_asset(
            "/Engine/BasicShapes/Cylinder.Cylinder"))
        comp.set_material(0, mat)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return a


def make_box(size, loc, mat, label):
    a = spawn_actor(unreal.StaticMeshActor, loc, unreal.Rotator(0, 0, 0), label)
    a.set_actor_scale3d(unreal.Vector(size[0] / 100.0, size[1] / 100.0,
                                      size[2] / 100.0))
    comp = a.get_component_by_class(unreal.StaticMeshComponent)
    if comp:
        comp.set_static_mesh(EAL.load_asset("/Engine/BasicShapes/Cube.Cube"))
        comp.set_material(0, mat)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return a


def build_inlet(field, radius, outer, water_z, metal, jet_mat, label):
    """供水系统：落地立管 → 横臂跨过池沿 → 竖管落水 → 半透明水柱。"""
    loc = field.get_actor_location()
    fx, fy = loc.x, loc.y
    riser_r = outer + 18.0
    pour_r = radius * 0.88
    top = water_z + 150.0
    mouth = water_z + 35.0

    make_pipe(9.0, top, unreal.Vector(fx + riser_r, fy, top * 0.5), 0.0,
              metal, "Pipe_Riser_" + label)
    arm_len = riser_r - pour_r
    make_box((arm_len, 18.0, 18.0),
             unreal.Vector(fx + (riser_r + pour_r) * 0.5, fy, top),
             metal, "Pipe_Arm_" + label)
    spout_len = top - mouth
    make_pipe(9.0, spout_len,
              unreal.Vector(fx + pour_r, fy, (top + mouth) * 0.5), 0.0,
              metal, "Pipe_Spout_" + label)

    # 落水柱：从管口到水面
    jet_len = mouth - water_z - 1.0
    jet = spawn_actor(unreal.StaticMeshActor,
                      unreal.Vector(fx + pour_r, fy, water_z + 1.0 + jet_len * 0.5),
                      unreal.Rotator(0, 0, 0), "Jet_" + label)
    jet.set_actor_scale3d(unreal.Vector(0.075, 0.075, jet_len / 100.0))
    comp = jet.get_component_by_class(unreal.StaticMeshComponent)
    if comp:
        comp.set_static_mesh(EAL.load_asset(
            "/Engine/BasicShapes/Cylinder.Cylinder"))
        comp.set_material(0, jet_mat)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)


def spawn_basin(field, mat, inner, outer, top_z, water_z, label):
    cls = unreal.load_class(None, "/Script/RobotGame.RobotBasin")
    if not cls:
        raise RuntimeError("找不到 RobotBasin 类")
    loc = field.get_actor_location()
    # ⚠️ 必须先生成在别处、写完属性再挪回来：OnConstruction 只在生成/移动时跑，
    #    直接生成到最终位置会用到默认参数（WetBand=10），池沿会被算成"半湿"而发黑。
    actor = spawn_actor(cls, unreal.Vector(loc.x, loc.y, 100.0),
                        unreal.Rotator(0, 0, 0), "Basin_" + label)
    for prop, val in (("inner_radius", inner), ("outer_radius", outer),
                      ("top_z", top_z), ("bottom_z", -12.0),
                      ("water_z", water_z), ("wet_band", 3.0),
                      ("segments", 96), ("rim_material", mat)):
        try:
            actor.set_editor_property(prop, val)
        except Exception as e:
            unreal.log_warning("[水池] %s 设置 %s 失败: %s"
                               % (label, prop, e))
    actor.set_actor_location(unreal.Vector(loc.x, loc.y, 0.0), False, False)
    return actor


def spawn_channel(field, mat, half_length, half_width, thickness, top_z,
                  water_z, label):
    """矩形水渠：内壁半长/半宽 + 壁厚，走向沿 +X。"""
    cls = unreal.load_class(None, "/Script/RobotGame.RobotBasin")
    if not cls:
        raise RuntimeError("找不到 RobotBasin 类")
    loc = field.get_actor_location()
    actor = spawn_actor(cls, unreal.Vector(loc.x, loc.y, 100.0),
                        unreal.Rotator(0, 0, 0), "Basin_" + label)
    for prop, val in ((("b_channel", "channel"), True),
                      ("half_length", half_length),
                      ("half_width", half_width),
                      ("wall_thickness", thickness),
                      ("top_z", top_z), ("bottom_z", -12.0),
                      ("water_z", water_z), ("wet_band", 3.0),
                      ("rim_material", mat)):
        names = prop if isinstance(prop, tuple) else (prop,)
        last = None
        for name in names:
            try:
                actor.set_editor_property(name, val)
                last = None
                break
            except Exception as e:
                last = e
        if last is not None:
            unreal.log_warning("[水渠] %s 设置 %s 失败: %s"
                               % (label, names[0], last))
    actor.set_actor_location(unreal.Vector(loc.x, loc.y, 0.0), False, False)
    return actor


def build_channel_inlet(field, half_length, half_width, thickness, water_z,
                        metal, jet_mat, label):
    """渠首龙门：立管在渠外侧 → 横臂跨过渠沿 → 竖管落水 → 水柱。"""
    loc = field.get_actor_location()
    fx, fy = loc.x, loc.y
    pour_x = fx - half_length + 50.0            # 渠首内侧 50cm 落水
    riser_y = fy - (half_width + thickness + 26.0)
    top = water_z + 150.0
    mouth = water_z + 35.0

    make_pipe(9.0, top, unreal.Vector(pour_x, riser_y, top * 0.5), 0.0,
              metal, "Pipe_Riser_" + label)
    arm_len = abs(fy - riser_y) + 18.0
    make_box((18.0, arm_len, 18.0),
             unreal.Vector(pour_x, (riser_y + fy) * 0.5, top),
             metal, "Pipe_Arm_" + label)
    spout_len = top - mouth
    make_pipe(9.0, spout_len, unreal.Vector(pour_x, fy, (top + mouth) * 0.5),
              0.0, metal, "Pipe_Spout_" + label)

    jet_len = mouth - water_z - 1.0
    jet = spawn_actor(unreal.StaticMeshActor,
                      unreal.Vector(pour_x, fy, water_z + 1.0 + jet_len * 0.5),
                      unreal.Rotator(0, 0, 0), "Jet_" + label)
    jet.set_actor_scale3d(unreal.Vector(0.075, 0.075, jet_len / 100.0))
    comp = jet.get_component_by_class(unreal.StaticMeshComponent)
    if comp:
        comp.set_static_mesh(EAL.load_asset(
            "/Engine/BasicShapes/Cylinder.Cylinder"))
        comp.set_material(0, jet_mat)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return pour_x - fx


def set_field(field, strength, interval, inflow_local, inflow_radius,
              flow_vec, label):
    # UE Python 对 bXxx 布尔属性的命名不一致：inflow / b_inflow 都试一遍。
    props = (
        (("b_inflow", "inflow"), True),
        ("inflow_local", inflow_local),
        ("inflow_strength", strength),
        ("inflow_radius", inflow_radius),
        ("inflow_interval", interval),
        ("flow_velocity", flow_vec),
    )
    for names, val in props:
        if not isinstance(names, tuple):
            names = (names,)
        ok = False
        last = None
        for prop in names:
            try:
                field.set_editor_property(prop, val)
                ok = True
                break
            except Exception as e:
                last = e
        if not ok:
            unreal.log_warning("[水池] %s 设置 %s 失败: %s"
                               % (label, names[0], last))


def main():
    ELL.load_level(LEVEL)
    basin_mat = make_basin_material()

    # 冷却液池水位在 z=7（Actor z=2 + BaseZ 5），单独一个实例改湿区高度
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mi_path = f"{MAT_DIR}/MI_Basin_Coolant"
    if EAL.does_asset_exist(mi_path):
        EAL.delete_asset(mi_path)
    basin_coolant = tools.create_asset(
        "MI_Basin_Coolant", MAT_DIR, unreal.MaterialInstanceConstant,
        unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(basin_coolant, basin_mat)
    MEL.set_material_instance_scalar_parameter_value(basin_coolant,
                                                     "Basin_WetZ", 7.0)
    MEL.update_material_instance(basin_coolant)
    EAL.save_loaded_asset(basin_coolant)

    jet_toxic = make_jet_material("M_WaterJet_Toxic",
                                  (0.10, 0.62, 0.30), 0.55)
    jet_coolant = make_jet_material("M_WaterJet_Coolant",
                                    (0.24, 0.72, 0.92), 0.50)
    metal = EAL.load_asset(f"{MAT_DIR}/M_Bolt_Trim")

    fields = [a for a in ELL.get_all_level_actors()
              if a.get_class().get_name() == "RobotCoolantField"]

    # 旧的水池构件先清掉，重复跑脚本不会堆叠
    stale_prefixes = ("Basin_", "Inlet_", "Pipe_", "Jet_")
    for a in list(ELL.get_all_level_actors()):
        if a.get_actor_label().startswith(stale_prefixes):
            ELL.destroy_actor(a)

    made = 0
    for a in fields:
        label = a.get_actor_label()
        loc = a.get_actor_location()
        # BaseZ 是私有成员（固定 5cm 基准），水面世界高度 = Actor Z + 5
        water_z = loc.z + 5.0

        if label.startswith("ToxicFluid_"):
            radius = 137.0
            outer = 152.0
            spawn_basin(a, basin_mat, radius - 1.0, outer, water_z + 3.0,
                        water_z, label)
            build_inlet(a, radius, outer, water_z, metal, jet_toxic, label)
            set_field(a, 1.1, 0.10,
                      unreal.Vector2D(radius * 0.88, 0.0), radius * 0.22,
                      unreal.Vector2D(0.0, 6.0), label)
        elif label.startswith("CoolantSpill_"):
            # 冷却液：矩形水渠，长 760 × 宽 200（内壁），走向 +X
            half_len = 380.0
            half_wid = 100.0
            thick = 28.0
            spawn_channel(a, basin_coolant, half_len, half_wid, thick,
                          water_z + 4.0, water_z, label)
            pour_x = build_channel_inlet(a, half_len, half_wid, thick, water_z,
                                         metal, jet_coolant, label)
            set_field(a, 1.3, 0.10,
                      unreal.Vector2D(pour_x, 0.0), 62.0,
                      unreal.Vector2D(35.0, 0.0), label)
        else:
            continue
        made += 1
        unreal.log("[水池] %s 池壁/供水/注水就绪 (water_z=%.1f)"
                   % (label, water_z))

    ELL.save_current_level()
    unreal.log("BASINS_OK pools=%d" % made)


main()
