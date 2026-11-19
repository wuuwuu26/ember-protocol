# -*- coding: utf-8 -*-
"""把"水柱纹理修复"追加到迭代报告（第一百一十九轮续）。"""
import os
import glob

DOCS = r"C:\Users\25227\Documents\robot_game\docs"
f = glob.glob(os.path.join(DOCS, "迭代报告_2026-10-31_*.md"))[0]

APPEND = r"""

---

## 第一百一十九轮·续（2026-11-13）：水柱竖直纹理修复（SM5 材质编译失败）

### 一、现象
用户截图反馈：水渠注水口那根**竖直水柱**是纯灰褐色、平涂、无纹理，
与上方金属波纹管、亮蓝渠水完全脱节（像一根水泥棍）。

### 二、根因（日志确证，非猜测）
`ue\Saved\Logs\RobotGame.log` 从 11/10 到 11/13 一直重复：
```
M_WaterJet_Coolant.uasset: Failed to compile Material for platform PCD3D_SM5,
Default Material will be used in game.
  (Node TextureSampleParameter2D) Sampler type is Linear Grayscale,
  should be Grayscale for T_Toxic_Bub
```
- 项目 RHI 是 **D3D12 但 Feature Level SM5**（`rhifeaturelevel="SM5"`）。
- 水柱材质 `M_WaterJet_Coolant` / `M_WaterJet_Toxic` 里的
  `TextureSampleParameter2D` 采样节点 sampler_type = `LinearGrayscale`，
  但贴图 `T_Toxic_Bub` 是普通 `Grayscale`(sRGB) → **采样器类型不匹配，
  SM5 下整个材质编译失败 → 引擎回退默认灰材质** → 水柱变纯灰平涂。
  与半透明、显存、法线都无关。
- 关卡里 `Jet_CoolantSpill_0` 确实挂的是 `M_WaterJet_Coolant`（诊断脚本确认）。

### 三、修复（两阶段）
**阶段 1 — 让材质能编译**：
`ue\Scripts\fix_waterjet_mat.py`（新建）。不删材质资产（保住关卡引用），
清空表达式，用**普通 `TextureSample`** 且显式设与贴图匹配的
`SAMPLERTYPE_GRAYSCALE` 重建为"深青 + 流动气泡条纹 + 半透明"水柱，
recompile + save；把关卡里 5 个 `Jet_*` 水柱显式 `set_material` 重挂。
重跑编辑器后 `M_WaterJet_*` 的 SM5 失败日志**消失**，水柱从灰平涂变半透明深青。

**阶段 2 — 让纹理可见**：
dump 出 `T_Toxic_Bub` 发现它是**黑底稀疏白点**（R 均值 2.5 / p90=0，
99% 纯黑）——本来就只适合做泡沫点缀，当水柱条纹几乎看不见。
`tools\make_jet_flow_tex.py` 生成专用 `T_Jet_Flow.png`（横向波纹亮暗条带
+ 碎气泡高光，可 tile；R 均值 152 / std 47 / p10~p90=90~209），
经 `T_Jet_Flow`（TC_GRAYSCALE / sRGB关 / Wrap）导入 UE；
材质改用 `SAMPLERTYPE_LINEAR_GRAYSCALE` 与之匹配（同样能在 SM5 编译）。
UV 沿 V 向下滚动（Panner speed_y=-3.0）→ 读作"往下流的水柱"；
emissive 用 Power(0.7) 提亮中间调强化亮带，opacity=0.42+0.50×条纹。
最终水柱呈**发亮的青色流动水柱**，与波纹管高光、渠水协调。

### 四、验收
- `-DropletClose` 近景截图：水柱有明暗流动条纹 + 气泡高光，半透明透出
  背后水面，深青与渠水同色；不再是纯灰平涂。
- `shot_JetFinal.log`：`M_WaterJet_*` 无 SM5 编译失败（干净通过）。
- 关卡已保存；备份 `$env:TEMP\opencode\ue_backup_jetfix\`。

### 五、备注（未动）
本次聚焦用户所指水柱。日志里仍有 6 条别的材质 SM5 编译失败，属同类历史问题、
与水柱无关：`M_Basin_Concrete`(LinearColor/Color 不匹配)、`M_Toxic_Bed`、
`M_Coolant_Fluid`(各 2 个 LinearGrayscale 节点)、PolyHaven 三个墙面
(ComponentMask 缺输入)。如后续这些表面也出现"默认灰"，按同一手法修
sampler_type 或补齐输入即可。

### 六、本轮新增/修改文件
| 文件 | 作用 |
|---|---|
| `ue\Scripts\fix_waterjet_mat.py` | 重建 2 个水柱材质 + 重挂 5 个 Jet_*（幂等） |
| `tools\make_jet_flow_tex.py` | 生成水柱流动条纹贴图 T_Jet_Flow.png |
| `tools\asset_src\T_Jet_Flow.png` | 条纹贴图源（导入为 UE 资产 T_Jet_Flow） |
| `ue\Scripts\diag_jet_state.py` | 诊断水柱 actor 材质 + 材质编译状态 |
| `ue\Scripts\dump_bub.py` | dump T_Toxic_Bub 确认其 99% 纯黑 |
| `ue\Content\...\Materials\M_WaterJet_Coolant/Toxic.uasset` | 重建后的水柱材质 |
| `ue\Content\...\Materials\T_Jet_Flow.uasset` | 新导入的流动条纹贴图 |
"""

with open(f, "a", encoding="utf-8") as fp:
    fp.write(APPEND)
print("APPENDED", os.path.basename(f))
