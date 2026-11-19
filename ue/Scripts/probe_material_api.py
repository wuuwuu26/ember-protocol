import unreal
unreal.log("[材质API] Material 属性含 sky: %s" % [p for p in dir(unreal.Material) if "sky" in p.lower()])
unreal.log("[材质API] MaterialInterface 属性含 sky: %s" % [p for p in dir(unreal.MaterialInterface) if "sky" in p.lower()])
unreal.log("[材质API] Component 属性含 sky: %s" % [p for p in dir(unreal.StaticMeshComponent) if "sky" in p.lower() or "background" in p.lower()])
unreal.log("[材质API] 完成")