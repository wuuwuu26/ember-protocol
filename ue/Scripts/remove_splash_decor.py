# -*- coding: utf-8 -*-
"""删除 3 个已废弃的注水落点静态装饰片（Splash_FoamRing/FoamDisc/SprayCone）。
它们几何互相穿插（全量 OBB 检测确认为唯一真实穿模），且已被物理流体 +
C++ 物理水珠系统完全替代，之前只是 visible=False 隐藏、hidden_in_game 未设，
运行时可能意外显示。幂等：重复运行第二次删 0 个。"""
import unreal
ELL=unreal.EditorLevelLibrary
L="/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL.load_level(L)
targets={"Splash_FoamRing","Splash_FoamDisc","Splash_SprayCone"}
removed=[]
for a in list(ELL.get_all_level_actors()):
    if a.get_actor_label() in targets:
        removed.append(a.get_actor_label())
        ELL.destroy_actor(a)
ELL.save_current_level()
with open(r"C:\Users\25227\Documents\robot_game\docs\splash_cleanup.txt","wb") as f:
    f.write(("删除的废弃装饰片: %s\n"%",".join(removed)).encode("utf-8"))
    f.write(("剩余数量: %d\n"%len(removed)).encode("utf-8"))
unreal.log("SPLASH_CLEANUP_DONE removed=%d"%len(removed))
