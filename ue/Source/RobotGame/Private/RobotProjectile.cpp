#include "RobotProjectile.h"

#include "PartDamageComponent.h"
#include "PartMapData.h"
#include "RobotPlayerController.h"
#include "RobotSfx.h"

#include "Components/PointLightComponent.h"
#include "Components/PoseableMeshComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/DamageEvents.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	/**
	 * 计算两根 3D 空间线段之间的最短距离平方（Dan Sunday 闭式算法，无开方、无除零）。
	 */
	static float DistSqSegmentToSegment(const FVector& P1, const FVector& P2,
		const FVector& Q1, const FVector& Q2)
	{
		const FVector u = P2 - P1;
		const FVector v = Q2 - Q1;
		const FVector w = P1 - Q1;
		const float a = FVector::DotProduct(u, u);
		const float b = FVector::DotProduct(u, v);
		const float c = FVector::DotProduct(v, v);
		const float d = FVector::DotProduct(u, w);
		const float e = FVector::DotProduct(v, w);
		const float D = a * c - b * b;

		float sc, sN, sD = D;
		float tc, tN, tD = D;

		if (D < 1e-4f)
		{
			sN = 0.0f;
			sD = 1.0f;
			tN = e;
			tD = c;
		}
		else
		{
			sN = (b * e - c * d);
			tN = (a * e - b * d);
			if (sN < 0.0f)
			{
				sN = 0.0f;
				tN = e;
				tD = c;
			}
			else if (sN > sD)
			{
				sN = sD;
				tN = e + b;
				tD = c;
			}
		}

		if (tN < 0.0f)
		{
			tN = 0.0f;
			if (-d < 0.0f) sN = 0.0f;
			else if (-d > a) sN = sD;
			else { sN = -d; sD = a; }
		}
		else if (tN > tD)
		{
			tN = tD;
			if ((-d + b) < 0.0f) sN = 0.0f;
			else if ((-d + b) > a) sN = sD;
			else { sN = (-d + b); sD = a; }
		}

		sc = (FMath::Abs(sN) < 1e-4f ? 0.0f : sN / sD);
		tc = (FMath::Abs(tN) < 1e-4f ? 0.0f : tN / tD);

		const FVector dP = w + (sc * u) - (tc * v);
		return dP.SizeSquared();
	}

	/**
	 * 命中点落在胶囊体上时，沿弹道射线穿越胶囊内部，寻找相交/最近的**肢体骨骼骨段**。
	 *
	 * 为什么升级为"射线-骨段距离"：
	 *   以前只算胶囊表面撞击点到关节单点的欧氏距离。当玩家瞄准小臂射击时，
	 *   撞击点在胶囊表面，距离肩关节反而比腕关节更近，经常把手腕/小臂误判为肩膀/躯干。
	 *   升级后：弹丸从命中点沿 ShotDir 刺入 150cm（贯穿胶囊体积），
	 *   与每根骨骼及其父节点构成的**三维骨段胶囊**求最短相交距离，
	 *   打中手臂就是手臂、打中小腿就是小腿，精准支持瞄准弱点拆解。
	 */
	FName FindNearestPartBone(AActor* Target, const FVector& ImpactPoint,
		const FVector& ShotDir, const UPartDamageComponent* Parts)
	{
		if (!Target || !Parts || !Parts->PartMap)
		{
			return NAME_None;
		}

		UPoseableMeshComponent* Mesh =
			Target->FindComponentByClass<UPoseableMeshComponent>();
		if (!Mesh)
		{
			return NAME_None;
		}

		TArray<FString> Prefixes;
		for (const FPartBoneRule& Rule : Parts->PartMap->Rules)
		{
			for (const FName& P : Rule.BonePrefixes)
			{
				Prefixes.Add(P.ToString());
			}
		}
		if (Prefixes.Num() == 0)
		{
			return NAME_None;
		}

		USkeletalMesh* SkinnedAsset = Cast<USkeletalMesh>(Mesh->GetSkinnedAsset());
		const FReferenceSkeleton* Ref = SkinnedAsset ? &SkinnedAsset->GetRefSkeleton() : nullptr;

		// 弹道贯穿射线：从胶囊表面起，向内穿深 160cm（胶囊直径 120cm）
		const FVector RayStart = ImpactPoint;
		const FVector RayEnd = ImpactPoint + ShotDir * 160.f;

		const int32 NumBones = Mesh->GetNumBones();
		FName Best = NAME_None;
		float BestSurfaceDistSq = TNumericLimits<float>::Max();

		for (int32 i = 0; i < NumBones; ++i)
		{
			const FName BoneName = Mesh->GetBoneName(i);
			const FString BoneStr = BoneName.ToString();
			bool bRoutable = false;
			for (const FString& P : Prefixes)
			{
				if (BoneStr.StartsWith(P, ESearchCase::IgnoreCase))
				{
					bRoutable = true;
					break;
				}
			}
			if (!bRoutable)
			{
				continue;
			}

			// 获取子骨骼世界坐标
			const FVector ChildLoc = Mesh->GetBoneLocationByName(
				BoneName, EBoneSpaces::WorldSpace);

			// 获取父骨骼世界坐标，构成三维肢体骨段
			FVector ParentLoc = ChildLoc;
			if (Ref)
			{
				const int32 ParentIdx = Ref->GetParentIndex(i);
				if (ParentIdx != INDEX_NONE)
				{
					ParentLoc = Mesh->GetBoneLocationByName(
						Ref->GetBoneName(ParentIdx), EBoneSpaces::WorldSpace);
				}
			}

			// 计算弹道射线到该骨段的最短距离平方
			const float DistSq = DistSqSegmentToSegment(RayStart, RayEnd, ParentLoc, ChildLoc);

			// 部位截面粗细权重补偿（核心粗 ~30cm，四肢细 ~14cm）
			float PartRadius = 14.f;
			if (BoneStr.Contains(TEXT("torso")) || BoneStr.Contains(TEXT("core")))
			{
				PartRadius = 30.f;
			}
			else if (BoneStr.Contains(TEXT("thigh")) || BoneStr.Contains(TEXT("shin")) || BoneStr.Contains(TEXT("leg")))
			{
				PartRadius = 18.f;
			}

			const float Dist = FMath::Sqrt(DistSq);
			const float SurfaceDist = FMath::Max(0.f, Dist - PartRadius);
			const float SurfaceDistSq = SurfaceDist * SurfaceDist;

			if (SurfaceDistSq < BestSurfaceDistSq)
			{
				BestSurfaceDistSq = SurfaceDistSq;
				Best = BoneName;
			}
		}
		return Best;
	}
}

ARobotProjectile::ARobotProjectile()
{
	// 需要 Tick：枪口闪光要在 FlashDuration 内衰减掉
	PrimaryActorTick.bCanEverTick = true;

	Collision = CreateDefaultSubobject<USphereComponent>(TEXT("Collision"));
	Collision->InitSphereRadius(12.f);
	Collision->SetCollisionProfileName(TEXT("BlockAllDynamic"));
	Collision->SetNotifyRigidBodyCollision(true);
	// 对角色只做重叠，不参与物理阻挡 —— 详见头文件里的说明。
	Collision->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	// 也不挡 Visibility：否则飞行中的弹丸会挡住敌人的视线射线，
	// 表现为"敌人时而有视线、时而没有"地每 0.15 秒抽搐一次。
	Collision->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
	Collision->SetGenerateOverlapEvents(true);
	RootComponent = Collision;

	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	Mesh->SetupAttachment(Collision);
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	// ★ 2026-10-26：弹丸从"拉伸的引擎球体"换成 Blender 建的
	//   SM_Bolt_Round（30cm 卵形弹 + 曳光带 + 船尾，见 tools/blender/build_bolt.py）。
	//   旧做法是把 100cm 的球体按 (0.50, 0.055, 0.055) 拉成一根 50cm×5.5cm 的
	//   发光长条 —— 远看是一道线，近看是根没有细节的胶囊，所以这次直接做网格。
	//   网格约定：+X 是弹头方向，正好等于 ProjectileMovement 的前向。
	//
	//   构造函数里设一次只是给新蓝图打底；BP_Projectile_C 的 CDO 可能把
	//   旧的 Sphere 序列化下来了，真正的替换在 BeginPlay 里再做一次。
	static ConstructorHelpers::FObjectFinder<UStaticMesh> BoltMesh(
		TEXT("/Game/RobotGame/Art/Props/SM_Bolt_Round.SM_Bolt_Round"));
	if (BoltMesh.Succeeded())
	{
		Mesh->SetStaticMesh(BoltMesh.Object);
	}
	else
	{
		// 资产还没导入时的兜底：宁可先看到一个球，也不要灰棋盘格方块。
		static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(
			TEXT("/Engine/BasicShapes/Sphere.Sphere"));
		if (SphereMesh.Succeeded())
		{
			Mesh->SetStaticMesh(SphereMesh.Object);
		}
	}
	// 网格本身已经是最终尺寸（29.9cm 长），不需要再拉伸。
	Mesh->SetRelativeScale3D(FVector(1.0f));

	// 枪口闪光。挂在碰撞体上（= 出弹点），出生瞬间拉满强度再快速衰减。
	// 用点光源而不是发光材质球：材质要资产配合，点光源不依赖任何资产、
	// 一定有效，而且不会被蓝图 CDO 的序列化吃掉。
	MuzzleLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("MuzzleLight"));
	MuzzleLight->SetupAttachment(Collision);
	MuzzleLight->SetMobility(EComponentMobility::Movable);
	MuzzleLight->SetCastShadows(false);
	MuzzleLight->SetAttenuationRadius(520.f);
	MuzzleLight->SetIntensity(0.f);

	// 曳光常亮光：从出膛到命中一直在，给地面扫出一条冷光。
	// 强度比枪口闪光低一个数量级，半径也小，避免整片场景被弹丸打亮。
	TracerLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("TracerLight"));
	TracerLight->SetupAttachment(Collision);
	TracerLight->SetMobility(EComponentMobility::Movable);
	TracerLight->SetCastShadows(false);
	TracerLight->SetAttenuationRadius(300.f);
	TracerLight->SetIntensity(0.f);

	Movement = CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("Movement"));
	Movement->InitialSpeed = 2400.f;
	Movement->MaxSpeed = 2400.f;
	Movement->bRotationFollowsVelocity = true;
	Movement->ProjectileGravityScale = 0.f;

	InitialLifeSpan = LifeSeconds;
}

static const TCHAR* kBoltShellMat =
	TEXT("/Game/RobotGame/Art/Materials/M_Bolt_Shell.M_Bolt_Shell");
static const TCHAR* kBoltTrimMat =
	TEXT("/Game/RobotGame/Art/Materials/M_Bolt_Trim.M_Bolt_Trim");
static const TCHAR* kBoltGlowPlayerMat =
	TEXT("/Game/RobotGame/Art/Materials/M_Bolt_Glow_Player.M_Bolt_Glow_Player");
static const TCHAR* kBoltGlowEnemyMat =
	TEXT("/Game/RobotGame/Art/Materials/M_Bolt_Glow_Enemy.M_Bolt_Glow_Enemy");

// 旧的两支 Unlit 材质保留作兜底：万一新材质还没导入，
// 至少弹丸仍然是青白/橙金的一道光，而不是灰球。
static const TCHAR* kBoltLegacyPlayer =
	TEXT("/Game/RobotGame/Art/Materials/M_Bolt_Player.M_Bolt_Player");
static const TCHAR* kBoltLegacyEnemy =
	TEXT("/Game/RobotGame/Art/Materials/M_Bolt_Enemy.M_Bolt_Enemy");

static const TCHAR* kBoltMeshPath =
	TEXT("/Game/RobotGame/Art/Props/SM_Bolt_Round.SM_Bolt_Round");

static UMaterialInterface* LoadCachedMat(
	TWeakObjectPtr<UMaterialInterface>& Cache, const TCHAR* Path)
{
	if (!Cache.IsValid())
	{
		Cache = LoadObject<UMaterialInterface>(nullptr, Path);
	}
	return Cache.Get();
}

/**
 * 保证运行时用的是新弹丸网格。
 *
 * BP_Projectile_C 是从 ARobotProjectile 派生的蓝图，它的 CDO 里可能
 * 序列化了旧的 /Engine/BasicShapes/Sphere。只改 C++ 构造函数对已经存在
 * 的蓝图不生效（缩放就踩过这个坑），所以这里再强制换一次。
 */
static void ApplyBoltMesh(UStaticMeshComponent* InMesh)
{
	if (!InMesh)
	{
		return;
	}
	static TWeakObjectPtr<UStaticMesh> BoltMesh;
	if (!BoltMesh.IsValid())
	{
		BoltMesh = LoadObject<UStaticMesh>(nullptr, kBoltMeshPath);
	}
	if (BoltMesh.IsValid() && InMesh->GetStaticMesh() != BoltMesh.Get())
	{
		InMesh->SetStaticMesh(BoltMesh.Get());
	}
	// 网格是 1:1 实尺（29.9cm），运行时再设一次防止蓝图 CDO 存着旧缩放。
	InMesh->SetRelativeScale3D(FVector(1.0f));
}

/**
 * 按阵营绑定三个材质槽：
 *   0 = 弹壳（PBR 钛合金，共用）
 *   1 = 曳光带（Unlit 等离子，玩家青白 / 敌人橙金）
 *   2 = 抛光环（亮钢，共用）
 *
 * 发光面在 Blender 里就是独立的几何+材质槽，不靠贴图 UV 遮罩，
 * 所以无论贴图怎么采样都不会"发光带跑到弹头上"。
 */
static void ApplyFactionBoltMaterials(UStaticMeshComponent* InMesh, bool bFromPlayer)
{
	if (!InMesh)
	{
		return;
	}
	static TWeakObjectPtr<UMaterialInterface> Shell;
	static TWeakObjectPtr<UMaterialInterface> Trim;
	static TWeakObjectPtr<UMaterialInterface> GlowP;
	static TWeakObjectPtr<UMaterialInterface> GlowE;
	static TWeakObjectPtr<UMaterialInterface> LegacyP;
	static TWeakObjectPtr<UMaterialInterface> LegacyE;

	UMaterialInterface* ShellMat = LoadCachedMat(Shell, kBoltShellMat);
	UMaterialInterface* TrimMat = LoadCachedMat(Trim, kBoltTrimMat);
	UMaterialInterface* GlowMat = LoadCachedMat(
		bFromPlayer ? GlowP : GlowE,
		bFromPlayer ? kBoltGlowPlayerMat : kBoltGlowEnemyMat);
	if (!GlowMat)
	{
		GlowMat = LoadCachedMat(
			bFromPlayer ? LegacyP : LegacyE,
			bFromPlayer ? kBoltLegacyPlayer : kBoltLegacyEnemy);
	}

	if (InMesh->GetNumMaterials() >= 2)
	{
		if (ShellMat) { InMesh->SetMaterial(0, ShellMat); }
		if (GlowMat)  { InMesh->SetMaterial(1, GlowMat); }
		if (TrimMat)  { InMesh->SetMaterial(2, TrimMat); }
	}
	else if (GlowMat)
	{
		// 兜底球体只有一个槽，只能整颗发光。
		InMesh->SetMaterial(0, GlowMat);
	}
}

void ARobotProjectile::BeginPlay()
{
	Super::BeginPlay();
	Collision->OnComponentHit.AddDynamic(this, &ARobotProjectile::OnHit);
	Collision->OnComponentBeginOverlap.AddDynamic(this, &ARobotProjectile::OnOverlap);

	// 蓝图 CDO 会覆盖构造函数里设过的碰撞响应（本项目踩过多次），
	// 所以在 BeginPlay 再设一遍 —— 这里才是真正决定运行时行为的时刻。
	Collision->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	Collision->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
	Collision->SetGenerateOverlapEvents(true);

	// 弹体网格与材质：BP_Projectile_C 的 CDO 可能还存着旧的引擎球体，
	// 这里强制换成 SM_Bolt_Round，并先按"玩家"配色打底 ——
	// 真正的阵营配色在 InitProjectile 里（SpawnActor 先 BeginPlay 后 Init）。
	if (Mesh)
	{
		ApplyBoltMesh(Mesh);
		ApplyFactionBoltMaterials(Mesh, true);
	}
}

void ARobotProjectile::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (FlashRemaining > 0.f && MuzzleLight)
	{
		FlashRemaining -= DeltaSeconds;
		const float T = FMath::Clamp(
			FlashRemaining / FMath::Max(FlashDuration, 0.001f), 0.f, 1.f);
		// 平方衰减：前段亮、后段收得干脆，更像"一闪"
		MuzzleLight->SetIntensity(FlashIntensity * T * T);
	}
}

void ARobotProjectile::InitProjectile(float InDamage, float InSpeed,
                                      AActor* InInstigatorActor)
{
	Damage = InDamage;
	if (Movement)
	{
		Movement->InitialSpeed = InSpeed;
		Movement->MaxSpeed = InSpeed;
		Movement->Velocity = GetActorForwardVector() * InSpeed;
	}
	if (InInstigatorActor)
	{
		SetInstigator(Cast<APawn>(InInstigatorActor));
		SetOwner(InInstigatorActor);
		// 不与自己碰撞，否则会在枪口处立刻自爆
		Collision->IgnoreActorWhenMoving(InInstigatorActor, true);
	}

	// 枪口闪光 / 曳光 / 弹体配色：一眼看出这一发是谁打的
	const APawn* InstigatorPawn = Cast<APawn>(InInstigatorActor);
	const bool bFromPlayer = InstigatorPawn && InstigatorPawn->IsPlayerControlled();
	const FLinearColor FactionColor = bFromPlayer
		? FLinearColor(0.30f, 0.86f, 1.00f)     // 玩家：青蓝
		: FLinearColor(1.00f, 0.42f, 0.10f);    // 敌人：橙金

	if (MuzzleLight)
	{
		MuzzleLight->SetLightColor(FactionColor);
		MuzzleLight->SetIntensity(FlashIntensity);
	}

	// 曳光常亮：弹丸飞出去之后继续把地面扫亮，而不是出膛 0.08 秒就熄。
	if (TracerLight)
	{
		TracerLight->SetLightColor(FactionColor);
		// 30 发在天上时 30 盏点光会明显吃性能，所以亮度/半径都压到
		// "刚好照亮弹体周围的一条地面"的程度，主视觉还是靠自发光带。
		TracerLight->SetIntensity(bFromPlayer ? 1600.f : 1300.f);
	}

	if (Mesh)
	{
		ApplyBoltMesh(Mesh);
		ApplyFactionBoltMaterials(Mesh, bFromPlayer);

		// 只记录前 6 发，确认网格/材质/缩放真的落到了运行时对象上。
		static int32 BoltLogCount = 0;
		if (BoltLogCount < 6)
		{
			++BoltLogCount;
			UE_LOG(LogTemp, Warning,
				TEXT("[弹丸] 玩家=%d 网格=%s 槽0=%s 槽1=%s 缩放=%s"),
				bFromPlayer ? 1 : 0,
				Mesh->GetStaticMesh() ? *Mesh->GetStaticMesh()->GetName() : TEXT("无"),
				Mesh->GetMaterial(0) ? *Mesh->GetMaterial(0)->GetName() : TEXT("无"),
				Mesh->GetMaterial(1) ? *Mesh->GetMaterial(1)->GetName() : TEXT("无"),
				*Mesh->GetRelativeScale3D().ToString());
		}
	}
	FlashRemaining = FlashDuration;
}

void ARobotProjectile::OnHit(UPrimitiveComponent* HitComp, AActor* OtherActor,
	UPrimitiveComponent* OtherComp, FVector NormalImpulse, const FHitResult& Hit)
{
	ProcessHit(OtherActor, OtherComp, Hit.ImpactPoint, Hit.ImpactNormal, Hit.BoneName);
}

void ARobotProjectile::OnOverlap(UPrimitiveComponent* OverlappedComp,
	AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex,
	bool bFromSweep, const FHitResult& SweepResult)
{
	if (!OtherActor || OtherActor == GetOwner())
	{
		return;
	}

	// 扫掠重叠能拿到真实命中点；非扫掠重叠（出生时已重叠）用当前位置兜底。
	const FVector ImpactPoint = bFromSweep
		? static_cast<FVector>(SweepResult.ImpactPoint) : GetActorLocation();
	const FVector ImpactNormal = bFromSweep
		? static_cast<FVector>(SweepResult.ImpactNormal)
		: -GetVelocity().GetSafeNormal();

	ProcessHit(OtherActor, OtherComp, ImpactPoint, ImpactNormal,
		bFromSweep ? SweepResult.BoneName : NAME_None);
}

void ARobotProjectile::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	// 弹道实测埋点（-DebugAim）：追踪"开了火但没产生命中"的弹丸结局。
	// 排查 107 发开火 vs 100 条实弹事件之间那 7 发的去向。
	if (FParse::Param(FCommandLine::Get(), TEXT("DebugAim")) && !bImpactProcessed)
	{
		UE_LOG(LogTemp, Log,
			TEXT("[漏弹] 未命中即结束 位置=(%.0f,%.0f,%.0f) 速度=%.0f 寿命=%.2f 原因=%d"),
			GetActorLocation().X, GetActorLocation().Y, GetActorLocation().Z,
			GetVelocity().Size(), GetGameTimeSinceCreation(),
			static_cast<int32>(EndPlayReason));
	}
	Super::EndPlay(EndPlayReason);
}

void ARobotProjectile::ProcessHit(AActor* OtherActor, UPrimitiveComponent* OtherComp,
	const FVector& ImpactPoint, const FVector& ImpactNormal, FName BoneName)
{
	if (!OtherActor || OtherActor == GetOwner() || bImpactProcessed)
	{
		return;
	}

	// ── 友军过滤 ──
	// 敌人开火时不应该打中自己人（实测 76 发里 5 发误伤友军，观感像内讧）。
	// 同一阵营的机体直接穿过：不结算伤害、不标记 bImpactProcessed，
	// 让弹丸继续飞向真正的目标。
	{
		// 只有"和射手同阵营的 Pawn"才穿透。场景几何（非 Pawn）必须正常结算，
		// 否则弹丸会穿过墙壁飞满 3 秒停在空中（r172 实测：4 发速度归零悬空）。
		const APawn* OtherPawn = Cast<APawn>(OtherActor);
		const APawn* ShooterPawn = Cast<APawn>(
			GetInstigator() ? GetInstigator() : GetOwner());
		if (OtherPawn && ShooterPawn &&
			OtherPawn->IsPlayerControlled() == ShooterPawn->IsPlayerControlled())
		{
			return;   // 同阵营 → 穿透
		}
	}

	bImpactProcessed = true;

	// 弹道实测埋点（-DebugAim）：这一发到底打中了谁 —— 判定的是**真实碰撞**，
	// 而不是开火瞬间的理想射线。用它统计移动目标下的真实命中率。
	if (FParse::Param(FCommandLine::Get(), TEXT("DebugAim")))
	{
		UE_LOG(LogTemp, Log, TEXT("[实弹] 命中=%s 骨骼=%s 点=(%.0f,%.0f,%.0f)"),
			*OtherActor->GetName(), *BoneName.ToString(),
			ImpactPoint.X, ImpactPoint.Y, ImpactPoint.Z);
	}

	FGameplayTag HitPart;
	bool bBroke = false;

	// 弹丸此刻的飞行方向（射手 → 目标）。
	FVector ShotDir = Movement ? Movement->Velocity : FVector::ZeroVector;
	if (ShotDir.IsNearlyZero())
	{
		ShotDir = GetActorForwardVector();
	}
	ShotDir = ShotDir.GetSafeNormal();

	// 部位伤害路由：骨骼名 → 部位标签 → 扣该部位的血
	if (UPartDamageComponent* Parts =
			OtherActor->FindComponentByClass<UPartDamageComponent>())
	{
		// ── 骨骼名解析 ──
		// 弹丸打中胶囊体时，Sweep 结果无骨骼名，沿弹道贯穿射线与机体骨段做精确求交判定。
		const bool bBoneFromCapsule = BoneName.IsNone();
		if (bBoneFromCapsule)
		{
			BoneName = FindNearestPartBone(OtherActor, ImpactPoint, ShotDir, Parts);
		}

		float Dealt = 0.f;
		bool bCoreDead = false;
		HitPart = Parts->ApplyDamageByBoneEx(
			BoneName, Damage, Dealt, bBroke, bCoreDead, ShotDir);
		const float Exposure = HitPart.IsValid()
			? Parts->GetExposureMultiplier(HitPart, ShotDir)
			: 1.f;

		// 诊断：部位命中日志（战斗验证用；查看请开 LogCmds=LogTemp Verbose）
		if (GetInstigator() && GetInstigator()->IsPlayerControlled())
		{
			UE_LOG(LogTemp, Verbose,
				TEXT("[命中] 目标=%s 组件=%s 骨骼=%s(%s) → 部位=%s 倍率=%.2f 扣血=%.0f%s"),
				*OtherActor->GetName(), *GetNameSafe(OtherComp), *BoneName.ToString(),
				bBoneFromCapsule ? TEXT("胶囊兜底") : TEXT("直接骨骼"),
				HitPart.IsValid() ? *HitPart.ToString() : TEXT("无效"),
				Exposure, Dealt, bBroke ? TEXT("（拆解！）") : TEXT(""));
		}

		// ── 命中反馈：只有"玩家打中了敌人"才触发准心命中标记 ──
		//
		// 判定三件事：① 造成了有效部位伤害（打空气/打地板不闪）；
		// ② 发射者是玩家控制的（敌人的弹丸打中玩家不走这条路 ——
		//    玩家的受击反馈由角色自己的 OnPartDamaged 驱动）；
		// ③ 打完这一发之后核心是否已被摧毁（决定标记颜色）。
		const APawn* Shooter = GetInstigator();
		const bool bPlayerShot = Shooter && Shooter->IsPlayerControlled();
		if (HitPart.IsValid() && bPlayerShot)
		{
			if (ARobotPlayerController* PC = Cast<ARobotPlayerController>(
					UGameplayStatics::GetPlayerController(this, 0)))
			{
				PC->NotifyHitConfirmed(bCoreDead, ImpactPoint);

				// 已毁部位不弹数字：那一枪没有收益，玩家需要知道
				if (Dealt > 0.f)
				{
					PC->PushDamageNumber(ImpactPoint, Dealt, HitPart, bBroke,
						Exposure);
				}
			}
		}
	}
	else
	{
		// 目标没有部位系统（例如战术燃料桶、可破坏掩体），通过标准 TakeDamage 路由伤害
		FPointDamageEvent PointDmg(Damage, FHitResult(OtherActor, OtherComp, ImpactPoint, ImpactNormal), ShotDir, nullptr);
		OtherActor->TakeDamage(Damage, PointDmg, GetInstigator() ? GetInstigator()->GetController() : nullptr, this);
	}

	if (!bDestroyOnHit)
	{
		return;
	}

	// 命中音效：拆解部位时触发高昂爆裂音，暴击核心时触发低沉金属穿透音，普通命中保留清脆撞击
	if (bBroke)
	{
		RobotSfx::PlayAt(this, TEXT("SFX_Destroy"), ImpactPoint, 0.95f, 1.15f, true);
	}
	else if (HitPart == RobotTags::Part_Core())
	{
		RobotSfx::PlayAt(this, TEXT("SFX_Impact"), ImpactPoint, 0.90f, 0.72f, true);
	}
	else
	{
		RobotSfx::PlayAt(this, TEXT("SFX_Impact"), ImpactPoint, 0.70f, 1.05f, true);
	}

	// ── 命中特效：把弹体就地"变成"一簇火花，而不是直接消失 ──
	//
	// 直接 Destroy() 会让命中毫无反馈（尤其打在墙上时，画面里什么都看不到）。
	// 这里复用已有的弹体与点光源：停下、贴到命中点、换成暖色、迅速熄灭。
	// 代价为零（不新增任何资产），但"打中了"这件事立刻变得可见。
	if (MuzzleLight)
	{
		MuzzleLight->SetLightColor(FLinearColor(1.0f, 0.72f, 0.30f));
		MuzzleLight->SetAttenuationRadius(280.f);
		// Tick 里按 FlashIntensity×T² 衰减，所以这里直接缩放峰值即可
		FlashIntensity *= 0.55f;
		MuzzleLight->SetIntensity(FlashIntensity);
	}
	if (Movement)
	{
		Movement->StopMovementImmediately();
		Movement->SetComponentTickEnabled(false);
	}
	if (TracerLight)
	{
		TracerLight->SetIntensity(0.f);
	}
	if (Mesh)
	{
		// 30cm 的弹体缩到 15cm，读成一团被压扁的金属火花。
		Mesh->SetRelativeScale3D(FVector(0.50f, 0.50f, 0.50f));
	}
	SetActorLocation(ImpactPoint + ImpactNormal * 4.f);
	Collision->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	// 复用 FlashRemaining 做余烬衰减，0.09 秒后自动销毁
	FlashDuration = 0.09f;
	FlashRemaining = FlashDuration;
	SetLifeSpan(0.09f);
}
