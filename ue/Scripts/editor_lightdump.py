"""
把灯光的全部关键属性挖出来，找出它为什么不贡献光照
================================================================
在编辑器 Output Log 的 Cmd 输入框执行：
    py exec(open(r'C:/Users/25227/Documents/robot_game/ue/Scripts/editor_lightdump.py').read())

已知：几何体管线正常（Unlit/Wireframe 都能渲染），但 Lit 模式全黑。
→ 光照计算输出 0，需要查灯光到底哪里不对。
"""

import unreal


def log(m):
    unreal.log("[灯光转储] %s" % m)
    print("[灯光转储] %s" % m)


PROPS = [
    # 通用灯光属性
    "intensity", "light_color", "lighting_channels", "affects_world",
    "visible", "mobility", "cast_shadows", "cast_static_shadows",
    "cast_dynamic_shadows", "cast_volumetric_shadows",
    "indirect_lighting_intensity", "volumetric_scattering_intensity",
    "use_temperature", "temperature", "enabled",
    # 平行光特有
    "atmosphere_sun_light", "atmosphere_sun_light_index",
    "dynamic_shadow_distance_movable", "shadow_bias",
    # 组件
    "component_tags", "detail_mode",
]


def dump_component(lc, label):
    log("--- %s ---" % label)
    for p in PROPS:
        try:
            v = lc.get_editor_property(p)
            log("  %-32s = %s" % (p, v))
        except Exception:
            pass


def main():
    log("=" * 60)
    actors = unreal.EditorLevelLibrary.get_all_level_actors()

    for a in actors:
        cn = a.get_class().get_name()
        if "DirectionalLight" in cn:
            log("找到平行光: %s" % a.get_name())
            for p in ("light_component", "directional_light_component"):
                try:
                    lc = a.get_editor_property(p)
                except Exception:
                    continue
                if lc:
                    dump_component(lc, "平行光组件")
                    break
            # 朝向
            try:
                r = a.get_actor_rotation()
                fwd = a.get_actor_forward_vector()
                log("  旋转 = %s" % r)
                log("  前向 = (%.2f, %.2f, %.2f)  ← Z 为负表示向下照" % (
                    fwd.x, fwd.y, fwd.z))
            except Exception:
                pass

        elif "SkyLight" in cn:
            log("找到天光: %s" % a.get_name())
            for p in ("light_component", "sky_light_component"):
                try:
                    lc = a.get_editor_property(p)
                except Exception:
                    continue
                if lc:
                    dump_component(lc, "天光组件")
                    for sp in ("real_time_capture", "source_type",
                               "lower_hemisphere_is_black",
                               "cubemap", "sky_distance_threshold"):
                        try:
                            log("  %-32s = %s" % (sp, lc.get_editor_property(sp)))
                        except Exception:
                            pass
                    break

        elif "SkyAtmosphere" in cn:
            log("找到大气: %s" % a.get_name())

    # ── 世界设置里的关键项 ──
    log("--- 世界设置 ---")
    try:
        world = unreal.EditorLevelLibrary.get_editor_world()
        ws = world.get_world_settings()
        for p in ("force_no_precomputed_lighting", "b_use_client_side_hitches",
                  "lightmap_type"):
            try:
                log("  %-32s = %s" % (p, ws.get_editor_property(p)))
            except Exception:
                pass
    except Exception as e:
        log("  世界设置读取失败: %s" % str(e)[:60])

    log("=" * 60)


main()
