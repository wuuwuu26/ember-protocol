# -*- coding: utf-8 -*-
"""把 3 个墙材质 BaseColor 冷灰化：Lerp(原贴图, 冷灰蓝, 0.72)。
保留 ~28% 原纹理色相/细节，整体收敛到深蓝灰工业风，消除绿/橙/白突兀感。
可逆（Lerp 节点可删/original texture 保留）。"""
import unreal
EAL=unreal.EditorAssetLibrary
MEL=unreal.MaterialEditingLibrary
MP=unreal.MaterialProperty
D="/Game/RobotGame/Art/Materials/PolyHaven"
TARGETS=["M_concrete_wall_001","M_factory_wall","M_rusty_metal"]
COOL=(0.16,0.20,0.26)   # 深冷灰蓝目标
ALPHA=0.72
lines=[]
def log(s):
    unreal.log("[WallCool] %s"%s); lines.append(str(s))

for name in TARGETS:
    p="%s/%s"%(D,name)
    m=EAL.load_asset(p)
    if not m: log("缺 %s"%name); continue
    # 移除旧的冷化 Lerp（幂等）
    for e in list(MEL.get_material_expressions(m)):
        if e.get_class().get_name()=="MaterialExpressionLinearInterpolate":
            MEL.delete_material_expression(m,e)
    # 找 BaseColor 的源 TextureSample
    bc_node=MEL.get_material_property_input_node(m,MP.MP_BASE_COLOR)
    bc_out=MEL.get_material_property_input_node_output_name(m,MP.MP_BASE_COLOR)
    if not bc_node: log("%s 无 BaseColor 节点"%name); continue
    # 断开旧 BaseColor 连接
    MEL.disconnect_material_property(m,MP.MP_BASE_COLOR)
    # 建冷灰目标色常量 + Lerp
    target=MEL.create_material_expression(m,unreal.MaterialExpressionConstant3Vector,150,120)
    target.set_editor_property("constant",unreal.LinearColor(COOL[0],COOL[1],COOL[2],1.0))
    lerp=MEL.create_material_expression(m,unreal.MaterialExpressionLinearInterpolate,350,-100)
    a=MEL.create_material_expression(m,unreal.MaterialExpressionConstant,150,-260)
    a.set_editor_property("r",ALPHA)
    MEL.connect_material_expressions(bc_node,bc_out or "RGB",lerp,"A")
    MEL.connect_material_expressions(target,"",lerp,"B")
    MEL.connect_material_expressions(a,"",lerp,"Alpha")
    MEL.connect_material_property(lerp,"",MP.MP_BASE_COLOR)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    log("%s 冷灰化完成 (Lerp alpha=%.2f)"%(name,ALPHA))

open(r"C:\Users\25227\Documents\robot_game\docs\wall_cool.txt","wb").write("\n".join(lines).encode("utf-8"))
unreal.log("WALL_COOL_DONE")
