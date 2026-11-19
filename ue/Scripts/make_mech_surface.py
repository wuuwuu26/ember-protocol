# -*- coding: utf-8 -*-
"""
机体表面材质：把程序化细节贴图接到机体上。
================================================================

目标（用户要求："机器人建模可以加上表面纹理，更精细"）：
    机体原本是"一块均色的深灰金属"，没有任何表面层次。这里加三层细节：

    ① 顶点色       —— 相邻装甲板之间的细微明暗差（Blender 侧写进顶点色，
                      UE 里就是 VertexColor 节点）。已经存在于资产里。
    ② 三平面细节贴图 —— 面板缝 / 铆钉 / 油污 / 刮痕。**不能用 UV 采样**：
                      这批资产是 Smart UV 自动展开的，方向随机，贴上去会撕裂。
                      改用引擎自带的 WorldAlignedTexture 材质函数做三平面投影，
                      完全不依赖 UV。
    ③ 磨损露底      —— 刮痕处粗糙度下降、颜色变亮，模拟"漆面磨掉露出金属"。

⚠️ 设计要点：所有"能不能连上"都靠**运行时枚举引脚名**判断，不写死。
   MaterialFunctionCall 的输入/输出引脚是跟着材质函数资源走的，
   版本之间名字会变；写死一个名字，连不上时 UE 只会静默忽略，
   最后拿到一个"看起来建好了、其实是空的"材质 —— 最难查的那种坑。
   所以这里每一步都打印结果，最后打印材质编译是否成功。

用法（编辑器命令行）：
    UnrealEditor-Cmd.exe <项目> -ExecutePythonScript="<本文件>"
"""

import os

import unreal

PROJ = r"C:\Users\25227\Documents\robot_game"
TEX_DIR = os.path.join(PROJ, "assets", "tex")
MAT_DIR = "/Game/RobotGame/Art/Materials"
MAT_PATH = MAT_DIR + "/M_MechSurface"
WAF_PATH = ("/Engine/Functions/Engine_MaterialFunctions01/"
            "/Texturing/WorldAlignedTexture")

# 调色板：与 tools/blender/robotlib.py 的 Palette 保持一致。
# (名称, BaseColor(线性), Metallic, Roughness, 是否自发光, 自发光色)
# 只列需要"金属细节"的；自发光件（M_Core_*/M_Visor_*）不套细节材质。
PALETTE = [
    ("M_Steel",        (0.082, 0.092, 0.108), 0.88, 0.46),
    ("M_SteelLight",   (0.145, 0.158, 0.176), 0.86, 0.40),
    ("M_Joint",        (0.030, 0.033, 0.040), 0.50, 0.72),
    ("M_Rubber",       (0.022, 0.024, 0.028), 0.10, 0.88),
    ("M_Copper",       (0.340, 0.200, 0.100), 0.95, 0.34),
    ("M_Rust",         (0.115, 0.062, 0.038), 0.55, 0.82),
]


def L(s):
    unreal.log("[机体表面] %s" % s)
    print("[机体表面] %s" % s)


def try_set(obj, attr, value):
    try:
        setattr(obj, attr, value)
        return True
    except Exception as e:
        L("    setattr(%s) 失败: %s" % (attr, str(e)[:70]))
        return False


def norm(s):
    """把引脚名归一化，方便模糊匹配。"""
    return "".join(ch for ch in str(s).lower() if ch.isalnum())


# ─────────────────────────────────────────────
# 贴图
# ─────────────────────────────────────────────

def import_texture(fname, name, normal_map):
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    path = os.path.join(TEX_DIR, fname)
    if not os.path.exists(path):
        L("❌ 找不到 %s" % path)
        return None
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
        L("❌ 导入 %s 失败: %s" % (fname, e))
        return None

    tex = unreal.EditorAssetLibrary.load_asset("%s/%s" % (MAT_DIR, name))
    if not tex:
        L("❌ 导入后读不到 %s" % name)
        return None

    try_set(tex, "srgb", False)          # 数据贴图不能走 sRGB 解码
    if normal_map:
        try_set(tex, "compression_settings",
                unreal.TextureCompressionSettings.TC_NORMALMAP)
    else:
        try_set(tex, "compression_settings",
                unreal.TextureCompressionSettings.TC_MASKS)
    try_set(tex, "mip_gen_settings",
            unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
    try:
        unreal.EditorAssetLibrary.save_loaded_asset(tex)
    except Exception:
        pass
    L("  贴图就绪 %s (%dx%d)" % (name, tex.blueprint_get_size_x(),
                                 tex.blueprint_get_size_y()))
    return tex


# ─────────────────────────────────────────────
# 材质图
# ─────────────────────────────────────────────

def build_material(detail, detail_n):
    mel = unreal.MaterialEditingLibrary
    at = unreal.AssetToolsHelpers.get_asset_tools()

    if unreal.EditorAssetLibrary.does_asset_exist(MAT_PATH):
        unreal.EditorAssetLibrary.delete_asset(MAT_PATH)

    mat = at.create_asset("M_MechSurface", MAT_DIR,
                          unreal.Material, unreal.MaterialFactoryNew())
    if not mat:
        L("❌ 材质创建失败")
        return None
    L("材质已创建 %s" % mat.get_name())

    def vec_param(name, color, x, y):
        e = mel.create_material_expression(
            mat, unreal.MaterialExpressionVectorParameter, x, y)
        try_set(e, "parameter_name", name)
        try_set(e, "default_value", unreal.LinearColor(
            color[0], color[1], color[2], 1.0))
        return e

    def scalar_param(name, val, x, y):
        e = mel.create_material_expression(
            mat, unreal.MaterialExpressionScalarParameter, x, y)
        try_set(e, "parameter_name", name)
        try_set(e, "default_value", float(val))
        return e

    def expr(cls, x, y):
        return mel.create_material_expression(mat, cls, x, y)

    # ── 参数 ──
    p_tint = vec_param("BaseTint", (0.082, 0.092, 0.108), -2100, -600)
    p_wear_col = vec_param("WearTint", (0.62, 0.58, 0.54), -2100, -450)
    p_metal = scalar_param("Metallic", 0.88, -2100, -250)
    p_rough = scalar_param("Roughness", 0.46, -2100, -150)
    p_scale = scalar_param("DetailScale", 0.0035, -2100, -50)
    p_seam = scalar_param("SeamDarken", 0.30, -2100, 50)
    p_wear = scalar_param("WearAmount", 0.55, -2100, 150)
    p_rough_lo = scalar_param("RoughDetail", 0.28, -2100, 250)

    # 顶点色：相邻装甲板的明暗差
    vcol = expr(unreal.MaterialExpressionVertexColor, -2100, 380)

    # ── 三平面采样 ──
    waf = unreal.EditorAssetLibrary.load_asset(WAF_PATH)
    if not waf:
        L("⚠️ 找不到材质函数 %s —— 退化为「顶点色 + 纯色」" % WAF_PATH)
        fc = None
    else:
        fc = expr(unreal.MaterialExpressionMaterialFunctionCall, -1500, 0)
        ok = False
        try:
            ok = fc.set_material_function(waf)
        except Exception as e:
            L("  set_material_function 失败: %s" % str(e)[:90])
        L("  材质函数 %s → %s" % (waf.get_name(), "挂上" if ok else "挂载失败"))
        if not ok:
            fc = None

    if fc is None:
        # 退化路径：只做顶点色 × 基色，至少保证材质是"能用的"
        mul = expr(unreal.MaterialExpressionMultiply, -900, -300)
        mel.connect_material_expressions(p_tint, "", mul, "A")
        mel.connect_material_expressions(vcol, "", mul, "B")
        mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_BASE_COLOR)
        mel.connect_material_property(p_metal, "", unreal.MaterialProperty.MP_METALLIC)
        mel.connect_material_property(p_rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
        mel.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat)
        return mat

    # ── 枚举引脚，按名字模糊匹配（不写死） ──
    fin, fout = [], []
    try:
        fin = [str(p.get_editor_property("input_name"))
               for p in fc.get_editor_property("function_inputs")]
    except Exception as e:
        L("  读 function_inputs 失败: %s" % str(e)[:70])
    try:
        fout = [str(p.get_editor_property("output_name"))
                for p in fc.get_editor_property("function_outputs")]
    except Exception as e:
        L("  读 function_outputs 失败: %s" % str(e)[:70])
    L("  输入引脚: %s" % fin)
    L("  输出引脚: %s" % fout)

    def pick(names, *cands):
        for c in cands:
            nc = norm(c)
            for n in names:
                if norm(n) == nc:
                    return n
        for c in cands:
            nc = norm(c)
            for n in names:
                if nc and nc in norm(n):
                    return n
        return None

    # 贴图对象参数
    t_obj = expr(unreal.MaterialExpressionTextureObjectParameter, -1800, 0)
    try_set(t_obj, "parameter_name", "DetailTex")
    try_set(t_obj, "texture", detail)

    # 法线贴图（可选，失败不影响其它通道）
    t_nrm = None
    if detail_n:
        t_nrm = expr(unreal.MaterialExpressionTextureObjectParameter, -1800, 300)
        try_set(t_nrm, "parameter_name", "NormalTex")
        try_set(t_nrm, "texture", detail_n)

    conn = 0

    def connect(src, dst, dst_input, src_out=""):
        nonlocal conn
        try:
            mel.connect_material_expressions(src, src_out, dst, dst_input)
            conn += 1
            return True
        except Exception as e:
            L("    连接 %s 失败: %s" % (dst_input, str(e)[:70]))
            return False

    pin_tex = pick(fin, "TextureObject", "Texture", "Tex")
    pin_scale = pick(fin, "WorldPositionScale", "PositionScale", "Scale")
    pin_nrm = pick(fin, "Normal", "NormalWS", "VertexNormal")
    pin_size = pick(fin, "TextureSize", "Size")

    if pin_tex:
        connect(t_obj, fc, pin_tex)
    else:
        L("  ⚠️ 找不到 TextureObject 输入引脚")
    if pin_scale:
        connect(p_scale, fc, pin_scale)
    if pin_nrm and t_nrm:
        pass  # Normal 引脚要的是法线向量，不是贴图，见下面单独处理

    out_xyz = pick(fout, "XYZ", "RGB", "Out", "Result")
    out_xy = pick(fout, "XY")
    out_xz = pick(fout, "XZ")
    out_yz = pick(fout, "YZ")
    L("  选用输出：XYZ=%s XY=%s XZ=%s YZ=%s" % (out_xyz, out_xy, out_xz, out_yz))

    if not out_xyz:
        L("  ⚠️ 没有合并输出，退化：只用 XZ 投影")
        out_xyz = out_xz or out_xy or out_yz
    if not out_xyz:
        L("  ❌ 一个可用输出都没有 —— 退化材质")
        mul = expr(unreal.MaterialExpressionMultiply, -900, -300)
        mel.connect_material_expressions(p_tint, "", mul, "A")
        mel.connect_material_expressions(vcol, "", mul, "B")
        mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_BASE_COLOR)
        mel.connect_material_property(p_metal, "", unreal.MaterialProperty.MP_METALLIC)
        mel.connect_material_property(p_rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
        mel.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat)
        return mat

    # ── 拆通道 ──
    # 约定（见 tools/make_detail_texture.py）：
    #   R = 面板缝遮罩(1=板面)  G = 粗糙度扰动  A = 磨损露底
    def mask(src, r, g, b, x, y):
        m = expr(unreal.MaterialExpressionComponentMask, x, y)
        try_set(m, "r", r)
        try_set(m, "g", g)
        try_set(m, "b", b)
        try_set(m, "a", False)
        mel.connect_material_expressions(src, out_xyz, m, "")
        return m

    m_mask = mask(fc, True, False, False, -1100, -200)     # R
    m_rough = mask(fc, False, True, False, -1100, 0)       # G
    m_wear = mask(fc, False, False, False, -1100, 200)     # A
    try_set(m_wear, "r", False)
    try_set(m_wear, "g", False)
    try_set(m_wear, "b", False)
    try_set(m_wear, "a", True)

    # 缝里压暗：lerp(SeamDarken, 1, mask)
    seam_lerp = expr(unreal.MaterialExpressionLinearInterpolate, -900, -300)
    connect(p_seam, seam_lerp, "A")
    c_one = expr(unreal.MaterialExpressionConstant, -1100, -420)
    try_set(c_one, "r", 1.0)
    connect(c_one, seam_lerp, "B")
    connect(m_mask, seam_lerp, "Alpha")

    # BaseColor = BaseTint * VertexColor * seamLerp
    mul1 = expr(unreal.MaterialExpressionMultiply, -650, -400)
    connect(p_tint, mul1, "A")
    connect(vcol, mul1, "B")
    mul2 = expr(unreal.MaterialExpressionMultiply, -450, -350)
    connect(mul1, mul2, "A")
    connect(seam_lerp, mul2, "B")

    # 磨损：把刮痕处朝 WearTint 拉
    wear_amt = expr(unreal.MaterialExpressionMultiply, -900, 250)
    connect(m_wear, wear_amt, "A")
    connect(p_wear, wear_amt, "B")
    wear_clamp = expr(unreal.MaterialExpressionClamp, -750, 250)
    connect(wear_amt, wear_clamp, "")
    base_lerp = expr(unreal.MaterialExpressionLinearInterpolate, -250, -300)
    connect(mul2, base_lerp, "A")
    connect(p_wear_col, base_lerp, "B")
    connect(wear_clamp, base_lerp, "Alpha")
    mel.connect_material_property(base_lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)

    # Roughness = Roughness + G * RoughDetail（油污/缝底更粗糙）
    rd = expr(unreal.MaterialExpressionMultiply, -700, 100)
    connect(m_rough, rd, "A")
    connect(p_rough_lo, rd, "B")
    radd = expr(unreal.MaterialExpressionAdd, -500, 60)
    connect(p_rough, radd, "A")
    connect(rd, radd, "B")
    rclamp = expr(unreal.MaterialExpressionClamp, -350, 60)
    connect(radd, rclamp, "")
    mel.connect_material_property(rclamp, "", unreal.MaterialProperty.MP_ROUGHNESS)

    # Metallic：磨损处略降（露出的底材没那么"抛光"）
    met_sub = expr(unreal.MaterialExpressionSubtract, -350, 220)
    connect(p_metal, met_sub, "A")
    connect(wear_clamp, met_sub, "B")

    # AO：缝里稍暗，增加凹陷感
    ao_lerp = expr(unreal.MaterialExpressionLinearInterpolate, -500, 420)
    c_ao = expr(unreal.MaterialExpressionConstant, -700, 520)
    try_set(c_ao, "r", 0.55)
    connect(c_ao, ao_lerp, "A")
    connect(c_one, ao_lerp, "B")
    connect(m_mask, ao_lerp, "Alpha")
    mel.connect_material_property(ao_lerp, "", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)

    mel.connect_material_property(met_sub, "", unreal.MaterialProperty.MP_METALLIC)

    # ── 法线（可选） ──
    if detail_n and out_xyz:
        try:
            nfc = expr(unreal.MaterialExpressionMaterialFunctionCall, -1500, 700)
            nfc.set_material_function(waf)
            nfin = [str(p.get_editor_property("input_name"))
                    for p in nfc.get_editor_property("function_inputs")]
            nfout = [str(p.get_editor_property("output_name"))
                     for p in nfc.get_editor_property("function_outputs")]
            pn_tex = pick(nfin, "TextureObject", "Texture", "Tex")
            pn_scale = pick(nfin, "WorldPositionScale", "PositionScale", "Scale")
            on_xyz = pick(nfout, "XYZ", "RGB", "Out", "Result") or \
                pick(nfout, "XZ") or pick(nfout, "XY")
            if pn_tex and on_xyz:
                connect(t_nrm, nfc, pn_tex)
                if pn_scale:
                    connect(p_scale, nfc, pn_scale)
                mel.connect_material_property(nfc, on_xyz,
                                              unreal.MaterialProperty.MP_NORMAL)
                L("  法线已接上（输出 %s）" % on_xyz)
            else:
                L("  ⚠️ 法线分支引脚缺失，跳过（不影响其它通道）")
        except Exception as e:
            L("  ⚠️ 法线分支失败：%s" % str(e)[:90])

    try:
        mel.layout_material_expressions(mat)
    except Exception:
        pass
    try:
        mel.recompile_material(mat)
        L("材质编译完成")
    except Exception as e:
        L("⚠️ 编译报错：%s" % str(e)[:120])

    L("共建立 %d 条连接" % conn)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


# ─────────────────────────────────────────────
# 材质实例 + 应用
# ─────────────────────────────────────────────

def make_mic(master, name, color, metallic, roughness):
    path = "%s/%s" % (MAT_DIR, name)
    at = unreal.AssetToolsHelpers.get_asset_tools()
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mic = unreal.EditorAssetLibrary.load_asset(path)
    else:
        mic = at.create_asset(name, MAT_DIR, unreal.MaterialInstanceConstant,
                              unreal.MaterialInstanceConstantFactoryNew())
    if not mic:
        L("  ❌ 实例 %s 创建失败" % name)
        return None
    try:
        mic.set_editor_property("parent", master)
    except Exception as e:
        L("  ❌ 实例 %s 设父类失败: %s" % (name, str(e)[:60]))
        return None
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        mic, "BaseTint", unreal.LinearColor(color[0], color[1], color[2], 1.0))
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        mic, "Metallic", metallic)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        mic, "Roughness", roughness)
    # 细节尺度：小件（关节/铜件）用更密的网格，大板件用更疏的
    scale = 0.0035 if max(color) < 0.2 else 0.0060
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        mic, "DetailScale", scale)
    unreal.EditorAssetLibrary.save_loaded_asset(mic)
    L("  实例 %s  (Metallic %.2f / Rough %.2f / Scale %.4f)"
      % (name, metallic, roughness, scale))
    return mic


def main():
    detail = import_texture("mech_detail.png", "T_MechDetail", False)
    detail_n = import_texture("mech_detail_n.png", "T_MechDetail_N", True)
    if not detail:
        L("❌ 主细节贴图缺失，中止")
        return

    master = build_material(detail, detail_n)
    if not master:
        return

    # 为调色板里每个材质名建一个实例
    mic_map = {}
    for name, color, metal, rough in PALETTE:
        mic = make_mic(master, name, color, metal, rough)
        if mic:
            mic_map[name] = mic

    # ── 应用到骨骼网格的材质槽 ──
    # 按"槽当前用的材质名"匹配实例名，没匹配上的保持原样。
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = ar.get_assets_by_path("/Game/RobotGame/Art/Characters", recursive=True)
    n_mesh = n_slot = 0
    for ad in assets:
        if str(ad.asset_class_path.asset_name) != "SkeletalMesh":
            continue
        nm = str(ad.asset_name)
        if "_LOD" in nm or nm.endswith("_Skeleton"):
            continue
        m = ad.get_asset()
        if not m:
            continue
        try:
            arr = m.get_editor_property("materials")
        except Exception:
            continue
        changed = 0
        detail_slots = []
        for i in range(len(arr)):
            try:
                cur = arr[i].get_editor_property("material_interface")
            except Exception:
                continue
            cur_name = cur.get_name() if cur else ""
            if cur_name in mic_map:
                arr[i].set_editor_property("material_interface", mic_map[cur_name])
                detail_slots.append("%d:%s" % (i, cur_name))
                changed += 1
        if changed:
            m.set_editor_property("materials", arr)
            unreal.EditorAssetLibrary.save_loaded_asset(m)
            n_mesh += 1
            n_slot += changed
        L("  %-24s 换 %d 槽  %s" % (nm, changed, " ".join(detail_slots)))
    L("完成：%d 个网格、%d 个槽位换上了细节材质" % (n_mesh, n_slot))


main()
