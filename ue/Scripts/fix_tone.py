# -*- coding: utf-8 -*-
"""
校正场景色调：把"全场橙红"拉回冷调夜景。
================================================================
诊断（probe_light.py / probe_fog.py）：

    太阳   22000 lux   use_temperature=True  5200K        → 偏暖
    天光   3.2         light_color (255,230,215)          → **明显偏暖**
    雾     密度 0.0055 散射色 (0.022,0.030,0.046)          → 已经是冷的，不用动

天光颜色是主要问题：它参与**所有间接光**，等于给整个场景加了一张橙色滤镜。
再叠 5200K 的太阳，地板、墙体、机体全被染橙 —— 细节被同一个色相糊掉，
这也是"看不出装甲纹理"的另一半原因。

改法：
    太阳  → 关掉色温，直接给冷白月光色 (199,219,255)，强度不变
    天光  → 中性偏冷 (230,240,255)，强度不变

⚠️ Python 里没有 mark_render_state_dirty()，set_editor_property 会自己触发
   PostEditChangeProperty；上一版在 set 之后调用它，抛异常把整个分支吞掉了
   （太阳/天光看起来"没生效"其实是异常打断，值其实已经写进去了）。
"""
import unreal

L = "[色调]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")

SUN_RGB = (199, 219, 255)
SKY_RGB = (230, 240, 255)

n_sun = n_sky = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    cn = a.get_class().get_name()
    if cn == "DirectionalLight":
        c = a.get_editor_property("light_component")
        try:
            c.set_editor_property("use_temperature", False)
        except Exception as e:
            unreal.log("%s ⚠️ use_temperature: %s" % (L, str(e)[:60]))
        c.set_editor_property("light_color",
                              unreal.Color(r=SUN_RGB[0], g=SUN_RGB[1],
                                           b=SUN_RGB[2], a=255))
        n_sun += 1
    elif cn == "SkyLight":
        c = a.get_editor_property("light_component")
        c.set_editor_property("light_color",
                              unreal.Color(r=SKY_RGB[0], g=SKY_RGB[1],
                                           b=SKY_RGB[2], a=255))
        n_sky += 1

# 回读确认（不靠计数器，直接读关卡里的真实值）
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    cn = a.get_class().get_name()
    if cn not in ("DirectionalLight", "SkyLight"):
        continue
    c = a.get_editor_property("light_component")
    col = c.get_editor_property("light_color")
    extra = ""
    if cn == "DirectionalLight":
        extra = " 用色温=%s 温度=%.0f" % (
            c.get_editor_property("use_temperature"),
            c.get_editor_property("temperature"))
    unreal.log("%s %-16s 色=(%d,%d,%d) 强度=%.1f%s"
               % (L, cn, col.r, col.g, col.b,
                  c.get_editor_property("intensity"), extra))

unreal.EditorLevelLibrary.save_current_level()
unreal.log("%s 已写入：太阳 %d 个 / 天光 %d 个" % (L, n_sun, n_sky))
