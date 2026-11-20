> 语言: **简体中文** | [English](./README_en.md)
# 余火协议 · UE5 工程骨架

从「有资产」到「有游戏」之间缺的那一环。这是**可编译的 C++ 骨架**，不是完整游戏 ——
它把制作计划第 2、3 节里的架构决策落成了代码。

---

## 目录

```
ue/
├─ RobotGame.uproject          引擎 5.8，启用 GAS / EnhancedInput / StateTree / Mutable
├─ Config/
│  ├─ DefaultGameplayTags.ini  全部 GameplayTag 登记表
│  └─ DefaultEngine.ini        渲染 / 物理 / 打包配置
└─ Source/
   ├─ RobotGame.Target.cs
   ├─ RobotGameEditor.Target.cs
   ├─ RobotCore/               基础类型、数据资产（不依赖任何其他游戏模块）
   ├─ RobotCombat/             GAS、伤害路由、部位系统
   └─ RobotGame/               角色、装配、输入
```

## 三个模块的依赖方向

```
RobotCore  ← 不依赖任何游戏模块
   ↑
RobotCombat  →  RobotCore
   ↑
RobotGame    →  RobotCore + RobotCombat
```

**硬规则：依赖只能单向。** 将来加 `RobotUI` 时，它不允许 `#include` `RobotCombat`
的头文件 —— UI 通过接口或事件拿数据。这条规则能防止后期 UI 与玩法互相纠缠到无法重构。

---

## 核心类

| 类 | 模块 | 职责 |
|---|---|---|
| `URobotChassisData` | Core | 机体配置：三条约束 + 插槽定义。**所有可调数值的唯一来源** |
| `URobotModuleData` | Core | 模块配置：对三条约束的影响、解锁成本、赋予的技能 |
| `FPartHealth` / `FPartBoneRule` | Core | 部位血量与骨骼映射规则的数据结构 |
| `RobotTags` | Core | GameplayTag 取值的唯一入口，杜绝硬编码字符串 |
| `UPartMapData` | Combat | 骨骼名 → 部位标签的映射表 |
| `UPartDamageComponent` | Combat | **游戏最核心的战斗机制**：部位 HP、拆解、瘫痪判定 |
| `URobotAttributeSet` | Combat | 电力 / 热量属性。热量是「只涨不降」的反向资源 |
| `UAssemblyComponent` | Game | 机体装配：约束汇总 + 供电硬校验 + 写入 GAS |
| `ARobotCharacter` | Game | 玩家机体，整合 ASC / 部位 / 装配 |

---

## 三个值得单独说的设计决策

### 1. 部位 HP 不进 GAS AttributeSet

部位数量是动态的（不同敌人部位数不同），而 AttributeSet 适合固定属性。
`UPartDamageComponent` 用独立组件管理 `TMap<FGameplayTag, FPartHealth>`，
GAS 只负责通过 GameplayEffect 把伤害投递进来。

**收益**：同一套组件服务玩家与全部 6 种敌人，配不同的 `UPartMapData` 即可。

### 2. 「假拆解」而不是 Chaos 逐块碎裂

`HandlePartDestruction()` 的做法是 `HideBoneByName` 隐藏骨骼，
再由游戏层根据 `OnPartDestroyed` 事件生成预制备件模型。

**为什么**：Chaos 逐部件碎裂在几十个敌人同屏时性能不可控，且碎块无法稳定
作为可拾取物。Chaos 只留给巨像关卡的脚本化表演。

### 3. 供电是硬约束，质量是软约束

`CanMount()` 对供电做**硬校验**（超载直接拒绝装配，并给出面向玩家的原因），
质量则通过 `Speed = BaseWalkSpeed / Mass` 自然惩罚。

**为什么不对称**：供电超载会让技能系统进入未定义状态（消耗超过上限），必须拦住；
质量过高只是变慢，玩家自己会权衡。两条约束用两种手段，比一律硬拦或一律软提示都合理。

---

## 数据校验已经写进代码

`URobotChassisData::IsDataValid()` 和 `URobotModuleData::IsDataValid()` 会在
编辑器的资产校验里检查：

- 机体三条约束是否齐全、插槽名是否为空/重复
- **模块是否"只加数值"** —— 按设计支柱 P1，既不给技能、不给移动能力、
  也不改散热/供电的模块会被标记为警告

最后一条是把设计原则写成了代码。人会在赶进度时忘记原则，编译器不会。

---

## 编译前需要做的事

这个骨架**尚未编译验证**（本机未装 UE 与 Visual Studio）。要跑起来需要：

1. 安装 **UE 5.8** + **Visual Studio 2022**（含「使用 C++ 的游戏开发」工作负载）
2. 右键 `RobotGame.uproject` → **Generate Visual Studio project files**
3. 编译。首次编译会有一些需要修的地方，重点检查：
   - `IsDataValid()` 的签名（UE 5.4 前后从 `TArray<FText>&` 改成了 `FDataValidationContext&`）
   - `GetSkeletalMeshAsset()` 在 5.1 之后才替代 `SkeletalMesh`
   - `SetReplicationMode` 在单机项目里的必要性
4. 创建 `Content/RobotGame/` 目录结构（见制作计划 2.1），
   把 `assets/out/*.fbx` 导入到 `Content/RobotGame/Art/Characters/`

### 导入资产时必须验证的两件事

- **朝向**：机体是否 +X 朝前
- **尺寸**：机体高度是否 2.4—2.6 米（FBX `global_scale=100` 的换算未经实机验证）

若不符，改 `tools/blender/robotlib.py` 里 `export_fbx()` 的
`global_scale` / `axis_forward`，或在 UE 导入设置里调 Uniform Scale。

---

## 下一步

| 优先级 | 任务 | 说明 |
|---|---|---|
| 1 | **编译通过** | 骨架必须先能编过，才谈得上继续 |
| 2 | 导入 3 台机体 + 验证朝向与尺寸 | 打通资产管线 |
| 3 | 实现 `GA_Dash`（冲刺技能） | 第一个 GAS 技能，验证电力消耗链路 |
| 4 | 实现过热锁定 | 热量杠杆的完整闭环 |
| 5 | 改装界面（Common UI + MVVM） | 承载支柱 P1，必须最早做 |
| 6 | 敌人 AI（StateTree） | 复用 `UPartDamageComponent` |
| 7 | 存档系统 | 检查点式，从第一天就带版本号 |
