# -*- coding: utf-8 -*-
"""重建 Poly Haven 材质（修正版，第一百零六轮）。

上一版 bug：
  - ComponentMask 用 set_editor_property({R:r,...}, True) 但没显式关掉其他通道，
    实际生成的是 RG / RG / RGB，AO/Rough/Metal 拆分全错。
  - 这次显式把 r/g/b/a 四个布尔值全部赋值，只留目标通道为 True。

贴图已导入（import_polyhaven.py 的第一部分），这里只重建材质，不重复导入贴图。
"""
import unreal

DEST = "/Game/RobotGame/Art/Materials/PolyHaven"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\polyhaven_matbuild.txt"

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
MP = unreal.MaterialProperty
lines = []


def log(s):
    unreal.log("[PolyMatBuild] %s" % s)
    lines.append(str(s))


MAT_DESC = [
    ("concrete_floor_02", "工业混凝土地面"),
    ("concrete_wall_001", "风化混凝土墙"),
    ("factory_wall", "工厂金属墙"),
    ("rusty_metal", "锈铁"),
    ("corrugated_iron", "波纹铁皮"),
    ("metal_grate_rusty", "锈金属格栅"),
]


def load_tex(aid, suffix):
    return EAL.load_asset("%s/%s/%s_%s" % (DEST, aid, aid, suffix))


for aid, desc in MAT_DESC:
    mat_path = "%s/M_%s" % (DEST, aid)
    if EAL.does_asset_exist(mat_path):
        EAL.delete_asset(mat_path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_%s" % aid, DEST, unreal.Material, unreal.MaterialFactoryNew())
    if not mat:
        log("!! 材质创建失败 %s" % aid)
        continue

    def sample(suffix, y):
        t = load_tex(aid, suffix)
        if not t:
            log("  !! %s 缺 %s" % (aid, suffix))
            return None
        n = MEL.create_material_expression(
            mat, unreal.MaterialExpressionTextureSample, -700, y)
        n.set_editor_property("texture", t)
        # 非颜色贴图关 sRGB（导入时已设，这里再保一次）
        if suffix != "BaseColor":
            try:
                t.set_editor_property("srgb", False)
            except Exception:
                pass
        return n

    bc = sample("BaseColor", -300)
    nm = sample("Normal", 0)
    arm = sample("ARM", 300)

    if bc:
        MEL.connect_material_property(bc, "RGB", MP.MP_BASE_COLOR)
    if nm:
        MEL.connect_material_property(nm, "RGB", MP.MP_NORMAL)

    if arm:
        # ARM: R=AO, G=Roughness, B=Metallic。显式设置四个通道布尔值。
        chan_specs = [
            ("r", MP.MP_AMBIENT_OCCLUSION, 300),
            ("g", MP.MP_ROUGHNESS, 460),
            ("b", MP.MP_METALLIC, 620),
        ]
        for target, prop, yy in chan_specs:
            mask = MEL.create_material_expression(
                mat, unreal.MaterialExpressionComponentMask, -400, yy)
            mask.set_editor_property("r", target == "r")
            mask.set_editor_property("g", target == "g")
            mask.set_editor_property("b", target == "b")
            mask.set_editor_property("a", False)
            # ⚠️ ComponentMask 的输入引脚名必须是 ""（不是 "Input"）。
            # UE5.8 下 mask 的 input name 实际为 None，用 "Input" 会连接失败，
            # 导致 SM5 编译报 "(Node ComponentMask) Missing ComponentMask input"，
            # 材质回退默认灰。第一百二十一 轮踩坑并修复。
            MEL.connect_material_expressions(arm, "RGB", mask, "")
            MEL.connect_material_property(mask, "", prop)

    MEL.recompile_material(mat)
    EAL.save_asset(mat_path, only_if_is_dirty=False)
    log("M_%s (%s) 6 节点" % (aid, desc))

with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("POLY_MATBUILD_DONE")
