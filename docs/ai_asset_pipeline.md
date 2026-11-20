> Language: **English** | [简体中文](./AI自动化资产工作流.md)
# AI Automated Asset Workflow (Ember Protocol)

> This document records the fully automated pipeline in the "Ember Protocol" project, **from a text idea to a refined 3D asset with complete PBR textures**.
> This is the project's core engineering practice: without an art team, use AI + procedural scripts to industrialize and make the asset production pipeline reproducible.

---

## 0. Why This Pipeline Is Needed

In indie 3D game development, the biggest bottleneck is often not code, but **assets**: a 3D model with a consistent style, complete textures, ready to drop into the engine, takes hours to days to make by hand from scratch.

This pipeline compresses that process into "edit the prompt / tweak parameters → run the script → get the finished product":

| Traditional manual work | This pipeline |
|---|---|
| Artisan modeling (hours per asset) | Image model produces concept art (~30 sec each) |
| Manual UV + hand-painted textures | Hunyuan3D image-to-3D (~10 min per asset) |
| Multi-view PBR painting | texgen multi-view diffusion auto-baking (~5.7 min per asset) |
| Manual naming / sockets / unit alignment | Fully automated by procedural scripts |

**Hardware prerequisite**: RTX 4070 Laptop with 8GB VRAM — the entire pipeline runs on a consumer-grade GPU, which is its greatest practical value.

---

## 1. Pipeline Overview

```
Text idea
   |
   v
+-----------------------------+
| (1) Image model (comfyui-image-studio) |  ComfyUI · Krea 2 / Z-Image / MOSS
|    Concept image gen_<name>.png          |  ~30 sec each, 1024²
+-----------------------------+
   |  (alpha cutout: gen_alpha_for_texgen.py)
   v
+-----------------------------+
| (2) AI-assisted Blender modeling       |  Procedural scripts (robotlib.py etc.)
|    Base mesh / white model              |  Or hand ①'s concept image straight to Hunyuan3D
+-----------------------------+
   |
   v
+-----------------------------+
| (3) Hunyuan3D image-to-3D              |  hy3d_asset.py, white-model GLB
+-----------------------------+
   |  (trimesh cleanup + decimate to 50k faces, texgen_batch2.py)
   v
+-----------------------------+
| (4) Hunyuan3D texgen PBR textures      |  Multi-view diffusion, 1024, all angles
+-----------------------------+
   |  (black-hole repair: fix_texgen_black.py)
   v
+-----------------------------+
| (5) Blender renders showcase image      |  show_asset.py -> docs/gen3d_shots/
+-----------------------------+
   |
   v
Import into UE5.8 -> place -> screenshot validation
```

The one-click entry script that chains the whole flow: `tools/mechwreck_pipeline.py` (one run produces a batch of assets).

---

## 2. Stage ① Image Model Generates Concept Art / Textures

### Tools
This project has two image-generation paths, both driven by **ComfyUI**:

1. **[comfyui-image-studio](https://github.com/wuuwuu26/comfyui-image-studio)** (main workhorse)
   - A local-first Chinese ComfyUI web UI, optimized for 8GB VRAM, with built-in Krea 2 / Z-Image / MOSS engines.
   - This project uses `tools/easyai.py` to call its `http://127.0.0.1:7860/api/generate` endpoint; `generate(prompt, out, engine, ratio, ...)` produces an image in one step.
   - Posters (`gen_posters*.py`), seamless textures (`gen_textures.py`) and most concept art use this path. **The code and license of the image toolchain itself are in the [comfyui-image-studio repository](https://github.com/wuuwuu26/comfyui-image-studio)**; this repository only contains the calling scripts, not its source.
2. **Direct ComfyUI connection** (`http://127.0.0.1:8188`): `tools/comfy_gen_*.py` / `generate_flux.py`, used for image-to-image and Flux generation for the mech-wreck batches.

### Related Scripts
| Script | Purpose |
|---|---|
| `tools/easyai.py` | [comfyui-image-studio](https://github.com/wuuwuu26/comfyui-image-studio) calling wrapper (main) |
| `tools/gen_posters.py` / `gen_posters2.py` | Posters (MOSS / Krea engine) |
| `tools/gen_textures.py` | Seamless textures (Krea engine) |
| `tools/comfy_gen_asset.py` | Single-asset concept art generation (direct ComfyUI) |
| `tools/comfy_gen_batch.py` | Batch generation (direct ComfyUI) |
| `tools/comfy_gen_mechwreck.py` | Mech-wreck batch (representative case of this pipeline) |
| `tools/generate_flux.py` | Flux model image generation |
| `tools/gen_coolant_tex.py` / `gen_plasma_tex.py` | Procedural texture assets |

### Case: Four Concept Images of Mech Wreckage
The theme is "destroyed mechs scattered in the new area": broken mech torso / severed mechanical arm / abandoned helmet / pile of armor debris.
Each `gen_<name>.png` takes about 30 seconds. `mech_head_wreck` came out looking like a human skull on the first try, and was regenerated as a mech helmet — demonstrating the role of "prompt iteration" in the pipeline.

> ⚠️ `gen_*.png` from both image paths are RGB with a light-gray background and no alpha. texgen's `recenter_image` / `delight_model` rely on alpha to identify the subject, so a cutout step is needed (see Stage ④).

---

## 3. Stage ② AI-Assisted Blender Modeling

### Tools
Blender 5.3 + Python scripts (procedural modeling, not manual).

### Core Scripts (`tools/blender/`)
| Script | Output |
|---|---|
| `robotlib.py` | Shared modeling library (prisms, armor, joints, UV, naming) |
| `build_chassis.py` | Player mechs ×3 (with skeleton / UV / LOD) |
| `build_modules.py` | Modules ×22 |
| `build_enemies.py` | Enemies ×6 |
| `build_props.py` | Props ×10 + environment ×9 + landmarks |
| `build_all.py` | Full rebuild (~90 seconds) |

This pipeline solves "asset quantity and consistency": change one number to produce a new chassis variant, and naming, sockets, units and UV are all automatically consistent. 51 assets were produced in total; see `assets/资产清单.md`.

> Procedural modeling guarantees "quantity" and "standards", while the **ceiling of visual quality** is taken over by the AI model in the next stage. For assets like wreckage with "organic damage, hard to parameterize", the concept image from Stage ① goes straight to Hunyuan3D image-to-3D.

---

## 4. Stage ③ Hunyuan3D Image-to-3D

### Tools
Tencent **Hunyuan3D** (`C:\AI\Hunyuan3D`, the `hunyuan3d-dit-v2-mini` image-to-3D model).

### Related Scripts
| Step | Script |
|---|---|
| Image-to-3D (with cutout) | `C:\AI\Hunyuan3D\hy3d_asset.py` |
| Batch processing | `tools/hy3d_batch.py` |
| Projection texture batch (early approach) | `tools/hy3d_texture_batch.py` |
| Background plane cleanup | `tools/blender/clean_bg_planes.py` |

Produces a white-model GLB. The early wreck batches used "projection textures", which only worked from the front and fell back to white on the back — that's exactly what drove the texgen approach.

**Pitfall**: Hunyuan3D single-image reconstruction produces a "background plane" artifact (`severed_mech_arm` had 2 planes of 1.99×1.99). `clean_bg_planes.py` deleted 509,000 faces by Z-layer (77MB → 26.5MB).

---

## 5. Stage ④ Hunyuan3D texgen PBR Textures (The Technical Core of This Pipeline)

This is the most engineering-heavy and pitfall-ridden link in the whole pipeline. Conclusion up front: **texgen runs stably on an RTX 4070 Laptop with 8GB VRAM, 1024 resolution is fine, about 5.7 minutes per asset.**

### Debugging Chain from "Hanging" to "Working"

1. **DLL loading** — under Python 3.12, `custom_rasterizer_kernel.pyd` requires `os.add_dll_directory(torch/lib)` and `CUDA\v12.4\bin` before importing torch; just patching PATH doesn't work.
2. **Resolution** — three key lines, none can be missing:
   ```python
   pipe.render.set_default_render_resolution(1024)
   pipe.render.set_default_texture_resolution(1024)
   config.render_size = config.texture_size = 1024
   ```
   The first version omitted these and used the default 2048 → VRAM blew up, hung for a whole day.
3. **Reference image alpha** — ComfyUI's RGB light-gray background needs to be cut out to RGBA (transparency ratio 0.70~0.90). Script `tools/gen_alpha_for_texgen.py`.
4. **"Hanging" was a misdiagnosis** — staged timing showed "GPU 0% + CPU maxed" wasn't a deadlock but UV unwrapping being extremely slow on the high-poly white model: `delight 64s / uv_wrap 330s / render 1s / diffusion 237s / bake 1s / inpaint 15s`.
5. **Decimation** — after reducing the white model to 50k faces, **uv_wrap 330s → 1.3s** (100×). Must stop ComfyUI before running to free VRAM (diffusion peak 9.9GB).
6. **Once all aligned, texgen ran stably 4/4.**

### The "Point Cloud" Nightmare and Its Root Cause (The Biggest Pitfall)

After decimation all 4 assets rendered as "point clouds/fragments". Layer-by-layer quantitative isolation:

- The original white model rendered perfectly → rule out the model itself
- trimesh vertex uniqueness 99.95% → rule out "unwelded vertices"
- Both decimators (trimesh quadric / Blender Decimate) broke it → rule out the decimation algorithm
- **Decisive evidence**: connected components went from 2 → after one pass through Blender `clean_bg_planes.py` it became **557984 components**, area collapsed 90%
- **Root cause**: Blender GLB import/export splits vertices by normal/UV, splitting 560k faces into 560k independent triangles, after which any decimation collapses each into a "point cloud"

**Fix**: use trimesh throughout, no Blender round-trip, keeping vertices welded. The flow of `tools/texgen_batch2.py`:

1. Read the original white model (welded)
2. Delete "very flat (flatness<0.02) and area share>15%" background planes/base discs by connected component
3. `simplify_quadric_decimation` down to 50k faces (area retained 100.5~100.8%, built-in 30% collapse protection)
4. texgen generates PBR textures (1024)
5. `show_asset.py` renders the showcase image

Single-instance lock `texgen_batch2.lock`: 8GB VRAM must never run two texgen jobs in parallel.

### texgen Texture "Black Hole" Repair

Black patches appeared on the torso in UE. Extracting the basecolor showed **25~36% pure black** — the multi-view diffusion didn't bake self-occluded faces invisible from all 6 views, and inpaint didn't fill them. `tools/fix_texgen_black.py`: treats "very dark (<48) and low saturation" as unbaked holes, fills them by spreading from neighbors with `cv2.inpaint` (Telea, radius 7), while preserving intentional dark colors (teal parts / gold wear / deep blue armor / dark gray internals). **Pure black ratio 36% → 0%.**

---

## 6. Stage ⑤ Showcase Images + UE Landing

### Showcase Images
After each asset is generated, `tools/blender/show_asset.py` renders a **textured showcase image** saved to `docs/gen3d_shots/show_<name>_fixed.png`. This is the pipeline's "QC outlet" — one glance shows whether textures are complete and whether there are black holes / point clouds.

### UE Import and Placement
- `ue/Scripts/import_mechwreck.py`: material priority `*_texgen_fixed.glb` > `*_texgen_final.glb` > `*_tex.glb`
- Import path: `/Game/RobotGame/Art/Props/Gen3D/<name>/SM_<name>`
- `ue/Scripts/fix_wreck_overlap.py`: uses bounding-box collision checks to re-place into empty spots without clipping
- Screenshot validation: `tools/shot_run.ps1` with the C++ debug cameras (`WreckCam` / `WreckTop` / `CosmosView`, etc.)

---

## 7. Showcase Image Gallery

All in `docs/gen3d_shots/`:

| Asset | White model | texgen version | texgen fixed version (final) |
|---|---|---|---|
| Broken mech torso | `show_mech_torso_wreck.png` | `show_mech_torso_wreck_texgen.png` | `show_mech_torso_wreck_fixed.png` |
| Severed mechanical arm | `show_severed_mech_arm.png` | `show_severed_mech_arm_texgen.png` | `show_severed_mech_arm_fixed.png` |
| Abandoned mech helmet | `show_mech_head_wreck.png` | `show_mech_head_wreck_texgen.png` | `show_mech_head_wreck_fixed.png` |
| Pile of armor debris | `show_armor_debris.png` | `show_armor_debris_texgen.png` | `show_armor_debris_fixed.png` |

This "three versions of the same asset" comparison directly records the evolution from white model to texgen PBR finished product to black-hole repair.

---

## 8. Quick Reference of Measured Data

| Metric | Value |
|---|---|
| Image generation (z_image_turbo, 1024²) | ~30 sec each |
| Hunyuan3D image-to-3D | ~10 min per asset |
| texgen PBR textures (1024, 50k faces) | ~5.7 min per asset |
| White-model decimation uv_wrap time | 330s → 1.3s (100×) |
| texgen VRAM peak | 9.9GB (8GB card barely copes via expandable_segments) |
| Pure black ratio after black-hole repair | 36% → 0% |
| Procedural modeling full rebuild | ~90 sec |

---

## 9. Reproduction Notes

1. **Single instance**: both texgen and ComfyUI must be single-instance; parallel on 8GB VRAM will definitely crash.
2. **Stop ComfyUI**: stop ComfyUI before running texgen, otherwise the diffusion peak squeezes out the margin and inpaint / export fails.
3. **No Blender round-trip**: handle GLB entirely with trimesh; once passed through Blender import/export, vertices split and the "point cloud" disaster returns.
4. **1024 resolution**: all five texgen resolution settings must be aligned, otherwise the default 2048 blows VRAM.
5. **RGBA reference images**: alpha determines subject identification, must first cut out with `gen_alpha_for_texgen.py`.

> This pipeline was polished over rounds 118–119; the full pitfall log is in `docs/迭代报告_2026-10-31_第六十至一百一十九轮.md` (rounds 118 and 119 chapters).
