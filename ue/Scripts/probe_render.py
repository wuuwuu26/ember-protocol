# -*- coding: utf-8 -*-
"""探查 UE 实际渲染能力（光追/Lumen/RHI），为光影打磨定方案。"""
import unreal

out = []

# 实际 RHI / 特性级别
for fn, label in [
    (lambda: unreal.SystemLibrary.get_rhi_name(), "RHI"),
    (lambda: unreal.SystemLibrary.get_rhi_feature_level(), "FeatureLevel"),
]:
    try:
        out.append("%-12s = %s" % (label, fn()))
    except Exception as e:
        out.append("%-12s err %s" % (label, e))

# 关键 CVar
CVARS = [
    "r.RayTracing",
    "r.RayTracing.Shadows",
    "r.RayTracing.AmbientOcclusion",
    "r.RayTracing.Reflections",
    "r.Lumen.Reflections.Allow",
    "r.Lumen.Reflections.ScreenTraces",
    "r.DynamicGlobalIlluminationMethod",
    "r.ReflectionMethod",
    "r.Shadow.Virtual.Enable",
    "r.DefaultFeature.AutoExposure",
    "r.GenerateMeshDistanceFields",
]
for c in CVARS:
    try:
        v = unreal.SystemLibrary.get_console_variable_value(c)
        out.append("%-42s = %s" % (c, v))
    except Exception as e:
        out.append("%-42s err %s" % (c, str(e)[:40]))

# 渲染设置（项目默认）
try:
    r = unreal.get_default_object(unreal.RendererSettings)
    for p in ("default_feature_level", "ray_tracing", "support_global_clip_planes"):
        try:
            out.append("RendererSettings.%s = %s" % (p, r.get_editor_property(p)))
        except Exception:
            pass
except Exception as e:
    out.append("RendererSettings err %s" % e)

# 关卡里的光源类型统计
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
counts = {}
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    cls = a.get_class().get_name()
    if "Light" in cls:
        counts[cls] = counts.get(cls, 0) + 1
out.append("")
out.append("关卡光源统计：")
for k, v in sorted(counts.items()):
    out.append("  %-24s %d" % (k, v))

with open(r"C:\Users\25227\Documents\robot_game\docs\render_probe.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("RENDER_PROBE_DONE")
