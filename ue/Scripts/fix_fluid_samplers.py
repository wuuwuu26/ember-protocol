# -*- coding: utf-8 -*-
"""批量修复液体/池材质的 SM5 编译失败（第一百一十九轮·续 2）。

根因：一批材质里的 TextureSampleParameter2D 节点 sampler_type 被设成
  - SAMPLERTYPE_LINEAR_GRAYSCALE，但引用 T_Toxic_Bub(srgb=True) → 应为 Grayscale
  - SAMPLERTYPE_LINEAR_COLOR，但引用 T_ConcreteDetail(srgb=True) → 应为 Color
PCD3D_SM5 下 sampler 与贴图 sRGB 不匹配 → 材质编译失败 → 回退默认材质。
表现：圆形毒液池液面出现黄褐色斑驳反射、池壁/池底变默认灰。

修复：不重建材质（保留原泡沫/法线/Fresnel 设计），遍历所有
TextureSample(Parameter)2D 节点，按引用贴图的 srgb / compression 自动
重设 sampler_type，recompile + save。

覆盖材质：M_Toxic_Fluid / M_Coolant_Fluid / M_Toxic_Bed / M_Basin_Concrete
（后两者是池底/池壁，同样失败，一并修）。
"""
import unreal

MAT_DIR = "/Game/RobotGame/Art/Materials"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary

TARGETS = ("M_Toxic_Fluid", "M_Coolant_Fluid",
           "M_Toxic_Bed", "M_Basin_Concrete")
lines = []


def log(s):
    unreal.log("[FluidSamplerFix] %s" % s)
    lines.append(str(s))


def enum_val(cls, *keywords):
    """从枚举类里找名字同时包含所有关键字（大写）的成员值。"""
    for nm in dir(cls):
        if nm.startswith("_"):
            continue
        up = nm.upper()
        if all(k.upper() in up for k in keywords):
            return getattr(cls, nm), nm
    return None, None


def desired_sampler(tex):
    """按贴图 srgb / compression 返回应有的 sampler_type。"""
    S = unreal.MaterialSamplerType
    C = unreal.TextureCompressionSettings
    try:
        comp = tex.get_editor_property("compression_settings")
        srgb = tex.get_editor_property("srgb")
    except Exception:
        return None, None
    # 法线贴图
    if comp == C.TC_NORMALMAP:
        v, n = enum_val(S, "NORMAL")
        return v, n
    # 灰度贴图：sRGB 开→Grayscale，关→LinearGrayscale
    if comp == C.TC_GRAYSCALE:
        if srgb:
            v, n = enum_val_exact(S, "GRAYSCALE", exclude="LINEAR")
            return v, n
        else:
            v, n = enum_val(S, "LINEAR", "GRAYSCALE")
            return v, n
    # 彩色（BC7/Default）：sRGB 开→Color，关→LinearColor
    if srgb:
        v, n = enum_val_exact(S, "COLOR")
        return v, n
    else:
        v, n = enum_val(S, "LINEAR", "COLOR")
        return v, n


def enum_val_exact(cls, kw, exclude=None):
    for nm in dir(cls):
        if nm.startswith("_"):
            continue
        up = nm.upper()
        if kw.upper() not in up:
            continue
        if exclude and exclude.upper() in up:
            continue
        return getattr(cls, nm), nm
    return None, None


for name in TARGETS:
    p = "%s/%s" % (MAT_DIR, name)
    m = EAL.load_asset(p)
    if not m:
        log("!! 缺 %s" % name)
        continue
    try:
        exprs = list(MEL.get_material_expressions(m))
    except Exception as e:
        log("%s 取表达式失败 %s" % (name, str(e)[:60]))
        continue
    changed = 0
    for e in exprs:
        cls = e.get_class().get_name()
        if "TextureSample" not in cls:
            continue
        try:
            tex = e.get_editor_property("texture")
        except Exception:
            continue
        if not tex:
            continue
        cur = None
        try:
            cur = e.get_editor_property("sampler_type")
        except Exception:
            pass
        want, want_name = desired_sampler(tex)
        if want is None:
            continue
        if cur == want:
            continue
        try:
            e.set_editor_property("sampler_type", want)
            changed += 1
            log("  %s: %s  sampler -> %s" % (
                name, tex.get_name(), want_name))
        except Exception as ex2:
            log("  %s: 设 sampler 失败 %s" % (name, str(ex2)[:60]))
    if changed:
        MEL.recompile_material(m)
        EAL.save_loaded_asset(m)
    log("%s 修正 %d 个节点，recompile+save" % (name, changed))

with open(r"C:\Users\25227\Documents\robot_game\docs\fluid_sampler_fix.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("FLUID_SAMPLER_FIX_DONE")
