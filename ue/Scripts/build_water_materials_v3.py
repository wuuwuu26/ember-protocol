# -*- coding: utf-8 -*-
"""M_Coolant_Fluid / M_Toxic_Fluid v3 —— 真正“活”的水面。

这一版解决三件事：
  1. 法线不再是一层匀速滚动：冷却液/毒液都用两层不同尺度、不同速度的
     法线做角度校正混合，波纹有交汇、有碎浪。
  2. 毒液池不再是“一块平坦绿玻璃”：岸边泡沫（世界坐标径向遮罩）、
     上浮气泡（高频泡沫纹理取幂）、折射（IOR 1.33）、逐像素点光高光。
  3. 冷却液补上折射和泡沫高光，和 ARobotCoolantField 的实时高度场配套。

Cell Fluids 是 Blender 的付费插件，本机没有安装；这里没有假装调用它。
实际用的是同类 2.5D 浅水高度场（C++ 实时求解）+ 这套材质。
"""
import unreal

MAT_DIR = "/Game/RobotGame/Art/Materials"
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary


def load_tex(name):
    t = unreal.EditorAssetLibrary.load_asset(f"{MAT_DIR}/{name}")
    if not t:
        unreal.log_error("[水材质] 缺贴图 %s" % name)
    return t


TEX_SRC = r"C:\Users\25227\Documents\robot_game\assets\tex"


def ensure_tex(png_name, asset_name):
    """没有就从 assets/tex 导入一张灰度贴图（气泡等自生成贴图用）。"""
    path = f"{MAT_DIR}/{asset_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    task = unreal.AssetImportTask()
    task.filename = f"{TEX_SRC}\\{png_name}"
    task.destination_path = MAT_DIR
    task.destination_name = asset_name
    task.automated = True
    task.save = True
    task.replace_existing = True
    TOOLS.import_asset_tasks([task])
    t = unreal.EditorAssetLibrary.load_asset(path)
    if t:
        t.set_editor_property("compression_settings",
                              unreal.TextureCompressionSettings.TC_GRAYSCALE)
        t.set_editor_property("srgb", False)
        unreal.EditorAssetLibrary.save_loaded_asset(t)
        unreal.log("[水材质] 导入 %s" % asset_name)
    return t


def ensure_normal_tex(png_name, asset_name):
    """导入自生成的各向同性法线贴图（TC_NORMALMAP，sRGB 关）。"""
    path = f"{MAT_DIR}/{asset_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    task = unreal.AssetImportTask()
    task.filename = f"{TEX_SRC}\\{png_name}"
    task.destination_path = MAT_DIR
    task.destination_name = asset_name
    task.automated = True
    task.save = True
    task.replace_existing = True
    TOOLS.import_asset_tasks([task])
    t = unreal.EditorAssetLibrary.load_asset(path)
    if t:
        t.set_editor_property("compression_settings",
                              unreal.TextureCompressionSettings.TC_NORMALMAP)
        t.set_editor_property("srgb", False)
        unreal.EditorAssetLibrary.save_loaded_asset(t)
        unreal.log("[水材质] 导入法线 %s" % asset_name)
    return t


def create_material(name, two_sided):
    path = f"{MAT_DIR}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = TOOLS.create_asset(name, MAT_DIR, unreal.Material,
                             unreal.MaterialFactoryNew())
    if not mat:
        raise RuntimeError("创建材质失败: " + name)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("shading_model",
                            unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    mat.set_editor_property("two_sided", two_sided)

    # 逐像素光照：点光才能在动态波纹上打出会移动的高光。
    for mode_name in ("TLM_SURFACE_FORWARD_SHADING",
                      "TLM_SURFACE_PER_PIXEL_LIGHTING"):
        try:
            mode = getattr(unreal.TranslucencyLightingMode, mode_name)
            mat.set_editor_property("translucency_lighting_mode", mode)
            break
        except Exception:
            pass

    try:
        mat.set_editor_property(
            "refraction_mode",
            unreal.RefractionMode.REFMODE_INDEX_OF_REFRACTION)
    except Exception as e:
        unreal.log_warning("[水材质] refraction_mode 设置失败: %s" % e)
    return mat


class Builder(object):
    """把重复的材质节点连接包成短函数，避免几百行 connect。"""

    def __init__(self, mat):
        self.mat = mat
        self.n = 0

    def ex(self, cls, px, py):
        self.n += 1
        return MEL.create_material_expression(self.mat, cls, px, py)

    def link(self, a, a_out, b, b_in=""):
        # b 是 MaterialProperty 时走属性连接（3 参数 API），否则是节点连接。
        try:
            is_prop = isinstance(b, unreal.MaterialProperty)
        except TypeError:
            is_prop = False
        if is_prop:
            MEL.connect_material_property(a, a_out, b)
        else:
            MEL.connect_material_expressions(a, a_out, b, b_in)

    def c1(self, v, px, py):
        e = self.ex(unreal.MaterialExpressionConstant, px, py)
        e.set_editor_property("r", float(v))
        return e

    def c3(self, x, y, z, px, py):
        e = self.ex(unreal.MaterialExpressionConstant3Vector, px, py)
        e.set_editor_property("constant", unreal.LinearColor(x, y, z, 1.0))
        return e

    def mul(self, a, b, px, py):
        e = self.ex(unreal.MaterialExpressionMultiply, px, py)
        self.link(a, "", e, "A")
        self.link(b, "", e, "B")
        return e

    def add(self, a, b, px, py):
        e = self.ex(unreal.MaterialExpressionAdd, px, py)
        self.link(a, "", e, "A")
        self.link(b, "", e, "B")
        return e

    def sub(self, a, b, px, py):
        e = self.ex(unreal.MaterialExpressionSubtract, px, py)
        self.link(a, "", e, "A")
        self.link(b, "", e, "B")
        return e

    def div(self, a, b, px, py):
        e = self.ex(unreal.MaterialExpressionDivide, px, py)
        self.link(a, "", e, "A")
        self.link(b, "", e, "B")
        return e

    def sat(self, a, px, py):
        e = self.ex(unreal.MaterialExpressionSaturate, px, py)
        self.link(a, "", e, "")
        return e

    def lerp(self, a, b, alpha, px, py):
        e = self.ex(unreal.MaterialExpressionLinearInterpolate, px, py)
        self.link(a, "", e, "A")
        self.link(b, "", e, "B")
        self.link(alpha, "", e, "Alpha")
        return e

    def power(self, base, exp_value, px, py):
        e = self.ex(unreal.MaterialExpressionPower, px, py)
        self.link(base, "", e, "Base")
        self.link(self.c1(exp_value, px - 140, py + 90), "", e, "Exp")
        return e

    def max2(self, a, b, px, py):
        e = self.ex(unreal.MaterialExpressionMax, px, py)
        self.link(a, "", e, "A")
        self.link(b, "", e, "B")
        return e

    def fresnel(self, exponent, base_fraction, px, py):
        e = self.ex(unreal.MaterialExpressionFresnel, px, py)
        e.set_editor_property("exponent", float(exponent))
        e.set_editor_property("base_reflect_fraction", float(base_fraction))
        return e

    def sample(self, param, tex_name, px, py, tiling, pan):
        uv = self.ex(unreal.MaterialExpressionTextureCoordinate, px - 380, py)
        uv.set_editor_property("u_tiling", float(tiling[0]))
        uv.set_editor_property("v_tiling", float(tiling[1]))
        pan_node = self.ex(unreal.MaterialExpressionPanner, px - 210, py)
        pan_node.set_editor_property("speed_x", float(pan[0]))
        pan_node.set_editor_property("speed_y", float(pan[1]))
        self.link(uv, "", pan_node, "Coordinate")

        t = self.ex(unreal.MaterialExpressionTextureSampleParameter2D, px, py)
        t.set_editor_property("parameter_name", param)
        t.set_editor_property("texture", load_tex(tex_name))
        self.link(pan_node, "", t, "UVs")
        return t

    def mask_r(self, px, py):
        vc = self.ex(unreal.MaterialExpressionVertexColor, px, py)
        m = self.ex(unreal.MaterialExpressionComponentMask, px + 170, py)
        m.set_editor_property("r", True)
        m.set_editor_property("g", False)
        m.set_editor_property("b", False)
        m.set_editor_property("a", False)
        self.link(vc, "", m, "")
        return m

    def mask_b(self, px, py):
        """顶点色 B：入水口冲刷带（C++ 每帧写入的空间遮罩）。"""
        vc = self.ex(unreal.MaterialExpressionVertexColor, px, py)
        m = self.ex(unreal.MaterialExpressionComponentMask, px + 170, py)
        m.set_editor_property("r", False)
        m.set_editor_property("g", False)
        m.set_editor_property("b", True)
        m.set_editor_property("a", False)
        self.link(vc, "", m, "")
        return m

    def normal_blend(self, a, b, px, py):
        try:
            n = self.ex(unreal.MaterialExpressionBlendAngleCorrectedNormals,
                        px, py)
            self.link(a, "", n, "A")
            self.link(b, "", n, "B")
            return n
        except Exception as e:
            unreal.log_warning("[水材质] 法线角度混合节点不可用，退回加法: %s" % e)
            n = self.add(a, b, px, py)
            half = self.c3(0.5, 0.5, 0.0, px + 140, py)
            return self.sub(n, half, px + 280, py)

    def flatten(self, normal, flatness, px, py):
        """把法线压平一部分：0=原样，1=完全平。水面不该像丝绸一样起大褶。"""
        try:
            e = self.ex(unreal.MaterialExpressionFlattenNormal, px, py)
            e.set_editor_property("flatness", float(flatness))
            self.link(normal, "", e, "Normal")
            return e
        except Exception as e:
            unreal.log_warning("[水材质] FlattenNormal 不可用，用 lerp 替代: %s" % e)
            flat = self.c3(0.0, 0.0, 1.0, px - 150, py + 100)
            return self.lerp(flat, normal, self.c1(1.0 - flatness, px - 300, py + 160),
                             px, py)

    def radial(self, radius, px, py):
        """返回 (m, rnorm)：m=1 池心，m=0 池边。"""
        wp = self.ex(unreal.MaterialExpressionWorldPosition, px - 620, py)
        op = self.ex(unreal.MaterialExpressionObjectPositionWS, px - 620, py + 110)
        d = self.ex(unreal.MaterialExpressionDistance, px - 430, py)
        self.link(wp, "", d, "A")
        self.link(op, "", d, "B")
        rn = self.div(d, self.c1(radius, px - 430, py + 120), px - 250, py)
        m = self.sat(self.sub(self.c1(1.0, px - 250, py + 200), rn,
                             px - 110, py), px, py)
        return m, rn

    def refl_z(self, px, py):
        cls = None
        for name in ("MaterialExpressionReflectionVectorWS",
                     "MaterialExpressionReflectionVector"):
            cls = getattr(unreal, name, None)
            if cls:
                break
        if not cls:
            raise RuntimeError("找不到反射向量节点")
        rv = self.ex(cls, px, py)
        m = self.ex(unreal.MaterialExpressionComponentMask, px + 170, py)
        m.set_editor_property("r", False)
        m.set_editor_property("g", False)
        m.set_editor_property("b", True)
        m.set_editor_property("a", False)
        self.link(rv, "", m, "")
        return m

    def sky_env(self, px, py):
        """伪环境反射：ReflectVector 的 Z 在地平线暗色与天顶亮色间插值。

        水面"假"的头号原因就是不反射世界：掠射角下真水会镜像天空和
        周围墙体，塑料片不会。这一层加上去， grazing 视角立刻有水味。
        """
        z = self.sat(self.refl_z(px, py), px + 320, py)
        t = self.power(z, 0.65, px + 460, py)
        horizon = self.c3(0.050, 0.058, 0.072, px + 320, py + 150)
        zenith = self.c3(0.30, 0.38, 0.48, px + 320, py + 280)
        return self.lerp(horizon, zenith, t, px + 620, py)

    def micro_normal(self, name, tiling, pan, weight, px, py):
        """高频微涟漪法线：把大片镜面高光拆成细碎闪光，去掉塑料感。"""
        n = self.sample(name, "T_WaterRipple_N", px, py, tiling, pan)
        flat = self.c3(0.0, 0.0, 1.0, px - 200, py + 140)
        return self.lerp(flat, n, self.c1(weight, px - 200, py + 260),
                         px + 200, py + 140)



def set_common_outputs(b, foam, rough_low, rough_high, px, py,
                       opacity_node=None):
    b.link(b.c1(0.0, px, py + 120), "", unreal.MaterialProperty.MP_METALLIC)
    b.link(b.c1(0.40, px + 140, py + 120), "",
           unreal.MaterialProperty.MP_SPECULAR)
    rough = b.lerp(b.c1(rough_low, px - 240, py),
                   b.c1(rough_high, px - 240, py + 90),
                   foam, px, py)
    b.link(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    if opacity_node is not None:
        b.link(opacity_node, "", unreal.MaterialProperty.MP_OPACITY)
    # 折射：指数按水的 1.33 IOR。折射模式在 create_material 里设置。
    b.link(b.c1(1.33, px + 280, py + 200), "",
           unreal.MaterialProperty.MP_REFRACTION)


def build_coolant():
    ensure_normal_tex("water_ripple_n.png", "T_WaterRipple_N")
    ensure_tex("toxic_bubbles.png", "T_Toxic_Bub")
    mat = create_material("M_Coolant_Fluid", False)
    b = Builder(mat)

    # 泡沫：只在浪尖最陡的一小部分出现，并且用圆点打散。
    # ⚠️ 原先 vc_foam × T_Coolant_F：顶点色在全池浪尖都非零，白色刀片铺满
    #    整池，像泼了一池牛奶（r40 实测）。刀片纹理绝不能当大面积泡沫用。
    vc_foam = b.mask_r(-1500, -420)
    crest = b.sat(b.mul(b.sub(vc_foam, b.c1(0.62, -1320, -520), -1200, -520),
                        b.c1(2.2, -1200, -600), -1060, -520), -940, -520)
    scum_tex = b.sample("CoolantFoam", "T_Toxic_Bub", -1100, -380,
                        (7.0, 7.0), (0.012, 0.018))
    scum_mix = b.sat(b.add(b.mul(scum_tex, b.c1(0.90, -900, -380), -820, -380),
                           b.c1(0.20, -820, -300), -700, -380), -580, -380)
    foam = b.mul(crest, scum_mix, -820, -420)
    foam = b.mul(foam, b.c1(0.45, -820, -540), -660, -420)
    foam = b.sat(foam, -500, -420)

    # 落水点冲刷：顶点色 B（空间遮罩）+ 圆点贴图 → 水柱落点一圈翻腾白沫
    churn = b.mask_b(-1500, 1100)
    churn_tex = b.sample("CoolantChurn", "T_Toxic_Bub", -1500, 1220,
                         (6.0, 6.0), (0.020, -0.030))
    churn = b.mul(churn, churn_tex, -1200, 1140)
    churn = b.mul(churn, b.c1(1.8, -1050, 1140), -900, 1120)
    foam = b.sat(b.add(foam, churn, -700, 1100), -600, 1100)

    # 双层法线，不同尺度和漂移方向；再叠一层高频微涟漪拆高光。
    # ⚠️ 必须用各向同性法线（T_WaterRipple_N）：T_Coolant_N 是斜向条纹，
    #    会把所有高光拉成同一方向的平行长条，像拉丝金属（r35 实测）。
    # 流向沿 +X：两层主涟漪的漂移方向都改成顺流（+U），水渠才有"在流"的读感。
    n_a = b.sample("CoolantNormalA", "T_WaterRipple_N", -1080, 620,
                   (4.0, 4.0), (0.030, 0.005))
    n_b = b.sample("CoolantNormalB", "T_WaterRipple_N", -1080, 900,
                   (6.5, 6.5), (0.021, -0.004))
    normal = b.normal_blend(n_a, n_b, -720, 740)
    normal = b.flatten(normal, 0.42, -480, 740)
    # 顺流拉丝层：U 向低倍率 / V 向高倍率 → 沿流向拉长的细纹；
    # 平移速度≈流速（35cm/s ÷ 800cm ≈ 0.044 UV/s），中后段水面不再死平。
    n_streak = b.sample("CoolantNormalStreak", "T_WaterRipple_N", -1080, 1180,
                        (1.4, 7.0), (0.044, 0.0))
    n_streak = b.flatten(n_streak, 0.55, -860, 1180)
    normal = b.normal_blend(normal, n_streak, -640, 900)
    n_micro = b.micro_normal("CoolantNormalMicro", (18.0, 18.0),
                             (0.030, -0.022), 0.30, -480, 980)
    normal = b.normal_blend(normal, n_micro, -260, 800)
    b.link(normal, "", unreal.MaterialProperty.MP_NORMAL)

    # 基础色：深青水 → 泡沫灰青。
    deep = b.c3(0.006, 0.024, 0.034, -820, 40)
    foam_col = b.c3(0.20, 0.42, 0.50, -820, 160)
    base = b.lerp(deep, foam_col, foam, -560, 90)
    b.link(base, "", unreal.MaterialProperty.MP_BASE_COLOR)

    # 自发光：掠射环境反射（菲涅尔加权）+ 泡沫碎光 + 很弱的深水青。
    fres5 = b.fresnel(2.0, 0.05, -820, 380)
    sky = b.sky_env(-1500, 700)
    env = sky
    onemf = b.sub(b.c1(1.0, -560, 460), foam, -420, 460)
    env_refl = b.mul(b.mul(env, fres5, -260, 420),
                     b.mul(onemf, b.c1(1.05, -260, 520), -120, 460), 40, 420)
    foam_glow = b.mul(b.power(foam, 1.6, -560, 300),
                      b.c3(0.04, 0.20, 0.26, -560, 220), -340, 300)
    emiss = b.add(env_refl, foam_glow, -120, 360)
    emiss = b.add(emiss, b.c3(0.006, 0.030, 0.042, -120, 500), 60, 380)
    b.link(emiss, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    # 透明度：矩形水渠遮罩（UV0 = 整张方网格 0..1，按渠宽/渠长比例裁出长条）。
    # ⚠️ 掠射提升必须乘同一遮罩：否则遮罩外的方形网格四角也会半透明，
    #    水面上方浮出一块幽灵方块（r29 实测踩坑）。
    # 渠内壁在 local ±380 / ±100，对应 UV 0.025..0.975 / 0.375..0.625。
    uv = b.ex(unreal.MaterialExpressionTextureCoordinate, -1700, 1080)
    uv.set_editor_property("u_tiling", 1.0)
    uv.set_editor_property("v_tiling", 1.0)

    def axis(src, comp, px, py):
        m = b.ex(unreal.MaterialExpressionComponentMask, px, py)
        m.set_editor_property("r", comp == 0)
        m.set_editor_property("g", comp == 1)
        m.set_editor_property("b", False)
        m.set_editor_property("a", False)
        b.link(src, "", m, "")
        return m

    def ramp(x, lo, hi, px, py):
        return b.sat(b.div(b.sub(x, b.c1(lo, px, py + 70), px + 110, py + 70),
                           b.c1(max(hi - lo, 1e-4), px, py + 140), px + 220, py + 70),
                     px + 330, py)

    U = axis(uv, 0, -1560, 1040)
    V = axis(uv, 1, -1560, 1160)
    U0, U1, V0, V1, FE = 0.025, 0.975, 0.375, 0.625, 0.004
    mu = b.mul(ramp(U, U0, U0 + FE, -1380, 1040),
               b.sub(b.c1(1.0, -1380, 990), ramp(U, U1 - FE, U1, -1380, 990), -1000, 990),
               -880, 1040)
    mv = b.mul(ramp(V, V0, V0 + FE, -1380, 1180),
               b.sub(b.c1(1.0, -1380, 1330), ramp(V, V1 - FE, V1, -1380, 1330), -1000, 1330),
               -880, 1180)
    opacity_tex = b.mul(mu, mv, -720, 1100)
    opacity = b.mul(opacity_tex, b.c1(0.88, -560, 1100), -400, 1100)
    opacity = b.sat(b.add(opacity,
                          b.mul(b.mul(fres5, b.c1(0.50, -400, 1200), -300, 1180),
                                opacity_tex, 40, 1140), 160, 1100), 300, 1040)

    set_common_outputs(b, foam, 0.10, 0.38, -60, 1080, opacity)
    MEL.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    unreal.log("[水材质] M_Coolant_Fluid v3 完成")
    return mat


def build_toxic():
    ensure_normal_tex("water_ripple_n.png", "T_WaterRipple_N")
    mat = create_material("M_Toxic_Fluid", True)
    b = Builder(mat)

    m, rnorm = b.radial(137.0, -1450, 0)
    edge = b.sat(b.sub(b.c1(1.0, -1150, 170), m, -980, 120), -820, 120)

    # 泡沫：死水池只保留岸边泡沫。
    # ⚠️ 顶点色泡沫通道彻底切断：高度场速度场在网格尺度上会有棋盘状干涉，
    #    经顶点色插值后正好是 ~1 格宽的斜向"刀片"纹（隔离实验排除法实测）。
    foam_tex = b.sample("ToxicFoam", "T_Coolant_F", -1050, -380,
                        (7.0, 7.0), (0.016, 0.026))
    # 岸边泡沫只允许在最外 30% 环带：edge^2.2 衰减太慢，半径一半处
    # 还有 0.22 的泡沫量，泡沫贴图的刀片会铺满半池（隔离实验实测真凶）。
    edge_ring = b.sat(b.div(b.sub(edge, b.c1(0.86, -980, -220), -900, -220),
                            b.c1(0.14, -900, -320), -820, -220), -740, -220)
    # 岸边泡沫痂改用稀疏圆点贴图打散：T_Coolant_F 的刀片图案会在环带上
    # 留下一圈规则斜纹领子（r29 实测）。圆点 + 0.3 底 = 有机浮渣。
    scum = b.sample("ToxicScum", "T_Toxic_Bub", -1050, -120,
                    (4.0, 4.0), (0.006, 0.004))
    scum_mix = b.sat(b.add(b.mul(scum, b.c1(0.90, -880, -120), -800, -120),
                           b.c1(0.30, -800, -40), -680, -80), -560, -80)
    foam = b.mul(b.power(edge_ring, 1.5, -660, -220), scum_mix, -480, -160)
    foam = b.mul(foam, b.c1(0.75, -480, -300), -360, -220)
    foam = b.sat(foam, -260, -220)

    # 漂浮浮膜：死水表面本来就有一层不规则的薄渣，纯色绿是"果冻感"主因之一。
    # ⚠️ 强度必须很低、尺度必须很大：0.4 强度 + 2.6 平铺会把整池铺成
    #    均匀波点（r33 实测），比纯色更假。这里只用它做很淡的大块明暗。
    film = b.sample("ToxicFilm", "T_Toxic_Bub", -1050, 760,
                    (1.7, 1.7), (0.003, 0.002))
    film = b.mul(film, b.c1(0.12, -880, 820), -740, 760)
    foam_all = b.sat(b.add(foam, film, -600, 700), -460, 700)

    # 入水口冲刷：顶点色 B 是纯空间遮罩（不是高度场导出的），
    # 落水点周围因此有一圈翻腾的浅色白沫，水柱"砸进水里"才有落点。
    churn = b.mask_b(-900, 980)
    churn_tex = b.sample("ToxicChurn", "T_Toxic_Bub", -1060, 1100,
                         (6.0, 6.0), (0.020, -0.030))
    churn = b.mul(churn, churn_tex, -760, 1020)
    churn = b.mul(churn, b.c1(2.2, -600, 1020), -480, 1000)
    foam_all = b.sat(b.add(foam_all, churn, -320, 900), -180, 900)

    # 法线：宽缓大浪 + 高频微涟漪。全部用各向同性贴图：
    # T_Coolant_N 的斜向条纹会让整池高光变成同一方向的平行拉丝（r35 实测）。
    n_a = b.sample("ToxicNormalA", "T_WaterRipple_N", -1080, 520,
                   (1.9, 1.9), (0.012, 0.018))
    # 第二层不同平铺：单层周期纹在远处会显出菱形重复格（r42 英雄镜头实测）。
    n_b = b.sample("ToxicNormalB", "T_WaterRipple_N", -1080, 680,
                   (3.1, 3.1), (-0.010, 0.008))
    normal = b.normal_blend(n_a, n_b, -760, 600)
    # ⚠️ flatten 的 flatness 是 1=完全压平，0=原样。之前写成 0.22 等于
    #    保留了 78% 法线起伏，整池碎闪（r44/r45 实测踩坑）。
    normal = b.flatten(normal, 0.84, -480, 660)
    # 高频微涟漪：把油面大片镜面高光拆成细碎闪光，去塑料感。
    # ⚠️ 权重 0.85 会铺满整池碎闪（r36）；平铺 30 会露出方块重复网格（r37）。
    n_micro = b.micro_normal("ToxicNormalMicro", (11.0, 11.0),
                             (0.030, -0.024), 0.06, -480, 900)
    normal = b.normal_blend(normal, n_micro, -260, 720)
    b.link(normal, "", unreal.MaterialProperty.MP_NORMAL)

    # 基础色：深墨绿。真水在正常视角下是"暗"的 —— 亮度主要来自反射，
    # 不是本体颜色；本体一亮就成绿果冻（r29 实测）。
    deep = b.c3(0.003, 0.010, 0.006, -620, -40)
    goo = b.c3(0.008, 0.030, 0.014, -620, 80)
    foam_col = b.c3(0.26, 0.42, 0.28, -620, 200)
    base = b.lerp(deep, goo, m, -380, 40)
    base = b.lerp(base, foam_col, foam_all, -180, 80)
    # 水线接触阴影：最外 12% 压暗，水面像"插进"岸里而不是浮在地板上的圆盘。
    contact = b.sat(b.div(b.sub(edge, b.c1(0.88, -380, 200), -300, 200),
                          b.c1(0.12, -300, 300), -220, 200), -140, 200)
    base = b.lerp(base, b.c3(0.002, 0.005, 0.003, -140, 320),
                  b.mul(contact, b.c1(0.85, -40, 260), 40, 260), 140, 120)
    b.link(base, "", unreal.MaterialProperty.MP_BASE_COLOR)

    # 自发光：池心呼吸绿 + 掠射环境反射 + 岸边泡沫 + 上浮气泡。
    center_glow = b.mul(b.power(m, 3.0, -820, 380),
                        b.c3(0.004, 0.028, 0.008, -820, 500), -560, 400)
    fres5 = b.fresnel(2.0, 0.05, -820, 620)
    sky = b.sky_env(-1500, 700)
    env = sky
    onemf = b.sub(b.c1(1.0, -560, 700), foam, -420, 700)
    env_refl = b.mul(b.mul(env, fres5, -260, 660),
                     b.mul(onemf, b.c1(1.10, -260, 760), -120, 700), 20, 680)
    foam_glow = b.mul(foam, b.c3(0.05, 0.16, 0.06, -560, 240), -340, 280)

    # 气泡用独立生成的稀疏圆点贴图（T_Toxic_Bub）：
    # 复用 T_Coolant_F 会把整池铺满斜向刀片自发光（不透明隔离实验实测教训）。
    ensure_tex("toxic_bubbles.png", "T_Toxic_Bub")
    bubble_tex = b.sample("ToxicBubble", "T_Toxic_Bub", -1080, 1120,
                          (5.0, 5.0), (0.010, -0.008))
    bubbles = b.mul(bubble_tex, b.c1(0.35, -900, 1220), -820, 1120)
    bubble_glow = b.mul(bubbles, b.c3(0.010, 0.12, 0.035, -560, 1140),
                        -480, 1140)

    emiss = b.add(center_glow, env_refl, -300, 520)
    emiss = b.add(emiss, foam_glow, -120, 540)
    emiss = b.add(emiss, bubble_glow, 60, 560)
    b.link(emiss, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    # 透明度：中心 55% —— 让斑驳池底透过水体、被折射扭动；掠射角提升到近镜面。
    # ⚠️ 提升项必须乘 inner，否则方形网格四角会浮出幽灵方块。
    inner = b.sat(b.div(b.sub(b.c1(0.998, -800, 860), rnorm, -640, 860),
                        b.c1(0.005, -800, 960), -480, 860), -320, 860)
    opacity = b.mul(inner, b.c1(0.78, -320, 980), -140, 900)
    opacity = b.sat(b.add(opacity,
                          b.mul(b.mul(fres5, b.c1(0.35, -140, 1060), 20, 1020),
                                inner, 160, 960), 300, 920), 420, 900)

    set_common_outputs(b, foam_all, 0.30, 0.45, 120, 1040, opacity)
    MEL.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    unreal.log("[水材质] M_Toxic_Fluid v3 完成")
    return mat


def main():
    coolant = build_coolant()
    toxic = build_toxic()
    unreal.log("WATER_MAT_V3_OK coolant=%s toxic=%s"
               % (coolant.get_name() if coolant else "null",
                  toxic.get_name() if toxic else "null"))
    with open(r"C:\Users\25227\Documents\robot_game\docs\water_mat_v3.txt",
              "w", encoding="utf-8") as f:
        f.write("WATER_MAT_V3_OK\n")


main()
