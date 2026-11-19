# -*- coding: utf-8 -*-
"""
电影化观感：后处理 + 体积雾 + 三点布光。
================================================================

用户要求"画面堪比 3A"。3A 和原型最大的差别往往**不在模型精度，而在光与后处理**：
  · 原型：平行光 + 天光 + 无后处理 → 平、灰、没有层次
  · 3A  ：手动曝光 + 低角度暖主光 + 冷补光 + 体积雾 + 泛光 + 暗角 +
          轻微色差/颗粒/景深 → 同样的模型立刻"有电影感"

这里全部走 UE 内置能力，不新增任何资产：
  ① PostProcessVolume（无边界、高优先级）—— 曝光/泛光/暗角/色差/颗粒/景深/色彩分级
  ② ExponentialHeightFog —— 体积雾，让远处自然衰减出层次，也给主光做出"光柱"
  ③ 主光（暖、低角度）+ 补光（冷、反向）+ 天光 —— 三点布光
  ④ 若干点光做"人造光源"，把场景从"荒地"变成"有人在用的设施"

⚠️ 所有属性设置都包在 try/except 里并逐条打印 —— 后处理的属性名在
   引擎版本之间改过好几次，写死一个不存在的名字，UE 只会静默忽略，
   最后拿到"看起来配好了、其实全是默认值"的关卡。

用法: bash tools/ue_py.sh ue/Scripts/cinematic_look.py "电影化"
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"

unreal.log("[电影化] 脚本已开始执行")


def log(m):
    unreal.log("[电影化] %s" % m)


def try_set(obj, attr, value, tag=""):
    try:
        obj.set_editor_property(attr, value)
        return True
    except Exception as e:
        log("    ❌ %s%s: %s" % (tag, attr, str(e)[:80]))
        return False


def try_get(obj, attr, default=None):
    try:
        return obj.get_editor_property(attr)
    except Exception:
        return default


# ─────────────────────────────────────────────
# ① 后处理
# ─────────────────────────────────────────────

# (属性名, 值, 说明)
PP_SCALARS = [
    # ── 曝光：手动，锁死 ──
    # 自动曝光会让"镜头转过去看到天空"和"低头看地面"的亮度差好几个档，
    # 画面忽明忽暗，完全没有电影感。手动锁定后每一帧的影调都一致。
    #
    # ⚠️ EV100 是"曝光值"，**越大越暗**（每个 +1 = 减半曝光）。
    #    第一版 10.4 实测画面均值 0.66、15% 像素过曝 —— 整个场景糊成一片白。
    #    实测标定：10.4 → 12.3（减约 1.9 档），画面均值落到 0.35 附近，
    #    正好是"暗背景 + 亮机甲"的工业夜景感目标区间。
    ("override_auto_exposure_min_brightness", True, ""),
    ("auto_exposure_min_brightness", 12.3, "EV100 下限"),
    ("override_auto_exposure_max_brightness", True, ""),
    ("auto_exposure_max_brightness", 12.3, "EV100 上限 = 下限 → 手动"),
    ("override_auto_exposure_bias", True, ""),
    ("auto_exposure_bias", 0.0, ""),

    # ── 泛光：金属高光溢出的关键 ──
    ("override_bloom_intensity", True, ""),
    ("bloom_intensity", 0.72, "别太糊，金属高光要炸得干净"),
    ("override_bloom_threshold", True, ""),
    ("bloom_threshold", 0.85, ""),

    # ── 暗角：把视线收拢到画面中心 ──
    ("override_vignette_intensity", True, ""),
    ("vignette_intensity", 0.42, ""),

    # ── 色差 / 颗粒：镜头质感 ──
    ("override_scene_fringe_intensity", True, ""),
    ("scene_fringe_intensity", 1.6, "很轻，只在画面边缘可见"),
    ("override_film_grain_intensity", True, ""),
    ("film_grain_intensity", 0.16, ""),

    # ── 景深：只在近景模式有意义，默认给很浅的强度 ──
    # ⚠️ 属性名是 fstop 不是 f_stop（UE 的 FPostProcessSettings 里就写 fstop）
    ("override_depth_of_field_focal_distance", True, ""),
    ("depth_of_field_focal_distance", 700.0, ""),
    ("override_depth_of_field_fstop", True, ""),
    ("depth_of_field_fstop", 8.0, "大光圈 → 背景虚化"),
    ("override_depth_of_field_sensor_width", True, ""),
    ("depth_of_field_sensor_width", 36.0, ""),
    ("override_depth_of_field_depth_blur_amount", True, ""),
    ("depth_of_field_depth_blur_amount", 1.0, ""),

    # ── 环境光遮蔽：缝隙/角落压暗，立体感的来源 ──
    ("override_ambient_occlusion_intensity", True, ""),
    ("ambient_occlusion_intensity", 0.85, ""),
    ("override_ambient_occlusion_radius", True, ""),
    ("ambient_occlusion_radius", 160.0, ""),
    ("override_ambient_occlusion_power", True, ""),
    ("ambient_occlusion_power", 2.4, ""),

    # ── 运动模糊 / 锐化 ──
    ("override_motion_blur_amount", True, ""),
    ("motion_blur_amount", 0.35, ""),
    ("override_sharpen", True, ""),
    ("sharpen", 0.30, ""),

    # ── 镜头光晕 ──
    ("override_lens_flare_intensity", True, ""),
    ("lens_flare_intensity", 0.35, ""),

    # ── 色温：整体偏冷一点点，和暖主光形成冷暖对比 ──
    ("override_white_temp", True, ""),
    ("white_temp", 5900.0, ""),
    ("override_tone_curve_amount", True, ""),
    ("tone_curve_amount", 0.85, ""),
]

# 色彩分级：UE 用的是"暗部/中间调/高光"三段式
PP_COLORS = [
    ("override_color_saturation", "color_saturation",
     (1.02, 1.02, 1.02, 1.0), "轻微提饱和"),
    ("override_color_contrast", "color_contrast",
     (1.08, 1.08, 1.10, 1.0), "提对比，蓝通道多一点"),
    ("override_color_gain", "color_gain",
     (1.03, 1.00, 0.96, 1.0), "高光偏暖"),
    ("override_color_offset", "color_offset",
     (0.0, 0.0, 0.008, 0.0), "暗部极轻微偏蓝 —— 冷暖分离"),
    ("override_color_gamma", "color_gamma",
     (0.97, 0.98, 1.0, 1.0), "压一点中间调"),
]


def setup_post_process(actor_sub):
    ppv = None
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if isinstance(a, unreal.PostProcessVolume):
            ppv = a
            break
    if not ppv:
        ppv = actor_sub.spawn_actor_from_class(
            unreal.PostProcessVolume, unreal.Vector(0, 0, 0),
            unreal.Rotator(0, 0, 0))
        log("新建 PostProcessVolume")
    else:
        log("复用已有 PostProcessVolume")

    try_set(ppv, "unbound", True, "PPV.")
    try_set(ppv, "enabled", True, "PPV.")
    try_set(ppv, "blend_weight", 1.0, "PPV.")
    try_set(ppv, "priority", 10.0, "PPV.")

    s = ppv.get_editor_property("settings")

    ok = 0
    for name, val, note in PP_SCALARS:
        if try_set(s, name, val, "PP."):
            ok += 1
    log("标量/开关：%d/%d 条生效" % (ok, len(PP_SCALARS)))

    okc = 0
    for flag, name, val, note in PP_COLORS:
        try_set(s, flag, True, "PP.")
        if try_set(s, name, unreal.Vector4(val[0], val[1], val[2], val[3]),
                   "PP."):
            okc += 1
            log("    ✓ %-22s %s（%s）" % (name, val, note))
    log("色彩分级：%d/%d 条生效" % (okc, len(PP_COLORS)))

    ppv.set_editor_property("settings", s)
    return ppv


# ─────────────────────────────────────────────
# ② 体积雾
# ─────────────────────────────────────────────

def setup_fog(actor_sub):
    fog = None
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if isinstance(a, unreal.ExponentialHeightFog):
            fog = a
            break
    if not fog:
        fog = actor_sub.spawn_actor_from_class(
            unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0),
            unreal.Rotator(0, 0, 0))
        log("新建 ExponentialHeightFog")

    comp = None
    for p in ("component", "exponential_height_fog_component"):
        comp = try_get(fog, p)
        if comp:
            break
    if not comp:
        log("❌ 拿不到雾组件")
        return fog

    settings = [
        # 传统高度雾：给远景一层薄纱。
        # ⚠️ UE5 之后**没有 volumetric_fog_density 这个属性了** ——
        #    体积雾的密度直接复用 fog_density，再用 volumetric_fog_extinction_scale
        #    单独放大。写错名字不会报错（只会静默不生效），所以这里逐个打印结果。
        ("fog_density", 0.020),
        ("fog_height_falloff", 0.25),
        ("fog_inscattering_luminance", unreal.LinearColor(0.36, 0.44, 0.58, 1.0)),
        ("fog_max_opacity", 0.92),
        ("fog_cutoff_distance", 24000.0),
        ("start_distance", 300.0),
        # 体积雾：这是"电影感"的主要来源 —— 光穿过空气时被散射成可见光柱
        ("enable_volumetric_fog", True),
        ("volumetric_fog_extinction_scale", 1.9),
        ("volumetric_fog_scattering_distribution", 0.25),
        ("volumetric_fog_distance", 8000.0),
        ("volumetric_fog_start_distance", 150.0),
        ("volumetric_fog_near_fade_in_distance", 300.0),
        ("volumetric_fog_emissive", unreal.LinearColor(0.0, 0.0, 0.0, 1.0)),
    ]
    ok = 0
    for name, val in settings:
        if try_set(comp, name, val, "Fog."):
            ok += 1
    log("体积雾：%d/%d 条生效" % (ok, len(settings)))
    return fog


# ─────────────────────────────────────────────
# ③ 布光
# ─────────────────────────────────────────────

def aim(actor, rot):
    """设置旋转并验证前向向量朝下 —— Rotator 的参数顺序坑过一次。"""
    actor.set_actor_rotation(rot, False)
    return actor.get_actor_forward_vector()


def setup_lights(actor_sub):
    dirs = []
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if isinstance(a, unreal.DirectionalLight):
            dirs.append(a)

    if not dirs:
        d = actor_sub.spawn_actor_from_class(
            unreal.DirectionalLight, unreal.Vector(0, 0, 1200),
            unreal.Rotator(0, 0, 0))
        dirs = [d]
        log("新建平行光")

    # ── 主光：低角度暖光 ──
    # 低角度（pitch 约 -28°）能拉出长影子，画面立刻有"时间感"；
    # 正午顶光是最平的，最不像电影。
    #
    # ⚠️ 方位角必须和**默认相机**配合：默认相机在角色**正后方**，
    #    如果主光从角色正面照过来（yaw 145），相机看到的就是整个背光面，
    #    机体变成一团黑。yaw 取 30° → 光从相机同侧的左后方来，
    #    机体正面被照亮，同时右脸留一条阴影，有立体感又不死黑。
    main = dirs[0]
    fwd = aim(main, unreal.Rotator(-28.0, 30.0, 0.0))
    if fwd.z > -0.05:
        log("⚠️ 主光前向 Z=%.2f 没有朝下，换参数顺序重试" % fwd.z)
        fwd = aim(main, unreal.Rotator(0.0, -28.0, 30.0))
    log("主光前向 = (%.2f, %.2f, %.2f)" % (fwd.x, fwd.y, fwd.z))

    lc = try_get(main, "directional_light_component") or try_get(main, "light_component")
    if lc:
        for name, val in (
                ("intensity", 9.0),
                ("light_color", unreal.Color(255, 226, 190, 255)),
                ("use_temperature", True),
                ("temperature", 5200.0),
                ("cast_shadows", True),
                ("affects_world", True),
                ("atmosphere_sun_light", True),
                # 阴影柔和一点：硬阴影看起来"廉价"
                ("light_source_angle", 1.6),
        ):
            try_set(lc, name, val, "主光.")
        try:
            lc.set_mobility(unreal.ComponentMobility.MOVABLE)
        except Exception:
            pass
        log("主光配置完成")

    # ── 只保留一盏平行光 ──
    #
    # ⚠️ 场景里存在 ≥2 盏平行光时，UE 每帧在**屏幕上**刷一条
    #    "Multiple directional lights are competing..." 警告（黑白字，
    #    -game 模式下直接盖在画面上，截图里清晰可见，非常出戏）。
    #    试过把补光的 volumetric_scattering_intensity 设为 0 —— 没用，
    #    引擎的判定只看"有几盏平行光参与"，不看雾的贡献。
    #    正确的做法就是**只留一盏**：多余的全部销毁。
    #    暗部照明交给天光 + 点光 + 雾的内散射，不再用第二盏平行光。
    extra = 0
    for a in dirs[1:]:
        actor_sub.destroy_actor(a)
        extra += 1
    if extra:
        log("销毁多余平行光 %d 盏（避免屏幕警告 + 双重照明）" % extra)
    dirs = dirs[:1]

    # ── 天光：环境光 ──
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if not isinstance(a, unreal.SkyLight):
            continue
        sc = try_get(a, "sky_light_component") or try_get(a, "light_component")
        if not sc:
            continue
        for name, val in (
                ("intensity", 0.85),
                ("light_color", unreal.Color(178, 205, 245, 255)),
                ("real_time_capture", True),
                ("affects_world", True),
                ("lower_hemisphere_is_black", True),
                ("occlusion_max_distance", 800.0),
        ):
            try_set(sc, name, val, "天光.")
        try:
            sc.set_mobility(unreal.ComponentMobility.MOVABLE)
            sc.recapture_sky()
        except Exception:
            pass
        log("天光配置完成")
        break

    # ── 点光：把场景从"荒地"变成"有人在用的设施" ──
    # 位置是照着竞技场的立柱/高台/拱门摆的，光色偏冷，和暖主光对冲。
    #
    # ⚠️ 必须先清掉上一轮生成的 —— 这个脚本会被反复重跑调参，
    #    不清就会每次多 11 盏灯，几十轮之后场景被灯淹掉，而且很难发现
    #    （画面只是"越来越亮"，看起来像曝光没调对）。
    killed = 0
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if isinstance(a, unreal.PointLight) and \
                str(a.get_actor_label()).startswith("AccentLight_"):
            actor_sub.destroy_actor(a)
            killed += 1
    if killed:
        log("清掉上一轮点光 %d 盏" % killed)

    accent_spots = [
        ((-900.0, -1000.0, 340.0), (0.55, 0.78, 1.00), 2600.0, 1400.0),
        ((-450.0, -1000.0, 340.0), (0.55, 0.78, 1.00), 2600.0, 1400.0),
        ((450.0, -1000.0, 340.0), (1.00, 0.62, 0.28), 2400.0, 1400.0),
        ((900.0, -1000.0, 340.0), (0.55, 0.78, 1.00), 2600.0, 1400.0),
        ((-900.0, 1000.0, 340.0), (1.00, 0.62, 0.28), 2400.0, 1400.0),
        ((0.0, 1000.0, 340.0), (0.55, 0.78, 1.00), 2600.0, 1400.0),
        ((900.0, 1000.0, 340.0), (1.00, 0.62, 0.28), 2400.0, 1400.0),
        ((1250.0, -1000.0, 520.0), (0.72, 0.52, 1.00), 2200.0, 1200.0),
        ((1250.0, 1000.0, 520.0), (0.72, 0.52, 1.00), 2200.0, 1200.0),
        ((700.0, 1380.0, 420.0), (1.00, 0.45, 0.30), 1800.0, 1100.0),
        ((700.0, -1380.0, 420.0), (0.40, 0.85, 1.00), 1800.0, 1100.0),
    ]
    n = 0
    for loc, col, inten, radius in accent_spots:
        pl = actor_sub.spawn_actor_from_class(
            unreal.PointLight, unreal.Vector(*loc), unreal.Rotator(0, 0, 0))
        if not pl:
            continue
        try:
            pl.set_actor_label("AccentLight_%d" % n)
        except Exception:
            pass
        plc = try_get(pl, "point_light_component") or try_get(pl, "light_component")
        if not plc:
            continue
        for name, val in (
                ("intensity", inten),
                ("light_color", unreal.Color(
                    int(col[0] * 255), int(col[1] * 255), int(col[2] * 255), 255)),
                ("attenuation_radius", radius),
                ("cast_shadows", False),
                ("affects_world", True),
                ("mobility", unreal.ComponentMobility.MOVABLE),
        ):
            try_set(plc, name, val, "点光.")
        n += 1
    log("点光 %d 盏" % n)


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(LEVEL)
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    setup_post_process(actor_sub)
    setup_fog(actor_sub)
    setup_lights(actor_sub)

    les.save_current_level()
    log("关卡已保存")
    log("完成")


main()
