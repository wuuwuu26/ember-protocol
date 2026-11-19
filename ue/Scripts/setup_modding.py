# -*- coding: utf-8 -*-
"""
改装系统的数据配置（一次性）：
  ① 给三台机体配置 9 个插槽（头部/核心/左右臂/左右推进器/背包/辅助×2）
  ② 创建 22 个模块数据资产（来自资产清单.md 的模块库）

背景：模块 MESH（SM_Module_*）早就建好了，但**模块数据资产从未创建**、
机体资产的插槽数组也是空的 —— 也就是说 `CanMount` 永远返回
"该机体没有这个插槽"，整个改装系统在数据层不存在。

数值设计遵循三条约束（质量/供电/散热互相牵制）：
  · 每个模块有质量（拖慢速度）、持续耗电（和冲刺抢电力池）、
    散热/热容修正（影响射击节奏）
  · 供电是硬约束：满配的耗电总和超过机体电力上限时无法装配
  · 玩家默认是"裸机"（速度 232），装模块是有意识的取舍

左右臂/左右推进器共用同一批模块资产（TargetSlot 声明左侧，运行时
CanMount 把左右视为同类槽位，见 AssemblyComponent 的注释）。

用法: bash tools/ue_py.sh ue/Scripts/setup_modding.py "改装数据"
"""
import unreal

CHASSIS_DIR = "/Game/RobotGame/Data/Chassis"
MODULE_DIR = "/Game/RobotGame/Data/Modules"

unreal.log("[改装数据] 开始")


def log(m):
    unreal.log("[改装数据] %s" % m)


# ─────────────────────────────────────────────
# ① 机体插槽
# ─────────────────────────────────────────────

# 直接用 Python 枚举名（UE 的枚举绑定用全大写+下划线）
SLOTS = ["HEAD", "CORE", "ARM_LEFT", "ARM_RIGHT",
         "THRUSTER_LEFT", "THRUSTER_RIGHT", "BACKPACK", "AUX01", "AUX02"]


def set_chassis_slots():
    ok = 0
    for name in ("DA_Chassis_Light", "DA_Chassis_Medium", "DA_Chassis_Heavy"):
        asset = unreal.EditorAssetLibrary.load_asset("%s/%s" % (CHASSIS_DIR, name))
        if not asset:
            log("❌ 找不到机体 %s" % name)
            continue
        try:
            slots_prop = []
            for s in SLOTS:
                d = unreal.ModuleSlotDef()
                d.set_editor_property("slot", getattr(unreal.ModuleSlot, s))
                d.set_editor_property("accepted_module_types",
                                      unreal.GameplayTagContainer())
                slots_prop.append(d)
            asset.set_editor_property("slots", slots_prop)
        except Exception as e:
            log("❌ %s 插槽写入失败: %s" % (name, str(e)[:120]))
            continue
        got = asset.get_editor_property("slots")
        if len(got) != len(SLOTS):
            log("⚠️ %s 回读插槽数=%d" % (name, len(got)))
            continue
        unreal.EditorAssetLibrary.save_loaded_asset(asset)
        log("  [ok] %s 插槽 %d 个" % (name, len(got)))
        ok += 1
    return ok


# ─────────────────────────────────────────────
# ② 模块库（22 个，来自资产清单.md）
# ─────────────────────────────────────────────

# 资产名, 显示名, 槽位, 类型标签, 质量, 耗电, 散热修正, 热容修正
MODULES = [
    # 头部（3）
    ("MOD_Head_Scout",     "侦察头",     "HEAD",     "Module.Head",     0.15, 2.0,  0.0,  0.0),
    ("MOD_Head_Standard",  "标准头",     "HEAD",     "Module.Head",     0.20, 0.0,  0.0,  0.0),
    ("MOD_Head_Heavy",     "重装头",     "HEAD",     "Module.Head",     0.35, 1.0,  0.0,  8.0),
    # 核心（3）
    ("MOD_Core_Standard",  "标准核心",   "CORE",     "Module.Core",     0.40, 0.0,  0.0, 10.0),
    ("MOD_Core_Output",    "高输出核心", "CORE",     "Module.Core",     0.50, 0.0, -4.0,  6.0),
    ("MOD_Core_Thermal",   "高散热核心", "CORE",     "Module.Core",     0.45, 3.0, 12.0,  0.0),
    # 武器臂（5，左右通用）。末三列是武器乘数（伤害/间隔/积热）——
    # 机体给"档位"，武器臂做乘法（左右叠乘）
    ("MOD_Arm_Mining",     "采矿臂",     "ARM_LEFT",  "Module.Arm",      0.45, 4.0,  0.0,  0.0, 0.75, 0.70, 0.70),
    ("MOD_Arm_Cannon",     "加农臂",     "ARM_LEFT",  "Module.Arm",      0.60, 6.0, -2.0,  0.0, 1.45, 1.40, 1.35),
    ("MOD_Arm_Shield",     "盾臂",       "ARM_LEFT",  "Module.Arm",      0.50, 3.0,  4.0,  0.0, 1.00, 1.00, 1.00),
    ("MOD_Arm_Grapple",    "钩索臂",     "ARM_LEFT",  "Module.Arm",      0.35, 2.0,  0.0,  0.0, 1.00, 1.00, 1.00),
    ("MOD_Arm_Welder",     "焊枪臂",     "ARM_LEFT",  "Module.Arm",      0.40, 5.0,  3.0,  0.0, 0.90, 0.95, 0.90),
    # 推进器（4，左右通用）
    ("MOD_Thr_Standard",   "标准推进器", "THRUSTER_LEFT", "Module.Thruster", 0.30, 0.0, 0.0, 0.0),
    ("MOD_Thr_Rapid",      "高速推进器", "THRUSTER_LEFT", "Module.Thruster", 0.25, 2.0, -2.0, 0.0),
    ("MOD_Thr_Quad",       "重型四足",   "THRUSTER_LEFT", "Module.Thruster", 0.50, 1.0,  0.0,  6.0),
    ("MOD_Thr_Magnetic",   "磁吸攀爬足", "THRUSTER_LEFT", "Module.Thruster", 0.40, 3.0,  0.0,  0.0),
    # 背包（4）
    ("MOD_Pack_Ammo",      "弹药背包",   "BACKPACK", "Module.Backpack", 0.30, 0.0,  0.0,  0.0),
    ("MOD_Pack_Thermal",   "散热背包",   "BACKPACK", "Module.Backpack", 0.35, 2.0, 15.0,  0.0),
    ("MOD_Pack_Sensor",    "传感器背包", "BACKPACK", "Module.Backpack", 0.25, 4.0,  0.0,  0.0),
    ("MOD_Pack_Battery",   "电池背包",   "BACKPACK", "Module.Backpack", 0.40, 0.0,  6.0,  4.0),
    # 辅助（3）
    ("MOD_Aux_Radar",      "雷达",       "AUX01",    "Module.Aux",      0.15, 3.0,  1.0,  0.0),
    ("MOD_Aux_ShieldGen",  "护盾发生器", "AUX01",    "Module.Aux",      0.30, 8.0,  0.0,  0.0),
    ("MOD_Aux_Repair",     "维修臂",     "AUX01",    "Module.Aux",      0.25, 5.0,  3.0,  0.0),
]


def make_module(entry):
    name, disp, slot, mtype, mass, draw, diss, cap = entry[:8]
    dmg_m = entry[8] if len(entry) > 8 else 1.0
    itv_m = entry[9] if len(entry) > 9 else 1.0
    heat_m = entry[10] if len(entry) > 10 else 1.0
    full = "%s/%s" % (MODULE_DIR, name)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    if unreal.EditorAssetLibrary.does_asset_exist(full):
        asset = unreal.EditorAssetLibrary.load_asset(full)
    else:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property("data_asset_class", unreal.RobotModuleData)
        asset = tools.create_asset(name, MODULE_DIR,
                                   unreal.RobotModuleData, factory)
    if not asset:
        log("❌ %s 创建失败" % name)
        return False
    try:
        asset.set_editor_property("display_name", unreal.Text(disp))
        asset.set_editor_property("target_slot",
                                  getattr(unreal.ModuleSlot, slot))
        # 模块"类型"标签（GameplayTag）在 Python 侧无法构造（tag_name 只读），
        # 留空即可 —— 机体插槽的接受列表也是空的（=不限制）。
        asset.set_editor_property("mass", mass)
        asset.set_editor_property("power_draw", draw)
        asset.set_editor_property("heat_dissipation_modifier", diss)
        asset.set_editor_property("heat_capacity_modifier", cap)
        asset.set_editor_property("weapon_damage_mult", dmg_m)
        asset.set_editor_property("weapon_fire_interval_mult", itv_m)
        asset.set_editor_property("weapon_heat_mult", heat_m)
    except Exception as e:
        log("❌ %s 属性写入失败: %s" % (name, str(e)[:120]))
        return False
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return True


def main():
    n_slots = set_chassis_slots()
    log("机体插槽配置：%d/3" % n_slots)

    ok = 0
    for e in MODULES:
        if make_module(e):
            ok += 1
    log("模块资产：%d/%d 个" % (ok, len(MODULES)))
    log("完成")


main()
