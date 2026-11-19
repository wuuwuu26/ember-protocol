# -*- coding: utf-8 -*-
"""打印每个材质资产的类 / 父类 / 参数，用来把 BaseColor 等读出来。

【重要发现】这批资产的材质**全是 MaterialInstanceConstant**，不是 Material ——
FBX 导入器给每个 Blender 材质建了一个实例，真正的 Master 是引擎侧生成的。
所以筛选条件必须带上 MaterialInstanceConstant，只认 "Material" 会得到 0 个。

为什么要读而不是抄 Blender 源码：抄错一个数，整台机器的配色就变了，
而且很难发现（看起来"就是有点不对"）。这里直接从资产里读。

用法: bash tools/ue_py.sh ue/Scripts/probe_mat_struct.py "材质结构"
"""
import unreal

ROOTS = ["/Game/RobotGame/Art/Characters", "/Game/RobotGame/Art/Environment",
         "/Game/RobotGame/Art/Props", "/Game/RobotGame/Art/Modules"]

unreal.log("[材质结构] 脚本已开始执行")


def log(m):
    unreal.log("[材质结构] %s" % m)


def dump_params(inst):
    """打印材质实例上的标量/向量/贴图参数覆盖。"""
    for getter, tag in (
            (unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value, "S"),
            (unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value, "V"),
    ):
        pass
    # 直接枚举已知参数名（没有"列出全部覆盖"的 API，只能按父类的参数名查）
    parent = None
    try:
        parent = inst.get_editor_property("parent")
    except Exception:
        pass
    names = []
    if parent:
        try:
            for p in unreal.MaterialEditingLibrary.get_scalar_parameter_names(parent):
                names.append(("S", str(p)))
            for p in unreal.MaterialEditingLibrary.get_vector_parameter_names(parent):
                names.append(("V", str(p)))
        except Exception as e:
            log("      读父类参数名失败: %s" % str(e)[:60])
    for kind, nm in names:
        try:
            if kind == "S":
                v = unreal.MaterialEditingLibrary \
                    .get_material_instance_scalar_parameter_value(inst, nm)
                log("      S %s = %.4f" % (nm, v))
            else:
                v = unreal.MaterialEditingLibrary \
                    .get_material_instance_vector_parameter_value(inst, nm)
                log("      V %s = (%.4f,%.4f,%.4f,%.4f)"
                    % (nm, v.r, v.g, v.b, v.a))
        except Exception:
            pass


def main():
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    log("主函数开始")
    seen = set()
    for root in ROOTS:
        n_all = n_mat = 0
        for ad in ar.get_assets_by_path(root, recursive=True):
            n_all += 1
            cls = str(ad.asset_class_path.asset_name)
            if cls not in ("Material", "MaterialInstanceConstant"):
                continue
            n_mat += 1
            nm = str(ad.asset_name)
            if nm in seen:
                continue
            seen.add(nm)
            m = ad.get_asset()
            if not m:
                log("%s  <加载失败>" % nm)
                continue
            parent = None
            try:
                parent = m.get_editor_property("parent")
            except Exception:
                pass
            log("%s   [%s]  parent=%s"
                % (nm, cls, parent.get_name() if parent else "-"))
            if cls == "MaterialInstanceConstant":
                dump_params(m)
        log("  %s：资产 %d，材质 %d" % (root, n_all, n_mat))
    log("共 %d 个材质资产" % len(seen))


main()
