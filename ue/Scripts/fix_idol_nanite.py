# -*- coding: utf-8 -*-
"""关掉 IdolMech 雕像的 Nanite（第一百零四轮）。

用户决定：不动项目渲染设置（DefaultEngine.ini 约定），
直接把 2 个开 Nanite 的雕像资产关掉，消除 SM6 警告。

⚠️ Nanite 网格在 SM5 下可能显示异常/回退；关掉后按普通静态网格渲染。
   9 米摆件、39.8 万面，关掉 Nanite 后用普通 LOD 渲染，单件开销可接受。
"""
import unreal

ASSETS = [
    "/Game/RobotGame/Art/Props/IdolMech/SM_IdolMech",
    "/Game/RobotGame/Art/Props/IdolMech_poisson/StaticMeshes/SM_IdolMech_Poisson",
]
REPORT = r"C:\Users\25227\Documents\robot_game\docs\idol_nanite_off.txt"
EAL = unreal.EditorAssetLibrary
out = []

for p in ASSETS:
    m = EAL.load_asset(p)
    if not m:
        out.append("!! 加载失败 %s" % p)
        continue
    try:
        ns = m.get_editor_property("nanite_settings")
        before = ns.get_editor_property("enabled")
        ns.set_editor_property("enabled", False)
        m.set_editor_property("nanite_settings", ns)
        after = m.get_editor_property("nanite_settings").get_editor_property("enabled")
        EAL.save_asset(p, only_if_is_dirty=False)
        out.append("%s : %s -> %s  (saved)" % (p.split("/")[-1], before, after))
    except Exception as e:
        out.append("!! %s : %s" % (p, e))

with open(REPORT, "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
for l in out:
    unreal.log("[IdolNanite] %s" % l)
unreal.log("IDOL_NANITE_OFF_DONE")
