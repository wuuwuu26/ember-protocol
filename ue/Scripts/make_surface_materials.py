# -*- coding: utf-8 -*-
"""
全项目表面材质：给机体 / 环境 / 道具 / 模块套上"三平面细节 + 金属工作流"。
================================================================

用户要求："机器人建模可以加上表面纹理，更精细"、"画面堪比 3A"。

原来的材质是 FBX 导入器生成的 **Phong 传统工作流**（DiffuseColor +
SpecularColor + Shininess，Metallic = 0）—— 金属度为零，所以机体看起来
像"上了色的塑料"，这是最不像 3A 的一环。本脚本做三件事：

  ① 换工作流：Metallic / Roughness 走金属工作流（钢 0.90 / 铜 0.95 …）
  ② 加细节层：三平面投影采样的面板缝 / 铆钉 / 油污 / 刮痕
     **不能用 UV** —— 这批资产是 Smart UV 自动展开的，方向随机，
     贴上去相邻面各朝各的方向，接缝处会撕裂。三平面完全绕开 UV。
  ③ 保留原配色：颜色不是抄 Blender 源码，而是**从现有材质实例里读**
     （DiffuseColor / EmissiveColor）—— 抄错一个数，整台机器配色就变了，
     而且很难发现。

⚠️ 这批材质**全是 MaterialInstanceConstant**，父类是 FBXLegacyPhongSurfaceMaterial。
   筛选时只认 "Material" 会得到 0 个（踩过）。
   换装是"把现有实例重新指定父类"，不是新建同名资产 —— 这样关卡与蓝图里
   的引用全部自动跟上，不需要改任何引用。

用法: bash tools/ue_py.sh ue/Scripts/make_surface_materials.py "表面材质"
"""
import unreal

ART = "/Game/RobotGame/Art"
MAT_DIR = ART + "/Materials"
MASTER_PATH = MAT_DIR + "/M_RobotSurface"
TEX_DIR = r"C:\Users\25227\Documents\robot_game\assets\tex"

# 引擎自带的三平面投影材质函数。用引擎的而不是手搭：手搭要 25+ 个表达式
# 节点，且引脚接线容易出错；引擎这个函数经过验证。
#
# ⚠️ 引脚名**必须**用「遍历材质函数内部的 FunctionInput / FunctionOutput 节点」
#    的方式读出来，不能写死、更不能"试着连一遍看哪个不报错" ——
#    connect_material_expressions 对不存在的引脚名**不会报错**，
#    它会静默成功但什么都不连，最后得到一个空壳材质还以为是对的。
#    实测（probe_fn_pins.py）：
#      WorldAlignedTexture 输入 = World Space Normal / TextureObject /
#                                 TextureSize / WorldPosition /
#                                 Export Float 4 / ProjectionTransitionContrast
#                        输出 = 'XYZ Texture' / 'XY Texture' / 'Z Texture'
#      WorldAlignedNormal  输入 = Normal / TextureObject / TextureSize /
#                                 WorldPosition / WorldSpace /
#                                 Use High Quality Normals /
#                                 ProjectionTransitionContrast
#                        输出 = 'XYZ Texture' / 'XYZFlatTop' / ...
#    注意：**没有 WorldPositionScale**，平铺密度由 TextureSize 控制
#    （TextureSize = 一张贴图覆盖多少世界单位；越大 → 图案越大）。
WAF = ("/Engine/Functions/Engine_MaterialFunctions01/Texturing/"
       "/WorldAlignedTexture")
WAN = ("/Engine/Functions/Engine_MaterialFunctions01/Texturing/"
       "/WorldAlignedNormal")

unreal.log("[表面材质] 脚本已开始执行")


def log(m):
    unreal.log("[表面材质] %s" % m)


def norm(s):
    return "".join(ch for ch in str(s).lower() if ch.isalnum())


# ─────────────────────────────────────────────
# 金属度 / 粗糙度表（按材质名匹配，不匹配就用默认）
# ─────────────────────────────────────────────
# ⚠️ 金属度不能一味往高里给。第一版按"机器人 = 全金属"给了 0.88~0.95，
#    结果整机变成一块**黑铁疙瘩** —— 因为金属没有漫反射，画面里唯一能
#    反射的就是天空（而天空在相机背后看不到的地方），实际收到的能量极少。
#    现实中的 3A 机器人美术几乎都是"**上漆的装甲板 + 裸露的关节/活塞**"：
#    大面积装甲走低金属度（0.25~0.45，靠漫反射把固有色显示出来），
#    只有关节、活塞、管线走真金属（0.6~0.95）做点缀。
#    这样既有金属的锐利高光，又不会丢掉整体配色。
#    (前缀, Metallic, Roughness, 是否自发光件)
# ⚠️ 金属度不能给太高。
# 金属材质的颜色**几乎全部来自反射**，而这个场景的天空和地面都很暗，
# 于是 metallic 0.9 的装甲反射出来就是一片黑 —— 实测整机变成黑剪影，
# 在黄昏光下完全没有体积感。真实机甲的装甲是**上漆的**，漆层是电介质，
# 只有裸露的钢板/关节/管线才是真金属。所以：
#   涂装装甲 0.15~0.30（靠漫反射出颜色，读得出形体）
#   裸露金属 0.85~0.95（靠反射出"金属感"，但面积要小）
METAL_TABLE = [
    # ⚠️ 金属度必须低。涂装装甲板的本质是"漆面"（金属度≈0.1），
    #    之前给到 0.42/0.30，材质就几乎只靠反射环境 ——
    #    而这个场景是夜景、天空很暗，结果机体在游戏里永远是黑的，
    #    贴图细节完全看不见（这也是"看起来没有纹理"的一半原因）。
    ("M_SteelLight",   0.16, 0.38, False),   # 裸露钢板 / 边缘
    ("M_Steel",        0.10, 0.54, False),   # 主体装甲（上漆）
    ("M_Copper",       0.92, 0.30, False),   # 活塞 / 管线，真金属
    ("M_Joint",        0.55, 0.64, False),   # 关节（油污、磨损）
    ("M_Rust",         0.12, 0.86, False),   # 锈蚀件
    ("M_AccentDark_",  0.18, 0.52, False),
    ("M_Accent_",      0.15, 0.36, False),   # 彩色识别面板
    ("M_Core_",        0.05, 0.28, True),
    ("M_Visor_",       0.10, 0.14, True),
]

# 各目录的细节尺度 —— 这里给的是 **TextureSize（一张贴图覆盖多少厘米）**。
# 环境的面比机体大一个量级，用同一尺度会变成一片噪点。
DETAIL_SCALE = {
    # 单位是"一张贴图铺多少厘米"（世界坐标 / 这个值 = UV）。
    #
    # ★ 2026-10-24：贴图从 3×3 等分改成 BSP 分割的 **11×11 ≈ 128 块板**，
    #   所以"一张铺多少"必须同比放大，否则板会密到看不出：
    #     Characters 360cm / 11 ≈ 33cm 一块板（真实装甲板量级）
    #     Environment 440cm / 11 ≈ 40cm（地面、墙体的分格）
    #   旧值 120/260 是配 3×3 的（40cm/块），直接沿用会变成 11cm/块。
    # 2026-10-24 二调：360 在近景下只有 6 倍缩小，22mm 的缝被压成 1 像素；
    # 收到 240 后缩小倍率降到 4 倍，缝能保住 2 像素，近看才读得出刻线。
    "Characters": 240.0,
    "Environment": 440.0,
    "Props": 320.0,
    "Modules": 360.0,
}

# 各目录用哪套细节贴图
DETAIL_TEX = {
    "Characters": ("T_MechDetail", "T_MechDetail_N"),
    "Modules": ("T_MechDetail", "T_MechDetail_N"),
    "Environment": ("T_EnvDetail", "T_EnvDetail_N"),
    "Props": ("T_EnvDetail", "T_EnvDetail_N"),
}

# ── 各目录的明度 / 金属度修正 ──
#
# 为什么必须修正：原来的 DiffuseColor 是给 **Phong 传统工作流**（Metallic=0）
# 调的 —— 那种工作流下 0.08 的暗色靠漫反射 + 高光还能看清。
# 一换成金属工作流（Metallic 0.9），BaseColor 的含义就变了：
# 它变成了"金属的反射率"，0.08 的反射率 ≈ 几乎不反射任何东西 ≈ 全黑。
# 实测第一版就是这样：整机变成一块黑铁疙瘩。
#
# ⚠️ 但**不能直接乘一个系数**：accent 面板本来就是亮色（0.88,0.58,0.18），
#    乘 3.6 之后三个通道全被 clamp 到 1 → 变成白黄色，橙色的辨识度就没了。
#    正确做法是"把最亮通道拉到目标值，其它通道等比跟随"——
#    保色相、只改明度。已经够亮的颜色 scale 会被夹到 1，保持原样。
#
# 目标亮度取"深色军用钢"的观感：反射率 0.30 左右
# （真实抛光钢 0.56 / 铁 0.56 / 铜 0.95，这里刻意压暗走风格化路线）。
FOLDER_ADJUST = {
    #               目标最大通道值, Metallic 倍数, 最大提亮倍数
    "Characters": (0.30, 1.00, 4.0),
    "Modules": (0.30, 1.00, 4.0),
    "Environment": (0.155, 0.55, 3.2),
    "Props": (0.20, 0.60, 3.4),
}


def lift_color(base, target, cap):
    """保色相地把颜色提到目标亮度（只提不压，且不超过 cap 倍）。"""
    m = max(base)
    if m <= 1e-4:
        return base
    scale = min(max(target / m, 1.0), cap)
    return tuple(min(c * scale, 1.0) for c in base)


# ─────────────────────────────────────────────
# 指定配色（覆盖 FBX 里的 DiffuseColor）
# ─────────────────────────────────────────────
#
# ⚠️ 为什么不能只靠"从现有实例里读颜色"：
#   重导 FBX 时，导入器发现同名材质已存在，会**复用旧实例**、不更新颜色 ——
#   于是 Blender 里改了 Palette，UE 里一点变化都没有（本轮实测）。
#   而且这套配色需要整体美术方向统一，不能由每个资产各自决定。
#
# 美术方向：**冷灰蓝涂装 + 安全色点缀 + 深色骨架**
#   场景是暖色（黄昏 / 钠灯 / 沙尘），机体走冷色才能在画面里"跳"出来；
#   反过来，环境本身要用深钢灰，否则暖光打在浅色地板上会整片泛黄。
#
# 数值参考（线性空间，UE BaseColor）：
#   涂装装甲 0.22~0.30 → 在 30000lux 的黄昏光下读作"浅灰"
#   裸露钢板 0.34~0.40 → 边缘/护板，比装甲亮一档
#   骨架     0.06~0.09 → 保证装甲之间那条缝是黑的，分块才看得见
FORCE_COLOR = {
    "Characters": [
        ("M_SteelLight", (0.400, 0.412, 0.428)),
        ("M_Steel",      (0.300, 0.312, 0.336)),
        ("M_Frame",      (0.075, 0.079, 0.088)),
        ("M_Joint",      (0.052, 0.054, 0.060)),
        ("M_Rust",       (0.135, 0.078, 0.048)),
        ("M_Copper",     (0.360, 0.205, 0.095)),
    ],
    "Environment": [
        ("M_SteelLight", (0.165, 0.172, 0.185)),
        ("M_Steel",      (0.105, 0.112, 0.125)),
        ("M_Joint",      (0.035, 0.037, 0.042)),
        ("M_Accent_prop",     (0.560, 0.360, 0.070)),   # 安全黄
        ("M_Accent_landmark", (0.560, 0.360, 0.070)),
        ("M_AccentDark_prop", (0.185, 0.120, 0.030)),
        ("M_AccentDark_landmark", (0.185, 0.120, 0.030)),
        ("M_Copper",     (0.330, 0.190, 0.090)),
    ],
    "Props": [
        ("M_SteelLight", (0.245, 0.252, 0.262)),
        ("M_Steel",      (0.165, 0.172, 0.185)),
        ("M_Accent_prop", (0.560, 0.360, 0.070)),
        ("M_AccentDark_prop", (0.185, 0.120, 0.030)),
        ("M_Rust",       (0.150, 0.085, 0.050)),
    ],
    "Modules": [],
}


def forced_color(folder, name):
    for pre, col in FORCE_COLOR.get(folder, []):
        if name.startswith(pre):
            return col
    return None



def metal_of(name):
    for pre, mt, rg, em in METAL_TABLE:
        if name.startswith(pre):
            return mt, rg, em
    return 0.60, 0.50, False


def folder_of(pkg):
    for k in DETAIL_SCALE:
        if "/Art/%s/" % k in pkg:
            return k
    return "Characters"


# ─────────────────────────────────────────────
# 贴图导入
# ─────────────────────────────────────────────

def import_tex(fname, name, normal_map):
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    path = "%s\\%s" % (TEX_DIR, fname)
    task = unreal.AssetImportTask()
    task.filename = path
    task.destination_path = MAT_DIR
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True
    try:
        tools.import_asset_tasks([task])
    except Exception as e:
        log("❌ 导入 %s 失败: %s" % (fname, e))
        return None
    tex = unreal.EditorAssetLibrary.load_asset("%s/%s" % (MAT_DIR, name))
    if not tex:
        log("❌ 导入后读不到 %s" % name)
        return None
    try:
        tex.set_editor_property("srgb", False)      # 数据贴图不做 sRGB 解码
    except Exception:
        pass
    try:
        tex.set_editor_property(
            "compression_settings",
            unreal.TextureCompressionSettings.TC_NORMALMAP if normal_map
            else unreal.TextureCompressionSettings.TC_MASKS)
    except Exception:
        pass
    unreal.EditorAssetLibrary.save_loaded_asset(tex)
    log("  贴图 %s (%dx%d)" % (name, tex.blueprint_get_size_x(),
                               tex.blueprint_get_size_y()))
    return tex


# ─────────────────────────────────────────────
# 主材质
# ─────────────────────────────────────────────

def build_master():
    mel = unreal.MaterialEditingLibrary
    at = unreal.AssetToolsHelpers.get_asset_tools()

    if unreal.EditorAssetLibrary.does_asset_exist(MASTER_PATH):
        unreal.EditorAssetLibrary.delete_asset(MASTER_PATH)

    mat = at.create_asset("M_RobotSurface", MAT_DIR,
                          unreal.Material, unreal.MaterialFactoryNew())
    if not mat:
        log("❌ 主材质创建失败")
        return None
    log("主材质已创建")

    for flag in ("used_with_skeletal_mesh", "used_with_static_mesh",
                 "used_with_instanced_static_meshes"):
        try:
            mat.set_editor_property(flag, True)
        except Exception:
            pass

    def vec(name, color, x, y):
        e = mel.create_material_expression(
            mat, unreal.MaterialExpressionVectorParameter, x, y)
        e.set_editor_property("parameter_name", name)
        e.set_editor_property("default_value", unreal.LinearColor(
            color[0], color[1], color[2], 1.0))
        return e

    def sca(name, v, x, y):
        e = mel.create_material_expression(
            mat, unreal.MaterialExpressionScalarParameter, x, y)
        e.set_editor_property("parameter_name", name)
        e.set_editor_property("default_value", float(v))
        return e

    def ex(cls, x, y):
        return mel.create_material_expression(mat, cls, x, y)

    def cst(v, x, y):
        e = ex(unreal.MaterialExpressionConstant, x, y)
        e.set_editor_property("r", float(v))
        return e

    conn = [0]

    def link(src, dst, inp, out=""):
        try:
            mel.connect_material_expressions(src, out, dst, inp)
            conn[0] += 1
            return True
        except Exception as e:
            log("    连接 %s 失败: %s" % (inp, str(e)[:70]))
            return False

    def prop(src, p, out=""):
        try:
            mel.connect_material_property(src, out, p)
            conn[0] += 1
            return True
        except Exception as e:
            log("    输出 %s 失败: %s" % (p, str(e)[:70]))
            return False

    # ── 参数 ──
    p_base = vec("BaseTint", (0.082, 0.092, 0.108), -2600, -900)
    p_emiss = vec("EmissiveTint", (0.0, 0.0, 0.0), -2600, -750)
    p_epow = sca("EmissivePower", 1.0, -2600, -600)
    p_metal = sca("Metallic", 0.90, -2600, -480)
    p_rough = sca("Roughness", 0.42, -2600, -360)
    p_scale = sca("TextureSize", 62.0, -2600, -240)
    # SeamDarken 现在是"槽底亮度"：cav = lerp(SeamDarken, 1, height)。
    # 高度 0.16（槽底）/ 0.70（倒角）/ 1.00（板面）→ 0.42 给出
    # 槽 0.51、倒角 0.83、板面 1.0 的三级明暗，正好是"板厚 + 倒角 + 凹槽"。
    p_seam = sca("SeamDarken", 0.30, -2600, 0)
    p_rdet = sca("RoughDetail", 0.30, -2600, 120)
    p_wear = sca("WearAmount", 0.50, -2600, 240)
    p_wtint = vec("WearTint", (0.55, 0.52, 0.48), -2600, 360)
    p_damt = sca("DetailAmount", 1.0, -2600, 480)
    p_nstr = sca("NormalStrength", 1.0, -2600, 600)
    p_vcol = sca("VertexColorAmount", 1.0, -2600, 720)
    p_ao = sca("SeamAO", 0.55, -2600, 840)

    vcol = ex(unreal.MaterialExpressionVertexColor, -2600, 980)

    # 贴图对象参数
    t_detail = ex(unreal.MaterialExpressionTextureObjectParameter, -2350, -1050)
    t_detail.set_editor_property("parameter_name", "DetailTex")
    t_normal = ex(unreal.MaterialExpressionTextureObjectParameter, -2350, -880)
    t_normal.set_editor_property("parameter_name", "NormalTex")

    # ── 三平面采样 ──
    waf = unreal.EditorAssetLibrary.load_asset(WAF)
    wan = unreal.EditorAssetLibrary.load_asset(WAN)
    if not waf:
        log("❌ 找不到 %s" % WAF)
        return None

    def pins_of(fn):
        """遍历材质函数内部，读出**真实**的输入/输出引脚名。

        为什么不用 MaterialEditingLibrary.get_inputs_for_material_function_expression：
        它返回的对象里 input_name 全是 None（实测），拿不到名字。
        遍历内部的 FunctionInput / FunctionOutput 节点是唯一可靠的路子。
        """
        ins, outs = [], []
        for e in mel.get_material_function_expressions(fn):
            cn = e.get_class().get_name()
            try:
                if "FunctionInput" in cn:
                    ins.append(str(e.get_editor_property("input_name")))
                elif "FunctionOutput" in cn:
                    outs.append(str(e.get_editor_property("output_name")))
            except Exception:
                pass
        return ins, outs

    # ★ 世界位置必须显式接到三平面函数的 WorldPosition 引脚上。
    #   不接的话该引脚取默认常量 0 —— 所有像素采样的是同一个纹素，
    #   整个表面变成一块纯色平板。这就是"加了细节贴图却完全看不出来"的原因。
    p_wpos = ex(unreal.MaterialExpressionWorldPosition, -2100, -1250)

    def triplanar(fn, tex_obj, x, y):
        if not fn:
            return None, None
        fc = ex(unreal.MaterialExpressionMaterialFunctionCall, x, y)
        try:
            if not fc.set_material_function(fn):
                log("  材质函数挂载失败: %s" % fn.get_name())
                return None, None
        except Exception as e:
            log("  set_material_function 抛异常: %s" % str(e)[:80])
            return None, None

        fin, fout = pins_of(fn)

        def pick(names, *cands):
            for c in cands:
                nc = norm(c)
                for n in names:
                    if norm(n) == nc:
                        return n
            return None

        pin_tex = pick(fin, "TextureObject")
        pin_size = pick(fin, "TextureSize")
        pin_wp = pick(fin, "WorldPosition")
        out_xyz = pick(fout, "XYZTexture", "XYZ", "XYZFlatTop")
        if not out_xyz:
            out_xyz = pick(fout, "XYTexture", "ZTexture")
        log("  三平面 %s: 输入=%s 输出=%s → 用 %s / %s"
            % (fn.get_name(), fin, fout, pin_tex, out_xyz))
        if not pin_tex or not out_xyz:
            log("  ❌ 引脚缺失，这个通道跳过")
            return None, None
        link(tex_obj, fc, pin_tex)
        if pin_size:
            link(p_scale, fc, pin_size)
        if pin_wp:
            link(p_wpos, fc, pin_wp)
        else:
            log("  ⚠️ 函数没有 WorldPosition 引脚，三平面会退化成纯色")
        return fc, out_xyz

    # ── UV 采样（立方投影 UV，见 robotlib.cube_uv）──
    #
    # ⚠️ 2026-10-19 改：原来的三平面（WorldAlignedTexture 材质函数）在本机
    #    **完全失效且无法验证** —— 无论把 TextureSize 从 120 改到 40、
    #    SeamDarken 从 0.46 改到 0.02、WearTint 改成纯红，
    #    画面一个像素都不变。函数节点的引脚连线在 Python 里读不出来，
    #    没法确认它到底连没连上，只能放弃这条路。
    #
    #    改成直接按 UV0 采样。资产侧（build_chassis / build_walls）
    #    已经把 UV 做成**世界对齐的立方投影**（1 UV 单位 = 1.2m），
    #    同一个朝向的面共享连续 UV，面板缝不会撕裂 ——
    #    也就是说"三平面"的效果已经在建模阶段解决了，材质里不需要再算。
    # ══════════════════════════════════════════════════════════
    # 世界对齐三平面采样（**不依赖网格 UV**）
    # ══════════════════════════════════════════════════════════
    #
    # 为什么必须这么做：骨骼网格（机体 + 6 种敌人）在 UE 里拿不到 UV ——
    # 同一个 FBX 以**静态网格**导入 UV 通道 = 1，以**骨骼网格**导入则
    # 贴图完全不显示（换成 16×16 棋盘图也一样，说明不是对比度问题）。
    # 重导、改 LOD 顺序、换渲染组件（-ShowSource）、查材质槽，全部无效。
    #
    # `MaterialExpressionWorldAlignedTexture` **没有暴露给 Python**
    # （AttributeError: module 'unreal' has no attribute ...），
    # 所以这里用基础节点手搭：
    #     UV = worldPos / TextureSize，按法线主轴取三个投影面，
    #     用 |n|^4 加权混合（指数越大投影越"硬"，面与面过渡越干净）。
    #
    # 附带好处：和网格 UV 彻底解耦，程序化生成的模型再也不会踩这个坑，
    # 也不用担心 LOD 的 UV 和 LOD0 不一致。
    vn_ws = ex(unreal.MaterialExpressionVertexNormalWS, -2700, -700)
    # 指数越大，三个投影面的过渡带越窄 —— 4 在曲面（胸腔/肩甲）上会把
    # 板缝糊成一片软阴影，8 才能保住缝的锐度。
    c_exp = cst(8.0, -2700, -560)

    def tri_mask(src, ax, x, y):
        m = ex(unreal.MaterialExpressionComponentMask, x, y)
        m.set_editor_property("r", ax == "x")
        m.set_editor_property("g", ax == "y")
        m.set_editor_property("b", ax == "z")
        m.set_editor_property("a", False)
        link(src, m, "")
        return m

    def tri_append(a, b, x, y):
        nd = ex(unreal.MaterialExpressionAppendVector, x, y)
        link(a, nd, "A")
        link(b, nd, "B")
        return nd

    def tri_mul(src, w, x, y):
        nd = ex(unreal.MaterialExpressionMultiply, x, y)
        link(src[0], nd, "A", src[1])
        link(w, nd, "B")
        return (nd, "")

    def tri_add(a, b, x, y):
        nd = ex(unreal.MaterialExpressionAdd, x, y)
        link(a[0], nd, "A", a[1])
        link(b[0], nd, "B", b[1])
        return (nd, "")

    # p = worldPos / TextureSize(cm)
    dv = ex(unreal.MaterialExpressionDivide, -2550, -1050)
    link(p_wpos, dv, "A")
    link(p_scale, dv, "B")
    px_ = tri_mask(dv, "x", -2420, -1140)
    py_ = tri_mask(dv, "y", -2420, -1050)
    pz_ = tri_mask(dv, "z", -2420, -960)
    uv_x = tri_append(py_, pz_, -2290, -1140)      # 法线朝 X → 投影到 YZ
    uv_y = tri_append(px_, pz_, -2290, -1050)      # 朝 Y → XZ
    uv_z = tri_append(px_, py_, -2290, -960)       # 朝 Z → XY

    def tri_sample(uv, x, y):
        sm = ex(unreal.MaterialExpressionTextureSampleParameter2D, x, y)
        sm.set_editor_property("parameter_name", "DetailTex")
        link(uv, sm, "UVs")
        return sm

    s_x = tri_sample(uv_x, -2150, -1150)
    s_y = tri_sample(uv_y, -2150, -1050)
    s_z = tri_sample(uv_z, -2150, -950)

    # 权重 |n|^4
    ab = ex(unreal.MaterialExpressionAbs, -2550, -700)
    link(vn_ws, ab, "")
    pw = ex(unreal.MaterialExpressionPower, -2420, -700)
    link(ab, pw, "Base")
    link(c_exp, pw, "Exp")
    w_x = tri_mask(pw, "x", -2280, -760)
    w_y = tri_mask(pw, "y", -2280, -700)
    w_z = tri_mask(pw, "z", -2280, -640)
    w_sum = tri_add(tri_add((w_x, ""), (w_y, ""), -2140, -740),
                    (w_z, ""), -2000, -720)

    def tri_blend(ch, x, y):
        """三个投影面的同一通道按权重混合，再除以权重和。"""
        vals = []
        for i, sm in enumerate((s_x, s_y, s_z)):
            if ch == "A":
                vals.append((sm, "A"))       # A 输出本身就是标量，不用 Mask
            else:
                m = ex(unreal.MaterialExpressionComponentMask, x, y + i * 120)
                m.set_editor_property("r", ch == "R")
                m.set_editor_property("g", ch == "G")
                m.set_editor_property("b", ch == "B")
                m.set_editor_property("a", False)
                link(sm, m, "")
                vals.append((m, ""))
        t1 = tri_mul(vals[0], w_x, x + 150, y)
        t2 = tri_mul(vals[1], w_y, x + 150, y + 60)
        t3 = tri_mul(vals[2], w_z, x + 150, y + 120)
        tot = tri_add(tri_add(t1, t2, x + 300, y + 20), t3, x + 440, y + 40)
        fin = ex(unreal.MaterialExpressionDivide, x + 580, y + 20)
        link(tot[0], fin, "A", tot[1])
        link(w_sum[0], fin, "B", w_sum[1])
        return fin

    tri_r = tri_blend("R", -1800, -1150)
    tri_a = tri_blend("A", -1800, -600)

    # 粗糙度 / 磨损是低频信息，单投影就够（省 12 个节点）
    m_rgh_z = ex(unreal.MaterialExpressionComponentMask, -1800, -260)
    m_rgh_z.set_editor_property("r", False)
    m_rgh_z.set_editor_property("g", True)
    m_rgh_z.set_editor_property("b", False)
    m_rgh_z.set_editor_property("a", False)
    link(s_z, m_rgh_z, "")
    m_wear_z = ex(unreal.MaterialExpressionComponentMask, -1800, -160)
    m_wear_z.set_editor_property("r", False)
    m_wear_z.set_editor_property("g", False)
    m_wear_z.set_editor_property("b", True)
    m_wear_z.set_editor_property("a", False)
    link(s_z, m_wear_z, "")

    fc, out_xyz = tri_r, ""
    # 法线：骨骼网格没有 UV，法线贴图同样采不到 → 直接不接（默认平面法线）。
    # 装甲的倒角高光已经烘进了 R 通道（倒角处 *1.16），不依赖法线也能读出来。
    fc_n, out_n = None, ""

    # ── 拆通道：R=板面亮度  G=粗糙度  B=磨损  A=高度 ──
    #
    # ★ 2026-10-24 修正：R 的语义从"板缝遮罩"改成"板面亮度"。
    #
    #   之前 R 被当成缝遮罩用：seamTint = lerp(SeamDarken, 1, R)。
    #   但纹理侧（tools/make_armor_texture.py / make_surface_set.py）里
    #   R 装的是**每块装甲板的色差**（0.70~1.00）。两套语义撞在一个通道上，
    #   结果是：
    #     · 每块板的色差被压成"0.7 → 缝更黑一点"，几乎看不见
    #     · 凹槽的深度完全没被用上（A 通道被丢在一边）
    #   于是画面里所有板都是同一块平板 —— 这就是"不像装甲"的第三个原因。
    #
    #   现在的分工：
    #     R → 乘到 BaseColor（板面色差 + 倒角高光）
    #     A → 高度，用来算**凹槽遮蔽**（凹槽暗、倒角亮、板面中性）
    #        同时也喂给法线贴图侧的 NormalStrength
    def mask_node(src, out, r, g, b, a, x, y):
        m = ex(unreal.MaterialExpressionComponentMask, x, y)
        m.set_editor_property("r", r)
        m.set_editor_property("g", g)
        m.set_editor_property("b", b)
        m.set_editor_property("a", a)
        link(src, m, "", out)
        return m

    m_bright = tri_r          # R：板面亮度（已做三平面混合）
    m_rgh = m_rgh_z           # G：粗糙度（单投影够用）
    m_wear = m_wear_z         # B：磨损（同上）
    # A = 高度（凹槽/倒角）。
    #
    # ⚠️⚠️ 这里**不能用 ComponentMask 取 A**。
    #
    #   `mask_node(..., a=True)` 接到的是 TextureSample 的默认输出（RGB，float3），
    #   取 A 会直接让整张材质编译失败：
    #     "(Node ComponentMask) Not enough components in (Local7.rgb: float3)
    #      for component mask 0001"
    #   而 UE 对编译失败的材质是**静默降级**成 DefaultMaterial ——
    #   运行时只在日志留一行 "Failed to compile Material ... Default Material
    #   will be used in game"，画面上表现为：所有用这个材质的网格变成一块纯灰，
    #   没有贴图、没有识别色、没有目镜发光。我一度以为是 UV / 贴图 / 灯光问题。
    #
    #   正确做法：把采样节点的 "A" 输出**直接**连到 lerp 的 Alpha，
    #   完全绕开 ComponentMask。同一个 A 输出可以连多个下游。
    m_height = None          # 占位：A 通道直接用 fc 的 "A" 输出

    # DetailAmount 统一缩放"细节强度"（自发光件可以调到 0）
    one = cst(1.0, -1900, -1200)

    # 板面亮度 remap：lerp(1, R, DetailAmount) —— 1 是"不改变"
    tone_amt = ex(unreal.MaterialExpressionLinearInterpolate, -1550, -1120)
    link(one, tone_amt, "A")
    link(m_bright, tone_amt, "B")
    link(p_damt, tone_amt, "Alpha")

    # 凹槽遮蔽：lerp(SeamDarken, 1, height)
    #   高度 1.0（板面）→ 1.0（不暗）
    #   高度 0.70（倒角）→ 略暗
    #   高度 0.16（槽底）→ 压到 SeamDarken 附近
    # ── 高度 → 硬边遮罩 ──
    #
    # 直接 lerp(SeamDarken, 1, h) 在槽底只压到约 50%（h=0.06 时），
    # 看起来是一条"软阴影"，不是刻线。
    # 这里做一次对比拉伸：clamp((h - 0.30) / 0.25)
    #     h = 0.06（槽底）→ 0（全暗）
    #     h = 0.58（倒角）→ 1（全亮）
    # 过渡带只占高度区间的 0.25，所以凹槽是**一条硬边暗线**。
    # 不用 SmoothStep 是因为它的引脚名跨版本不稳定，Clamp 是稳的。
    h_off = ex(unreal.MaterialExpressionSubtract, -1600, -820)
    link(tri_a, h_off, "A")
    link(cst(0.30, -1750, -880), h_off, "B")
    h_div = ex(unreal.MaterialExpressionDivide, -1450, -820)
    link(h_off, h_div, "A")
    link(cst(0.25, -1600, -740), h_div, "B")
    h_sharp = ex(unreal.MaterialExpressionClamp, -1300, -820)
    link(h_div, h_sharp, "")

    cav = ex(unreal.MaterialExpressionLinearInterpolate, -1300, -1120)
    link(p_seam, cav, "A")
    link(one, cav, "B")
    link(h_sharp, cav, "Alpha")     # ← 提亮后的高度（缝更锐）

    # ── BaseColor ──
    # VColor 也要能被关掉：lerp(1, vcol, VertexColorAmount)
    vc_amt = ex(unreal.MaterialExpressionLinearInterpolate, -2350, 1100)
    link(one, vc_amt, "A")
    link(vcol, vc_amt, "B")
    link(p_vcol, vc_amt, "Alpha")

    bc1 = ex(unreal.MaterialExpressionMultiply, -1050, -1150)
    link(p_base, bc1, "A")
    link(vc_amt, bc1, "B")
    bc2 = ex(unreal.MaterialExpressionMultiply, -900, -1150)
    link(bc1, bc2, "A")
    link(tone_amt, bc2, "B")
    # 凹槽压暗：AO 只影响间接光，直接光下槽还是亮的，
    # 所以 BaseColor 上也要乘一次（真实凹槽在直射光下本来也是暗的 —— 侧壁挡光）。
    bc2c = ex(unreal.MaterialExpressionMultiply, -780, -1150)
    link(bc2, bc2c, "A")
    link(cav, bc2c, "B")

    # 磨损：把刮痕处朝 WearTint 拉
    wear_amt = ex(unreal.MaterialExpressionMultiply, -1300, -800)
    link(m_wear, wear_amt, "A")
    link(p_wear, wear_amt, "B")
    wear_cl = ex(unreal.MaterialExpressionClamp, -1150, -800)
    link(wear_amt, wear_cl, "")
    bc3 = ex(unreal.MaterialExpressionLinearInterpolate, -700, -1150)
    link(bc2c, bc3, "A")
    link(p_wtint, bc3, "B")
    link(wear_cl, bc3, "Alpha")
    prop(bc3, unreal.MaterialProperty.MP_BASE_COLOR)

    # ── Roughness ──
    rd = ex(unreal.MaterialExpressionMultiply, -1050, -950)
    link(m_rgh, rd, "A")
    link(p_rdet, rd, "B")
    radd = ex(unreal.MaterialExpressionAdd, -900, -950)
    link(p_rough, radd, "A")
    link(rd, radd, "B")
    rcl = ex(unreal.MaterialExpressionClamp, -750, -950)
    link(radd, rcl, "")
    prop(rcl, unreal.MaterialProperty.MP_ROUGHNESS)

    # ── Metallic ──
    prop(p_metal, unreal.MaterialProperty.MP_METALLIC)

    # ── AO（凹槽遮蔽，直接来自高度）──
    ao = ex(unreal.MaterialExpressionLinearInterpolate, -700, -700)
    link(p_ao, ao, "A")
    link(one, ao, "B")
    link(h_sharp, ao, "Alpha")      # ← 同上
    prop(ao, unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)

    # ── 自发光 ──
    em = ex(unreal.MaterialExpressionMultiply, -700, -500)
    link(p_emiss, em, "A")
    link(p_epow, em, "B")
    prop(em, unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    # ── 法线 ──
    if fc_n is not None and out_n:
        # NormalStrength：把法线朝 (0,0,1) 插值
        flat = ex(unreal.MaterialExpressionConstant3Vector, -1050, -300)
        flat.set_editor_property("constant",
                                 unreal.LinearColor(0.0, 0.0, 1.0, 1.0))
        nlerp = ex(unreal.MaterialExpressionLinearInterpolate, -800, -320)
        link(flat, nlerp, "A")
        link(fc_n, nlerp, "B", out_n)
        link(p_nstr, nlerp, "Alpha")
        prop(nlerp, unreal.MaterialProperty.MP_NORMAL)

    try:
        mel.layout_material_expressions(mat)
    except Exception:
        pass
    try:
        mel.recompile_material(mat)
        log("  主材质编译完成")
    except Exception as e:
        log("  ⚠️ 编译报错: %s" % str(e)[:150])

    log("  共建立 %d 条连接" % conn[0])
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


# ─────────────────────────────────────────────
# 换装
# ─────────────────────────────────────────────

def main():
    import_tex("mech_detail.png", "T_MechDetail", False)
    import_tex("mech_detail_n.png", "T_MechDetail_N", True)
    import_tex("env_detail.png", "T_EnvDetail", False)
    import_tex("env_detail_n.png", "T_EnvDetail_N", True)

    master = build_master()
    if not master:
        return

    tex_cache = {}

    # ── 按材质类型分配纹理 ──
    #
    # 之前所有环境材质共用 T_EnvDetail —— 地面、墙、立柱、集装箱全是
    # 同一张"壁纸"，近看就露馅。现在按材质名分：
    #   地面/基座（M_Steel）      → 混凝土（细密分格 + 粗颗粒）
    #   结构件（M_SteelLight）    → 涂装钢板（少缝、板面平、有掉漆）
    #   关节/连接（M_Joint/Copper/Rust）→ 锈蚀（斑驳锈斑 + 起皮）
    #   识别色/发光件             → 涂装（发光件的 DetailAmount=0，纹理不参与）
    MAT_TEX = {
        "M_Steel":      ("T_ConcreteDetail", "T_ConcreteDetail_N"),
        "M_SteelLight": ("T_PaintDetail", "T_PaintDetail_N"),
        "M_Joint":      ("T_RustDetail", "T_RustDetail_N"),
        "M_Copper":     ("T_RustDetail", "T_RustDetail_N"),
        "M_Rust":       ("T_RustDetail", "T_RustDetail_N"),
        "M_AccentDark": ("T_PaintDetail", "T_PaintDetail_N"),
        "M_Accent":     ("T_PaintDetail", "T_PaintDetail_N"),
        "M_Core":       ("T_PaintDetail", "T_PaintDetail_N"),
    }

    def resolve_tex(folder, matname):
        if folder == "Characters":
            return ("T_MechDetail", "T_MechDetail_N")
        # 长名优先：M_AccentDark 不能被 M_Accent 抢先匹配
        for k in sorted(MAT_TEX, key=len, reverse=True):
            if matname.startswith(k):
                return MAT_TEX[k]
        return DETAIL_TEX.get(folder, DETAIL_TEX["Characters"])

    def get_tex(folder, matname=""):
        key = (folder, matname)
        if key not in tex_cache:
            dn, nn = resolve_tex(folder, matname)
            tex_cache[key] = (
                unreal.EditorAssetLibrary.load_asset("%s/%s" % (MAT_DIR, dn)),
                unreal.EditorAssetLibrary.load_asset("%s/%s" % (MAT_DIR, nn)))
        return tex_cache[key]

    mel = unreal.MaterialEditingLibrary
    ar = unreal.AssetRegistryHelpers.get_asset_registry()

    n_done = n_skip = 0
    for folder in DETAIL_SCALE:
        root = "%s/%s" % (ART, folder)
        for ad in ar.get_assets_by_path(root, recursive=True):
            if str(ad.asset_class_path.asset_name) != "MaterialInstanceConstant":
                continue
            nm = str(ad.asset_name)
            mic = ad.get_asset()
            if not mic:
                continue

            # ── 先把原配色读出来 ──
            base = (0.5, 0.5, 0.5)
            emiss = (0.0, 0.0, 0.0)
            for it in mic.get_editor_property("vector_parameter_values"):
                try:
                    pname = it.get_editor_property(
                        "parameter_info").get_editor_property("name")
                    val = it.get_editor_property("parameter_value")
                except Exception:
                    continue
                if pname == "DiffuseColor":
                    base = (val.r, val.g, val.b)
                elif pname == "EmissiveColor":
                    emiss = (val.r, val.g, val.b)

            metal, rough, is_emissive = metal_of(nm)

            # 自发光件兜底：FBX 的 Emission 不一定导得过来，
            # 拿不到就用 Blender 侧 glow 色（见 tools/blender/robotlib.py Palette）。
            if is_emissive and max(emiss) < 0.02:
                if nm.endswith("_light") or "light" in nm:
                    emiss = (0.30, 0.95, 0.82)
                elif nm.endswith("_heavy") or "heavy" in nm:
                    emiss = (0.52, 0.45, 0.92)
                elif "module" in nm:
                    emiss = (0.52, 0.45, 0.92)
                else:
                    emiss = (1.00, 0.68, 0.26)

            bmul, mmul, bcap = FOLDER_ADJUST[folder]
            forced = forced_color(folder, nm)
            if forced is not None:
                # 指定配色不再走 lift（数值已经是最终值）
                base = forced
            else:
                base = lift_color(base, bmul, bcap)
            metal = min(max(metal * mmul, 0.0), 1.0)

            try:
                mic.set_editor_property("parent", master)
            except Exception as e:
                log("❌ %s 换父类失败: %s" % (nm, str(e)[:70]))
                n_skip += 1
                continue

            def sv(k, v):
                mel.set_material_instance_scalar_parameter_value(mic, k, float(v))

            def vv(k, c):
                mel.set_material_instance_vector_parameter_value(
                    mic, k, unreal.LinearColor(c[0], c[1], c[2], 1.0))

            vv("BaseTint", base)
            vv("EmissiveTint", emiss)
            # ★ 2026-10-24：6.0 太高。Lumen GI 开启时，这些自发光条会
            #   把整个场地当光源照亮 —— 场地的"暖粉色"很大一部分来自它们，
            #   而不是来自太阳（太阳实测是 9000lux 冷白，改了没反应）。
            #   降到 2.2 仍然够亮（肉眼是发光条），但不再主导全局照明。
            sv("EmissivePower", 2.2 if is_emissive else 0.0)
            sv("Metallic", metal)
            sv("Roughness", rough)
            sv("TextureSize", DETAIL_SCALE[folder])
            # 自发光件不要面板缝（会破坏"发光条"的观感）
            sv("DetailAmount", 0.0 if is_emissive else 1.0)
            # ⚠️ 0.46 会把板缝压成纯黑，机体表面看起来像"贴了网格纸"。
            #    真实装甲的板缝是**阴影**，不是黑线 —— 0.16 刚好。
            # 0.42 = 槽底相对亮度。低于 0.3 会让槽变成纯黑细线（像网格纸）。
            sv("SeamDarken", 0.30)
            sv("RoughDetail", 0.34)
            sv("WearAmount", 0.38 if folder == "Environment" else 0.5)
            # ⚠️ 磨损色必须**相对基色**算，不能写死 base*0.5+0.45。
            #    写死的话，深色表面（0.10）的磨损色是 0.50 —— 亮 5 倍；
            #    而 env_detail 的磨损通道本来就大面积偏亮（B 通道均值 0.89），
            #    于是整块地板被"磨损"洗成浅灰白，改基色完全没反应
            #    （实测：把环境钢从 0.15 调到 0.105，画面亮度一点没变）。
            vv("WearTint", (min(base[0] * 1.45 + 0.015, 1.0),
                            min(base[1] * 1.45 + 0.015, 1.0),
                            min(base[2] * 1.45 + 0.015, 1.0)))
            sv("NormalStrength", 1.6)
            sv("VertexColorAmount", 1.0)
            sv("SeamAO", 0.60)

            td, tn = get_tex(folder, nm)
            try:
                mel.set_material_instance_texture_parameter_value(
                    mic, "DetailTex", td)
                if tn:
                    mel.set_material_instance_texture_parameter_value(
                        mic, "NormalTex", tn)
            except Exception as e:
                log("  贴图参数设置失败 %s: %s" % (nm, str(e)[:60]))

            unreal.EditorAssetLibrary.save_loaded_asset(mic)
            n_done += 1
            log("  %-30s base=(%.3f,%.3f,%.3f) M=%.2f R=%.2f%s"
                % (nm, base[0], base[1], base[2], metal, rough,
                   " 自发光" if is_emissive else ""))

    log("完成：换装 %d 个材质实例，失败 %d 个" % (n_done, n_skip))


main()
