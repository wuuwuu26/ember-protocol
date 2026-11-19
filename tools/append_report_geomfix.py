# -*- coding: utf-8 -*-
"""把"穿模/悬空修复"追加到迭代报告（第一百一十九轮·续 4）。"""
import glob
import os

DOCS = r"C:\Users\25227\Documents\robot_game\docs"
f = glob.glob(os.path.join(DOCS, "迭代报告_2026-10-31_*.md"))[0]

APPEND = r"""

---

## 第一百一十九轮·续 4（2026-11-13）：全场景穿模 / 悬空修复

### 一、现象
用户反馈"很多地方有穿模问题，还有些模型悬空"。全场景几何排查，
不靠肉眼逐个猜，先用包围盒数据定位 + 多视角截图复核。

### 二、诊断（数据先行）
1. **`diag_geometry.py`**：dump 全部 375 个 StaticMeshActor 的世界包围盒
   与底部 Z（`docs/geom_diag.txt`）。
   - 木箱三层 `zmin=62/125`：核对 `SM_met-wooden-crate01a` 高 21cm、
     缩放 3.0→63cm，三层 Z=0/63/126 **精确对齐**，是设计堆叠，**不是悬空**。
   - 管道 A/B/C `zmin=20`、壁灯/海报/风扇挂墙：均为设计悬挂，非 bug。
   - 4 个 MechWreck 碎骸 `zmin≈-3~+2`：落地公式正确，无悬空。
2. **`diag_overlap.py`**：道具级 bbox 两两相交检测（`docs/overlap_diag.txt`），
   初始 83 件 / **32 对**重叠。分类：
   - 约 18 对是原竞技场 `PROP_*` 工业堆场故意堆叠（俯视 `geom_scenic`
     复核正常），非 bug；
   - `管道 B/C × 管道接头 A/B`：管道本就该接到接头上，是设计连接；
   - **真穿模集中在"最后加入的碎骸"与"Gen3D 填充大件"**：
     - 断臂被 `野战栅栏 A` 横穿、头盔插进 `工业发电机/沙袋 A2`、
       `装甲碎片堆 × 废弃机甲核心`；
     - `管道接头B × 废弃吊臂`、`油桶组B × 管道接头A`、
       `沙袋A2 × 工业发电机` 等 Gen3D 大件互吞。
3. **根因**：
   - `place_mechwreck.py` 的 4 个碎骸坐标 (4400,620)/(4050,700)/
     (3200,-760)/(4900,-760) 是独立定的，**落进了已有 Gen3D 大件、
     Cosmos 掩体/栅栏的 bbox 里**；
   - `place_gen3d.py` 给填充件设了 260/240/320/240/200cm 目标高，
     比周围 50~160cm 的 Cosmos 道具大一圈，包围盒自然互相吞；
   - 两个脚本各自独立定坐标、从未做过互相协调。

### 三、修复（三批，均带 bbox 碰撞校验、位置可回滚）
| 脚本 | 动作 |
|---|---|
| `fix_wreck_overlap.py` | 用 `find_wreck_spots.py` 的空位搜索 + 逐个 bbox 碰撞校验，**重摆 4 个碎骸**：躯干(3900,-760)、断臂(3600,-760)、头盔(4700,680)、碎片堆(4500,680)，落地 Z 用轴心公式重算 |
| `fix_gen3d_overlap.py` | 把"废弃吊臂"缩到 190cm（原 320 巨无霸怎么挪都擦碰）并挪到 (4340,-800)，消除 `管道接头B`/`野战栅栏A`/`壁灯C` 的吊臂穿模 |
| `fix_gen3d_shrink.py` | 把 `管道接头A/B`→165cm、`废弃机甲核心`→165cm、`工业发电机`→140cm **原地缩小**（位置不动→保持叙事且不引入新碰撞），按新 scale 重算落地 Z |

- 重叠对演进：**32 → 28 → 26 → 25 → 23**；"涉及 MechWreck 碎骸的相交"
  段落 **从 4 对变为空**，吊臂相关穿模全清。
- 回归防护：把 `place_mechwreck.py` 的 LAYOUT、`place_gen3d.py` 的目标高
  /吊臂坐标**同步为修复后的值**，避免重跑旧脚本重新引入穿模（原文件里的
  旧坐标加了显著注释说明）。

### 四、验收
- 剩余 23 对：~18 对原竞技场 `PROP_*` 故意堆叠、`管道×管道接头` 设计连接、
  `壁灯C×管道接头B` / `沙袋B1×旧冰柜B` 等贴墙件轻微边缘互蹭 —— 俯视
  `ScenicCam` 复核为正常工业堆场，判定非 bug，不动。
- 多视角截图复核（`-CosmosView` / `-WreckCam` / `-WreckTop`）：
  - 断臂不再被栅栏横穿、头盔贴地摆、碎片堆落地散开，4 碎骸均在空地上、
    彼此分开、底部贴地（`zmin≈0`）；
  - `list_wrecks.py` 确认碎骸类 actor 恰好 4 个、无重复残留；
  - `CosmosView` 里"头盔浮在箱堆顶"是**低角度透视遮挡错觉**（远端
    (4700,680) 头盔被近处箱堆挡住），`WreckTop` 俯视 + `WreckCam` 近景
    均证明其贴地，非真实悬空。
- 关卡已保存 `L_TestArena.umap`；备份 `$env:TEMP\opencode\ue_backup_geomfix\`。

### 五、本轮新增/修改文件
| 文件 | 作用 |
|---|---|
| `ue\Scripts\diag_geometry.py` / `diag_overlap.py` | 375 actor bbox dump / 道具两两相交检测（核心诊断） |
| `ue\Scripts\find_wreck_spots.py` / `diag_mesh_sizes.py` | 空位网格搜索 / mesh 尺寸核对（排除木箱"假悬空"） |
| `ue\Scripts\fix_wreck_overlap.py` | 重摆 4 碎骸到无碰撞空位（核心修复） |
| `ue\Scripts\fix_gen3d_overlap.py` | 吊臂缩小+挪位 |
| `ue\Scripts\fix_gen3d_shrink.py` | 3 类 Gen3D 填充件原地缩小 |
| `ue\Scripts\list_wrecks.py` | 碎骸清点（确认无重复/悬空） |
| `ue\Scripts\place_mechwreck.py` / `place_gen3d.py` | LAYOUT/尺寸同步为修复值（回归防护） |
| `docs\geom_diag.txt` / `overlap_diag.txt` / `wreck_fix.txt` / `crane_fix.txt` / `gen3d_shrink.txt` / `free_spots.txt` / `mesh_sizes.txt` / `wreck_list.txt` | 诊断与修复报告 |

### 六、备注
- 修复刻意**限定范围**：只动"最后加入、确证相撞"的 4 个碎骸 + 制造
  冲突的 Gen3D 填充大件；**没有**大范围重排历史 `PROP_*` / Gen3D /
  Cosmos 布局 —— 绝大多数 bbox 重叠是有意的工业堆叠，盲目挪动会破坏
  既有布局且引入新碰撞。
- Gen3D 填充件改为"原地缩小"而非"重摆"，就是为了避免挪动牵一发动全身。
"""

with open(f, "a", encoding="utf-8") as fp:
    fp.write(APPEND)
print("APPENDED", os.path.basename(f))
