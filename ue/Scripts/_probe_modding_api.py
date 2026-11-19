# -*- coding: utf-8 -*-
"""探测改装数据脚本需要的 Python API 细节（一次性诊断）。"""
import unreal

unreal.log("[探针] 开始")

# 1) ModuleSlot 枚举的全部取值
try:
    vals = [a for a in dir(unreal.ModuleSlot) if not a.startswith("_")]
    unreal.log("[探针] ModuleSlot 枚举值: %s" % vals)
except Exception as e:
    unreal.log("[探针] ModuleSlot 读取失败: %s" % e)

# 2) ModuleSlotDef 结构可用属性
try:
    d = unreal.ModuleSlotDef()
    props = [p for p in unreal.ModuleSlotDef.get_editor_property.__doc__ or ""]
    unreal.log("[探针] ModuleSlotDef 可实例化 OK")
    for attr in ("slot", "accepted_module_types", "Slot", "AcceptedModuleTypes"):
        try:
            v = d.get_editor_property(attr)
            unreal.log("[探针]   ModuleSlotDef.%s = %s" % (attr, v))
        except Exception:
            pass
except Exception as e:
    unreal.log("[探针] ModuleSlotDef 失败: %s" % e)

# 3) 现有模块资产（上次部分创建成功的）
for name in ("MOD_Head_Scout", "MOD_Arm_Mining", "MOD_Thr_Cannon"):
    p = "/Game/RobotGame/Data/Modules/%s" % name
    a = unreal.EditorAssetLibrary.load_asset(p)
    unreal.log("[探针] %s 存在=%s" % (name, a is not None))

# 4) ModuleData 的属性名回读（用已有资产）
a = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Data/Modules/MOD_Head_Scout")
if a:
    for attr in ("display_name", "target_slot", "module_type", "mass",
                 "power_draw"):
        try:
            unreal.log("[探针]   %s = %s" % (attr, a.get_editor_property(attr)))
        except Exception as e:
            unreal.log("[探针]   %s 读取失败: %s" % (attr, str(e)[:60]))

unreal.log("[探针] 完成")
