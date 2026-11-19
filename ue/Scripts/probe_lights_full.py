# -*- coding: utf-8 -*-
"""灯光/后处理盘点（只读，不改任何东西）。

用途：调光之前先弄清楚"到底有多少盏灯、各自什么参数"。
之前的经验是：同一类灯在三个地方被反复覆盖（关卡数据 / relight.py /
RobotCharacter::FixLevelLighting / RobotGameMode::EnsureLevelLighting），
谁最后执行谁说了算 —— 不盘点就只能靠猜。

运行：
    bash tools/ue_py.sh ue/Scripts/probe_lights_full.py "灯光盘点"
"""
import unreal

L = "[灯光盘点]"
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"

unreal.EditorLevelLibrary.load_level(LEVEL)
actors = unreal.EditorLevelLibrary.get_all_level_actors()
unreal.log("%s Actor 总数 = %d" % (L, len(actors)))


def lit_summary(a):
    """返回 (类型, 名字, 强度, 半径, 颜色, 是否投影, 是否可见)"""
    cls = a.get_class().get_name()
    comp = None
    for attr in ("light_component", "point_light_component",
                 "spot_light_component", "rect_light_component",
                 "directional_light_component"):
        try:
            comp = a.get_editor_property(attr)
            if comp:
                break
        except Exception:
            comp = None
    if not comp:
        return None

    def g(name, default=None):
        try:
            return comp.get_editor_property(name)
        except Exception:
            return default

    col = g("light_color")
    colstr = "(%.2f,%.2f,%.2f)" % (col.r, col.g, col.b) if col else "-"
    return (cls, a.get_actor_label(), g("intensity"), g("attenuation_radius"),
            colstr, g("cast_shadows"), g("visible"))


counts = {}
total_lux_guess = 0.0
for a in actors:
    s = lit_summary(a)
    if not s:
        continue
    cls, label, inten, radius, col, shadow, vis = s
    counts[cls] = counts.get(cls, 0) + 1
    if cls == "DirectionalLight":
        # 平行光只报详情（强度单位是 lux，直接和曝光挂钩）
        unreal.log("%s %s %s 强度=%s 颜色=%s 投影=%s 可见=%s"
                   % (L, cls, label, inten, col, shadow, vis))
    elif cls in ("PointLight", "SpotLight", "RectLight"):
        # 点光很多，只报"前 5 盏 + 总量"，避免日志刷屏
        if counts[cls] <= 5:
            unreal.log("%s %s %s 强度=%s 半径=%s 颜色=%s 投影=%s 可见=%s"
                       % (L, cls, label, inten, radius, col, shadow, vis))
        try:
            if inten:
                total_lux_guess += float(inten)
        except Exception:
            pass

unreal.log("%s 计数：%s" % (L, counts))
unreal.log("%s 点光/聚光强度总和 = %.0f cd" % (L, total_lux_guess))

# ── 后处理 ──
for a in actors:
    if a.get_class().get_name() != "PostProcessVolume":
        continue
    st = a.get_editor_property("settings")
    unreal.log("%s PPV %s unbound=%s priority=%s bias=%s method=%s bloom=%s/%s"
               % (L, a.get_actor_label(),
                  a.get_editor_property("unbound"),
                  a.get_editor_property("priority"),
                  st.get_editor_property("auto_exposure_bias"),
                  st.get_editor_property("auto_exposure_method"),
                  st.get_editor_property("bloom_intensity"),
                  st.get_editor_property("bloom_threshold")))

# ── 天光 ──
for a in actors:
    if a.get_class().get_name() != "SkyLight":
        continue
    c = a.get_editor_property("light_component")
    unreal.log("%s 天光强度=%s 颜色=%s 实时捕获=%s 下半球黑=%s"
               % (L, c.get_editor_property("intensity"),
                  c.get_editor_property("light_color"),
                  c.get_editor_property("real_time_capture"),
                  c.get_editor_property("lower_hemisphere_is_black")))

# ── 雾 ──
for a in actors:
    if a.get_class().get_name() != "ExponentialHeightFog":
        continue
    c = a.get_editor_property("component")
    unreal.log("%s 雾 密度=%s 体积雾=%s 起始距离=%s"
               % (L, c.get_editor_property("fog_density"),
                  c.get_editor_property("enable_volumetric_fog"),
                  c.get_editor_property("start_distance")))

unreal.log("%s 完成" % L)
