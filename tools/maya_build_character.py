# -*- coding: utf-8 -*-
import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds

print("=== Maya 2027 精细人物建模启动 ===")
cmds.file(new=True, force=True)
cmds.currentUnit(linear='cm')
cmds.loadPlugin('fbxmaya')

# 1. 建立骨骼骨架体系 (完全匹配余火协议骨骼驱动层)
# 关节位置完全严格对应游戏运动学体系 (Y-Up, 厘米单位, 总高约 235cm)
joints_def = [
    ("root", (0.0, 0.0, 0.0), None),
    ("pelvis", (0.0, 140.0, 0.0), "root"),
    ("torso", (0.0, 185.0, 0.0), "pelvis"),
    ("head", (0.0, 230.0, 0.0), "torso"),
    # 左手
    ("shoulder_L", (0.0, 202.0, 22.0), "torso"),
    ("upperarm_L", (0.0, 202.0, 45.0), "shoulder_L"),
    ("forearm_L", (0.0, 160.0, 68.0), "upperarm_L"),
    # 右手 (主开火臂)
    ("shoulder_R", (0.0, 202.0, -22.0), "torso"),
    ("upperarm_R", (0.0, 202.0, -45.0), "shoulder_R"),
    ("forearm_R", (0.0, 160.0, -68.0), "upperarm_R"),
    # 左腿
    ("thigh_L", (0.0, 134.0, 26.0), "pelvis"),
    ("shin_L", (0.0, 90.0, 26.0), "thigh_L"),
    ("foot_L", (0.0, 28.0, 26.0), "shin_L"),
    # 右腿
    ("thigh_R", (0.0, 134.0, -26.0), "pelvis"),
    ("shin_R", (0.0, 90.0, -26.0), "thigh_R"),
    ("foot_R", (0.0, 28.0, -26.0), "shin_R"),
]

joint_objs = {}
for jname, pos, parent in joints_def:
    cmds.select(clear=True)
    j = cmds.joint(name=jname, position=pos)
    joint_objs[jname] = j
    if parent and parent in joint_objs:
        cmds.parent(j, joint_objs[parent])

print(f"骨骼体系创建成功: {len(joint_objs)} 根主关节")

# 2. 建立材质着色组 (完全匹配游戏内 9 大核心材质槽)
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

# 3. 精细构建人物角色几何体部件
parts_list = []

def assign_mat(obj, mat_name):
    if mat_name in shading_groups:
        cmds.sets(obj, forceElement=shading_groups[mat_name])

# 3.1 头部与战术战术头盔 (Visor + Head Shell)
head_shell = cmds.polyCube(w=26, h=28, d=28, sx=4, sy=4, sz=4, name="Head_Armor")[0]
cmds.move(0, 232, 0, head_shell)
cmds.polyBevel3(head_shell, offset=2.5, segments=2)
assign_mat(head_shell, "M_SteelLight")
parts_list.append(head_shell)

visor = cmds.polyCube(w=22, h=10, d=8, name="Head_Visor")[0]
cmds.move(0, 233, 14, visor)
cmds.polyBevel3(visor, offset=1.2, segments=2)
assign_mat(visor, "M_Visor_medium")
parts_list.append(visor)

# 3.2 躯干防弹装甲胸板与动力反应核心 (Torso Plate + Energy Core)
torso_chest = cmds.polyCube(w=52, h=48, d=36, sx=4, sy=4, sz=4, name="Torso_Chestplate")[0]
cmds.move(0, 186, 0, torso_chest)
cmds.polyBevel3(torso_chest, offset=4.0, segments=3)
assign_mat(torso_chest, "M_Steel")
parts_list.append(torso_chest)

core_emitter = cmds.polyCylinder(r=10, h=8, sx=24, name="Torso_Core")[0]
cmds.rotate(90, 0, 0, core_emitter)
cmds.move(0, 188, 18, core_emitter)
assign_mat(core_emitter, "M_Core_medium")
parts_list.append(core_emitter)

backpack = cmds.polyCube(w=38, h=42, d=16, name="Torso_Backpack")[0]
cmds.move(0, 186, -20, backpack)
cmds.polyBevel3(backpack, offset=2.0, segments=2)
assign_mat(backpack, "M_SteelLight")
parts_list.append(backpack)

# 3.3 双肩重甲护肩 (Shoulder Pads)
for side, z_sign in [("L", 1), ("R", -1)]:
    pad = cmds.polyCube(w=24, h=26, d=22, sx=3, sy=3, sz=3, name=f"Shoulder_Pad_{side}")[0]
    cmds.move(0, 204, z_sign * 36, pad)
    cmds.polyBevel3(pad, offset=3.0, segments=2)
    assign_mat(pad, "M_Accent_medium")
    parts_list.append(pad)

# 3.4 手臂动力护臂与外骨骼机械肘关节
for side, z_sign in [("L", 1), ("R", -1)]:
    arm_upper = cmds.polyCylinder(r=9, h=32, sx=16, name=f"UpperArm_Armor_{side}")[0]
    cmds.rotate(0, 0, 90, arm_upper)
    cmds.move(0, 202, z_sign * 54, arm_upper)
    cmds.polyBevel3(arm_upper, offset=1.5, segments=2)
    assign_mat(arm_upper, "M_SteelLight")
    parts_list.append(arm_upper)

    elbow = cmds.polyCylinder(r=8, h=14, sx=16, name=f"Elbow_Joint_{side}")[0]
    cmds.move(0, 160, z_sign * 68, elbow)
    assign_mat(elbow, "M_Joint")
    parts_list.append(elbow)

    forearm = cmds.polyCube(w=16, h=36, d=18, sx=3, sy=3, sz=3, name=f"ForeArm_Armor_{side}")[0]
    cmds.move(0, 142, z_sign * 68, forearm)
    cmds.polyBevel3(forearm, offset=2.0, segments=2)
    assign_mat(forearm, "M_Steel")
    parts_list.append(forearm)

# 3.5 骨盆护裆与战术甲裙 (Pelvis)
pelvis = cmds.polyCube(w=42, h=22, d=30, sx=3, sy=3, sz=3, name="Pelvis_Armor")[0]
cmds.move(0, 140, 0, pelvis)
cmds.polyBevel3(pelvis, offset=3.0, segments=2)
assign_mat(pelvis, "M_Steel")
parts_list.append(pelvis)

# 3.6 腿部重型护膝、大腿装甲与防滑动力战靴
for side, z_sign in [("L", 1), ("R", -1)]:
    thigh = cmds.polyCube(w=20, h=40, d=22, sx=3, sy=3, sz=3, name=f"Thigh_Armor_{side}")[0]
    cmds.move(0, 114, z_sign * 26, thigh)
    cmds.polyBevel3(thigh, offset=2.5, segments=2)
    assign_mat(thigh, "M_SteelLight")
    parts_list.append(thigh)

    knee = cmds.polyCylinder(r=9, h=18, sx=16, name=f"Knee_Joint_{side}")[0]
    cmds.rotate(90, 0, 0, knee)
    cmds.move(0, 90, z_sign * 26, knee)
    assign_mat(knee, "M_Joint")
    parts_list.append(knee)

    shin = cmds.polyCube(w=22, h=44, d=24, sx=3, sy=3, sz=3, name=f"Shin_Armor_{side}")[0]
    cmds.move(0, 62, z_sign * 26, shin)
    cmds.polyBevel3(shin, offset=2.5, segments=2)
    assign_mat(shin, "M_Steel")
    parts_list.append(shin)

    boot = cmds.polyCube(w=26, h=18, d=34, sx=3, sy=3, sz=3, name=f"Combat_Boot_{side}")[0]
    cmds.move(4, 12, z_sign * 26, boot)
    cmds.polyBevel3(boot, offset=2.5, segments=2)
    assign_mat(boot, "M_SteelLight")
    parts_list.append(boot)

print(f"人物机体建模完成，部件数量: {len(parts_list)}")

# 4. 蒙皮绑定 (Smooth Skinning) 到各骨骼关节
# 统一结合为单体网格 SK_Chassis_Medium
combined_mesh = cmds.polyUnite(parts_list, ch=False, name="SK_Chassis_Medium")[0]
cmds.delete(all=True, constructionHistory=True)

skin_cluster = cmds.skinCluster(
    list(joint_objs.values()),
    combined_mesh,
    toSelectedBones=True,
    bindMethod=0, # Closest joint
    normalizeWeights=1,
    weightDistribution=0,
    maximumInfluences=3,
    obeyMaxInfluences=True,
    name="PilotHero_SkinCluster"
)[0]

print("骨骼蒙皮绑定完成 (SkinCluster ready)")

# 5. 导出游戏专用 FBX
out_fbx = "C:/Users/25227/Documents/robot_game/assets/out/maya_pilot_hero.fbx"
cmds.select([combined_mesh, "root"])

# 设置 FBX 导出选项
cmds.FBXResetExport()
cmds.FBXExportSmoothingGroups("-v", True)
cmds.FBXExportSmoothMesh("-v", True)
cmds.FBXExportBakeComplexAnimation("-v", False)
cmds.FBXExportSkins("-v", True)
cmds.FBXExportShapes("-v", True)
cmds.FBXExportInputConnections("-v", False)
cmds.FBXExportInAscii("-v", False)

cmds.FBXExport("-file", out_fbx, "-s", True)
print(f"成功导出 Maya 2027 精细人物模型 FBX: {out_fbx}")

with open(r"C:\Users\25227\Documents\robot_game\docs\maya_model_done.txt", "w", encoding="utf-8") as f:
    f.write(f"FBX: {out_fbx}\nMAYA_DONE\n")

maya.standalone.uninitialize()
print("=== Maya 2027 建模任务圆满完成 ===")
