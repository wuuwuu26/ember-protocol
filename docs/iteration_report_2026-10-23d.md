> Language: **English** | [简体中文](./迭代报告_2026-10-23d_纹理4K.md)
# Iteration Report · 2026-10-23 (Fourth Round): Textures Not Loading + Full 4K

Goal for this round: figure out "why textures aren't loading", and upgrade all scene textures to 4K.

---

## I. Diagnosis: The Textures Really Are Broken, and Completely

Probe results:

```
T_MechDetail     32x32     <- used by all mech materials
T_MechDetail_N   32x32
T_EnvDetail      1024x1024
T_EnvDetail_N    1024x1024
```

**The mech's detail texture is a blank 32×32 image.** In other words, all this time the "panel seams on the mech surface"
were actually computed entirely by the procedural material's SeamDarken / WearAmount — the texture itself had no content.

### Why It Stayed Stuck at 32×32

UE's FBX/texture importer **skips rebuilding assets whose "source file hasn't changed"**.
When one import failed, UE left a 32×32 placeholder; after that, no matter how many times `replace_existing=True` ran,
it decided "the source file hasn't changed" and didn't rebuild — the placeholder was permanently frozen in.

**The only solution is to delete the asset first, then import.**

### Why It "Looked Textured" Before

The `DetailTex` parameter in the material was bound to `T_MechDetail` on the MI (the binding itself was fine),
but that image was a uniform 32×32 gray, which samples as one flat gray field —
equivalent to "no texture". All the visual cues of panel seams and rivets came from the material's procedural terms.

---

## II. Generating 4K

The generators `make_detail_texture.py` / `make_env_texture.py` had their `SIZE` changed from 1024 to 4096.

**Key**: every "per-pixel" parameter must be multiplied by `S = SIZE/1024`, otherwise at 4K the seam width is still 16px —
only 4.7mm at the 1.2m UV scale, which disappears at a distance.

| Parameter | 1024 baseline | Actual 4K |
|---|---|---|
| Main panel seam width | 16px | 64px |
| Sub-panel seam width | 10px | 40px |
| Fine scribe lines | 5px | 20px |
| Rivet radius | 5.5px | 22px |
| Scratch length | 30~230px | 120~920px |
| Scratch count | 46 | 92 (area ratio should be 16×, but full-image computation is too slow, so take 2× and lengthen) |

The `fbm` frequency parameters are resolution-independent (computed as "cycles per image"), so they stay unchanged —
4K automatically gets finer noise.

Generation time: mech 3.5 minutes, environment 2.5 minutes (numpy full-image operations).

---

## III. Import Settings (The Other Half of "Not Loading")

`reimport_tex.py` was rewritten to do four things:

| Setting | Value | Why |
|---|---|---|
| Delete first, then import | — | Bypasses the "skip rebuild if source unchanged" pitfall |
| `max_texture_size` | 4096 | Default may compress down to 2048 |
| `never_stream` | True | At 4K texture streaming is used by default, and some quality levels only load low mips — **which looks exactly like "not loading"** |
| `compression_settings` | `TC_GRAYSCALE` (normals still `TC_NORMALMAP`) | Grayscale detail textures get blocky compression with MASKS/DXT |

The four textures use about 80MB of VRAM in total, resident directly.

---

## IV. Two Script Bugs Fixed Along the Way

1. **`make_detail_texture.py` lacked an `if __name__ == "__main__"` guard**
   → `make_env_texture.py` merely `import`ing it triggered the entire mech texture generation,
   wasting 3 minutes before discovering the real error.

2. **The function `tileable_gradient` doesn't exist**
   `make_env_texture.py` imported it from the detail script, but it had long been deleted —
   so the environment texture line was actually broken all along.
   Restored the implementation: use `np.roll` for wrap-around differences, ensuring the tangent is also continuous at the texture border (otherwise normals have a bright seam when tiled).

---

## V. About "Using UE5's Built-In Assets"

I checked the engine's built-in content on this machine; the directly usable 4K textures are very limited:

| Path | Contents | Usable |
|---|---|---|
| `/Engine/EngineSky/T_Sky_Blue` | 15MB sky image | Already used its counterpart (`T_Sky_Stars` for the starfield) |
| `/Engine/EngineSky/T_Sky_Clouds_M` | Cloud mask | Usable, but this project is a night scene, not needed for now |
| `/Engine/StarterContent/Textures/` | **Only 1** `T_ground_Moss_D` | Moss ground, doesn't fit an industrial site |
| `/Engine/EngineMaterials/` | Mostly materials, no general 4K surface textures | No use |

**The engine has no "industrial metal/concrete" surface detail textures** — StarterContent on this machine
has only a single texture installed. So surface textures can only be procedurally generated, which is why the pipeline
had `make_detail_texture.py` written from the start.

Where engine assets genuinely helped was the **sky** (`T_Sky_Stars` wired into `M_SkyDome`, done last round).

---

## VI. Validation

- Textures: all four are `4096x4096`, `never_stream=True` (confirmed in logs)
- Close-up: panel seams and block lines visible on the mech's breastplate/legs, floor tile seams sharp
- Game view: the floor's large grid + sub-panels + rivet dots all visible

---

## VII. Remaining

1. **The mech is still too dark in the game view**. I tried rotating the sun to "shine from the −X side"
   (the player walks toward +X with the camera behind, so this would light the player's back and the enemies' fronts),
   but both azimuths were miscalculated (`yaw=202` has a negative cosine, so the light still pointed −X),
   and the overall brightness changed after the change. **Currently rolled back to the original azimuth**, leaving this for a dedicated next round.
2. **The review mode's exposure window is very narrow**: bias 2.6 is dark, 4.3 overexposes, no comfortable middle —
   meaning the review lights (4 point lights) need recalibration.
3. The environment texture's seam width (the env script's own parameters) hasn't been rechecked at 4K scale yet,
   only the detail script's has been changed.
