# -*- coding: utf-8 -*-
"""
玩家部位耐久微调（数值平衡，不改代码）。

为什么改：
    实测"站着不动"从满血到瘫痪只要 6 秒。敌人在 1.35s 间隔下每次 7 点伤害，
    5 个敌人 ≈ 26 dps，而玩家四条功能部位合计只有 128 点 —— 128/26 ≈ 5 秒。
    这意味着一进场就被压制，玩家还没来得及瞄准就先断一条腿。
    把部位耐久提到 1.5 倍后，站桩存活约 9 秒，配合移动/闪避就有足够反应时间。

⚠️ 只能按下标改，不能按 tag 匹配：
   UE 的 Python 接口读不出 FGameplayTag 的名字（返回空结构体），
   用 tag 做 key 会全部匹配失败、静默不改（第一版就是这样）。
   规则表的顺序是固定的：Core / Torso / Arm.L / Arm.R / Leg.L / Leg.R。
"""
import unreal

PATH = "/Game/RobotGame/Data/Enemies/DA_PartMap_Player"
LOG = "[平衡]"
SCALE = 1.5

BASE = [90.0, 40.0, 34.0, 34.0, 30.0, 30.0]
NAMES = ["Core", "Torso", "Arm.L", "Arm.R", "Leg.L", "Leg.R"]


def log(s):
    unreal.log("%s %s" % (LOG, s))


da = unreal.EditorAssetLibrary.load_asset(PATH)
if not da:
    log("❌ 找不到 %s" % PATH)
    raise SystemExit(1)

rules = da.get_editor_property("rules")
log("规则数 = %d" % len(rules))

changed = 0
for i, e in enumerate(rules):
    if i >= len(BASE):
        break
    old = float(e.get_editor_property("max_health"))
    new = round(BASE[i] * SCALE, 1)
    if abs(new - old) > 0.01:
        e.set_editor_property("max_health", new)
        changed += 1
    log("  %-8s %.0f → %.0f" % (NAMES[i], old, new))

da.set_editor_property("rules", rules)
unreal.EditorAssetLibrary.save_loaded_asset(da)
log("完成，改动 %d 条（倍率 %.1f）" % (changed, SCALE))
