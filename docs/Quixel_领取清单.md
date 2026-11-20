> 语言: **简体中文** | [English](./quixel_claim_list.md)
# Quixel Megascans 领取清单（第一百零五轮 / 2026-11-09）

目标：用 Fab 上的免费 Quixel Megascans 资产，继续深化「余火协议」的
科幻工业竞技场（当前新区域是程序化灰蓝钢板 + Cosmos 工业道具）。

## 一、为什么必须你先领取

| | Cosmos（上轮，已跑通） | Fab / Megascans（本轮） |
| --- | --- | --- |
| 获取 | 公开 CDN 预览 glTF，我直接下载 | Epic 账号登录 → 领取 → Launcher 下载 |
| 匿名直链 | 有 | **没有**，匿名接口只给元数据（标题/封面/价格） |
| 我能自动落地 | 能 | **不能**，需你先把文件下载到本地 |

本机现状：装了 Epic Games Launcher 且已登录（日志有 `LoggedIn` /
`Verify access token succeeded`），但 `VaultCache\FabLibrary\listings_v1.db`
与下载缓存 **全为 0 行** —— 没有任何已领取/已下载的 Megascans 资产。

## 二、关于「免费」的重要提醒

- **2026-11-05** Quixel 官网公告：`Update: Megascans are going free again` ——
  **整个 Megascans 库在 Fab 重新免费**，并给 2025 年后购买者退款。
- 但今天匿名搜索接口里这些资产 `isFree` 仍全是 `false`、显示 `$4.99`。
  这是**匿名缓存滞后 / 分批生效**（才过 4 天）。

👉 **以你登录后的 Fab 界面为准**：登录后应显示为「免费 / 已拥有 / 领取」。
若个别仍要付费，就先领明确免费的 `... Megascans Sample` 整包和
Fab 的 `Free` 筛选项，其余等分批生效。别按匿名页面的 $4.99 付费。

也建议先翻一下 **My Library**，历史领取过的 Megascans 会保留在里面。

## 三、领取清单（名字都是 Fab 上真实可搜到的）

Fab 一个系列有几十个变体，逐个点太累 —— 按「搜索关键词」整批领最快。
优先级：**P0 先领**（少而精、见效大），P1/P2 有余力再补。

### P0 — 最契合，优先领

| 在 Fab 搜这个 | 代表资产 | 类型 | 用在场景哪里 |
| --- | --- | --- | --- |
| `Industrial Abandoned Factory` | Wall Set Concrete Modular（模块化混凝土墙） | 3D | 替换/丰富新区域两侧围墙，做工业墙体 |
| 同上 | Door Double Metal（双开金属门）、Vent Air Metal Rusted（锈通风口）、Panel Console Modular（控制台面板）、Cable Wall Modular（墙面电缆） | 3D | 门洞、墙面细节、贴墙装置 |
| 同上 | Ground Patch Gravel / Scatter Debris Plaster / Rubble Pile Plaster（碎石地/散落碎片/瓦砾堆） | 3D | 地面散落、掩体周边，破掉「干净地板」感 |
| 同上 | Debris Pipe Metal / Ceiling Concrete Rebar（金属管碎片/钢筋天花） | 3D | 管道与顶部层次 |
| `Derelict Corridor Megascans Sample` | Derelict Corridor Megascans Sample | 整包 | 直接强化「通道 → 新区域」那一段（现成成套） |
| `Industrial Concrete Floor` | Industrial Concrete Floor | 材质 | 地面从纯色程序材质换成写实混凝土 |
| `Weathered Concrete Wall` | Weathered / Damaged / Stained Concrete Wall | 材质 | 墙面写实化 |

### P1 — 掩体与工业道具（补强现有 Cosmos 布局）

| 在 Fab 搜这个 | 代表资产 | 类型 | 用途 |
| --- | --- | --- | --- |
| `Rusty Metal Barrel` | Rusty Metal Barrel / Shelf / Workbench（锈桶/锈架/工作台） | 3D | 成组掩体 |
| `Tarped Crate` | Tarped Crate（盖篷布箱） | 3D | 掩体 |
| `Corrugated Metal Sheet` | Corrugated Metal Sheet（波纹铁皮） | 3D | 临时挡板/掩体 |
| `Painted Pipe` / `Concrete Pipe` | Painted Pipe Straight / Connector / Base / Y / T / Cross | 3D | 管道组，呼应现有 `cs1-pipe` |
| `Concrete Rubble Pile` | Concrete Rubble Pile / Cement Rubble / Construction Rubble | 3D | 瓦砾掩体 |
| `Sandbag` | Military Trenches Barrier Sandbag Canvas | 3D | 呼应现有沙袋堆 |
| `Rusty Metal Sheet` | Rusty / Rusty Painted / Rusty Green Metal Sheet | 材质 | 锈铁表面 |

### P2 — 材质与氛围（有余力再补）

| 在 Fab 搜 | 类型 | 用途 |
| --- | --- | --- |
| `Ground Gravel` / `Gravel Ground` / `Asphalt Road` | 材质 | 碎石/沥青地面 |
| `Damaged Concrete` | Decal | 地面破损贴花 |
| `Urban Trash` / `Bricks Rubble` | 3D | 环境杂散 |
| `Dark Ruins` / `Military Trench` Megascans Sample | 整包 | 废土/战壕氛围参考或复用 |

> 类型建议：优先 **3D Model** 和 **Material**（我们场景用 StaticMesh + PBR 材质），
> Decal / Brush 次之。

## 四、领取与放置步骤

1. **Fab 网页**：右上角登录 Epic 账号 → 进 `Quixel Megascans` 卖家页
   → 按上表关键词搜 → 逐个点「领取 / Add to Library」（现在应免费）。
   或直接用 **Epic Games Launcher → Fab** 标签页搜、领取、下载。
2. **下载 / 导出**：在 Launcher 的 **Fab Library** 里下载所需资产；
   若有「导出到项目 / 导出为文件」，导出为 **FBX + 贴图** 或 UE 原生包均可。
3. **放到这个目录**（保持子目录结构，别改名合并）：
   ```
   C:\Users\25227\Documents\robot_game\art_src\megascans\
   ```
4. **告诉我一声**，我接手：扫描实际格式 → 缩贴图 → 批量导入 UE →
   按现有布局逻辑摆进新区域（复用上轮 Cosmos 那套幂等流水线）。

## 五、我这边已就绪的东西

- UE 5.8 自带 `MegascansPlugin`（无需另装）
- 上轮跑通的离线流水线：`tools/cosmos_build.py`（缩图 + 打包）、
  `ue/Scripts/import_cosmos_assets.py`（批量导入）、
  `ue/Scripts/place_cosmos_props.py`（幂等摆放）—— 换资产源后可直接改造复用
- 新区域骨架 + 31 个 Cosmos 道具已在关卡里，Megascans 是「叠加深化」，
  不会推翻已有成果

探查脚本留档：`tools/probe_fab_api*.py`、`probe_fab_quixel.py`、
`probe_fab_free.py`、`probe_fab_cache.py`；真实资产元数据在
`docs/fab_quixel_assets.json`（163 条 Quixel 资产）。
