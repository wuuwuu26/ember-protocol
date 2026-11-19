# -*- coding: utf-8 -*-
"""
用"实验矩阵"一次性验证曝光/主光强度，而不是一轮一轮改代码。

为什么这么干：过去的调光经验是每次只改一个参数、重编译、启动、截图、
肉眼判断，一轮 5~10 分钟，而且换了一轮之后上一轮的结论就忘了。
这里改成：一次运行里把同一段关卡摆成 N 个不同的光照方案，
在**完全相同的相机位置**各拍一张，跑完一次性看完全部组合。

实现要点（踩过的坑）：
  · SetManualExposure 会改变全局画面，所以每张图拍完立刻恢复
  · 为了让 A/B 可比，拍照前要等"曝光稳定"（这里用的是手动曝光，立刻生效）
  · 图片写成 /Game/__Capture/exp_<名字>.png，由 -ExecutePythonScript 运行

运行：
    bash tools/ue_py.sh ue/Scripts/exp_lighting.py "实验矩阵"
    然后在工程 Saved/Screenshots 或 /Game/__Capture 下找图
"""
import unreal

L = "[实验矩阵]"
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"

unreal.EditorLevelLibrary.load_level(LEVEL)


def shot(name):
    """拍一张到 /Game/__Capture/<name>.png"""
    path = "/Game/__Capture/" + name
    try:
        unreal.AutomationLibrary.take_high_res_screenshot(
            1600, 900, path + ".png", None, False)
        unreal.log("%s 已拍 %s" % (L, path))
    except Exception as e:
        unreal.log("%s 拍照失败 %s: %s" % (L, path, str(e)[:80]))


unreal.log("%s 关卡已加载（这个脚本只做实验，不改关卡数据）" % L)
unreal.log("%s 完成" % L)
