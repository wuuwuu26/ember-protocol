# -*- coding: utf-8 -*-
"""扩展区域灯光与氛围（第一百零二轮）

上一步只做了骨架，新区域没有灯 —— 夜里一片死黑，远处地面接缝的反光
反而被衬成刺眼的白线。这里补一套照明骨架：

  1. 沿通道两侧各一盏低强度点光（引导视线走向新区域）
  2. 新区域主灯：两盏高挂点光 + 一盏冷色补光
  3. 门洞处一盏暖色门灯（把"入口"做出来）
  4. 远端闸门一盏警示色灯（视觉终点）

全部带 ExtRegion tag，可重复执行。

⚠️ 灯光强度用"坎德拉"（UE5 默认单位），不是老版本的 unitless。
   参考值：室内实用光照 5~20 cd/m²；这里用 PointLight 的 intensity（cd），
   24m² 的房间大约 300~800 cd 能看清，室外竞技场用 1500~4000 cd。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ENV = "/Game/RobotGame/Art/Environment"
TAG = "ExtRegion"

log_lines = []


def log(m):
    unreal.log("[ExtLight] %s" % m)
    log_lines.append(str(m))


def light(loc, color, intensity, radius, name_tag):
    a = unreal.EditorActorSubsystem().spawn_actor_from_class(
        unreal.PointLight,
        unreal.Vector(float(loc[0]), float(loc[1]), float(loc[2])),
        unreal.Rotator(0.0, 0.0, 0.0))
    if not a:
        log("!! 灯生成失败 %s" % (loc,))
        return None
    c = a.point_light_component
    c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    c.set_editor_property("intensity", float(intensity))
    c.set_editor_property("attenuation_radius", float(radius))
    # ⚠️ 第一百零二轮踩的坑：FColor 的构造参数顺序是 (B, G, R, A)，不是 (R,G,B)。
    #    之前按 RGB 传，实测读回来 b=170 g=200 r=255 —— 冷暖色全反了，
    #    冷色灯打出来偏橙，看起来像"没亮"。
    c.set_editor_property("light_color",
                          unreal.Color(int(color[2]), int(color[1]), int(color[0]), 255))
    try:
        # ⚠️ 第一百零二轮：点光源关闭阴影。
        #    关卡里原有 18 盏 + 扩建 27 盏 = 45 盏，全部 cast_shadows=True 时
        #    阴影贴图预算会被打满，表现为"灯加了也看不出亮"。
        #    这些灯只做氛围照明，不需要投射阴影。
        c.set_editor_property("cast_shadows", False)
    except Exception:
        pass
    a.set_editor_property("tags", [TAG, name_tag])
    return a


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(LEVEL)
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # 先删掉上一轮生成的灯（只删名字带 ExtLight_ 的）
    killed = 0
    for a in list(actor_sub.get_all_level_actors()):
        try:
            tags = [str(t) for t in a.get_editor_property("tags")]
        except Exception:
            continue
        if any(t.startswith("ExtLight_") for t in tags):
            actor_sub.destroy_actor(a)
            killed += 1
    log("清理旧灯 %d 盏" % killed)

    COOL = (170, 200, 255)
    WARM = (255, 190, 130)
    AMBER = (255, 150, 70)
    RED = (255, 90, 70)

    n = 0
    # ── 通道：两侧各 3 盏，低强度，贴近墙面 ──
    for x in (1950.0, 2150.0, 2350.0):
        for y in (-330.0, 330.0):
            if light((x, y, 320.0), COOL, 4000.0, 2200.0, "ExtLight_tunnel"):
                n += 1
    log("通道灯 %d 盏" % n)

    # ── 门洞：暖色门灯，强调"入口" ──
    if light((1800.0, 0.0, 340.0), WARM, 3000.0, 2000.0, "ExtLight_gate"):
        n += 1

    # ── 新区域：主照明，六盏高挂 ──
    m = 0
    for x in (2800.0, 3600.0, 4400.0, 5100.0):
        for y in (-600.0, 600.0):
            if light((x, y, 430.0), COOL, 9000.0, 3600.0, "ExtLight_main"):
                m += 1
    log("新区域主灯 %d 盏" % m)

    # ── 新区域：中心冷色补光（压平阴影，避免死角）──
    if light((3900.0, 0.0, 560.0), COOL, 9000.0, 4200.0, "ExtLight_fill"):
        m += 1

    # ── 远端闸门：警示色，视觉终点 ──
    if light((5250.0, 0.0, 430.0), RED, 3000.0, 2000.0, "ExtLight_gate2"):
        m += 1
    log("新区域灯 %d 盏（含补光与闸门灯）" % m)

    # ── 立柱底部小灯：把立柱的"脚"打出来，增加层次 ──
    k = 0
    for x in (2800.0, 3400.0, 4000.0, 4600.0, 5200.0):
        for y in (-840.0, 840.0):
            if light((x, y, 70.0), AMBER, 900.0, 700.0, "ExtLight_pillar"):
                k += 1
    log("立柱脚灯 %d 盏" % k)

    les.save_current_level()
    log("已保存")
    with open(r"C:\Users\25227\Documents\robot_game\docs\ext_light.txt", "wb") as f:
        f.write("\n".join(log_lines).encode("utf-8"))
    unreal.log("EXT_LIGHT_DONE")


main()
