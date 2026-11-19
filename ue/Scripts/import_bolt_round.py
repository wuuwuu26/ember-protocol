# -*- coding: utf-8 -*-
"""
导入弹丸资产 + 建材质。
================================================================
1. 导入 Blender 生成的 SM_Bolt_Round（3 个材质槽：壳 / 曳光 / 抛光环）
2. 导入 Krea 2 生成的钛合金贴图、法线、等离子贴图
3. 建 PBR 弹壳材质 + 两套 Unlit 曳光材质（玩家青白 / 敌人橙金）
4. 把默认材质绑到静态网格槽上（C++ 运行时还会按阵营再设一次）

用法: bash tools/ue_py.sh ue/Scripts/import_bolt_round.py "BOLTROUND_OK"
"""
import os
import unreal

L = "[弹丸资产]"
MAT_DIR = "/Game/RobotGame/Art/Materials"
PROP_DIR = "/Game/RobotGame/Art/Props"
FBX = r"C:\Users\25227\Documents\robot_game\assets\out\bolt_round.fbx"
TEX = r"C:\Users\25227\Documents\robot_game\assets\tex"

sub = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary


def log(m):
    unreal.log("%s %s" % (L, m))


# ══════════════════════════════════════════════════════════
# 贴图
# ══════════════════════════════════════════════════════════
def import_tex(fname, name, normal=False):
    src = os.path.join(TEX, fname)
    path = "%s/%s" % (MAT_DIR, name)
    if not os.path.exists(src):
        log("!! 缺源图 %s" % src)
        return None
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        sub.delete_asset(path)
    task = unreal.AssetImportTask()
    task.filename = src
    task.destination_path = MAT_DIR
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True
    tools.import_asset_tasks([task])
    t = unreal.EditorAssetLibrary.load_asset(path)
    if not t:
        log("!! 导入失败 %s" % name)
        return None
    try:
        t.set_editor_property("srgb", not normal)
        t.set_editor_property("never_stream", True)
        t.set_editor_property("max_texture_size", 2048)
        t.set_editor_property("filter", unreal.TextureFilter.TF_TRILINEAR)
        if normal:
            t.set_editor_property(
                "compression_settings",
                unreal.TextureCompressionSettings.TC_NORMALMAP)
        else:
            t.set_editor_property(
                "compression_settings",
                unreal.TextureCompressionSettings.TC_BC7)
    except Exception as e:
        log("  贴图设置告警 %s: %s" % (name, str(e)[:70]))
    unreal.EditorAssetLibrary.save_loaded_asset(t)
    try:
        w, h = t.blueprint_get_size_x(), t.blueprint_get_size_y()
    except Exception:
        w = h = -1
    log("贴图 %-16s %dx%d  normal=%s" % (name, w, h, normal))
    return t


tex_metal = import_tex("bolt_metal.png", "T_BoltMetal")
tex_normal = import_tex("bolt_metal_n.png", "T_BoltMetal_N", normal=True)
tex_plasma = import_tex("bolt_plasma.png", "T_BoltPlasma")


# ══════════════════════════════════════════════════════════
# 材质工具
# ══════════════════════════════════════════════════════════
def new_mat(name):
    path = "%s/%s" % (MAT_DIR, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        sub.delete_asset(path)
    return tools.create_asset(name, MAT_DIR, unreal.Material,
                              unreal.MaterialFactoryNew())


def c3(m, x, y, z, px, py):
    e = mel.create_material_expression(
        m, unreal.MaterialExpressionConstant3Vector, px, py)
    e.set_editor_property("constant", unreal.LinearColor(x, y, z, 1.0))
    return e


def c1(m, v, px, py):
    e = mel.create_material_expression(
        m, unreal.MaterialExpressionConstant, px, py)
    e.set_editor_property("r", v)
    return e


def mul(m, a, b, px, py):
    e = mel.create_material_expression(
        m, unreal.MaterialExpressionMultiply, px, py)
    mel.connect_material_expressions(a, "", e, "A")
    mel.connect_material_expressions(b, "", e, "B")
    return e


def add(m, a, b, px, py):
    e = mel.create_material_expression(
        m, unreal.MaterialExpressionAdd, px, py)
    mel.connect_material_expressions(a, "", e, "A")
    mel.connect_material_expressions(b, "", e, "B")
    return e


def tex_sample(m, tex, px, py):
    e = mel.create_material_expression(
        m, unreal.MaterialExpressionTextureSample, px, py)
    e.set_editor_property("texture", tex)
    return e


def save_mat(m, name):
    mel.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m)
    log("材质 %s OK" % name)


# ══════════════════════════════════════════════════════════
# 1. 弹壳：PBR 钛合金
# ══════════════════════════════════════════════════════════
def make_shell(name="M_Bolt_Shell", rough=0.30, tint=None):
    m = new_mat(name)
    m.set_editor_property("shading_model",
                          unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    m.set_editor_property("two_sided", False)

    if tint:
        base = c3(m, tint[0], tint[1], tint[2], -620, -80)
    elif tex_metal:
        s = tex_sample(m, tex_metal, -900, -60)
        base = s
    else:
        base = c3(m, 0.20, 0.22, 0.25, -620, -80)
    mel.connect_material_property(base, "RGB" if not tint else "",
                                  unreal.MaterialProperty.MP_BASE_COLOR)

    mel.connect_material_property(c1(m, 0.92, -620, 120), "",
                                  unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(c1(m, rough, -620, 200), "",
                                  unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(c1(m, 1.0, -620, 280), "",
                                  unreal.MaterialProperty.MP_SPECULAR)

    if tex_normal:
        n = tex_sample(m, tex_normal, -900, 340)
        mel.connect_material_property(n, "RGB",
                                      unreal.MaterialProperty.MP_NORMAL)
    save_mat(m, name)
    return m


shell_mat = make_shell("M_Bolt_Shell", rough=0.30)
trim_mat = make_shell("M_Bolt_Trim", rough=0.13,
                      tint=(0.52, 0.55, 0.60))


# ══════════════════════════════════════════════════════════
# 2. 曳光：Unlit 等离子带（按阵营染色）
# ══════════════════════════════════════════════════════════
def make_glow(name, color, boost=2.6):
    m = new_mat(name)
    m.set_editor_property("shading_model",
                          unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", False)

    if tex_plasma:
        s = tex_sample(m, tex_plasma, -900, 0)
        # 曳光带只有 2cm 宽，原始 UV 在 V 方向只采到很薄一条，看起来像纯色。
        # 把等离子贴图在 U（绕一圈）方向铺 3 次，丝状结构才会显出来。
        tc = mel.create_material_expression(
            m, unreal.MaterialExpressionTextureCoordinate, -1120, 120)
        tc.set_editor_property("u_tiling", 3.0)
        tc.set_editor_property("v_tiling", 2.0)
        try:
            mel.connect_material_expressions(tc, "", s, "UVs")
        except Exception as e:
            log("等离子 UV 平铺连接告警: %s" % str(e)[:70])
        # 贴图是灰度丝状 → 提高对比，只让丝发亮
        a = mul(m, s, c1(m, 180.0, -700, 120), -700, 0)
        # 底色抬到 55：等离子贴图的暗区不至于把整条曳光带压成哑光漆。
        b = add(m, a, c1(m, 55.0, -560, 120), -560, 0)
        c = mul(m, b, c1(m, boost, -420, 120), -420, 0)
        glow = mul(m, c, c3(m, color[0], color[1], color[2], -700, 220),
                   -260, 60)
    else:
        glow = c3(m, color[0] * 260.0, color[1] * 260.0,
                  color[2] * 260.0, -420, 0)

    mel.connect_material_property(glow, "",
                                  unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    save_mat(m, name)
    return m


glow_player = make_glow("M_Bolt_Glow_Player", (0.30, 0.88, 1.00), boost=2.6)
# 敌人橙金：原来的 (1.0,0.40,0.06) 在夜景里偏暗红，绿通道抬到 0.62 才是"金"。
glow_enemy = make_glow("M_Bolt_Glow_Enemy", (1.00, 0.62, 0.14), boost=3.4)


# ══════════════════════════════════════════════════════════
# 3. 静态网格
# ══════════════════════════════════════════════════════════
sm_path = "%s/SM_Bolt_Round" % PROP_DIR
if unreal.EditorAssetLibrary.does_asset_exist(sm_path):
    sub.delete_asset(sm_path)

task = unreal.AssetImportTask()
task.filename = FBX
task.destination_path = PROP_DIR
task.destination_name = "SM_Bolt_Round"
task.automated = True
task.save = True
task.replace_existing = True

ui = unreal.FbxImportUI()
ui.import_mesh = True
ui.import_materials = False
ui.import_textures = False
ui.import_animations = False
ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
try:
    data = getattr(ui, "static_mesh_import_data", None)
    if data:
        data.set_editor_property("import_uniform_scale", 1.0)
        data.set_editor_property("combine_meshes", True)
        data.set_editor_property("generate_lightmap_u_vs", True)
        try:
            data.set_editor_property("convert_scene", True)
        except Exception:
            pass
except Exception as e:
    log("静态网格导入参数告警: %s" % str(e)[:80])
task.options = ui

tools.import_asset_tasks([task])
sm = unreal.EditorAssetLibrary.load_asset(sm_path)
if not sm:
    raise RuntimeError("SM_Bolt_Round 导入失败")

bounds = sm.get_bounds()
ext = bounds.box_extent
log("网格包围盒 中心=%s 半径=%.1fcm  半长 X=%.1f Y=%.1f Z=%.1f"
    % (bounds.origin, bounds.sphere_radius, ext.x, ext.y, ext.z))

slots = sm.get_editor_property("static_materials")
log("材质槽数量=%d" % len(slots))
for i, s in enumerate(slots):
    log("  槽%d: %s" % (i, s.get_editor_property("material_slot_name")))

# 按顺序绑定：壳 / 曳光 / 抛光环
want = [shell_mat, glow_player, trim_mat]
for i in range(len(slots)):
    if i < len(want) and want[i]:
        slots[i].set_editor_property("material_interface", want[i])
sm.set_editor_property("static_materials", slots)
unreal.EditorAssetLibrary.save_loaded_asset(sm)

# 灯光/流送标记，方便后面排查
log("SM_Bolt_Round 就绪  槽0=%s 槽1=%s 槽2=%s"
    % (want[0].get_name() if want[0] else "-",
       want[1].get_name() if want[1] else "-",
       want[2].get_name() if want[2] else "-"))

with open(r"C:\Users\25227\Documents\robot_game\docs\bolt_round.txt",
          "w", encoding="utf-8") as f:
    f.write("SM_Bolt_Round extent=(%.1f, %.1f, %.1f) slots=%d\nBOLTROUND_OK\n"
            % (ext.x, ext.y, ext.z, len(slots)))

unreal.log("%s BOLTROUND_OK" % L)
