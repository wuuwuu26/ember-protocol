# -*- coding: utf-8 -*-
"""诊断地面材质"纹理没加载"（第一百一十一轮）。

重点查：
  1) M_concrete_floor_02 的节点图是否完整（上一轮插入的 Multiply 是否破坏了连接）
  2) 贴图资产本身是否有数据（尺寸/是否有效）
  3) Roughness 链路是否还通
  4) 地面 actor 的 override_materials 是否还指向这个材质
  5) 是否有 BaseColor 断掉
"""
import unreal

PH = "/Game/RobotGame/Art/Materials/PolyHaven"
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
out = []

mat = EAL.load_asset(PH + "/M_concrete_floor_02")
if not mat:
    out.append("!! 材质 M_concrete_floor_02 加载失败")
else:
    out.append("=== 材质 %s ===" % mat.get_name())

    # 1. 节点全清单
    exprs = MEL.get_material_expressions(mat)
    out.append("节点 %d 个：" % len(exprs))
    for e in exprs:
        cls = e.get_class().get_name()
        extra = ""
        if "TextureSample" in cls:
            t = e.get_editor_property("texture")
            if t:
                # 贴图是否有数据
                try:
                    has = t.is_valid_low_level() if hasattr(t, "is_valid_low_level") else "?"
                except Exception:
                    has = "?"
                extra = " tex=%s  size=%dx%d  srgb=%s" % (
                    t.get_name(),
                    (t.get_editor_property("blueprint_get_size_x") if False else 0),
                    0, "?")
                # 用 platform data 拿尺寸更可靠
                try:
                    sx, sy = t.get_editor_property("compression_settings"), None
                except Exception:
                    pass
            else:
                extra = " tex=None  <<< 缺失！"
        if "ComponentMask" in cls:
            extra = " r=%s g=%s b=%s a=%s" % (
                e.get_editor_property("r"), e.get_editor_property("g"),
                e.get_editor_property("b"), e.get_editor_property("a"))
        if cls == "MaterialExpressionConstant":
            extra = " r=%s" % e.get_editor_property("r")
        out.append("  [%d] %-40s %s" % (exprs.index(e), cls, extra))

    # 2. 各材质属性连接
    out.append("")
    out.append("=== 材质属性连接 ===")
    for pname, prop in [("BaseColor", unreal.MaterialProperty.MP_BASE_COLOR),
                        ("Normal", unreal.MaterialProperty.MP_NORMAL),
                        ("Roughness", unreal.MaterialProperty.MP_ROUGHNESS),
                        ("Metallic", unreal.MaterialProperty.MP_METALLIC),
                        ("AO", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION),
                        ("Emissive", unreal.MaterialProperty.MP_EMISSIVE_COLOR)]:
        try:
            node = MEL.get_material_property_input_node(mat, prop)
            out.append("  %-12s <- %s" % (pname, node.get_class().get_name() if node else "**未连接**"))
        except Exception as ex:
            out.append("  %-12s err %s" % (pname, str(ex)[:50]))

    # 3. 贴图资产细节
    out.append("")
    out.append("=== 贴图资产 ===")
    for tex_name in ("concrete_floor_02_BaseColor", "concrete_floor_02_Normal",
                     "concrete_floor_02_ARM"):
        p = "%s/concrete_floor_02/%s" % (PH, tex_name)
        t = EAL.load_asset(p)
        if not t:
            out.append("  %-32s !! 加载失败" % tex_name)
            continue
        info = []
        for prop in ("srgb", "compression_settings", "lod_group", "never_stream"):
            try:
                info.append("%s=%s" % (prop, t.get_editor_property(prop)))
            except Exception:
                pass
        # 尺寸
        try:
            size = t.get_editor_property("imported_size")
            info.append("imported_size=%s" % size)
        except Exception:
            pass
        out.append("  %-32s %s" % (tex_name, " ".join(str(x)[:40] for x in info)))

# 4. 地面 actor 的材质覆盖
out.append("")
out.append("=== 地面 actor 材质覆盖（EXT 区抽样）===")
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
n = 0
for a in sub.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    c = a.static_mesh_component
    m = c.get_editor_property("static_mesh") if c else None
    if not m or "floor" not in m.get_name().lower():
        continue
    loc = a.get_actor_location()
    if loc.x < 1800:
        continue
    ov = c.get_editor_property("override_materials")
    names = [x.get_name() if x else "None" for x in ov]
    if n < 6:
        out.append("  (%.0f,%.0f) ov=%s" % (loc.x, loc.y, names))
    n += 1
out.append("  EXT 地面共 %d 块" % n)

with open(r"C:\Users\25227\Documents\robot_game\docs\floor_diag.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("FLOOR_DIAG_DONE")
