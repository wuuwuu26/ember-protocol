# -*- coding: utf-8 -*-
"""扩展场景 —— 骨架版（第一百零一轮）

目标：在现有竞技场的远墙（X=1800）上开一个门洞，用通道接出去，
展开第二个战斗场地。本脚本只做"骨架"：地面、围墙、门洞、灯光。

坐标约定（沿用 L_TestArena 的既有约定）：
  +X = 竞技场的"前方"（玩家出生在 -1300，敌人朝 +X 排开）
  地面块 SM_Env_Floor 是 400x400，minZ=-30，摆放时 z=-12，顶面在 z≈0
  墙段 sm_wall_segment 是 412 长 x 90 厚 x 396 高，沿 Y 铺需要 yaw=90
  ⚠️ 只删除本脚本自己生成的 actor（按 tag 标记），绝不碰原有内容
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ENV = "/Game/RobotGame/Art/Environment"
TAG = "ExtRegion"          # 本脚本生成的所有 actor 都带这个 tag，便于重复执行时精确清理

# ── 布局参数（cm）──
X_GATE = 1800.0            # 现有远墙位置（门洞开在这里）
GATE_HALF = 400.0          # 门洞半宽 → 洞宽 800
X_TUNNEL_END = 2400.0      # 通道结束 / 新区域开始
X_NEW_FAR = 5400.0         # 新区域远端（封闭闸门）
Y_NEW_HALF = 900.0         # 新区域半宽（总宽 1800）

log_lines = []


def log(m):
    unreal.log("[ExtScene] %s" % m)
    log_lines.append(str(m))


def load_mesh(name):
    p = "%s/%s" % (ENV, name)
    a = unreal.EditorAssetLibrary.load_asset(p)
    if not a:
        log("!! 资产缺失 %s" % p)
    return a


def spawn(mesh, loc, yaw=0.0, scale=None, tag_extra=None, mats=None):
    """生成一个 StaticMeshActor，打上 TAG。返回 actor。

    ⚠️ 第一百零二轮踩的坑：不设材质覆盖时，StaticMeshActor 会回落到网格的
    默认材质。SM_Env_Floor 的槽 0 是引擎的 BasicShapeMaterial（纯白），
    于是新铺的地面在暗场里反光成刺眼的白线（实测截图里那条 400 网格线）。
    原有 56 块地面每块都显式设了 [M_Steel, M_SteelLight, M_Joint, M_Copper]，
    新块必须一模一样地设。
    """
    a = unreal.EditorActorSubsystem().spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(float(loc[0]), float(loc[1]), float(loc[2])),
        unreal.Rotator(0.0, float(yaw), 0.0))
    if not a:
        log("!! spawn 失败 %s" % (loc,))
        return None
    c = a.static_mesh_component
    c.set_mobility(unreal.ComponentMobility.STATIC)
    c.set_static_mesh(mesh)
    if mats:
        c.set_editor_property("override_materials", list(mats))
    if scale:
        a.set_actor_scale3d(unreal.Vector(*scale))
    tags = [TAG]
    if tag_extra:
        tags.append(tag_extra)
    a.set_editor_property("tags", tags)
    return a


def clear_previous(actor_sub):
    """只删本脚本生成过的**几何** actor（带 ExtRegion tag）。

    ⚠️ 第一百零二轮踩的坑：灯也带 ExtRegion tag，重跑几何脚本时把灯一起删了，
    结果灯一盏都不剩（probe 报"扩建灯 0 盏"），画面看着像"灯不亮"。
    这里跳过所有带 ExtLight_ tag 的 actor —— 灯由 build_ext_lights.py 单独管理。
    """
    killed = 0
    for a in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        try:
            tags = [str(t) for t in a.get_editor_property("tags")]
        except Exception:
            continue
        if any(t.startswith("ExtLight_") for t in tags):
            continue          # 灯归 build_ext_lights.py 管，这里不碰
        if TAG in tags:
            actor_sub.destroy_actor(a)
            killed += 1
    log("清理旧扩建几何 %d 个" % killed)


def main():
    actor_sub = unreal.EditorActorSubsystem()
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(LEVEL)
    clear_previous(actor_sub)

    floor = load_mesh("SM_Env_Floor")
    wall = load_mesh("sm_wall_segment")
    corner = load_mesh("sm_wall_corner")
    doorframe = load_mesh("SM_Env_Doorframe")
    gantry = load_mesh("SM_Env_Gantry")
    pillar = load_mesh("SM_Env_Pillar")

    if not (floor and wall and corner):
        log("!! 核心资产缺失，中止")
        return

    # 地面材质必须与原区域一致（否则回落到白色 BasicShapeMaterial）
    def load_mat(n):
        return unreal.EditorAssetLibrary.load_asset(ENV + "/" + n)

    floor_mats = [load_mat("M_Steel"), load_mat("M_SteelLight"),
                  load_mat("M_Joint"), load_mat("M_Copper")]
    # 其余构件沿用原关卡里同名构件的材质槽顺序（实测值，见 docs/ext_mats.txt）
    wall_mats = [load_mat("M_Steel"), load_mat("M_Joint"), load_mat("M_Copper"),
                 load_mat("M_SteelLight"), load_mat("M_Accent_wall")]
    corner_mats = [load_mat("M_Steel"), load_mat("M_SteelLight"), load_mat("M_Joint"),
                   load_mat("M_Core_wall"), load_mat("M_Accent_wall")]
    pillar_mats = [load_mat("M_Steel"), load_mat("M_Accent_prop"), load_mat("M_Copper"),
                   load_mat("M_Joint"), load_mat("M_SteelLight")]
    gantry_mats = [load_mat("M_Steel"), load_mat("M_Joint"), load_mat("M_Accent_prop"),
                   load_mat("M_SteelLight"), load_mat("M_Copper")]
    door_mats = [load_mat("M_Steel"), load_mat("M_Accent_prop"),
                 load_mat("M_Core_prop"), load_mat("M_Joint")]
    log("材质槽已按原关卡对齐")

    # ────────────────────────────────────────────
    # 1. 地面：通道 + 新区域
    #    地面块 400x400，中心对齐到 400 的整数倍
    #    通道：X 1800..2400（1 列），Y -400..400
    #    新区域：X 2400..5400，Y -1000..1000
    # ────────────────────────────────────────────
    n_floor = 0
    for ix in range(5, 15):          # 中心 x = 2000 .. 5600（覆盖 1800..5800）
        for iy in range(-3, 4):      # 中心 y = -1200 .. 1200
            cx = ix * 400.0
            cy = iy * 400.0
            # 通道段只铺中间三块（y -400..400）
            if cx < X_TUNNEL_END and abs(cy) > 400.0:
                continue
            # 新区域：Y 限制在 ±1000 内 → |cy| <= 1000
            if cx >= X_TUNNEL_END and abs(cy) > 1000.0:
                continue
            if spawn(floor, (cx, cy, -12.0), mats=floor_mats):
                n_floor += 1
    log("地面块 %d 个（通道 + 新区域）" % n_floor)

    # ────────────────────────────────────────────
    # 2. 通道侧墙：X 1800..2400，Y = ±400
    #    墙段 412 长，一段刚好覆盖半径 206 → 放 2 段覆盖 824 长
    # ────────────────────────────────────────────
    n_tw = 0
    for x in (2000.0, 2200.0):
        for y in (-400.0, 400.0):
            if spawn(wall, (x, y, 0.0), 90.0, mats=wall_mats):
                n_tw += 1
    log("通道侧墙 %d 段" % n_tw)

    # ────────────────────────────────────────────
    # 3. 新区域围墙
    #    南北墙：Y = ±900，X 2400..5400
    #    东墙（封闭闸门）：X = 5400
    #    西侧：贴着通道出口，除门洞外要补墙
    # ────────────────────────────────────────────
    n_w = 0
    # 南北墙（沿 X 铺，每 400 一段）
    x = 2600.0
    while x <= 5200.0 + 1.0:
        for y in (-Y_NEW_HALF, Y_NEW_HALF):
            if spawn(wall, (x, y, 0.0), 0.0, mats=wall_mats):
                n_w += 1
        x += 400.0
    # 东墙（封闭闸门，沿 Y 铺）
    for y in (-800.0, -400.0, 0.0, 400.0, 800.0):
        if spawn(wall, (X_NEW_FAR, y, 0.0), 90.0, mats=wall_mats):
            n_w += 1
    log("新区域围墙 %d 段" % n_w)

    # ────────────────────────────────────────────
    # 4. 西侧过渡墙（新区域靠通道那一头）
    #    Y 从 ±400 到 ±900 的两段
    # ────────────────────────────────────────────
    n_ww = 0
    for y in (-650.0, 650.0):
        if spawn(wall, (X_TUNNEL_END, y, 0.0), 90.0, mats=wall_mats):
            n_ww += 1
    log("西侧过渡墙 %d 段" % n_ww)

    # ────────────────────────────────────────────
    # 5. 门洞：在远墙 X=1800 上开门
    #    原远墙有 7 段（y = -1200..1200，每 400 一段，中心在 i*STEP）
    #    要开口 |y| < 400，即中间 3 段（y=-400,0,400）必须移除
    #    ⚠️ 这些是原有 actor，不能删！改为把门洞位置的三段"移走"？
    #       不行 —— 只能在门洞两侧补齐，并接受原墙挡住。
    #       正确做法：先检查原远墙的实际分段，再决定是否需要重建那面墙。
    # ────────────────────────────────────────────
    existing_far = []
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_class().get_name() != "StaticMeshActor":
            continue
        try:
            c = a.static_mesh_component
            m = c.get_editor_property("static_mesh") if c else None
        except Exception:
            continue
        if not m or "wall_segment" not in m.get_name().lower():
            continue
        loc = a.get_actor_location()
        if abs(loc.x - X_GATE) < 60.0:
            existing_far.append((loc.x, loc.y, loc.z, a))
    existing_far.sort(key=lambda t: t[1])
    log("原远墙段 %d 个，Y = %s"
        % (len(existing_far), ", ".join("%.0f" % t[1] for t in existing_far)))

    # 打 tag 以便后续（门洞那几段需要被本脚本管理）
    for (fx, fy, fz, a) in existing_far:
        if abs(fy) <= GATE_HALF:
            try:
                tags = [str(t) for t in a.get_editor_property("tags")]
            except Exception:
                tags = []
            if TAG not in tags:
                tags.append(TAG)
            a.set_editor_property("tags", tags)
            actor_sub.destroy_actor(a)
            log("  移除门洞位置的墙段 y=%.0f" % fy)

    # 门框装饰
    if doorframe:
        for y in (-GATE_HALF - 20.0, GATE_HALF + 20.0):
            spawn(doorframe, (X_GATE, y, 0.0), 0.0, mats=door_mats)
        log("门框 2 个")

    # ────────────────────────────────────────────
    # 6. 立柱 + 龙门架：给新区域一点纵向层次
    # ────────────────────────────────────────────
    n_p = 0
    if pillar:
        for x in (2800.0, 3400.0, 4000.0, 4600.0, 5200.0):
            for y in (-840.0, 840.0):
                if spawn(pillar, (x, y, -140.0), mats=pillar_mats):
                    n_p += 1
    log("立柱 %d 根" % n_p)

    n_g = 0
    if gantry:
        for x in (3200.0, 4400.0):
            if spawn(gantry, (x, 0.0, 0.0), 0.0, mats=gantry_mats):
                n_g += 1
    log("龙门架 %d 座" % n_g)

    les.save_current_level()
    log("已保存关卡")
    with open(r"C:\Users\25227\Documents\robot_game\docs\ext_build.txt", "wb") as f:
        f.write("\n".join(log_lines).encode("utf-8"))
    unreal.log("EXT_SCENE_DONE")


main()
