"""
补上 SkyAtmosphere，让天光能正常捕获环境光
================================================================
在编辑器 Output Log 的 Cmd 输入框执行：
    py exec(open(r'C:/Users/25227/Documents/robot_game/ue/Scripts/fix_atmosphere.py').read())

【背景】平行光朝上的 bug 已修好，地面能被照亮了。
但编辑器仍提示「可实时捕获的天空光照需要 SkyAtmosphere」，
说明关卡里缺 SkyAtmosphere，天光拿不到环境光。
补上它能让阴影里的部分也有亮度，画面不会那么硬。
"""

import unreal


def log(m):
    unreal.log("[补大气] %s" % m)
    print("[补大气] %s" % m)


def main():
    log("=" * 60)
    actors = unreal.EditorLevelLibrary.get_all_level_actors()

    # ── 1. 检查是否已有 SkyAtmosphere ──
    existing = [a for a in actors if "SkyAtmosphere" in a.get_class().get_name()]
    log("关卡里现有 SkyAtmosphere: %d 个" % len(existing))

    if not existing:
        log("缺少，正在创建……")
        actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        try:
            sa = actor_sub.spawn_actor_from_class(
                unreal.SkyAtmosphere,
                unreal.Vector(0.0, 0.0, 0.0),
                unreal.Rotator(0.0, 0.0, 0.0))
            if sa:
                sa.set_actor_label("SkyAtmosphere_0")
                log("✅ SkyAtmosphere 已创建")
            else:
                log("❌ 创建返回空")
        except Exception as e:
            log("❌ 创建失败: %s" % str(e)[:70])
    else:
        for a in existing:
            log("  已存在: %s" % a.get_name())

    # ── 2. 重新捕获天光 ──
    for a in actors:
        if "SkyLight" not in a.get_class().get_name():
            continue
        for p in ("light_component", "sky_light_component"):
            try:
                lc = a.get_editor_property(p)
            except Exception:
                continue
            if not lc:
                continue
            try:
                lc.set_editor_property("real_time_capture", True)
                lc.recapture_sky()
                log("天光 %s: 已重新捕获天空" % a.get_name())
            except Exception as e:
                log("天光捕获失败: %s" % str(e)[:60])
            break

    # ── 3. 保存 ──
    try:
        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        les.save_current_level()
        log("✅ 关卡已保存")
    except Exception as e:
        log("保存失败: %s" % str(e)[:60])

    log("=" * 60)
    log("完成")


main()
