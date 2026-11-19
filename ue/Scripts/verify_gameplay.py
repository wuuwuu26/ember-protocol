"""
余火协议 · 端到端验证
================================================
在 UE 内检查整个游戏链路是否完整可跑。

用法:
    UnrealEditor-Cmd.exe <项目> -unattended -nopause -nosplash \
      -ExecutePythonScript="<本文件>" -log

检查项:
  A. 部位映射表：规则数、标签有效性、致命部位
  B. 机体数据资产：三条约束、网格绑定
  C. 类默认值：CDO 上的关键引用是否就位
  D. 输入系统：Action 与 MappingContext 是否创建成功
  E. 测试关卡：资产存在、Actor 数量
  F. 类可加载性
"""

import unreal

PASS, FAIL = "OK", "FAIL"
_results = []


def log(msg):
    unreal.log("[验证] %s" % msg)
    print("[验证] %s" % msg)


def check(label, ok, detail=""):
    _results.append((label, ok))
    mark = "OK  " if ok else "FAIL"
    log("  [%s] %-42s %s" % (mark, label, detail))
    return ok


def tag_str(tag):
    for prop in ("tag_name", "TagName"):
        try:
            return str(tag.get_editor_property(prop))
        except Exception:
            continue
    return str(tag)


def load(path):
    try:
        return unreal.EditorAssetLibrary.load_asset(path)
    except Exception:
        return None


# ─────────────────────────────────────────────
# A. 部位映射表
# ─────────────────────────────────────────────

def check_part_maps():
    log("A. 部位映射表")
    for name, path in (("玩家", "/Game/RobotGame/Data/Enemies/DA_PartMap_Player"),
                       ("敌人", "/Game/RobotGame/Data/Enemies/DA_PartMap_Enemy")):
        pm = load(path)
        if not check("%s部位表存在" % name, pm is not None, path):
            continue
        rules = pm.get_editor_property("rules")
        check("%s规则数 = 6" % name, len(rules) == 6, "实际 %d" % len(rules))

        bad = [r for r in rules if not tag_str(r.get_editor_property("part_tag"))]
        check("%s所有规则标签非空" % name, len(bad) == 0,
              "空标签 %d 条" % len(bad))

        kill_count = sum(1 for r in rules
                         if r.get_editor_property("destruction_kills"))
        check("%s恰有 1 个致命部位" % name, kill_count == 1,
              "致命部位 %d 个" % kill_count)

        prefixes_ok = all(len(r.get_editor_property("bone_prefixes")) > 0
                          for r in rules)
        check("%s所有规则都有骨骼前缀" % name, prefixes_ok)

        if name == "敌人":
            detail = ", ".join(tag_str(r.get_editor_property("part_tag"))
                               for r in rules)
            log("       敌人部位：%s" % detail)


# ─────────────────────────────────────────────
# B. 机体数据资产
# ─────────────────────────────────────────────

CHASSIS_EXPECT = {
    "Light": (1.0, 60.0, 34.0),
    "Medium": (1.5, 100.0, 22.0),
    "Heavy": (2.4, 140.0, 13.0),
}


def check_chassis():
    log("B. 机体数据资产")
    for key, (mass, power, diss) in CHASSIS_EXPECT.items():
        a = load("/Game/RobotGame/Data/Chassis/DA_Chassis_%s" % key)
        if not check("%s 存在" % key, a is not None):
            continue
        check("%s 质量 = %.1f" % (key, mass),
              abs(a.get_editor_property("mass") - mass) < 0.01)
        check("%s 供电 = %.0f" % (key, power),
              abs(a.get_editor_property("power_capacity") - power) < 0.01)
        check("%s 散热 = %.0f" % (key, diss),
              abs(a.get_editor_property("heat_dissipation") - diss) < 0.01)
        mesh = a.get_editor_property("chassis_mesh")
        check("%s 机体网格已绑定" % key, mesh is not None)


# ─────────────────────────────────────────────
# C. 类默认值
# ─────────────────────────────────────────────

def bp_cdo(bp_path):
    bp = load(bp_path)
    if not bp:
        return None
    try:
        return unreal.get_default_object(bp.generated_class())
    except Exception:
        return None


def check_blueprints():
    log("C. 蓝图默认值（C++ CDO 无法持久化，所以配置在蓝图里）")

    cdo = bp_cdo("/Game/RobotGame/Blueprints/BP_RobotCharacter")
    if check("BP_RobotCharacter 存在", cdo is not None):
        check("  PartMap 已配",
              cdo.get_editor_property("part_map") is not None)
        presets = cdo.get_editor_property("chassis_presets")
        check("  机体预设 = 3", len(presets) == 3, "实际 %d" % len(presets))
        abilities = cdo.get_editor_property("default_abilities")
        check("  默认技能 = 2", len(abilities) == 2, "实际 %d" % len(abilities))

    cdo = bp_cdo("/Game/RobotGame/Blueprints/BP_Enemy")
    if check("BP_Enemy 存在", cdo is not None):
        check("  PartMap 已配", cdo.get_editor_property("part_map") is not None)
        check("  ProjectileClass 已配",
              cdo.get_editor_property("projectile_class") is not None)
        check("  SalvageClass 已配",
              cdo.get_editor_property("salvage_class") is not None)

    cdo = bp_cdo("/Game/RobotGame/Blueprints/BP_RobotGameMode")
    if check("BP_RobotGameMode 存在", cdo is not None):
        pawn = cdo.get_editor_property("default_pawn_class")
        check("  默认 Pawn 指向玩家蓝图",
              pawn is not None and "RobotCharacter" in str(pawn))

    for n in ("BP_Projectile", "BP_Salvage"):
        check("%s 存在" % n,
              unreal.EditorAssetLibrary.does_asset_exist(
                  "/Game/RobotGame/Blueprints/%s" % n))


# ─────────────────────────────────────────────
# D. 输入系统
# ─────────────────────────────────────────────

def check_input():
    log("D. 输入系统（在 C++ 构造函数里创建，不依赖资产）")
    cdo = bp_cdo("/Game/RobotGame/Blueprints/BP_RobotCharacter")
    if not cdo:
        check("读取输入配置", False, "蓝图不可用")
        return

    for prop, label in (("move_action", "Move"),
                        ("look_action", "Look"),
                        ("fire_action", "Fire"),
                        ("dash_action", "Dash"),
                        ("cycle_chassis_action", "CycleChassis"),
                        ("default_mapping_context", "MappingContext")):
        v = cdo.get_editor_property(prop)
        check("输入 %s 已创建" % label, v is not None)

    imc = cdo.get_editor_property("default_mapping_context")
    check("MappingContext 已创建", imc is not None)

    # UInputMappingContext::Mappings 是 protected，Python 读不到，
    # 改用 C++ 侧暴露的访问器。注意：UFUNCTION 直接当方法调用，
    # 不是 call_method() —— 用后者会报 "Failed to find function"。
    n = None
    try:
        n = cdo.get_input_mapping_count()
    except Exception as e:
        check("按键映射条数", False, str(e)[:60])
    if n is not None:
        # 10 条 = 移动 D/A/W/S 4 + 鼠标 1 + 左键 1 + 空格 1 + 机体切换 1/2/3 三条
        check("按键映射 = 10 条", n == 10, "实际 %d" % n)


# ─────────────────────────────────────────────
# E. 测试关卡
# ─────────────────────────────────────────────

def check_level():
    log("E. 测试关卡")
    path = "/Game/RobotGame/Maps/Persistent/L_TestArena"
    exists = unreal.EditorAssetLibrary.does_asset_exist(path)
    check("L_TestArena 存在", exists, path)
    if not exists:
        return

    try:
        actors = unreal.EditorLevelLibrary.get_all_level_actors()
        counts = {}
        for a in actors:
            n = a.get_class().get_name()
            counts[n] = counts.get(n, 0) + 1
        check("关卡含 PlayerStart", counts.get("PlayerStart", 0) >= 1)
        enemy_n = sum(v for k, v in counts.items() if "Enemy" in k)
        check("关卡含敌人实例", enemy_n >= 5, "%d 个" % enemy_n)
        check("关卡含 StaticMeshActor", counts.get("StaticMeshActor", 0) >= 40,
              "%d 个" % counts.get("StaticMeshActor", 0))
        check("关卡含光照", counts.get("DirectionalLight", 0) >= 1)
    except Exception as e:
        check("关卡 Actor 统计", False, str(e)[:60])


# ─────────────────────────────────────────────
# F. 类可加载性
# ─────────────────────────────────────────────

def check_classes():
    log("F. 类可加载性")
    for n in ("RobotCharacter", "RobotEnemy", "RobotProjectile",
              "SalvagePickup", "RobotGameMode", "PartMapData",
              "RobotChassisData", "RobotModuleData", "PartDamageComponent",
              "RobotAttributeSet"):
        check("unreal.%s" % n, hasattr(unreal, n))


# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────

def main():
    log("=" * 68)
    log("端到端验证")
    log("=" * 68)
    check_classes()
    check_part_maps()
    check_chassis()
    check_blueprints()
    check_input()
    check_level()

    total = len(_results)
    passed = sum(1 for _, ok in _results if ok)
    failed = [(l, ) for l, ok in _results if not ok]

    log("")
    log("=" * 68)
    log("通过 %d / %d" % (passed, total))
    if failed:
        log("失败项：")
        for (l, ) in failed:
            log("  - %s" % l)
        log("结论：存在未通过项 ❌")
    else:
        log("结论：全部通过 ✅ 游戏链路完整可跑")
    log("=" * 68)


main()
