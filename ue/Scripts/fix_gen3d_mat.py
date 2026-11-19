# -*- coding: utf-8 -*-
"""给 Gen3D 资产套项目工业材质（第一百一十轮）。

Hunyuan3D 输出只有几何、没有 UV/贴图，导入后是灰色默认材质。
这里把材质槽替换成项目已有的工业材质（M_Steel 为主，按用途区分），
让它和场景里 Cosmos / 环境件风格统一。

⚠️ 用 StaticMesh.set_material(index, mat) 逐个设置 ——
   StaticMaterial 的构造参数在不同版本不一致，用 set_material 最稳。
"""
import unreal

BASE = "/Game/RobotGame/Art/Props/Gen3D"
ENV = "/Game/RobotGame/Art/Environment"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\gen3d_mat.txt"

EAL = unreal.EditorAssetLibrary
lines = []


def log(s):
    unreal.log("[Gen3DMat] %s" % s)
    lines.append(str(s))


# 资产 -> 材质名（按语义选）
MAT_MAP = {
    "airlock": ["M_Steel", "M_Accent_wall", "M_Joint"],
    "pipe_junction": ["M_Steel", "M_Copper", "M_Joint"],
    "crane_arm": ["M_Steel", "M_Accent_prop", "M_Joint"],
    "bunker_vent": ["M_Steel", "M_SteelLight", "M_Joint"],
    "mech_core": ["M_Steel", "M_Core_prop", "M_Copper"],
    "generator": ["M_Steel", "M_Copper", "M_Accent_prop"],
}

for p in sorted(EAL.list_assets(BASE, recursive=True)):
    name = p.split("/")[-1]
    if not name.startswith("SM_"):
        continue
    key = name[3:]
    m = EAL.load_asset(p)
    if not m:
        continue
    # 已带投影贴图的资产**不能**覆盖材质（否则贴图被 M_Steel 顶掉）
    slots = m.get_editor_property("static_materials")
    has_tex = False
    for sm in slots:
        mi = sm.get_editor_property("material_interface")
        if mi and "Projected" in mi.get_name():
            has_tex = True
    if has_tex:
        log("%-16s 已有投影材质，跳过" % key)
        continue
    mats = MAT_MAP.get(key, ["M_Steel"])
    try:
        slots = m.get_editor_property("static_materials")
        n = max(1, len(slots))
        done = 0
        for i in range(n):
            mname = mats[i % len(mats)]
            mat = EAL.load_asset("%s/%s" % (ENV, mname))
            if mat:
                m.set_material(i, mat)
                done += 1
        EAL.save_asset(p, only_if_is_dirty=False)
        log("%-16s 槽位 %d 个 -> 设置 %d 个 (%s)" % (key, n, done, mats))
    except Exception as e:
        log("%-16s !! %s: %s" % (key, type(e).__name__, str(e)[:90]))

with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("GEN3D_MAT_DONE")
