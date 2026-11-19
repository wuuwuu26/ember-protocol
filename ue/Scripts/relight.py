# -*- coding: utf-8 -*-
"""
重做整个关卡的光照与大气 —— 目标"黎明前的废弃机甲竞技场"。

为什么要推倒重来而不是微调：
  诊断发现场景里堆了 33 盏彩色点光（每盏 1800~2600 cd，半径 11~14m），
  而太阳只有 9 lux。等于没有主光、全靠一堆彩色灯泡互相叠加 ——
  结果就是"没有明暗、没有方向、没有阴影"，整张图糊成一片粉紫的中间调。
  实测截图：均值 0.29、p95 只有 0.63（正常电影感画面 p95 应在 0.8 以上）。
  p95 上不去 = 画面上根本不存在高光 = 金属材质全部失效。

新的布光结构（标准三点 + 环境）：
  ① 太阳（暖、低角度）—— 唯一主光，负责方向感和长影子
  ② SkyAtmosphere —— 让天空真的存在。这一步是金属材质能不能"像金属"的关键：
     metallic 0.9 的表面几乎不漫反射，颜色**全部来自反射**。
     没有天空 → 反射的是纯黑 → 金属看起来就是一块哑光塑料。
  ③ SkyLight —— 从 SkyAtmosphere 捕获，给暗部一层冷蓝环境光
  ④ 少量钠灯点光 —— 只做局部光池和画面层次，不再当主光用
  ⑤ 体积雾 —— 压低密度、改冷色，只做空气感

用法: bash tools/ue_py.sh ue/Scripts/relight.py "布光"
"""
import math
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"

# ══════════════════════════════════════════════════════
# 可调参数（一次改这里，跑一次脚本）
# ══════════════════════════════════════════════════════
CFG = {
    # 太阳：低角度暖光。pitch 越接近 0 越"贴地"，影子越长越戏剧化。
    # ⚠️ DirectionalLight 照的是自己的 Forward 方向：yaw=18 → 光沿 +X 传播，
    #    也就是**从 -X 侧照来**。玩家朝 +X 走、相机在身后（-X 侧），
    #    所以这个方位同时照亮"玩家背对相机的那一面"和"敌人的正面"。
    #    （yaw=202 是反的 —— cos202 为负，光仍朝 -X 传播，光源还在 +X 侧。）
    "sun_pitch": -26.0,
    "sun_yaw": 18.0,
    "sun_intensity": 22000.0,      # lux；夜景量级，配合下面的 EV 使用
    "sun_temp": 5200.0,        # 偏暖（日出前的橙）
    "sun_source_angle": 0.7,   # 阴影半影，太硬会显得廉价

    # 天光：从 SkyAtmosphere 捕获，给暗部冷色
    "sky_intensity": 3.2,
    "sky_color": (215, 230, 255),

    # 大气
    "atmo_mie_scale": 1.0,
    "atmo_rayleigh_scale": 1.0,
    "atmo_absorption": 0.0,

    # 雾：冷、薄
    "fog_density": 0.0055,
    "fog_height_falloff": 0.12,
    "fog_inscatter": (0.022, 0.030, 0.046),
    "fog_start": 900.0,
    "vol_fog_enable": True,
    "vol_fog_albedo": (0.42, 0.50, 0.62),
    "vol_fog_extinction": 1.4,
    "vol_fog_scatter": 0.35,

    # 点光：只保留光池，不再当主光
    "point_intensity": 2600.0,
    "point_radius": 1700.0,
    "point_shadow": True,

    # 后处理
    "ev100": 13.6,
    "bloom": 0.50,
    "bloom_threshold": 1.0,
    "vignette": 0.28,
}


def log(m):
    unreal.log("[布光] %s" % m)


def g(o, a, d=None):
    try:
        return o.get_editor_property(a)
    except Exception:
        return d


def s(o, a, v, tag=""):
    try:
        o.set_editor_property(a, v)
        return True
    except Exception as e:
        log("  ❌ %s%s: %s" % (tag, a, str(e)[:90]))
        return False


def col3(rgb):
    return unreal.Color(int(rgb[0]), int(rgb[1]), int(rgb[2]), 255)


def lin3(rgb):
    return unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0)


unreal.EditorLevelLibrary.load_level(LEVEL)
actors = unreal.EditorLevelLibrary.get_all_level_actors()
log("关卡 Actor 数 = %d" % len(actors))


def find(cls_name):
    return [a for a in actors if a.get_class().get_name() == cls_name]


# ─────────────────────────────────────────────
# ① 清掉重复的自动点光
# ─────────────────────────────────────────────
#
# 上一版脚本每次运行都 spawn 一批 AccentLight，跑了几次就叠了 33 盏。
# 这里保留名字以 AccentLight 开头的（它们的摆位是设计过的），
# 把脚本反复 spawn 出来的 PointLight* 全删掉。
killed = 0
for a in actors:
    lbl = a.get_actor_label()
    if a.get_class().get_name() == "PointLight" and lbl.startswith("PointLight"):
        unreal.EditorLevelLibrary.destroy_actor(a)
        killed += 1
log("删掉重复点光 %d 盏" % killed)

actors = unreal.EditorLevelLibrary.get_all_level_actors()


# ─────────────────────────────────────────────
# ② 太阳
# ─────────────────────────────────────────────
dls = find("DirectionalLight")
if not dls:
    log("❌ 关卡里没有 DirectionalLight")
else:
    dl = dls[0]
    rot = unreal.Rotator(0.0, CFG["sun_pitch"], CFG["sun_yaw"])
    dl.set_actor_rotation(rot, False)
    c = g(dl, "directional_light_component") or g(dl, "light_component")
    s(c, "intensity", CFG["sun_intensity"], "Sun.")
    s(c, "use_temperature", True, "Sun.")
    s(c, "temperature", CFG["sun_temp"], "Sun.")
    s(c, "light_source_angle", CFG["sun_source_angle"], "Sun.")
    s(c, "cast_shadows", True, "Sun.")
    s(c, "mobility", unreal.ComponentMobility.MOVABLE, "Sun.")
    # 让大气把它当太阳（决定天空的颜色分布）
    s(c, "atmosphere_sun_light", True, "Sun.")
    log("太阳：pitch=%.1f yaw=%.1f 强度=%.1f lux 色温=%.0fK"
        % (CFG["sun_pitch"], CFG["sun_yaw"],
           CFG["sun_intensity"], CFG["sun_temp"]))


# ─────────────────────────────────────────────
# ③ SkyAtmosphere —— 金属材质的命根子
# ─────────────────────────────────────────────
atmos = find("SkyAtmosphere")
if not atmos:
    atmos = [unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))]
    if atmos[0]:
        atmos[0].set_actor_label("SkyAtmosphere_0")
        log("✅ 新建 SkyAtmosphere")
else:
    log("SkyAtmosphere 已存在")

if atmos and atmos[0]:
    ac = g(atmos[0], "atmosphere_component") or g(atmos[0], "sky_atmosphere_component")
    if ac:
        s(ac, "mie_scattering_scale", CFG["atmo_mie_scale"], "Atmo.")
        s(ac, "rayleigh_scattering_scale", CFG["atmo_rayleigh_scale"], "Atmo.")
        s(ac, "absorption_scale", CFG["atmo_absorption"], "Atmo.")
        s(ac, "bottom_radius_km", 6360.0, "Atmo.")
        s(ac, "atmosphere_height_km", 60.0, "Atmo.")
        s(ac, "multiscattering", True, "Atmo.")
        log("大气参数已设")


# ─────────────────────────────────────────────
# ④ SkyLight
# ─────────────────────────────────────────────
sls = find("SkyLight")
for sl in sls:
    # 天光必须抬到空中。SkyLight 是"从自身位置捕获场景"的 ——
    # 放在关卡原点（也就是地板高度）时，捕获到的下半球全是地板，
    # 上半球被墙挡住，环境光几乎为 0，整机就变成黑剪影。
    sl.set_actor_location(unreal.Vector(0, 0, 1600), False, False)
    sc = g(sl, "sky_light_component") or g(sl, "light_component")
    if not sc:
        continue
    s(sc, "intensity", CFG["sky_intensity"], "Sky.")
    s(sc, "light_color", col3(CFG["sky_color"]), "Sky.")
    s(sc, "real_time_capture", True, "Sky.")
    s(sc, "mobility", unreal.ComponentMobility.MOVABLE, "Sky.")
    # 下半球压黑：地面反光不该和天空一样亮，否则整个场景"发飘"
    s(sc, "lower_hemisphere_is_black", True, "Sky.")
    s(sc, "lower_hemisphere_color", col3((6, 7, 10)), "Sky.")
    s(sc, "source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE, "Sky.")
    try:
        sc.recapture_sky()
        log("天光已重捕获")
    except Exception as e:
        log("  recapture_sky 失败: %s" % str(e)[:70])
    log("天光：强度=%.2f 颜色=%s" % (CFG["sky_intensity"], CFG["sky_color"]))


# ─────────────────────────────────────────────
# ⑤ 雾
# ─────────────────────────────────────────────
for fog in find("ExponentialHeightFog"):
    fc = g(fog, "component") or g(fog, "exponential_height_fog_component")
    if not fc:
        continue
    s(fc, "fog_density", CFG["fog_density"], "Fog.")
    s(fc, "fog_height_falloff", CFG["fog_height_falloff"], "Fog.")
    s(fc, "fog_inscattering_luminance", lin3(CFG["fog_inscatter"]), "Fog.")
    s(fc, "fog_max_opacity", 0.85, "Fog.")
    s(fc, "start_distance", CFG["fog_start"], "Fog.")
    s(fc, "enable_volumetric_fog", CFG["vol_fog_enable"], "Fog.")
    # ⚠️ 这个属性是 Color 不是 LinearColor —— 上一版传 LinearColor 静默失败，
    #    雾反照率一直停在默认纯白，于是雾把整个画面洗成粉白。
    s(fc, "volumetric_fog_albedo", col3([c * 255 for c in CFG["vol_fog_albedo"]]), "Fog.")
    s(fc, "volumetric_fog_extinction_scale", CFG["vol_fog_extinction"], "Fog.")
    s(fc, "volumetric_fog_scattering_distribution", CFG["vol_fog_scatter"], "Fog.")
    s(fc, "volumetric_fog_emissive", lin3((0, 0, 0)), "Fog.")
    s(fc, "volumetric_fog_distance", 8000.0, "Fog.")
    log("雾：密度=%.4f 反照率=%s" % (CFG["fog_density"], CFG["vol_fog_albedo"]))


# ─────────────────────────────────────────────
# ⑥ 点光：只做光池
# ─────────────────────────────────────────────
n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "PointLight":
        continue
    c = g(a, "point_light_component") or g(a, "light_component")
    if not c:
        continue
    s(c, "intensity", CFG["point_intensity"], "Pt.")
    s(c, "attenuation_radius", CFG["point_radius"], "Pt.")
    s(c, "cast_shadows", CFG["point_shadow"], "Pt.")
    n += 1
log("点光已收敛 %d 盏：强度=%.0f 半径=%.0f" % (n, CFG["point_intensity"], CFG["point_radius"]))


# ─────────────────────────────────────────────
# ⑦ 后处理
# ─────────────────────────────────────────────
for pp in find("PostProcessVolume"):
    s(pp, "unbound", True, "PP.")
    s(pp, "priority", 10.0, "PP.")
    st = g(pp, "settings")
    if not st:
        continue
    s(st, "override_auto_exposure_min_brightness", True, "PP.")
    s(st, "auto_exposure_min_brightness", CFG["ev100"], "PP.")
    s(st, "override_auto_exposure_max_brightness", True, "PP.")
    s(st, "auto_exposure_max_brightness", CFG["ev100"], "PP.")
    s(st, "override_bloom_intensity", True, "PP.")
    s(st, "bloom_intensity", CFG["bloom"], "PP.")
    s(st, "override_bloom_threshold", True, "PP.")
    s(st, "bloom_threshold", CFG["bloom_threshold"], "PP.")
    s(st, "override_vignette_intensity", True, "PP.")
    s(st, "vignette_intensity", CFG["vignette"], "PP.")
    # ⚠️ 这里**不能**用 AEM_MANUAL。Manual 模式会完全绕开下面那两个
    #    brightness（EV100）参数，改成手动之后 EV 从 16 调到 7 画面一点没变 ——
    #    排查了很久"天空为什么不亮"，真正的原因是曝光根本没在生效。
    #    正确做法是 Histogram 模式 + min == max，等价于"锁定曝光"，
    #    而且对 EV100 的调整有响应。
    s(st, "override_auto_exposure_method", True, "PP.")
    s(st, "auto_exposure_method", unreal.AutoExposureMethod.AEM_HISTOGRAM, "PP.")
    # 暗部往冷蓝推，亮部留暖 —— 这是"电影调色"最有效的一步
    s(st, "override_color_gain_shadows", True, "PP.")
    s(st, "color_gain_shadows", unreal.Vector4(0.92, 1.0, 1.10, 1.0), "PP.")
    s(st, "override_color_gain_highlights", True, "PP.")
    s(st, "color_gain_highlights", unreal.Vector4(1.06, 1.0, 0.94, 1.0), "PP.")
    s(st, "override_color_saturation", True, "PP.")
    s(st, "color_saturation", unreal.Vector4(0.90, 0.90, 0.90, 1.0), "PP.")
    s(st, "override_color_contrast", True, "PP.")
    s(st, "color_contrast", unreal.Vector4(1.14, 1.14, 1.16, 1.0), "PP.")
    s(st, "override_tone_curve_amount", True, "PP.")
    s(st, "tone_curve_amount", 0.78, "PP.")
    s(st, "override_ambient_occlusion_intensity", True, "PP.")
    s(st, "ambient_occlusion_intensity", 1.0, "PP.")
    s(st, "override_ambient_occlusion_radius", True, "PP.")
    s(st, "ambient_occlusion_radius", 120.0, "PP.")
    log("后处理：EV100=%.1f bloom=%.2f/%.2f"
        % (CFG["ev100"], CFG["bloom"], CFG["bloom_threshold"]))

unreal.EditorLevelLibrary.save_current_level()
log("已保存关卡")
