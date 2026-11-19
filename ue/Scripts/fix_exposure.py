# -*- coding: utf-8 -*-
"""还原后处理曝光参数（撤销上一次"归零后处理"的实验）。

实验结论（2026-10-25）：把 AutoExposureApplyPhysicalCameraExposure 关掉 +
Bloom 归零之后，画面变成 99% 纯白 —— 说明这套工程的亮度主要由
**Histogram 自动曝光**在控制，而不是我们写在 PPV 里的那组数。
（Manual + Bias 的值确实生效过，但这个开关会让手动曝光失效。）

所以恢复：Method = Manual、Bias = 4.3、关掉物理相机曝光开关的覆盖、
Bloom 回到温和值。

运行：
    bash tools/ue_py.sh ue/Scripts/fix_exposure.py "曝光还原"
"""
import unreal

L = "[曝光还原]"
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"

unreal.EditorLevelLibrary.load_level(LEVEL)

BIAS = 4.3
BLOOM = 0.35
THRESHOLD = 1.4

n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "PostProcessVolume":
        continue
    st = a.get_editor_property("settings")
    st.set_editor_property("override_auto_exposure_method", True)
    st.set_editor_property("auto_exposure_method",
                           unreal.AutoExposureMethod.AEM_MANUAL)
    st.set_editor_property("override_auto_exposure_bias", True)
    st.set_editor_property("auto_exposure_bias", BIAS)
    st.set_editor_property("override_auto_exposure_apply_physical_camera_exposure",
                           False)
    st.set_editor_property("override_bloom_intensity", True)
    st.set_editor_property("bloom_intensity", BLOOM)
    st.set_editor_property("override_bloom_threshold", True)
    st.set_editor_property("bloom_threshold", THRESHOLD)
    a.set_editor_property("settings", st)
    n += 1
    unreal.log("%s %s: manual bias=%.2f bloom=%.2f/%.2f"
               % (L, a.get_actor_label(), BIAS, BLOOM, THRESHOLD))

unreal.EditorLevelLibrary.save_current_level()
unreal.log("%s 处理 %d 个后处理体" % (L, n))
