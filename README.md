# Ember Protocol

> [简体中文](./README_CN.md) · **English**

> A UE5.8 mech arena game driven by an **AI-powered automated asset pipeline** — from concept art to finely detailed 3D models, the entire process is scripted and reproducible.

[![UE 5.8](https://img.shields.io/badge/Unreal_Engine-5.8-0x313131?style=flat-square&logo=unrealengine&logoColor=white)](https://www.unrealengine.com/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Blender](https://img.shields.io/badge/Blender-5.3-E87D1F?style=flat-square&logo=blender&logoColor=white)](https://www.blender.org/)
[![Hunyuan3D](https://img.shields.io/badge/Hunyuan3D-2.x-6C5CE7?style=flat-square)](https://github.com/Tencent/Hunyuan3D-2)
[![License: source code MIT](https://img.shields.io/badge/license-source%20MIT-lightgrey?style=flat-square)](./LICENSE) · [![Third-party notices](https://img.shields.io/badge/assets-third--party%20notices-orange?style=flat-square)](./THIRD_PARTY_NOTICES.md)

---

## 🔥 Highlight: AI-Powered Asset Pipeline

The core engineering practice of this project is a pipeline that **automates game art production**. It answers one question: *without an art team, how can one person quickly produce a batch of stylistically consistent, fully textured, high-quality 3D assets?*

The answer is to chain three AI / procedural capabilities into a reproducible pipeline:

```mermaid
flowchart LR
    A[Text idea / concept] --> B[① Image model<br/>comfyui-image-studio · ComfyUI]
    B -->|concept / reference| C[② AI-assisted Blender modeling<br/>procedural scripts]
    C -->|base mesh / white model| D[③ Hunyuan3D<br/>image-to-3D]
    D -->|white GLB| E[Hunyuan3D texgen<br/>multi-view diffusion PBR]
    E -->|textured GLB| F[Blender render showcase]
    F --> G[Import to UE5.8 · place · verify]
```

### ① Image Models for Textures / Concept Art
Image generation runs through **[comfyui-image-studio](https://github.com/wuuwuu26/comfyui-image-studio)** — a local-first web UI for ComfyUI (Krea 2 / Z-Image / MOSS, tuned for 8 GB GPUs). This project calls it via `tools/easyai.py` (`http://127.0.0.1:7860/api/generate`) to batch-generate concept art and texture materials from text prompts. The 4 mech-wreck concept images (`gen_<name>.png`), posters and seamless textures all came from this step.
- Calling wrapper: `tools/easyai.py` → [comfyui-image-studio](https://github.com/wuuwuu26/comfyui-image-studio)
- Scripts: `tools/gen_posters.py`, `tools/gen_posters2.py`, `tools/gen_textures.py`, `tools/comfy_gen_asset.py`, `tools/comfy_gen_batch.py`, `tools/comfy_gen_mechwreck.py`, `tools/generate_flux.py`
- Texture generation: `tools/gen_coolant_tex.py`, `tools/gen_plasma_tex.py`, `tools/make_*_texture.py`

### ② AI-Assisted Blender Modeling
**Parametric scripts** instead of hand-modeling: change one number to get a new mech variant, with naming, sockets, units, UVs and LODs kept automatically consistent. 51 assets were produced this way — player chassis, 22 modules, 6 enemies, props and environment pieces.
- Library & build scripts: `tools/blender/robotlib.py`, `build_chassis.py`, `build_modules.py`, `build_enemies.py`, `build_props.py`, `build_all.py` (full rebuild ~90 s)
- This solves asset *quantity and consistency*; the *quality ceiling* is handled by the next AI stage.

### ③ Hunyuan3D for Fine 3D Models
Tencent **Hunyuan3D** converts concept art into 3D, then its **texgen** (multi-view diffusion) bakes full-angle PBR textures — overcoming the old "projected textures only work from the front" limitation.
- Image-to-3D + batch: `tools/hy3d_batch.py`, `tools/hy3d_texture_batch.py`
- texgen batch: `tools/texgen_batch2.py`, `tools/fix_texgen_black.py`
- Showcase rendering: `tools/blender/show_asset.py`
- One-command end-to-end pipeline: `tools/mechwreck_pipeline.py`
- **Every asset gets a Blender-rendered textured showcase image** (see `docs/gen3d_shots/`)

> 📖 **Full workflow, pitfalls and measured data: [docs/AI自动化资产工作流.md](./docs/AI自动化资产工作流.md)** (Chinese)

**Textured showcase examples** (`docs/gen3d_shots/`, AI gen → Hunyuan3D → texgen → Blender render):

| Wrecked Mech Torso | Severed Mech Arm | Abandoned Mech Head | Armor Debris |
|:---:|:---:|:---:|:---:|
| ![show_mech_torso_wreck_fixed](./docs/gen3d_shots/show_mech_torso_wreck_fixed.png) | ![show_severed_mech_arm_fixed](./docs/gen3d_shots/show_severed_mech_arm_fixed.png) | ![show_mech_head_wreck_fixed](./docs/gen3d_shots/show_mech_head_wreck_fixed.png) | ![show_armor_debris_fixed](./docs/gen3d_shots/show_armor_debris_fixed.png) |

---

## 🎮 The Game

The game lives in `ue/` (a UE 5.8 C++ project) and is a complete playable loop:

- **Launch**: double-click `ue/启动游戏.bat`
- **Goal**: clear all 5 enemy mechs in the arena (remaining count at top-right)
- **Result**: wipe all → "Mission Complete" (time / salvage / kills), Enter to redeploy

### Controls

| Action | Keyboard / Mouse | Gamepad |
|---|---|---|
| Move | WASD | Left stick |
| Look | Mouse | Right stick |
| Fire | Left mouse | RT |
| Dash | Space | LT / A |
| Workshop | M | Y / Start |
| Switch mech | 1 / 2 / 3 | D-pad ←→ / RB |
| Confirm / Back | Enter / Esc | A / B |

### Core Mechanics

- **Part damage**: shoot off limbs for more salvage (but enemies last longer), or hit the core for a quick kill
- **Heat constraint**: sustained fire overheats and locks for 2 s — forcing you to plan your output rhythm
- **3 mechs + 22 modules**: 9 slots with live constraints, loadouts change your playstyle

### Core-Loop Prototype

`prototype/core_loop_prototype.html` is an experimental prototype you can open directly in a browser — a 10-minute test of whether the "part damage + heat constraint + three-mech tradeoff" loop is fun, before installing a 100 GB engine.

---

## 📁 Repository Structure

```
robot_game/
├─ README.md                      This file (English, homepage)
├─ README_CN.md                   Chinese version
├─ LICENSE                        MIT License
├─ docs/
│  ├─ AI自动化资产工作流.md        ★ Full AI pipeline record (Chinese)
│  ├─ 余火协议_UE5制作计划.md      Full production plan (Chinese)
│  ├─ 余火协议_UE5制作计划.html    Visual version
│  ├─ 迭代报告_2026-10-31_第六十至一百一十九轮.md   Iteration log (Chinese)
│  ├─ gen3d_shots/                 ★ AI→Hunyuan3D textured showcase images
│  ├─ lighting_shots/ / fluid_shots/ / ui_shots/ ...  scene verification
│  └─ ...
├─ prototype/
│  └─ core_loop_prototype.html    Browser core-loop prototype
├─ tools/
│  ├─ blender/                    Blender procedural modeling (51 assets)
│  ├─ mechwreck_pipeline.py        ★ One-command AI pipeline
│  ├─ hy3d_batch.py / hy3d_texture_batch.py            Hunyuan3D batch
│  ├─ texgen_batch2.py / fix_texgen_black.py           PBR texture gen/fix
│  ├─ easyai.py                       caller for comfyui-image-studio (image gen)
│  ├─ comfy_gen_*.py / generate_flux.py                image generation
│  └─ ...
├─ assets/
│  ├─ 资产清单.md                  Full 51-asset list (Chinese)
│  └─ out/                         Generated .fbx / .blend / .glb / previews
├─ art_src/                        Raw art sources
└─ ue/                             Full UE 5.8 project
   ├─ Content/                     Maps / meshes / materials / textures
   ├─ Source/                      C++ gameplay (GAS / part damage / AI / UI)
   ├─ Config/                      Project config
   └─ 启动游戏.bat                 One-click launch
```

---

## 🛠️ Tech Stack

| Area | Tech |
|---|---|
| Engine | Unreal Engine 5.8 (C++ / GAS / ISM fluid replacing Niagara) |
| 3D generation | Hunyuan3D (image-to-3D + texgen multi-view diffusion PBR) |
| Image generation | [comfyui-image-studio](https://github.com/wuuwuu26/comfyui-image-studio) (ComfyUI web UI: Krea 2 / Z-Image / MOSS) |
| Modeling | Blender 5.3 (Python procedural), trimesh |
| Scripting | Python 3.12 (numpy / cv2 / trimesh / PIL) |
| Textures | texgen native PBR (1024), procedural texture generation |

---

## Documentation / 文档索引

Every Chinese document has a complete English counterpart. Each file links to the other language in its header. All written documents (design docs, iteration reports, asset lists, UE guides and the browser prototype) are bilingual.

每份中文文档都有完整英文版，各文件顶部均有语言互链。所有书面文档（设计文档、迭代报告、资产清单、UE 指南、浏览器原型）均为双语。

| 中文 / Chinese | English |
|---|---|
| [制作计划](./docs/余火协议_UE5制作计划.md) | [Production Plan](./docs/production_plan.md) |
| [制作计划（可视化）](./docs/余火协议_UE5制作计划.html) | [Production Plan (visual)](./docs/production_plan.html) |
| [AI自动化资产工作流](./docs/AI自动化资产工作流.md) | [AI Asset Pipeline](./docs/ai_asset_pipeline.md) |
| [资产清单](./assets/资产清单.md) | [Asset List](./assets/asset_list.md) |
| [迭代报告 10-19](./docs/迭代报告_2026-10-19.md) | [Iteration Report 10-19](./docs/iteration_report_2026-10-19.md) |
| [迭代报告 10-23](./docs/迭代报告_2026-10-23.md) | [Iteration Report 10-23](./docs/iteration_report_2026-10-23.md) |
| [迭代报告 10-23b 高级建模](./docs/迭代报告_2026-10-23b_高级建模.md) | [Iteration Report 10-23b](./docs/iteration_report_2026-10-23b.md) |
| [迭代报告 10-23c 缺陷修复](./docs/迭代报告_2026-10-23c_缺陷修复.md) | [Iteration Report 10-23c](./docs/iteration_report_2026-10-23c.md) |
| [迭代报告 10-23d 更换4K](./docs/迭代报告_2026-10-23d_纹理4K.md) | [Iteration Report 10-23d](./docs/iteration_report_2026-10-23d.md) |
| [迭代报告 10-23e 全局换4K](./docs/迭代报告_2026-10-23e_全场景4K.md) | [Iteration Report 10-23e](./docs/iteration_report_2026-10-23e.md) |
| [迭代报告 10-23f UV修复](./docs/迭代报告_2026-10-23f_UV修复.md) | [Iteration Report 10-23f](./docs/iteration_report_2026-10-23f.md) |
| [迭代报告 10-25](./docs/迭代报告_2026-10-25.md) | [Iteration Report 10-25](./docs/iteration_report_2026-10-25.md) |
| [迭代报告 60-119](./docs/迭代报告_2026-10-31_第六十至一百一十九轮.md) | [Iteration Report 60-119](./docs/iteration_report_60-119.md) |
| [Quixel 领取清单](./docs/Quixel_领取清单.md) | [Quixel Claim List](./docs/quixel_claim_list.md) |
| [UE 工程说明](./ue/README.md) | [UE Project README](./ue/README_en.md) |
| [环境搭建](./ue/环境搭建.md) | [Environment Setup](./ue/environment_setup.md) |
| [编译与运行](./ue/编译与运行.md) | [Build and Run](./ue/build_and_run.md) |
| [开发进度报告](./ue/开发进度报告.md) | [Development Progress Report](./ue/development_progress_report.md) |
| [首次导入步骤](./ue/首次导入步骤.md) | [First Import Steps](./ue/first_import_steps.md) |
| [Blender 管线说明](./tools/blender/README.md) | [Blender Pipeline](./tools/blender/README_en.md) |
| [核心循环原型](./prototype/core_loop_prototype.html) | [Core Loop Prototype](./prototype/core_loop_prototype_en.html) |

---

## 📌 Notes

This is a personal learning and prototype project demonstrating an AI automated asset workflow in indie game development. The UE content (`.uasset`) are binary assets requiring UE 5.8 to open; a browser prototype is provided in `prototype/` as an alternative experience.

### Licensing

The [MIT License](./LICENSE) covers only the original source code and works authored by this project. Third-party assets are governed by their own terms — see [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md) for a per-category breakdown (CC0 textures, Hunyuan3D outputs with use restrictions, Unreal Engine EULA, etc.). Commercial third-party models whose redistribution is not permitted (e.g. Cosmos/Leartes) have been removed from this repository.
