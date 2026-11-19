# -*- coding: utf-8 -*-
"""把 4 个静态毒液池换成 ARobotCoolantField 实时浅水场。

原做法：ARobotHazardSludge 挂一块静态网格 + 静态法线贴图，水面是死的。
现在：隐藏那块网格，在同一个位置生成一个 ARobotCoolantField，
      用 M_Toxic_Fluid（绿色、泡沫、气泡、折射）作为液面材质。
      场本身的 2.5D 高度场每帧求解 —— 但毒液是死水，bStagnant=True，
      只保留很轻的环境涟漪，玩家/弹丸扰动时才起明显波纹。

另外补一块深绿池底（ToxicBed_*）：之前只藏网格不留底，水又半透明，
竞技场地板的黑色网格线直接从水下透出来，像一道一道黑栏杆。

伤害仍然由 ARobotHazardSludge 的 Zone 负责；场的 SphereComponent
关掉碰撞，避免毒液池反而给玩家降温。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
MAT_DIR = "/Game/RobotGame/Art/Materials"
TOXIC_MAT = f"{MAT_DIR}/M_Toxic_Fluid"
BED_MAT = f"{MAT_DIR}/M_Toxic_Bed"
POOL_RADIUS = 137.0
GRID_CELLS = 48
GREEN = unreal.LinearColor(0.05, 0.95, 0.12, 1.0)

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary


def make_bed_material():
    """池底：斑驳泥底（不是一块纯色板）。

    水面只有 55% 不透明，池底纹路会透过水体、并被法线折射扭动 ——
    这是"液体有深度"最有效的一条线索；纯色池底只会得到一块绿玻璃。
    每次重建，参数改动才会生效。
    """
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    if EAL.does_asset_exist(BED_MAT):
        EAL.delete_asset(BED_MAT)
    mat = tools.create_asset("M_Toxic_Bed", MAT_DIR, unreal.Material,
                             unreal.MaterialFactoryNew())
    mat.set_editor_property("shading_model",
                            unreal.MaterialShadingModel.MSM_DEFAULT_LIT)

    def ex(cls, px, py):
        return MEL.create_material_expression(mat, cls, px, py)

    def link(a, b, b_in=""):
        MEL.connect_material_expressions(a, "", b, b_in)

    def c1(v, px, py):
        e = ex(unreal.MaterialExpressionConstant, px, py)
        e.set_editor_property("r", float(v))
        return e

    def c3(x, y, z, px, py):
        e = ex(unreal.MaterialExpressionConstant3Vector, px, py)
        e.set_editor_property("constant", unreal.LinearColor(x, y, z, 1.0))
        return e

    def mul(a, b, px, py):
        e = ex(unreal.MaterialExpressionMultiply, px, py)
        link(a, e, "A")
        link(b, e, "B")
        return e

    def add(a, b, px, py):
        e = ex(unreal.MaterialExpressionAdd, px, py)
        link(a, e, "A")
        link(b, e, "B")
        return e

    def sat(a, px, py):
        e = ex(unreal.MaterialExpressionSaturate, px, py)
        link(a, e, "")
        return e

    def lerp(a, b, al, px, py):
        e = ex(unreal.MaterialExpressionLinearInterpolate, px, py)
        link(a, e, "A")
        link(b, e, "B")
        link(al, e, "Alpha")
        return e

    def sample(name, tiling, px, py):
        tex = EAL.load_asset(f"{MAT_DIR}/{name}")
        if not tex:
            raise RuntimeError("缺贴图 " + name)
        uv = ex(unreal.MaterialExpressionTextureCoordinate, px - 220, py)
        uv.set_editor_property("u_tiling", float(tiling))
        uv.set_editor_property("v_tiling", float(tiling))
        s = ex(unreal.MaterialExpressionTextureSampleParameter2D, px, py)
        s.set_editor_property("parameter_name", "Bed_" + name)
        s.set_editor_property("texture", tex)
        link(uv, s, "UVs")
        return s

    # 池底：深色湿泥 + 细颗粒。透过水体只该看到"隐约的底"，不是亮底纹身。
    patch = sample("T_Coolant_F", 1.1, -980, -420)
    grain = sample("T_Toxic_Bub", 9.0, -980, -140)
    grain2 = sample("T_Toxic_Bub", 16.0, -980, 140)
    mask = sat(add(add(mul(patch, c1(0.18, -640, -400), -500, -400),
                       mul(grain, c1(0.55, -640, -160), -500, -160), -360, -240),
                   mul(grain2, c1(0.35, -640, 80), -360, 80), -200, -140),
               -60, -140)
    base = lerp(c3(0.014, 0.020, 0.013, -360, -520),
                c3(0.003, 0.005, 0.003, -360, -620), mask, -40, -420)
    MEL.connect_material_property(
        base, "", unreal.MaterialProperty.MP_BASE_COLOR)

    rough = ex(unreal.MaterialExpressionConstant, -40, 80)
    rough.set_editor_property("r", 0.92)
    MEL.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    spec = ex(unreal.MaterialExpressionConstant, -40, 180)
    spec.set_editor_property("r", 0.10)
    MEL.connect_material_property(
        spec, "", unreal.MaterialProperty.MP_SPECULAR)
    # 池沿只留极弱的自发光：之前 0.25 系数被池子的绿色点光叠成发亮的
    # 橄榄色塑料圈（r33 实测），湿泥沿不该自己发光。
    emiss = mul(c3(0.002, 0.006, 0.003, -360, -440),
                c1(0.10, -200, -440), -40, -400)
    MEL.connect_material_property(
        emiss, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    unreal.log("[毒液场] 重建池底材质 M_Toxic_Bed（斑驳泥底）")
    return mat


unreal.EditorLevelLibrary.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
field_cls = unreal.load_class(None, "/Script/RobotGame.RobotCoolantField")
if not field_cls:
    raise RuntimeError("RobotCoolantField 类未找到")
toxic_mat = EAL.load_asset(TOXIC_MAT)
if not toxic_mat:
    raise RuntimeError("找不到 M_Toxic_Fluid")
bed_mat = make_bed_material()
cylinder = EAL.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")
if not cylinder:
    raise RuntimeError("找不到 BasicShapes/Cylinder")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())

# 清理上一轮生成的水场 + 池底
removed = 0
for a in actors:
    label = a.get_actor_label()
    if label.startswith("ToxicFluid_") or label.startswith("ToxicBed_"):
        sub.destroy_actor(a)
        removed += 1
unreal.log("[毒液场] 清理旧水场/池底 %d 个" % removed)

sludges = [a for a in actors
           if a.get_class().get_name() == "RobotHazardSludge"]
unreal.log("[毒液场] 找到 %d 个毒液池" % len(sludges))

count = 0
for i, sludge in enumerate(sludges):
    loc = sludge.get_actor_location()
    rot = sludge.get_actor_rotation()

    # 池底：斑驳泥底圆盘，半径 153cm（液面 137）——外圈 16cm 露出成暗色池沿，
    # 水面才有"嵌在池子里"的水线，而不是一块浮在地板上的绿果冻。
    # 顶面 z=3.0，液面 5±0.8，最薄处仍留 5mm 以上不穿帮。
    bed = sub.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(loc.x, loc.y, -1.0),
        unreal.Rotator(0.0, 0.0, 0.0))
    if bed:
        bed.set_actor_label("ToxicBed_%d" % i)
        bed.set_actor_scale3d(unreal.Vector(3.00, 3.00, 0.08))
        bed_comp = bed.get_component_by_class(unreal.StaticMeshComponent)
        if bed_comp:
            bed_comp.set_mobility(unreal.ComponentMobility.STATIC)
            bed_comp.set_static_mesh(cylinder)
            bed_comp.set_material(0, bed_mat)
            bed_comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)

    # 实时液面
    field = sub.spawn_actor_from_class(
        field_cls, unreal.Vector(loc.x, loc.y, loc.z),
        unreal.Rotator(0.0, rot.yaw, 0.0))
    if not field:
        unreal.log_error("[毒液场] 第 %d 个生成失败" % i)
        continue

    field.set_actor_label("ToxicFluid_%d" % i)
    field.set_editor_property("pool_radius", POOL_RADIUS)
    field.set_editor_property("grid_cells", GRID_CELLS)
    field.set_editor_property("surface_material", toxic_mat)
    field.set_editor_property("glow_color", GREEN)
    field.set_editor_property("glow_intensity", 900.0)
    field.set_editor_property("heat_cool_per_second", 0.0)
    # UE Python 对 bXxx 布尔属性的暴露名有时带 b、有时不带，两个都试。
    stagnant_set = False
    for prop in ("b_stagnant", "stagnant"):
        try:
            field.set_editor_property(prop, True)
            stagnant_set = True
            break
        except Exception:
            continue
    if not stagnant_set:
        unreal.log_warning("[毒液场] bStagnant 属性设置失败，水面会按冷液池起浪")
    # 死水不该有碎浪：高度场振幅压到 0.12cm。之前 0.8cm 在 5.7cm 网格上
    # 产生逐格法线抖动，水面铺满碎闪、像撒了糖霜（r36/r44 实测）。
    field.set_editor_property("max_height", 0.12)
    # 死水要"死"得彻底：阻尼加大、波速放慢，干涉纹来不及成形就衰减掉。
    field.set_editor_property("damping", 0.970)
    field.set_editor_property("wave_speed_sq", 0.10)

    # 场的冷却区关掉：毒液池不能给玩家降温
    zone = field.get_component_by_class(unreal.SphereComponent)
    if zone:
        zone.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)

    # 隐藏原来的静态毒液网格，只留 HazardSludge 的伤害区
    hidden = 0
    for comp in sludge.get_components_by_class(unreal.StaticMeshComponent):
        comp.set_visibility(False, True)
        hidden += 1

    # 原废液池自带一盏很亮的绿灯，会把整池打成荧光绿；
    # 压到 1500，交给液面自己的呼吸光。
    for light in sludge.get_components_by_class(unreal.PointLightComponent):
        light.set_intensity(1500.0)

    unreal.log("[毒液场] ToxicFluid_%d @ (%.0f, %.0f) 隐藏网格 %d"
               % (i, loc.x, loc.y, hidden))
    count += 1

# ── 平面反射相机：实验失败（RT 黑帧），先不布置；清掉旧实例 ──
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label().startswith("WaterMirror_"):
        sub.destroy_actor(a)

unreal.EditorLevelLibrary.save_current_level()
unreal.log("TOXIC_FIELDS_OK count=%d" % count)
