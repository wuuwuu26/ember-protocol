# Blender 程序化建模管线

用 Blender 的 Python API 无头生成机体模型，输出 UE5 可直接导入的资产。

## 快速开始

```bash
# 生成单个机型（含预览渲染）
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background \
  --python build_robot.py -- --chassis medium --out ../../assets/out

# 批量生成三个机型
... --chassis all

# 跳过渲染，只出模型（批量迭代时快很多）
... --chassis all --no-render
```

已验证环境：**Blender 5.2.2 LTS**（2026-09-15 构建），单机型含渲染约 6 秒。

## 输出

| 文件 | 用途 |
|---|---|
| `robot_<variant>.blend` | Blender 工程，供美术接手修改 |
| `robot_<variant>.fbx` | **UE5 导入用**，单位已按 100 倍换算为厘米 |
| `robot_<variant>.glb` | 通用交换格式，供其他工具链使用 |
| `preview_robot_<variant>.png` | 1280×1280 预览渲染 |

## 三种机型

| 机型 | 高 | 宽 | 散热鳍 | 设计对应 |
|---|---|---|---|---|
| 轻型侦察 | 2.50 m | 1.25 m | 5 片（大） | 窄、薄、散热最好 |
| 中型通用 | 2.46 m | 1.47 m | 3 片 | 平衡 |
| 重型攻坚 | 2.37 m | 1.86 m | 2 片（小） | 宽、厚、装甲最厚 |

**几何本身承载了设计约束**——轻型机窄而多鳍，重型机宽而少鳍。这不是装饰，是让玩家在改装界面一眼就能读出"这机器跑得快还是扛得住"。

## 命名规范（与制作计划附录 A 一致）

**部件对象**（导入 UE 后对应可独立摧毁的部位）：

```
chassis_torso / chassis_pelvis / chassis_head      机体骨架
part_core                                           核心（可摧毁，自发光）
part_shoulder_L / _R                                肩甲
part_upperarm_L / _R                                上臂
part_forearm_L / _R                                 前臂
part_muzzle_L / _R                                  武器炮口
part_thruster_L / _R                                推进器
part_foot_L / _R                                    足部
part_backpack                                       背包
part_hip_L / _R / part_knee_L / _R / part_ankle_L / _R   关节
part_fin_L_01 …                                     散热鳍
```

**挂点空物体**（导入 UE 后作为 Socket 定位参考）：

```
socket_head      socket_arm_L      socket_arm_R
socket_back      socket_aux_01     socket_aux_02
socket_core      socket_root
```

## 坐标与单位约定

- Blender 中 **-Y 为机体正面，Z 轴向上**（Blender 标准正面视图约定）
- FBX 导出 `global_scale=100`，把 Blender 的米换算成 UE 的厘米
- 期望结果：UE 导入时 **Uniform Scale 保持 1.0**，机体高度约 2.4—2.5 米

> ⚠️ **首次导入 UE 必须验证两件事**：① 机体朝向是否为 +X 朝前；② 高度是否为 2.4—2.5 米。若不符，调整导入设置或在 Blender 侧改 `axis_forward` / `global_scale`。这一步必须在正式资产管线建立前跑通。

## 脚本结构

| 函数 | 职责 |
|---|---|
| `variant_params(v)` | 机型参数表（尺寸、配色、鳍片数量）—— **改数值就改这里** |
| `make_material(...)` | 创建 Principled BSDF 材质，对插槽名做版本兼容 |
| `add_box / add_cyl` | 带倒角的图元，倒角是硬表面机械感的关键 |
| `add_socket(...)` | 创建挂点空物体 |
| `build_robot(P, mats)` | 组装机体，返回 (部件列表, 挂点列表) |
| `world_bounds(objs)` | 世界空间包围盒，用于核对尺寸 |
| `setup_render(...)` | 相机、三点布光、色彩管理 |
| `export_fbx / export_glb` | 导出，参数按 RNA 实际支持的字段过滤 |

## 当前局限（诚实清单）

这一版是 **blockout 级（占位模型）**，不是成品资产：

| 缺失 | 影响 | 补齐方式 |
|---|---|---|
| **无 UV 展开** | 无法贴图，只能靠材质分槽 | 脚本可做 Smart UV Project，但需要美术调整接缝 |
| **无骨骼绑定** | 不能做动画，导入 UE 是静态网格 | 需要加 Armature + 顶点权重，或改用 UE 骨骼重定向 |
| **无 LOD** | 高模直接进游戏，性能超标 | 脚本可生成 Decimate 版 LOD1—3 |
| **无碰撞体** | 需要 UE 侧手动生成 | UE 的 Physics Asset 自动生成够用 |
| **拓扑为图元拼合** | 面数偏高、布线不规范，不适合做形变 | 若要变形动画需重新拓扑 |

## 下一步可做的事

按优先级：

1. **补 UV + LOD**（脚本可完成 80%，剩余接缝需人工）
2. **加骨架绑定**（这是让模型真正可用的关键一步）
3. **把 `variant_params` 接到 Excel/CSV**，让策划改表就能出新机型
4. **做部件模块库**：手臂、背包、推进器各出 3—5 个变体，用同一套挂点，直接对应游戏里的 40 个模块
