#include "RobotEnemy.h"

#include "RobotProjectile.h"
#include "RobotSfx.h"
#include "SalvagePickup.h"
#include "RobotDamageSpark.h"
#include "RobotAttributeSet.h"
#include "RobotTypes.h"

#include "PartDamageComponent.h"
#include "PartMapData.h"

#include "AbilitySystemComponent.h"
#include "AIController.h"
#include "Components/CapsuleComponent.h"
#include "Components/PoseableMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
#include "Engine/EngineTypes.h"
#include "CollisionQueryParams.h"
#include "UObject/UObjectGlobals.h"
#include "Engine/SkeletalMesh.h"

namespace
{
	/**
	 * 敌人外观表。索引由实例序号决定（见 ResolveVariantIndex）。
	 *
	 * Scale 说明：Colossus 原始高 597cm，而敌人胶囊只有 260cm 高，
	 * 不缩的话碰撞和外观完全对不上（打身体会打空）。缩到 0.5 → 约 299cm，
	 * 仍然是场上最高大的机体，但打得到。
	 */
	struct FEnemyMeshDef
	{
		const TCHAR* Path;
		float Scale;
		/** 离地高度（cm）。有腿的机型填 0；悬浮机型填正数。 */
		float Hover;
	};

	const FEnemyMeshDef GEnemyMeshes[] =
	{
		// 5 种敌人各用各的机体，一眼能分辨类型与威胁。
		//
		// 早先这里 5 行全写的 Guard —— 当时以为 Patrol/Hauler/Gardener/
		// Colossus 的材质槽是空的（会用默认棋盘格材质渲染成灰方块）。
		// 后来用 `get_editor_property("materials")` 复核，5 个资产的材质槽
		// **其实都是满的**，之前的判断是 API 用错（用了 get_material(i)）。
		// 现已恢复各自的外观。
		//
		// 缩放按各自包围盒定：Colossus 体型远超胶囊，缩到 0.5。
		// Hover：Patrol 是悬浮机，没有腿。贴地之后看起来像"一个球趴在地上"，
		// 给 45cm 离地高度才读得出"浮着"。
		{ TEXT("/Game/RobotGame/Art/Characters/SK_Enemy_Guard.SK_Enemy_Guard"), 1.0f, 0.f },
		{ TEXT("/Game/RobotGame/Art/Characters/SK_Enemy_Patrol.SK_Enemy_Patrol"), 1.0f, 95.f },
		{ TEXT("/Game/RobotGame/Art/Characters/SK_Enemy_Hauler.SK_Enemy_Hauler"), 1.0f, 0.f },
		{ TEXT("/Game/RobotGame/Art/Characters/SK_Enemy_Gardener.SK_Enemy_Gardener"), 1.0f, 0.f },
		{ TEXT("/Game/RobotGame/Art/Characters/SK_Enemy_Colossus.SK_Enemy_Colossus"), 0.5f, 0.f },
	};}

int32 ARobotEnemy::ResolveVariantIndex() const
{
	if (MeshVariantIndex >= 0)
	{
		return MeshVariantIndex;
	}

	// 按 Actor 名字末尾的数字挑（RobotEnemy_0 / _1 / …）。
	// 这样脚本摆进关卡的 5 个敌人自动各不相同，不用一个个去配。
	const FString Name = GetName();
	int32 i = Name.Len() - 1;
	while (i >= 0 && FChar::IsDigit(Name[i]))
	{
		--i;
	}
	if (i < Name.Len() - 1)
	{
		return FCString::Atoi(*Name.Mid(i + 1));
	}
	return 0;
}

void ARobotEnemy::ApplyMeshVariant()
{
	USkeletalMeshComponent* MeshComp = GetMesh();
	if (!MeshComp)
	{
		return;
	}

	// 美术已经在蓝图里配过网格就不要覆盖
	if (MeshComp->GetSkeletalMeshAsset())
	{
		return;
	}

	const int32 Count = UE_ARRAY_COUNT(GEnemyMeshes);
	const int32 Idx = FMath::Abs(ResolveVariantIndex()) % Count;
	const FEnemyMeshDef& Def = GEnemyMeshes[Idx];

	USkeletalMesh* NewMesh = LoadObject<USkeletalMesh>(nullptr, Def.Path);
	if (!NewMesh)
	{
		UE_LOG(LogTemp, Warning, TEXT("[敌人] 骨骼网格加载失败：%s"), Def.Path);
		return;
	}

	const float Scale = (MeshScale > KINDA_SMALL_NUMBER) ? MeshScale : Def.Scale;
	MeshComp->SetRelativeScale3D(FVector(Scale));
	MeshComp->SetSkeletalMesh(NewMesh);
	bHoverMech = Def.Hover > KINDA_SMALL_NUMBER;

	// （腿长自适应步速的尝试已撤回：初始化阶段骨骼位置尚未同步，
	//   GetBoneLocation 取不到有效值，且曾导致崩溃。留待单独处理。）


	// 悬浮机没有腿：兜底步态会按 45cm 假腿去画，这里把腿类骨骼全部隐藏。

	// 让脚底贴地：和玩家用同一套算法。网格原点不一定在脚底
	// （Patrol 的原点就悬在半空 31cm），所以从包围盒算偏移，
	// 换外观时自动适配，不写死数值。
	const FBoxSphereBounds B = NewMesh->GetBounds();
	const float MeshBottomLocal = (B.Origin.Z - B.BoxExtent.Z) * Scale;
	const float CapsuleHalfHeight =
		GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	const float OffsetZ = -CapsuleHalfHeight - MeshBottomLocal + Def.Hover * Scale;
	MeshComp->SetRelativeLocation(FVector(0.f, 0.f, OffsetZ));

	UE_LOG(LogTemp, Log,
		TEXT("[敌人] %s 外观=%s 缩放=%.2f 网格底=%.1fcm 偏移=%.1fcm"),
		*GetName(), *NewMesh->GetName(), Scale, MeshBottomLocal, OffsetZ);

	// 建立可见的程序化动画网格（原网格转为不可见，只给部位系统查询骨骼）
	RefreshAnimMesh();
}

bool ARobotEnemy::IsQuadruped() const
{
	// 四足骨骼里有 thigh_BL（Blender 侧后腿命名），双足和悬浮机没有
	const USkeletalMeshComponent* Mc = GetMesh();
	const USkeletalMesh* Sk = Mc ? Cast<USkeletalMesh>(Mc->GetSkinnedAsset()) : nullptr;
	if (!Sk)
	{
		return false;
	}
	const FReferenceSkeleton& Ref = Sk->GetRefSkeleton();
	for (int32 i = 0; i < Ref.GetNum(); ++i)
	{
		if (Ref.GetBoneName(i) == FName(TEXT("thigh_BL")))
		{
			return true;
		}
	}
	return false;
}

void ARobotEnemy::RefreshAnimMesh(){
	USkeletalMeshComponent* Src = GetMesh();
	if (!Src || !Src->GetSkeletalMeshAsset())
	{
		return;
	}

	if (!AnimMesh)
	{
		AnimMesh = MechProceduralAnim::CreateVisualMesh(this, Src);
	}
	if (!AnimMesh)
	{
		return;
	}

	// 资产 + 材质。材质这步不能省：UPoseableMeshComponent 不会自动继承
	// 骨骼网格资产的材质槽，漏掉就会渲染成 UE 默认的棋盘格材质。
	MechProceduralAnim::SyncVisualMesh(AnimMesh, Src);

	// 资产换了 → 基准姿势失效，重新缓存
	AnimState.BaseTransforms.Reset();
	AnimState.bBaseCached = false;
	MechProceduralAnim::CacheBasePose(AnimMesh, AnimState);

	// 悬浮机没有腿：兜底步态会按 45cm 假腿去画，这里把腿类骨骼全部隐藏。
	if (bHoverMech)
	{
		MechProceduralAnim::HideBonesByPrefix(AnimMesh, TEXT("leg"));
		MechProceduralAnim::HideBonesByPrefix(AnimMesh, TEXT("thigh"));
		MechProceduralAnim::HideBonesByPrefix(AnimMesh, TEXT("shin"));
		MechProceduralAnim::HideBonesByPrefix(AnimMesh, TEXT("foot"));
	}

	// 已断部位重新隐藏：新建的 AnimMesh 是全新网格，之前 HideBonesByPrefix
	// 作用在旧实例上（或根本还没建），必须按当前部位状态再刷一遍。
	// ⚠️ 不依赖 PartMap 配置：那份 DataAsset 的前缀（leg_L/leg_R）在骨架改成
	//    thigh/shin/foot 之后就匹配不上了，而 Python 改它的嵌套数组存不住。
	//    这里按部位语义直接列举三脚架命名的全部变体。
	if (PartDamage && !bHoverMech)
	{
		auto HideAll = [&](std::initializer_list<const TCHAR*> Prefixes)
		{
			for (const TCHAR* P : Prefixes)
			{
				MechProceduralAnim::HideBonesByPrefix(AnimMesh, P);
			}
		};
		if (PartDamage->IsPartDestroyed(RobotTags::Part_Leg_L()))
		{
			HideAll({ TEXT("thigh_L"), TEXT("shin_L"), TEXT("foot_L"),
			          TEXT("thigh_BL"), TEXT("shin_BL"), TEXT("foot_BL"),
			          TEXT("leg_L") });
		}
		if (PartDamage->IsPartDestroyed(RobotTags::Part_Leg_R()))
		{
			HideAll({ TEXT("thigh_R"), TEXT("shin_R"), TEXT("foot_R"),
			          TEXT("thigh_BR"), TEXT("shin_BR"), TEXT("foot_BR"),
			          TEXT("leg_R") });
		}
		if (PartDamage->IsPartDestroyed(RobotTags::Part_Arm_L()))
		{
			HideAll({ TEXT("arm_L"), TEXT("upperarm_L"), TEXT("forearm_L"),
			          TEXT("shoulder_L") });
		}
		if (PartDamage->IsPartDestroyed(RobotTags::Part_Arm_R()))
		{
			HideAll({ TEXT("arm_R"), TEXT("upperarm_R"), TEXT("forearm_R"),
			          TEXT("shoulder_R") });
		}
	}

	UE_LOG(LogTemp, Log, TEXT("[敌人] %s 动画网格就绪 骨骼=%d 悬浮=%d 腿有效 L=%d R=%d BL=%d BR=%d"),
		*GetName(), AnimMesh->BoneSpaceTransforms.Num(), bHoverMech ? 1 : 0,
		AnimState.LegL.bValid ? 1 : 0, AnimState.LegR.bValid ? 1 : 0,
		AnimState.LegBL.bValid ? 1 : 0, AnimState.LegBR.bValid ? 1 : 0);
}

ARobotEnemy::ARobotEnemy()
{
	PrimaryActorTick.bCanEverTick = true;

	// 敌人的开火要看得清：后坐比玩家大、回弹比玩家快（玩家保持默认）
	AnimState.RecoilKickDeg = 24.f;
	AnimState.RecoilDecayRate = 5.5f;

	// 调试：-EnemyInPlace 让敌人原地播放步态（位置锁定，合成速度驱动动画）
	// -EnemyInPlaceIndex=<N>：只有该序号的敌人原地（其余照常行动，避免互相遮挡）
	bDebugInPlace = FParse::Param(FCommandLine::Get(), TEXT("EnemyInPlace"));
	{
		FString IdxStr;
		if (FParse::Value(FCommandLine::Get(), TEXT("EnemyInPlaceIndex="), IdxStr))
		{
			DebugInPlaceIndex = FCString::Atoi(*IdxStr);
		}
	}

	// 调试：-BreakLeg=L / -BreakLeg=R 在出生时打断指定腿，用于验证独腿支撑补偿
	{
		FString LegSide;
		if (FParse::Value(FCommandLine::Get(), TEXT("BreakLeg="), LegSide))
		{
			DebugBreakLeg = LegSide;
		}
	}

	GetCapsuleComponent()->InitCapsuleSize(60.f, 130.f);

	AbilitySystemComponent = CreateDefaultSubobject<UAbilitySystemComponent>(
		TEXT("AbilitySystemComponent"));
	AbilitySystemComponent->SetIsReplicated(false);
	AbilitySystemComponent->SetReplicationMode(EGameplayEffectReplicationMode::Minimal);

	AttributeSet = CreateDefaultSubobject<URobotAttributeSet>(TEXT("AttributeSet"));
	PartDamage = CreateDefaultSubobject<UPartDamageComponent>(TEXT("PartDamage"));
	// 敌人用 infer_bone_name 生成的骨架命名（有独立的 core 骨骼）
	PartDamage->bUsePlayerRigDefaults = false;

	if (UCharacterMovementComponent* Move = GetCharacterMovement())
	{
		Move->bOrientRotationToMovement = true;
		Move->RotationRate = FRotator(0.f, 360.f, 0.f);
		Move->MaxWalkSpeed = BaseMoveSpeed;
		Move->BrakingDecelerationWalking = 1600.f;

		// 没有 Controller 时也要跑物理。
		// 关卡里直接摆的敌人没有 PlayerController/AIController，
		// 而这个开关默认 false —— 那样即使 Tick 里调了 AddMovementInput，
		// 移动组件也不会真的推着角色走（表现为敌人站着不动）。
		Move->bRunPhysicsWithNoController = true;
	}

	bUseControllerRotationYaw = false;
}

UAbilitySystemComponent* ARobotEnemy::GetAbilitySystemComponent() const
{
	return AbilitySystemComponent;
}

void ARobotEnemy::BeginPlay()
{
	Super::BeginPlay();

	// 调试：-EnemyAt=x,y,z 覆盖出生点（把目标敌人挪到空地拍近景）
	// -EnemyAtIndex=<N>：只挪该序号的敌人（其余保持原位）
	{
		FString AtStr;
		FString AtIdxStr;
		const bool bHasIdx = FParse::Value(FCommandLine::Get(),
			TEXT("EnemyAtIndex="), AtIdxStr);
		const int32 AtIdx = bHasIdx ? FCString::Atoi(*AtIdxStr) : INDEX_NONE;
		if (FParse::Value(FCommandLine::Get(), TEXT("EnemyAt="), AtStr) &&
			(AtIdx == INDEX_NONE || AtIdx == ResolveVariantIndex()))
		{
			TArray<FString> Parts;
			AtStr.ParseIntoArray(Parts, TEXT(","), true);
			if (Parts.Num() == 3)
			{
				SetActorLocation(FVector(
					FCString::Atof(*Parts[0]), FCString::Atof(*Parts[1]),
					FCString::Atof(*Parts[2])), false, nullptr,
					ETeleportType::TeleportPhysics);
			}
		}
	}

	// 记录出生点：掉出地图时拉回来（正常情况下走不到，见 Tick 的边界检查）
	HomeLocation = GetActorLocation();
	LockedLocation = HomeLocation;

	UE_LOG(LogTemp, Warning, TEXT("[调试] %s 出生点=(%.0f,%.0f,%.0f)"),
		*GetName(), HomeLocation.X, HomeLocation.Y, HomeLocation.Z);

	// 调试：出生时打断指定腿（仅双足敌人），验证独腿支撑补偿。
	// ⚠️ 部位系统需要 PartMap 已就绪，所以放在下面 SetPartMap 之后执行。
	PendingBreakLeg = DebugBreakLeg;

	if (AbilitySystemComponent)
	{
		AbilitySystemComponent->InitAbilityActorInfo(this, this);
	}

	// 组件 BeginPlay 早于 Actor BeginPlay，所以这里必须显式换表并重建部位
	if (PartDamage)
	{
		if (PartMap)
		{
			PartDamage->SetPartMap(PartMap);
		}
		PartDamage->OnPartDestroyed.AddDynamic(this, &ARobotEnemy::HandlePartDestroyed);
		PartDamage->OnActorDisabled.AddDynamic(this, &ARobotEnemy::HandleActorDisabled);
	}

	if (UCharacterMovementComponent* Move = GetCharacterMovement())
	{
		Move->MaxWalkSpeed = BaseMoveSpeed;
	}

	// 外观：BP_Enemy 没有配骨骼网格（脚本创建时没设），
	// 所以这里按实例序号自动套上 5 种敌人机体之一，否则敌人是隐形的。
	ApplyMeshVariant();

	// 调试断腿：必须放在 ApplyMeshVariant 之后（骨架这时才确定，才能判断是不是四足）。
	// 只对双足敌人生效，保证画面里只有目标那台是独腿状态。
	if (!PendingBreakLeg.IsEmpty() && PartDamage && !bHoverMech && !IsQuadruped())
	{
		const bool bBoth = PendingBreakLeg.Equals(TEXT("Both"), ESearchCase::IgnoreCase);
		const bool bLeft = bBoth ||
			PendingBreakLeg.Equals(TEXT("L"), ESearchCase::IgnoreCase);
		const bool bRight = bBoth ||
			PendingBreakLeg.Equals(TEXT("R"), ESearchCase::IgnoreCase);
		if (bLeft)
		{
			PartDamage->ApplyDamageToPart(RobotTags::Part_Leg_L(), 100000.f);
		}
		if (bRight)
		{
			PartDamage->ApplyDamageToPart(RobotTags::Part_Leg_R(), 100000.f);
		}
		UE_LOG(LogTemp, Warning, TEXT("[调试] %s 外观=%s 出生时打断腿 %s"),
			*GetName(), *GetMesh()->GetSkinnedAsset()->GetName(), *PendingBreakLeg);

		// ⚠️ 顺序：ApplyMeshVariant 内部已经建过 AnimMesh（刷新时的"重隐"
		// 跑在断腿之前），所以这里断完腿必须重建一次，否则骨骼仍显示。
		RefreshAnimMesh();
	}

	// 战术角色：一部分绕后，一部分压制（见 FlankerRoleModulo 的注释）。
	bFlanker = (ResolveVariantIndex() % FMath::Max(1, FlankerRoleModulo)) == 0;
	UE_LOG(LogTemp, Log, TEXT("[战术] %s 角色=%s"),
		*GetName(), bFlanker ? TEXT("绕后") : TEXT("压制"));

	// ── 让敌人真的能移动 ──
	//
	// 这是个真 bug：APawn::AddMovementInput 只在**有 Controller** 时才会
	// 把输入累积到 ControlInputVector 里，而关卡里直接摆上去的敌人没有
	// Controller —— 于是 Tick 里那句 AddMovementInput 一直是空操作，
	// 敌人站着不动（既不会走过来，也不会拉开距离）。
	//
	// 补一个 AIController 把它 possess 掉就行，AI 逻辑一行都不用改。
	if (!GetController() && GetWorld())
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride =
			ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		if (AAIController* AI = GetWorld()->SpawnActor<AAIController>(
				AAIController::StaticClass(), GetActorLocation(),
				GetActorRotation(), Params))
		{
			AI->Possess(this);
			UE_LOG(LogTemp, Log, TEXT("[敌人] %s 已挂上 AIController"), *GetName());
		}
	}
}

void ARobotEnemy::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// ── 第一帧之后：按腿长修正行走速度 ──
	// 为什么不在 BeginPlay 做：那时 AnimMesh 的骨骼姿势还没同步，GetBoneLocation
	// 拿不到有效坐标（试过 GetRefBonePose / GetBoneLocationByName，前者取不到、
	// 后者直接崩溃）。到第一帧 Tick 末，pose 已经算好一次，数据才可用。
	if (!bLegSpeedAdjusted && AnimMesh)
	{
		bLegSpeedAdjusted = true;
		const USkeletalMesh* SkAsset = Cast<USkeletalMesh>(AnimMesh->GetSkinnedAsset());
		if (SkAsset)
		{
			const FReferenceSkeleton& RefSkel = SkAsset->GetRefSkeleton();
			int32 HipIdx = INDEX_NONE;
			int32 AnkIdx = INDEX_NONE;
			for (int32 i = 0; i < RefSkel.GetNum(); ++i)
			{
				const FName Bn = RefSkel.GetBoneName(i);
				if (HipIdx == INDEX_NONE &&
					(Bn == FName(TEXT("thigh_L")) || Bn == FName(TEXT("leg_L"))))
				{
					HipIdx = i;
				}
				if (AnkIdx == INDEX_NONE && Bn == FName(TEXT("foot_L")))
				{
					AnkIdx = i;
				}
			}
			if (HipIdx != INDEX_NONE && AnkIdx != INDEX_NONE)
			{
				const FVector Hip = AnimMesh->GetBoneLocation(
					RefSkel.GetBoneName(HipIdx), EBoneSpaces::WorldSpace);
				const FVector Ank = AnimMesh->GetBoneLocation(
					RefSkel.GetBoneName(AnkIdx), EBoneSpaces::WorldSpace);
				const float LegLenCm = FVector::Dist(Hip, Ank);
				// 步幅上限是腿长×0.62；支撑期占比 0.62。
				// 可承载速度 = 步幅 / 支撑期 = (腿长×0.62) / (周期×0.62)
				//             = 腿长 / 周期；周期取 0.52s（≈1.9 步/秒）→ 速度 ≈ 腿长×1.92
				// 旧系数 1.15 过于保守（把 260 压到 144），这里放宽到 1.7，
				// 只拦下真正超出步态承载的极端值。
				// ⚠️ 四足（运输机/巨像）再收紧到 0.9：它们的腿几乎完全伸直（落差比 1.0），
				//    水平余量为 0，满速时 IK 必然超伸。程序内无法安全补偿，只能靠降速。
				bool bIsQuad = false;
				for (int32 i = 0; i < RefSkel.GetNum(); ++i)
				{
					if (RefSkel.GetBoneName(i) == FName(TEXT("thigh_BL")))
					{
						bIsQuad = true;
						break;
					}
				}
				const float SpeedK = bIsQuad ? 1.30f : 1.70f;
				if (LegLenCm > 20.f && BaseMoveSpeed > LegLenCm * SpeedK)
				{
					const float NaturalMax = LegLenCm * SpeedK;
					UE_LOG(LogTemp, Warning,
						TEXT("[步速] %s 腿长=%.0fcm 步速 %.0f → %.0f"),
						*GetName(), LegLenCm, BaseMoveSpeed, NaturalMax);
					BaseMoveSpeed = NaturalMax;
					if (UCharacterMovementComponent* Mv = GetCharacterMovement())
					{
						Mv->MaxWalkSpeed = BaseMoveSpeed;
					}
				}
			}
		}
	}

	if (bDisabled)
	{
		// 瘫痪状态下的间歇性短路机械痉挛与金属火花听觉
		DisabledSparkTimer -= DeltaSeconds;
		if (DisabledSparkTimer <= 0.f)
		{
			DisabledSparkTimer = FMath::FRandRange(1.8f, 4.2f);
			if (AnimMesh)
			{
				// 核心或关节微小抖动痉挛，呈现内部伺服损坏短路特征
				AnimMesh->SetRelativeLocation(FVector(
					FMath::FRandRange(-2.5f, 2.5f),
					FMath::FRandRange(-2.5f, 2.5f),
					FMath::FRandRange(-1.0f, 1.0f)));
			}
			RobotSfx::PlayAt(this, TEXT("SFX_Impact"), GetActorLocation(), 0.35f, 1.8f, true);
		}
		return;
	}

	// ── 掉出地图兜底 ──
	// 玩家被硬边界挡住之后，敌人一般不会跑出场地；但如果关卡几何有缝，
	// 敌人掉下去会一直下坠（既打不到也死不了），直接把任务卡死。
	// 这里拉回出生点，比"永远掉着"好。
	{
		const FVector P = GetActorLocation();
		if (P.Z < -300.f)
		{
			SetActorLocation(HomeLocation + FVector(0.f, 0.f, 20.f), false,
				nullptr, ETeleportType::TeleportPhysics);
			if (UCharacterMovementComponent* Mv = GetCharacterMovement())
			{
				Mv->StopMovementImmediately();
			}
			UE_LOG(LogTemp, Warning, TEXT("[敌人] 掉出地图，已拉回出生点"));
		}
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	// 独腿支撑补偿需要知道还有几条腿、哪一侧断了。
	// 必须每帧在动画更新之前写入（包括"没有目标"的早退分支）。
	// 断腿只是隐藏骨骼，LegL/LegR 的 bValid 不会自己变 false，这里显式同步。
	if (PartDamage)
	{
		const bool bLLost = PartDamage->IsPartDestroyed(RobotTags::Part_Leg_L());
		const bool bRLost = PartDamage->IsPartDestroyed(RobotTags::Part_Leg_R());
		AnimState.LegsAlive = (bLLost ? 0 : 1) + (bRLost ? 0 : 1);
		// 只记录"哪侧断了"，不改 bValid（改了会让 IK 跳过剩下的那条腿）
		AnimState.MissingLegSide = bLLost ? -1 : (bRLost ? 1 : 0);

		// 双腿全断：视觉网格已经坐下，碰撞胶囊也要跟着变矮，
		// 否则会留一个"看不见的站立胶囊"挡子弹、挡住玩家走位。
		// 130cm 半高 → 55cm，中心下移 75cm，让底部仍贴地。
		if (UCapsuleComponent* Capsule = GetCapsuleComponent())
		{
			const bool bSitting = (AnimState.LegsAlive <= 0);
			if (bSitting && !bCapsuleShrunk)
			{
				bCapsuleShrunk = true;
				// ⚠️ 只改形状，不动中心位置：SetRelativeLocation(-75) 会让整个
				//    角色下沉 75cm（网格跟着胶囊走），实测敌人直接掉出画面。
				//    胶囊中心保持在 Actor 原点即可，底部会随半高自然抬高。
				Capsule->SetCapsuleSize(60.f, 55.f, false);
				UE_LOG(LogTemp, Warning,
					TEXT("[坐姿] %s 双腿全断 → 胶囊半高 %.0f 中心Z %.0f"),
					*GetName(), Capsule->GetScaledCapsuleHalfHeight(),
					Capsule->GetRelativeLocation().Z);
			}
			else if (!bSitting && bCapsuleShrunk)
			{
				// 兜底恢复路径（理论上腿断了不会长回来）
				bCapsuleShrunk = false;
				Capsule->SetCapsuleSize(60.f, 130.f, true);
				Capsule->SetRelativeLocation(FVector::ZeroVector);
			}
		}
	}

	// ── 目标获取 ──
	// 每 0.25 秒重新找一次玩家，避免每帧都做 GetPlayerPawn 查询
	RepathTimer -= DeltaSeconds;
	if (RepathTimer <= 0.f || !CurrentTarget)
	{
		RepathTimer = 0.25f;
		CurrentTarget = UGameplayStatics::GetPlayerPawn(this, 0);
	}

	AActor* Target = CurrentTarget;
	if (!Target)
	{
		// 没有目标：瞄准过渡量放下，否则丢失目标后手臂会一直举着。
		// 动画照常更新 —— 之前这里直接 return，巡逻/待机时腿与身体全部静止。
		AnimState.AimBlend = FMath::Lerp(AnimState.AimBlend, 0.f,
			FMath::Clamp(7.f * DeltaSeconds, 0.f, 1.f));
		if (AnimMesh)
		{
			MechProceduralAnim::Update(AnimMesh, AnimState, GetVelocity(),
				GetActorRotation().Yaw, FMath::Max(BaseMoveSpeed, 1.f),
				DeltaSeconds);
		}
		return;
	}

	const FVector MyLoc = GetActorLocation();
	const FVector TargetLoc = Target->GetActorLocation();
	const float Distance = FVector::Dist(MyLoc, TargetLoc);

	if (Distance > LoseTargetRange)
	{
		CurrentTarget = nullptr;
		return;
	}

	// 水平朝向目标的方向。走位与交战朝向都用它。
	const FVector ToTarget2D = (TargetLoc - MyLoc).GetSafeNormal2D();

	// ── 移动：推进器存活数直接决定能不能动、动多快 ──
	const int32 AliveThrusters = GetAliveThrusterCount();
	const float MoveScale = (AliveThrusters >= 2) ? 1.0f
		: (AliveThrusters == 1 ? 0.45f : 0.0f);

	// 瞄准姿态：交战距离内且武器臂存活时抬枪，离开交战区放下。
	// 枪口俯仰按目标相对枪口高度的仰角算（限制在 -20°~50°，超出不再抬）。
	{
		const bool bAimingNow = Distance <= AttackRange * 1.15f && HasAliveWeaponArm();
		const float AimRate = FMath::Clamp(7.f * DeltaSeconds, 0.f, 1.f);
		AnimState.AimBlend = FMath::Lerp(AnimState.AimBlend, bAimingNow ? 1.f : 0.f, AimRate);

		const float DzCm = (TargetLoc.Z + 40.f) - (MyLoc.Z + 80.f);
		const float HorizCm = FMath::Max(FVector::Dist2D(MyLoc, TargetLoc), 1.f);
		AnimState.AimPitchDeg = FMath::Clamp(
			FMath::RadiansToDegrees(FMath::Atan2(DzCm, HorizCm)), -20.f, 50.f);
	}

	// 程序化动画（-EnemyInPlace 时用合成速度驱动步态，身体不动）
	// -EnemyWalkConst：动画速度也用固定值，与机体推进速度严格一致
	const bool bWalkConst = bDebugInPlace &&
		FParse::Param(FCommandLine::Get(), TEXT("EnemyWalkConst"));
	const FVector AnimVel = bWalkConst
		? FVector(BaseMoveSpeed, 0.f, 0.f)
		: (bDebugInPlace ? DebugSynthVel : GetVelocity());
	// 瞄准 / 后坐调试输出（-DebugAim）：验证抬枪与后坐是否按预期变化
	if (FParse::Param(FCommandLine::Get(), TEXT("DebugAim")))
	{
		const float NowA = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
		if (NowA - DebugAimLastLog > 0.10f)
		{
			DebugAimLastLog = NowA;
			UE_LOG(LogTemp, Log,
				TEXT("[瞄准] %s 距离=%.0f 瞄=%.2f 俯仰=%.1f 后坐=%.2f 腿=%d"),
				*GetName(), Distance, AnimState.AimBlend,
				AnimState.AimPitchDeg, AnimState.Recoil, AnimState.LegsAlive);
		}
	}
	// 逐帧核对独腿状态下脚掌与地面的高度（-DebugFoot）
	// ⚠️ 必须量"脚底最低点"，不能量踝骨：园丁骨架里 foot 骨在踝部
	//    (Blender z=0.10m)，到脚底还有 10cm，量踝会系统性高估离地。
	if (AnimMesh && FParse::Param(FCommandLine::Get(), TEXT("DebugFoot")))
	{
		// ⚠️ 节流变量必须是**每实例**的成员，不能写函数内 static ——
		//    static 跨实例共享，第一个实例占住节流窗口后，其余实例永远不打印
		//    （实测只有 C_5 输出，C_7/C_9 完全看不到）。这是第三次踩同一个坑。
		const float NowT = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
		if (NowT - DebugFootLastLog > 0.08f)
		{
			DebugFootLastLog = NowT;
			// 用动画网格组件的世界包围盒最低点：包含所有可见几何（含支撑脚），
			// 比量踝骨可靠（园丁 foot 骨在踝部，到脚底还有 10cm）。
			const FBoxSphereBounds B = AnimMesh->Bounds;
			const float LowestZ = B.Origin.Z - B.BoxExtent.Z;
			// 脚下地面：从最低点向上 60cm 处向下打射线
			float GroundZ = -1e9f;
			bool bHit = false;
			UWorld* W = GetWorld();
			if (W && LowestZ < 1e8f)
			{
				FHitResult Hit;
				const FVector Base = GetActorLocation();
				const FVector Start(Base.X, Base.Y, LowestZ + 60.f);
				const FVector End(Base.X, Base.Y, LowestZ - 200.f);
				FCollisionQueryParams QP(SCENE_QUERY_STAT(DebugFootGround), false, this);
				if (W->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, QP))
				{
					GroundZ = Hit.ImpactPoint.Z;
					bHit = true;
				}
			}
			UE_LOG(LogTemp, Log,
				TEXT("[FootH] t=%.2f owner=%s legs=%d missing=%d lowZ=%.1f groundZ=%.1f gap=%.1f%s"),
				NowT, *GetName(), AnimState.LegsAlive, AnimState.MissingLegSide, LowestZ,
				GroundZ, bHit ? (LowestZ - GroundZ) : -999.f,
				bHit ? TEXT("") : TEXT(" (no-ground)"));
		}
	}
	// 位置锁定：合成速度只喂动画，不真的位移（否则固定机位拍不到）
	const bool bLockHere = bDebugInPlace &&
		(DebugInPlaceIndex == INDEX_NONE || DebugInPlaceIndex == ResolveVariantIndex());
	if (bLockHere)
	{
		// -EnemyWalkConst：不做锁定，改为按合成速度**真实推进**位置。
		// 用途：既保持恒定速度（消除 AI 加减速噪声），又有真实世界位移，
		// 这样"支撑脚在世界里是否静止"才是有效的滑步度量。
		// （纯 -EnemyInPlace 会锁死机体，脚的世界位移=步态后移量，量不出滑步。）
		if (FParse::Param(FCommandLine::Get(), TEXT("EnemyWalkConst")) && DebugSynthVel.SizeSquared2D() > 1.f)
		{
			// 严格受控：固定方向（+X）、固定大小，完全绕开 AI 的转向/加减速。
			// ⚠️ 必须按**实例**保存：用函数内 static 会让所有实体共用第一台的
			//    速度和初始化标志，其余实例的推进速度与自身动画速度不匹配 → 假滑步。
			if (!bWalkConstInit)
			{
				WalkConstVel = FVector(BaseMoveSpeed, 0.f, 0.f);
				bWalkConstInit = true;
				UE_LOG(LogTemp, Warning,
					TEXT("[WalkConst] %s 固定推进速度=%.0fcm/s 方向=+X"),
					*GetName(), BaseMoveSpeed);
			}
			SetActorLocation(GetActorLocation() + WalkConstVel * DeltaSeconds,
				false, nullptr, ETeleportType::TeleportPhysics);
			SetActorRotation(FRotator(0.f, 0.f, 0.f));
		}
		else
		{
			SetActorLocation(LockedLocation, false, nullptr,
				ETeleportType::TeleportPhysics);
		}
	}
	if (AnimMesh)
	{
		// ⚠️ MaxSpeed 必须传"实际能达到的速度"：BaseMoveSpeed 在腿长修正后
		// 可能已被下调（260 → 213），若仍按 260 归一化，SpeedRatio 只有 0.82，
		// 步频被算低 → 脚速跟不上身体，支撑脚滑动。
		float MaxSpeedForAnim = BaseMoveSpeed;
		if (UCharacterMovementComponent* Mv = GetCharacterMovement())
		{
			MaxSpeedForAnim = FMath::Max(Mv->MaxWalkSpeed, 1.f);
		}
		MechProceduralAnim::Update(AnimMesh, AnimState, AnimVel,
			GetActorRotation().Yaw, MaxSpeedForAnim,
			DeltaSeconds);
	}
	else if (GetMesh() && GetMesh()->GetSkeletalMeshAsset())
	{
		// 降级：动画网格没建好时，至少做整体身体动作
		MechProceduralAnim::UpdateBody(GetMesh(), AnimState,
			GetVelocity(), GetActorForwardVector(),
			GetActorRotation().Yaw, FMath::Max(BaseMoveSpeed, 1.f),
			DeltaSeconds);
	}

	if (MoveScale > 0.f)
	{
		const bool bCanStrafe = AliveThrusters >= 2;

		// ── 换向：优先朝玩家背后绕 ──
		//
		// 每 2—4 秒重选一次。方向不是随机的：用「我相对玩家的方位」与
		// 「玩家背后方向」的叉积判断哪边更近，就往哪边绕。已经在背后
		// （叉积接近 0）时换一边继续绕 —— 保持移动，不要站着当靶子。
		StrafeFlipTimer -= DeltaSeconds;
		if (StrafeFlipTimer <= 0.f && bCanStrafe)
		{
			StrafeFlipTimer = FMath::FRandRange(StrafeFlipMin, StrafeFlipMax);

			const FVector PlayerBack =
				(-Target->GetActorForwardVector()).GetSafeNormal2D();
			const FVector ToMe = (MyLoc - TargetLoc).GetSafeNormal2D();
			const float CrossZ = FVector::CrossProduct(ToMe, PlayerBack).Z;

			int32 NewSign = StrafeSign;
			if (bFlanker)
			{
				if (FMath::Abs(CrossZ) > 0.2f)
				{
					// 叉积 > 0：玩家背后在我左手边 → 逆时针（+1）更近
					NewSign = CrossZ > 0.f ? 1 : -1;
				}
				else
				{
					NewSign = -StrafeSign;
				}
			}
			else
			{
				// 压制手：随机换向。它们不追玩家的背，只需要从不同方向
				// 持续施压 —— 这样玩家视野里总有一两个看得见的目标。
				NewSign = FMath::RandBool() ? 1 : -1;
			}

			StrafeSign = NewSign;
			if (StrafeSign != LastLoggedStrafeSign)
			{
				LastLoggedStrafeSign = StrafeSign;
				UE_LOG(LogTemp, Log,
					TEXT("[战术] %s 环绕方向=%s（%s）"),
					*GetName(), StrafeSign > 0 ? TEXT("逆时针") : TEXT("顺时针"),
					bFlanker ? TEXT("朝玩家背后") : TEXT("压制换向"));
			}
		}

		FVector Desired = FVector::ZeroVector;
		if (!bCanStrafe)
		{
			// 只剩一条腿：绕不动了，只能直线挪到射程内。
			// 拆腿的收益必须"看得见"——从绕着玩家转，退化成慢慢挪过来的靶子。
			Desired = (Distance > AttackRange * 0.7f) ? ToTarget2D : FVector::ZeroVector;
		}
		else
		{
			const FVector Radial = (MyLoc - TargetLoc).GetSafeNormal2D();
			const FVector Tangent =
				FVector::CrossProduct(FVector::UpVector, Radial).GetSafeNormal2D();

			// 半径带：远了压、近了退、中间纯绕圈。
			// 注意 Radial 是「目标指向我」（向外），所以靠近要用负权重。
			float RadialWeight = 0.f;
			if (!bFlanker)
			{
				// 压制手：稳定停在射程内约 0.88 倍处 —— 太远打不到，
				// 太近又会把"压制位"变成"贴脸"。
				const float TargetRadius = AttackRange * 0.88f;
				// Radial 向外：比目标半径远 → 负权重（靠近），近了 → 正权重（后退）
				RadialWeight = FMath::Clamp(
					(TargetRadius - Distance) / (AttackRange * 0.2f), -1.f, 1.f);
			}
			else if (Distance > AttackRange * StrafeOuterRatio)
			{
				RadialWeight = -0.75f;   // 太远：一边绕一边压上
			}
			else if (Distance < AttackRange * StrafeInnerRatio)
			{
				RadialWeight = 1.0f;     // 太近：边打边退，保持射程
			}

			const float TangentWeight = bFlanker ? StrafeWeight : StrafeWeight * 0.7f;
			Desired = (Radial * RadialWeight + Tangent * StrafeSign * TangentWeight)
				.GetSafeNormal2D();
		}

		// 被掩体挡住视线时先直推过去拿射界 ——
		// 否则会隔着墙绕圈，既不开火也不逼近，看起来像卡住了。
		if (bRequireLineOfSight && !bHasLineOfSight && bCanStrafe)
		{
			Desired = ToTarget2D;
		}

		if (!Desired.IsNearlyZero())
		{
			if (bDebugInPlace)
			{
				// -EnemyInPlace：不真移动，只把期望速度喂给动画，步态照常播。
				// 这样固定机位能逐帧比对敌人步态（角色移动会让相机错位）。
				DebugSynthVel = Desired * BaseMoveSpeed;
			}
			else
			{
				AddMovementInput(Desired, 1.f);
			}
			if (UCharacterMovementComponent* Move = GetCharacterMovement())
			{
				Move->MaxWalkSpeed = BaseMoveSpeed * MoveScale;
			}
		}
	}

	// ── 交战朝向：横向平移时也把炮口对着玩家 ──
	//
	// 不这么做的话，bOrientRotationToMovement 会让敌人一直侧着身子横向滑行，
	// 弹道从侧面射出来，看起来像"螃蟹开枪"。而且敌机正面朝向玩家，
	// 玩家想打背面就必须真的绕过去 —— 方向加成才成立。
	if (UCharacterMovementComponent* Move = GetCharacterMovement())
	{
		const bool bInCombat = Distance <= AttackRange * 1.15f && HasAliveWeaponArm();
		Move->bOrientRotationToMovement = !bInCombat;

		if (bInCombat && !ToTarget2D.IsNearlyZero())
		{
			// ⚠️ 旧实现让身体始终正对目标，绕圈移动时腿只能"横着走"，
			//    而程序化步态只有前后迈步 —— 观感就是"平移滑行"（实测脚滑 400~900cm/s）。
			//    改为：身体朝向**移动方向**（腿正常迈步），瞄准由上身/武器臂转向承担。
			//    原地不动时仍朝向目标。
			const FVector MoveDir = GetVelocity().GetSafeNormal2D();
			const FVector FaceDir = MoveDir.IsNearlyZero() ? ToTarget2D : MoveDir;
			const FRotator Want(0.f, FaceDir.Rotation().Yaw, 0.f);
			SetActorRotation(FMath::RInterpTo(
				GetActorRotation(), Want, DeltaSeconds, 8.f));
		}
	}

	// ── 视线 ──
	// 每 0.15 秒查一次就够：射线很便宜，但没必要每帧做。
	//
	// 去抖是必需的：掩体边缘（柱子、脚手架、箱体）会让射线在"通/断"之间
	// 每 0.15 秒跳一次，敌人就会在"绕圈"和"直冲"之间反复抽搐。
	// 只有连续 0.35 秒都维持新结果，才真正切换状态。
	LOSCheckTimer -= DeltaSeconds;
	if (LOSCheckTimer <= 0.f)
	{
		constexpr float LOSCheckInterval = 0.15f;
		constexpr float LOSDebounceSeconds = 0.35f;

		LOSCheckTimer = LOSCheckInterval;
		FString Blocker;
		const bool bRawLOS = HasLineOfSightTo(Target, &Blocker);

		if (bRawLOS != bHasLineOfSight)
		{
			LOSPendingTime += LOSCheckInterval;
			if (LOSPendingTime >= LOSDebounceSeconds)
			{
				bHasLineOfSight = bRawLOS;
				LOSPendingTime = 0.f;

				if (bHasLineOfSight != bLastLoggedLOS)
				{
					bLastLoggedLOS = bHasLineOfSight;
					UE_LOG(LogTemp, Log, TEXT("[战术] %s 视线=%s 距离=%.0f 遮挡=%s"),
						*GetName(), bHasLineOfSight ? TEXT("有") : TEXT("被遮挡"),
						Distance, Blocker.IsEmpty() ? TEXT("-") : *Blocker);
				}
			}
		}
		else
		{
			LOSPendingTime = 0.f;
		}
	}

	// ── 攻击：武器臂存活数决定能不能打、打多快；没有视线就不开枪 ──
	AttackTimer -= DeltaSeconds;
	if (Distance <= AttackRange && HasAliveWeaponArm() && AttackTimer <= 0.f
		&& (!bRequireLineOfSight || bHasLineOfSight))
	{
		TryAttack(Target);
	}
}

// ─────────────────────────────────────────────
// 部位状态查询
// ─────────────────────────────────────────────

bool ARobotEnemy::HasAliveWeaponArm() const
{
	if (!PartDamage)
	{
		return false;
	}
	// 只要还有一条臂就能开火
	const bool bLeftAlive = !PartDamage->IsPartDestroyed(RobotTags::Part_Arm_L());
	const bool bRightAlive = !PartDamage->IsPartDestroyed(RobotTags::Part_Arm_R());
	return bLeftAlive || bRightAlive;
}

int32 ARobotEnemy::GetAliveThrusterCount() const
{
	if (!PartDamage)
	{
		return 0;
	}
	int32 Count = 0;
	if (!PartDamage->IsPartDestroyed(RobotTags::Part_Leg_L()))
	{
		++Count;
	}
	if (!PartDamage->IsPartDestroyed(RobotTags::Part_Leg_R()))
	{
		++Count;
	}
	return Count;
}

bool ARobotEnemy::IsCoreDestroyed() const
{
	return PartDamage ? PartDamage->IsCoreDestroyed() : false;
}

// ─────────────────────────────────────────────
// 行为
// ─────────────────────────────────────────────

bool ARobotEnemy::HasLineOfSightTo(const AActor* Target, FString* OutBlocker) const
{
	const UWorld* World = GetWorld();
	if (!World || !Target)
	{
		return false;
	}

	// 用胸口高度对射：脚底到脚底的射线会被地面/台阶误判成"被遮挡"。
	const FVector Start = GetActorLocation() + FVector(0.f, 0.f, 40.f);
	const FVector End = Target->GetActorLocation() + FVector(0.f, 0.f, 40.f);

	// 忽略自己与目标：目标胶囊本身就是"第一个挡住的东西"，
	// 不忽略的话这条射线永远返回"被遮挡"。
	FCollisionQueryParams Params(SCENE_QUERY_STAT(EnemyLOS), false, this);
	Params.AddIgnoredActor(Target);

	FHitResult Hit;
	const bool bBlocked = World->LineTraceSingleByChannel(
		Hit, Start, End, ECC_Visibility, Params);

	if (bBlocked && OutBlocker)
	{
		*OutBlocker = FString::Printf(TEXT("%s/%s"),
			*GetNameSafe(Hit.GetActor()), *GetNameSafe(Hit.GetComponent()));
	}
	return !bBlocked;
}

void ARobotEnemy::TryAttack(AActor* Target)
{
	// 调试：-NoEnemyFire 关闭敌人开火，用于无战斗的布光/构图截图验证。
	if (FParse::Param(FCommandLine::Get(), TEXT("NoEnemyFire")))
	{
		return;
	}
	UWorld* World = GetWorld();
	if (!World || !Target || !ProjectileClass)
	{
		return;
	}

	// 只有一条臂时射速减半 —— 打掉一条臂的收益是可感知的
	const int32 ArmCount = (PartDamage
		&& !PartDamage->IsPartDestroyed(RobotTags::Part_Arm_L()) ? 1 : 0)
		+ (PartDamage
			&& !PartDamage->IsPartDestroyed(RobotTags::Part_Arm_R()) ? 1 : 0);
	const float IntervalScale = (ArmCount >= 2) ? 1.0f : 2.0f;
	AttackTimer = AttackInterval * IntervalScale;

	// ── 枪口位置 ──
	//
	// 优先取动画网格上的**武器臂骨骼**（arm_R），并沿前向探出 55cm 作为真正枪口
	FVector Start = GetActorLocation() + FVector(0.f, 0.f, 40.f);
	if (AnimMesh)
	{
		FTransform BoneXf;
		if (MechProceduralAnim::GetBoneWorldTransform(
				AnimMesh, FName(TEXT("arm_R")), BoneXf))
		{
			Start = BoneXf.GetLocation() + GetActorForwardVector() * 55.f;
		}
	}

	// ── 瞄准：玩家胸口 + 随机散布锥 ──
	//
	// 散布是"弹道可见、可以躲"的前提（详见头文件 AttackSpreadDegrees 的注释）。
	// 只剩一条臂（后坐不对称）或一条腿（站不稳）时散布更大：
	// 拆掉部位除了"少一条枪/跑得慢"，命中率也该一起下降，
	// 否则拆解的即时收益对玩家来说仍然只是数字。
	float Spread = AttackSpreadDegrees;
	if (ArmCount <= 1)
	{
		Spread *= 1.6f;
	}
	if (GetAliveThrusterCount() <= 1)
	{
		Spread *= LameSpreadScale;
	}

	FVector Aim = (Target->GetActorLocation() + FVector(0.f, 0.f, 40.f) - Start)
		.GetSafeNormal();
	// ── 提前量预测 ──
	// 弹丸有飞行时间：距离 700cm / 弹速 1600cm/s ≈ 0.44s，玩家 140cm/s 会移动 61cm，
	// 超过 45cm 胶囊半径 —— 不预测就必然脱靶（实测移动目标命中率只有 84%）。
	// 用两次迭代估前置点：t = 距离/弹速，前置点 = 目标位置 + 目标速度 × t。
	//
	// ⚠️ 目标急停/变向时纯外推会过冲：前置点落在目标将要"不去"的地方。
	//    这里加一个**置信度**：比较目标速度与上一帧速度，变化越大前置量越少。
	//    - 速度大小骤降（急停）→ 前置量趋近 0（对准当前位置）
	//    - 方向突变（变向）→ 前置量减半
	if (Target)
	{
		const FVector TargetCore = Target->GetActorLocation() + FVector(0.f, 0.f, 40.f);
		const FVector TargetVel = Target->GetVelocity();
		const float NowS = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;

		// 与上次开火时的速度比较，估算机动剧烈程度
		float Confidence = 1.f;
		if (TargetVel.SizeSquared() > 1.f && !LastAimTargetVel.IsNearlyZero())
		{
			const float SpeedRatio = TargetVel.Size() /
				FMath::Max(LastAimTargetVel.Size(), 1.f);
			const FVector DirNow = TargetVel.GetSafeNormal();
			const FVector DirPrev = LastAimTargetVel.GetSafeNormal();
			const float DirDot = FVector::DotProduct(DirNow, DirPrev);

			// 速度下降（急停）→ 置信度随之降低；方向反转（DirDot 越小）→ 也降低
			const float SpeedFactor = FMath::Clamp(SpeedRatio, 0.f, 1.f);
			const float DirFactor = FMath::Clamp((DirDot + 1.f) * 0.5f, 0.f, 1.f);
			Confidence = FMath::Clamp(SpeedFactor * 0.7f + DirFactor * 0.3f, 0.15f, 1.f);
		}
		LastAimTargetVel = TargetVel;
		LastAimTime = NowS;

		if (!TargetVel.IsNearlyZero() && ProjectileSpeed > KINDA_SMALL_NUMBER)
		{
			float T = (TargetCore - Start).Size() / ProjectileSpeed;
			for (int32 Iter = 0; Iter < 2; ++Iter)
			{
				const FVector Lead = TargetCore + TargetVel * T;
				T = (Lead - Start).Size() / ProjectileSpeed;
			}
			// 前置量乘置信度：机动越剧烈，越倾向于直接打当前位置
			const FVector Lead = TargetCore + TargetVel * T * Confidence;
			Aim = (Lead - Start).GetSafeNormal();

			if (FParse::Param(FCommandLine::Get(), TEXT("DebugAim")))
			{
				UE_LOG(LogTemp, Log,
					TEXT("[预判] 速度=%.0f 置信=%.2f 前置=%.1fcm"),
					TargetVel.Size(), Confidence,
					(TargetVel * T * Confidence).Size());
			}
		}
	}
	if (Spread > KINDA_SMALL_NUMBER)
	{
		Aim = FMath::VRandCone(Aim, FMath::DegreesToRadians(Spread));
	}
	const FRotator Rot = Aim.Rotation();

	// ── 弹道命中比对（-DebugAim）──
	// 用**加了散布之后的真实方向**算射线到目标胸口垂心的最短距离：
	//   垂直距离 ≤ 目标半径 → 这一发会命中。
	// 同时记录主轴偏差角（无散布的"理想瞄准"与"实际发射"之间的夹角）。
	if (FParse::Param(FCommandLine::Get(), TEXT("DebugAim")))
	{
		const FVector TargetCore = Target->GetActorLocation() + FVector(0.f, 0.f, 40.f);
		const FVector IdealDir = (TargetCore - Start).GetSafeNormal();
		const float OffAxisDeg = FMath::RadiansToDegrees(
			FMath::Acos(FMath::Clamp(FVector::DotProduct(IdealDir, Aim), -1.f, 1.f)));

		// 射线到"预判命中点"的最短距离：有提前量时，理想弹道本来就不指向
		// 目标当前位置，所以这里和预判点比，而不是和当前位置比。
		const FVector TargetVelP = Target->GetVelocity();
		float Tp = (TargetCore - Start).Size() / FMath::Max(ProjectileSpeed, 1.f);
		const FVector Predicted = TargetCore + TargetVelP * Tp;

		// 射线到点的最短距离（用预判点）
		const FVector ToTarget = Predicted - Start;
		const float Proj = FVector::DotProduct(ToTarget, Aim);
		const float MissDist = FMath::Sqrt(FMath::Max(
			ToTarget.SizeSquared() - Proj * Proj, 0.f));

		// 目标碰撞半径（胶囊或球体）
		float TargetRadius = 60.f;
		if (const UCapsuleComponent* Cap = Target->FindComponentByClass<UCapsuleComponent>())
		{
			TargetRadius = Cap->GetScaledCapsuleRadius();
		}

		UE_LOG(LogTemp, Log,
			TEXT("[弹道] %s 距离=%.0f 散布角=%.2f° 脱靶量=%.1fcm 目标半径=%.1fcm 命中=%s 枪口=(%.0f,%.0f,%.0f)"),
			*GetName(), ToTarget.Size(), OffAxisDeg, MissDist, TargetRadius,
			(MissDist <= TargetRadius) ? TEXT("是") : TEXT("否"),
			Start.X, Start.Y, Start.Z);
	}

	// 开火反馈：武器臂后坐
	MechProceduralAnim::TriggerRecoil(AnimState, 1.f);

	FActorSpawnParameters Params;
	Params.Owner = this;
	Params.Instigator = this;
	Params.SpawnCollisionHandlingOverride =
		ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	ARobotProjectile* Projectile = World->SpawnActor<ARobotProjectile>(
		ProjectileClass, Start, Rot, Params);
	if (Projectile)
	{
		Projectile->InitProjectile(AttackDamage, ProjectileSpeed, this);
	}

	// 敌方开火音效：音色比玩家更低沉 —— 战场上"谁在开火"一耳朵能听出来
	RobotSfx::PlayAt(this, TEXT("SFX_Fire_Enemy"), Start, 0.8f, 1.f, true);
}

void ARobotEnemy::EnterDisabledState()
{
	bDisabled = true;

	if (UCharacterMovementComponent* Move = GetCharacterMovement())
	{
		Move->StopMovementImmediately();
		Move->DisableMovement();
	}
}

// ─────────────────────────────────────────────
// 事件
// ─────────────────────────────────────────────

void ARobotEnemy::HandlePartDestroyed(FGameplayTag PartTag)
{
	// 部位被摧毁的"金属爆裂"音效 —— 打断、碎甲、零件飞出的听觉锚点
	RobotSfx::PlayAt(this, TEXT("SFX_Destroy"), GetActorLocation(),
		0.9f, 1.f, true);

	// 把骨骼隐藏同步到可见的动画网格（部位系统只隐藏 GetMesh() 上的骨骼，
	// 而那个网格不可见，所以要在 AnimMesh 上再隐藏一次）。
	// ⚠️ 不靠 PartMap 的前缀（那份 DataAsset 还写着旧的 leg_L/leg_R），
	//    按部位语义直接列举骨骼名前缀。
	if (AnimMesh)
	{
		FVector BreakBoneLoc = GetActorLocation();
		bool bFoundBoneLoc = false;

		auto HideSet = [&](std::initializer_list<const TCHAR*> Prefixes)
		{
			for (const TCHAR* P : Prefixes)
			{
				if (!bFoundBoneLoc)
				{
					if (USkeletalMesh* SkMesh =
							Cast<USkeletalMesh>(AnimMesh->GetSkinnedAsset()))
					{
						const FReferenceSkeleton& Ref = SkMesh->GetRefSkeleton();
						for (int32 i = 0; i < Ref.GetNum(); ++i)
						{
							const FName BName = Ref.GetBoneName(i);
							if (BName.ToString().StartsWith(P, ESearchCase::IgnoreCase))
							{
								BreakBoneLoc = AnimMesh->GetBoneLocationByName(
									BName, EBoneSpaces::WorldSpace);
								bFoundBoneLoc = true;
								break;
							}
						}
					}
				}
				MechProceduralAnim::HideBonesByPrefix(AnimMesh, P);
			}
		};

		if (PartTag == RobotTags::Part_Leg_L())
		{
			HideSet({ TEXT("thigh_L"), TEXT("shin_L"), TEXT("foot_L"),
			          TEXT("thigh_BL"), TEXT("shin_BL"), TEXT("foot_BL"), TEXT("leg_L") });
		}
		else if (PartTag == RobotTags::Part_Leg_R())
		{
			HideSet({ TEXT("thigh_R"), TEXT("shin_R"), TEXT("foot_R"),
			          TEXT("thigh_BR"), TEXT("shin_BR"), TEXT("foot_BR"), TEXT("leg_R") });
		}
		else if (PartTag == RobotTags::Part_Arm_L())
		{
			HideSet({ TEXT("arm_L"), TEXT("upperarm_L"), TEXT("forearm_L"), TEXT("shoulder_L") });
		}
		else if (PartTag == RobotTags::Part_Arm_R())
		{
			HideSet({ TEXT("arm_R"), TEXT("upperarm_R"), TEXT("forearm_R"), TEXT("shoulder_R") });
		}
		else if (PartMap)
		{
			FPartBoneRule Rule;
			if (PartMap->FindRule(PartTag, Rule))
			{
				for (const FName& Prefix : Rule.BonePrefixes)
				{
					MechProceduralAnim::HideBonesByPrefix(AnimMesh, Prefix.ToString());
				}
			}
		}

		if (bFoundBoneLoc)
		{
			// 在断口处生成持续滋滋作响的短路电火花
			if (UWorld* World = GetWorld())
			{
				FActorSpawnParameters SparkParams;
				SparkParams.SpawnCollisionHandlingOverride =
					ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
				if (ARobotDamageSpark* Spark = World->SpawnActor<ARobotDamageSpark>(
						ARobotDamageSpark::StaticClass(), BreakBoneLoc,
						FRotator::ZeroRotator, SparkParams))
				{
					Spark->AttachToActor(this,
						FAttachmentTransformRules::KeepWorldTransform);
					Spark->InitSpark(16.f);
				}
			}
		}
	}

	// 掉落回收物。位置用 Actor 位置加一点随机偏移 —— 精确到骨骼位置
	// 需要把位置一起放进委托，目前垂直切片阶段不值得为此改接口。
	if (SalvageClass)
	{
		// 优先用敌人的自定义掉落表；没有则回退到部位映射表里的价值。
		// 回退是必需的 —— 脚本无法构造 TMap<FGameplayTag,int32> 的键，
		// 所以自定义表默认是空的，不回退就永远不掉落。
		int32 Value = 0;
		if (const int32* Found = SalvageValues.Find(PartTag))
		{
			Value = *Found;
		}
		else if (PartMap)
		{
			FPartBoneRule Rule;
			if (PartMap->FindRule(PartTag, Rule))
			{
				Value = Rule.SalvageValue;
			}
		}

		if (Value > 0)
		{
			if (UWorld* World = GetWorld())
			{
				const FVector Offset(
					FMath::FRandRange(-70.f, 70.f),
					FMath::FRandRange(-70.f, 70.f),
					40.f);
				FActorSpawnParameters Params;
				Params.SpawnCollisionHandlingOverride =
					ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
				if (ASalvagePickup* Pickup = World->SpawnActor<ASalvagePickup>(
						SalvageClass, GetActorLocation() + Offset,
						FRotator::ZeroRotator, Params))
				{
					Pickup->SetValue(Value);
					// 开发期日志：确认"拆部件 → 掉落"这一段真的发生
					UE_LOG(LogTemp, Log, TEXT("[掉落] %s 部位=%s 价值=%d"),
						*GetName(), *PartTag.ToString(), Value);
				}
			}
		}
	}

	UE_LOG(LogTemp, Verbose, TEXT("%s 部位被摧毁：%s"),
		*GetName(), *PartTag.ToString());
}

void ARobotEnemy::HandleActorDisabled()
{
	// 核心被毁，或功能部位全毁但核心存活 —— 两者都进入瘫痪
	EnterDisabledState();

	// 瘫痪而非死亡：保留 Actor 以便玩家交互（修复或拆解）。
	// 是否销毁由游戏层根据玩家选择决定。
	UE_LOG(LogTemp, Log, TEXT("%s 进入瘫痪状态"), *GetName());
}
