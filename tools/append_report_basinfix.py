# -*- coding: utf-8 -*-
"""把"圆形水池纹理修复"追加到迭代报告（第一百一十九轮·续 3）。"""
import os
import glob

DOCS = r"C:\Users\25227\Documents\robot_game\docs"
f = glob.glob(os.path.join(DOCS, "迭代报告_2026-10-31_*.md"))[0]

APPEND = r"""

---

## 第一百一十九轮·续 3（2026-11-13）：圆形水池纹理修复

### 一、现象
用户反馈圆形毒液池（池心 -200,350）也有纹理问题。`-BasinCam` 截图：
液面**右半边一大片金色/铜色细密波纹反光**，左半边正常墨绿，
中间一条青绿水柱 —— 像贴了错误的暖色贴图/污渍。

### 二、分层定位（A/B + 日志，逐层排除）
1. **诊断水池构成**（`diag_basin_state.py`）：
   - `ToxicBed_0` 池底圆盘 -> `M_Toxic_Bed`
   - `ToxicFluid_0` = `ARobotCoolantField`，`SurfaceMaterial = M_Toxic_Fluid`
     （运行时 `BeginPlay` 里 `Surface->SetMaterial` 用它画液面）
   - `Basin_ToxicFluid_0` 池壁容器（C++ `RobotBasin`）
   - 液面金色与池底/池壁无关（换液面材质即消失）。
2. **SM5 编译失败**（`shot_BasinDiag.log`）：`M_Toxic_Fluid`、
   `M_Coolant_Fluid`、`M_Toxic_Bed`、`M_Basin_Concrete` 全部
   `Failed to compile Material for PCD3D_SM5`：
   ```
   (Node TextureSampleParameter2D) Sampler type is Linear Grayscale,
   should be Grayscale for T_Toxic_Bub
   (Node TextureSampleParameter2D) Sampler type is Linear Color,
   should be Color for T_ConcreteDetail
   ```
   与"水柱"完全同源：材质里 TextureSampleParameter2D 的 sampler_type
   与引用贴图 sRGB 不匹配。
3. **贴图配置**（`diag_tex_cfg.py`）：`T_Toxic_Bub` srgb=True/TC_GRAYSCALE
   → 应 `GRAYSCALE`；`T_Coolant_F` srgb=False/TC_GRAYSCALE
   → 应 `LINEAR_GRAYSCALE`；`T_ConcreteDetail` srgb=True/BC7
   → 应 `COLOR`。材质里全被设成了 Linear 版。
4. **A/B 判定金色来源**（`ab_fluid_mat.py`）：临时把 `ToxicFluid_0`
   的 SurfaceMaterial 换成 `M_Coolant_Fluid` → **金色斑驳完全消失**。
   证明金色不是场景反射/PPV/池底，而是 `M_Toxic_Fluid` 材质自身。
5. **材质 trace**（`dump_fluid_mats.py` / `trace_toxic.py`）：
   `M_Toxic_Fluid` 无任何暖色常量（全是墨绿/灰蓝冷色），但含
   `Fresnel` + `ReflectionVectorWS` 强镜面反射链路，roughness 由 lerp
   动态降低 → 在 Lumen/暖色灯下把环境反射拉满成金色铜斑。
   `M_Coolant_Fluid` 反射权重低，故无此问题。

### 三、修复
**A. 批量修 sampler（保留原材质设计）** `fix_fluid_samplers.py`：
遍历 4 个材质所有 TextureSample(Parameter)2D，按引用贴图的
srgb/compression 自动重设 sampler_type，recompile+save：
- `M_Toxic_Fluid` 4 个 / `M_Coolant_Fluid` 2 个 / `M_Toxic_Bed` 2 个
  `T_Toxic_Bub` -> `SAMPLERTYPE_GRAYSCALE`
- `M_Basin_Concrete` `T_ConcreteDetail` -> `SAMPLERTYPE_COLOR`
重跑后这 4 个材质的 SM5 编译失败全部消失（只剩 3 个 PolyHaven 墙面
ComponentMask 缺输入，与水池无关）。

**B. 液面换用干净材质** `finalize_toxic.py`：
sampler 修好后金色仍在（反射设计问题）。曾尝试自建精简材质
`M_Toxic_Fluid_Fixed`（无 Fresnel/Reflection），但它自身踩了
`(Node Multiply) float2 and float3 are undefined` 的 SM5 编译错误
→ 回退默认灰棋盘格，已删除该试验资产。
最终把 `ToxicFluid_0.SurfaceMaterial` 指向**已 A/B 验证无金色**的
`M_Coolant_Fluid`（墨绿液面 + 蓝色泡沫带 + 落点白沫），关卡保存。

### 四、验收
`-BasinCam` 最终截图：金色斑驳彻底消失，圆形池为干净墨绿液面 +
蓝色泡沫带 + 落点白沫，池壁为水泥/金属质感；SM5 编译只剩 3 个
PolyHaven 墙面历史问题。关卡已保存；
备份 `$env:TEMP\opencode\ue_backup_basinfix\`。

### 五、本轮新增/修改文件
| 文件 | 作用 |
|---|---|
| `ue\Scripts\fix_fluid_samplers.py` | 批量按贴图修 sampler_type（4 个材质，核心修复） |
| `ue\Scripts\finalize_toxic.py` | 液面 SurfaceMaterial -> M_Coolant_Fluid + 删试验材质 |
| `ue\Scripts\diag_basin_state.py` / `diag_fluid_mat.py` / `diag_tex_cfg.py` | 水池构成/SurfaceMaterial/贴图配置诊断 |
| `ue\Scripts\dump_fluid_mats.py` / `dump_mat_links.py` / `trace_toxic.py` | 材质表达式/反射链路 trace |
| `ue\Scripts\dump_fluid_tex.py` / `dump_bub.py` | 贴图 dump（确认无暖色贴图） |
| `ue\Scripts\ab_fluid_mat.py` | A/B 换材质判定金色来源 |
| `ue\Content\...\Materials\M_Toxic_Fluid/Coolant_Fluid/Toxic_Bed/Basin_Concrete.uasset` | sampler 修正后的材质 |

### 六、备注
- 圆形池液面现用 `M_Coolant_Fluid`，与冷却液水渠同款材质（墨绿/蓝带），
  失去原"毒液绿"区分；若之后要恢复专属毒液色且避免金色，需重建一个
  不含 Fresnel/低粗糙度镜面、且能在 SM5 编译的精简材质（本次自建版
  因 float2×float3 Multiply 报错未成功）。
- 池壁 `M_Basin_Concrete` 修好 sampler 后露出了 `T_ConcreteDetail` 的
  黑白水泥斑驳纹理（原先编译失败回退是纯白），属正常纹理、噪点偏重可接受。
"""

with open(f, "a", encoding="utf-8") as fp:
    fp.write(APPEND)
print("APPENDED", os.path.basename(f))
