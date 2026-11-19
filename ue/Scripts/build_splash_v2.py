# -*- coding: utf-8 -*-
"""新建干净的 M_Splash_Foam_V2，并赋给两个泡沫圆盘（第一百一十二轮）。

不修改旧的 M_Splash_Foam（已被多次改动、节点重复），而是新建一个
结构确定的材质，避免"清空节点又叠加"的坑。

材质设计（泡沫/水花落点）：
  BaseColor = 浅蓝灰底 (0.30,0.48,0.55) + 气泡贴图×0.5（明暗颗粒）
  Emissive  = 气泡贴图×0.05（极轻高光，不过曝）
  Roughness = 0.55
  气泡贴图 T_Toxic_Bub（黑底白点）用 TextureCoordinate×3 平铺，
  让气泡点在圆盘上分布更密、更像水花。
"""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
MP = unreal.MaterialProperty
MATDIR = "/Game/RobotGame/Art/Materials"
NEW = MATDIR + "/M_Splash_Foam_V2"
TEX = MATDIR + "/T_Toxic_Bub"
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\splash_v2.txt"

lines = []


def log(s):
    unreal.log("[SplashV2] %s" % s)
    lines.append(str(s))


def build_material():
    t = EAL.load_asset(TEX)
    if not t:
        log("!! 贴图缺失")
        return None

    # 幂等：存在就直接返回
    if EAL.does_asset_exist(NEW):
        m = EAL.load_asset(NEW)
        log("M_Splash_Foam_V2 已存在，复用")
        return m

    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_Splash_Foam_V2", MATDIR,
        unreal.Material, unreal.MaterialFactoryNew())
    if not m:
        log("!! 材质创建失败")
        return None

    def add(cls, x, y):
        return MEL.create_material_expression(m, cls, x, y)

    # UV 平铺 ×3（气泡更密）—— TC 节点自带 tiling，直接接贴图 UVs
    tc = add(unreal.MaterialExpressionTextureCoordinate, -900, -100)
    tc.set_editor_property("u_tiling", 3.0)
    tc.set_editor_property("v_tiling", 3.0)

    tex = add(unreal.MaterialExpressionTextureSample, -600, -100)
    tex.set_editor_property("texture", t)
    MEL.connect_material_expressions(tc, "UVs", tex, "UVs")

    # BaseColor = 浅底 + 气泡×0.5
    base = add(unreal.MaterialExpressionConstant3Vector, -600, 140)
    base.set_editor_property("constant", unreal.LinearColor(0.30, 0.48, 0.55, 1.0))
    bs = add(unreal.MaterialExpressionConstant, -400, 40)
    bs.set_editor_property("r", 0.5)
    bm = add(unreal.MaterialExpressionMultiply, -250, -100)
    MEL.connect_material_expressions(tex, "RGB", bm, "A")
    MEL.connect_material_expressions(bs, "", bm, "B")
    badd = add(unreal.MaterialExpressionAdd, -50, 0)
    MEL.connect_material_expressions(base, "", badd, "A")
    MEL.connect_material_expressions(bm, "", badd, "B")
    MEL.connect_material_property(badd, "", MP.MP_BASE_COLOR)

    # Emissive = 气泡 × 0.05
    es = add(unreal.MaterialExpressionConstant, -400, 260)
    es.set_editor_property("r", 0.05)
    em = add(unreal.MaterialExpressionMultiply, -250, 220)
    MEL.connect_material_expressions(tex, "RGB", em, "A")
    MEL.connect_material_expressions(es, "", em, "B")
    MEL.connect_material_property(em, "", MP.MP_EMISSIVE_COLOR)

    # Roughness
    rg = add(unreal.MaterialExpressionConstant, -250, 400)
    rg.set_editor_property("r", 0.55)
    MEL.connect_material_property(rg, "", MP.MP_ROUGHNESS)

    MEL.recompile_material(m)
    EAL.save_asset(NEW, only_if_is_dirty=False)
    log("新建 M_Splash_Foam_V2（节点 %d 个）" % len(MEL.get_material_expressions(m)))
    return m


def apply_to_actors(m):
    if not m:
        return
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(LEVEL)
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for a in sub.get_all_level_actors():
        label = a.get_actor_label()
        if "Splash_Foam" not in label:
            continue
        if a.get_class().get_name() != "StaticMeshActor":
            continue
        c = a.static_mesh_component
        # 用 override_materials 覆盖，不动资产本身
        c.set_editor_property("override_materials", [m])
        n += 1
        log("  %s -> M_Splash_Foam_V2" % label)
    log("应用 %d 个泡沫圆盘" % n)
    les.save_current_level()
    log("已保存关卡")


m = build_material()
apply_to_actors(m)
with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("SPLASH_V2_DONE")
