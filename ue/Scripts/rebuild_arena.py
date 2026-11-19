# -*- coding: utf-8 -*-
"""
重建竞技场。

为什么要重建：原来的布局有三个问题
  1. PlayerStart 朝 +Y，而 5 个敌人全在 +X —— 敌人一直在玩家侧后方，看不见
  2. 只有一块平地 + 3 个道具，没有任何高低层次和掩体，看起来"很粗糙"
  3. 敌人最远的在 x=1600，已经超出 7x7 地面范围（地面只铺到 x=1200）

新布局（X = 前方）：
  玩家在 (-1500, 0) 朝 +X；敌人排成扇形在 x=100..1300
  两侧天桥 + 立柱、后方龙门架、两台高台、拱门、地标灯塔
  约 25 个道具做掩体与视觉密度

尺寸都是实测的（见 _probe_sizes.py 的输出），不是猜的。
"""
import unreal

ENV = "/Game/RobotGame/Art/Environment"
PROPS = "/Game/RobotGame/Art/Props"

LOG = []


def log(s):
    LOG.append(s)


def load(path):
    a = unreal.EditorAssetLibrary.load_asset(path)
    if not a:
        log("  ❌ 加载失败 %s" % path)
    return a


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # ── 1. 清掉旧的场景几何 / 敌人 / 出生点（灯光大气保留）──
    kill_types = (unreal.StaticMeshActor, unreal.PlayerStart)
    removed = 0
    for a in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        cn = a.get_class().get_name()
        # 注意：敌人是蓝图实例，类名是 BP_Enemy_C 而不是 RobotEnemy ——
        # 只匹配 "RobotEnemy" 会漏掉它们，每次重建都在累加（踩过，堆到 25 个）
        if isinstance(a, kill_types) or "Enemy" in cn:
            actor_sub.destroy_actor(a)
            removed += 1
    log("清理旧 Actor：%d 个" % removed)

    def spawn_mesh(path, loc, rot=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0)):
        mesh = load(path)
        if not mesh:
            return None
        a = actor_sub.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(*loc), unreal.Rotator(*rot))
        if not a:
            return None
        c = a.static_mesh_component
        try:
            c.set_mobility(unreal.ComponentMobility.MOVABLE)
        except Exception:
            pass
        c.set_static_mesh(mesh)
        if scale != (1.0, 1.0, 1.0):
            a.set_actor_scale3d(unreal.Vector(*scale))
        return a

    floor_mesh = ENV + "/SM_Env_Floor"

    # ── 2. 地面：8 x 7 块 400x400 拼接（顶面贴到 z=0）──
    # 地板 400x400x42，原点 z=-9 → 放在 z=-12 时顶面正好 z≈0
    n = 0
    for ix in range(-3, 5):        # 中心 x = -1200 .. 1600
        for iy in range(-3, 4):    # 中心 y = -1200 .. 1200
            if spawn_mesh(floor_mesh, (ix * 400.0, iy * 400.0, -12.0)):
                n += 1
    log("地面：%d 块（覆盖 x -1400~1800, y -1400~1400）" % n)

    # ── 3. 外围墙 ──
    # 墙 46(x) x 416(y) x 320(z)，底在 z=0
    wall = ENV + "/SM_Env_Wall"
    n = 0
    for iy in range(-3, 4):
        y = iy * 416.0
        if spawn_mesh(wall, (-1300.0, y, 0.0)):          # 玩家背后
            n += 1
        if spawn_mesh(wall, (1800.0, y, 0.0)):           # 远端
            n += 1
    for ix in range(-3, 5):
        x = ix * 416.0
        if spawn_mesh(wall, (x, -1380.0, 0.0), rot=(0.0, 90.0, 0.0)):
            n += 1
        if spawn_mesh(wall, (x, 1380.0, 0.0), rot=(0.0, 90.0, 0.0)):
            n += 1
    log("围墙：%d 段" % n)

    # ── 4. 立柱 + 两侧天桥 ──
    # 柱 110x110x400（底 z=0）；天桥 126x400x130（走道面在 z≈350）
    # 柱放 z=-140 → 顶到 260，与天桥底 220 咬合，看起来是"撑住的"
    pillar = ENV + "/SM_Env_Pillar"
    catwalk = ENV + "/SM_Env_Catwalk"
    n_p = n_c = 0
    for y in (-1000.0, 1000.0):
        for x in (-900.0, -450.0, 0.0, 450.0, 900.0, 1350.0):
            if spawn_mesh(pillar, (x, y, -140.0)):
                n_p += 1
            # 旋转 90° 让天桥的长边沿 X 铺开
            if spawn_mesh(catwalk, (x, y, 247.0), rot=(0.0, 90.0, 0.0)):
                n_c += 1
    log("立柱：%d 根，天桥：%d 段" % (n_p, n_c))

    # ── 5. 两台高台（掩体 + 视觉层次）──
    # 平台 627x627x239，原点 z=-110 → 放在 z=240 时台面 ≈ 250
    platform = ENV + "/SM_Env_Platform"
    n = 0
    for loc in ((1250.0, -1000.0, 240.0), (1250.0, 1000.0, 240.0)):
        if spawn_mesh(platform, loc):
            n += 1
    log("高台：%d 座" % n)

    # ── 6. 龙门架 + 拱门 + 管线（工业感）──
    gantry = ENV + "/SM_Env_Gantry"
    doorframe = ENV + "/SM_Env_Doorframe"
    piperun = ENV + "/SM_Env_Piperun"
    n = 0
    for loc in ((-500.0, -1380.0, 0.0), (-500.0, 1380.0, 0.0),
                (700.0, -1380.0, 0.0), (700.0, 1380.0, 0.0)):
        if spawn_mesh(gantry, loc):
            n += 1
    if spawn_mesh(doorframe, (-1250.0, 0.0, 0.0), rot=(0.0, 90.0, 0.0)):
        n += 1
    if spawn_mesh(doorframe, (1750.0, 0.0, 0.0), rot=(0.0, 90.0, 0.0)):
        n += 1
    # 管线贴着后墙走一圈
    for iy in range(-3, 4):
        if spawn_mesh(piperun, (-1240.0, iy * 400.0, 330.0)):
            n += 1
    log("龙门架/拱门/管线：%d 件" % n)

    # ── 7. 道具：掩体与视觉密度 ──
    # 位置手工挑的，避开玩家出生点 (-1500,0) 与敌人落点
    prop_layout = [
        ("SM_Prop_Container",  (-1100.0, -700.0, 0.0), (0, 0, 0)),
        ("SM_Prop_Container",  (-1100.0, -400.0, 0.0), (0, 0, 0)),
        ("SM_Prop_Container",  (-600.0, 800.0, 0.0), (0, 30, 0)),
        ("SM_Prop_Container",  (300.0, -1000.0, 0.0), (0, -20, 0)),
        ("SM_Prop_Container",  (900.0, 1000.0, 0.0), (0, 15, 0)),
        ("SM_Prop_Container",  (250.0, 950.0, 0.0), (0, 45, 0)),
        ("SM_Prop_Shelf",      (-800.0, 0.0, 0.0), (0, 90, 0)),
        ("SM_Prop_Shelf",      (500.0, 700.0, 0.0), (0, 0, 0)),
        ("SM_Prop_Shelf",      (1000.0, -600.0, 0.0), (0, 90, 0)),
        ("SM_Prop_Beacon",     (-1400.0, -800.0, 0.0), (0, 0, 0)),
        ("SM_Prop_Beacon",     (-1400.0, 800.0, 0.0), (0, 0, 0)),
        ("SM_Prop_Beacon",     (1600.0, 0.0, 0.0), (0, 0, 0)),
        ("SM_Prop_FuelBarrel", (-950.0, 300.0, 0.0), (0, 0, 0)),
        ("SM_Prop_FuelBarrel", (-900.0, 360.0, 0.0), (0, 0, 0)),
        ("SM_Prop_FuelBarrel", (150.0, 850.0, 0.0), (0, 0, 0)),
        ("SM_Prop_FuelBarrel", (1450.0, -300.0, 0.0), (0, 0, 0)),
        ("SM_Prop_Terminal",   (-1200.0, 0.0, 0.0), (0, 0, 0)),
        ("SM_Prop_Terminal",   (700.0, -1200.0, 0.0), (0, 180, 0)),
        ("SM_Prop_SupplyBox",  (-700.0, -900.0, 0.0), (0, 20, 0)),
        ("SM_Prop_SupplyBox",  (-660.0, -880.0, 0.0), (0, 70, 0)),
        ("SM_Prop_ScrapCrate", (-400.0, 500.0, 0.0), (0, 0, 0)),
        ("SM_Prop_ScrapCrate", (-360.0, 540.0, 0.0), (0, 40, 0)),
        ("SM_Prop_Debris",     (250.0, 250.0, 0.0), (0, 0, 0)),
        ("SM_Prop_Debris",     (1100.0, -900.0, 0.0), (0, 60, 0)),
        ("SM_Prop_PipeSegment", (-1300.0, -1100.0, 0.0), (0, 90, 0)),
        ("SM_Prop_PipeSegment", (-1300.0, 1100.0, 0.0), (0, 90, 0)),
        ("SM_Prop_SalvagePod", (600.0, -300.0, 0.0), (0, 0, 0)),
        ("SM_Prop_SalvagePod", (1300.0, 400.0, 0.0), (0, 0, 0)),
    ]
    # 出生点附近 900cm 内不放道具：相机臂有 480cm，太近的道具会糊住整个画面
    SPAWN_XY = (-200.0, 0.0)
    n = skipped = 0
    for name, loc, rot in prop_layout:
        dx = loc[0] - SPAWN_XY[0]
        dy = loc[1] - SPAWN_XY[1]
        if (dx * dx + dy * dy) < 900.0 * 900.0:
            skipped += 1
            continue
        if spawn_mesh("%s/%s" % (PROPS, name), loc, rot):
            n += 1
    log("道具：%d 件（跳过出生点附近 %d 件）" % (n, skipped))

    # ── 8. 地标 ──
    # 暂时不放灯塔：它在正前方渲染成一个巨大的灰色棋盘格方块
    # （资产材质缺失，会渲染成 UE 默认材质），挡住整个视野。
    # 等确认环境资产的材质都齐了再加回来。
    log("地标：本次跳过（灯塔材质缺失，会变成大灰块挡住视野）")

    # ── 9. 出生点：朝 +X（正对竞技场）──
    ps = actor_sub.spawn_actor_from_class(
        unreal.PlayerStart, unreal.Vector(-200.0, 0.0, 130.0),
        unreal.Rotator(0.0, 0.0, 0.0))
    log("出生点：%s（朝 +X；离后墙 1100cm，后墙/拱门/管线都在相机后方）" % ("已创建" if ps else "创建失败"))

    # ── 10. 敌人：扇形排布在玩家正前方 ──
    bp_enemy = unreal.EditorAssetLibrary.load_asset(
        "/Game/RobotGame/Blueprints/BP_Enemy")
    enemy_cls = bp_enemy.generated_class() if bp_enemy else None
    spots = ((400.0, -400.0), (750.0, 300.0), (1050.0, -750.0),
             (1350.0, 650.0), (1550.0, -100.0))
    n = 0
    if enemy_cls:
        for (x, y) in spots:
            if actor_sub.spawn_actor_from_class(
                    enemy_cls, unreal.Vector(x, y, 140.0),
                    unreal.Rotator(0.0, 180.0, 0.0)):
                n += 1
    log("敌人：%d 个（全部在玩家正前方 x=400~1550）" % n)

    les.save_current_level()
    log("关卡已保存")

    for s in LOG:
        print("[竞技场] %s" % s)


main()
