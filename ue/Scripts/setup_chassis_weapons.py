# -*- coding: utf-8 -*-
"""
给三台机体数据资产配置"武器档位"。
================================================================

背景：武器数值（伤害/射速/每发积热）现在由机体数据驱动 ——
三台机体的散热能力天差地别（34/22/13），武器打同一个热量时
节奏完全不同（轻型机永远不过热、重型机两三发就锁）。
这组数值来自**浏览器原型的 loadout 表**（已实机验证过手感）：

    轻型侦察：8/发 · 0.115s · 6.5 热   → 高速低伤、长爆发
    中型通用：15/发 · 0.19s · 11.5 热  → 均衡
    重型攻坚：27/发 · 0.30s · 18 热    → 慢速高伤、短爆发

射击不耗电（WeaponPowerPerShot=0）：电力是机动资源（冲刺 + 模块待机）。

用法: bash tools/ue_py.sh ue/Scripts/setup_chassis_weapons.py "武器档位"
"""
import unreal

DIR = "/Game/RobotGame/Data/Chassis"

# 资产名 → (伤害, 射速间隔, 每发积热, 每发耗电)
WEAPONS = {
    "DA_Chassis_Light":  (8.0,  0.115, 6.5,  0.0),
    "DA_Chassis_Medium": (15.0, 0.19,  11.5, 0.0),
    "DA_Chassis_Heavy":  (27.0, 0.30,  18.0, 0.0),
}

unreal.log("[武器档位] 开始")


def log(m):
    unreal.log("[武器档位] %s" % m)


ok = 0
for name, (dmg, interval, heat, power) in WEAPONS.items():
    asset = unreal.EditorAssetLibrary.load_asset("%s/%s" % (DIR, name))
    if not asset:
        log("❌ 找不到 %s" % name)
        continue
    try:
        asset.set_editor_property("weapon_damage", dmg)
        asset.set_editor_property("weapon_fire_interval", interval)
        asset.set_editor_property("weapon_heat_per_shot", heat)
        asset.set_editor_property("weapon_power_per_shot", power)
    except Exception as e:
        log("❌ %s 写入失败: %s" % (name, str(e)[:100]))
        continue
    # 回读校验 —— 结构体属性写错名字时 UE 只静默忽略
    got = (asset.get_editor_property("weapon_damage"),
           asset.get_editor_property("weapon_fire_interval"),
           asset.get_editor_property("weapon_heat_per_shot"),
           asset.get_editor_property("weapon_power_per_shot"))
    if (abs(got[0] - dmg) > 0.01 or abs(got[1] - interval) > 0.001
            or abs(got[2] - heat) > 0.01 or abs(got[3] - power) > 0.01):
        log("⚠️ %s 回读不一致: %s" % (name, got))
        continue
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    log("  [ok] %-20s 伤害=%.0f 间隔=%.3fs 热=%.1f 电=%.1f"
        % (name, dmg, interval, heat, power))
    ok += 1

log("完成：%d/%d 台机体配置武器档位" % (ok, len(WEAPONS)))
