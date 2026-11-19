# -*- coding: utf-8 -*-
"""把后处理里的"锐化"关掉，修掉几何边缘的黑边/白边。

现象：场景里所有硬边（墙的转折、集装箱边框、机体装甲边缘）都带一圈黑边，
看起来像"描了线"，金属件像贴图一样薄。

根因：后处理的 Sharpen（默认 0.55）是一个**反锐化掩模**：它取原图减去
模糊图，把差值放大后加回去。对照片是"提细节"，但对**高对比度的硬边**
（脚本生成的方块几何体全是这种边）会过冲 —— 暗面一侧被拉到负值后
被截断成纯黑、亮面一侧被拉到过曝，于是就出现了黑边。

UE 里对硬边最友好的做法是**不开锐化**，而是让 TSR 自己保边
（r.TSR.Sharpness）。所以这里把 PPV 的 Sharpen 归零。

同时把泛光阈值抬到 1.2：现在地面的高光已经到 0.997，阈值 1.0 会让
整块亮地板都进泛光，画面糊成一片糖霜感。

运行：
    bash tools/ue_py.sh ue/Scripts/fix_sharpen.py "锐化"
"""
import unreal

L = "[锐化]"
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"

unreal.EditorLevelLibrary.load_level(LEVEL)

SHARPEN = 0.0
BLOOM_THRESHOLD = 1.2
BLOOM_INTENSITY = 0.42

n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "PostProcessVolume":
        continue
    st = a.get_editor_property("settings")
    st.set_editor_property("override_sharpen", True)
    st.set_editor_property("sharpen", SHARPEN)
    st.set_editor_property("override_bloom_threshold", True)
    st.set_editor_property("bloom_threshold", BLOOM_THRESHOLD)
    st.set_editor_property("override_bloom_intensity", True)
    st.set_editor_property("bloom_intensity", BLOOM_INTENSITY)
    a.set_editor_property("settings", st)
    unreal.log("%s PPV %s: sharpen=%.2f bloom=%.2f/%.2f"
               % (L, a.get_actor_label(), SHARPEN, BLOOM_INTENSITY,
                  BLOOM_THRESHOLD))
    n += 1

unreal.EditorLevelLibrary.save_current_level()
unreal.log("%s 处理 %d 个后处理体" % (L, n))
