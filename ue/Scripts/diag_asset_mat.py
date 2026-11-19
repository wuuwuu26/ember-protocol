"""找 GeometryCache 资产/轨道上可写的材质属性。"""
import unreal

EAL = unreal.EditorAssetLibrary
gc = EAL.load_asset("/Game/RobotGame/Art/Fluids/flip_channel_full")
print("[a] asset attrs with 'mat':", [x for x in dir(gc) if "mat" in x.lower() or "Mat" in x])
tracks = gc.get_editor_property("tracks")
t = tracks[0]
print("[a] track class:", t.get_class().get_name())
print("[a] track attrs with 'mat':", [x for x in dir(t) if "mat" in x.lower() or "Mat" in x])
# 试常见属性名
for prop in ("materials", "default_materials", "material_slots"):
    for obj, lbl in ((gc, "asset"), (t, "track")):
        try:
            v = obj.get_editor_property(prop)
            print("[a] %s.%s = %s" % (lbl, prop, v))
        except Exception:
            pass
# AbcMaterialSettings 字段
try:
    ms = unreal.AbcMaterialSettings()
    print("[a] AbcMaterialSettings attrs:", [x for x in dir(ms) if not x.startswith("_")])
except Exception as e:
    print("[a] AbcMaterialSettings 失败:", e)
print("ASSET_MAT_PROBE_OK")
