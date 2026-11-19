# -*- coding: utf-8 -*-
"""第一百一十轮：安全光影打磨（不碰光追、不改项目配置）。

只改关卡里的 PPV / 光源 / 雾，全部可回退（关卡已备份）。

做的五件事：
  1) PPV 开启 Lumen 反射 + Lumen GI（软件 Lumen，SM5 支持，无需 r.RayTracing）
     并提高反射质量 / 最大粗糙度、调 Bloom 让金属高光出"辉光"
  2) 给 EXT 区少量主灯开启阴影（只在 1/3 的点光源上开，避免
     "45 盏全开阴影把预算打满"的老坑 —— 第一百零二轮的教训）
  3) SkyLight 下半球不再全黑（消除物体底部死黑）
  4) 指数雾加浓 + 提高散射，做出体积光层次
  5) 曝光/色调微调（保持 Manual 曝光基调，只压一点灰度）

⚠️ 全部幂等：按 tag `LightPolish` 记录，重跑覆盖同一批参数。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\lighting_polish.txt"
TAG = "LightPolish"

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary
lines = []


def log(s):
    unreal.log("[LightPolish] %s" % s)
    lines.append(str(s))


# ═══════════════════════════════════════════════════════════
# 1. PostProcessVolume：Lumen 反射 + GI
# ═══════════════════════════════════════════════════════════
def polish_ppv():
    n = 0
    for a in sub.get_all_level_actors():
        if a.get_class().get_name() != "PostProcessVolume":
            continue
        st = a.get_editor_property("settings")

        # Lumen 反射：软件路径，不需要硬件光追
        st.set_editor_property("override_reflection_method", True)
        st.set_editor_property("reflection_method", unreal.ReflectionMethod.LUMEN)

        # Lumen GI
        st.set_editor_property("override_dynamic_global_illumination_method", True)
        st.set_editor_property(
            "dynamic_global_illumination_method",
            unreal.DynamicGlobalIlluminationMethod.LUMEN)

        # 反射质量：1 = 高。分辨率越高质量越好、开销越大；8GB 卡用 1
        st.set_editor_property("override_lumen_reflection_quality", True)
        st.set_editor_property("lumen_reflection_quality", 1)

        # 允许较粗糙的表面也参与反射追踪 —— 金属/混凝土才有"湿面"感
        st.set_editor_property("override_lumen_max_roughness_to_trace_reflections", True)
        st.set_editor_property("lumen_max_roughness_to_trace_reflections", 0.6)

        # 场景光照质量
        st.set_editor_property("override_lumen_scene_lighting_quality", True)
        st.set_editor_property("lumen_scene_lighting_quality", 1)

        # 屏幕空间追踪兜底（Lumen 内部会用它补细节）
        st.set_editor_property("override_lumen_reflections_screen_traces", True)
        st.set_editor_property("lumen_reflections_screen_traces", True)

        # Bloom：让自发光/灯具有辉光，保留原有的低强度基调只微调
        st.set_editor_property("override_bloom_intensity", True)
        st.set_editor_property("bloom_intensity", 0.62)
        st.set_editor_property("override_bloom_threshold", True)
        st.set_editor_property("bloom_threshold", 1.15)

        # AO 加强接触暗部（配合开阴影，让物体"落地"）
        st.set_editor_property("override_ambient_occlusion_intensity", True)
        st.set_editor_property("ambient_occlusion_intensity", 1.4)
        st.set_editor_property("override_ambient_occlusion_radius", True)
        st.set_editor_property("ambient_occlusion_radius", 150.0)

        # 曝光：保持 Manual，只降一点 bias（当前 5.6 偏亮、灰）
        st.set_editor_property("override_auto_exposure_bias", True)
        st.set_editor_property("auto_exposure_bias", 5.1)

        # 轻微压暗 & 提对比，去掉"发灰"
        st.set_editor_property("override_color_saturation", True)
        st.set_editor_property("color_saturation", unreal.Vector4(1.02, 1.02, 1.04, 1.0))
        st.set_editor_property("override_color_contrast", True)
        st.set_editor_property("color_contrast", unreal.Vector4(1.10, 1.10, 1.12, 1.0))

        a.set_editor_property("settings", st)

        tags = [str(t) for t in a.get_editor_property("tags")]
        if TAG not in tags:
            tags.append(TAG)
            a.set_editor_property("tags", tags)
        n += 1
    log("PPV：Lumen 反射 + GI 已开（%d 个）" % n)


# ═══════════════════════════════════════════════════════════
# 2. 少量主灯开阴影
# ═══════════════════════════════════════════════════════════
def enable_key_shadows():
    """只给 EXT 区的"主照明"灯开阴影 —— 每 3 盏开 1 盏。

    ⚠️ 第一百零二轮教训：45 盏灯全开 cast_shadows 会把阴影贴图预算打满，
    表现为"灯加了也看不出亮"。这里刻意稀疏开启，兼顾接触阴影与性能。
    """
    opened = 0
    total = 0
    for a in sub.get_all_level_actors():
        cls = a.get_class().get_name()
        if cls not in ("PointLight", "SpotLight"):
            continue
        try:
            tags = [str(t) for t in a.get_editor_property("tags")]
        except Exception:
            continue
        if "ExtRegion" not in tags:
            continue
        total += 1
        # 只对带 ExtLight_main / ExtLight_fill 的主灯开（tag 里可能带 ExtLight_ 前缀）
        is_main = any(t.startswith("ExtLight_main") or t.startswith("ExtLight_fill")
                      or t.startswith("ExtLight_tunnel") for t in tags)
        if not is_main:
            continue
        # 每 3 盏开 1 盏（用位置哈希挑选，保证每次挑同一批）
        loc = a.get_actor_location()
        if int(abs(loc.x) + abs(loc.y)) % 3 != 0:
            continue
        comp = (a.get_editor_property("point_light_component")
                if cls == "PointLight" else a.get_editor_property("spot_light_component"))
        if not comp:
            continue
        comp.set_editor_property("cast_shadows", True)
        # 阴影贴图分辨率：属性名在不同版本不同，找不到就跳过（不影响功能）
        for p in ("shadow_map_resolution_scale", "shadow_map_resolution"):
            try:
                comp.set_editor_property(p, 0.5)
                break
            except Exception:
                continue
        opened += 1
    log("EXT 灯光 %d 盏，其中开启阴影 %d 盏（稀疏开启，防阴影预算打满）"
        % (total, opened))


# ═══════════════════════════════════════════════════════════
# 3. SkyLight：下半球不再全黑
# ═══════════════════════════════════════════════════════════
def fix_skylight():
    for a in sub.get_all_level_actors():
        if a.get_class().get_name() != "SkyLight":
            continue
        comp = a.get_editor_property("light_component")
        if not comp:
            continue
        # lower_hemisphere_is_black=True 让物体底部死黑；
        # 关掉它，改为用 AO/阴影制造接触暗部（更真实）
        comp.set_editor_property("lower_hemisphere_is_black", False)
        # 强度略提，补足关掉全黑半球后地面反射的对比
        comp.set_editor_property("intensity", 1.15)
        comp.set_editor_property("real_time_capture", True)
        log("SkyLight：半球不再全黑，强度 1.35→1.15")
        return
    log("!! 未找到 SkyLight")


# ═══════════════════════════════════════════════════════════
# 4. 雾：加浓 + 散射
# ═══════════════════════════════════════════════════════════
def polish_fog():
    for a in sub.get_all_level_actors():
        if a.get_class().get_name() != "ExponentialHeightFog":
            continue
        comp = a.get_editor_property("component")
        if not comp:
            continue
        comp.set_editor_property("fog_density", 0.012)       # 0.006 → 0.012
        comp.set_editor_property("fog_height_falloff", 0.25)
        comp.set_editor_property("start_distance", 400.0)
        # 散射亮度：冷蓝，配合工业夜景
        comp.set_editor_property(
            "fog_inscattering_luminance",
            unreal.LinearColor(0.030, 0.042, 0.070, 1.0))
        try:
            comp.set_editor_property("fog_radial_inscattering", True)
        except Exception:
            pass
        log("雾：密度 0.006→0.012，起始距离 600→400，冷蓝散射")
        return
    log("!! 未找到 ExponentialHeightFog")


polish_ppv()
enable_key_shadows()
fix_skylight()
polish_fog()

les.save_current_level()
log("已保存关卡")
with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("LIGHT_POLISH_DONE")
