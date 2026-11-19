# -*- coding: utf-8 -*-
"""
重新导入细节贴图（4K）。
================================================================
两个必须做的动作：

1. **先删再导**。UE 的导入器遇到"源文件没变"的资产会跳过重建，
   一旦某次导入失败留下 32×32 占位图，就永远修不好 ——
   机体贴图就这样一直是 32×32 的空白图（T_MechDetail 实测 32x32）。

2. **显式设 max_texture_size / never_stream**。4K 贴图默认会走
   texture streaming，在某些画质档位下只加载低 mip —— 看起来就像
   "纹理没加载出来"。这四张图总共约 80MB 显存，直接常驻更省心。

用法: bash tools/ue_py.sh ue/Scripts/reimport_tex.py "贴图重导"
"""
import unreal

L = "[贴图重导]"
D = "/Game/RobotGame/Art/Materials"
TEX = r"C:/Users/25227/Documents/robot_game/assets/tex"
sub = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)

JOBS = [
    ("mech_detail.png",     "T_MechDetail",     False, True),
    ("mech_detail_n.png",   "T_MechDetail_N",   True,  True),
    ("env_detail.png",      "T_EnvDetail",      False, True),
    ("env_detail_n.png",    "T_EnvDetail_N",    True,  True),
    # 多套表面（每类物体用自己的纹理，而不是全场一张壁纸）
    ("paint_detail.png",    "T_PaintDetail",    False, True),
    ("paint_detail_n.png",  "T_PaintDetail_N",  True,  True),
    ("concrete_detail.png", "T_ConcreteDetail", False, True),
    ("concrete_detail_n.png", "T_ConcreteDetail_N", True, True),
    ("rust_detail.png",     "T_RustDetail",     False, True),
    ("rust_detail_n.png",   "T_RustDetail_N",   True,  True),
]

# 先删
for _, name, _, _ in JOBS:
    p = "%s/%s" % (D, name)
    if unreal.EditorAssetLibrary.does_asset_exist(p):
        sub.delete_asset(p)
        unreal.log("%s 删除旧资产 %s" % (L, name))

tools = unreal.AssetToolsHelpers.get_asset_tools()
for fname, name, is_norm, _ in JOBS:
    task = unreal.AssetImportTask()
    task.filename = "%s\\%s" % (TEX, fname)
    task.destination_path = D
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True
    tools.import_asset_tasks([task])

    t = unreal.EditorAssetLibrary.load_asset("%s/%s" % (D, name))
    if not t:
        unreal.log("%s ❌ %s 导入后不存在" % (L, name))
        continue

    def st(attr, val):
        try:
            t.set_editor_property(attr, val)
        except Exception as e:
            unreal.log("%s   %s 设置失败: %s" % (L, attr, str(e)[:50]))

    st("srgb", False)
    st("max_texture_size", 4096)
    # ⚠️ 这几张是**打包贴图**（R 板面亮度 / G 粗糙 / B 磨损 / A 高度），
    #    必须用 BC7（RGBA 各 8bit）。
    #
    #    之前用的是 TC_GRAYSCALE —— 它在 UE 里是 BC4，**只存一个通道**，
    #    再把那一个通道复制到 RGB，A 直接丢弃。结果：
    #      · 板面亮度 / 粗糙 / 磨损 三个通道变成同一个值
    #      · 高度（A）归零 → 法线全平 → 倒角和凹槽完全看不见
    #    这就是"纹理不像装甲"的第二个真因（第一个是 UV 归一化）。
    if is_norm:
        comp = unreal.TextureCompressionSettings.TC_NORMALMAP
    else:
        comp = getattr(unreal.TextureCompressionSettings, "TC_BC7",
                       unreal.TextureCompressionSettings.TC_DEFAULT)
    st("compression_settings", comp)
    st("never_stream", True)          # 不走流送，避免"加载不出来"
    st("filter", unreal.TextureFilter.TF_TRILINEAR)
    st("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)

    unreal.EditorAssetLibrary.save_loaded_asset(t)
    try:
        w, h = t.blueprint_get_size_x(), t.blueprint_get_size_y()
    except Exception:
        w = h = -1
    unreal.log("%s %-16s %dx%d  never_stream=%s"
               % (L, name, w, h, t.get_editor_property("never_stream")))
