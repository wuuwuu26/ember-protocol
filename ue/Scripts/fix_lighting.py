"""
修复光照：把平行光转向下方 + 开启天光实时捕获
================================================================
在编辑器 Output Log 的 Cmd 输入框执行：
    py exec(open(r'C:/Users/25227/Documents/robot_game/ue/Scripts/fix_lighting.py').read())

【根因】灯光转储发现：
  平行光旋转 = (pitch 30, yaw 0, roll -45) → 前向向量 (0.87, 0, +0.50)
  **Z 为正 = 朝上照！** 太阳在地平线以下，地面收不到直接光。
  天光 real_time_capture = False 且 cubemap = None → 环境光也是零。
  → 场景光照总量为 0 → 受光材质渲染成纯黑。

【注意参数顺序坑】
生成关卡时传的是 Rotator(-48, 35, 0)，但关卡里实际是 pitch=30, roll=-45 ——
说明 `unreal.Rotator(a, b, c)` 的参数顺序和我想的不一样。
所以这里**设置后必须验证前向向量**，不对就换顺序重试。
"""

import unreal


def log(m):
    unreal.log("[修光照] %s" % m)
    print("[修光照] %s" % m)


def aim_down(light_actor):
    """把平行光转向下方，返回是否成功。"""
    # 尝试几种参数顺序，取第一个让前向向量 Z 为负的
    candidates = [
        ("pitch,yaw,roll", (-48.0, 35.0, 0.0)),
        ("roll,pitch,yaw", (0.0, -48.0, 35.0)),
        ("pitch,yaw,roll(-60)", (-60.0, 35.0, 0.0)),
        ("roll,pitch,yaw(-60)", (0.0, -60.0, 35.0)),
    ]
    for name, args in candidates:
        try:
            light_actor.set_actor_rotation(unreal.Rotator(*args), False)
        except Exception as e:
            log("  顺序 %s 设置失败: %s" % (name, str(e)[:50]))
            continue
        fwd = light_actor.get_actor_forward_vector()
        log("  顺序 %-18s → 前向=(%.2f, %.2f, %.2f)" % (name, fwd.x, fwd.y, fwd.z))
        if fwd.z < -0.1:
            log("  ✅ 命中！Z 为负，光朝下照")
            return True
    return False


def main():
    log("=" * 60)
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    fixed = 0

    for a in actors:
        cn = a.get_class().get_name()

        # ── 平行光 ──
        if "DirectionalLight" in cn:
            log("处理平行光 %s" % a.get_name())
            ok = aim_down(a)
            if not ok:
                log("  ⚠️ 所有参数顺序都没能让光朝下，请手动在编辑器里改旋转")

            for p in ("light_component", "directional_light_component"):
                try:
                    lc = a.get_editor_property(p)
                except Exception:
                    continue
                if not lc:
                    continue
                try:
                    lc.set_editor_property("intensity", 10.0)
                    lc.set_mobility(unreal.ComponentMobility.MOVABLE)
                    lc.set_editor_property("affects_world", True)
                    lc.set_editor_property("cast_shadows", True)
                    log("  强度=10 / Movable / AffectsWorld / 阴影开")
                except Exception as e:
                    log("  配置失败: %s" % str(e)[:60])
                break
            fixed += 1

        # ── 天光 ──
        elif "SkyLight" in cn:
            log("处理天光 %s" % a.get_name())
            for p in ("light_component", "sky_light_component"):
                try:
                    lc = a.get_editor_property(p)
                except Exception:
                    continue
                if not lc:
                    continue
                try:
                    lc.set_mobility(unreal.ComponentMobility.MOVABLE)
                    lc.set_editor_property("intensity", 1.0)
                    lc.set_editor_property("real_time_capture", True)
                    lc.set_editor_property("affects_world", True)
                    lc.recapture_sky()
                    rt = lc.get_editor_property("real_time_capture")
                    log("  实时捕获=%s（已重新捕获天空）" % rt)
                except Exception as e:
                    log("  配置失败: %s" % str(e)[:60])
                break
            fixed += 1

    log("共处理 %d 个灯光" % fixed)

    try:
        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        les.save_current_level()
        log("✅ 关卡已保存")
    except Exception as e:
        log("保存失败: %s" % str(e)[:60])

    log("=" * 60)
    log("完成。请把视口切回「光照」模式看效果")


main()
