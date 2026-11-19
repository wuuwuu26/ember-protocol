# -*- coding: utf-8 -*-
"""把 Poly Haven PBR 材质应用到新区域地面/墙（第一百零六轮）。

⚠️ 只改 EXT 区（X>=1800 或带 ExtRegion tag），原竞技场绝不动。
⚠️ 第一百零二轮白线教训：这些 actor 用 override_materials，**槽数必须保持**，
    否则回落到网格默认白色 BasicShapeMaterial。所以这里把每个槽的材质
    **整体替换**（槽数不变），而不是只设 1 个。

材质分配：
  EXT 地面 48 块 -> M_concrete_floor_02（工业混凝土）
  EXT 墙 -> 按 X 分段变化：
     通道两侧短墙 / 靠前的墙 -> M_factory_wall（工厂金属，亮一点）
     其余 -> M_concrete_wall_001（风化混凝土）
     每隔几段插一面 M_rusty_metal（锈铁，做斑驳节奏）

幂等：用 tag `PolyMat` 标记改过的 actor，重跑前恢复成原始材质。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
PH = "/Game/RobotGame/Art/Materials/PolyHaven"
ENV = "/Game/RobotGame/Art/Environment"
TAG = "PolyMat"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\polyhaven_apply.txt"

EAL = unreal.EditorAssetLibrary
lines = []


def log(s):
    unreal.log("[PolyApply] %s" % s)
    lines.append(str(s))


MAT = {
    "floor": EAL.load_asset(PH + "/M_concrete_floor_02"),
    "factory": EAL.load_asset(PH + "/M_factory_wall"),
    "concrete": EAL.load_asset(PH + "/M_concrete_wall_001"),
    "rust": EAL.load_asset(PH + "/M_rusty_metal"),
    "grate": EAL.load_asset(PH + "/M_metal_grate_rusty"),
}
# 原始 override 材质（恢复用）
ORIG = {
    "floor": [EAL.load_asset(ENV + "/" + n) for n in
              ("M_Steel", "M_SteelLight", "M_Joint", "M_Copper")],
    "wall": [EAL.load_asset(ENV + "/" + n) for n in
             ("M_Steel", "M_Joint", "M_Copper", "M_SteelLight", "M_Accent_wall")],
    "corner": [EAL.load_asset(ENV + "/" + n) for n in
               ("M_Steel", "M_SteelLight", "M_Joint", "M_Core_wall", "M_Accent_wall")],
}

for k, v in MAT.items():
    if not v:
        log("!! 材质缺失 %s" % k)


def all_ph(mat):
    """把某个 Poly Haven 材质重复填成 n 个槽。"""
    return mat


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(LEVEL)
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    nf = nw = nrestore = 0
    for a in list(actor_sub.get_all_level_actors()):
        if a.get_class().get_name() != "StaticMeshActor":
            continue
        c = a.static_mesh_component
        m = c.get_editor_property("static_mesh") if c else None
        if not m:
            continue
        nm = m.get_name().lower()
        try:
            tags = [str(t) for t in a.get_editor_property("tags")]
        except Exception:
            tags = []

        # ── 第一百零九轮修复 ──
        # 上一版用 `"wall" in nm` 筛墙，误伤了名字里带 wall 的 Cosmos 道具
        # （cs1-wallfanhatch / cs1-wall-light-6）—— 材质被覆盖成混凝土，
        # 丢失自带贴图，表现就是"纹理没加载出来"。
        # 用 tag 精确排除所有 Cosmos 道具；若已被误改（带 PolyMat tag），
        # 清掉 override，让它们回落到 glTF 网格自带的材质。
        if "CosmosProp" in tags:
            if "PolyMat" in tags:
                c.set_editor_property("override_materials", [])
                tags = [t for t in tags if t != "PolyMat"]
                a.set_editor_property("tags", tags)
                nrestore += 1
            continue

        if "floor" not in nm and "wall" not in nm:
            continue
        loc = a.get_actor_location()
        # 真正的场景墙/地面：必须带 ExtRegion tag（build_ext_region.py 生成）。
        # 不再用 loc.x>=1800 兜底 —— 那会把 X>1800 的 Cosmos 道具也圈进来。
        is_ext = "ExtRegion" in tags
        if not is_ext:
            continue

        ov = c.get_editor_property("override_materials")
        n = len(ov)
        if n == 0:
            # 没覆盖的墙（4 段），给一个槽即可
            n = 1

        if "floor" in nm:
            new_mat = MAT["floor"]
        else:
            # 墙：靠前/通道用工厂金属，中后段用混凝土，按 x 插锈铁
            if loc.x < 2600:
                new_mat = MAT["factory"]
            elif (int(loc.x) // 400) % 5 == 0:
                new_mat = MAT["rust"]
            else:
                new_mat = MAT["concrete"]

        # 槽数不变，全部填成同一材质
        c.set_editor_property("override_materials", [new_mat] * n)

        # 打 tag 便于幂等/恢复
        if TAG not in tags:
            tags.append(TAG)
        a.set_editor_property("tags", tags)

        if "floor" in nm:
            nf += 1
        else:
            nw += 1

    log("已应用：地面 %d 块、墙 %d 段；恢复被误改的 Cosmos 道具 %d 个" %
        (nf, nw, nrestore))
    les.save_current_level()
    log("已保存关卡")
    with open(REPORT, "wb") as f:
        f.write("\n".join(lines).encode("utf-8"))
    unreal.log("POLY_APPLY_DONE")


main()
