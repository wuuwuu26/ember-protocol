# -*- coding: utf-8 -*-
"""
把场景里"默认材质"的静态网格全部换回网格资产自己的材质。
================================================================

诊断（2026-10-19）：
    竞技场是脚本重建的（rebuild_arena.py），生成 StaticMeshActor 之后
    没有把材质重新指回去 —— 结果 **146 个地面/墙体/天桥构件全部挂着
    引擎的 BasicShapeMaterial**（一块没有细节的浅灰塑料）。
    这就是"纹理和场景不搭"的根因：
      · 地面是一片均匀的浅灰，被暖光一照就变成沙黄色，像沙漠
      · 所有 M_RobotSurface 的调色、面板缝、金属度对它**完全无效**
      · 机体（有材质）和场景（没材质）根本不在一个美术体系里

修法：
    ① 网格资产自身的材质槽有空的（SM_Env_Floor 槽 0 = BasicShapeMaterial）→ 补上
    ② 关卡里每个 StaticMeshActor 的材质**覆盖**清掉，回落到网格自带材质

用法: bash tools/ue_py.sh ue/Scripts/fix_env_materials.py "环境材质"
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ENV = "/Game/RobotGame/Art/Environment"
PROPS = "/Game/RobotGame/Art/Props"
LOG = "[环境材质]"

# 槽位为空时按网格名补的默认材质（Environment 目录下的 MI）
DEFAULT_BY_MESH = {
    "SM_Env_Floor": ["M_Steel", "M_SteelLight", "M_Joint", "M_Copper"],
    "SM_Env_Wall": ["M_Steel", "M_SteelLight", "M_Joint",
                    "M_Accent_prop", "M_AccentDark_prop", "M_Copper"],
}

BAD = ("BasicShapeMaterial", "WorldGridMaterial", "DefaultMaterial")


def log(m):
    unreal.log("%s %s" % (LOG, m))


def load_mi(name, folder=ENV):
    mi = unreal.EditorAssetLibrary.load_asset("%s/%s" % (folder, name))
    return mi


unreal.EditorLevelLibrary.load_level(LEVEL)

# ── ① 补网格资产上的空槽 ──
ar = unreal.AssetRegistryHelpers.get_asset_registry()
fixed_assets = 0
for root in (ENV, PROPS):
    for ad in ar.get_assets_by_path(root, recursive=True):
        if str(ad.asset_class_path.asset_name) != "StaticMesh":
            continue
        nm = str(ad.asset_name)
        if "_LOD" in nm:
            continue
        sm = ad.get_asset()
        if not sm:
            continue
        mats = sm.get_editor_property("static_materials")
        changed = False
        defaults = DEFAULT_BY_MESH.get(nm)
        for i, m in enumerate(mats):
            mi = None
            try:
                mi = m.get_editor_property("material_interface")
            except Exception:
                pass
            if mi and mi.get_name() not in BAD:
                continue
            repl = None
            if defaults and i < len(defaults):
                repl = load_mi(defaults[i], root)
            if repl:
                m.set_editor_property("material_interface", repl)
                mats[i] = m
                changed = True
                log("  %s 槽%d → %s" % (nm, i, repl.get_name()))
        if changed:
            sm.set_editor_property("static_materials", mats)
            unreal.EditorAssetLibrary.save_loaded_asset(sm)
            fixed_assets += 1
log("补网格空槽：%d 个资产" % fixed_assets)

# ── ② 清掉关卡里 StaticMeshActor 的材质覆盖 ──
n_actor = 0
n_slot = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    smc = a.static_mesh_component
    if not smc:
        continue
    mesh = smc.get_editor_property("static_mesh")
    if not mesh:
        continue
    mats = mesh.get_editor_property("static_materials")
    did = False
    for i, m in enumerate(mats):
        try:
            mi = m.get_editor_property("material_interface")
        except Exception:
            mi = None
        if mi:
            smc.set_material(i, mi)
            n_slot += 1
            did = True
    if did:
        n_actor += 1
log("清理材质覆盖：%d 个 Actor / %d 个槽" % (n_actor, n_slot))

unreal.EditorLevelLibrary.save_current_level()
log("完成并已保存关卡")
