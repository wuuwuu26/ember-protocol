# -*- coding: utf-8 -*-
"""真正修复：ComponentMask 输入引脚名应为 ""（不是 "Input"），证据见 conn_probe.txt。
重新连接 3 个墙材质 ARM->mask->属性 并重新编译。"""
import unreal
EAL=unreal.EditorAssetLibrary
MEL=unreal.MaterialEditingLibrary
MP=unreal.MaterialProperty
D="/Game/RobotGame/Art/Materials/PolyHaven"
TARGETS=[("concrete_wall_001",True),("factory_wall",True),("rusty_metal",True)]
lines=[]
def log(s):
    unreal.log("[RealFix] %s"%s); lines.append(str(s))
for aid,_ in TARGETS:
    p="%s/M_%s"%(D,aid)
    m=EAL.load_asset(p)
    if not m: log("缺 %s"%aid); continue
    arm=None; masks=[]
    for e in MEL.get_material_expressions(m):
        cls=e.get_class().get_name()
        if cls=="MaterialExpressionTextureSample":
            t=e.get_editor_property("texture")
            if t and "ARM" in t.get_name(): arm=e
        elif cls=="MaterialExpressionComponentMask": masks.append(e)
    if not arm or len(masks)<3: log("%s 节点不齐"%aid); continue
    # 用正确引脚名 "" 连接
    for mask in masks:
        ok=MEL.connect_material_expressions(arm,"RGB",mask,"")
        log("%s mask 连接 ok=%s"%(aid,ok))
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    log("%s 重编译+保存"%aid)
open(r"C:\Users\25227\Documents\robot_game\docs\real_fix.txt","wb").write("\n".join(lines).encode("utf-8"))
unreal.log("REAL_FIX_DONE")
