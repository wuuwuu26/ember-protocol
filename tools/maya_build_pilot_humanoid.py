# -*- coding: utf-8 -*-
import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds
import math

print("=== Maya 2027 AAA 级硬表面人物战术外骨骼建模启动 ===")
cmds.file(new=True, force=True)
cmds.currentUnit(linear='cm')
cmds.loadPlugin('fbxmaya')

# 1. 骨骼体系
joints_def = [
    ("root", (0.0, 0.0, 0.0), None),
    ("pelvis", (0.0, 115.0, 0.0), "root"),
    ("torso", (0.0, 155.0, 0.0), "pelvis"),
    ("head", (0.0, 195.0, 0.0), "torso"),
    # 左臂
    ("shoulder_L", (0.0, 172.0, 20.0), "torso"),
    ("upperarm_L", (0.0, 172.0, 36.0), "shoulder_L"),
    ("forearm_L", (0.0, 136.0, 48.0), "upperarm_L"),
    # 右臂 (武器臂)
    ("shoulder_R", (0.0, 172.0, -20.0), "torso"),
    ("upperarm_R", (0.0, 172.0, -36.0), "shoulder_R"),
    ("forearm_R", (0.0, 136.0, -48.0), "upperarm_R"),
    # 左腿
    ("thigh_L", (0.0, 110.0, 16.0), "pelvis"),
    ("shin_L", (0.0, 68.0, 16.0), "thigh_L"),
    ("foot_L", (4.0, 10.0, 16.0), "shin_L"),
    # 右腿
    ("thigh_R", (0.0, 110.0, -16.0), "pelvis"),
    ("shin_R", (0.0, 68.0, -16.0), "thigh_R"),
    ("foot_R", (4.0, 10.0, -16.0), "shin_R"),
]

joint_objs = {}
for jname, pos, parent in joints_def:
    cmds.select(clear=True)
    j = cmds.joint(name=jname, position=pos)
    joint_objs[jname] = j
    if parent and parent in joint_objs:
        cmds.parent(j, joint_objs[parent])

# 2. 材质着色组
mat_slots = [
    ("M_Frame", (0.075, 0.079, 0.088)),
    ("M_Joint", (0.052, 0.054, 0.060)),
    ("M_Copper", (0.360, 0.205, 0.095)),
    ("M_SteelLight", (0.400, 0.412, 0.428)),
    ("M_Steel", (0.300, 0.312, 0.336)),
    ("M_Core_medium", (0.187, 0.187, 0.300)),
    ("M_Visor_medium", (0.160, 0.200, 0.280)),
    ("M_Accent_medium", (0.260, 0.540, 0.820)),
    ("M_AccentDark_medium", (0.109, 0.226, 0.344)),
]

shading_groups = {}
for mname, col in mat_slots:
    mat = cmds.shadingNode('lambert', asShader=True, name=mname)
    cmds.setAttr(mat + '.color', col[0], col[1], col[2], type='double3')
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=mname + "SG")
    cmds.connectAttr(mat + '.outColor', sg + '.surfaceShader', force=True)
    shading_groups[mname] = sg

parts = []
def assign(obj, mat_name):
    if mat_name in shading_groups:
        cmds.sets(obj, forceElement=shading_groups[mat_name])

# 3. 仿人精雕部件
# 3.1 头部战术头盔与护目镜 (Humanoid Proportions)
head = cmds.polySphere(r=11, sx=24, sy=18, name="Pilot_Helmet")[0]
cmds.scale(0.85, 1.15, 1.05, head)
cmds.move(0, 196, 2, head)
assign(head, "M_SteelLight")
parts.append(head)

# 锋锐战术护目镜
visor = cmds.polyCube(w=16, h=5.5, d=6, name="Pilot_Visor")[0]
cmds.move(0, 197, 11, visor)
cmds.polyBevel3(visor, offset=1.0, segments=2)
assign(visor, "M_Visor_medium")
parts.append(visor)

# 颈部内骨架
neck = cmds.polyCylinder(r=6, h=10, sx=16, name="Pilot_Neck")[0]
cmds.move(0, 180, 0, neck)
assign(neck, "M_Joint")
parts.append(neck)

# 3.2 躯干人体工程学胸甲 (V形倒三角战术装甲)
chest_upper = cmds.polyCube(w=36, h=26, d=24, sx=4, sy=4, sz=4, name="Chest_Armor")[0]
cmds.move(0, 166, 1, chest_upper)
cmds.polyBevel3(chest_upper, offset=3.5, segments=3)
assign(chest_upper, "M_Steel")
parts.append(chest_upper)

# 锁骨与肩部固定环
collar_L = cmds.polyCube(w=14, h=6, d=16, name="Collar_L")[0]
cmds.move(0, 176, 14, collar_L)
cmds.rotate(0, 0, -15, collar_L)
assign(collar_L, "M_SteelLight")
parts.append(collar_L)

collar_R = cmds.polyCube(w=14, h=6, d=16, name="Collar_R")[0]
cmds.move(0, 176, -14, collar_R)
cmds.rotate(0, 0, 15, collar_R)
assign(collar_R, "M_SteelLight")
parts.append(collar_R)

# 核心聚能环 (胸前发光核心)
core = cmds.polyCylinder(r=5.5, h=5, sx=24, name="Chest_Core")[0]
cmds.rotate(90, 0, 0, core)
cmds.move(0, 166, 14, core)
assign(core, "M_Core_medium")
parts.append(core)

# 背部动力电池舱
pack = cmds.polyCube(w=26, h=30, d=12, name="Spine_PowerPack")[0]
cmds.move(0, 164, -14, pack)
cmds.polyBevel3(pack, offset=2.0, segments=2)
assign(pack, "M_Accent_medium")
parts.append(pack)

# 腹肌段活动防弹肋板 (Abdominal Section)
abs_armor = cmds.polyCube(w=26, h=18, d=20, sx=3, sy=3, sz=3, name="Abdominal_Plates")[0]
cmds.move(0, 144, 0, abs_armor)
cmds.polyBevel3(abs_armor, offset=2.0, segments=2)
assign(abs_armor, "M_Frame")
parts.append(abs_armor)

# 骨盆与战术腰带 (Pelvis)
belt = cmds.polyCube(w=30, h=14, d=22, sx=3, sy=3, sz=3, name="Tactical_Belt")[0]
cmds.move(0, 128, 0, belt)
cmds.polyBevel3(belt, offset=2.5, segments=2)
assign(belt, "M_SteelLight")
parts.append(belt)

# 3.3 双臂人体肌肉流线装甲 (Biceps, Forearm & Hands)
for side, sign in [("L", 1), ("R", -1)]:
    # 肩甲 (Shoulder Pauldron) - 倒角包覆感
    sh_pad = cmds.polyCube(w=16, h=18, d=18, sx=3, sy=3, sz=3, name=f"Shoulder_{side}")[0]
    cmds.move(0, 174, sign * 28, sh_pad)
    cmds.rotate(0, 0, -sign * 18, sh_pad)
    cmds.polyBevel3(sh_pad, offset=2.5, segments=2)
    assign(sh_pad, "M_Accent_medium")
    parts.append(sh_pad)

    # 大臂二头肌装甲
    bicep = cmds.polyCylinder(r=6.5, h=20, sx=18, name=f"Bicep_{side}")[0]
    cmds.move(0, 154, sign * 36, bicep)
    assign(bicep, "M_SteelLight")
    parts.append(bicep)

    # 肘关节阻尼器
    elbow = cmds.polySphere(r=5.5, sx=16, sy=16, name=f"Elbow_{side}")[0]
    cmds.move(0, 140, sign * 40, elbow)
    assign(elbow, "M_Joint")
    parts.append(elbow)

    # 前臂流线战术腕甲 (Forearm Armor)
    forearm = cmds.polyCube(w=11, h=24, d=12, sx=3, sy=3, sz=3, name=f"Forearm_{side}")[0]
    cmds.move(0, 124, sign * 44, forearm)
    cmds.polyBevel3(forearm, offset=1.8, segments=2)
    assign(forearm, "M_Steel")
    parts.append(forearm)

    # 战术战术手套拳部 (Tactical Hand)
    hand = cmds.polyCube(w=9, h=11, d=9, name=f"Hand_{side}")[0]
    cmds.move(0, 107, sign * 46, hand)
    cmds.polyBevel3(hand, offset=1.2, segments=2)
    assign(hand, "M_SteelLight")
    parts.append(hand)

# 3.4 双腿人体骨骼动力外骨骼 (Thigh, Knee, Calf & Boots)
for side, sign in [("L", 1), ("R", -1)]:
    # 大腿股四头肌重甲
    thigh = cmds.polyCube(w=15, h=34, d=17, sx=3, sy=3, sz=3, name=f"Thigh_{side}")[0]
    cmds.move(0, 95, sign * 16, thigh)
    cmds.polyBevel3(thigh, offset=2.5, segments=2)
    assign(thigh, "M_SteelLight")
    parts.append(thigh)

    # 机械护膝外骨骼铰链
    knee = cmds.polyCylinder(r=6.5, h=12, sx=18, name=f"Knee_{side}")[0]
    cmds.rotate(90, 0, 0, knee)
    cmds.move(3, 76, sign * 16, knee)
    assign(knee, "M_Joint")
    parts.append(knee)

    # 小腿小腿肌与迎面骨装甲 (Shin)
    shin = cmds.polyCube(w=14, h=38, d=16, sx=3, sy=3, sz=3, name=f"Shin_{side}")[0]
    cmds.move(0, 48, sign * 16, shin)
    cmds.polyBevel3(shin, offset=2.5, segments=2)
    assign(shin, "M_Steel")
    parts.append(shin)

    # 防滑动力作战战靴 (Tactical Boot) - 人体脚掌前伸贴地
    boot = cmds.polyCube(w=14, h=12, d=26, sx=3, sy=3, sz=3, name=f"Boot_{side}")[0]
    cmds.move(4, 10, sign * 16, boot)
    cmds.polyBevel3(boot, offset=2.0, segments=2)
    assign(boot, "M_SteelLight")
    parts.append(boot)

print(f"仿人高精度部件创建完毕，总数量: {len(parts)}")

# 4. 结合网格并绑定蒙皮
combined = cmds.polyUnite(parts, ch=False, name="SK_Pilot_Maya")[0]
cmds.delete(all=True, constructionHistory=True)

# 蒙皮权重绑定
cmds.skinCluster(
    list(joint_objs.values()),
    combined,
    toSelectedBones=True,
    bindMethod=0, # Closest joint
    normalizeWeights=1,
    weightDistribution=0,
    maximumInfluences=3,
    obeyMaxInfluences=True,
    name="PilotHero_SkinCluster"
)

# 5. 导出 FBX
out_fbx = "C:/Users/25227/Documents/robot_game/assets/out/maya_pilot_hero.fbx"
cmds.select([combined, "root"])
cmds.FBXResetExport()
cmds.FBXExportSmoothingGroups("-v", True)
cmds.FBXExportSmoothMesh("-v", True)
cmds.FBXExportSkins("-v", True)
cmds.FBXExportShapes("-v", True)
cmds.FBXExport("-file", out_fbx, "-s", True)

print("Maya 2027 AAA 人物战斗机甲 FBX 成功导出！")
maya.standalone.uninitialize()
