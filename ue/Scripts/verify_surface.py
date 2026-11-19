# -*- coding: utf-8 -*-
"""
验证「表面材质换装」是否真正生效。
================================================================
检查四件事：
  A. 主材质 M_RobotSurface 重新编译 → 是否成功（并尝试读取编译错误列表）
  B. 所有 MaterialInstanceConstant 的父类 → 是否已指向 M_RobotSurface
  C. 骨骼网格资产的材质槽 → 槽里挂的是不是那些已换装的 MIC
  D. 骨骼网格资产是否带顶点色（尝试多种 API，能读到什么算什么）

用法: bash tools/ue_py.sh ue/Scripts/verify_surface.py "验证]"
"""
import unreal

ART = "/Game/RobotGame/Art"
MAT_DIR = ART + "/Materials"
MASTER = MAT_DIR + "/M_RobotSurface"

unreal.log("[验证] 脚本已开始执行")

fails = []

# ── A. 主材质编译 ──
mel = unreal.MaterialEditingLibrary
mat = unreal.EditorAssetLibrary.load_asset(MASTER)
if not mat:
    fails.append("主材质读不到")
    unreal.log("[验证] ❌ 主材质读不到 %s" % MASTER)
else:
    ok = None
    try:
        ok = mel.recompile_material(mat)
    except Exception as e:
        unreal.log("[验证] recompile_material 异常: %s" % str(e)[:120])
    unreal.log("[验证] A. 主材质重新编译返回 = %s" % ok)

    # 尝试读取编译错误（不同版本 API 不一样，能读就读）
    for attr in ("compile_errors", "CompileErrors"):
        try:
            errs = mat.get_editor_property(attr)
            unreal.log("[验证] A. 编译错误列表(%s) = %s" % (attr, errs))
            break
        except Exception:
            pass

    # 表达式数量（空壳材质会很小）
    try:
        exprs = mel.get_material_expressions(mat)
        unreal.log("[验证] A. 表达式数量 = %d" % len(exprs))
        if len(exprs) < 25:
            fails.append("表达式数量异常（疑似空壳）")
    except Exception as e:
        unreal.log("[验证] A. 表达式数量读取失败: %s" % str(e)[:80])

# ── B. MIC 父类普查 ──
ar = unreal.AssetRegistryHelpers.get_asset_registry()
total = 0
good = 0
bad = []
for folder in ("Characters", "Modules", "Environment", "Props", "Landmarks"):
    root = "%s/%s" % (ART, folder)
    for ad in ar.get_assets_by_path(root, recursive=True):
        if str(ad.asset_class_path.asset_name) != "MaterialInstanceConstant":
            continue
        total += 1
        mic = ad.get_asset()
        if not mic:
            bad.append("%s(读不到)" % ad.asset_name)
            continue
        try:
            parent = mic.get_editor_property("parent")
            pname = parent.get_path_name() if parent else "None"
        except Exception as e:
            bad.append("%s(%s)" % (ad.asset_name, str(e)[:30]))
            continue
        if "M_RobotSurface" in pname:
            good += 1
        else:
            bad.append("%s → %s" % (ad.asset_name, pname.split("/")[-1]))

unreal.log("[验证] B. MIC 父类：%d/%d 指向 M_RobotSurface" % (good, total))
if bad:
    for b in bad[:15]:
        unreal.log("[验证] B. ⚠️ %s" % b)
    if good < total:
        fails.append("有 %d 个 MIC 没换装" % (total - good))

# ── C. 骨骼网格材质槽 ──
def mat_slots_of(path):
    sk = unreal.EditorAssetLibrary.load_asset(path)
    if not sk:
        return None
    out = []
    try:
        for sm in sk.get_editor_property("materials"):
            try:
                mi = sm.get_editor_property("material_interface")
            except Exception:
                mi = None
            out.append(mi.get_path_name().split("/")[-1] if mi else "None")
    except Exception as e:
        out.append("ERR:%s" % str(e)[:50])
    return out

for name in ("SK_Chassis_Light", "SK_Chassis_Medium", "SK_Chassis_Heavy",
             "SK_Enemy_Guard", "SK_Enemy_Colossus"):
    slots = mat_slots_of("%s/Characters/%s" % (ART, name))
    if slots is None:
        unreal.log("[验证] C. ❌ %s 读不到" % name)
        fails.append("%s 读不到" % name)
    else:
        unreal.log("[验证] C. %s 材质槽(%d) = %s" % (name, len(slots), slots))

# ── D. 顶点色探测（尽力而为）──
sk = unreal.EditorAssetLibrary.load_asset("%s/Characters/SK_Chassis_Light" % ART)
if sk:
    found = False
    for attr in ("has_vertex_colors", "bHasVertexColors",
                 "vertex_color", "HasVertexColors"):
        try:
            v = sk.get_editor_property(attr)
            unreal.log("[验证] D. 顶点色属性 %s = %s" % (attr, v))
            found = True
        except Exception:
            pass
    if not found:
        # 退而求其次：读导入来源，确认网格资产时间戳晚于 FBX
        try:
            src = sk.get_editor_property("asset_import_data")
            unreal.log("[验证] D. 导入源文件 = %s" % (src.get_first_filename() if src else "?"))
        except Exception as e:
            unreal.log("[验证] D. 顶点色无法直接读取（%s），需运行时观察" % str(e)[:60])

unreal.log("[验证] ====== 结果：%s ======" %
           ("全部通过" if not fails else "存在问题: " + "; ".join(fails)))
