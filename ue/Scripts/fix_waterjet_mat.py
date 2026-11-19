# -*- coding: utf-8 -*-
"""修复水柱材质 SM5 编译失败（第...轮）。

根因（日志确证）：M_WaterJet_Coolant / M_WaterJet_Toxic 里
TextureSampleParameter2D 节点 sampler_type = LinearGrayscale，
但 T_Toxic_Bub 是普通 Grayscale(sRGB) —— PCD3D_SM5 下采样器类型不匹配，
材质编译失败 → 引擎回退默认灰材质，水柱变成纯灰平涂圆柱。

修复：不删资产（保住关卡引用），清空表达式，用普通 TextureSample
且显式把 sampler_type 设成 Grayscale（与贴图一致）重建为
"深青/毒绿 + 向下流动气泡条纹 + 半透明"的水柱材质，recompile + save；
再把关卡里所有 Jet_* 水柱显式重新 set_material。

判据：重跑编辑器后日志里不再出现
  "M_WaterJet_Coolant.uasset: Failed to compile Material for platform PCD3D_SM5"
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
MAT_DIR = "/Game/RobotGame/Art/Materials"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
ELL = unreal.EditorLevelLibrary

lines = []


def log(s):
    unreal.log("[JetFix] %s" % s)
    lines.append(str(s))


def ex(mat, cls, x, y):
    return MEL.create_material_expression(mat, cls, x, y)


def link(a, b, pin):
    MEL.connect_material_expressions(a, "", b, pin)


def c1(mat, v, x, y):
    n = ex(mat, unreal.MaterialExpressionConstant, x, y)
    n.set_editor_property("r", float(v))
    return n


def c3(mat, r, g, b, x, y):
    n = ex(mat, unreal.MaterialExpressionConstant3Vector, x, y)
    n.set_editor_property("constant", unreal.LinearColor(r, g, b, 1.0))
    return n


def linear_gray_sampler():
    """新贴图 T_Jet_Flow 是 TC_GRAYSCALE/srgb=False → LinearGrayscale。
    返回与之匹配的 sampler 枚举值，保证 PCD3D_SM5 下能编译。"""
    try:
        e = unreal.MaterialSamplerType
        for nm in dir(e):
            up = nm.upper()
            if "GRAYSCALE" in up and "LINEAR" in up and not nm.startswith("_"):
                return getattr(e, nm), nm
    except Exception as ex0:
        log("枚举扫描失败 %s" % str(ex0)[:60])
    return None, None


def ensure_jet_flow_tex():
    """导入 T_Jet_Flow.png（水柱流动条纹）为 TC_GRAYSCALE / sRGB关 / 可 tile。"""
    path = "%s/T_Jet_Flow" % MAT_DIR
    src = r"C:\Users\25227\Documents\robot_game\tools\asset_src\T_Jet_Flow.png"
    if EAL.does_asset_exist(path):
        return EAL.load_asset(path)
    task = unreal.AssetImportTask()
    task.filename = src
    task.destination_path = MAT_DIR
    task.destination_name = "T_Jet_Flow"
    task.automated = True
    task.save = True
    task.replace_existing = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    t = EAL.load_asset(path)
    if t:
        t.set_editor_property("compression_settings",
                              unreal.TextureCompressionSettings.TC_GRAYSCALE)
        t.set_editor_property("srgb", False)
        try:
            t.set_editor_property("address_x", unreal.TextureAddress.TA_WRAP)
            t.set_editor_property("address_y", unreal.TextureAddress.TA_WRAP)
        except Exception:
            pass
        EAL.save_loaded_asset(t)
        log("导入 T_Jet_Flow（TC_GRAYSCALE / sRGB关 / Wrap）")
    else:
        log("!! T_Jet_Flow 导入失败")
    return t


def rebuild(mat_name, base_rgb, glow_rgb, emissive_base, speed_y, tex, sampler):
    path = "%s/%s" % (MAT_DIR, mat_name)
    mat = EAL.load_asset(path)
    if not mat:
        log("!! 缺 %s" % path)
        return None

    # 清空旧表达式（保留材质资产对象，关卡引用不丢）
    try:
        MEL.delete_all_material_expressions(mat)
    except Exception as e:
        log("delete_all 失败(%s)，试逐个删" % str(e)[:50])
        try:
            for e0 in list(MEL.get_material_expressions(mat)):
                MEL.delete_material_expression(mat, e0)
        except Exception as e2:
            log("逐个删也失败 %s" % str(e2)[:60])

    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    mat.set_editor_property("two_sided", True)

    st, st_name = sampler

    # UV：沿 V 拉长 + 向下滚动（条纹贴图本身横向条带，v_tiling 别太大否则太密）
    uv = ex(mat, unreal.MaterialExpressionTextureCoordinate, -1040, 0)
    uv.set_editor_property("u_tiling", 1.0)
    uv.set_editor_property("v_tiling", 2.0)
    pan = ex(mat, unreal.MaterialExpressionPanner, -860, 0)
    pan.set_editor_property("speed_x", 0.0)
    pan.set_editor_property("speed_y", speed_y)
    link(uv, pan, "Coordinate")

    # 普通 TextureSample（非 Parameter），显式 sampler_type 与贴图匹配 → 绝不 SM5 失败
    samp = ex(mat, unreal.MaterialExpressionTextureSample, -660, 0)
    samp.set_editor_property("texture", tex)
    if st is not None:
        try:
            samp.set_editor_property("sampler_type", st)
        except Exception as e:
            log("设 sampler_type 失败 %s" % str(e)[:60])
    link(pan, samp, "UVs")
    # 用 R 通道（灰度）驱动 emissive/opacity 条纹

    mask = ex(mat, unreal.MaterialExpressionComponentMask, -460, 0)
    mask.set_editor_property("r", True)
    mask.set_editor_property("g", False)
    mask.set_editor_property("b", False)
    mask.set_editor_property("a", False)
    link(samp, mask, "")

    # Emissive = 深青底 + 条纹提亮 → 流动的水
    # 条纹对比强化：先把 R(0..1) 用 Power(<1) 提亮中间调，再乘权重，
    # 让"亮带"和"暗带"在半透明细柱上也能读出流动感。
    pw = ex(mat, unreal.MaterialExpressionPower, -360, 120)
    link(mask, pw, "Base")
    link(c1(mat, 0.7, -460, 120), pw, "Exponent")
    mul = ex(mat, unreal.MaterialExpressionMultiply, -260, 100)
    link(pw, mul, "A")
    link(c3(mat, glow_rgb[0], glow_rgb[1], glow_rgb[2], -460, 240), mul, "B")
    add = ex(mat, unreal.MaterialExpressionAdd, -40, 140)
    link(c3(mat, emissive_base[0], emissive_base[1], emissive_base[2],
            -460, 380), add, "A")
    link(mul, add, "B")
    MEL.connect_material_property(add, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    MEL.connect_material_property(
        c3(mat, base_rgb[0], base_rgb[1], base_rgb[2], -460, -200), "",
        unreal.MaterialProperty.MP_BASE_COLOR)

    # Opacity = 0.42 + 0.50 × 条纹（水柱有疏密，不是玻璃棍）
    omul = ex(mat, unreal.MaterialExpressionMultiply, -260, -80)
    link(pw, omul, "A")
    link(c1(mat, 0.50, -460, -60), omul, "B")
    oadd = ex(mat, unreal.MaterialExpressionAdd, -40, -40)
    link(omul, oadd, "A")
    link(c1(mat, 0.42, -260, 20), oadd, "B")
    MEL.connect_material_property(oadd, "", unreal.MaterialProperty.MP_OPACITY)

    MEL.connect_material_property(c1(mat, 0.15, -100, 280), "",
                                  unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(c1(mat, 0.80, -100, 380), "",
                                  unreal.MaterialProperty.MP_SPECULAR)

    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    log("重建 %s  sampler=%s" % (mat_name, st_name))
    return mat


# T_Jet_Flow：横向流动条纹贴图（对比充足），TC_GRAYSCALE/srgb关
# → sampler 用 LinearGrayscale 与之匹配（PCD3D_SM5 可编译）
jet_tex = ensure_jet_flow_tex()
sampler = linear_gray_sampler()
log("使用贴图 %s  sampler=%s" % (
    jet_tex.get_name() if jet_tex else "None", sampler[1]))

# 压暗 emissive 底色、用条纹 R 通道提亮 → 明暗流动对比明显（水柱几何很细，
# 条纹弱了在屏幕上就消失；保持半透明与渠水融合）
# 提亮亮带（与上方金属波纹管的青色高光呼应），暗带仍压暗 → 明暗流动分明
cool = rebuild("M_WaterJet_Coolant",
               base_rgb=(0.02, 0.13, 0.19),
               glow_rgb=(0.55, 1.35, 1.70),
               emissive_base=(0.010, 0.045, 0.070),
               speed_y=-3.0, tex=jet_tex, sampler=sampler)
tox = rebuild("M_WaterJet_Toxic",
              base_rgb=(0.05, 0.16, 0.05),
              glow_rgb=(0.65, 1.35, 0.35),
              emissive_base=(0.015, 0.045, 0.010),
              speed_y=-2.2, tex=jet_tex, sampler=sampler)

# 关卡里所有 Jet_* 水柱显式重新挂（幂等，双保险）
ELL.load_level(LEVEL)
n = 0
for a in ELL.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl.startswith("Jet_"):
        comp = a.get_component_by_class(unreal.StaticMeshComponent)
        if not comp:
            continue
        m = cool if "Coolant" in lbl else tox
        if m:
            comp.set_material(0, m)
            n += 1
            log("  %-24s -> %s" % (lbl, m.get_name()))
ELL.save_current_level()
log("重挂 %d 个水柱，关卡已保存" % n)

with open(r"C:\Users\25227\Documents\robot_game\docs\jet_fix.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("JET_FIX_DONE")
