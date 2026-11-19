# -*- coding: utf-8 -*-
"""列出雾组件 / 后处理设置上跟"体积雾""景深"有关的**真实**属性名。

为什么要探：UE 的 Python 绑定对不存在的属性名**不报错也不生效**
（set_editor_property 会抛，但很多人用 try/except 吞掉），
写错一个名字的结果就是"以为配了、其实是默认值"。
这里直接把候选名打出来，不猜。

用法: bash tools/ue_py.sh ue/Scripts/probe_fog_props.py "雾属性"
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.log("[雾属性] 脚本已开始执行")


def log(m):
    unreal.log("[雾属性] %s" % m)


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(LEVEL)

    # ── 雾组件 ──
    comp = None
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if isinstance(a, unreal.ExponentialHeightFog):
            comp = a.get_editor_property("component")
            break
    if comp:
        names = [n for n in dir(comp) if not n.startswith("_")]
        log("雾组件共 %d 个属性；含 fog 的：" % len(names))
        for n in names:
            if "fog" in n.lower() or "volumet" in n.lower():
                log("    %s" % n)
    else:
        log("❌ 找不到雾组件")

    # ── 后处理 ──
    ppv = None
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if isinstance(a, unreal.PostProcessVolume):
            ppv = a
            break
    if ppv:
        s = ppv.get_editor_property("settings")
        names = [n for n in dir(s) if not n.startswith("_")]
        log("后处理设置共 %d 个属性；含 field/focus/aperture 的：" % len(names))
        for n in names:
            low = n.lower()
            if ("field" in low or "focus" in low or "aperture" in low
                    or "depth" in low):
                log("    %s" % n)
        log("后处理里含 exposure / bloom 的：")
        for n in names:
            low = n.lower()
            if "exposure" in low or "bloom" in low:
                log("    %s" % n)


main()
