"""看 GeometryCache 资产的轨道与材质：白色到底挂在资产哪一层。"""
import unreal

EAL = unreal.EditorAssetLibrary
gc = EAL.load_asset("/Game/RobotGame/Art/Fluids/flip_channel_full")
tracks = gc.get_editor_property("tracks")
print("[trk] 轨道数量=%d" % len(tracks))
for i, t in enumerate(tracks):
    print("[trk] track%d class=%s" % (i, t.get_class().get_name()))
    for prop in ("materials", "material_slots", "default_material"):
        try:
            v = t.get_editor_property(prop)
            print("[trk]   %s = %s" % (prop, v))
        except Exception as e:
            pass
print("TRACKS_OK")
