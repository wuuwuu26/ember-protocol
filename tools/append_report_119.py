# -*- coding: utf-8 -*-
"""把第 118–119 轮追加到迭代报告，并把文件名更新为"…一百一十九轮"。"""
import os
import glob

DOCS = r"C:\Users\25227\Documents\robot_game\docs"
f = glob.glob(os.path.join(DOCS, "迭代报告_2026-10-31_*.md"))[0]

APPEND = r"""

---

# 第一百一十八轮（2026-11-12）：机甲碎骸资产批次（4 个）

## 一、目标
用"生成概念图 → Hunyuan3D 转 3D → 投影贴图 → UE"的既有流水线，
再补一批"被击毁机甲碎骸"资产，丰富扩建区域（X 2400–5400, Y±900）的叙事。
主题：破损机甲躯干 / 断裂机械臂 / 废弃头盔 / 装甲碎片堆。

## 二、产出
- 4 张概念图：`C:\AI\Hunyuan3D\input\gen_<name>.png`（ComfyUI z_image_turbo）。
  `mech_head_wreck` 首次生成像人类骷髅，重生成一次改为机甲头盔。
- 4 个白模 + 投影贴图版 GLB：`output\*.glb` / `output\*_tex.glb`。
- 4 张带贴图展示图：`docs\gen3d_shots\show_<name>.png`。
- `severed_mech_arm` 有 2 块 1.99×1.99 的"背景大板"（单图重建伪影），
  用 `tools\blender\clean_bg_planes.py` 按 Z 分层删掉 50.9 万面（77MB→26.5MB）。

## 三、关键教训（为第 119 轮埋的坑）
Hunyuan3D 单图模型**没有 UV**，投影贴图只在正面有效、背面回退白色 →
用户提出"可以用 texgen 生成贴图，效果更好"，转入第 119 轮。

---

# 第一百一十九轮（2026-11-13）：texgen 原生 PBR 贴图攻坚 + 碎骸落地

## 一、目标
把第 118 轮的 4 个碎骸改用 Hunyuan3D 官方 texgen（多视图扩散 PBR 贴图），
替代投影贴图，得到全角度贴图；导入 UE、摆放、截图验收。

## 二、texgen 从"挂死"到"跑通"的排错链（本轮核心）
**结论先行：texgen 在 8GB 显存的 RTX 4070 Laptop 上能跑，1024 分辨率 OK。**
用户坚持"1024 之前能跑过"，据此逐层排错：

1. **DLL 加载** ✓ Python 3.12 下 `custom_rasterizer_kernel.pyd` 必须在 import 前
   `os.add_dll_directory(torch/lib)` + `CUDA\v12.4\bin`（补 PATH 无效）。
2. **分辨率** ✓ 关键：`pipe.render.set_default_render_resolution(1024)` /
   `texture_resolution(1024)` / `config.render_size=texture_size=1024`。
   第一版 `texgen_asset.py` 漏了这几行，用默认 2048 → 显存爆、挂死一整天。
   （已跑通的 `run_texgen.py` 里就有这几行。）
3. **参考图 alpha** ✓ texgen 的 `recenter_image`/`delight_model` 依赖 alpha 判断主体。
   ComfyUI 出的 `gen_*.png` 是 RGB 浅灰背景；用
   `tools\gen_alpha_for_texgen.py` 抠成 RGBA（透明占比 0.70~0.90，与基准
   `herta_rgba.png` 的 0.717 一致）。
4. **挂死误判** ✗→✓ 用 `texgen_staged.py` 把 `__call__` 拆成分阶段计时，
   发现"GPU 0% + CPU 满跑"不是死锁，而是 **UV 展开在高面数白模上极慢**：
   `delight 64s / uv_wrap 330s / render 1s / diffusion 237s / bake 1s / inpaint 15s`。
   之前判"挂死"太早。
5. **减面** ✓ 白模减到 5 万面后 **uv_wrap 330s→1.3s**（100 倍），
   单资产总耗时降到约 5.7 分钟。跑前停 ComfyUI 腾显存（diffusion 峰值 9.9GB，
   靠 `expandable_segments` 硬扛，ComfyUI 常驻会挤掉余量导致 inpaint/导出失败）。
6. **RGBA + 1024 + 减面 + 停 ComfyUI 全部对齐后 texgen 稳定跑通 4/4。**

## 三、"点云"噩梦与根因（本轮最大的坑）
减面后 4 个资产全渲染成"点云/碎片"。逐层量化定位：
- 原始白模渲染**完全正常**（实心机甲躯干）。
- `trimesh` 顶点唯一率 99.95%（已焊接），排除"未焊点"。
- 两种减面器（trimesh quadric / Blender Decimate）都毁 → 排除减面算法。
- **决定性证据**：连通分量 `mech_torso_wreck.glb` = 2 块，
  但过一遍 Blender `clean_bg_planes.py` 后的 `_nobg.glb` = **557984 块**；
  面积 12.99→1.29（塌缩 90%）。
  → **Blender 导入/导出 GLB 会按法线/UV 拆分顶点**，把 56 万面拆成 56 万个
  独立三角形，之后任何减面都变成各自塌缩的"点云"。

**修复：全程用 trimesh，不做 Blender 往返，保持顶点焊接。**
`tools\texgen_batch2.py`：
- 读原始白模（welded）→ 按连通块删"极扁(flatness<0.02)且面积占比>15%"
  的背景大板/底座盘 → `simplify_quadric_decimation` 减到 5 万面
  （面积保持 100.5~100.8%，脚本内置 30% 塌缩保护）→ texgen → 展示图。
- 单实例锁 `texgen_batch2.lock`：8GB 显存绝不能并行两个 texgen
  （本轮因重复启动抢显存，清理了 4 次）。
- `mech_torso_wreck`/`severed_mech_arm` 各删掉背景大板/底座盘，
  `mech_head_wreck`/`armor_debris` 无杂散面。
- 结果 `output\*_texgen_final.glb`（4 个，2.1~2.5MB）+ 展示图，
  4 张全是完整实体 + 全角度 PBR 贴图（白装甲、青绿面罩/能量件、焦边做旧）。

## 四、texgen 贴图"黑洞"修复
UE 里躯干出现突兀黑斑。提取 basecolor 发现 **25~36% 纯黑**——多视图扩散
在 6 视角都看不到的自遮挡面没烘焙到，inpaint 没补全（Blender 固定灯光
恰好没照到，展示图看不出来）。
`tools\fix_texgen_black.py`：把"极暗(<48)且低饱和"判为未烘焙空洞，
`cv2.inpaint`（Telea, 半径 7）从邻域扩散填充，保留青绿件/金色磨损/
深蓝装甲/深灰内构等有意深色。**纯黑占比 36%→0%**。
产出 `output\*_texgen_fixed.glb` + 4 张 `show_*_fixed.png` 展示图。

## 五、UE 落地与验收
- 备份关卡 → `$env:TEMP\opencode\ue_backup_texgen_import\`。
- `ue\Scripts\import_mechwreck.py`：优先级
  `*_texgen_fixed.glb` > `*_texgen_final.glb` > `*_tex.glb`；
  4 个导入到 `/Game/RobotGame/Art/Props/Gen3D/<name>/SM_<name>`，
  bbox 88~199cm，各带 1 个贴图材质槽。
- `ue\Scripts\place_mechwreck.py`：4 个碎骸摆在新区域
  （躯干 4400,620 / 断臂 4050,700 / 头盔 3200,-760 / 碎片 4900,-760），
  tag `MechWreck`，缩放后高 110~300cm，关卡已保存。
- 新增调试相机 `WreckCam`(mode 24, 碎骸近景) / `WreckTop`(mode 25, 俯视全景)，
  `RobotCharacter.cpp` 重编译通过。
- 截图验收：`-WreckCam` / `-WreckTop` 确认 UE 里贴图正确、无大面积黑斑、
  深色部分是胸腔/关节等本就深色的结构；确认导入的 UE 贴图 dump 出来
  纯黑 0%（即修复版生效）。俯视全景 4 个碎骸分布两侧、场景更丰富。

## 六、本轮新增/修改文件
| 文件 | 作用 |
|---|---|
| `C:\AI\Hunyuan3D\texgen_asset.py` | texgen 修正版（DLL+1024 分辨率） |
| `C:\AI\Hunyuan3D\texgen_staged.py` | 分阶段计时 texgen（定位瓶颈用，批量实际调用它） |
| `C:\AI\Hunyuan3D\simplify_for_texgen.py` | trimesh 减面（诊断用） |
| `tools\gen_alpha_for_texgen.py` | 概念图抠 RGBA |
| `tools\texgen_batch2.py` | **本轮正式流水线**（trimesh 清背景+减面+texgen+展示图，带单实例锁） |
| `tools\fix_texgen_black.py` | cv2.inpaint 修复 basecolor 黑洞 |
| `tools\diag_decimate.py` / `diag_parts.py` / `dump_tex.py` | 点云根因/贴图诊断 |
| `tools\blender\decimate_blender.py` | Blender Decimate 验证（排除用，未采用） |
| `ue\Scripts\import_mechwreck.py` | 优先 `_texgen_fixed.glb` 导入 |
| `ue\Scripts\place_mechwreck.py` | 碎骸摆放（tag MechWreck） |
| `ue\Scripts\diag_wreck_mat.py` / `diag_wreck_texture.py` | UE 材质/贴图诊断 |
| `ue\Source\RobotGame\Private\RobotCharacter.cpp` | +WreckCam/WreckTop 相机 |
| `docs\gen3d_shots\show_*_texgen.png` / `show_*_fixed.png` | 展示图 |

## 七、仍需注意
- texgen 单资产约 6~8 分钟、diffusion 显存峰值 ~9.9GB（8GB 卡靠分段硬扛），
  跑前必须停 ComfyUI、串行、单实例。
- `expandable_segments` 在 Windows 上不被支持（仅警告），不影响结果。
- texgen 的黑洞是自遮挡面的固有缺陷，`fix_texgen_black.py` 是后处理兜底；
  若换更简单的构图/更多视角可进一步减少。
"""

with open(f, "a", encoding="utf-8") as fp:
    fp.write(APPEND)

new_name = f.replace("一百一十七轮", "一百一十九轮")
if new_name != f and not os.path.exists(new_name):
    os.rename(f, new_name)
print("APPENDED", os.path.basename(new_name))
