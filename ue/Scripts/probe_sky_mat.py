# -*- coding: utf-8 -*-
"""检查天空材质的 IsSky 标记与自发光节点。"""
import unreal

mat = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/M_SkyDome")
unreal.log("[天空材质] mat=%s" % mat.get_name())
props = [p for p in dir(mat) if "sky" in p.lower() or "used" in p.lower()]
unreal.log("[天空材质] 候选属性: %s" % props)
for p in props:
    try:
        unreal.log("[天空材质]   %s = %s" % (p, mat.get_editor_property(p)))
    except Exception as e:
        unreal.log("[天空材质]   %s 读取失败: %s" % (p, str(e)[:80]))

mel = unreal.MaterialEditingLibrary
try:
    root = mel.get_material_property_input_node(mat, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.log("[天空材质] emissive root=%s class=%s" % (root.get_name(), root.get_class().get_name()))
    def walk(n, depth):
        if depth > 7:
            return
        prefix = "  " * depth
        unreal.log("[天空材质] %s%s [%s]" % (prefix, n.get_name(), n.get_class().get_name()))
        for attr in ("constant", "r", "g", "b", "a", "parameter_name"):
            try:
                v = n.get_editor_property(attr)
                if v is not None:
                    unreal.log("[天空材质] %s  %s=%s" % (prefix, attr, v))
            except Exception:
                pass
        for m in dir(n):
            if "input" in m.lower() and callable(getattr(n, m)):
                unreal.log("[天空材质] %s  input-method: %s" % (prefix, m))
        try:
            for inp in n.get_inputs():
                if inp:
                    walk(inp, depth + 1)
        except Exception as e:
            pass
    walk(root, 0)
except Exception as e:
    unreal.log("[天空材质] 读取节点失败: %s" % e)
unreal.log("[天空材质] 完成")