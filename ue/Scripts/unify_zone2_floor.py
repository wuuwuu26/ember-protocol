# -*- coding: utf-8 -*-
"""把场景2（新区域）的地面材质改成和场景1一致（第一百一十二轮）。

场景1（原竞技场 X<1800）地面 override：
  [M_Steel, M_SteelLight, M_Joint, M_Copper]
场景2（新区域 X>=1800）当前是：
  [M_concrete_floor_02 x4]   <- 上一轮换成写实混凝土，与场景1不统一

用户要求"场景2的地面纹理改成和场景1一样"→ 直接把场景2的 48 块地面
override 恢复成场景1那套，槽数保持 4 不变（不回落 BasicShapeMaterial）。

⚠️ 只改地面 actor，不改墙、不改水渠。
⚠️ 幂等：带 PolyMat tag 的地面同样会被处理。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ENV = "/Game/RobotGame/Art/Environment"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\zone2_floor_unify.txt"

EAL = unreal.EditorAssetLibrary
lines = []


def log(s):
    unreal.log("[Zone2Floor] %s" % s)
    lines.append(str(s))


# 场景1 的标准地面材质槽（4 个，顺序固定）
ZONE1_MATS = [
    EAL.load_asset(ENV + "/M_Steel"),
    EAL.load_asset(ENV + "/M_SteelLight"),
    EAL.load_asset(ENV + "/M_Joint"),
    EAL.load_asset(ENV + "/M_Copper"),
]

for i, m in enumerate(ZONE1_MATS):
    log("槽%d = %s" % (i, m.get_name() if m else "**缺失**"))

if any(m is None for m in ZONE1_MATS):
    log("!! 场景1 材质有缺失，中止")
else:
    def main():
        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        les.load_level(LEVEL)
        sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

        n = 0
        for a in sub.get_all_level_actors():
            if a.get_class().get_name() != "StaticMeshActor":
                continue
            c = a.static_mesh_component
            mesh = c.get_editor_property("static_mesh") if c else None
            if not mesh or "floor" not in mesh.get_name().lower():
                continue
            loc = a.get_actor_location()
            if loc.x < 1800.0:          # 场景1 不动
                continue
            c.set_editor_property("override_materials", list(ZONE1_MATS))
            n += 1
        log("场景2 地面 %d 块 -> 已统一为场景1材质" % n)
        les.save_current_level()
        log("已保存关卡")

    main()

with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("ZONE2_FLOOR_DONE")
