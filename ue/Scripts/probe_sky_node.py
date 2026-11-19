import unreal
root = unreal.MaterialEditingLibrary.get_material_property_input_node(unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/M_SkyDome"), unreal.MaterialProperty.MP_EMISSIVE_COLOR)
unreal.log("[节点探针] root=%s class=%s" % (root.get_name(), root.get_class().get_name()))
unreal.log("[节点探针] 方法: %s" % [m for m in dir(root) if "input" in m.lower() or "expression" in m.lower()])
for attr in ("a", "b", "const_a", "const_b", "constant", "r", "g", "b", "a"):
    try:
        v = root.get_editor_property(attr)
        unreal.log("[节点探针] %s = %s" % (attr, v))
    except Exception as e:
        pass
unreal.log("[节点探针] 完成")