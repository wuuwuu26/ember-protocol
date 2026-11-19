# -*- coding: utf-8 -*-
"""把装饰点光降到"氛围"级别，让冷白太阳成为主光。

诊断依据：太阳 9000 lux 冷白 (0.78,0.86,1.0)，但画面 R/B 仍是 1.29；
把太阳关掉只降到 1.82 —— 说明 11 盏 2600cd 的暖色装饰灯贡献了约一半照度，
把整体色相拉暖了。装饰灯应该只在地面/墙面留下彩色光斑，不该参与主照明。
"""
import unreal
L = "[灯光调校]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")

ACCENT_CD = 800.0     # 装饰点光：2600 → 800（约 -1.7 档）
FLOOD_CD = 4200.0     # 泛光：7000 → 4200（仍是中性白，压暗避免过曝）

n_a = n_f = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    cn = a.get_class().get_name()
    if cn not in ("PointLight", "SpotLight", "RectLight"):
        continue
    lbl = a.get_actor_label()
    c = a.get_editor_property("light_component")
    try:
        if lbl.startswith("Accent"):
            c.set_editor_property("intensity", ACCENT_CD)
            n_a += 1
        elif lbl.startswith("Flood"):
            c.set_editor_property("intensity", FLOOD_CD)
            n_f += 1
        else:
            continue
    except Exception as e:
        unreal.log("%s ⚠️ %s: %s" % (L, lbl, str(e)[:50]))

unreal.EditorLevelLibrary.save_current_level()
unreal.log("%s 装饰点光 %d 盏 → %.0fcd，泛光 %d 盏 → %.0fcd"
           % (L, n_a, ACCENT_CD, n_f, FLOOD_CD))
