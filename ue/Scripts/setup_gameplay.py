"""
余火协议 · 游戏配置脚本
================================================
在 UE 编辑器里跑，完成：
  1. 创建部位映射表（玩家 / 敌人各一套）
  2. 创建三台机体的数据资产
  3. 创建蓝图子类并把默认值写进去
  4. 生成可玩测试关卡

用法（编辑器关闭时）:
    UnrealEditor-Cmd.exe <项目> -unattended -nopause -nosplash \
      -ExecutePythonScript="<本文件>" -log

⚠️ 两个踩过的坑，改动前务必先读:

  1. 不要往 C++ 类的 CDO 写默认值。
     C++ 类的 CDO 是编译产物、不是资产，改了无法持久化到磁盘 ——
     脚本跑完看着成功，下次打开全是空的。必须用蓝图子类。

  2. 不要在脚本里构造 FGameplayTag。
     UE 的 Python 绑定把 tag_name 设成了只读，构造出来全是空标签，
     部位系统会静默失效。规则内容改由 C++ 的 BuildDefaultRules() 填充。
"""

import unreal

# ─────────────────────────────────────────────
# 路径
# ─────────────────────────────────────────────

DIR_DATA_CHASSIS = "/Game/RobotGame/Data/Chassis"
DIR_DATA_ENEMY = "/Game/RobotGame/Data/Enemies"
DIR_BP = "/Game/RobotGame/Blueprints"
DIR_MAPS = "/Game/RobotGame/Maps/Persistent"
DIR_CHAR = "/Game/RobotGame/Art/Characters"
DIR_ENV = "/Game/RobotGame/Art/Environment"
DIR_PROPS = "/Game/RobotGame/Art/Props"

LEVEL_PATH = DIR_MAPS + "/L_TestArena"

CHASSIS_MESHES = {
    "Light": DIR_CHAR + "/SK_Chassis_Light",
    "Medium": DIR_CHAR + "/SK_Chassis_Medium",
    "Heavy": DIR_CHAR + "/SK_Chassis_Heavy",
}


def log(msg):
    unreal.log("[配置] %s" % msg)
    print("[配置] %s" % msg)


def warn(msg):
    unreal.log_warning("[配置] %s" % msg)
    print("[配置][警告] %s" % msg)


# ─────────────────────────────────────────────
# 工具
# ─────────────────────────────────────────────

def asset_tools():
    return unreal.AssetToolsHelpers.get_asset_tools()


def load(path):
    try:
        return unreal.EditorAssetLibrary.load_asset(path)
    except Exception:
        return None


def save(asset):
    try:
        unreal.EditorAssetLibrary.save_loaded_asset(asset)
    except Exception as e:
        warn("保存失败: %s" % e)


def create_data_asset(name, path, cls):
    full = "%s/%s" % (path, name)
    if unreal.EditorAssetLibrary.does_asset_exist(full):
        return load(full)
    factory = unreal.DataAssetFactory()
    try:
        factory.set_editor_property("data_asset_class", cls)
    except Exception as e:
        warn("设置 data_asset_class 失败: %s" % e)
    try:
        return asset_tools().create_asset(name, path, cls, factory)
    except Exception as e:
        warn("创建 %s 失败: %s" % (full, e))
        return None


def create_blueprint(name, parent_class):
    full = "%s/%s" % (DIR_BP, name)
    existing = load(full)
    if existing:
        return existing
    factory = unreal.BlueprintFactory()
    try:
        factory.set_editor_property("parent_class", parent_class)
    except Exception as e:
        warn("设置 parent_class 失败: %s" % e)
        return None
    try:
        bp = asset_tools().create_asset(name, DIR_BP, None, factory)
        return bp
    except Exception as e:
        warn("创建蓝图 %s 失败: %s" % (full, e))
        return None


def bp_class(bp):
    """取蓝图生成的类，用于在关卡里生成实例。"""
    if not bp:
        return None
    try:
        return unreal.EditorAssetLibrary.load_blueprint_class(
            "%s/%s" % (DIR_BP, bp.get_name()))
    except Exception:
        pass
    try:
        return bp.generated_class()
    except Exception:
        return None


def set_bp_defaults(bp, **props):
    """在蓝图 CDO 上设置默认值并保存。

    C++ 类的 CDO 改了不落盘，蓝图 CDO 改了会随蓝图资产一起保存 ——
    这就是必须走蓝图的原因。
    """
    if not bp:
        return 0
    try:
        cdo = unreal.get_default_object(bp.generated_class())
    except Exception as e:
        warn("  取蓝图 CDO 失败: %s" % e)
        return 0

    ok = 0
    for k, v in props.items():
        try:
            cdo.set_editor_property(k, v)
            ok += 1
        except Exception as e:
            warn("  %s.%s 赋值失败: %s" % (bp.get_name(), k, str(e)[:70]))

    try:
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    except Exception:
        pass
    save(bp)
    return ok


def tag_str(tag):
    for prop in ("tag_name", "TagName"):
        try:
            return str(tag.get_editor_property(prop))
        except Exception:
            continue
    return str(tag)


# ─────────────────────────────────────────────
# 1. 部位映射表
# ─────────────────────────────────────────────

def create_part_maps():
    log("创建部位映射表...")

    pm_player = create_data_asset("DA_PartMap_Player", DIR_DATA_ENEMY,
                                  unreal.PartMapData)
    if pm_player:
        pm_player.build_default_rules(True)
        save(pm_player)

    pm_enemy = create_data_asset("DA_PartMap_Enemy", DIR_DATA_ENEMY,
                                 unreal.PartMapData)
    if pm_enemy:
        pm_enemy.build_default_rules(False)
        save(pm_enemy)

    for pm, label in ((pm_player, "玩家"), (pm_enemy, "敌人")):
        if not pm:
            warn("  %s部位表创建失败" % label)
            continue
        try:
            rules = pm.get_editor_property("rules")
            detail = ", ".join(
                "%s(hp=%.0f%s)"
                % (tag_str(r.get_editor_property("part_tag")),
                   r.get_editor_property("max_health"),
                   ",致命" if r.get_editor_property("destruction_kills") else "")
                for r in rules)
            log("  %s部位表 %d 条：%s" % (label, len(rules), detail))
        except Exception as e:
            warn("  %s部位表读取失败: %s" % (label, e))

    return pm_player, pm_enemy


# ─────────────────────────────────────────────
# 2. 机体数据资产
# ─────────────────────────────────────────────

CHASSIS_PARAMS = {
    "Light": dict(name="轻型侦察", cls=unreal.ChassisClass.LIGHT,
                  mass=1.0, power=60.0, diss=34.0, regen=9.0),
    "Medium": dict(name="中型通用", cls=unreal.ChassisClass.MEDIUM,
                   mass=1.5, power=100.0, diss=22.0, regen=13.0),
    "Heavy": dict(name="重型攻坚", cls=unreal.ChassisClass.HEAVY,
                  mass=2.4, power=140.0, diss=13.0, regen=17.0),
}


def create_chassis_assets():
    log("创建机体数据资产...")
    out = {}
    for key, p in CHASSIS_PARAMS.items():
        asset = create_data_asset("DA_Chassis_%s" % key, DIR_DATA_CHASSIS,
                                  unreal.RobotChassisData)
        if not asset:
            continue
        try:
            asset.set_editor_property("display_name",
                                      unreal.Text.fromstring(p["name"]))
        except Exception:
            pass
        asset.set_editor_property("chassis_class", p["cls"])
        asset.set_editor_property("mass", p["mass"])
        asset.set_editor_property("power_capacity", p["power"])
        asset.set_editor_property("heat_capacity", 100.0)
        asset.set_editor_property("heat_dissipation", p["diss"])
        asset.set_editor_property("power_regen", p["regen"])
        asset.set_editor_property("base_walk_speed", 232.0)
        asset.set_editor_property("dash_power_cost", 22.0)

        mesh = load(CHASSIS_MESHES[key])
        if mesh:
            try:
                asset.set_editor_property("chassis_mesh", mesh)
            except Exception as e:
                warn("  %s 网格绑定失败: %s" % (key, e))
        else:
            warn("  %s 找不到机体网格" % key)

        save(asset)
        out[key] = asset
        log("  DA_Chassis_%-7s 质量 %.1f  供电 %.0f  散热 %.0f"
            % (key, p["mass"], p["power"], p["diss"]))
    return out


# ─────────────────────────────────────────────
# 3. 蓝图子类
# ─────────────────────────────────────────────

def create_blueprints(chassis_map, pm_player, pm_enemy):
    log("创建蓝图子类...")
    out = {}

    # ── 玩家机体 ──
    bp = create_blueprint("BP_RobotCharacter", unreal.RobotCharacter)
    presets = [c for c in (chassis_map.get("Light"),
                           chassis_map.get("Medium"),
                           chassis_map.get("Heavy")) if c]
    props = {"chassis_presets": presets}
    if presets:
        props["default_chassis"] = presets[0]
    if pm_player:
        props["part_map"] = pm_player
    n = set_bp_defaults(bp, **props)
    out["player"] = bp
    log("  BP_RobotCharacter：%d 项默认值（含 %d 个机体预设）" % (n, len(presets)))

    # ── 敌人 ──
    bp = create_blueprint("BP_Enemy", unreal.RobotEnemy)
    props = {"projectile_class": unreal.RobotProjectile,
             "salvage_class": unreal.SalvagePickup}
    if pm_enemy:
        props["part_map"] = pm_enemy
    n = set_bp_defaults(bp, **props)
    out["enemy"] = bp
    log("  BP_Enemy：%d 项默认值" % n)

    # ── 弹丸 ──
    out["projectile"] = create_blueprint("BP_Projectile", unreal.RobotProjectile)
    set_bp_defaults(out["projectile"])
    log("  BP_Projectile")

    # ── 回收物 ──
    out["salvage"] = create_blueprint("BP_Salvage", unreal.SalvagePickup)
    set_bp_defaults(out["salvage"])
    log("  BP_Salvage")

    # ── 游戏模式 ──
    bp = create_blueprint("BP_RobotGameMode", unreal.RobotGameMode)
    player_cls = bp_class(out["player"])
    props = {}
    if player_cls:
        props["default_pawn_class"] = player_cls
        props["robot_character_class"] = player_cls
    n = set_bp_defaults(bp, **props)
    out["gamemode"] = bp
    log("  BP_RobotGameMode：%d 项默认值" % n)

    return out


# ─────────────────────────────────────────────
# 4. 测试关卡
# ─────────────────────────────────────────────

def spawn(actor_sub, cls, loc, rot=(0, 0, 0)):
    if cls is None:
        return None
    try:
        return actor_sub.spawn_actor_from_class(
            cls, unreal.Vector(loc[0], loc[1], loc[2]),
            unreal.Rotator(rot[0], rot[1], rot[2]))
    except Exception as e:
        warn("  生成 %s 失败: %s" % (cls, str(e)[:60]))
        return None


def create_test_level(bps):
    log("生成测试关卡...")

    level_sub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not level_sub or not actor_sub:
        warn("  关卡子系统不可用")
        return False

    # 必须先删掉旧关卡。new_level() 在关卡已存在时会「加载」而不是「新建」，
    # 于是重跑脚本会往已有关卡里再生成一份，敌人和道具数量翻倍。
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        try:
            unreal.EditorAssetLibrary.delete_asset(LEVEL_PATH)
            log("  已删除旧关卡，重建")
        except Exception as e:
            warn("  删除旧关卡失败: %s" % e)

    try:
        level_sub.new_level(LEVEL_PATH)
    except Exception as e:
        warn("  新建关卡失败: %s" % e)
        return False

    # 清掉上一次生成留下的 Actor。
    # new_level() 对已存在的关卡是「加载」而不是「新建」，而 delete_asset 又删不掉
    # 已加载的关卡，所以必须在生成前主动清场 —— 否则每次重跑都叠一份，
    # 敌人数量会 5 → 10 → 15 地涨。
    clear_types = (unreal.StaticMeshActor, unreal.PlayerStart,
                   unreal.DirectionalLight, unreal.SkyLight,
                   unreal.SkyAtmosphere, unreal.ExponentialHeightFog,
                   unreal.PostProcessVolume)
    removed = 0
    try:
        for a in unreal.EditorLevelLibrary.get_all_level_actors():
            cls_name = a.get_class().get_name()
            if isinstance(a, clear_types) or "Enemy" in cls_name:
                actor_sub.destroy_actor(a)
                removed += 1
    except Exception as e:
        warn("  清理旧 Actor 失败: %s" % e)
    if removed:
        log("  清理上次生成的 %d 个 Actor" % removed)

    # 地面：用导入的环境构件平铺，顺便验证资产可用
    floor_mesh = load(DIR_ENV + "/SM_Env_Floor")
    floors = 0
    if floor_mesh:
        for ix in range(-3, 4):
            for iy in range(-3, 4):
                a = spawn(actor_sub, unreal.StaticMeshActor,
                          (ix * 400.0, iy * 400.0, 0.0))
                if a:
                    a.static_mesh_component.set_static_mesh(floor_mesh)
                    floors += 1
    log("  地面 %d 块" % floors)

    spawn(actor_sub, unreal.PlayerStart, (0.0, -700.0, 130.0), (0.0, 90.0, 0.0))

    enemy_cls = bp_class(bps.get("enemy"))
    enemies = 0
    for (x, y) in ((900.0, 0.0), (1200.0, 500.0), (1100.0, -600.0),
                   (1600.0, 200.0), (1500.0, -400.0)):
        if spawn(actor_sub, enemy_cls, (x, y, 140.0)):
            enemies += 1
    log("  敌人 %d 个" % enemies)

    props = 0
    for path, loc in ((DIR_PROPS + "/SM_Prop_Container", (-800.0, 800.0, 60.0)),
                      (DIR_PROPS + "/SM_Prop_Shelf", (700.0, -900.0, 100.0)),
                      (DIR_PROPS + "/SM_Prop_Beacon", (-900.0, -300.0, 105.0))):
        mesh = load(path)
        if not mesh:
            continue
        a = spawn(actor_sub, unreal.StaticMeshActor, loc)
        if a:
            a.static_mesh_component.set_static_mesh(mesh)
            props += 1
    log("  场景道具 %d 个" % props)

    # 🔴 灯光 Mobility 必须设为 Movable，否则场景全黑。
    #
    # UE 的灯光分 Static / Stationary / Movable：
    #   - Static 灯光需要烘焙光照贴图，没有烘焙就完全不贡献照明
    #   - 脚本 spawn_actor_from_class 生成的灯光默认是 Static
    #   - 而且 Static 的天光不允许开 real_time_capture（设了会读回 False）
    #
    # 症状：整个场景只有自发光材质可见，其余一片黑 —— 排查了很久。
    # 用 Movable 就不需要烘焙，代价是性能略高，垂直切片阶段完全可接受。

    def make_movable(actor, label):
        """把灯光组件设为 Movable。"""
        for prop in ("light_component", "directional_light_component",
                     "sky_light_component"):
            try:
                lc = actor.get_editor_property(prop)
            except Exception:
                continue
            if not lc:
                continue
            try:
                lc.set_mobility(unreal.ComponentMobility.MOVABLE)
                log("  %s 已设为 Movable" % label)
            except Exception as e:
                warn("  %s 设 Mobility 失败: %s" % (label, str(e)[:60]))
            return lc
        warn("  %s 找不到灯光组件" % label)
        return None

    atmo_ok = False
    if hasattr(unreal, "SkyAtmosphere"):
        try:
            sa = actor_sub.spawn_actor_from_class(
                unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
            atmo_ok = sa is not None
            log("  大气：%s" % ("已创建" if atmo_ok else "创建返回空"))
        except Exception as e:
            warn("  大气创建失败: %s" % str(e)[:70])
    else:
        warn("  unreal.SkyAtmosphere 不存在，跳过大气")

    sun = spawn(actor_sub, unreal.DirectionalLight,
                (0.0, 0.0, 1500.0), (-48.0, 35.0, 0.0))
    if sun:
        lc = make_movable(sun, "平行光")
        if lc:
            try:
                # 强度提到 100000 lux（真实太阳量级），不依赖自动曝光补偿
                lc.set_editor_property("intensity", 100000.0)
                lc.set_editor_property("atmosphere_sun_light", atmo_ok)
                log("  平行光：100000 lux，大气太阳光=%s" % atmo_ok)
            except Exception as e:
                warn("  平行光配置失败: %s" % str(e)[:70])

    sky = spawn(actor_sub, unreal.SkyLight, (0.0, 0.0, 800.0))
    if sky:
        lc = make_movable(sky, "天光")
        if lc:
            try:
                lc.set_editor_property("intensity", 1.0)
                # 必须实时捕获：没有烘焙的天空贴图时，不实时捕获就没有环境光
                lc.set_editor_property("real_time_capture", True)
                log("  天光：强度 1.0，实时捕获已开")
            except Exception as e:
                warn("  天光配置失败: %s" % str(e)[:70])

    # 后处理体积：显式打开自动曝光，作为工程设置的兜底
    ppv = spawn(actor_sub, unreal.PostProcessVolume, (0.0, 0.0, 600.0))
    if ppv:
        try:
            ppv.set_editor_property("unbound", True)
            st = ppv.get_editor_property("settings")
            st.set_editor_property("override_auto_exposure_method", True)
            st.set_editor_property("auto_exposure_method",
                                   unreal.AutoExposureMethod.AEM_HISTOGRAM)
            st.set_editor_property("override_auto_exposure_min_brightness", True)
            st.set_editor_property("auto_exposure_min_brightness", 0.03)
            st.set_editor_property("override_auto_exposure_max_brightness", True)
            st.set_editor_property("auto_exposure_max_brightness", 8.0)
            ppv.set_editor_property("settings", st)
            log("  后处理体积：自动曝光已显式打开")
        except Exception as e:
            warn("  后处理体积配置失败: %s" % str(e)[:70])

    spawn(actor_sub, unreal.ExponentialHeightFog, (0.0, 0.0, 0.0))

    try:
        level_sub.save_current_level()
        log("  关卡已保存：%s" % LEVEL_PATH)
    except Exception as e:
        warn("  保存关卡失败: %s" % e)
    return True


# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────

def main():
    log("=" * 62)
    log("游戏配置开始")
    log("=" * 62)

    for d in (DIR_DATA_CHASSIS, DIR_DATA_ENEMY, DIR_BP, DIR_MAPS):
        try:
            unreal.EditorAssetLibrary.make_directory(d)
        except Exception:
            pass

    pm_player, pm_enemy = create_part_maps()
    chassis_map = create_chassis_assets()
    bps = create_blueprints(chassis_map, pm_player, pm_enemy)
    ok = create_test_level(bps)

    log("=" * 62)
    log("完成。测试关卡：%s" % ("已生成" if ok else "生成失败"))
    log("打开 %s 后按 Play 试玩：" % LEVEL_PATH)
    log("  WASD 移动 / 鼠标 视角 / 左键 射击 / 空格 冲刺 / 1-2-3 切换机体")
    log("=" * 62)


main()
