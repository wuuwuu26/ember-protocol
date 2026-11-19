# -*- coding: utf-8 -*-
"""
用"天空穹顶"替代 SkyAtmosphere —— 引擎的大气在这台机器上不出图。

为什么放弃 SkyAtmosphere：
    已经确认它存在于关卡里、太阳也被正确指认为 atmosphere_sun_light、
    太阳强度提到 30000 lux、曝光从 EV16 一路降到 EV7，天空区域始终是
    (13, 2, 11) 这种近乎全黑的颜色。结论是这套环境里大气渲染没生效。
    与其继续和它较劲，不如自己画一个 —— 而且自己画的好处是**完全可控**：
    天顶色、地平线色、太阳辉光的位置和强度都能精确指定。

做法：
    ① 建一个 Unlit + TwoSided 的自发光材质 M_SkyDome，
       颜色 = 天顶/地平线渐变 + 太阳方向的辉光
    ② 生成一个 900m 的球（引擎自带 /Engine/BasicShapes/Sphere），
       材质换上 M_SkyDome，关阴影、关碰撞

    Unlit 是关键：天空不该被太阳照亮（它本身就是光源），
    如果走默认的 Lit，天顶会被太阳再打一遍，颜色完全失控。
"""
import math
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
MAT_DIR = "/Game/RobotGame/Art/Materials"
MAT_NAME = "M_SkyDome"
MAT_PATH = "%s/%s" % (MAT_DIR, MAT_NAME)

# ── 美术参数（v2：夜景）──
#
# ★ 2026-10-25 v2：光照已经改成"月光 1800 lux 冷白 + 地面暖色光池"，
#   天空却还是黄昏的暖橙渐变 —— 冷地面配暖天空，色温打架，
#   而且天空是一整块平色布，没有纵深。v2 重画：
#     ① 天顶深蓝 → 地平线冷蓝（大气散射），地平线贴一条**暖橙光害带**
#        （工业废墟的城市余光），冷暖交界线正好压住远景剪影
#     ② 一颗低垂的冷月 + 两级光晕（紧晕给锐度，宽晕给散射）
#     ③ 星点亮度从 0.025 提到 0.35（0.025×75≈1.9 nit，比天空还暗，
#        等于没画；0.35×75≈26 nit 才是"能看见的星"）
#
# ★ 2026-10-25 改：整屏统计发现**天空是画面里唯一的"死黑"来源** ——
#   顶部 200px 实测 RGB=(0.001,0.005,0.056)，贡献了全图 45% 的 crush。
#
#   排了两轮才找到真正的原因：**自发光和"物理光照"根本不是一个量纲**。
#   实测地面（albedo 0.105，太阳 5200 lux）算出来的亮度在 **100+ nit**，
#   而天空穹顶的自发光只有 0~1 —— 在物理相机曝光下，1 nit 的天空
#   相对 137 nit 的地面等于纯黑。所以 INTENSITY 从 3.2 提到 9.0
#   天空几乎没有任何变化（B 0.056 → 0.059），因为两者都远低于下趾。
#   反推出"天空读作深蓝"需要的量级是 **~70**（B 通道 0.108×75≈8 nit）。
#   ★ 教训：给 Unlit/自发光材质调亮度时，不能拿"0~1 的比例"思考，
#     要拿"场景里其他东西有多少 nit"当参照。
ZENITH = (0.028, 0.040, 0.085)          # 天顶：深蓝（夜空最暗处，但不死黑）
HORIZON = (0.34, 0.22, 0.13)            # 地平线暖色：工业区光害，把远景剪影压出来
HORIZON_COOL = (0.13, 0.18, 0.32)       # 背光侧地平线：大气散射的冷蓝
MOON_COLOR = (1.25, 1.30, 1.38)         # 月盘：比天空亮一个数量级才读得出"一个盘"
MOON_HALO = (0.16, 0.20, 0.28)          # 月晕：宽、淡，冷蓝
GLOW_POWER = 4.5                        # 月晕衰减（越小晕越大）
MOON_POWER = 1200.0                     # 月盘边缘锐度（越小盘越大；4000 只有 8px，被 TSR 吃掉了）
# 月亮挂在哪：仰角 30°，方位取 +X —— 这是第三人称默认机位的正前方，
# 保证开局抬头就能看到。换关卡朝向时只改这一个向量。
MOON_DIR = (0.960, 0.207, 0.186)   # 仰角 ~11°：镜头只看到地平线以上 ~24°，
                                   # 30° 的月亮在画面外（第一版就踩了这个坑）
INTENSITY = 75.0  # 2026-10-25：3.2 → 9.0 → 75.0。见下面"为什么是 75"。
STAR_SCALE = 3.0      # 星星密度（UV 重复次数）
STAR_BRIGHT = 0.32    # 星星亮度：0.025×75≈1.9 nit（比天空还暗=看不见），
                      # 0.32×75≈24 nit 才是"能看见的星"


def log(m):
    unreal.log("[天空穹顶] %s" % m)


mel = unreal.MaterialEditingLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()


def build_material():
    if unreal.EditorAssetLibrary.does_asset_exist(MAT_PATH):
        unreal.EditorAssetLibrary.delete_asset(MAT_PATH)
    mat = at.create_asset(MAT_NAME, MAT_DIR, unreal.Material,
                          unreal.MaterialFactoryNew())
    if not mat:
        log("❌ 材质创建失败")
        return None

    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", True)
    # 天空不该参与光照，也不该被雾遮挡（雾会把远处的天压灰）
    # ⚠️ 关键：天光（SkyLight 实时捕获）只认**标记为 IsSky 的材质**。
    #    不设这个标志时，引擎会报警
    #    "A sky light with real-time capture ... Otherwise it will be black"，
    #    天空被捕获成黑色 → 环境光为零 → 整个场景只剩灯光直射，发灰发橙。
    for flag in ("used_with_sky", "is_sky"):
        try:
            mat.set_editor_property(flag, True)
            log("材质标志 %s = True" % flag)
        except Exception as e:
            log("材质标志 %s 设置失败: %s" % (flag, str(e)[:50]))

    def ex(cls, x, y):
        return mel.create_material_expression(mat, cls, x, y)

    def c3(rgb, x, y):
        e = ex(unreal.MaterialExpressionConstant3Vector, x, y)
        e.set_editor_property("constant",
                              unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
        return e

    def c1(v, x, y):
        e = ex(unreal.MaterialExpressionConstant, x, y)
        e.set_editor_property("r", float(v))
        return e

    def link(a, b, inp, out=""):
        try:
            mel.connect_material_expressions(a, out, b, inp)
            return True
        except Exception as e:
            log("  连接 %s 失败: %s" % (inp, str(e)[:70]))
            return False

    # dir = normalize(WorldPos - ActorPos)
    wp = ex(unreal.MaterialExpressionWorldPosition, -1800, 0)
    ap = ex(unreal.MaterialExpressionActorPositionWS, -1800, 150)
    sub = ex(unreal.MaterialExpressionSubtract, -1600, 60)
    link(wp, sub, "A")
    link(ap, sub, "B")
    nrm = ex(unreal.MaterialExpressionNormalize, -1450, 60)
    link(sub, nrm, "")

    # t = saturate(dir.Z)
    maskz = ex(unreal.MaterialExpressionComponentMask, -1300, -120)
    maskz.set_editor_property("r", False)
    maskz.set_editor_property("g", False)
    maskz.set_editor_property("b", True)
    maskz.set_editor_property("a", False)
    link(nrm, maskz, "")

    # 用 0.55 次幂把地平线的暖色往上多推一点，避免"地平线只有一条细线"
    tpow = ex(unreal.MaterialExpressionPower, -1150, -120)
    link(maskz, tpow, "Base")
    link(c1(0.55, -1300, -260), tpow, "Exp")

    # dot(dir, sunDir) 提前算，地平线的冷暖分离要用
    dot0 = ex(unreal.MaterialExpressionDotProduct, -1450, -700)
    link(nrm, dot0, "A")
    link(c3(MOON_DIR, -1600, -700), dot0, "B")
    d01 = ex(unreal.MaterialExpressionMultiply, -1300, -700)
    link(dot0, d01, "A")
    link(c1(0.5, -1450, -820), d01, "B")
    d02 = ex(unreal.MaterialExpressionAdd, -1150, -700)
    link(d01, d02, "A")
    link(c1(0.5, -1300, -820), d02, "B")
    d0c = ex(unreal.MaterialExpressionClamp, -1000, -700)
    link(d02, d0c, "")

    # 地平线：**月亮那一侧冷、背月那一侧暖**（暖的是城市光害）
    hcol = ex(unreal.MaterialExpressionLinearInterpolate, -1200, -420)
    link(c3(HORIZON, -1400, -520), hcol, "A")
    link(c3(HORIZON_COOL, -1400, -420), hcol, "B")
    link(d0c, hcol, "Alpha")

    # 渐变
    grad = ex(unreal.MaterialExpressionLinearInterpolate, -1000, -60)
    link(hcol, grad, "A")
    link(c3(ZENITH, -1200, -540), grad, "B")
    link(tpow, grad, "Alpha")

    # dot(dir, moonDir)
    dot = ex(unreal.MaterialExpressionDotProduct, -1300, 260)
    link(nrm, dot, "A")
    link(c3(MOON_DIR, -1500, 260), dot, "B")

    # 月晕（宽、淡）
    dot_c = ex(unreal.MaterialExpressionClamp, -1150, 260)
    link(dot, dot_c, "")
    glowp = ex(unreal.MaterialExpressionPower, -1000, 260)
    link(dot_c, glowp, "Base")
    link(c1(GLOW_POWER, -1150, 160), glowp, "Exp")
    glow = ex(unreal.MaterialExpressionMultiply, -850, 260)
    link(glowp, glow, "A")
    link(c3(MOON_HALO, -1000, 380), glow, "B")

    # 月盘（窄、亮）
    sunp = ex(unreal.MaterialExpressionPower, -1000, 560)
    link(dot_c, sunp, "Base")
    link(c1(MOON_POWER, -1150, 560), sunp, "Exp")
    sun = ex(unreal.MaterialExpressionMultiply, -850, 560)
    link(sunp, sun, "A")
    link(c3(MOON_COLOR, -1000, 680), sun, "B")

    # ── 星空：直接用引擎自带的 T_Sky_Stars ──
    #
    # 纯渐变天空在夜景里是"一块布"，加一层星星立刻有纵深。
    # 引擎资产 /Engine/EngineSky/T_Sky_Stars 是一张可平铺的星点图，
    # 用方向向量的 XZ 投影当 UV（水平环绕），再按 dir.Z 的幂衰减，
    # 地平线附近自动没有星星（真实夜空也是这样，被大气消光吃掉）。
    star = None
    try:
        tex = unreal.EditorAssetLibrary.load_asset("/Engine/EngineSky/T_Sky_Stars")
        if tex:
            mx = ex(unreal.MaterialExpressionComponentMask, -1300, 900)
            mx.set_editor_property("r", True)
            mx.set_editor_property("g", False)
            mx.set_editor_property("b", False)
            mx.set_editor_property("a", False)
            link(nrm, mx, "")

            mz = ex(unreal.MaterialExpressionComponentMask, -1300, 1000)
            mz.set_editor_property("r", False)
            mz.set_editor_property("g", False)
            mz.set_editor_property("b", True)
            mz.set_editor_property("a", False)
            link(nrm, mz, "")

            app = ex(unreal.MaterialExpressionAppendVector, -1150, 950)
            link(mx, app, "A")
            link(mz, app, "B")

            uvs = ex(unreal.MaterialExpressionMultiply, -1000, 950)
            link(app, uvs, "A")
            link(c1(STAR_SCALE, -1150, 1080), uvs, "B")

            ts = ex(unreal.MaterialExpressionTextureSampleParameter2D, -820, 950)
            ts.set_editor_property("parameter_name", "StarTex")
            ts.set_editor_property("texture", tex)
            try:
                ts.set_editor_property(
                    "sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
            except Exception:
                pass
            link(uvs, ts, "UVs")

            # 只保留上半球，并且越靠天顶越亮
            # ★ 修正：原来是 clamp(dir.z)^1.6 —— 镜头只看到地平线以上 20°，
            #   dir.z ≈ 0.1~0.4，1.6 次幂把它压到 0.02~0.2，星星比天空还暗，
            #   等于没画。改成 saturate(dir.z*3.5)：可见天空算"满天"，
            #   只有紧贴地平线的一小条被消光吃掉（真实夜空也是这样）。
            zmask = ex(unreal.MaterialExpressionMultiply, -1300, 1200)
            link(maskz, zmask, "A")
            link(c1(3.5, -1450, 1300), zmask, "B")
            zclamp2 = ex(unreal.MaterialExpressionClamp, -1150, 1200)
            link(zmask, zclamp2, "")
            zpow = zclamp2

            star = ex(unreal.MaterialExpressionMultiply, -640, 1000)
            link(ts, star, "A")
            link(zpow, star, "B")
            star2 = ex(unreal.MaterialExpressionMultiply, -500, 1000)
            link(star, star2, "A")
            link(c1(STAR_BRIGHT, -640, 1120), star2, "B")
            star = star2
            log("✅ 星空层已接入（T_Sky_Stars，强度 %.2f）" % STAR_BRIGHT)
        else:
            log("⚠️ 找不到 /Engine/EngineSky/T_Sky_Stars，跳过星空")
    except Exception as e:
        log("⚠️ 星空构建失败：%s" % str(e)[:100])

    # 合计
    add1 = ex(unreal.MaterialExpressionAdd, -650, 100)
    link(grad, add1, "A")
    link(glow, add1, "B")
    add2 = ex(unreal.MaterialExpressionAdd, -500, 100)
    link(add1, add2, "A")
    link(sun, add2, "B")
    add3 = ex(unreal.MaterialExpressionAdd, -380, 100)
    link(add2, add3, "A")
    if star is not None:
        link(star, add3, "B")
    else:
        link(c3((0.0, 0.0, 0.0), -500, -40), add3, "B")
    fin = ex(unreal.MaterialExpressionMultiply, -250, 100)
    link(add3, fin, "A")
    link(c1(INTENSITY, -400, 240), fin, "B")

    try:
        mel.connect_material_property(fin, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    except Exception as e:
        log("  接自发光失败: %s" % str(e)[:80])

    mel.layout_material_expressions(mat)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    log("✅ 材质 %s 已建立" % MAT_PATH)
    return mat


mat = build_material()
if not mat:
    raise SystemExit(1)

# ─────────────────────────────────────────────
# 生成 / 更新穹顶
# ─────────────────────────────────────────────
unreal.EditorLevelLibrary.load_level(LEVEL)
SPHERE = "/Engine/BasicShapes/Sphere.Sphere"
mesh = unreal.EditorAssetLibrary.load_asset(SPHERE)
if not mesh:
    log("❌ 找不到 %s" % SPHERE)
    raise SystemExit(1)

dome = None
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "SkyDome":
        dome = a
        break

if dome is None:
    dome = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    dome.set_actor_label("SkyDome")
    log("新建 SkyDome")

dome.set_actor_scale3d(unreal.Vector(100.0, 100.0, 100.0))
dome.set_actor_location(unreal.Vector(0, 0, 0), False, False)
smc = dome.static_mesh_component
smc.set_static_mesh(mesh)
smc.set_material(0, mat)
smc.set_editor_property("cast_shadow", False)
smc.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
dome.set_actor_enable_collision(False)
log("穹顶：半径 50m，材质 %s" % MAT_NAME)

unreal.EditorLevelLibrary.save_current_level()
log("已保存关卡")

# 落盘结果 + 打一个 ue_py.sh 能识别的独有标记
# （日志里 "已保存关卡" 这种中文串不会被 grep 稳定匹配，而且 PowerShell 会乱码）
try:
    with open(r"C:\Users\25227\Documents\robot_game\docs\sky_result.txt", "w") as f:
        f.write("zenith=%s horizon=%s horizon_cool=%s\n"
                % (ZENITH, HORIZON, HORIZON_COOL))
        f.write("moon_dir=%s intensity=%.1f star_bright=%.2f\n"
                % (MOON_DIR, INTENSITY, STAR_BRIGHT))
        f.write("SKYDOME_V2_DONE\n")
except Exception as e:
    log("写结果失败: %s" % str(e))

