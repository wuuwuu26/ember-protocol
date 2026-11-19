# -*- coding: utf-8 -*-
"""列出项目里所有材质资产，按目录分组。

为什么要这个：要给机体/环境套"表面细节材质"，必须先把**现有材质名**
摸清楚 —— 换装是按名字匹配的，漏一个就有一整块板子保持原样。
另外也用来确认 Blender 侧导出的材质确实都进来了。

用法: UnrealEditor-Cmd.exe <项目> -ExecutePythonScript="<本文件>"
"""
import unreal

ROOTS = [
    "/Game/RobotGame/Art/Characters",
    "/Game/RobotGame/Art/Environment",
    "/Game/RobotGame/Art/Props",
    "/Game/RobotGame/Art/Modules",
]


def log(m):
    unreal.log("[材质清单] %s" % m)
    print("[材质清单] %s" % m)


def main():
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    seen = {}
    for root in ROOTS:
        names = []
        for ad in ar.get_assets_by_path(root, recursive=True):
            cls = str(ad.asset_class_path.asset_name)
            if cls not in ("Material", "MaterialInstanceConstant"):
                continue
            names.append("%s%s" % (str(ad.asset_name),
                                   "" if cls == "Material" else "*"))
        names.sort()
        log("%-42s %d 个" % (root.split("/")[-1], len(names)))
        for i in range(0, len(names), 6):
            log("    " + "  ".join("%-26s" % n for n in names[i:i + 6]))
        for n in names:
            seen[n.rstrip("*")] = True
    log("全部材质名 %d 个：%s" % (len(seen), ", ".join(sorted(seen))))


main()
