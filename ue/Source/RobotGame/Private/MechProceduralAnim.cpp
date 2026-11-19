#include "MechProceduralAnim.h"

#include "Components/PoseableMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Actor.h"
#include "Engine/SkeletalMesh.h"
#include "Misc/CommandLine.h"

namespace
{
	// ── 骨骼名候选表 ──
	// 玩家 rig（build_chassis.build_rig）：
	//   root / pelvis / torso / head
	//   shoulder_L,R / upperarm_L,R / forearm_L,R
	//   thigh_L,R / shin_L,R / foot_L,R
	// 敌人 rig（robotlib.auto_rig）：core / torso / head / arm_L,R / leg_L,R
	// 候选表让两套命名共用同一份代码；旧版单段腿（leg_L）保留为兜底，
	// 这样即使资产没重导也不会崩，只是没有膝弯。
	const TCHAR* GPelvisNames[] = { TEXT("pelvis"), TEXT("core"), TEXT("root") };
	const TCHAR* GTorsoNames[]  = { TEXT("torso") };
	const TCHAR* GHeadNames[]   = { TEXT("head") };

	const TCHAR* GThighLNames[] = { TEXT("thigh_L"), TEXT("leg_L") };
	const TCHAR* GThighRNames[] = { TEXT("thigh_R"), TEXT("leg_R") };
	const TCHAR* GShinLNames[]  = { TEXT("shin_L"), TEXT("calf_L") };
	const TCHAR* GShinRNames[]  = { TEXT("shin_R"), TEXT("calf_R") };
	const TCHAR* GFootLNames[]  = { TEXT("foot_L") };
	const TCHAR* GFootRNames[]  = { TEXT("foot_R") };
	// 四足的后腿：Blender 侧命名为 *_BL / *_BR（前腿沿用 *_L / *_R）
	const TCHAR* GThighBLNames[] = { TEXT("thigh_BL") };
	const TCHAR* GThighBRNames[] = { TEXT("thigh_BR") };
	const TCHAR* GShinBLNames[]  = { TEXT("shin_BL") };
	const TCHAR* GShinBRNames[]  = { TEXT("shin_BR") };
	const TCHAR* GFootBLNames[]  = { TEXT("foot_BL") };
	const TCHAR* GFootBRNames[]  = { TEXT("foot_BR") };

	const TCHAR* GClavLNames[]   = { TEXT("shoulder_L") };
	const TCHAR* GClavRNames[]   = { TEXT("shoulder_R") };
	const TCHAR* GUpperArmLNames[] = { TEXT("upperarm_L"), TEXT("arm_L") };
	const TCHAR* GUpperArmRNames[] = { TEXT("upperarm_R"), TEXT("arm_R") };
	const TCHAR* GForearmLNames[]  = { TEXT("forearm_L") };
	const TCHAR* GForearmRNames[]  = { TEXT("forearm_R") };

	int32 FindBone(const FReferenceSkeleton& Ref,
		const TCHAR* const* Names, int32 Count)
	{
		for (int32 i = 0; i < Count; ++i)
		{
			const int32 Idx = Ref.FindBoneIndex(FName(Names[i]));
			if (Idx != INDEX_NONE)
			{
				return Idx;
			}
		}
		return INDEX_NONE;
	}

	/** 从 BoneSpaceTransforms 累积出某骨骼的组件空间变换（父→子连乘）
	 *
	 * ⚠️⚠️ 乘法顺序是这份代码历史上最贵的一个坑 ⚠️⚠️
	 *
	 * UE 的约定（TransformNonVectorized.h 原文）：
	 *     "C = A * B will yield a transform C that logically first applies A then B"
	 * 而引擎自己算组件空间姿势时是（PoseableMeshComponent.cpp:133）：
	 *     FTransform::Multiply(SpaceBases + i, Local + i, SpaceBases + parent)
	 * 即  C[i] = L[i] * C[parent]  —— 先 L[i]，再 C[parent]。
	 *
	 * 展开成链：C[i] = L[i] * L[parent] * L[gp] * ... * L[root]
	 *              ↑ 左起第一个先作用，所以 **祖先在右边**。
	 *
	 * 我第一版写成了 `Comp = L[parent] * Comp`（顺序反过来），
	 * 结果：只有"父骨就是 root"的那一层是对的（例如 thigh 的父是 pelvis，
	 * pelvis 的父是 root —— 恰好一层），再深一层全错：
	 *   · thigh 的旋转轴正确 → 大腿确实在矢状面里前后摆
	 *   · shin / foot / upperarm / forearm 的 ParentCompRot 全错
	 *     → 膝盖、脚踝、肩膀、肘的**旋转轴是歪的** → 小腿横着甩、手臂乱摆
	 * 症状就是"前后差看着还行、左右差却在几十厘米到一米之间乱跳"，
	 * 以及用户反馈的"腿和手都不是绕根部转"。**顺序就是根因。**
	 */
	FTransform ComponentSpaceOf(const UPoseableMeshComponent* Mesh,
		const FReferenceSkeleton& Ref, int32 Index)
	{
		FTransform Comp = Mesh->BoneSpaceTransforms[Index];
		int32 Parent = Ref.GetParentIndex(Index);
		int32 Guard = 0;
		while (Parent >= 0 && Guard++ < 256)
		{
			Comp = Comp * Mesh->BoneSpaceTransforms[Parent];
			Parent = Ref.GetParentIndex(Parent);
		}
		return Comp;
	}

	/**
	 * 摆姿势用的上下文：把"网格 + 骨架 + 每根骨骼**当前**的组件空间旋转"
	 * 打包在一起。
	 *
	 * 为什么要存"当前"旋转，而不是每次去查 CacheBasePose 里的静止旋转？
	 *
	 * ① 旋转轴必须相对**当前的父骨朝向**换算。父骨已经转过之后，
	 *    子骨绕"组件空间某轴"转，等价于绕"父骨局部空间的某个方向"转 ——
	 *    这个方向会随父骨一起变。用静止值算，子骨就会甩到错误的方向上。
	 *
	 * ② 同一根骨骼可能被旋转两次（例如躯干：先绕左右轴前倾，再绕前后轴侧倾）。
	 *    旧实现每次都写 `Delta * 静止旋转`，**第二次会把第一次覆盖掉**，
	 *    前倾直接丢失。改成在"当前值"上累乘，两次旋转才真正叠加。
	 *
	 * 前提：调用顺序必须"父先子后"。FReferenceSkeleton 保证父骨的 index
	 * 一定小于子骨，所以按 index 递增顺序处理天然满足。
	 */
	struct FPoseCtx
	{
		UPoseableMeshComponent* Mesh = nullptr;
		const FReferenceSkeleton* Ref = nullptr;
		TArray<FQuat> CurRot;   // 每根骨骼当前的组件空间旋转
		/** 骨骼局部空间的长度单位 / 厘米（见 FMechAnimState::BoneUnitPerCm） */
		float UnitPerCm = 1.f;

		FQuat ParentRot(int32 Index) const
		{
			const int32 P = Ref->GetParentIndex(Index);
			return (P >= 0 && CurRot.IsValidIndex(P)) ? CurRot[P] : FQuat::Identity;
		}
	};

	/**
	 * 在**组件空间**里绕某根骨骼自身原点额外旋转 Degrees 度。
	 *
	 * 推导：要把"组件空间的轴 a"变成"父骨局部空间的方向"，只需
	 *         a' = ParentRot⁻¹ · a
	 *       然后在父空间里左乘 Δ = Q(a', θ)。因为
	 *         NewCompRot = ParentRot · Δ · L = (ParentRot·Δ·ParentRot⁻¹) · ParentRot · L
	 *                     = Δ_comp · CurCompRot
	 *       正好等于"在组件空间里绕 a 转 θ"。
	 *
	 * 全程只读写 BoneSpaceTransforms 与我们自己的 CurRot，不碰引擎缓存，
	 * 所以同一帧里"先转父、再转子"是精确的，不会累积误差。
	 */
	void RotateBoneAxis(FPoseCtx& C, int32 Index,
		const FVector& AxisComponent, float Degrees)
	{
		if (Index < 0 || !C.Mesh || !C.CurRot.IsValidIndex(Index)
			|| FMath::IsNearlyZero(Degrees, 0.0005f))
		{
			return;
		}
		const FQuat ParentRot = C.ParentRot(Index);
		const FVector AxisInParent = ParentRot.Inverse().RotateVector(AxisComponent);
		const FQuat Delta(AxisInParent, FMath::DegreesToRadians(Degrees));

		FTransform& T = C.Mesh->BoneSpaceTransforms[Index];
		const FQuat NewLocalRot = (Delta * T.GetRotation()).GetNormalized();
		T.SetRotation(NewLocalRot);
		C.CurRot[Index] = (ParentRot * NewLocalRot).GetNormalized();
	}

	/**
	 * 把骨骼的**组件空间朝向**直接设为 Target（不基于当前值）。
	 * 用于"脚掌必须平贴地面"这种绝对约束：脚的世界俯仰不该随小腿摆动而变。
	 */
	void SetBoneCompRot(FPoseCtx& C, int32 Index, const FQuat& Target)
	{
		if (Index < 0 || !C.Mesh || !C.CurRot.IsValidIndex(Index))
		{
			return;
		}
		const FQuat ParentRot = C.ParentRot(Index);
		FTransform& T = C.Mesh->BoneSpaceTransforms[Index];
		const FQuat NewLocalRot = (ParentRot.Inverse() * Target).GetNormalized();
		T.SetRotation(NewLocalRot);
		C.CurRot[Index] = Target.GetNormalized();
	}

/** 沿**组件空间**方向平移骨骼（骨盆起伏），支点仍是骨骼自身原点 */
void OffsetBoneAxis(FPoseCtx& C, int32 Index,
	const FVector& AxisComponent, float Distance)
{
	if (Index < 0 || !C.Mesh || FMath::IsNearlyZero(Distance, 0.001f))
	{
		return;
	}
	const FVector DirInParent =
		C.ParentRot(Index).Inverse().RotateVector(AxisComponent);
	FTransform& T = C.Mesh->BoneSpaceTransforms[Index];
	// ⚠️ 必须乘 UnitPerCm：骨骼局部位移的单位是米，传入的 Distance 是厘米。
	//    漏掉这一步 → 3cm 的起伏变成 3m 的下沉（本轮踩到的坑）。
	T.SetLocation(T.GetLocation() + DirInParent * (Distance * C.UnitPerCm));
}

	/** 平滑步进，用于把 0/1 过渡量变成平滑曲线 */
	float SmoothStep(float x)
	{
		x = FMath::Clamp(x, 0.f, 1.f);
		return x * x * (3.f - 2.f * x);
	}

	/**
	 * 从 BoneSpaceTransforms **自己**累积出骨骼的组件空间位置。
	 *
	 * ⚠️ 不要用 Mesh->GetBoneLocation(WorldSpace) 来验证手动摆骨的结果：
	 *    它读的是引擎缓存 ComponentSpaceTransforms，那份数组只在
	 *    RefreshBoneTransforms 时刷新，可能落后一帧甚至几帧。
	 *    调姿态时如果依赖它做反馈，就会得到"自相矛盾"的数值，
	 *    进而把完全正确的数学误判成错误。这里全程只读我们刚写进去的数组。
	 *
	 * ⚠️ 乘法顺序同 ComponentSpaceOf：祖先在右，写成 `Comp * Local[parent]`。
	 */
	FVector LocalAccumCompPos(const UPoseableMeshComponent* Mesh,
		const FReferenceSkeleton& Ref, int32 Index)
	{
		if (Index < 0 || Index >= Mesh->BoneSpaceTransforms.Num())
		{
			return FVector::ZeroVector;
		}
		FTransform Comp = Mesh->BoneSpaceTransforms[Index];
		int32 P = Ref.GetParentIndex(Index);
		int32 Guard = 0;
		while (P >= 0 && Guard++ < 256)
		{
			Comp = Comp * Mesh->BoneSpaceTransforms[P];
			P = Ref.GetParentIndex(P);
		}
		return Comp.GetLocation();
	}

	/** 同上，但再乘组件世界变换，得到世界坐标 */
	FVector LocalAccumWorldPos(const UPoseableMeshComponent* Mesh,
		const FReferenceSkeleton& Ref, int32 Index)
	{
		return Mesh->GetComponentTransform().TransformPosition(
			LocalAccumCompPos(Mesh, Ref, Index));
	}

	/**
	 * 按**参考姿势**（RefBonePose）累积出骨骼原点在组件空间的坐标（第七十六轮）。
	 *
	 * 为什么不用 LocalAccumCompPos：它读的是运行时数组 BoneSpaceTransforms，
	 * 而 IK 目标点（Rest.Ankle 等）必须在"未被打过姿态的静止几何"上量，
	 * 否则两者基准不同 —— 实测巨像 C_9 目标 43cm、脚实际落在 22cm（差 21cm），
	 * 而 IK 报 clamp == d，即"以为到了"。同一份缓存里一半读参考姿势、
	 * 一半读运行时数组，是这类"目标与实际对不上"的通病。
	 */
	FVector RefAccumCompPos(const FReferenceSkeleton& Ref, int32 Index)
	{
		const TArray<FTransform>& RefPose = Ref.GetRefBonePose();
		if (Index < 0 || !RefPose.IsValidIndex(Index))
		{
			return FVector::ZeroVector;
		}
		FTransform Comp = RefPose[Index];
		int32 P = Ref.GetParentIndex(Index);
		int32 Guard = 0;
		while (P >= 0 && RefPose.IsValidIndex(P) && Guard++ < 256)
		{
			Comp = Comp * RefPose[P];
			P = Ref.GetParentIndex(P);
		}
		return Comp.GetLocation();
	}
}

// ─────────────────────────────────────────────
// 网格管理
// ─────────────────────────────────────────────

UPoseableMeshComponent* MechProceduralAnim::CreateVisualMesh(AActor* Owner,
	USkeletalMeshComponent* SourceMesh)
{
	if (!Owner || !SourceMesh)
	{
		return nullptr;
	}

	UPoseableMeshComponent* Visual = NewObject<UPoseableMeshComponent>(Owner);
	if (!Visual)
	{
		return nullptr;
	}

	Visual->SetMobility(EComponentMobility::Movable);
	Visual->SetupAttachment(SourceMesh->GetAttachParent());
	Visual->RegisterComponent();
	Visual->AttachToComponent(SourceMesh->GetAttachParent(),
		FAttachmentTransformRules::KeepRelativeTransform);

	// 必须和源网格的相对变换完全一致，否则动画网格会和角色错位
	Visual->SetRelativeTransform(SourceMesh->GetRelativeTransform());
	Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Visual->SetCastShadow(true);
	Visual->SetVisibility(true, true);

	// 手动摆骨骼的组件**不会**跟着骨骼更新自己的包围盒，很容易被视锥剔除 ——
	// 表现就是"角色明明站在画面正中，却完全看不见"。
	// 直接沿用父组件（胶囊体）的包围盒：胶囊体有 120cm 半径，足够安全。
	Visual->bUseAttachParentBound = true;

	// 源网格退居幕后：它只负责给部位破坏系统做骨骼查询与隐藏，
	// 不参与渲染（否则两个网格重叠会 z-fighting）
	//
	// -ShowSource：诊断开关。反过来隐藏 PoseableMesh、显示原生骨骼网格，
	// 用来判断"表面没有贴图"到底是网格 UV 丢了，还是 PoseableMesh 这条
	// 渲染路径不传 UV。
	if (FParse::Param(FCommandLine::Get(), TEXT("ShowSource")))
	{
		Visual->SetVisibility(false, true);
		SourceMesh->SetVisibility(true, true);
		SourceMesh->SetHiddenInGame(false);
	}
	else
	{
		SourceMesh->SetVisibility(false, true);
		SourceMesh->SetHiddenInGame(true);
	}

	return Visual;
}

void MechProceduralAnim::SyncVisualMesh(UPoseableMeshComponent* Visual,
	USkeletalMeshComponent* Source)
{
	if (!Visual || !Source)
	{
		return;
	}
	USkeletalMesh* Mesh = Source->GetSkeletalMeshAsset();
	if (!Mesh)
	{
		return;
	}
	Visual->SetSkinnedAssetAndUpdate(Mesh, true);

	// 材质：**直接写 OverrideMaterials 数组**，不要用 SetMaterial。
	//
	// 踩过的坑：UMeshComponent::SetMaterial 只在
	// `0 <= ElementIndex < OverrideMaterials.Num()` 时生效，
	// 而新组件的 OverrideMaterials 是空数组 —— 调用直接被忽略，
	// 结果角色渲染成 UE 的默认"棋盘格"材质。
	TArray<TObjectPtr<UMaterialInterface>> Mats;
	const int32 NumMats = Source->GetNumMaterials();
	for (int32 i = 0; i < NumMats; ++i)
	{
		Mats.Add(Source->GetMaterial(i));
	}
	Visual->OverrideMaterials = Mats;
	Visual->MarkRenderStateDirty();

	// 诊断：把实际拿到的材质打出来（排查"表面没有贴图"用）
	{
		FString Names;
		for (int32 i = 0; i < Mats.Num(); ++i)
		{
			Names += Mats[i] ? Mats[i]->GetName() : TEXT("null");
			if (i < Mats.Num() - 1)
			{
				Names += TEXT(",");
			}
		}
		UE_LOG(LogTemp, Warning,
			TEXT("[视觉] 网格=%s 源材质槽=%d → %s"),
			Mesh ? *Mesh->GetName() : TEXT("null"), Mats.Num(), *Names);
	}
}

void MechProceduralAnim::CacheBasePose(UPoseableMeshComponent* Mesh,
	FMechAnimState& State)
{
	State.Rest.Reset();
	State.BaseTransforms.Reset();
	State.bBaseCached = false;

	if (!Mesh)
	{
		return;
	}
	USkeletalMesh* SkinnedAsset = Cast<USkeletalMesh>(Mesh->GetSkinnedAsset());
	if (!SkinnedAsset)
	{
		return;
	}

	const FReferenceSkeleton& Ref = SkinnedAsset->GetRefSkeleton();
	const int32 Num = Ref.GetNum();
	if (Mesh->BoneSpaceTransforms.Num() != Num)
	{
		// 姿势数组还没初始化好，下一帧再试
		return;
	}

	// ⚠️ 基准姿势必须取**参考姿势**（RefBonePose），不能取 Mesh->BoneSpaceTransforms：
	//    后者是运行时数组，首次进入本函数时可能仍是导入时的初始值，
	//    也可能是上一次会话留下的姿态。用错基准 → 每帧的重置起点错 →
	//    IK 目标与真实骨骼错位（第七十四轮"脚穿地 16cm"就出在这里）。
	const TArray<FTransform>& RefPoseRef = Ref.GetRefBonePose();
	for (int32 i = 0; i < Num; ++i)
	{
		const FName BoneName = Ref.GetBoneName(i);
		FMechBoneRest R;
		R.Local = RefPoseRef.IsValidIndex(i) ? RefPoseRef[i] : Mesh->BoneSpaceTransforms[i];

		// 组件空间朝向也按参考姿势累积
		FTransform Comp = R.Local;
		int32 P = Ref.GetParentIndex(i);
		int32 Guard = 0;
		while (P >= 0 && RefPoseRef.IsValidIndex(P) && Guard++ < 256)
		{
			Comp = Comp * RefPoseRef[P];
			P = Ref.GetParentIndex(P);
		}
		R.CompRot = Comp.GetRotation().GetNormalized();

		const int32 ParentIdx = Ref.GetParentIndex(i);
		FTransform ParentComp = FTransform::Identity;
		if (ParentIdx >= 0 && RefPoseRef.IsValidIndex(ParentIdx))
		{
			ParentComp = RefPoseRef[ParentIdx];
			int32 Q = Ref.GetParentIndex(ParentIdx);
			int32 G2 = 0;
			while (Q >= 0 && RefPoseRef.IsValidIndex(Q) && G2++ < 256)
			{
				ParentComp = ParentComp * RefPoseRef[Q];
				Q = Ref.GetParentIndex(Q);
			}
		}
		R.ParentCompRot = ParentComp.GetRotation().GetNormalized();

		State.Rest.Add(BoneName, R);
		State.BaseTransforms.Add(BoneName, R.Local);
	}
	State.bBaseCached = State.Rest.Num() == Num;

	// ── 量腿部尺寸（髋 / 膝 / 踝 的高度差）──
	// 髋 = thigh 原点，膝 = shin 原点，踝 = foot 原点。
	// 因为骨架原点就锚在关节上（见 build_rig），这几个差值就是真实骨长。
	const int32 IThigh = FindBone(Ref, GThighLNames, UE_ARRAY_COUNT(GThighLNames));
	const int32 IShin = FindBone(Ref, GShinLNames, UE_ARRAY_COUNT(GShinLNames));
	const int32 IFoot = FindBone(Ref, GFootLNames, UE_ARRAY_COUNT(GFootLNames));

	auto BoneLocZ = [&](int32 Idx) -> float
	{
		return (Idx >= 0)
			? Mesh->GetBoneLocation(Ref.GetBoneName(Idx), EBoneSpaces::ComponentSpace).Z
			: 0.f;
	};

	// 组件空间的 Z 不一定等于世界上下轴（资产可能整体转过 90°）。
	// 这里用"髋→踝"向量的模长做腿长，用它在上下轴上的投影做竖直落差，
	// 两者都从实际骨架量，不做任何朝向假设。
	// ⚠️ 必须从**参考姿势**（FReferenceSkeleton 的 RefBonePose）自己累积，不能读
	//    BoneSpaceTransforms（那是运行时数组，可能已被上一帧姿态改写），
	//    也不能用 Mesh->GetBoneLocation（引擎缓存可能落后一帧甚至未初始化）。
	//    第七十四轮的"脚没贴地"就是这里出错：C_9 量到踝高 33cm、实际脚块顶也 34cm
	//    看着合理，但拿它当 IK 目标后脚被拉到 18.8cm（穿地 16cm）——
	//    因为量的时候用的是被打过姿态的数组。
	//    第七十六轮：实现收敛成全局的 RefAccumCompPos，避免这里和 FillLeg 两份实现走偏。
	auto CompPos = [&](int32 Idx) -> FVector
	{
		return RefAccumCompPos(Ref, Idx);
	};

	if (IThigh >= 0 && IFoot >= 0)
	{
		const FVector Hip = CompPos(IThigh);
		const FVector Ankle = CompPos(IFoot);
		const FVector Delta = Ankle - Hip;
		const float Len = Delta.Size();
		if (Len > 1.f)
		{
			State.LegLengthCm = Len;
			State.HipToFootRest = Delta;
		}
	}
	if (IThigh >= 0 && IShin >= 0)
	{
		// 用三维距离：膝盖可能水平偏移（四足屈膝站立），只取 Z 差会低估骨长，
		// 让 L1+L2 恒等于垂直落差 → 腿"看起来"伸直 → 水平余量恒为 0 → IK 必超伸。
		const float L = FVector::Dist(CompPos(IThigh), CompPos(IShin));
		if (L > 1.f) { State.ThighLenCm = L; }
	}
	if (IShin >= 0 && IFoot >= 0)
	{
		const float L = FVector::Dist(CompPos(IShin), CompPos(IFoot));
		if (L > 1.f) { State.ShinLenCm = L; }
	}
	// 兜底：没有分节腿（旧资产 / 敌人）时按总长对半分
	if (State.ThighLenCm < 1.f || State.ShinLenCm < 1.f)
	{
		const float Half = FMath::Max(State.LegLengthCm, 90.f) * 0.5f;
		State.ThighLenCm = Half;
		State.ShinLenCm = Half;
	}

	// ── 两骨 IK 的静止几何 ──
	// 把髋/膝/踝的组件空间位置与"相对竖直方向的前倾角"记下来，
	// 之后每帧只要求出目标角，减去这两个静止角就是骨骼该转多少度。
	//
	// 组件空间的前方/上方取 +X / +Z：本项目的机体在导出时已把场景转过 90°，
	// 网格组件的相对旋转是单位阵，所以组件轴 = 角色轴（见文件头「坑 1」）。
	// 敌我共用同一份代码，敌人的 rig 也走同样的约定。
	auto FillLeg = [&](FMechLegRest& L, int32 IThigh, int32 IShin, int32 IFoot)
	{
		if (IThigh < 0 || IShin < 0 || IFoot < 0)
		{
			L.bValid = false;
			return;
		}
		// ⚠️ 必须用**参考姿势**量（RefAccumCompPos），不能用运行时数组：
		//    这三个点会直接当作 IK 目标（Target = Ankle + Fwd + Lift）。
		//    用运行时数组量出来的目标和脚骨的实际静止位置基准不同，
		//    IK 会"以为到了"（clamp == d）而脚实际差 20cm（第七十六轮实测）。
		L.Hip = RefAccumCompPos(Ref, IThigh);
		L.Knee = RefAccumCompPos(Ref, IShin);
		L.Ankle = RefAccumCompPos(Ref, IFoot);

		const FVector V1 = L.Knee - L.Hip;
		const FVector V2 = L.Ankle - L.Knee;
		L.Theta1Deg = FMath::RadiansToDegrees(FMath::Atan2(V1.X, -V1.Z));
		L.Theta2Deg = FMath::RadiansToDegrees(FMath::Atan2(V2.X, -V2.Z));
		L.DropCm = FMath::Max(L.Hip.Z - L.Ankle.Z, 1.f);
		L.bValid = (V1.SizeSquared() > 1.f && V2.SizeSquared() > 1.f);
		if (FParse::Param(FCommandLine::Get(), TEXT("DebugLegShape")))
		{
			// 脚掌朝向：踝→脚底的方向。脚骨原点在踝，尾巴指向脚尖，
			// 它相对竖直的偏角就是"脚掌俯仰"。静止时脚掌应大致水平（尾巴朝前）。
			const FVector V3 = L.Ankle - L.Knee;
			UE_LOG(LogTemp, Warning,
				TEXT("[LegShape] thigh=%d V1=(%.1f,%.1f,%.1f)|%.1f V2=(%.1f,%.1f,%.1f)|%.1f th1=%.1f th2=%.1f ank=%d valid=%d"),
				IThigh, V1.X, V1.Y, V1.Z, V1.Size(),
				V2.X, V2.Y, V2.Z, V2.Size(),
				L.Theta1Deg, L.Theta2Deg, IFoot, L.bValid ? 1 : 0);
		}
	};

	const int32 IThighR = FindBone(Ref, GThighRNames, UE_ARRAY_COUNT(GThighRNames));
	const int32 IShinR = FindBone(Ref, GShinRNames, UE_ARRAY_COUNT(GShinRNames));
	const int32 IFootR = FindBone(Ref, GFootRNames, UE_ARRAY_COUNT(GFootRNames));
	FillLeg(State.LegL, IThigh, IShin, IFoot);
	// ⚠️ 第九十三轮：上面这几条腿的 L1/L2 是**全局单值**，这里用每条腿自己的
	//    骨长覆盖掉。C_7/C_9 是四足机，后腿的骨架长度与前腿不同，
	//    用前腿的 L1/L2 去解后腿的 IK，目标永远差一截。
	State.LegL.Thigh = State.LegL.bValid
		? (State.LegL.Knee - State.LegL.Hip).Size() : 0.f;
	State.LegL.Shin = State.LegL.bValid
		? (State.LegL.Ankle - State.LegL.Knee).Size() : 0.f;
	State.LegR.Thigh = State.LegR.bValid
		? (State.LegR.Knee - State.LegR.Hip).Size() : 0.f;
	State.LegR.Shin = State.LegR.bValid
		? (State.LegR.Ankle - State.LegR.Knee).Size() : 0.f;
	FillLeg(State.LegR, IThighR, IShinR, IFootR);

	// 四足后腿（双足机没有这两条，FillLeg 会把它们标为无效）
	const int32 IThighBL = FindBone(Ref, GThighBLNames, UE_ARRAY_COUNT(GThighBLNames));
	const int32 IShinBL  = FindBone(Ref, GShinBLNames,  UE_ARRAY_COUNT(GShinBLNames));
	const int32 IFootBL  = FindBone(Ref, GFootBLNames,  UE_ARRAY_COUNT(GFootBLNames));
	const int32 IThighBR = FindBone(Ref, GThighBRNames, UE_ARRAY_COUNT(GThighBRNames));
	const int32 IShinBR  = FindBone(Ref, GShinBRNames,  UE_ARRAY_COUNT(GShinBRNames));
	const int32 IFootBR  = FindBone(Ref, GFootBRNames,  UE_ARRAY_COUNT(GFootBRNames));
	FillLeg(State.LegBL, IThighBL, IShinBL, IFootBL);
	FillLeg(State.LegBR, IThighBR, IShinBR, IFootBR);
	State.LegBL.Thigh = State.LegBL.bValid
		? (State.LegBL.Knee - State.LegBL.Hip).Size() : 0.f;
	State.LegBL.Shin = State.LegBL.bValid
		? (State.LegBL.Ankle - State.LegBL.Knee).Size() : 0.f;
	State.LegBR.Thigh = State.LegBR.bValid
		? (State.LegBR.Knee - State.LegBR.Hip).Size() : 0.f;
	State.LegBR.Shin = State.LegBR.bValid
		? (State.LegBR.Ankle - State.LegBR.Knee).Size() : 0.f;

	// ── 骨骼链诊断（第九十三轮）──
	// 一眼看清：哪几根腿骨被认出来、父骨是谁、以及静止时髋到踝的竖直落差。
	// 巨像 C_9 实测脚离髋 186cm 而骨长只有 176cm —— 说明"用的髋"不是
	// 该腿腿骨的实际父节点，或者取到了别的骨骼。
	{
		auto DumpChain = [&](const TCHAR* Tag, int32 IThigh, int32 IShin, int32 IFoot)
		{
			if (IThigh < 0) { return; }
			const int32 P = Ref.GetParentIndex(IThigh);
			UE_LOG(LogTemp, Warning,
				TEXT("[Chain] %s thigh=%s(parent=%s) shin=%s foot=%s"),
				Tag, *Ref.GetBoneName(IThigh).ToString(),
				P >= 0 ? *Ref.GetBoneName(P).ToString() : TEXT("none"),
				IShin >= 0 ? *Ref.GetBoneName(IShin).ToString() : TEXT("-"),
				IFoot >= 0 ? *Ref.GetBoneName(IFoot).ToString() : TEXT("-"));
		};
		DumpChain(TEXT("L"), IThigh, IShin, IFoot);
		DumpChain(TEXT("R"), IThighR, IShinR, IFootR);
		DumpChain(TEXT("BL"), IThighBL, IShinBL, IFootBL);
		DumpChain(TEXT("BR"), IThighBR, IShinBR, IFootBR);
		const FMechLegRest* Legs[4] = { &State.LegL, &State.LegR, &State.LegBL, &State.LegBR };
		for (int32 k = 0; k < 4; ++k)
		{
			const FMechLegRest& L = *Legs[k];
			if (!L.bValid) { continue; }
			UE_LOG(LogTemp, Warning,
				TEXT("[ChainGeo] leg%d hipZ=%.1f ankZ=%.1f drop=%.1f boneL1L2=%.1f"),
				k, L.Hip.Z, L.Ankle.Z, L.Hip.Z - L.Ankle.Z, L.Thigh + L.Shin);
		}
	}

	// ── 骨骼局部单位换算 ──
	// 用"小腿局部位移长度 / 小腿实际厘米长度"直接量出来，不猜导入缩放。
	State.BoneUnitPerCm = 1.f;
	if (const FTransform* ShinLocal =
		State.BaseTransforms.Find(FName(TEXT("shin_L"))))
	{
		const float LocalLen = ShinLocal->GetLocation().Size();
		if (LocalLen > 0.001f && State.ShinLenCm > 1.f)
		{
			State.BoneUnitPerCm = LocalLen / State.ShinLenCm;
		UE_LOG(LogTemp, Warning,
			TEXT("[Unit] shinLocalLen=%.3f shinCm=%.1f unitPerCm=%.4f"),
			LocalLen, State.ShinLenCm, State.BoneUnitPerCm);
		}
	}
}

void MechProceduralAnim::HideBonesByPrefix(UPoseableMeshComponent* Mesh,
	const FString& Prefix)
{
	if (!Mesh || Prefix.IsEmpty())
	{
		return;
	}
	USkeletalMesh* SkinnedAsset = Cast<USkeletalMesh>(Mesh->GetSkinnedAsset());
	if (!SkinnedAsset)
	{
		return;
	}

	const FReferenceSkeleton& Ref = SkinnedAsset->GetRefSkeleton();
	for (int32 i = 0; i < Ref.GetNum(); ++i)
	{
		const FName BoneName = Ref.GetBoneName(i);
		if (BoneName.ToString().StartsWith(Prefix, ESearchCase::IgnoreCase))
		{
			Mesh->HideBoneByName(BoneName, PBO_None);
		}
	}
}

void MechProceduralAnim::TriggerRecoil(FMechAnimState& State, float Strength)
{
	State.Recoil = FMath::Clamp(State.Recoil + Strength, 0.f, 1.f);
}

bool MechProceduralAnim::GetBoneWorldTransform(UPoseableMeshComponent* Mesh,
	const FName BoneName, FTransform& Out)
{
	if (!Mesh || BoneName.IsNone())
	{
		return false;
	}
	USkeletalMesh* SkinnedAsset = Cast<USkeletalMesh>(Mesh->GetSkinnedAsset());
	if (!SkinnedAsset)
	{
		return false;
	}
	const FReferenceSkeleton& Ref = SkinnedAsset->GetRefSkeleton();
	if (Ref.FindBoneIndex(BoneName) == INDEX_NONE)
	{
		return false;
	}
	// 注意：这里读的是引擎缓存的组件空间姿势，可能落后一帧 ——
	// 对"枪口跟随手臂"这种用途完全够用（1 帧 ≈ 16ms，肉眼无感）。
	Out = Mesh->GetBoneTransformByName(BoneName, EBoneSpaces::WorldSpace);
	return true;
}

// ─────────────────────────────────────────────
// 每帧姿势
// ─────────────────────────────────────────────

void MechProceduralAnim::Update(UPoseableMeshComponent* Mesh, FMechAnimState& S,
	const FVector& Velocity, float YawDegrees, float MaxSpeed, float Dt)
{
	if (!Mesh || Dt <= KINDA_SMALL_NUMBER)
	{
		return;
	}

	// 基准姿势必须先缓存好；第一帧可能拿不到（姿势数组还没初始化），下一帧再来
	if (!S.bBaseCached)
	{
		CacheBasePose(Mesh, S);
		if (!S.bBaseCached)
		{
			return;
		}
	}

	USkeletalMesh* SkinnedAsset = Cast<USkeletalMesh>(Mesh->GetSkinnedAsset());
	if (!SkinnedAsset)
	{
		return;
	}
	const FReferenceSkeleton& Ref = SkinnedAsset->GetRefSkeleton();
	if (Mesh->BoneSpaceTransforms.Num() != Ref.GetNum())
	{
		return;
	}

	S.Time += Dt;

	const float Speed = Velocity.Size2D();

	// ── 实际位移速度（第六十八轮）──
	// 问题：敌人 AI 走位时会快速改变方向（追击/侧移/拉开），GetVelocity() 的瞬时速度
	// 一直很高，但**净位移**接近零。步态按瞬时速度满速摆腿，机体却没走多远，
	// 观感就是"腿在原地划"。
	// 修法：额外算一个"实际位移速度"= 组件位置的真实位移速率，并用它给步态速度封顶。
	// 只封顶不抬升 —— 机体确实在快速移动时不受影响，只在"划腿"时把节奏压下来。
	{
		const FVector CompNow = Mesh->GetComponentTransform().GetLocation();
		if (S.bCompPrevValid && Dt > 1e-4f)
		{
			const float Actual = FVector::Dist2D(CompNow, S.CompPrev) / Dt;
			S.ActualSpeed = (S.ActualSpeed < 0.f)
				? Actual : FMath::FInterpTo(S.ActualSpeed, Actual, Dt, 10.f);
		}
		S.CompPrev = CompNow;
		S.bCompPrevValid = true;
	}

	const float SpeedRatio = (MaxSpeed > 1.f)
		? FMath::Clamp(Speed / MaxSpeed, 0.f, 1.f) : 0.f;
	// ⚠️ 用真正的"是否在动"判据：速度 > 0.5cm/s 就算在走。
	//    旧判据 SpeedRatio > 0.06（≈13cm/s）太钝：敌人被墙挡住/转向时速度在
	//    0~10cm/s 之间抖动，bMoving 反复翻转 → Stride 在 0 与正常值之间跳变
	//    （MoveBlend 却已 >0），脚在"静止位"与"步态位"之间瞬移 20cm+
	//    （实测 C_7 速度=5 时脚跳 21.6cm、组件位移 0）。
	const bool bMoving = Speed > 0.5f;

	// ① 先把所有骨骼复位到基准姿势。
	// 不做这一步的话，每帧都会在上一次的旋转上再叠一次，
	// 几十帧后骨骼会扭成麻花。
	for (int32 i = 0; i < Mesh->BoneSpaceTransforms.Num(); ++i)
	{
		if (const FTransform* Base = S.BaseTransforms.Find(Ref.GetBoneName(i)))
		{
			Mesh->BoneSpaceTransforms[i] = *Base;
		}
	}

	// 步态速度不做低通：实测低通让 Stride 与实际前进量脱节，反而加剧滑步
	// （0-30 段 C_5 从 21 推到 132）。已回退。

	// ② 组件空间的角色轴。
	// ⚠️ 见文件头「坑 1」：绝不能写死"组件 X = 前后 / 组件 Y = 左右"。
	// 把**世界空间**的角色前后/左右/上下轴变换进组件空间，无论网格组件
	// 带什么相对旋转，摆腿永远绕"角色的左右轴"。
	const FQuat CompQ = Mesh->GetComponentTransform().GetRotation();
	const FQuat ActorQ = FRotator(0.f, YawDegrees, 0.f).Quaternion();
	const FQuat WorldToComp = CompQ.Inverse() * ActorQ;
	const FVector AxisRight = WorldToComp.RotateVector(FVector(0.f, 1.f, 0.f));
	const FVector AxisFwd   = WorldToComp.RotateVector(FVector(1.f, 0.f, 0.f));
	const FVector AxisUp    = WorldToComp.RotateVector(FVector(0.f, 0.f, 1.f));

	// ②' 姿势上下文：缓存每根骨骼"当前"的组件空间旋转，供 RotateBoneAxis
	//     换算旋转轴。初值是静止姿势的组件空间旋转。
	FPoseCtx Ctx;
	Ctx.Mesh = Mesh;
	Ctx.Ref = &Ref;
	Ctx.UnitPerCm = S.BoneUnitPerCm;
	Ctx.CurRot.SetNumUninitialized(Ref.GetNum());
	for (int32 i = 0; i < Ref.GetNum(); ++i)
	{
		const FMechBoneRest* R = S.Rest.Find(Ref.GetBoneName(i));
		Ctx.CurRot[i] = R ? R->CompRot : FQuat::Identity;
	}

	// ③ 骨骼索引
	const int32 IPelvis  = FindBone(Ref, GPelvisNames, UE_ARRAY_COUNT(GPelvisNames));
	const int32 ITorso   = FindBone(Ref, GTorsoNames,  UE_ARRAY_COUNT(GTorsoNames));
	const int32 IHead    = FindBone(Ref, GHeadNames,   UE_ARRAY_COUNT(GHeadNames));
	const int32 IThighL  = FindBone(Ref, GThighLNames, UE_ARRAY_COUNT(GThighLNames));
	const int32 IThighR  = FindBone(Ref, GThighRNames, UE_ARRAY_COUNT(GThighRNames));
	const int32 IShinL   = FindBone(Ref, GShinLNames,  UE_ARRAY_COUNT(GShinLNames));
	const int32 IShinR   = FindBone(Ref, GShinRNames,  UE_ARRAY_COUNT(GShinRNames));
	const int32 IFootL   = FindBone(Ref, GFootLNames,  UE_ARRAY_COUNT(GFootLNames));
	const int32 IFootR   = FindBone(Ref, GFootRNames,  UE_ARRAY_COUNT(GFootRNames));
	const int32 IThighBL = FindBone(Ref, GThighBLNames, UE_ARRAY_COUNT(GThighBLNames));
	const int32 IThighBR = FindBone(Ref, GThighBRNames, UE_ARRAY_COUNT(GThighBRNames));
	const int32 IShinBL  = FindBone(Ref, GShinBLNames,  UE_ARRAY_COUNT(GShinBLNames));
	const int32 IShinBR  = FindBone(Ref, GShinBRNames,  UE_ARRAY_COUNT(GShinBRNames));
	const int32 IFootBL  = FindBone(Ref, GFootBLNames,  UE_ARRAY_COUNT(GFootBLNames));
	const int32 IFootBR  = FindBone(Ref, GFootBRNames,  UE_ARRAY_COUNT(GFootBRNames));
	const int32 IClavL   = FindBone(Ref, GClavLNames,  UE_ARRAY_COUNT(GClavLNames));
	const int32 IClavR   = FindBone(Ref, GClavRNames,  UE_ARRAY_COUNT(GClavRNames));
	const int32 IArmL    = FindBone(Ref, GUpperArmLNames, UE_ARRAY_COUNT(GUpperArmLNames));
	const int32 IArmR    = FindBone(Ref, GUpperArmRNames, UE_ARRAY_COUNT(GUpperArmRNames));
	const int32 IForeL   = FindBone(Ref, GForearmLNames, UE_ARRAY_COUNT(GForearmLNames));
	const int32 IForeR   = FindBone(Ref, GForearmRNames, UE_ARRAY_COUNT(GForearmRNames));

	auto SwingBone = [&](int32 Index, float Degrees)
	{
		RotateBoneAxis(Ctx, Index, AxisRight, Degrees);
	};

	// 一次性诊断：把"实际用的组件空间轴"和"关键骨骼的静止位置"打出来。
	// 步态数值不对时，第一件要确认的事就是轴到底是不是 (0,1,0) ——
	// 这一步没确认，后面所有推理都建立在假设上。
	if (FParse::Param(FCommandLine::Get(), TEXT("AutoWalk")))
	{
		static bool bLoggedAxes = false;
		if (!bLoggedAxes)
		{
			bLoggedAxes = true;
			const FRotator CompR = Mesh->GetComponentTransform().GetRotation().Rotator();
			UE_LOG(LogTemp, Warning,
				TEXT("[轴向] 组件世界旋转(P=%.1f Y=%.1f R=%.1f) 角色yaw=%.1f | "
					 "组件空间轴 右=(%.2f,%.2f,%.2f) 前=(%.2f,%.2f,%.2f) 上=(%.2f,%.2f,%.2f)"),
				CompR.Pitch, CompR.Yaw, CompR.Roll, YawDegrees,
				AxisRight.X, AxisRight.Y, AxisRight.Z,
				AxisFwd.X, AxisFwd.Y, AxisFwd.Z,
				AxisUp.X, AxisUp.Y, AxisUp.Z);
			auto RestLoc = [&](int32 Idx) -> FString
			{
				if (Idx < 0) { return TEXT("-"); }
				const FMechBoneRest* R2 = S.Rest.Find(Ref.GetBoneName(Idx));
				if (!R2) { return TEXT("无"); }
				return R2->Local.GetLocation().ToCompactString();
			};
			UE_LOG(LogTemp, Warning,
				TEXT("[轴向] 静止局部位移 髋L=%s 膝L=%s 踝L=%s | 腿长=%.1f 大腿=%.1f 小腿=%.1f"),
				*RestLoc(IThighL), *RestLoc(IShinL), *RestLoc(IFootL),
				S.LegLengthCm, S.ThighLenCm, S.ShinLenCm);

			// ── 骨架的真实几何（世界坐标，自己累积，不信引擎缓存）──
			// 这三个点必须满足：髋最高、膝居中、踝最低，且三点的 X/Y 基本对齐
			// （只有小腿因为 Blender 里给了 8% 的 Y 偏移而略有前后差）。
			// 若三点 Z 不是递减的，说明骨架本身建错了，跟动画无关。
			auto WPos = [&](int32 Idx) -> FString
			{
				if (Idx < 0) { return TEXT("-"); }
				return LocalAccumWorldPos(Mesh, Ref, Idx).ToCompactString();
			};
			UE_LOG(LogTemp, Warning,
				TEXT("[轴向] 世界坐标 骨盆=%s 髋L=%s 膝L=%s 踝L=%s"),
				*WPos(IPelvis), *WPos(IThighL), *WPos(IShinL), *WPos(IFootL));

			// ── 每根腿骨相对父骨的朝向（欧拉）──
			// 关键判据：thigh/shin/foot 的 **Roll** 若接近 ±90，
			// 说明骨骼自身轴向与父骨差 90°，则"绕组件 Y 轴转"的结果
			// 会与直觉相反 —— 这正是"迈腿变成横着甩"的根源。
			auto LocalRot = [&](int32 Idx) -> FString
			{
				if (Idx < 0) { return TEXT("-"); }
				const FMechBoneRest* R2 = S.Rest.Find(Ref.GetBoneName(Idx));
				if (!R2) { return TEXT("无"); }
				const FRotator E = R2->Local.GetRotation().Rotator();
				return FString::Printf(TEXT("P=%.1f Y=%.1f R=%.1f"),
					E.Pitch, E.Yaw, E.Roll);
			};
			UE_LOG(LogTemp, Warning,
				TEXT("[轴向] 局部位姿 髋L=%s 膝L=%s 踝L=%s 肩L=%s 上臂L=%s 前臂L=%s"),
				*LocalRot(IThighL), *LocalRot(IShinL), *LocalRot(IFootL),
				*LocalRot(IClavL), *LocalRot(IArmL), *LocalRot(IForeL));

			// ── 父链名字（确认骨架层级与预期一致）──
			auto Chain = [&](int32 Idx) -> FString
			{
				FString Out;
				int32 Guard = 0;
				while (Idx >= 0 && Guard++ < 12)
				{
					Out += Ref.GetBoneName(Idx).ToString();
					Idx = Ref.GetParentIndex(Idx);
					if (Idx >= 0) { Out += TEXT("<"); }
				}
				return Out;
			};
			UE_LOG(LogTemp, Warning, TEXT("[轴向] 父链 髋L=%s | 上臂L=%s"),
				*Chain(IThighL), *Chain(IArmL));
		}
	}

	// ④ 步态相位（节奏）
	//
	// 本帧偏航率，仅用于躯干侧倾的观感补偿（不再用于脚部补偿）。
	// ⚠️ 夹得紧（±90°/s）：敌人原地转向瞄准时 YawDegrees 单帧跳变，
	//    除以 Dt 会打到 ±360 饱和，饱和值直接驱动侧倾会让躯干抽搐。
	const float GaitYawRate = FMath::Clamp(
		FMath::FindDeltaAngleDegrees(S.PrevYaw, YawDegrees) / FMath::Max(Dt, 0.001f),
		-90.f, 90.f);
	// 脚静止时距中线的侧向距离（cm）：用左脚静止踝位的侧向量取绝对值。
	const float RestLatCm = S.LegL.bValid
		? FMath::Abs(S.LegL.Ankle.Y)
		: 12.f;
	//
	// v5 改动：不再用"正弦摆髋 + 启发式屈膝"，改成**两骨 IK 反解**。
	// 原因：正弦步态在数学上永远无法保证"支撑脚在世界里不动" ——
	// 髋角和膝角各自按经验曲线走，脚的实际落点由两者合成，
	// 于是脚在地面上以每秒几十厘米的速度滑行。远看就是"踩在冰上"，
	// 这是上一版动画最大的观感问题。
	//
	// 新做法：先定**脚的目标轨迹**（支撑期相对身体匀速后移、摆动期抬脚前送），
	// 再用余弦定理反解髋/膝角度。支撑脚的目标点在世界里是静止的，
	// 所以只要反解成立，脚就不可能滑。
	const float ThighLen = FMath::Max(S.ThighLenCm, 1.f);
	const float ShinLen = FMath::Max(S.ShinLenCm, 1.f);
	const float L1 = ThighLen;
	const float L2 = ShinLen;
	// ⚠️ 第九十三轮实验：改用"每条腿自己的骨长"后 C_5 从 6 恶化到 24~30，
	//    C_9 不变。说明当前全局骨长与资产的实际膝/踝位置是配套的，
	//    按"髋到膝的三维距离"重算反而引入偏差（膝盖不是骨链端点）。
	//    已回退，保留全局 L1/L2。勿再改。
	const bool bUsePerLegLen = FParse::Param(FCommandLine::Get(), TEXT("PerLegLen"));
	const float LegLen = (S.LegLengthCm > 1.f) ? S.LegLengthCm : (L1 + L2);
	// 支撑期占比：取 0.50 —— 两条腿的相位差正好 0.5，Duty=0.5 时
	// 恰好"一条支撑、一条摆动"，没有两条腿同时压地的重叠区。
	// ⚠️ 旧的 0.62 有 0.12 的重叠：重叠期两腿都要求贴地，目标不一致时互相拉扯，
	//    表现为换腿瞬间脚滑尖峰（实测 C_5 帧间 324 → 94 的剧烈波动）。
	// 第六十六轮：双足机试过给重叠缓冲（Duty 0.56 / 0.62），实测几乎无改善
	// （C_5 1.53→1.50→1.45，C_8 1.61→1.65→1.63，在噪声内），已回退为 0.50。
	const float Duty = 0.50f;
	// 步幅上限按腿长的 0.62：接近人类/双足机械的舒适步幅比例。
	// ⚠️ 试过改成"按 IK 水平可达距离限制"（sqrt(腿长²-落差²)），实测反而更差：
	//    髋踝落差约等于腿长时，水平可达只剩 28cm，步幅被压到 54cm，
	//    脚移动距离不足以覆盖位移，滑步从 17 涨到 185cm/s。已回退，保留 0.62。
	const float StrideMax = LegLen * 0.62f;
	// ⚠️ 试过给四足单独收紧到 0.42，反而让裁剪从 32 次增到 48 次（r202）：
	//    运输机速度只有 48cm/s，步幅本来就远小于上限，收紧步幅触不到问题。
	//    它的超伸来自"静止时髋踝距离已贴近腿长"的几何本身，与步幅无关。已回退。

	// 步频：低速 2.4rad/s，全速时最高 20rad/s（≈3.2 步/秒）。
	// 拉高上限是为了让"高速"由步频承担而不是靠拉大步幅 —— 步幅受限后，
	// 多余的速度只能靠更高步频消化，否则就会变成滑步。
	//
	// ⚠️ 第六十八轮：步态用**实际位移速度**，而不是瞬时速度。
	//    敌人 AI 走位时瞬时速度高但净位移小（追击/侧移/原地转向），
	//    按瞬时速度摆腿就是"腿在原地划"。取 min(瞬时, 实际) 作为步态速度：
	//    真在快速直线移动时不受影响；只在"划腿"时把节奏压下来。
	// ⚠️ 第八十七轮：试过用"速度在机体前向上的分量"来定步幅，想让转向时
	//    少滑一点 —— 实测失败：转弯时前向分量变小，步幅跟着缩，
	//    脚反而被机体拖着走（C_8 支撑滑动 119~182cm/s）。
	//    恢复用速度模长，转向的侧向滑留待真正的 yaw-aware 解法。
	const float SpeedForGait = (S.ActualSpeed >= 0.f &&
		!FParse::Param(FCommandLine::Get(), TEXT("NoActualGate")))
		? FMath::Min(Speed, S.ActualSpeed * 1.25f + 8.f)
		: Speed;
	// ⚠️ 第六十五轮：步频上限 12 → 20。
	//    实测"残差随速度单调增大"：C_8（219cm/s，Omega 顶到 12）残差 2.50cm，
	//    C_9（124cm/s）只有 0.38cm。说明高速时机体前进快过脚的摆动节奏，
	//    仅靠 12rad/s 消化不掉多余速度 → 脚被拖着滑。
	//    逐步试 16 / 18 / 20 / 24，残差单调下降并在 20 附近饱和（24 几乎无增益）。
	//    C_8: 2.50 → 1.82cm（-27%），C_5: 2.27 → 1.76cm，C_7: 0.99 → 0.70cm。
	// ⚠️ 第八十五轮：步频上限 20 → 15。
	//    20 rad/s 时玩家 140cm/s 的步幅只有 22cm（腿长 104），
	//    而抬脚还有 16~22cm —— 迈得比抬得少，走起来像高抬腿原地踏步。
	//    11 rad/s 试验：步幅 40cm、姿态自然，但 netSlip 从 24/30/8/10 涨到
	//    52/79/82/38（三次中位），脚在支撑期明显打滑 —— 说明当前姿态链
	//    在更长支撑上无法把脚钉住，不能一步到位。
	//    取 15 作为折中：步幅约 29cm，抬脚随步幅（下面单独改），
	//    先把"高抬腿"这个最刺眼的问题解决，滑步留待下一步深挖。
	//
	// ⚠️ 第九十八轮：步频上限必须**按腿长缩放**。
	//    固定 15 对玩家（腿长 104）刚好，但对巨像 C_9（腿长 176.7）意味着
	//    它的步幅/腿长只有 12.8%，而玩家是 28% —— 长腿机被迫走"小碎步"，
	//    支撑期脚的后退速度只有机体速度的一半，脚一定在地上拖。
	//    按 sqrt(腿长) 缩放（步态频率 ∝ 1/√L，是摆的物理规律）：
	//    玩家 √104=10.2 → 系数 1.00；C_9 √166=12.9 → 系数 0.79。
	//    ⚠️ 方向不能反：长腿走得更**慢**（omega 更小、步幅更大），
	//    写成 sqrt(L)/sqrt(104) 会让 C_9 越走越快，实测步幅反而缩到 19.7。
	const float LegScale = FMath::Clamp(
		FMath::Sqrt(104.f) / FMath::Sqrt(FMath::Max(LegLen, 1.f)), 0.6f, 1.15f);
	float Omega = (2.4f + 12.6f * SpeedRatio) * LegScale;
	// ⚠️ 第八十六轮：步态速度必须**时间平滑**。
	//    敌人 AI 的速度在一秒内会从 194 掉到 38（加速/减速/转向），
	//    而 Stride 每帧按当前速度重算 —— 速度一抖，支撑脚的目标点就整段跳，
	//    表现为"机体几乎没动、脚却在地上划 40cm/s"（实测 C_8 速度=38 时左脚滑 40）。
	//    用指数平滑把步幅的变化摊到 ~0.25s，脚不再被速度抖动拽着走。
	if (S.GaitSpeedSmoothed < 0.f)
	{
		S.GaitSpeedSmoothed = SpeedForGait;
	}
	else
	{
		S.GaitSpeedSmoothed = FMath::FInterpTo(
			S.GaitSpeedSmoothed, SpeedForGait, Dt, 6.f);
	}
	const float GaitSpeed = S.GaitSpeedSmoothed;

	// ── 支撑期步幅锁定（第一百轮）──
	// 实测问题：敌人 AI 有 10% 以上的时间**完全静止**（v_p10 = 0），
	// 高速行走中突然停下时，平滑后的 GaitSpeed 还留在 145，
	// 脚仍按原来的速度后退 —— 实测瞬时滑移 246cm/s。
	// 反过来如果不平滑，速度抖动又会让目标点乱跳（第八十六轮的老问题）。
	//
	// 正确做法是两头都要：**支撑期一旦落地，把当时的步幅锁定**，
	// 这一整段支撑期内脚匀速后退、世界坐标严格不动；
	// 摆动期再按最新速度重新计算，下一只脚落地时用新的值。
	// 这样"速度变化"只在换脚那一瞬间发生，不影响已落地的脚。
	float Stride = 0.f;
	if (bMoving)
	{
		const float T = 2.f * PI / FMath::Max(Omega, 0.1f);
		Stride = GaitSpeed * Duty * T;
		if (Stride > StrideMax)
		{
			// 步幅超出腿能跨的范围 → 加快步频（而不是让脚滑）
			// ⚠️ 必须用 SpeedForGait（已按实际位移封顶），用瞬时 Speed 会让
			//    步态速度在地形/走位时回退到"满速"，原地划腿又回来了。
			Stride = StrideMax;
			Omega = FMath::Max(GaitSpeed, 1.f) * Duty * 2.f * PI / Stride;
		}
	}
	// ⚠️ 第一百轮实验（已回退）：改成“支撑期锁定步幅”后，
	//    C_7 脚速从 14 升到 58.5（变差）。原因：锁定后摆动期用新速度、
	//    支撑期用旧速度，两者在换脚瞬间不连续。保持全局平滑。
	auto StrideForLeg = [&](FMechLegRest& Rest, bool bStance) -> float
	{
		(void)Rest; (void)bStance;
		return Stride;
	};
	S.GaitPhase += Dt * (bMoving ? Omega : 0.9f);
	// 步态调试（-DebugGait）：速度、比值、步频、步幅、腿长
	// ⚠️ 用独立节流字段 PrevPhaseLog：若也用 S.PrevGaitLog，会与 ⑥' 的
	//    [步态]/[脚滑] 日志（0.15s）互相覆盖，令后者输出时机紊乱、甚至被吞。
	if (FParse::Param(FCommandLine::Get(), TEXT("DebugGait")))
	{
		if (S.Time - S.PrevPhaseLog > 0.25f)
		{
			S.PrevPhaseLog = S.Time;
			const float RatioDbg = (S.ActualSpeed >= 0.f && MaxSpeed > 1.f)
				? FMath::Clamp(S.ActualSpeed / MaxSpeed, 0.f, 1.f) : SpeedRatio;
			UE_LOG(LogTemp, Log,
				TEXT("[Gait] owner=%s speed=%.1f ratio=%.2f omega=%.2f stride=%.1f stridemax=%.1f leglen=%.1f rblend=%.3f actual=%.1f maxspd=%.1f"),
				Mesh->GetOwner() ? *Mesh->GetOwner()->GetName() : TEXT("?"),
				Speed, SpeedRatio, Omega, Stride, StrideMax, LegLen,
				RatioDbg, S.ActualSpeed, MaxSpeed);
		}
	}
	if (S.GaitPhase > 2.f * PI)
	{
		S.GaitPhase -= 2.f * PI;
	}
	const float Phase = S.GaitPhase;
	// 摆幅（度）：仅用于手臂反相摆动与诊断日志
	const float Swing = FMath::RadiansToDegrees(
		FMath::Asin(FMath::Clamp(Stride * 0.5f / FMath::Max(LegLen, 1.f),
			0.f, 0.62f)));

	// ⑤ 脚的目标轨迹 + 两骨 IK
	//
	// 相位定义：LegPhase ∈ [0,1)，0 = 刚触地（脚在最前），Duty = 离地（脚在最后）。
	//   支撑期：脚相对身体从 +S/2 匀速移到 −S/2，高度贴地
	//   摆动期：脚从 −S/2 抬到 +S/2，高度走一条正弦拱
	//
	// 符号：正角度 = 肢体下端向**后**摆（UE 绕 +Y 右手法则）。
	struct FLegPose
	{
		float Hip = 0.f;
		float Knee = 0.f;
		float Ankle = 0.f;
		float Fwd = 0.f;      // 脚相对髋的前后偏移（正 = 前）
		float Lift = 0.f;     // 脚离地高度
		float FwdLat = 0.f;   // 脚相对髋的侧向偏移（正 = 右），用于抵消转弯时的切向滑动
		/** 第九十五轮：沿实际移动方向的侧向偏移（相对右轴分解的那一半） */
		float OffLat = 0.f;
		/** 髋部偏航（第八十八轮）：把整条腿绕竖轴转，解决侧向目标够不到的问题 */
		float HipYaw = 0.f;
		bool bStance = true;
		float DbgU = 0.f;     // 诊断：支撑/摆动期进度
	};

	// 速度很低时把步态整体收掉，避免"原地踏步"
	// 双腿全断：没有腿可走，步态整体停掉（否则残肢还在空中摆）
	//
	// ⚠️ 第七十二轮：MoveBlend 必须用**实际位移速度**的比值，不能用瞬时 SpeedRatio。
	//    敌人原地转向/来回走位时瞬时速度很高（MoveBlend→1，满幅摆腿），
	//    但机体净位移接近零 —— 观感就是"腿在原地划"。
	//    第六十八轮只给 Omega/Stride 封了顶，摆幅与抬脚高度仍按瞬时速度，
	//    这里统一改到实际位移口径。
	const float RatioForBlend = (!FParse::Param(FCommandLine::Get(), TEXT("NoActualBlend"))
		&& S.ActualSpeed >= 0.f && MaxSpeed > 1.f)
		? FMath::Clamp(S.ActualSpeed / MaxSpeed, 0.f, 1.f)
		: SpeedRatio;
	const float MoveBlend = (S.LegsAlive <= 0) ? 0.f
		: SmoothStep(FMath::Clamp((RatioForBlend - 0.02f) / 0.16f, 0.f, 1.f));

	// ⚠️ 第九十五轮：支撑脚的后退方向必须等于**机体实际移动方向在组件空间里的投影**，
	//    不能假设"机体永远朝自己的前方走"。
	//    实测 C_8：机体朝 (-X,-Y) 平移，而脚在支撑期朝 +X 后移 —— 方向相反，
	//    脚与地面的相对速度是两者之和，所以 IK 跟踪误差只有 0.01cm，
	//    脚仍在世界坐标里以约 200cm/s 滑动。
	//    敌人会侧移/倒退/绕行，这个方向必须每帧从速度向量求。
	const FVector CompQ_inv = Mesh->GetComponentTransform().GetRotation().Inverse()
		.RotateVector(Velocity.GetSafeNormal2D());
	FVector MoveDirLocal = FVector(1.f, 0.f, 0.f);
	if (!CompQ_inv.IsNearlyZero(0.05f))
	{
		// ⚠️ 第一百轮（关键 bug）：这里原本用 FMath::VInterpNormalRotationTo，
		//    实测它**没有把向量转到目标方向** ——
		//    速度 (-64.8, 130.3)（方向 116°），算出的 MoveDirLocal 却是 (1,0)（0°）。
		//    于是 C_7 侧着走时，脚仍沿机体前向后退，与位移方向差 100°，
		//    世界滑移 60cm/s。改为自己按角度插值（先把初值兜底成目标）。
		const FVector DirTarget = CompQ_inv.GetSafeNormal2D();
		// 恢复平滑（第九十五轮的原意）：不平滑会让目标点在速度方向抖动时整段跳。
		if (S.MoveDirSmoothed.IsNearlyZero(0.05f))
		{
			S.MoveDirSmoothed = DirTarget;
		}
		else
		{
			const float CurAng = FMath::Atan2(S.MoveDirSmoothed.Y, S.MoveDirSmoothed.X);
			const float TgtAng = FMath::Atan2(DirTarget.Y, DirTarget.X);
			const float MaxStep = FMath::DegreesToRadians(400.f * Dt);
			const float Delta = FMath::Clamp(
				FMath::FindDeltaAngleRadians(CurAng, TgtAng), -MaxStep, MaxStep);
			const float NewAng = CurAng + Delta;
			S.MoveDirSmoothed = FVector(FMath::Cos(NewAng), FMath::Sin(NewAng),
				S.MoveDirSmoothed.Z);
		}
		MoveDirLocal = S.MoveDirSmoothed.GetSafeNormal2D();
	}
	const FVector StrideDir = MoveDirLocal * MoveBlend
		+ AxisFwd * (1.f - MoveBlend);

	auto LegTarget = [&](float LegPhase, bool bLeft, float LegStride) -> FLegPose
	{
		FLegPose P;
		const float LP = LegPhase - FMath::FloorToFloat(LegPhase);
		P.bStance = LP < Duty;
		const float U = P.bStance
			? (LP / Duty)
			: ((LP - Duty) / FMath::Max(1.f - Duty, 0.001f));
		P.DbgU = U;

		// 脚的"前后"方向改为沿实际移动方向（移动很慢时退化为机体前向）
		const FVector FwdAxis = (StrideDir | AxisFwd) > 0.85f ? AxisFwd : StrideDir;
		const float Half = LegStride * 0.5f * MoveBlend;
		// 步幅向量按"沿机体前向 / 侧向"分解，两者都按相位走同样的曲线
		const float LatHalf = FVector::DotProduct(StrideDir, AxisRight) * Half;
		const float FwdHalf = FVector::DotProduct(StrideDir, AxisFwd) * Half;
		// ── 转弯补偿：已移除（第六十四轮）──
		// 原实现按 `FwdLat = -ω×Lat×T×(U-0.5)` 抵消转弯切向滑动。
		// 实测它是**显著的滑步来源**，而不是修复：
		//   · `GaitYawRate = FindDeltaAngleDegrees(...)/Dt` 在敌人原地转向瞄准时
		//     单帧跳变，被夹到 ±360°/s 饱和，再乘 30~90cm 的力臂，`FwdLat` 一帧跳 25~30cm；
		//   · 诊断显示 `yawRate≈0`、`FwdLat=0` 的那一帧，脚仍侧向跳 20~31cm
		//     （饱和帧与归零帧交替），多个实体同帧同向跳，确认是这一项造成的。
		// 让侧向分量尽量小——只有机体真的朝自己身侧走时才需要它
		if (P.bStance)
		{
			// 线性后移 —— 与身体前进严格抵消，这是"不滑"的关键
			P.Fwd = FwdHalf - 2.f * FwdHalf * U;
			P.OffLat = LatHalf - 2.f * LatHalf * U;
			P.Lift = 0.f;
		}
		else
		{
			// 前送：用 smoothstep 让起落速度为零，脚不会"弹射"
			const float E = U * U * (3.f - 2.f * U);
			P.Fwd = -FwdHalf + 2.f * FwdHalf * E;
			P.OffLat = -LatHalf + 2.f * LatHalf * E;
			// ⚠️ 第八十五轮：抬脚高度改为**与步幅成比例**，不再与速度挂钩。
			//    旧式 (6 + 16*ratio) 在低速时也有 6cm、满速 22cm，
			//    而步幅可能只有 20cm —— 抬得比迈得还高，只能靠大幅屈膝把脚提起来，
			//    看起来就是"高抬腿原地踏步"（实测玩家 hip=46° knee=-69° lift=16 但 fwd 只有 7cm）。
			//    真实步态里抬脚高度约为步幅的 25~35%。
			//    Half 已经是"按 MoveBlend 缩放的半幅"，所以 2*Half 就是当前有效步幅。
			const float EffStride = Half * 2.f;
			const float H = FMath::Clamp(EffStride * 0.30f, 3.f, 16.f);
			P.Lift = H * FMath::Sin(PI * U);
		}

		// 脚掌俯仰：触地瞬间脚尖微抬（脚跟先着地），离地时脚尖下压（蹬地）
		float FootPitch = 0.f;
		if (P.bStance)
		{
			FootPitch = FMath::Lerp(-7.f, 14.f, FMath::Pow(U, 2.2f));
		}
		else
		{
			FootPitch = FMath::Lerp(16.f, -8.f, SmoothStep(U));
		}
		FootPitch *= MoveBlend;

		// 待机：腿回到静止位，只留一点呼吸。
		// ⚠️ 这里**不能**再乘一次 MoveBlend：Half（第 812 行）已经乘过 MoveBlend，
		//    P.Fwd 已是"按 MoveBlend 缩放的步幅"。再乘一次等于步幅 ∝ MoveBlend²，
		//    速度未满时支撑期后移跟不上机体前进速度 → 脚在地上向后滑
		//    （实测玩家 140cm/s 时每帧残留约 1cm 滑步，满速敌人反而没有）。
		if (MoveBlend < 1.f)
		{
			const float Idle = 1.f - MoveBlend;
			FootPitch += Idle * FMath::Sin(S.Time * 1.5f + (bLeft ? 0.f : PI)) * 1.2f;
		}
		P.Ankle = FootPitch;
		return P;
	};

	const float PhaseL = Phase / (2.f * PI);
	const float PhaseR = PhaseL + 0.5f;
	// 先判定这条腿这一刻是支撑还是摆动（决定要不要锁定步幅），再生成目标
	constexpr float DutyLocal = 0.50f;
	auto IsStanceNow = [&](float P)
	{
		const float LP = P - FMath::FloorToFloat(P);
		return LP < DutyLocal;
	};
	FLegPose PoseL = LegTarget(PhaseL, true,
		StrideForLeg(S.LegL, IsStanceNow(PhaseL)));
	FLegPose PoseR = LegTarget(PhaseR, false,
		StrideForLeg(S.LegR, IsStanceNow(PhaseR)));
	// 四足对角步态：左后与右前同相，右后与左前同相。双足机后腿无效，这两个姿势不会被用到。
	FLegPose PoseBL = LegTarget(PhaseR, true,
		StrideForLeg(S.LegBL, IsStanceNow(PhaseR)));
	FLegPose PoseBR = LegTarget(PhaseL, false,
		StrideForLeg(S.LegBR, IsStanceNow(PhaseL)));
	// 四足后腿的转弯侧向补偿与前腿同式（LegTarget 内已按 bLeft 定号，
	// 后腿只是相位不同，补偿量一致），无需额外处理。

	// ⑥ 骨盆高度
	//
	// ⚠️ 第六十三轮修正：骨架现在有**真实屈膝**（四足 th1≈±23~45°、th2≈∓30~52°，
	//    由资产层让大腿/小腿骨真正斜向膝/踝产生）。旧逻辑用
	//      h = sqrt((L1+L2)·0.985² − Fwd²)
	//    反推骨盆高度，隐含假设"腿在静止时几乎伸直"；但屈膝后真实静止落差
	//    RestDrop 明显小于腿全长，照旧公式会把骨盆抬得过高 → 支撑腿被压到
	//    钳位上限（实测 IK 裁剪从 0 涨到 6800~14800）。
	//    改为以**真实静止落差**为基准，只按 Fwd 造成的"髋踝距离变化"做小幅补偿。
	const float DMax = (L1 + L2) * 0.985f;
	const float RestDropBase = (S.LegL.bValid && S.LegL.DropCm > 1.f)
		? S.LegL.DropCm : (L1 + L2) * 0.98f;
	float SupportH = -1.f;
	auto LegSupportH = [&](const FLegPose& P, bool bLegValid)
	{
		if (!bLegValid || !P.bStance || P.Lift >= 1.f)
		{
			return;
		}
		// 支撑腿要够到地面：髋高上限是 sqrt(dMax² − Fwd²)，
		// 但不能超过"静止落差 + 屈膝余量"——否则会把屈膝的腿强行拉直。
		//
		// ⚠️ 第七十四轮：不能无条件取 sqrt(DMax²−Fwd²)。
		//    步幅有 30~50cm，Fwd 摆动时这个值会从 DMax 掉到 105 左右，
		//    骨盆被跟着压下去 4~12cm —— 而脚的目标点没动，腿被迫更弯，
		//    脚反而被抬起（实测行走时 Bob=−11~−14，脚底离地 20~35cm）。
		//    正确语义：**只有腿真的够不到时才压低**。静止落差已留了屈膝余量，
		//    所以在 Fwd 不超过"余量对应的水平行程"时，骨盆保持 RestDrop 不动。
		const float Slack = FMath::Max(DMax - RestDropBase, 0.5f);   // 屈膝余量
		// 余量能覆盖的水平位移：d² = RestDrop² + Fwd² ≤ DMax²  →  |Fwd| ≤ sqrt(DMax²−RestDrop²)
		const float FwdAllow = FMath::Sqrt(
			FMath::Max(DMax * DMax - RestDropBase * RestDropBase, 1.f));
		const float OverFwd = FMath::Max(FMath::Abs(P.Fwd) - FwdAllow, 0.f);
		// 只有超出部分才需要压低骨盆，压低量按超出的平方关系估算（近似）
		const float NeedH = FMath::Sqrt(FMath::Max(
			DMax * DMax - P.Fwd * P.Fwd, 1.f));
		const float Floor = RestDropBase - Slack;   // 最多压到把余量用完
		const float Target = (OverFwd > 0.f) ? FMath::Max(NeedH, Floor) : RestDropBase;
		SupportH = FMath::Max(SupportH, Target);
	};
	LegSupportH(PoseL, S.LegL.bValid);
	LegSupportH(PoseR, S.LegR.bValid);
	LegSupportH(PoseBL, S.LegBL.bValid);
	LegSupportH(PoseBR, S.LegBR.bValid);
	if (SupportH < 0.f)
	{
		SupportH = RestDropBase;
	}
	// 平滑支撑骨盆高度：换腿时"支撑腿集合"离散切换，SupportH 会跳变，
	// 对于腿长接近腿长的四足/运输机，IK 近奇异，骨盆跳变被放大成 70~120cm
	// 的脚滑（实测 C_5/C_7/C_9 在支撑连帧=3 处必现）。用指数平滑消除这个跳变。
	// 平滑系数拉到 12（约 0.1s 收敛），既消除跳变又不让落点滞后于地面。
	if (S.SupportHSmoothed < 0.f)
	{
		S.SupportHSmoothed = SupportH;
	}
	else
	{
		S.SupportHSmoothed = FMath::FInterpTo(
			S.SupportHSmoothed, SupportH, Dt, 12.f);
	}
	const float SupportHUsed = S.SupportHSmoothed;
	const float RestDrop = RestDropBase;
	float Bob = (SupportHUsed - RestDrop) * MoveBlend;
	float DbgLastSink = 0.f;
	float DbgLastImpact = 0.f;
	if (FParse::Param(FCommandLine::Get(), TEXT("DebugLegShape")))
	{
		// ⚠️ 按实例节流（用 S.PrevGaitLog），不能用函数内 static —— 会跨实例污染
		if (S.Time - S.PrevGaitLog > 0.5f)
		{
			S.PrevGaitLog = S.Time;
			UE_LOG(LogTemp, Warning,
				TEXT("[LegGeom] owner=%s LegLen=%.1f RestDrop=%.1f SupTarget=%.2f smoothed=%.1f Bob=%.1f "
					 "mb=%.2f sink=%.1f impact=%.1f | L1+L2=%.1f slack=%.1f"),
				Mesh->GetOwner() ? *Mesh->GetOwner()->GetName() : TEXT("?"),
				LegLen, RestDrop, SupportH, S.SupportHSmoothed, Bob,
				MoveBlend, DbgLastSink, DbgLastImpact,
				L1 + L2, (L1 + L2) - LegLen);
		}
	}

	// ── 伸直腿的下沉补偿：已移除（第七十四轮）──
	//
	// 这段是为**旧资产**（腿完全伸直、落差比≈1.0）写的：行走时主动压低躯干，
	// 让腿弯起来腾出水平行程。
	//
	// 第七十一轮已经在**资产层**把髋部压低 8%，腿本身就有真实屈膝余量。
	// 程序层再压一次就是重复压低 —— 实测把骨盆压到 −12~−14cm，
	// 而脚的 IK 目标点没动，腿被迫过度弯曲、脚被抬起 → "脚没贴地"。
	//
	// 判据（DropRatio ≤ 0.95 才跳过）也不可靠：资产压过后 LegLen 与 L1+L2
	// 同时缩小，比值仍接近 1.0，判据永远不成立。所以整段删除。

	// 触地缓冲：脚跟落地的一瞬间再压一点（只压不抬）
	// 与 MoveBlend 同口径：原地划腿/低速行走时不该有"重重踩一脚"的下沉。
	const auto ImpactOf = [&](float LegPhase, bool bStance)
	{
		if (!bStance) { return 0.f; }
		const float LP = LegPhase - FMath::FloorToFloat(LegPhase);
		const float U = LP / Duty;
		return FMath::Exp(-U * 9.f) * 1.2f * MoveBlend;
	};
	// ⚠️ 这里**不能**再乘 MoveBlend：ImpactOf 内部已经乘过（同第六十一轮的教训）。
	Bob -= FMath::Max(ImpactOf(PhaseL, PoseL.bStance),
		ImpactOf(PhaseR, PoseR.bStance));

	// 待机呼吸
	const float IdleBob = FMath::Sin(S.Time * 1.5f) * 0.9f * (1.f - MoveBlend);
	// 下限放宽到 -32：运输机腿长 158、落差比 0.95，需下沉 ~19cm 才够；
	// 旧 -20 的钳制会把这部分截断，导致 C_7 下沉补偿无效（裁剪 32 次不变）。
	if (FParse::Param(FCommandLine::Get(), TEXT("DebugBobFast")))
	{
		if (S.Time - S.PrevFootLog > 0.02f)
		{
			S.PrevFootLog = S.Time;
			UE_LOG(LogTemp, Warning, TEXT("[BobFast] %s t=%.3f Bob=%.2f SupT=%.2f sm=%.2f StL=%d StR=%d"),
				Mesh->GetOwner() ? *Mesh->GetOwner()->GetName() : TEXT("?"),
				S.Time, Bob, SupportH, S.SupportHSmoothed,
				PoseL.bStance ? 1 : 0, PoseR.bStance ? 1 : 0);
		}
	}
	Bob = FMath::Clamp(Bob, -32.f, 4.f) + IdleBob;

	if (IPelvis >= 0)
	{
		OffsetBoneAxis(Ctx, IPelvis, AxisUp, Bob);
	}

	// ⑥'' 脚滑检测已合并进下方 ⑥'（SolveLeg 之后、复用 FLw/FRw），
	// 因为本段原本在 SolveLeg 之前执行，读的是上一帧遗留的旧脚位，
	// 与 SolveLeg 之后写入的 PrevAnkleL 错帧，会把整步位移误算成滑步
	// （实测 C_8 因此报 766cm/s，真实稳态滑步≈0）。详见 ⑥' 的 [脚滑] 日志。

	// ⑥''' 独腿支撑补偿
	//
	// 一条腿被打掉后，旧实现只是隐藏骨骼：骨盆还停在双腿高度、身体竖直，
	// 剩下的那条腿会"够不到地"，画面就是独腿悬空 + 身体倾斜不自然。
	// 这里让骨盆下沉一点、整个躯干向支撑侧倾斜，读作"重心压在剩下那条腿上"。
	// 两条腿都在（LegsAlive==2）时偏移全为 0，不影响正常步态。
	{
		const float Missing = FMath::Clamp(2 - S.LegsAlive, 0, 2) * 0.5f;
		if (S.LegsAlive <= 0 && IPelvis >= 0)
		{
			// 双腿全断：机体没有支撑，跌坐在地。
			// ⚠️ 敌人骨架没有 pelvis 骨（torso 直接挂在 root 下），
			//    所以位移必须作用在 torso 上，否则躯干纹丝不动。
			//
			// ⚠️ 保守参数（第四十二轮）：上一版把"下沉 55% 腿长 + 前趴 14cm +
			//    侧倾 18° + 低头 24°"叠加在 torso 上，结果整机侧翻扭曲（r161）。
			//    这里只保留"坐下"本身的三个最小量：垂直下沉、轻微前倾、轻微前趴。
			//    - 下沉固定 32cm（落在 30~35 区间，与腿长无关，避免长腿机翻倒）
			//    - 前倾 7°（≤8°），不再侧倾、不再低头
			//    - 前趴位移压到 5cm，仅仅让重心落在座面上
			const float SinkCm = 32.f;
			const int32 Body = (ITorso >= 0) ? ITorso : IPelvis;
			OffsetBoneAxis(Ctx, Body, AxisUp, -SinkCm);
			OffsetBoneAxis(Ctx, Body, AxisFwd, 5.f);
			if (ITorso >= 0)
			{
				RotateBoneAxis(Ctx, ITorso, AxisRight, 7.f);
			}
		}
		else if (Missing > 0.f && IPelvis >= 0)
		{
			// 独腿：一样，敌人没有 pelvis 骨，位移作用在 torso 上
			const int32 Body = (ITorso >= 0) ? ITorso : IPelvis;
			OffsetBoneAxis(Ctx, Body, AxisUp, -6.f * Missing);
			// 往活着的那条腿一侧压。断腿只是隐藏骨骼，LegL/LegR 的 bValid 仍为 true，
			// 所以用 MissingLegSide 判断：左断 → 重心压右（+1），右断 → 压左（-1）。
			float SupportSide = 0.f;
			if (S.LegsAlive == 1)
			{
				SupportSide = (S.MissingLegSide == -1) ? 1.f
					: (S.MissingLegSide == 1 ? -1.f : 0.f);
			}
			if (SupportSide != 0.f)
			{
				OffsetBoneAxis(Ctx, Body, AxisRight, 8.f * Missing * SupportSide);
				if (ITorso >= 0 && Body != ITorso)
				{
					RotateBoneAxis(Ctx, ITorso, AxisFwd, -5.f * Missing * SupportSide);
				}
				else if (ITorso >= 0)
				{
					RotateBoneAxis(Ctx, ITorso, AxisFwd, -5.f * Missing * SupportSide);
				}
			}
		}
	}

	// ⑥'' 骨盆左右摆：重心压到支撑腿一侧（2~3cm 就够，多了像崴脚）
	//
	// ⚠️ 必须在**腿骨求解之前**算出：腿挂在躯干下，先转腿后移骨盆会把整条腿带走，
	//    脚在世界里横飘（实测脚速 266~1122cm/s，身体只有 140 → 观感"平移"）。
	// ⚠️ 也必须平滑：按支撑腿硬切的话换腿那一帧骨盆横移 5cm，指标瞬间飙高。
	float SwayCm = 0.f;
	{
		float TargetSway = 0.f;
		// ⚠️ 第六十四轮：四足（有后腿）时抑制骨盆横摆。
		//    四足用对角步态，同一相位上左前+右后同时支撑、另一相位右前+左后同时支撑
		//    → 任何时刻左右两侧都有支撑腿，重心不需要左右摆。
		//    而旧逻辑只看前腿（PoseL/PoseR）判断支撑侧，每半周期强行 ±2.6cm 摆一次，
		//    把骨盆拖着左右晃、连带前腿 IK 目标横移 —— 这正是四足比玩家滑 3~6 倍的来源。
		const bool bQuad = (S.LegBL.bValid || S.LegBR.bValid);
		const float Lateral = (bQuad ? 0.6f : 2.6f) * MoveBlend;
		if (PoseL.bStance && !PoseR.bStance) { TargetSway = -Lateral; }
		else if (PoseR.bStance && !PoseL.bStance) { TargetSway = Lateral; }
		S.SwayCm = FMath::FInterpTo(S.SwayCm, TargetSway, Dt, 7.f);
		SwayCm = S.SwayCm;
		if (IPelvis >= 0 && !FMath::IsNearlyZero(SwayCm, 0.01f))
		{
			OffsetBoneAxis(Ctx, IPelvis, AxisRight, SwayCm);
		}
	}



	// ⑥' 两骨 IK：把"脚的目标点"解成髋/膝角度
	// 四条腿髐的静态质心（用于判断前后腿）
	const FVector HipCentroid = (S.LegL.Hip + S.LegR.Hip + S.LegBL.Hip + S.LegBR.Hip) / 4.f;
	//
	//   d   = 髋→踝 距离
	//   α   = acos((L1² + d² − L2²) / (2·L1·d))    大腿相对髋踝连线的夹角
	//   K   = π − acos((L1² + L2² − d²) / (2·L1·L2))  膝弯角
	//   θ1  = base + α    （base = 髋踝连线相对竖直方向的前倾角）
	//   θ2  = θ1 − K
	// 膝盖朝前弯 → 大腿比连线更前倾，所以是 +α 而不是 −α。
	auto SolveLeg = [&](FMechLegRest& Rest, FLegPose& P) -> bool
	{
		if (!Rest.bValid)
		{
			return false;
		}
		// ── 组件缩放的补偿（第九十九轮，本轮核心修正）──
		// 目标点是在**组件空间**里叠加 Fwd/Lift 的，而骨骼的组件空间本身
		// 已经带了组件缩放（巨像 C_9 是 0.5）。
		// 于是：目标在组件空间后退 22.6cm，到世界里只有 11.3cm ——
		// 而机体在世界里仍然走了 108cm/s，**脚只退了应有一半**，
		// 只能被机体拖着走（实测 C_9 支撑滑移 55cm/s，玩家只有 10.8）。
		// 修法：把"厘米"换算成"组件空间单位"，即乘以组件缩放。
		// ⚠️ 只补偿**位移**，不补偿角度 —— 角度与缩放无关。
		const float CompScale = Mesh->GetComponentTransform().GetScale3D().GetAbsMin();
		// 髋的位置：静止位置 + 骨盆起伏
		// 髋的位置：静止位置 + 骨盆起伏 + 骨盆横摆（sway 已作用到骨盆骨上，
		// IK 的髋参考点必须同步，否则解出来的脚会偏离目标）
		const FVector Hip = Rest.Hip + AxisUp * Bob + AxisRight * SwayCm;
		Rest.DbgHip = Hip;
		Rest.DbgTarget = Rest.Ankle + AxisFwd * (P.Fwd * (1.f / FMath::Max(Mesh->GetComponentTransform().GetScale3D().GetAbsMin(), 0.01f)))
			+ AxisUp * (P.Lift * (1.f / FMath::Max(Mesh->GetComponentTransform().GetScale3D().GetAbsMin(), 0.01f)))
			+ AxisRight * ((P.FwdLat + P.OffLat) * (1.f / FMath::Max(Mesh->GetComponentTransform().GetScale3D().GetAbsMin(), 0.01f)));
		Rest.DbgAnkle = Rest.Ankle;
		Rest.DbgAxisUp = AxisUp;
		// 踝的目标：静止位置 + 前后偏移 + 抬脚高度 + 转弯侧向补偿
		// 位移必须除以组件缩放：这些厘米值最终会乘上组件变换才到世界。
		const float W2C = 1.f / FMath::Max(CompScale, 0.01f);
		const FVector Target = Rest.Ankle
			+ AxisFwd * (P.Fwd * W2C)
			+ AxisUp * (P.Lift * W2C)
			+ AxisRight * ((P.FwdLat + P.OffLat) * W2C);

		const FVector D = Target - Hip;
		if (!bMoving)
		{
			UE_LOG(LogTemp, Warning,
				TEXT("[Raw] owner=%s D=(%.2f,%.2f,%.2f) Hip=(%.2f,%.2f,%.2f) "
					 "Target=(%.2f,%.2f,%.2f) AxisUp=(%.2f,%.2f,%.2f)"),
				Mesh->GetOwner() ? *Mesh->GetOwner()->GetName() : TEXT("?"),
				D.X, D.Y, D.Z, Hip.X, Hip.Y, Hip.Z,
				Target.X, Target.Y, Target.Z,
				AxisUp.X, AxisUp.Y, AxisUp.Z);
		}
		const float DbgEy = FVector::DotProduct(D, AxisFwd);
		const float DbgEz = FVector::DotProduct(D, AxisUp);
		Rest.DbgE = FVector(DbgEy, DbgEz, D.X);
		// ⚠️ 第九十三轮：默认用全局 L1/L2（与资产配套）。
		//    -PerLegLen 时才用每条腿自己的骨长（实验证明对 C_5 更差）。
		const float L1 = (bUsePerLegLen && Rest.Thigh > 1.f) ? Rest.Thigh : ThighLen;
		const float L2 = (bUsePerLegLen && Rest.Shin > 1.f) ? Rest.Shin : ShinLen;
		const float dy = FVector::DotProduct(D, AxisFwd);
		const float dz = FVector::DotProduct(D, AxisUp);
		const float dx = FVector::DotProduct(D, AxisRight);
		// 用三维距离：骨盆横摆会把髋推离矢状面，只算 dy/dz 会低估腿长需求
		float d = FMath::Sqrt(dy * dy + dz * dz + dx * dx);
		const float dRaw = d;
		// ⚠️ 第七十四轮：上限必须接近真实腿长（0.999），不能压到 0.80。
		//    0.80 是早前为"留弯曲余量"加的，但资产层（第七十一轮）已经把髋部压低
		//    让腿真正屈膝了；再砍 20% 可达距离，腿就永远伸不到目标点 ——
		//    实测 clamp=96 而目标 d=118.5，脚被拉到半空（"脚没贴地"的直接原因）。
		// ⚠️ 第九十七轮实验：把可达上限改成"静止 |髋−踝| ×1.005"后，
		//    支撑段数从 35 掉到 1~4、滑移全部 >100 —— 脚完全够不到目标。
		//    说明当前 L1/L2 与资产的膝/踝位置是配套的，改上限反而破坏它。
		//    已回退，保留 (L1+L2)*0.999。
		d = FMath::Clamp(d, FMath::Abs(L1 - L2) + 2.f, (L1 + L2) * 0.999f);
		Rest.LastD = dRaw;
		// 可达性诊断：目标超出腿长时记录超出量，并区分支撑期/摆动期。
		// 阈值 1.0cm：腿在静止姿态本就接近伸直（垂直落差≈腿长，差 0.4% 属建模精度），
		// 0.5cm 边界抖动会逐帧误判；真实超伸（如四足满速）都 >2cm，不会漏判。
		Rest.LastDClamped = d;

		const float Base = FMath::RadiansToDegrees(FMath::Atan2(dy, -dz));

		const float CosA = FMath::Clamp(
			(L1 * L1 + d * d - L2 * L2) / FMath::Max(2.f * L1 * d, 1.f), -1.f, 1.f);
		const float A = FMath::RadiansToDegrees(FMath::Acos(CosA));
		const float CosK = FMath::Clamp(
			(L1 * L1 + L2 * L2 - d * d) / FMath::Max(2.f * L1 * L2, 1.f), -1.f, 1.f);
		const float K = 180.f - FMath::RadiansToDegrees(FMath::Acos(CosK));

		// ⚠️ 第七十七轮：膝盖**朝前弯还是朝后弯**，决定反解的符号 ——
		//    朝前弯：θ1 = base + α, θ2 = θ1 − K
		//    朝后弯：θ1 = base − α, θ2 = θ1 + K
		//    四足机的前腿膝朝前（-Y）、后腿膝朝后（+Y），原来一律按"朝前"解，
		//    后腿的 IK 就是错的。实测到位误差：前腿 0.14cm，后腿 5.3~10.5cm
		//    （C_9 后腿 10.5cm）—— 脚没落到目标点，支撑期在地上滑。
		//    这里用静止姿态里"膝相对髋在矢状面哪一侧"来自动判定，不依赖命名。
		//    这里用静止姿态里"膝相对髋在**矢状面（X 轴）**哪一侧"来自动判定：
		//    四足机的前后腿膝偏移沿 X 轴错开（V1=(±36.4, 0, -92.9)），
		//    前腿 V1.X<0、后腿 V1.X>0，因此判定天然给出相反符号。
		//    ⚠️ 不要用 AxisRight（Y 轴）—— 膝偏移的 Y 分量恒为 0，判定会失效。
		const float KneeSide = FVector::DotProduct(Rest.Knee - Rest.Hip, AxisFwd);
		// ── 膝弯方向判定（第九十六轮重写）──
		// ⚠️ 原判据 `KneeSide >= 0 → 朝后弯` 建立在"前腿 V1.X<0、后腿 V1.X>0"
		//    这个假设上。实测 C_9 的前腿 thigh_L 的 V1.X = **+36.4**（与后腿同号），
		//    于是前腿被当成后腿解 → 脚被甩到髋后方（实测差 180cm），
		//    支撑期只能靠骨骼链拖动，这就是 C_9 滑步 55~79cm/s 的真正来源。
		//    改用**踝相对髋**的矢状位置：前腿的脚在髋前方、后腿在髋后方，
		//    这个量与"骨骼轴朝向"无关，只取决于腿装在哪。
		const float AnkleSide = FVector::DotProduct(Rest.Ankle - Rest.Hip, AxisFwd);
		// 膝弯方向的**正确判据**：这条腿装在髋的前侧还是后侧。
		// 四足机的四条腿围绕同一个躯干，前两腿与后两腿的膝弯方向相反。
		// 用"髋相对静态质心（四条腿髋的平均）"的矢状位置来判：
		//   前腿 hip.x > 0 → 膝朝前弯；后腿 hip.x < 0 → 膝朝后弯。
		// ⚠️ 不能用 V1.X（大腿骨轴朝向）：C_7/C_9 的前腿 V1.X 也是正值，
		//    与前腿/后腿无关，这正是之前 C_9 前腿被当成后腿解、脚被甩到
		//    髋后 100cm 的原因。
		const float SideSignal = KneeSide;
		(void)AnkleSide;
		// ── 几何诊断（第九十三轮）──
		// 真可达半径 = 腿全长与"髋到目标竖直落差"的勾股关系：
		//   R = sqrt((L1+L2)² − dz²)
		// 之前所有步幅上限都按"腿长 × 比例"拍，没考虑长腿机的踝点本来就高，
		// 真正卡人的是竖直落差，不是腿长本身。
		if (FParse::Param(FCommandLine::Get(), TEXT("DebugReach")))
		{
			const int32 KeyG = FMath::RoundToInt(Rest.Hip.X) * 10000
				+ FMath::RoundToInt(Rest.Hip.Y);
			if (!S.BendLogged.Contains(KeyG + 777))
			{
				S.BendLogged.Add(KeyG + 777, 1);
				const float Dz0 = Rest.Hip.Z - Rest.Ankle.Z;
				const float ReachR = FMath::Sqrt(FMath::Max(
					(L1 + L2) * (L1 + L2) - Dz0 * Dz0, 1.f));
				UE_LOG(LogTemp, Warning,
					TEXT("[Reach] owner=%s hipZ=%.1f ankZ=%.1f dz=%.1f "
						 "legL1L2=%.1f R=%.1f restFwd=%.1f"),
					Mesh->GetOwner() ? *Mesh->GetOwner()->GetName() : TEXT("?"),
					Rest.Hip.Z, Rest.Ankle.Z, Dz0, L1 + L2, ReachR,
					Rest.Ankle.X - Rest.Hip.X);
			}
		}
		// 膝弯方向：前腿 V1.X<0、后腿 V1.X>0（镜像几何），反解符号必须相反，
		// 否则后腿的 IK 永远差一截（实测到位误差 后腿 10.5cm vs 前腿 0.13cm）。
		// 对照实验（-ExpBendSign 关闭 vs 开启，各跑 15s）：
		//   C_7 39→27、C_8 16→2、C_9 16→11，脚底离地两者都是 2.1cm。
		const float BendSign = (SideSignal >= 0.f) ? -1.f : 1.f;   // +1 = 朝前弯
		// 诊断：确认每条腿判成哪种弯曲方向（后腿必须与前腿相反）
		// ⚠️ 不能在这里做时间节流：本函数对四条腿各调一次，节流会让三条腿静默，
		//    看到的永远是最后一条腿（后腿），误以为"所有腿都同向"。
		//    用"每条腿只打一次"的标记代替时间节流。
		if (FParse::Param(FCommandLine::Get(), TEXT("DebugLegShape")))
		{
			// 用髋的组件空间位置当键：同一台机体的四条腿各有一个不同位置
			const int32 Hx = FMath::RoundToInt(Rest.Hip.X);
			const int32 Hy = FMath::RoundToInt(Rest.Hip.Y);
			const int32 Key = Hx * 10000 + Hy;
			if (!S.BendLogged.Contains(Key))
			{
				S.BendLogged.Add(Key, 1);
				UE_LOG(LogTemp, Warning,
					TEXT("[Bend] owner=%s hip=(%.0f,%.0f) V1=(%.1f,%.1f,%.1f) BendSign=%.0f th1rest=%.1f"),
					Mesh->GetOwner() ? *Mesh->GetOwner()->GetName() : TEXT("?"),
					Rest.Hip.X, Rest.Hip.Y,
					(Rest.Knee - Rest.Hip).X, (Rest.Knee - Rest.Hip).Y,
					(Rest.Knee - Rest.Hip).Z,
					BendSign, Rest.Theta1Deg);
			}
			if (!S.BendLogged.Contains(Key + 5000))
			{
				S.BendLogged.Add(Key + 5000, 1);
				(void)Rest;
			}
		}

		const float Theta1 = Base + A * BendSign;
		const float Theta2 = Theta1 - K * BendSign;
		// 相对静止姿势的角度差（静止腿本来就有 1~2° 的前倾）
		const float D1 = Theta1 - Rest.Theta1Deg;
		const float D2 = Theta2 - Rest.Theta2Deg;

		P.Hip = -D1;              // 正角度 = 向后摆
		P.Knee = (D1 - D2);       // 膝弯：小腿相对大腿向后
		// ⚠️ 第七十七轮：膝弯角的符号对**两组腿都正确**，不要再翻转。
		//    受控实验（-ExpKneeFlip / -ExpKneeFlip2）显示：
		//      · 翻转 V1.X>0 那组 → 其到位误差 0.13 → 150.9cm
		//      · 翻转 V1.X<0 那组 → 其到位误差 10.5 → 157.5cm
		//    两组翻转都会让误差爆炸，说明符号本身是对的。
		//    四足机后腿（BL/BR）残留 5~10cm 的到位误差另有原因，未定位；
		//    它不影响落地（脚底离地中位 2.1cm，与玩家一致），见 [FootH]。
		// ⚠️ 第九十二轮：内联 `P.Ankle = P.Ankle;` 是**自我赋值**（原意"只表示俯仰，
		//    不叠加 D2"），本身无害但会让 P.Ankle 一直是初值。脚掌俯仰另由
		//    FixFootRot 处理，这里保持不动。
		// ⚠️ 第九十二轮实验：把 P.Knee 从 `D1 - D2` 改成 `D2 - D1`（理论正解）后，
		//    脚底离地从 2.1cm **暴涨到 102.9cm**（脚被提到半空）——
		//    说明 D1/D2 的符号与 SwingBone 的施加方向是配套的，
		//    "D1 - D2" 才是这套增量坐标下的正确值。已回退，勿再改。
		P.Knee = (D1 - D2);
		// ── 直接按世界角施加（第九十四轮）──
		// 上一轮实测：IK 解出世界角 θ1=base+A·bs、θ2=θ1−K·bs，
		// 而 `D1-D2` 把 θ1 又减了两次 —— 正向运动学核对显示脚落点与目标
		// 差 8~70cm（C_9 实际脚离髋 215cm，超过骨长 177cm）。
		// 这里改成"相对静止世界角"的纯增量：
		//   P.Hip  = -(θ1 - θ1rest)   大腿转多少
		//   P.Knee =  K·BendSign      小腿再弯多少（世界角 θ2 = θ1 − K·bs）
		// 用 -NoIKWorldAngle 回到旧路径做对照。
		// ⚠️ 第九十四轮：用 `-(θ1-θ1rest)` / `K·bs` 直接施加也没成功 ——
		//    玩家 trk 0.8→2.6、滑移 10.9→10.6 但 p90 12.6→95.5，全部退化。
		//    结论：`D1-D2` 与 SwingBone 的轴向是配套的，问题不在这里。
		// 用 -IKWorldAngle 开启这条实验路径（默认关闭）。
		if (FParse::Param(FCommandLine::Get(), TEXT("IKWorldAngle")))
		{
			P.Hip = -(Base + A * BendSign - Rest.Theta1Deg);
			P.Knee = K * BendSign;
		}
		// ⚠️ 第九十八轮实验（**已推翻，不要重试**）：让髐角只跟随 base、A 用静止值。
		//    几何上很干净（r² 全线 1.00、前后腿斜率一致），
		//    但 105fps 下实测滑移全面恶化：玩家 10.8→34.9、C_5 15.1→69.1、
		//    C_7 59.5→85.6、C_8 11.2→74.9、C_9 54.9→68.0。
		//    结论："躯角与步幅严格线性" 不是脚钉得住的条件。

		// 诊断：本腿解算出的世界角与目标（组件空间，用于验证 IK 与正向运动学一致）
		Rest.DbgBase = Base;
		Rest.DbgA = A;
		Rest.DbgK = K;
		Rest.DbgBendSign = BendSign;
		// ── 正向运动学核对（第九十二轮）──
		// 从静止姿态沿矢状面推进大腿角 P.Hip、再叠加小腿角 P.Knee，
		// 算出"这套角度实际把脚放到哪"，与 IK 目标相减。
		// 差值不为零 = 增量角度的符号/坐标约定与 IK 假设不一致，
		// 脚就落不到目标点 —— 支撑期必然在地上滑。
		{
			const FVector2D V1(Rest.Knee - Rest.Hip);
			const FVector2D V2(Rest.Ankle - Rest.Knee);
			auto Rot2 = [](const FVector2D& V, float Deg)
			{
				const float R = FMath::DegreesToRadians(Deg);
				const float C = FMath::Cos(R);
				const float S = FMath::Sin(R);
				return FVector2D(V.X * C - V.Y * S, V.X * S + V.Y * C);
			};
			const FVector2D V1b = Rot2(V1, P.Hip);
			const FVector2D V2b = Rot2(V2, P.Hip + P.Knee);
			const FVector2D FootFK = FVector2D(Rest.Hip.X, Rest.Hip.Y) + V1b + V2b;
			const FVector2D FootTgt(Rest.DbgTarget.X, Rest.DbgTarget.Y);
			Rest.DbgFKErr = (FootFK - FootTgt).Size();
		}
		// 可达性诊断：目标超出腿长时记录超出量，并区分支撑期/摆动期。
		// 阈值 1.0cm：腿在静止姿态本就接近伸直（垂直落差≈腿长，差 0.4% 属建模精度），
		// 0.5cm 边界抖动会逐帧误计数；真实超伸（如四足满速）都 >2cm，不会漏判。
		if (dRaw > d + 1.0f)
		{
			S.IKOverreachCm = FMath::Max(S.IKOverreachCm, dRaw - d);
			++S.IKClampCount;
			if (P.bStance && P.Lift < 1.f)
			{
				++S.IKClampStance;
			}
			else
			{
				++S.IKClampSwing;
			}
		}
		return true;
	};

	const bool bSolvedL = SolveLeg(S.LegL, PoseL);
	const bool bSolvedR = SolveLeg(S.LegR, PoseR);
	const bool bSolvedBL = SolveLeg(S.LegBL, PoseBL);
	const bool bSolvedBR = SolveLeg(S.LegBR, PoseBR);

	SwingBone(IThighL, bSolvedL ? PoseL.Hip : 0.f);
	SwingBone(IShinL, bSolvedL ? PoseL.Knee : 0.f);
	SwingBone(IFootL, bSolvedL ? PoseL.Ankle : 0.f);
	SwingBone(IThighR, bSolvedR ? PoseR.Hip : 0.f);
	SwingBone(IShinR, bSolvedR ? PoseR.Knee : 0.f);
	SwingBone(IFootR, bSolvedR ? PoseR.Ankle : 0.f);
	SwingBone(IThighBL, bSolvedBL ? PoseBL.Hip : 0.f);
	SwingBone(IShinBL, bSolvedBL ? PoseBL.Knee : 0.f);
	SwingBone(IFootBL, bSolvedBL ? PoseBL.Ankle : 0.f);
	SwingBone(IThighBR, bSolvedBR ? PoseBR.Hip : 0.f);
	SwingBone(IShinBR, bSolvedBR ? PoseBR.Knee : 0.f);
	SwingBone(IFootBR, bSolvedBR ? PoseBR.Ankle : 0.f);

	// ── 脚掌绝对朝向纠正（第六十九轮）──
	// 问题：小臂式的增量补偿 `P.Ankle = D2 + FootPitch` 只抵消了小腿的转动，
	//       脚的世界俯仰仍随小腿摆动而变 —— 实际画面里脚掌是斜着立起来的。
	// 修法：脚骨的**世界（组件空间）朝向**直接钉在静止朝向上，再只叠加 FootPitch。
	//       支撑期以"平放"为主（FootPitch 权重小），摆动期允许脚尖下压/上翘。
	//       这样无论大腿小腿怎么摆，脚掌都保持平贴地面。
	auto FixFootRot = [&](int32 FootIdx, float PitchDeg, bool bUse)
	{
		if (!bUse || FootIdx < 0) { return; }
		const FMechBoneRest* R = S.Rest.Find(Ref.GetBoneName(FootIdx));
		if (!R) { return; }
		const FQuat Pitch(AxisRight, FMath::DegreesToRadians(PitchDeg));
		SetBoneCompRot(Ctx, FootIdx, (R->CompRot * Pitch).GetNormalized());
	};
	FixFootRot(IFootL, bSolvedL ? PoseL.Ankle : 0.f, bSolvedL);
	FixFootRot(IFootR, bSolvedR ? PoseR.Ankle : 0.f, bSolvedR);
	FixFootRot(IFootBL, bSolvedBL ? PoseBL.Ankle : 0.f, bSolvedBL);
	FixFootRot(IFootBR, bSolvedBR ? PoseBR.Ankle : 0.f, bSolvedBR);

	// ── 支撑脚轨迹导出（第九十轮）──
	// 为什么单独做：之前的 [FootZ] "支撑滑动"是逐帧累加，节流/初始化异常时
	// 样本数会失真（第八十九轮出现 n=66），而且只能看一个平均值。
	// 这里把**每一帧每条腿**的世界坐标原样写进日志，交给 Python 离线统计：
	// 真实的滑移 = 一段连续支撑期内脚的世界位置变化量。
	// 数据量：100fps × 4 腿 × 6 实体 ≈ 2400 行/秒，只用于短时间诊断运行。
	if (FParse::Param(FCommandLine::Get(), TEXT("DumpFootCsv")))
	{
		const FVector CompLoc = Mesh->GetComponentTransform().GetLocation();
		struct FCSVSlot
		{
			int32 FootIdx;
			const FLegPose* Pose;
			const TCHAR* Name;
			const FVector* Loc;
			const FMechLegRest* Rest;
		};
		const FCSVSlot Slots[4] = {
			{ IFootL, &PoseL, TEXT("L"), &S.LegL.Ankle, &S.LegL }, { IFootR, &PoseR, TEXT("R"), &S.LegR.Ankle, &S.LegR },
			{ IFootBL, &PoseBL, TEXT("BL"), &S.LegBL.Ankle, &S.LegBL }, { IFootBR, &PoseBR, TEXT("BR"), &S.LegBR.Ankle, &S.LegBR },
		};
		// 第九十五轮：把这些腿当成腿的只有 L/R 与 BL/BR 两对。
		// 双足机没有 BL/BR（索引为 -1，上面已跳过）。
		for (int32 k = 0; k < 4; ++k)
		{
			if (Slots[k].FootIdx < 0) { continue; }
			const FVector FW = LocalAccumWorldPos(Mesh, Ref, Slots[k].FootIdx);
			// 对照：引擎自己累积的骨骼矩阵（组件空间）
			const FVector BoneComp = Mesh->GetBoneMatrix(Slots[k].FootIdx)
				.GetOrigin();
			UE_LOG(LogTemp, Log,
				TEXT("[FootCSV] owner=%s leg=%s t=%.4f st=%d ph=%.3f fwd=%.2f lift=%.2f "
					 "fz=%.2f fx=%.2f fy=%.2f cx=%.2f cy=%.2f ly=%.1f "
					 "tgx=%.2f tgy=%.2f d=%.2f dc=%.2f "
					 "ax=%.2f ay=%.2f az=%.2f ihx=%.2f tlx=%.2f "
					 "hipx=%.2f hipz=%.2f ankx=%.2f ankz=%.2f uz=%.2f "
					 "bs=%.0f A=%.1f K=%.1f base=%.1f d2=%.2f fke=%.2f "
					 "trk=%.2f rdx=%.2f rdy=%.2f rdz=%.2f wdx=%.2f wdy=%.2f "
					 "bmx=%.2f bmy=%.2f bmz=%.2f bx=%.2f by=%.2f bz=%.2f "
					 "ey=%.2f ez=%.2f eX=%.2f Draw=%.2f mb=%.2f half=%.2f act=%.1f "
					 "upc=%.4f sc=%.3f php=%.2f pkn=%.2f "
					 "yx=%.3f yy=%.3f yz=%.3f "
					 "sx=%.3f sy=%.3f sz=%.3f "
					 "tgz=%.2f hipzw=%.2f "
					 "yp=%.1f yy=%.1f yr=%.1f "
					 "mdx=%.2f mdy=%.2f vx=%.2f vy=%.2f "
					 // 尾部的这个随帧变化量用于绕开 UE 日志的"重复行折叠"
					 // （同一条腿行首完全一样时会被合并，实测采样从 78/s 掉到 2.5/s）
					 "k=%d"),
				Mesh->GetOwner() ? *Mesh->GetOwner()->GetName() : TEXT("?"),
				Slots[k].Name, S.Time, Slots[k].Pose->bStance ? 1 : 0,
				Slots[k].Pose->DbgU, Slots[k].Pose->Fwd, Slots[k].Pose->Lift,
				FW.Z, FW.X, FW.Y, CompLoc.X, CompLoc.Y,
				Slots[k].Loc ? Slots[k].Loc->Y : 0.f,
				Slots[k].Rest->DbgTarget.X - Slots[k].Rest->DbgHip.X,
				Slots[k].Rest->DbgTarget.Y - Slots[k].Rest->DbgHip.Y,
				Slots[k].Rest->LastD, Slots[k].Rest->LastDClamped,
				AxisFwd.X, AxisFwd.Y, AxisFwd.Z,
				Slots[k].Rest->Hip.X, Slots[k].Loc ? Slots[k].Loc->X : 0.f,
				Slots[k].Rest->DbgHip.X, Slots[k].Rest->DbgHip.Z,
				Slots[k].Rest->DbgAnkle.X, Slots[k].Rest->DbgAnkle.Z,
				Slots[k].Rest->DbgAxisUp.Z,
				Slots[k].Rest->DbgBendSign, Slots[k].Rest->DbgA,
				Slots[k].Rest->DbgK, Slots[k].Rest->DbgBase,
				Slots[k].Pose->Knee, Slots[k].Rest->DbgFKErr,
				// trk：脚相对髋的**世界**位移 与 目标相对髋的**世界**位移 之差。
				// ⚠️ 第九十九轮（最终版）：所有量先换到世界空间再相减。
				//    C_9 缩放 0.5：目标在组件空间抬 7.7cm，世界只抬 3.85cm，
				//    而脚实测抬 3.4cm —— 完全吻合。之前混用组件/世界，永远报 100+。
				((FW
					- Mesh->GetComponentTransform().TransformPosition(
						Slots[k].Rest->DbgHip + AxisUp * Bob + AxisRight * SwayCm))
				 - (Mesh->GetComponentTransform().TransformVector(
						Slots[k].Rest->DbgTarget - Slots[k].Rest->DbgHip))).Size(),
				((FW - CompLoc) - Slots[k].Rest->Ankle).X,
				((FW - CompLoc) - Slots[k].Rest->Ankle).Y,
				((FW - CompLoc) - Slots[k].Rest->Ankle).Z,
				// wdx/wdy：目标相对静止姿势要求的偏移（这才是"IK 应当完成"的量）
				(Slots[k].Rest->DbgTarget - Slots[k].Rest->Ankle).X,
				(Slots[k].Rest->DbgTarget - Slots[k].Rest->Ankle).Y,
				BoneComp.X, BoneComp.Y, BoneComp.Z,
				BoneComp.X - Slots[k].Rest->Ankle.X,
				BoneComp.Y - Slots[k].Rest->Ankle.Y,
				BoneComp.Z - Slots[k].Rest->Ankle.Z,
				Slots[k].Rest->DbgE.X, Slots[k].Rest->DbgE.Y,
				Slots[k].Rest->DbgE.Z,
				Slots[k].Rest->LastD,
				MoveBlend, Stride * 0.5f * MoveBlend, S.ActualSpeed,
				S.BoneUnitPerCm,
				Mesh->GetComponentTransform().GetScale3D().GetAbsMin(),
				Slots[k].Pose->Hip, Slots[k].Pose->Knee,
				AxisFwd.X, AxisFwd.Y, AxisFwd.Z,
				Mesh->GetComponentTransform().GetScale3D().X,
				Mesh->GetComponentTransform().GetScale3D().Y,
				Mesh->GetComponentTransform().GetScale3D().Z,
				Slots[k].Rest->DbgTarget.Z,
				(Slots[k].Rest->DbgHip + AxisUp * Bob + AxisRight * SwayCm).Z,
				S.MoveDirSmoothed.X, S.MoveDirSmoothed.Y,
				Velocity.X, Velocity.Y,
				Mesh->GetComponentTransform().GetRotation().Rotator().Yaw,
				Mesh->GetComponentTransform().GetRotation().Rotator().Pitch,
				Mesh->GetComponentTransform().GetRotation().Rotator().Roll,
				FMath::RoundToInt(S.Time * 10000.f) & 0xFFFF);
		}
	}

	// ── 脚底离地诊断（第七十四轮，第七十六轮扩展为按腿统计）──
	// 直接量"脚骨原点在世界里的 Z"与"机体位置 Z"的差，以及支撑脚相对静止高度的偏差。
	// 之前一直靠截图判断"有没有悬空"，不够准；这里给出可比较的数字。
	// ⚠️ 累加必须每帧做（不能放在下面的日志节流里，否则采样率随节流变化）。
	// ⚠️ 必须覆盖**四条腿**：只统计 L/R 时，四足机（C_7/C_9）的另外两条腿完全没被
	//    检查过。
	//
	// ⚠️ 第七十七轮：这个统计原来的口径是错的 —— 它比较"脚当前 Z"和"静止 Z"，
	//    但 IK 的目的**就是**把脚摆到目标点（目标 = 静止 + Fwd + Lift），
	//    所以这个差在正常行走时本来就不该是 0。实测巨像 C_9 恒报 20~25cm，
	//    而物理判据（网格包围盒最低点 vs 地面）显示它的脚一直贴着地（2.1cm）。
	//    现在改为量**真正的 IK 到位误差**：脚实际位置 与 IK 目标点 的差。
	//    这个值才应该接近 0；它大才说明 IK 解算或骨骼朝向有问题。
	if (FParse::Param(FCommandLine::Get(), TEXT("DebugFootZ")) ||
		FParse::Param(FCommandLine::Get(), TEXT("DebugGait")))
	{
		// 顺序固定 L, R, BL, BR，与 FMechAnimState 的 DbgLeg*[4] 对应
		struct FLegDbgSlot
		{
			int32 FootIdx;
			const FLegPose* Pose;
			const FMechLegRest* Leg;
		};
		const FLegDbgSlot Slots[4] = {
			{ IFootL,  &PoseL,  &S.LegL  },
			{ IFootR,  &PoseR,  &S.LegR  },
			{ IFootBL, &PoseBL, &S.LegBL },
			{ IFootBR, &PoseBR, &S.LegBR },
		};
		const TCHAR* SlotNames[4] = { TEXT("L"), TEXT("R"), TEXT("BL"), TEXT("BR") };

		for (int32 k = 0; k < 4; ++k)
		{
			if (Slots[k].FootIdx < 0 || !Slots[k].Leg->bValid)
			{
				continue;
			}
			// IK 目标点：与 SolveLeg 内部完全相同的构造
			const FVector Target = Slots[k].Leg->Ankle
				+ AxisFwd * Slots[k].Pose->Fwd
				+ AxisUp * Slots[k].Pose->Lift
				+ AxisRight * Slots[k].Pose->FwdLat;
			const FVector Actual = LocalAccumCompPos(Mesh, Ref, Slots[k].FootIdx);
			const float Err = FVector::Dist(Actual, Target);
			S.DbgLegStanceDev[k] += Err;
			++S.DbgLegStanceN[k];
			if (!Slots[k].Pose->bStance)
			{
				S.DbgLegSwingMax[k] = FMath::Max(S.DbgLegSwingMax[k], Err);
				++S.DbgLegSwingN[k];
			}
		}

		if (S.Time - S.PrevFootLog > 1.0f)
		{
			S.PrevFootLog = S.Time;
			FString LegReport;
			for (int32 k = 0; k < 4; ++k)
			{
				if (S.DbgLegStanceN[k] <= 0)
				{
					continue;
				}
				const float ErrAvg = S.DbgLegStanceDev[k] / S.DbgLegStanceN[k];
				LegReport += FString::Printf(
					TEXT(" %s[到位误差=%.2f 摆动最大=%.2f n=%d hip=%.0f knee=%.0f lift=%.1f fwd=%.1f st=%d 支撑滑动=%.1f]"),
					SlotNames[k], ErrAvg, S.DbgLegSwingMax[k],
					S.DbgLegStanceN[k],
					Slots[k].Pose->Hip, Slots[k].Pose->Knee,
					Slots[k].Pose->Lift, Slots[k].Pose->Fwd,
					Slots[k].Pose->bStance ? 1 : 0,
					(k == 0 && S.DbgStanceMoveNL > 0) ? S.DbgStanceMoveL / S.DbgStanceMoveNL
					: (k == 1 && S.DbgStanceMoveNR > 0) ? S.DbgStanceMoveR / S.DbgStanceMoveNR
					: -1.f);
			}
			UE_LOG(LogTemp, Warning, TEXT("[FootZ] owner=%s bob=%.1f |%s"),
				Mesh->GetOwner() ? *Mesh->GetOwner()->GetName() : TEXT("?"),
				Bob, *LegReport);
		}
	}

	// （骨盆左右摆已挪到腿骨求解之前，见上方"⑨ 骨盆左右摆"）

	// ⑧ 躯干：速度前倾 + 转向侧倾 + 开火后坐
	//
	// ⚠️ 顺序：躯干必须**先于**它的子骨（锁骨 / 上臂 / 头）处理。
	//    FPoseCtx 里存的是"当前"组件空间旋转，父骨没更新就去转子骨，
	//    子骨会用上一版父朝向换算旋转轴 → 又是歪的。
	//    FReferenceSkeleton 保证父骨 index < 子骨 index，按 index 顺序即可。
	//
	// ⚠️⚠️ 第九十八轮：躯干旋转已**移到腿部 IK 之前**（见上方 ⑧′）。
	//    腿（thigh_*）是 torso 的子骨，torso 一转，整条腿就被带着走。
	//    原来放在 IK 之后：IK 按"torso 未旋转"求出关节角，
	//    随后 torso 转 Lean/Roll/Yaw，脚就被甩开 —— 长腿机（C_9 腿长 176）
	//    尤其明显。这里只留一个空块占位，不要再在这里旋转躯干。

	// ⑦ 手臂：与同侧腿反相摆动；抬枪瞄准时收窄摆幅。
	//
	// 顺序：锁骨（父）→ 上臂 → 前臂。
	// 摆幅系数 0.85（原来 0.62）：v5 的步幅是从 IK 反解出来的，
	// 数值比旧的"经验摆幅"小，乘 0.62 之后手臂几乎不动 —— 走路像"端着"。
	// 手臂摆幅按腿的 0.85 走，配合肘部随摆动屈伸，才有"甩起来"的重量感。
	const float ArmSwing = Swing * 0.85f;
	// 瞄准姿态：双臂略前抬、前臂内收，让枪管指向正前方
	const float Aim = SmoothStep(S.AimBlend);
	// 目标在上方时整条武器臂随仰角抬起，枪口才真的指向目标（玩家的 AimPitchDeg 恒为 0）
	const float ArmBase = -6.f - 10.f * Aim - S.AimPitchDeg * 0.9f * Aim;   // 负 = 前抬
	const float ForeBase = -4.f - 12.f * Aim;            // 负 = 枪口上抬

	const float ArmPhaseL = Phase;                       // 左臂与左腿反相
	const float ArmPhaseR = Phase + PI;
	// 肘部：手臂向后摆时自然弯曲（人手摆臂的规律），向前摆时伸直
	const float ElbowFlex = 12.f * FMath::Max(0.f,
		FMath::Cos(ArmPhaseL)) * MoveBlend;

	// 锁骨：瞄准时轻微下沉，让肩甲不挡住抬起的枪
	if (IClavL >= 0 || IClavR >= 0)
	{
		RotateBoneAxis(Ctx, IClavL, AxisRight, 4.f * Aim);
		RotateBoneAxis(Ctx, IClavR, AxisRight, -4.f * Aim);
	}

	// 左臂
	SwingBone(IArmL, ArmBase - ArmSwing * FMath::Cos(ArmPhaseL) * (1.f - Aim));
	SwingBone(IForeL, ForeBase + ElbowFlex);
	// 右臂（武器臂）：开火后坐把它往后推
	const float RecoilKick = S.Recoil * S.RecoilKickDeg;
	SwingBone(IArmR, ArmBase - ArmSwing * FMath::Cos(ArmPhaseR) * (1.f - Aim)
		+ RecoilKick);
	SwingBone(IForeR, ForeBase - S.Recoil * (S.RecoilKickDeg * 10.f / 14.f));

	// ⑨ 头部：朝视线方向微俯仰（瞄准时更明显）
	//    头是躯干的子骨，所以必须放在躯干旋转之后。
	if (IHead >= 0)
	{
		RotateBoneAxis(Ctx, IHead, AxisRight, 3.f * Aim);
	}

	S.PrevYaw = YawDegrees;
	S.PrevVelocity = Velocity;
	S.Recoil = FMath::Max(0.f, S.Recoil - Dt * S.RecoilDecayRate);

	Mesh->MarkRefreshTransformDirty();

	// 调试日志：只在 -AutoWalk / -AutoFire 下输出，正常玩没有。
	//
	// 判据：把两只脚的世界位置投影到**角色的前后轴**上，两者之差叫"前后差"；
	//   走路动画正确时：前后差来回摆动，左右差恒定，且高差在小范围内。
	//   若前后差恒为 0、左右差在摆动 → 腿在横着劈，摆错轴了。
	if (FParse::Param(FCommandLine::Get(), TEXT("AutoWalk")) ||
		FParse::Param(FCommandLine::Get(), TEXT("AutoFire")))
	{
		// ── 滑步量（每帧执行，不能放在下面的 0.15s 节流日志块里）──
		// 支撑脚在世界里应该是**静止**的。用相邻两帧的世界位移度量
		// "脚在地上蹭的速度"：< 10 cm/s 肉眼看不出来，> 40 cm/s 就是滑冰。
		//
		// ⚠️ 必须每帧调用！此前整段计算位于 `if (S.Time - S.PrevGaitLog > 0.15f)`
		//    节流块内，约 0.15s 才跑一次，于是 PrevFL 是"0.15 秒前"的脚位而非上一帧：
		//    速度 140cm/s × 0.15s ≈ 21cm，转弯时弧长叠加可达 60~73cm，再 ×60
		//    就成了 3600~4400cm/s 的假爆表 —— 指标失真的真正根因。
		//    移到节流块外后 PrevFL 才是真正的"上一帧"，等效 60fps 才有意义。
		auto WL = [&](int32 Idx) -> FVector
		{
			return LocalAccumWorldPos(Mesh, Ref, Idx);
		};
		const FVector FLw = WL(IFootL), FRw = WL(IFootR);
		// ── 支撑脚真实打滑量（第八十七轮）──
		// MacroSlip 是"窗口净位移差"，对窗口相位敏感，不能当打滑量用。
		// 这里只统计**处于支撑期的腿**在世界里的逐帧位移速度 —— 它应当接近 0。
		if (S.bPrevValid && Dt > 0.0005f && Dt < 0.03f)
		{
			if (PoseL.bStance)
			{
				S.DbgStanceMoveL += FVector::Dist2D(FLw, S.PrevFL) / Dt;
				++S.DbgStanceMoveNL;
			}
			if (PoseR.bStance)
			{
				S.DbgStanceMoveR += FVector::Dist2D(FRw, S.PrevFR) / Dt;
				++S.DbgStanceMoveNR;
			}
		}
		float SlipL = 0.f, SlipR = 0.f;
		if (S.bPrevValid)
		{
			// 滑步速度用"等效 60fps"：位移 × 60。
			// 游戏以 60fps 为目标帧率，这是玩家实际看到的滑速基准。
			//
			// ⚠️ 必须跳过掉帧帧（Dt > 0.03，实测出现过 Dt=0.4 的长帧）：
			//    长帧里机体自己走了一大步，位移×60 会把"一步"报成 3000~6000cm/s 假尖峰。
			//    这类帧既不是滑步也不是可复现现象，直接不计入统计。
			const bool bGoodDt = Dt > 0.0005f && Dt < 0.03f;
			// 同时用组件空间量一份，用于判定"全局同帧跳变"是否来自组件变换抖动
			const FVector FLc = LocalAccumCompPos(Mesh, Ref, IFootL);
			const FVector FRc = LocalAccumCompPos(Mesh, Ref, IFootR);
			const float InstCompL = bGoodDt ? FVector::Dist2D(FLc, S.PrevFLc) * 60.f : 0.f;
			S.PrevFLc = FLc;
			const float InstL = bGoodDt ? FVector::Dist2D(FLw, S.PrevFL) * 60.f : 0.f;
			const float InstR = bGoodDt ? FVector::Dist2D(FRw, S.PrevFR) * 60.f : 0.f;
			// ── 宏观滑步度量（第六十七轮）──
			// 窗口开始记一次脚与机体的绝对位置/时间，窗口结束再记一次，
			// 用 (脚位移 − 机体位移) / 时间 直接得滑步速度。
			// 完全不依赖逐帧差分，因此不受"哪些帧被统计"影响——这是本轮所有
			// 逐帧口径反复出错的根源（跨帧、跨相位、跨支撑段都会污染差分）。
			{
				const FVector CompNow = Mesh->GetComponentTransform().GetLocation();
				if (!S.bMacroInit)
				{
					S.MacroFootStart = FLw;
					S.MacroCompStart = CompNow;
					S.MacroTimeStart = S.Time;
					S.MacroPathLen = 0.f;
					S.bMacroInit = true;
				}
				// 累积脚走过的总路程（含摆动），用来衡量"腿忙不忙"
				if (bGoodDt) { S.MacroPathLen += InstL / 60.f; }
			}
			{
				// 临时诊断：把脚的水平位移分解成"沿机体前向 / 沿机体侧向"两轴。
				// 用来判定残余滑步到底来自 Fwd 补偿不足（前向）还是骨盆横摆/耦合（侧向）。
				const FQuat AQd = FRotator(0.f, YawDegrees, 0.f).Quaternion();
				const FVector AxF = AQd.RotateVector(FVector(1.f, 0.f, 0.f));
				const FVector AxR = AQd.RotateVector(FVector(0.f, 1.f, 0.f));
				const FVector dFL = FLw - S.PrevFL;
				S.DbgFwdStepL = FVector::DotProduct(dFL, AxF);
				S.DbgLatStepL = FVector::DotProduct(dFL, AxR);
				S.DbgCompStep = FVector::Dist2D(
					Mesh->GetComponentTransform().GetLocation(), S.DbgPrevCompW);
				S.DbgPrevCompW = Mesh->GetComponentTransform().GetLocation();
				// 侧向滑步：脚沿机体右向的世界位移（支撑脚应≈0）
				S.DbgLatStepAbs = FMath::Abs(S.DbgLatStepL);
			}
			S.CntStanceL = (PoseL.bStance && PoseL.Lift < 1.f) ? S.CntStanceL + 1 : 0;
			S.CntStanceR = (PoseR.bStance && PoseR.Lift < 1.f) ? S.CntStanceR + 1 : 0;
			if (PoseL.bStance && S.bPrevStanceL && S.CntStanceL >= 3 && S.LegL.bValid)
			{
				SlipL = InstL;
				S.SlideSumL += InstL;
				++S.SlideSamplesL;
				if (InstL > S.SlipMaxL) { S.SlipMaxL = InstL; }
				// ⚠️ footStep 与 expect 必须同口径：InstL 用的是"上次累加帧"的脚位，
				//    若中间隔了非支撑帧，就会把多帧位移算成一步。只在时间连续时累计。
				const bool bFootStepValid =
					S.DbgHavePrevFrame
					&& (S.Time - S.DbgPrevTime) <= FMath::Max(Dt * 2.f, 0.001f);
				// 诊断：把连续性判据的实际数值打出来（每窗只打一次）
				if (!S.bDbgLoggedGap && FParse::Param(FCommandLine::Get(), TEXT("DebugGait")))
				{
					S.bDbgLoggedGap = true;
					UE_LOG(LogTemp, Warning,
						TEXT("[GapProbe] owner=%s time=%.4f prevTime=%.4f dt=%.4f gap=%.4f limit=%.4f ok=%d"),
						Mesh->GetOwner() ? *Mesh->GetOwner()->GetName() : TEXT("?"),
						S.Time, S.DbgPrevTime, Dt, S.Time - S.DbgPrevTime,
						FMath::Max(Dt * 2.f, 0.001f), bFootStepValid ? 1 : 0);
				}
				// ── 无偏诊断（第六十五轮）──
				// 逐帧累加，不做任何阈值筛选，最后汇总成一行日志。
				// 验证的核心命题：支撑期脚相对机体的"后移速率"是否精确等于机体速度。
				//   · dFwd 是脚沿机体前向的**世界**位移（应≈0，脚应钉在地上）
				//   · 这里同时记录 |dFwd| 的绝对量，用来看残余的量级
				if (bGoodDt && bFootStepValid)
				{
					// ⚠️ 本帧的 dFwd 是"自上次累加帧以来"的累计位移（可能跨了若干帧），
					//    所以期望值也必须按同样的时间跨度算，否则口径不一致：
					//    会把多帧位移拿去和单帧 Speed·Dt 比，残差虚高。
					const float ElapsedForStep = FMath::Max(S.Time - S.DbgPrevTime, Dt);
					S.DbgNFrames++;
					S.DbgSumAbsStep += FMath::Abs(S.DbgFwdStepL);
					S.DbgSumExpect += Speed * ElapsedForStep;
					S.DbgSumStep += S.DbgFwdStepL;
					// 带符号的机体位移（世界 +X，即 -EnemyWalkConst 推进方向）
					const FVector dCompSigned = Mesh->GetComponentTransform().GetLocation()
						- S.DbgPrevCompW2;
					S.DbgSumCompSigned += dCompSigned.X;
					const float Residual = S.DbgFwdStepL - Speed * ElapsedForStep;
					S.DbgSumResidual += FMath::Abs(Residual);
					if (FMath::Abs(Residual) > S.DbgMaxResidual)
					{
						S.DbgMaxResidual = FMath::Abs(Residual);
					}
					// 帧间差分的连续性由外层的 bFootStepValid 保证（同一口径）。
					const bool bContiguous = bFootStepValid;
					const float DPh = FMath::FindDeltaAngleDegrees(
						S.DbgPrevPhase * 180.f / PI, Phase * 180.f / PI) * PI / 180.f;
					if (bContiguous)
					{
						S.DbgSumDPhase += FMath::Abs(DPh);
						S.DbgSumOmegaDt += Omega * Dt;
					}
					S.DbgPrevPhase = Phase;
					// 骨盆起伏逐帧变化量：这是唯一能通过 IK 把脚"上下+前后"拖动的量。
					// 用 |ΔBob|/帧 而不是 Bob 本身——恒定的 Bob 不会拖脚，跳变才会。
					if (S.DbgHavePrevBob && bContiguous)
					{
						const float DB = FMath::Abs(Bob - S.DbgPrevBob);
						S.DbgSumAbsDBob += DB;
						if (DB > S.DbgMaxDBob) { S.DbgMaxDBob = DB; }
					}
					S.DbgPrevBob = Bob;
					S.DbgHavePrevBob = true;
					S.DbgSumLatStep += S.DbgLatStepAbs;
					// 机体本帧实际位移（沿 +X，即 -EnemyWalkConst 的推进方向）：
					// 用来验证 expect = Speed·Dt 这个基准本身是否成立。
					if (S.DbgHavePrevComp && bContiguous)
					{
						const FVector dComp = Mesh->GetComponentTransform().GetLocation()
							- S.DbgPrevCompW2;
						S.DbgSumCompStep += FMath::Abs(dComp.X);
					}
					S.DbgPrevCompW2 = Mesh->GetComponentTransform().GetLocation();
					S.DbgHavePrevComp = true;
					// 骨盆横摆逐帧变化量：与 dBob 同理，恒定值不拖脚，跳变才拖
					if (S.DbgHavePrevSway && bContiguous)
					{
						S.DbgSumAbsDSway += FMath::Abs(SwayCm - S.DbgPrevSway);
					}
					S.DbgPrevSway = SwayCm;
					S.DbgHavePrevSway = true;
					// Fwd 的逐帧变化：这是脚位的直接驱动量。
					// 支撑期内理论上应恒为 -Speed·Dt（精确抵消机体前进）。
					// ⚠️ 只有**连续两帧都在累加**时差值才有效；中间隔了非支撑帧会累积多帧。
					if (S.DbgHavePrevFwd && bContiguous)
					{
						const float DF = PoseL.Fwd - S.DbgPrevFwd;
						S.DbgSumAbsDFwd += FMath::Abs(DF);
						S.DbgSumAbsDFwdErr += FMath::Abs(DF + Speed * Dt);
					}
					S.DbgPrevFwd = PoseL.Fwd;
					S.DbgHavePrevFwd = true;
				}
				// ⚠️ DbgPrevTime 必须**无条件**更新（不能放在上面的连续帧判定块里）：
				//    它自己就是连续性判据的输入，放进去会形成死锁——
				//    判据要求"上次已更新"，而上一次的更新又被判据挡住 → 永远不成立。
				S.DbgPrevTime = S.Time;
				S.DbgHavePrevFrame = true;
			}
			if (PoseR.bStance && S.bPrevStanceR && S.CntStanceR >= 3 && S.LegR.bValid)
			{
				SlipR = InstR;
				S.SlideSumR += InstR;
				++S.SlideSamplesR;
				if (InstR > S.SlipMaxR) { S.SlipMaxR = InstR; }
			}
		}
		S.PrevFL = FLw;
		S.PrevFR = FRw;
		S.bPrevStanceL = PoseL.bStance;
		S.bPrevStanceR = PoseR.bStance;
		S.bPrevValid = true;

		// 日志节流（-DebugGait）：每实例独立基准。
		if (S.Time - S.PrevGaitLog > 0.15f)
		{
			S.PrevGaitLog = S.Time;
			const FQuat AQ = FRotator(0.f, YawDegrees, 0.f).Quaternion();
			const FVector Fwd = AQ.RotateVector(FVector(1.f, 0.f, 0.f));
			const FVector Rgt = AQ.RotateVector(FVector(0.f, 1.f, 0.f));
			const FVector D = FLw - FRw;

			UE_LOG(LogTemp, Log,
				TEXT("[步态] 相位=%.2f 步幅=%.1f 步频=%.1f | 髋L=%+.1f 膝L=%.1f "
					 "踝L=%+.1f 髋R=%+.1f 膝R=%.1f 踝R=%+.1f | 起伏=%.1f "
					 "滑步L=%.1f 滑步R=%.1f"),
				Phase, Stride, Omega, PoseL.Hip, PoseL.Knee, PoseL.Ankle,
				PoseR.Hip, PoseR.Knee, PoseR.Ankle, Bob, SlipL, SlipR);

			// ── [脚滑] 汇总日志（与 [步态] 同源、同节流基准，避免错帧失真）──
			if (FParse::Param(FCommandLine::Get(), TEXT("DebugGait")) &&
				S.Time - S.PrevSlideLog > 0.25f)
			{
				S.PrevSlideLog = S.Time;
				const float NL = FMath::Max(1, S.SlideSamplesL);
				const float NR = FMath::Max(1, S.SlideSamplesR);
				UE_LOG(LogTemp, Log,
					TEXT("[脚滑] %s 速度=%.0f 左脚支撑期=%.0fcm/s 右脚支撑期=%.0fcm/s IK裁剪=%d(支撑%d/摆动%d) 超出=%.0fcm | 峰值L=%.0f 峰值R=%.0f"),
					Mesh->GetOwner() ? *Mesh->GetOwner()->GetName() : TEXT("?"),
					Speed, S.SlideSumL / NL, S.SlideSumR / NR, S.IKClampCount,
					S.IKClampStance, S.IKClampSwing, S.IKOverreachCm,
					S.SlipMaxL, S.SlipMaxR);
				// 无偏后移速率核对：脚沿前向位移 vs 机体应前进量
				if (S.DbgNFrames > 0)
				{
					const float N = static_cast<float>(S.DbgNFrames);
					UE_LOG(LogTemp, Log,
						TEXT("[RateCheck] owner=%s n=%d footStep=%.2fcm expect=%.2fcm ratio=%.2f "
							 "residMean=%.2fcm residMax=%.2fcm | dPhase=%.3f omegaDt=%.3f phaseRatio=%.2f "
							 "|dBob|=%.3fcm dBobMax=%.2fcm latStep=%.2fcm compStep=%.2fcm "
							 "|dSway|=%.3fcm |dFwd|=%.3fcm dFwdErr=%.3fcm "
							 "signedStep=%.3fcm signedComp=%.3fcm"),
						Mesh->GetOwner() ? *Mesh->GetOwner()->GetName() : TEXT("?"),
						S.DbgNFrames,
						S.DbgSumAbsStep / N, S.DbgSumExpect / N,
						(S.DbgSumExpect > 0.001f) ? (S.DbgSumAbsStep / S.DbgSumExpect) : 0.f,
						S.DbgSumResidual / N, S.DbgMaxResidual,
						S.DbgSumDPhase / N, S.DbgSumOmegaDt / N,
						(S.DbgSumOmegaDt > 0.0001f) ? (S.DbgSumDPhase / S.DbgSumOmegaDt) : 0.f,
						S.DbgSumAbsDBob / N, S.DbgMaxDBob, S.DbgSumLatStep / N,
						S.DbgSumCompStep / N, S.DbgSumAbsDSway / N,
						S.DbgSumAbsDFwd / N, S.DbgSumAbsDFwdErr / N,
						S.DbgSumStep / N, S.DbgSumCompSigned / N);
				}
				// 宏观滑步：脚沿机体前向的**净位移** 减去 机体前进量，除以经过的时间。
				// ⚠️ 必须用带符号的净位移（不是距离）：脚前后摆动，取距离会累加成
				//    一个与滑步无关的大数。
				if (S.bMacroInit)
				{
					const FQuat AQm = FRotator(0.f, YawDegrees, 0.f).Quaternion();
					const FVector AxFm = AQm.RotateVector(FVector(1.f, 0.f, 0.f));
					const float Elapsed = FMath::Max(S.Time - S.MacroTimeStart, 1e-4f);
					const FVector CompNow = Mesh->GetComponentTransform().GetLocation();
					const float FootNet = FVector::DotProduct(FLw - S.MacroFootStart, AxFm);
					// ⚠️ 机体位移也必须投影到**同一前向轴**：
					//    之前用世界 X，而敌人在 -WalkForever 下朝任意方向走，
					//    方向不一致时会把"正常前进"算成巨大的负向滑步（实测 C_8 -63cm）。
					const float CompNet = FVector::DotProduct(
						CompNow - S.MacroCompStart, AxFm);
					const float NetSlipCms = (FootNet - CompNet) / Elapsed;
					UE_LOG(LogTemp, Log,
						TEXT("[MacroSlip] owner=%s sec=%.2f footNet=%.1fcm compNet=%.1fcm netSlip=%.0fcm/s footPath=%.1fcm"),
						Mesh->GetOwner() ? *Mesh->GetOwner()->GetName() : TEXT("?"),
						Elapsed, FootNet, CompNet, NetSlipCms, S.MacroPathLen);
					S.MacroFootStart = FLw;
					S.MacroCompStart = CompNow;
					S.MacroTimeStart = S.Time;
					S.MacroPathLen = 0.f;
				}
				S.DbgNFrames = 0;
				S.DbgSumAbsStep = 0.f;
				S.DbgSumExpect = 0.f;
				S.DbgSumStep = 0.f;
				S.DbgSumResidual = 0.f;
				S.DbgMaxResidual = 0.f;
				S.DbgSumDPhase = 0.f;
				S.DbgSumOmegaDt = 0.f;
				S.DbgSumAbsDBob = 0.f;
				S.DbgMaxDBob = 0.f;
				S.DbgHavePrevBob = false;
				S.DbgSumLatStep = 0.f;
				S.DbgSumCompStep = 0.f;
				S.DbgSumCompSigned = 0.f;
				S.DbgHavePrevComp = false;
				S.DbgSumAbsDSway = 0.f;
				S.DbgHavePrevSway = false;
				S.DbgSumAbsDFwd = 0.f;
				S.DbgSumAbsDFwdErr = 0.f;
				S.DbgHavePrevFwd = false;
				S.DbgHavePrevFrame = false;
				S.SlideSumL = 0.f;
				S.SlideSumR = 0.f;
				S.SlideSamplesL = 0;
				S.SlideSamplesR = 0;
				S.IKClampCount = 0;
				S.IKClampStance = 0;
				S.IKClampSwing = 0;
				S.IKOverreachCm = 0.f;
				S.SlipMaxL = 0.f;
				S.SlipMaxR = 0.f;
			}
			UE_LOG(LogTemp, Log,
				TEXT("     脚世界坐标 左=(%+.1f,%+.1f,%+.1f) 右=(%+.1f,%+.1f,%+.1f) "
					 "前后差=%.1f 左右差=%.1f 高差=%.1f"),
				FLw.X, FLw.Y, FLw.Z, FRw.X, FRw.Y, FRw.Z,
				FVector::DotProduct(D, Fwd),
				FVector::DotProduct(D, Rgt),
				FLw.Z - FRw.Z);
		}
	}
}

// ─────────────────────────────────────────────
// 整体身体动作（降级方案：动画网格建不起来时用）
// ─────────────────────────────────────────────

void MechProceduralAnim::UpdateBody(USkeletalMeshComponent* Mesh,
	FMechAnimState& S, const FVector& Velocity, const FVector& ActorForward,
	float YawDegrees, float MaxSpeed, float Dt)
{
	if (!Mesh || Dt <= KINDA_SMALL_NUMBER)
	{
		return;
	}

	if (!S.bBaseMeshCached)
	{
		S.BaseMeshLoc = Mesh->GetRelativeLocation();
		S.BaseMeshRot = Mesh->GetRelativeRotation();
		S.bBaseMeshCached = true;
	}

	S.Time += Dt;
	const float Speed = Velocity.Size2D();
	const float SpeedRatio = (MaxSpeed > 1.f)
		? FMath::Clamp(Speed / MaxSpeed, 0.f, 1.f) : 0.f;

	float YawRate = 0.f;
	{
		const float Delta = FMath::FindDeltaAngleDegrees(S.PrevYaw, YawDegrees);
		YawRate = FMath::Clamp(Delta / Dt, -360.f, 360.f);
		S.PrevYaw = YawDegrees;
	}

	const FVector Accel = (Velocity - S.PrevVelocity) / Dt;
	S.PrevVelocity = Velocity;
	const FVector Dir2D = Velocity.GetSafeNormal2D();
	const float AccelAlong = Dir2D.IsNearlyZero()
		? 0.f : FVector::DotProduct(Accel, Dir2D);
	const float AccelPitch = FMath::Clamp(-AccelAlong * 0.010f, -9.f, 9.f);

	S.Recoil = FMath::Max(0.f, S.Recoil - Dt * S.RecoilDecayRate);

	const bool bMoving = SpeedRatio > 0.06f;
	// ⚠️ 第九十三轮：这里原本又推进了一次 S.GaitPhase（2.4 + 5.2*ratio）。
	//    腿部步态在下面 SolveLeg 里以 15rad/s 推进同一个变量，于是相位被
	//    每帧推进两次、且速率不同 —— 骨盆起伏、横摆与实际步韵完全脱钩
	//    （支撑期 0.21s 而起伏周期的 0.83s）。这里不再推进，
	//    起伏一律跟随腿部步态计算出来的相位。
	const float Idle = 1.f - SpeedRatio;

	// 上下起伏：走路双频 + 待机慢呼吸
	const float BobWalk = FMath::Sin(S.GaitPhase * 2.f) * 4.5f * SpeedRatio;
	const float BobIdle = FMath::Sin(S.Time * 1.6f) * 1.2f * Idle;

	// 前后倾：速度前倾 + 加速度俯仰 + 开火后坐后仰
	const float LeanFwd = SpeedRatio * 9.f + AccelPitch - S.Recoil * 7.f;
	// 转向侧倾
	const float RollTurn = FMath::Clamp(-YawRate * 0.035f, -14.f, 14.f)
		* FMath::Max(SpeedRatio, 0.35f);

	Mesh->SetRelativeLocation(S.BaseMeshLoc + FVector(0.f, 0.f, BobWalk + BobIdle));

	// 用四元数叠加：先应用网格自己的初始朝向，再在父节点（胶囊）坐标系里
	// 叠加倾角 —— 这样"前倾"永远绕角色的左右轴。
	const FQuat BaseQ = S.BaseMeshRot.Quaternion();
	const FQuat TiltQ = FRotator(LeanFwd, 0.f, RollTurn).Quaternion();
	Mesh->SetRelativeRotation((TiltQ * BaseQ).Rotator());
}
