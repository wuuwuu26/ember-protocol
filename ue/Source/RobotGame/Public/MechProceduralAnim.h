// 程序化机体动画 —— 项目里没有任何动画资产，所以用代码摆骨骼
//
// 为什么不用动画资产：项目里一个 AnimSequence / AnimBlueprint 都没有，
// 而且这类资产没法用脚本从零生成。而"机体"这个题材恰好适合程序化：
//   走路 = 髋摆 + 膝弯 + 踝滚 + 骨盆起伏 + 躯干前倾
//   转向 = 躯干侧倾
//   开火 = 武器臂后坐 + 躯干后仰
//   待机 = 轻微呼吸摆动
//
// 为什么必须用 UPoseableMeshComponent：
//   USkeletalMeshComponent **没有**设置单根骨骼变换的接口 ——
//   SetBoneTransformByName 只存在于 UPoseableMeshComponent 上，
//   而 USkinnedMeshComponent 的 BoneSpaceTransforms 是 protected。
//   UPoseableMeshComponent 的 BoneSpaceTransforms 是 public，可以直接写。
//
// ─────────────────────────────────────────────────────────────
// 关于旋转的坐标系（这里踩过两次坑，改动前务必读完）
// ─────────────────────────────────────────────────────────────
//
// 【坑 1】写死"组件空间轴 = 角色轴"。组件轴的世界朝向取决于网格组件的
//   相对旋转，而这个旋转因资产来源而异：UE 标准人形资产是 +Y 朝前、
//   组件带 −90° yaw；本项目的机体在 Blender 导出时已把场景转过 90°，
//   组件相对旋转是**单位阵**。写死轴 → 一个资产上是对的，另一个上就把
//   "前后摆腿"变成"左右劈叉"。
//   → 修法：把**世界空间**的角色前后/左右/上下轴变换进组件空间再用。
//
// 【坑 2】用 SetBoneTransformByName(ComponentSpace) 逐骨旋转。
//   该接口内部要用 `ComponentSpaceTransforms[父]` 换算，而这个缓存数组
//   只在 RefreshBoneTransforms 时更新。同一帧里先转父、再转子，子骨读到
//   的是**上一帧**的父变换 → 层级累积误差，实测骨盆和腿骨漂移几十厘米。
//   → 修法：全程只写**局部变换**（BoneSpaceTransforms），旋转轴在缓存
//     基准姿势时一次性换算到"骨骼父空间"，之后每帧纯数学叠加，
//     不依赖任何引擎缓存。
//
// 局部增量的推导（bone-local delta）：
//   设骨骼静止时组件空间旋转为 C、父级为 P，则局部旋转 L = P⁻¹·C。
//   想让骨骼在组件空间里额外绕轴 a 转 θ，即 C' = Q(a,θ)·C，则
//       L' = P⁻¹·Q(a,θ)·C = Q(P⁻¹·a, θ)·L
//   所以只要把组件空间轴 a 变换进**父空间**（P⁻¹·a），再左乘到局部旋转上即可。
//   父级自己动的时候，子骨的轴自然跟着父级走 —— 这正是层级骨骼该有的行为
//   （膝弯平面跟着大腿走、踝弯平面跟着小腿走）。
#pragma once

#include "CoreMinimal.h"

class UPoseableMeshComponent;
class USkeletalMeshComponent;
class AActor;

/** 单根骨骼的静止参考数据 */
struct FMechBoneRest
{
	/** 静止局部变换（BoneSpaceTransforms 的初始值） */
	FTransform Local = FTransform::Identity;
	/** 静止组件空间旋转 */
	FQuat CompRot = FQuat::Identity;
	/** 父级静止组件空间旋转（用来把组件空间轴变换进骨骼父空间） */
	FQuat ParentCompRot = FQuat::Identity;
};

/** 一条腿的静止几何（组件空间），供两骨 IK 反解使用 */
struct FMechLegRest
{
	FVector Hip = FVector::ZeroVector;
	FVector Knee = FVector::ZeroVector;
	FVector Ankle = FVector::ZeroVector;
	/** 静止时大腿相对竖直方向的前倾角（度，正 = 向前） */
	float Theta1Deg = 0.f;
	/** 静止时小腿相对竖直方向的前倾角（度，正 = 向前） */
	float Theta2Deg = 0.f;
	/** 静止时髋到踝的竖直落差（cm，正数） */
	float DropCm = 0.f;
	/** 该腿自身的骨长（cm）。四足机前后腿不同，IK 必须用各自的。 */
	float Thigh = 0.f;
	float Shin = 0.f;
	/** 支撑期锁定的步幅（第一百轮）：落地那一刻取当前值，支撑期内不再变 */
	float LockedStride = 0.f;
	bool bStrideLocked = false;
	bool bValid = false;
	/** 诊断：上一帧 SolveLeg 解算的髋→踝距离（与夹紧前），用于定位脚滑跳变 */
	float LastD = 0.f;
	float LastDClamped = 0.f;
	/**
	 * 支撑期锚点（第八十七轮）：落地瞬间把脚的世界位置钉住，
	 * 支撑期直接用这个锚点做 IK 目标 —— 不管机体加减速，脚都不会在地上滑。
	 * 之前是"按速度推算步幅、让脚相对机体匀速后移"，速度一变就对不上。
	 */
	FVector AnchorWorld = FVector::ZeroVector;
	bool bAnchored = false;
	/** 上一帧是否处于支撑期（用于检测"刚落地"那一帧） */
	bool bPrevStance = false;
	/** 诊断：本帧 IK 用的髋位置与目标点（组件空间） */
	FVector DbgHip = FVector::ZeroVector;
	FVector DbgTarget = FVector::ZeroVector;
	FVector DbgAnkle = FVector::ZeroVector;
	FVector DbgAxisUp = FVector::ZeroVector;
	float DbgBase = 0.f;
	float DbgA = 0.f;
	float DbgK = 0.f;
	float DbgBendSign = 1.f;
	/** 诊断：正向运动学算出的脚位置与 IK 目标的偏差（cm） */
	float DbgFKErr = 0.f;
	/** 诊断：本帧 髋→目标 向量在（前向, 上, 组件X）上的分量 */
	FVector DbgE = FVector::ZeroVector;
};

/** 程序化动画的每实例状态 */
struct FMechAnimState
{	/** 步态相位，按速度累加，0—2π 循环 */
	float GaitPhase = 0.f;
	/** 累计时间，用于待机摆动 */
	float Time = 0.f;
	/** 后坐强度 0—1，触发后自然衰减 */
	float Recoil = 0.f;
	/** 瞄准强度 0—1：抬起武器臂的过渡量 */
	float AimBlend = 0.f;
	/** 枪口俯仰（度，正 = 目标在上方）。由外部按目标方向写入，只在瞄准时生效 */
	float AimPitchDeg = 0.f;
	/** 后坐时武器臂上摆的最大角度（度）。玩家保持默认，敌人覆盖为更明显的值 */
	float RecoilKickDeg = 14.f;
	/** 后坐衰减速率（1/秒）。越大恢复越快，开火"啪"一下的感觉越强 */
	float RecoilDecayRate = 3.4f;
	/** 支撑腿状态：两条腿都在 = 双腿支撑；只剩一条 = 独腿支撑（骨盆下沉+侧倾）；全无 = 站立不播步态 */
	int32 LegsAlive = 2;
	/** 另一侧腿已断（用于判断往哪边压重心）：0=没断, -1=左断, +1=右断 */
	int32 MissingLegSide = 0;
	/** -DebugGait 脚滑日志节流时间 */
	float PrevSlideLog = -100.f;
	/** -DebugGait 步态日志节流时间（每实例独立，否则多台机共用计时互相干扰） */
	float PrevGaitLog = -100.f;
	/** -DebugGait ④ 阶段（速度/步频/步幅）日志节流，与 ⑥' 的日志分开，避免互相覆盖 */
	float PrevPhaseLog = -100.f;
	/** 脚滑检测：连续支撑帧计数（用于连续第 3+ 帧稳态统计，排除落地跳变） */
	int32 CntStanceL = 0;
	int32 CntStanceR = 0;
	float SlideSumL = 0.f;
	float SlideSumR = 0.f;
	int32 SlideSamplesL = 0;
	int32 SlideSamplesR = 0;
	/** 脚滑检测：上一帧脚世界位置（每实例独立，绝不能用品 static 否则多台机互相污染） */
	FVector PrevFL = FVector::ZeroVector;
	FVector PrevFR = FVector::ZeroVector;
	bool bPrevStanceL = false;
	bool bPrevStanceR = false;
	bool bPrevValid = false;
	/** 脚滑诊断：支撑骨盆高度（SupportH）平滑值，消除换腿时支撑集切换导致的骨盆跳变 */
	float SupportHSmoothed = -1.f;
	/** 支撑期单窗口最大滑步（cm/s，等效 60fps），随 [脚滑] 日志重置 */
	float SlipMaxL = 0.f, SlipMaxR = 0.f;
	/** 诊断：脚单帧位移的前向/侧向分量、机体位移（判定残余滑步来源） */
	float DbgFwdStepL = 0.f;
	float DbgLatStepL = 0.f;
	float DbgCompStep = 0.f;
	FVector DbgPrevCompW = FVector::ZeroVector;
	/** 诊断：上一帧脚的**组件空间**位置（排除组件变换抖动，用于对照） */
	FVector PrevFLc = FVector::ZeroVector;
	/** 平滑后的步态相位推进速率（rad/s），避免瞬时速度抖动导致 Fwd 跳变 */
	float SmoothOmega = -1.f;
	/** 无偏后移核对累加器（第六十五轮）：逐帧累加、不筛选，按窗口汇总 */
	int32 DbgNFrames = 0;
	float DbgSumAbsStep = 0.f;
	float DbgSumExpect = 0.f;
	float DbgSumStep = 0.f;
	float DbgSumResidual = 0.f;
	float DbgMaxResidual = 0.f;
	/** 诊断：实际相位增量 vs Omega·Dt（验证后移速率前提） */
	float DbgSumDPhase = 0.f;
	float DbgSumOmegaDt = 0.f;
	float DbgPrevPhase = 0.f;
	/** 诊断：骨盆起伏逐帧变化量（|ΔBob|），用于判定它是否是拖脚的主因 */
	float DbgSumAbsDBob = 0.f;
	float DbgMaxDBob = 0.f;
	float DbgPrevBob = 0.f;
	bool DbgHavePrevBob = false;
	/** 诊断：脚沿机体侧向的世界位移绝对量（侧向滑步） */
	float DbgLatStepAbs = 0.f;
	float DbgSumLatStep = 0.f;
	/** 诊断：机体实际位移（验证 expect=Speed·Dt 基准） */
	float DbgSumCompStep = 0.f;
	/** 诊断：机体沿世界 +X 的带符号累计位移 */
	float DbgSumCompSigned = 0.f;
	/** 宏观滑步度量：窗口起点的脚/机体绝对位置与时间（不依赖逐帧差分） */
	FVector MacroFootStart = FVector::ZeroVector;
	FVector MacroCompStart = FVector::ZeroVector;
	float MacroTimeStart = 0.f;
	bool bMacroInit = false;
	/** 窗口内脚走过的总路程（cm），衡量腿的忙碌程度 */
	float MacroPathLen = 0.f;
	/** 实际位移速度（cm/s）：组件位置的真实位移速率，用于给步态节奏封顶 */
	float ActualSpeed = -1.f;
	FVector CompPrev = FVector::ZeroVector;
	bool bCompPrevValid = false;
	FVector DbgPrevCompW2 = FVector::ZeroVector;
	bool DbgHavePrevComp = false;
	/** 诊断：骨盆横摆逐帧变化量 */
	float DbgSumAbsDSway = 0.f;
	float DbgPrevSway = 0.f;
	bool DbgHavePrevSway = false;
	/** 诊断：Fwd 逐帧变化量与理论值(-Speed·Dt)的偏差 */
	float DbgSumAbsDFwd = 0.f;
	float DbgSumAbsDFwdErr = 0.f;
	float DbgPrevFwd = 0.f;
	bool DbgHavePrevFwd = false;
	/** 诊断：上一累加帧的 S.Time 与是否已有（帧间差分只在时间连续时有效） */
	float DbgPrevTime = 0.f;
	bool DbgHavePrevFrame = false;
	/** 诊断：脚底离地的日志节流 */
	float PrevFootLog = -100.f;
	/** 步态速度的平滑值（-1 = 尚未初始化）——避免速度抖动直接驱动步幅 */
	float GaitSpeedSmoothed = -1.f;
	/** 移动方向（组件空间）的平滑值，用于支撑脚沿真实方向后退 */
	FVector MoveDirSmoothed = FVector::ZeroVector;
	/** 支撑期脚在世界里的位移速度累计（cm/s），真实打滑量 */
	float DbgStanceMoveL = 0.f;
	float DbgStanceMoveR = 0.f;
	int32 DbgStanceMoveNL = 0;
	int32 DbgStanceMoveNR = 0;
	/** 诊断：膝盖弯曲方向日志节流（每条腿独立计时） */
	float PrevBendLog = -100.f;
	/** 诊断：已打印过弯曲判定的腿（按髋位置区分） */
	TMap<int32, int32> BendLogged;
	/** 诊断：支撑脚相对静止高度的偏差累计 */
	float DbgStanceDev = 0.f;
	int32 DbgStanceN = 0;
	float DbgSwingMax = 0.f;
	/**
	 * 诊断：按腿分别统计（第七十六轮）。
	 * 四足机有四条腿，只统计 L/R 会把另外两条完全漏掉 —— 上一轮 C_9 报
	 * "摆动最高=0" 就是这个原因（它的 IFootL 那条腿常处支撑态）。
	 * 顺序固定为 L, R, BL, BR。
	 */
	float DbgLegStanceDev[4] = {0.f, 0.f, 0.f, 0.f};
	int32 DbgLegStanceN[4] = {0, 0, 0, 0};
	float DbgLegSwingMax[4] = {0.f, 0.f, 0.f, 0.f};
	int32 DbgLegSwingN[4] = {0, 0, 0, 0};
	bool bDbgLoggedGap = false;
	/** IK 可达性裁剪次数（诊断滑步来源） */
	int32 IKClampCount = 0;
	/** IK 超出腿长的最大量（cm） */
	float IKOverreachCm = 0.f;
	/** IK 裁剪分别发生在支撑期 / 摆动期的次数 */
	int32 IKClampStance = 0;
	int32 IKClampSwing = 0;
	/** 上一帧速度，用来算加速度引起的俯仰 */
	FVector PrevVelocity = FVector::ZeroVector;

	/** 骨骼名 → 静止参考数据 */
	TMap<FName, FMechBoneRest> Rest;
	/** 兼容旧代码：静止局部变换表 */
	TMap<FName, FTransform> BaseTransforms;

	/** 髋→膝 长度（cm），缓存时从骨架量出 */
	float ThighLenCm = 0.f;
	/** 膝→踝 长度（cm） */
	float ShinLenCm = 0.f;
	/** 髋→踝 长度（cm），用于步幅反解 */
	float LegLengthCm = 0.f;
	/** 静止姿势下"髋→脚"的组件空间向量（保留给旧逻辑/诊断） */
	FVector HipToFootRest = FVector::ZeroVector;

	/** 左右腿的静止几何（两骨 IK 用；拿不到时 bValid=false，退回旧逻辑） */
	FMechLegRest LegL;
	FMechLegRest LegR;
	/** 四足的后腿（左后 / 右后）。双足机这两条恒为 bValid=false */
	FMechLegRest LegBL;
	FMechLegRest LegBR;

	/**
	 * 骨骼局部空间的长度单位 / 厘米。
	 *
	 * ⚠️ 这批资产从 FBX 进来后，骨骼的局部位移是**米**（小腿 0.43），
	 * 而世界单位是厘米（小腿 43cm）—— 中间有一层 100 倍的缩放挂在骨架上。
	 * 所以任何"往骨骼局部平移 N 厘米"的代码都必须乘这个系数，
	 * 否则 3cm 的骨盆起伏会变成 3 米的位移（实测：走路时机体直接沉到地下）。
	 */
	float BoneUnitPerCm = 1.f;

	/** 骨盆左右摆的平滑值（cm）。直接按支撑腿切换会让身体横向"弹"一下 */
	float SwayCm = 0.f;

	/** 上一步的朝向，用来算转向角速度 */
	float PrevYaw = 0.f;
	bool bBaseCached = false;

	// ── 整体身体动作（作用在网格组件的相对变换上，不依赖骨骼）──
	/** 网格组件的初始相对位置/旋转，第一帧缓存，之后都在它基础上叠加 */
	FVector BaseMeshLoc = FVector::ZeroVector;
	FRotator BaseMeshRot = FRotator::ZeroRotator;
	bool bBaseMeshCached = false;
};

namespace MechProceduralAnim
{
	/**
	 * 创建一个可见的、可程序化摆姿势的网格，挂在 SourceMesh 的父节点上，
	 * 并把 SourceMesh 设为不可见。
	 */
	UPoseableMeshComponent* CreateVisualMesh(AActor* Owner,
		USkeletalMeshComponent* SourceMesh);

	/** 让动画网格跟随源网格的资产（换机体 / 换敌人外观时调用） */
	void SyncVisualMesh(UPoseableMeshComponent* Visual,
		USkeletalMeshComponent* Source);

	/** 缓存基准姿势。设置网格之后调用一次。 */
	void CacheBasePose(UPoseableMeshComponent* Mesh, FMechAnimState& State);

	/**
	 * 每帧更新**骨骼姿势**：髋摆 + 膝弯 + 踝滚的三段式步态、手臂反相摆动、
	 * 骨盆起伏（按"支撑腿伸长度"精确计算，不穿地也不悬空）、
	 * 躯干前倾/侧倾/开火后坐、头部注视。
	 *
	 * 作用对象必须是 UPoseableMeshComponent（见文件头的说明）。
	 * 骨骼名用候选表匹配，玩家 rig 与敌人 rig 共用同一份代码。
	 */
	void Update(UPoseableMeshComponent* Mesh, FMechAnimState& State,
		const FVector& Velocity, float YawDegrees, float MaxSpeed,
		float DeltaSeconds);

	/**
	 * 每帧更新**整体身体动作**：走路上下起伏、加速前后倾、转向侧倾、
	 * 开火后坐。作用在网格组件的相对变换上，完全不依赖骨骼。
	 * 这是骨骼动画的降级方案。
	 */
	void UpdateBody(USkeletalMeshComponent* Mesh, FMechAnimState& State,
		const FVector& Velocity, const FVector& ActorForward,
		float YawDegrees, float MaxSpeed, float DeltaSeconds);

	/** 开火后坐 */
	void TriggerRecoil(FMechAnimState& State, float Strength = 1.f);

	/** 把"部位破坏隐藏骨骼"同步到动画网格（按骨骼名前缀） */
	void HideBonesByPrefix(UPoseableMeshComponent* Mesh, const FString& Prefix);

	/**
	 * 取某根骨骼在世界空间的变换。找不到返回 false。
	 * 用于把枪口 / 挂点跟随程序化动画（骨骼姿势每帧被代码改写，
	 * 所以必须从动画网格上取，而不是从不参与动画的源网格上取）。
	 */
	bool GetBoneWorldTransform(UPoseableMeshComponent* Mesh,
		const FName BoneName, FTransform& Out);
}
