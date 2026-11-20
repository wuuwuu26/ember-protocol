> 语言: **简体中文** | [English](./ai_asset_pipeline.md)
# AI 自动化资产工作流（余火协议）

> 本文记录《余火协议》项目里，**从一段文字创意到一个带完整 PBR 贴图的精细 3D 资产**的全自动化管线。
> 这是本项目最核心的工程实践：在没有美术团队的前提下，用 AI + 程序化脚本把资产生产流水线化、可复现化。

---

## 0. 为什么需要这条管线

独立开发做 3D 游戏，最大的瓶颈往往不是代码，而是**资产**：一个风格统一、带完整贴图、能直接进引擎的 3D 模型，手工_from scratch_要花数小时到数天。

这条管线把这个过程压缩成"改提示词 / 改参数 → 跑脚本 → 拿成品"：

| 传统手工 | 本管线 |
|---|---|
| 美术手搓建模（数小时/个） | 生图模型出概念图（约 30 秒/张） |
| 手工 UV + 手绘贴图 | Hunyuan3D 图生 3D（约 10 分钟/个） |
| 多视图绘制 PBR | texgen 多视图扩散自动烘焙（约 5.7 分钟/个） |
| 人工命名/挂点/单位对齐 | 程序化脚本全自动 |

**硬件前提**：RTX 4070 Laptop 8GB 显存 —— 整条管线都在消费级显卡上跑通，这是它最大的实用价值。

---

## 1. 管线全景

```
文字创意
   │
   ▼
┌─────────────────────────────────────┐
│ ① 生图模型（comfyui-image-studio）  │  ComfyUI · Krea 2 / Z-Image / MOSS
│    概念图 gen_<name>.png             │  ~30 秒/张，1024²
└─────────────────────────────────────┘
   │  （抠 alpha：gen_alpha_for_texgen.py）
   ▼
┌─────────────────────────────────────┐
│ ② AI 辅助 Blender 建模              │  程序化脚本（robotlib.py 等）
│    基础网格 / 白模                    │  或直接用 ① 的概念图交给 Hunyuan3D
└─────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────┐
│ ③ Hunyuan3D 图生 3D                 │  hy3d_asset.py，白模 GLB
└─────────────────────────────────────┘
   │  （trimesh 清理 + 减面到 5 万面，texgen_batch2.py）
   ▼
┌─────────────────────────────────────┐
│ ④ Hunyuan3D texgen PBR 贴图         │  多视图扩散，1024，全角度
└─────────────────────────────────────┘
   │  （黑洞修复：fix_texgen_black.py）
   ▼
┌─────────────────────────────────────┐
│ ⑤ Blender 渲染展示图                │  show_asset.py → docs/gen3d_shots/
└─────────────────────────────────────┘
   │
   ▼
导入 UE5.8 → 摆放 → 截图验收
```

一键串起全流程的入口脚本：`tools/mechwreck_pipeline.py`（跑一次产出一批资产）。

---

## 2. 阶段① 生图模型生成概念图 / 贴图

### 工具
本项目有两条生图路径，都由 **ComfyUI** 驱动：

1. **[comfyui-image-studio](https://github.com/wuuwuu26/comfyui-image-studio)**（主力）
   - 一个本地优先的中文 ComfyUI 网页界面，针对 8GB 显存优化，内置 Krea 2 / Z-Image / MOSS 引擎。
   - 本项目用 `tools/easyai.py` 调用它的 `http://127.0.0.1:7860/api/generate` 接口，`generate(prompt, out, engine, ratio, ...)` 一步出图。
   - 海报（`gen_posters*.py`）、无缝贴图（`gen_textures.py`）、概念图大多走这条路。**生图工具链本身的代码与许可见 [comfyui-image-studio 仓库](https://github.com/wuuwuu26/comfyui-image-studio)**，本仓库只包含调用脚本，不包含其源码。
2. **直连 ComfyUI**（`http://127.0.0.1:8188`）：`tools/comfy_gen_*.py` / `generate_flux.py`，用于机甲碎骸批次的图生图与 Flux 生图。

### 相关脚本
| 脚本 | 用途 |
|---|---|
| `tools/easyai.py` | [comfyui-image-studio](https://github.com/wuuwuu26/comfyui-image-studio) 调用封装（主力） |
| `tools/gen_posters.py` / `gen_posters2.py` | 海报（MOSS / Krea 引擎） |
| `tools/gen_textures.py` | 无缝贴图（Krea 引擎） |
| `tools/comfy_gen_asset.py` | 单资产概念图生成（直连 ComfyUI） |
| `tools/comfy_gen_batch.py` | 批量生成（直连 ComfyUI） |
| `tools/comfy_gen_mechwreck.py` | 机甲碎骸批次（本流水线的代表案例） |
| `tools/generate_flux.py` | Flux 模型生图 |
| `tools/gen_coolant_tex.py` / `gen_plasma_tex.py` | 程序化贴图素材 |

### 案例：机甲碎骸的 4 张概念图
主题是"被击毁的机甲散落在新区域"：破损机甲躯干 / 断裂机械臂 / 废弃头盔 / 装甲碎片堆。
每张 `gen_<name>.png` 生成约 30 秒。其中 `mech_head_wreck` 首次生成像人类骷髅，重新生成一次改为机甲头盔——这体现了"提示词迭代"在管线里的作用。

> ⚠️ 两条生图路径出的 `gen_*.png` 都是 RGB 浅灰背景，没有 alpha。而 texgen 的 `recenter_image` / `delight_model` 依赖 alpha 判断主体，因此需要一个抠图步骤（见阶段④）。

---

## 3. 阶段② AI 辅助 Blender 建模

### 工具
Blender 5.3 + Python 脚本（程序化建模，非手工）。

### 核心脚本（`tools/blender/`）
| 脚本 | 产出 |
|---|---|
| `robotlib.py` | 共享建模库（棱柱、装甲、关节、UV、命名） |
| `build_chassis.py` | 玩家机体 ×3（带骨骼 / UV / LOD） |
| `build_modules.py` | 模块 ×22 |
| `build_enemies.py` | 敌人 ×6 |
| `build_props.py` | 道具 ×10 + 环境 ×9 + 地标 |
| `build_all.py` | 全量重建（约 90 秒） |

这套管线解决的是"资产数量与一致性"：改一个数字就能出新机型，命名、挂点、单位、UV 全部自动一致。共产出 51 个资产，清单见 `assets/资产清单.md`。

> 程序化建模保证的是"量"和"规范"，而**质感上限**由下一阶段的 AI 模型接管。对于碎骸这类"有机破损、难以参数化"的资产，则直接走阶段①的概念图 → Hunyuan3D 图生 3D。

---

## 4. 阶段③ Hunyuan3D 图生 3D

### 工具
腾讯 **Hunyuan3D**（`C:\AI\Hunyuan3D`，`hunyuan3d-dit-v2-mini` 图生 3D 模型）。

### 相关脚本
| 步骤 | 脚本 |
|---|---|
| 图生 3D（含抠图） | `C:\AI\Hunyuan3D\hy3d_asset.py` |
| 批处理 | `tools/hy3d_batch.py` |
| 投影贴图批处理（早期方案） | `tools/hy3d_texture_batch.py` |
| 背景大板清理 | `tools/blender/clean_bg_planes.py` |

产出白模 GLB。早期碎骸批次用"投影贴图"，只有正面有效、背面回退白色——这正是推动 texgen 方案的直接原因。

**踩坑**：Hunyuan3D 单图重建会产生"背景大板"伪影（`severed_mech_arm` 有 2 块 1.99×1.99 的板）。`clean_bg_planes.py` 按 Z 分层删掉 50.9 万面（77MB → 26.5MB）。

---

## 5. 阶段④ Hunyuan3D texgen PBR 贴图（本管线技术核心）

这是整条管线里工程含量最高、踩坑最多的一环。结论先行：**texgen 能在 8GB 显存的 RTX 4070 Laptop 上稳定跑，1024 分辨率 OK，单资产约 5.7 分钟。**

### 从"挂死"到"跑通"的排错链

1. **DLL 加载** — Python 3.12 下 `custom_rasterizer_kernel.pyd` 必须在 import torch 之前 `os.add_dll_directory(torch/lib)` 和 `CUDA\v12.4\bin`；只补 PATH 无效。
2. **分辨率** — 关键三行缺一不可：
   ```python
   pipe.render.set_default_render_resolution(1024)
   pipe.render.set_default_texture_resolution(1024)
   config.render_size = config.texture_size = 1024
   ```
   第一版漏了这几行用默认 2048 → 显存爆、挂死一整天。
3. **参考图 alpha** — ComfyUI 的 RGB 浅灰背景需抠成 RGBA（透明占比 0.70~0.90）。脚本 `tools/gen_alpha_for_texgen.py`。
4. **"挂死"是误判** — 分阶段计时发现"GPU 0% + CPU 满跑"不是死锁，而是 UV 展开在高面数白模上极慢：`delight 64s / uv_wrap 330s / render 1s / diffusion 237s / bake 1s / inpaint 15s`。
5. **减面** — 白模减到 5 万面后 **uv_wrap 330s → 1.3s**（100 倍）。跑前必须停 ComfyUI 腾显存（diffusion 峰值 9.9GB）。
6. **全部对齐后 texgen 稳定跑通 4/4。**

### "点云"噩梦与根因（最大的坑）

减面后 4 个资产全渲染成"点云/碎片"。逐层量化定位：

- 原始白模渲染完全正常 → 排除模型本身
- trimesh 顶点唯一率 99.95% → 排除"未焊点"
- 两种减面器（trimesh quadric / Blender Decimate）都毁 → 排除减面算法
- **决定性证据**：连通分量从 2 块 → 过一遍 Blender `clean_bg_planes.py` 后变成 **557984 块**，面积塌缩 90%
- **根因**：Blender 导入/导出 GLB 会按法线/UV 拆分顶点，把 56 万面拆成 56 万个独立三角形，之后任何减面都各自塌缩成"点云"

**修复**：全程用 trimesh，不做 Blender 往返，保持顶点焊接。`tools/texgen_batch2.py` 的流程：

1. 读原始白模（welded）
2. 按连通块删"极扁(flatness<0.02)且面积占比>15%"的背景大板/底座盘
3. `simplify_quadric_decimation` 减到 5 万面（面积保持 100.5~100.8%，内置 30% 塌缩保护）
4. texgen 生成 PBR 贴图（1024）
5. `show_asset.py` 渲染展示图

单实例锁 `texgen_batch2.lock`：8GB 显存绝不能并行两个 texgen。

### texgen 贴图"黑洞"修复

UE 里躯干出现突兀黑斑。提取 basecolor 发现 **25~36% 纯黑**——多视图扩散在 6 视角都看不到的自遮挡面没烘焙到，inpaint 没补全。`tools/fix_texgen_black.py`：把"极暗(<48)且低饱和"判为未烘焙空洞，用 `cv2.inpaint`（Telea, 半径 7）从邻域扩散填充，保留有意深色（青绿件/金色磨损/深蓝装甲/深灰内构）。**纯黑占比 36% → 0%。**

---

## 6. 阶段⑤ 展示图 + UE 落地

### 展示图
每个资产生成后都用 `tools/blender/show_asset.py` 渲染一张**带贴图的展示图**，存到 `docs/gen3d_shots/show_<name>_fixed.png`。这是管线的"质检出口"——一眼就能看出贴图是否完整、有没有黑洞/点云。

### UE 导入与摆放
- `ue/Scripts/import_mechwreck.py`：材质优先级 `*_texgen_fixed.glb` > `*_texgen_final.glb` > `*_tex.glb`
- 导入路径：`/Game/RobotGame/Art/Props/Gen3D/<name>/SM_<name>`
- `ue/Scripts/fix_wreck_overlap.py`：用包围盒碰撞校验重摆到无穿模空位
- 截图验收：`tools/shot_run.ps1` 配合 C++ 调试相机（`WreckCam` / `WreckTop` / `CosmosView` 等）

---

## 7. 展示图库

全部位于 `docs/gen3d_shots/`：

| 资产 | 白模 | texgen 版 | texgen 修复版（最终） |
|---|---|---|---|
| 破损机甲躯干 | `show_mech_torso_wreck.png` | `show_mech_torso_wreck_texgen.png` | `show_mech_torso_wreck_fixed.png` |
| 断裂机械臂 | `show_severed_mech_arm.png` | `show_severed_mech_arm_texgen.png` | `show_severed_mech_arm_fixed.png` |
| 废弃机甲头盔 | `show_mech_head_wreck.png` | `show_mech_head_wreck_texgen.png` | `show_mech_head_wreck_fixed.png` |
| 装甲碎片堆 | `show_armor_debris.png` | `show_armor_debris_texgen.png` | `show_armor_debris_fixed.png` |

这套"同一资产三个版本"的对照图，直观记录了从白模到 texgen PBR 成品、再到黑洞修复的演进过程。

---

## 8. 实测数据速查

| 指标 | 数值 |
|---|---|
| 生图（z_image_turbo, 1024²） | ~30 秒/张 |
| Hunyuan3D 图生 3D | ~10 分钟/个 |
| texgen PBR 贴图（1024, 5 万面） | ~5.7 分钟/个 |
| 白模减面 uv_wrap 耗时 | 330s → 1.3s（100×） |
| texgen 显存峰值 | 9.9GB（8GB 卡靠 expandable_segments 硬扛） |
| 黑洞修复后纯黑占比 | 36% → 0% |
| 程序化建模全量重建 | ~90 秒 |

---

## 9. 复现注意事项

1. **单实例**：texgen 和 ComfyUI 都要单实例，8GB 显存并行必崩。
2. **停 ComfyUI**：跑 texgen 前停掉 ComfyUI，否则 diffusion 峰值会挤掉余量，导致 inpaint / 导出失败。
3. **不做 Blender 往返**：GLB 处理全程用 trimesh，一旦过 Blender 导入导出就拆顶点，"点云"灾难重现。
4. **1024 分辨率**：五个 texgen 分辨率设置必须全部对齐，否则默认 2048 爆显存。
5. **RGBA 参考图**：alpha 决定主体判断，必须先用 `gen_alpha_for_texgen.py` 抠图。

> 本管线经过 118~119 轮迭代打磨，完整踩坑实录见 `docs/迭代报告_2026-10-31_第六十至一百一十九轮.md`（第 118、119 轮章节）。
