#include "RobotCoolantField.h"

#include "RobotCharacter.h"
#include "RobotAttributeSet.h"

#include "ProceduralMeshComponent.h"
#include "Components/SphereComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/StaticMesh.h"

ARobotCoolantField::ARobotCoolantField()
{
	PrimaryActorTick.bCanEverTick = true;

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;

	Surface = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("Surface"));
	Surface->SetupAttachment(Root);
	Surface->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Surface->SetCastShadow(false);
	Surface->bUseAsyncCooking = false;
	Surface->SetTranslucentSortPriority(8);

	Zone = CreateDefaultSubobject<USphereComponent>(TEXT("Zone"));
	Zone->SetupAttachment(Root);
	Zone->InitSphereRadius(PoolRadius);
	Zone->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Zone->SetCollisionResponseToAllChannels(ECR_Ignore);
	Zone->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	Zone->SetGenerateOverlapEvents(true);
	Zone->SetRelativeLocation(FVector(0.f, 0.f, 20.f));

	Glow = CreateDefaultSubobject<UPointLightComponent>(TEXT("Glow"));
	Glow->SetupAttachment(Root);
	Glow->SetRelativeLocation(FVector(0.f, 0.f, 45.f));
	Glow->SetIntensity(9000.f);
	Glow->SetAttenuationRadius(460.f);
	Glow->SetLightColor(FLinearColor(0.12f, 0.92f, 1.0f));
	Glow->SetCastShadows(false);

	// ── 落水水珠：InstancedStaticMesh，一个组件画所有粒子 ──
	Droplets = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Droplets"));
	Droplets->SetupAttachment(Root);
	Droplets->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Droplets->SetCastShadow(false);
	Droplets->SetGenerateOverlapEvents(false);
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(
		TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (SphereMesh.Succeeded())
	{
		Droplets->SetStaticMesh(SphereMesh.Object);
	}
	// 实例数在 BeginPlay 按 MaxDroplets 实际值初始化（构造函数里读不到实例值）
	Droplets->NumCustomDataFloats = 0;
}

void ARobotCoolantField::BeginPlay()
{
	Super::BeginPlay();

	if (Surface)
	{
		// SurfaceMaterial 为空时退回冷却液默认材质；毒液池在关卡里指到 M_Toxic_Fluid。
		UMaterialInterface* Mat = SurfaceMaterial;
		if (!Mat)
		{
			Mat = LoadObject<UMaterialInterface>(nullptr,
				TEXT("/Game/RobotGame/Art/Materials/M_Coolant_Fluid.M_Coolant_Fluid"));
		}
		if (Mat)
		{
			Surface->SetMaterial(0, Mat);
		}
	}

	if (Glow)
	{
		Glow->SetLightColor(GlowColor);
	}

	// 落水水珠：材质用项目冷却液材质（青蓝反光），球体缩放由 DropletRadius 控制。
	// 若没有可用材质就退回引擎默认（至少可见）。
	if (Droplets && Droplets->GetStaticMesh())
	{
		UMaterialInterface* DropMat = LoadObject<UMaterialInterface>(nullptr,
			TEXT("/Game/RobotGame/Art/Materials/M_SplashDroplet.M_SplashDroplet"));
		if (!DropMat)
		{
			DropMat = LoadObject<UMaterialInterface>(nullptr,
				TEXT("/Game/RobotGame/Art/Materials/M_Coolant_Fluid.M_Coolant_Fluid"));
		}
		if (!DropMat)
		{
			DropMat = UMaterial::GetDefaultMaterial(MD_Surface);
		}
		if (DropMat)
		{
			Droplets->SetMaterial(0, DropMat);
		}
		const int32 PoolSize = FMath::Clamp(MaxDroplets, 8, 256);
		DropletPool.SetNumZeroed(PoolSize);
		Droplets->ClearInstances();
	}

	BuildMesh();
}

void ARobotCoolantField::BuildMesh()
{
	if (!Surface)
	{
		return;
	}

	N = FMath::Max(8, GridCells);
	CellSize = (PoolRadius * 2.f) / static_cast<float>(N);

	const int32 VertsPerRow = N + 1;
	const int32 NumVerts = VertsPerRow * VertsPerRow;
	Height.SetNumZeroed(NumVerts);
	Velocity.SetNumZeroed(NumVerts);

	Verts.SetNumUninitialized(NumVerts);
	Normals.SetNumUninitialized(NumVerts);
	UVs.SetNumUninitialized(NumVerts);
	Colors.SetNumUninitialized(NumVerts);
	Tangents.SetNumUninitialized(NumVerts);
	Tris.Reset();

	for (int32 j = 0; j <= N; ++j)
	{
		for (int32 i = 0; i <= N; ++i)
		{
			const int32 Idx = j * VertsPerRow + i;
			const float X = -PoolRadius + i * CellSize;
			const float Y = -PoolRadius + j * CellSize;
			Verts[Idx] = FVector(X, Y, BaseZ);
			Normals[Idx] = FVector::UpVector;
			UVs[Idx] = FVector2D(static_cast<float>(i) / N, static_cast<float>(j) / N);
			Colors[Idx] = FLinearColor(0.f, 0.f, 0.f, 1.f);
			Tangents[Idx] = FProcMeshTangent(1.f, 0.f, 0.f);
		}
	}

	for (int32 j = 0; j < N; ++j)
	{
		for (int32 i = 0; i < N; ++i)
		{
			const int32 a = j * VertsPerRow + i;
			const int32 b = a + 1;
			const int32 c = a + VertsPerRow;
			const int32 d = c + 1;
			Tris.Add(a);
			Tris.Add(c);
			Tris.Add(b);
			Tris.Add(b);
			Tris.Add(c);
			Tris.Add(d);
		}
	}

	Surface->CreateMeshSection_LinearColor(0, Verts, Tris, Normals, UVs, Colors, Tangents, false);
	bMeshReady = true;
	bMeshDirty = true;
}

void ARobotCoolantField::ApplyImpulse(float LocalX, float LocalY, float Strength, float RadiusCm)
{
	const int32 VertsPerRow = N + 1;
	const int32 CenterI = FMath::RoundToInt((LocalX + PoolRadius) / CellSize);
	const int32 CenterJ = FMath::RoundToInt((LocalY + PoolRadius) / CellSize);
	const int32 R = FMath::Max(1, FMath::RoundToInt(RadiusCm / CellSize));

	for (int32 j = CenterJ - R; j <= CenterJ + R; ++j)
	{
		for (int32 i = CenterI - R; i <= CenterI + R; ++i)
		{
			if (i < 1 || j < 1 || i > N - 1 || j > N - 1)
			{
				continue;
			}
			const float dx = (i - CenterI) * CellSize;
			const float dy = (j - CenterJ) * CellSize;
			const float DistSq = dx * dx + dy * dy;
			const float RSq = RadiusCm * RadiusCm;
			if (DistSq > RSq)
			{
				continue;
			}
			const float Falloff = 1.f - DistSq / RSq;
			Velocity[j * VertsPerRow + i] += Strength * Falloff * Falloff;
		}
	}
	bMeshDirty = true;
}

void ARobotCoolantField::StepSim()
{
	const int32 VertsPerRow = N + 1;

	// 波源一：断管入水口，持续注入节律性水柱
	// 冷液池保留这个"活着"的入水口，但强度从 30 降到 6 —— 之前 30 会把
	// 局部水面直接顶到 ±12cm 的上限，整池变成尖刺状绿色山峰。
	// 毒液池是死水：bStagnant 时完全跳过持续波源，只留极轻的环境涟漪。
	TimeAccum += 1.f / 60.f;
	if (!bStagnant)
	{
		// 有可见注水口时，关掉这个"看不见的断管波源"：否则池子里有两处
		// 主扰动，而画面上只有一根管子，浪的来源对不上（r63 实测大浪没有出处）。
		if (!bInflow)
		{
			const float PourPhase = TimeAccum * 9.f;
			const float PourPulse = 0.55f + 0.45f * FMath::Sin(PourPhase);
			ApplyImpulse(-PoolRadius * 0.68f, PoolRadius * 0.34f,
				-0.90f * PourPulse * 6.f, 34.f);
			if (FMath::FRand() < 0.18f)
			{
				ApplyImpulse(
					-PoolRadius * 0.68f + FMath::FRandRange(-40.f, 40.f),
					PoolRadius * 0.34f + FMath::FRandRange(-40.f, 40.f),
					FMath::FRandRange(-3.0f, -1.2f), 18.f);
			}
		}

		// 波源二：边缘渗流，让边缘不至于完全静止
		static float EdgeTimer = 0.f;
		EdgeTimer += 1.f / 60.f;
		if (EdgeTimer > 0.55f)
		{
			EdgeTimer = 0.f;
			const float Angle = FMath::FRandRange(0.f, 2.f * PI);
			const float Rad = PoolRadius * FMath::FRandRange(0.55f, 0.92f);
			ApplyImpulse(FMath::Cos(Angle) * Rad, FMath::Sin(Angle) * Rad,
				FMath::FRandRange(-4.0f, -1.0f), 22.f);
		}
	}
	else
	{
		// 死水：每 3 秒在随机位置极轻地推一下，水面有呼吸感但不会起浪。
		StagnantTimer += 1.f / 60.f;
		if (StagnantTimer > 3.00f)
		{
			StagnantTimer = 0.f;
			const float Angle = FMath::FRandRange(0.f, 2.f * PI);
			const float Rad = PoolRadius * FMath::FRandRange(0.20f, 0.72f);
			ApplyImpulse(FMath::Cos(Angle) * Rad, FMath::Sin(Angle) * Rad,
				FMath::FRandRange(-0.05f, -0.02f), 110.f);
		}
	}

	// 持续注水：入水口把液体不断压进池里，产生连续外扩的涟漪。
	// 与"死水/活水"无关：毒液池也可以有缓慢注入口，只是强度和节律更小。
	if (bInflow)
	{
		InflowTimer += 1.f / 60.f;
		if (InflowTimer >= FMath::Max(0.02f, InflowInterval))
		{
			InflowTimer = 0.f;
			ApplyImpulse(InflowLocal.X, InflowLocal.Y, -InflowStrength,
				InflowRadius);
			// 每次注水脉冲同步喷出一小簇水珠（与物理涟漪同源）
			SpawnDroplets(DropletsPerPulse);
		}
	}

	const float C = WaveSpeedSq;
	const float D = Damping;

	for (int32 j = 1; j < N; ++j)
	{
		for (int32 i = 1; i < N; ++i)
		{
			const int32 Idx = j * VertsPerRow + i;
			const float Avg = (Height[Idx - 1] + Height[Idx + 1] +
				Height[Idx - VertsPerRow] + Height[Idx + VertsPerRow]) * 0.25f;
			float Vel = Velocity[Idx] + (Avg - Height[Idx]) * C * 4.f;
			Vel *= D;
			Velocity[Idx] = Vel;
			float H = Height[Idx] + Vel;
			// 轻微重力回中，避免整片水面被推得越来越高
			H *= 0.9994f;
			Height[Idx] = FMath::Clamp(H, -MaxHeight, MaxHeight);
		}
	}

	// 边界固定为 0：液面在池沿被“钉住”，形成自然的边缘衰减
	for (int32 i = 0; i <= N; ++i)
	{
		Height[i] = 0.f;
		Velocity[i] = 0.f;
		Height[N * VertsPerRow + i] = 0.f;
		Velocity[N * VertsPerRow + i] = 0.f;
		Height[i * VertsPerRow] = 0.f;
		Velocity[i * VertsPerRow] = 0.f;
		Height[i * VertsPerRow + N] = 0.f;
		Velocity[i * VertsPerRow + N] = 0.f;
	}

	// 平流：整张高度场沿主流向平移，涟漪会顺流漂走。
	// 这是"液体在流"最直接的一条线索 —— 只靠法线贴图滚动是看不出方向的。
	if (!FlowVelocity.IsNearlyZero())
	{
		Advect(1.f / 60.f);
	}

	// 注水口每 0.1s 往下压一次，会持续激励网格尺度的棋盘模态；
	// 不压掉的话整池会浮出一层规则的菱形格（近景实测像针织布）。
	SmoothHeight(0.10f);
}

void ARobotCoolantField::SmoothHeight(float Amount)
{
	const int32 VertsPerRow = N + 1;
	HeightSrc = Height;
	for (int32 j = 1; j < N; ++j)
	{
		for (int32 i = 1; i < N; ++i)
		{
			const int32 Idx = j * VertsPerRow + i;
			const float Avg = 0.25f * (HeightSrc[Idx - 1] + HeightSrc[Idx + 1] +
				HeightSrc[Idx - VertsPerRow] + HeightSrc[Idx + VertsPerRow]);
			Height[Idx] = FMath::Lerp(HeightSrc[Idx], Avg, Amount);
		}
	}
}

void ARobotCoolantField::Advect(float Dt)
{
	const int32 VertsPerRow = N + 1;
	const float ShiftX = FlowVelocity.X * Dt / CellSize;
	const float ShiftY = FlowVelocity.Y * Dt / CellSize;
	if (FMath::Abs(ShiftX) < 1e-4f && FMath::Abs(ShiftY) < 1e-4f)
	{
		return;
	}

	HeightSrc = Height;
	VelocitySrc = Velocity;

	for (int32 j = 0; j <= N; ++j)
	{
		for (int32 i = 0; i <= N; ++i)
		{
			const float Sx = FMath::Clamp(i - ShiftX, 0.f, static_cast<float>(N));
			const float Sy = FMath::Clamp(j - ShiftY, 0.f, static_cast<float>(N));
			const int32 X0 = FMath::FloorToInt(Sx);
			const int32 Y0 = FMath::FloorToInt(Sy);
			const int32 X1 = FMath::Min(X0 + 1, N);
			const int32 Y1 = FMath::Min(Y0 + 1, N);
			const float Fx = Sx - X0;
			const float Fy = Sy - Y0;

			const int32 I00 = Y0 * VertsPerRow + X0;
			const int32 I10 = Y0 * VertsPerRow + X1;
			const int32 I01 = Y1 * VertsPerRow + X0;
			const int32 I11 = Y1 * VertsPerRow + X1;

			const float H = FMath::Lerp(
				FMath::Lerp(HeightSrc[I00], HeightSrc[I10], Fx),
				FMath::Lerp(HeightSrc[I01], HeightSrc[I11], Fx), Fy);
			const float V = FMath::Lerp(
				FMath::Lerp(VelocitySrc[I00], VelocitySrc[I10], Fx),
				FMath::Lerp(VelocitySrc[I01], VelocitySrc[I11], Fx), Fy);

			const int32 Idx = j * VertsPerRow + i;
			Height[Idx] = H;
			Velocity[Idx] = V;
		}
	}
}

void ARobotCoolantField::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (!bMeshReady)
	{
		return;
	}

	// 角色涉水：按移动速度在水面注入连续扰动，形成拖尾涟漪
	TArray<AActor*> Pawns;
	UGameplayStatics::GetAllActorsOfClass(this, APawn::StaticClass(), Pawns);
	const FTransform Xf = GetActorTransform();
	for (AActor* A : Pawns)
	{
		APawn* P = Cast<APawn>(A);
		if (!P)
		{
			continue;
		}
		const FVector L = Xf.InverseTransformPosition(P->GetActorLocation());
		if (FMath::Abs(L.X) > PoolRadius * 0.98f || FMath::Abs(L.Y) > PoolRadius * 0.98f)
		{
			continue;
		}
		const float Speed = P->GetVelocity().Size2D();
		if (Speed < 40.f)
		{
			continue;
		}
		const float Strength = -FMath::Clamp(Speed / 380.f, 0.15f, 1.6f) * 0.10f;
		ApplyImpulse(L.X, L.Y, Strength, 30.f);
	}

	SimAccum += FMath::Min(DeltaSeconds, 0.05f);
	int32 Steps = 0;
	while (SimAccum >= 1.f / 60.f && Steps < 3)
	{
		StepSim();
		SimAccum -= 1.f / 60.f;
		++Steps;
	}

	// 水珠每帧按真实 dt 积分（不跟固定步长，避免步长上限时水珠变慢）
	StepDroplets(DeltaSeconds);

	if (bMeshDirty)
	{
		RefreshMesh();
	}

	// 冷光呼吸
	if (Glow)
	{
		const float T = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
		Glow->SetIntensity(GlowIntensity * (0.85f + 0.15f * FMath::Sin(T * 1.7f)));
	}

	// 冷却收益：站在液体中快速排热
	if (Zone)
	{
		TArray<AActor*> Inside;
		Zone->GetOverlappingActors(Inside, ARobotCharacter::StaticClass());
		for (AActor* A : Inside)
		{
			if (ARobotCharacter* Player = Cast<ARobotCharacter>(A))
			{
				if (URobotAttributeSet* Attr = Player->GetAttributeSet())
				{
					const float Before = Attr->GetHeat();
					const float NewHeat = FMath::Max(0.f, Before - HeatCoolPerSecond * DeltaSeconds);
					Attr->SetHeat(NewHeat);

					// 每秒打一条排热日志，便于跑测确认涉水收益真实生效
					static float NextCoolLog = 0.f;
					const float NowT = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
					if (NowT >= NextCoolLog)
					{
						NextCoolLog = NowT + 1.f;
						UE_LOG(LogTemp, Warning, TEXT("[冷却液] 涉水排热 %.1f -> %.1f（本帧 %+.3f，%.0f/s）"),
							Before, NewHeat, NewHeat - Before, HeatCoolPerSecond);
					}
				}
			}
		}
	}
}

void ARobotCoolantField::RefreshMesh()
{
	const int32 VertsPerRow = N + 1;

	for (int32 j = 0; j <= N; ++j)
	{
		for (int32 i = 0; i <= N; ++i)
		{
			const int32 Idx = j * VertsPerRow + i;
			const float H = Height[Idx];
			Verts[Idx] = FVector(-PoolRadius + i * CellSize, -PoolRadius + j * CellSize, BaseZ + H);

			// 法线用 ±2 格的宽模板差分：±1 格会把高度场里的高频干涉纹
			// 原样变成尖锐的斜向划痕（毒液池近景实测像揉皱的锡纸）。
			const int32 iL = FMath::Max(0, i - 2);
			const int32 iR = FMath::Min(N, i + 2);
			const int32 jD = FMath::Max(0, j - 2);
			const int32 jU = FMath::Min(N, j + 2);
			const float Hx = (Height[j * VertsPerRow + iR] - Height[j * VertsPerRow + iL]) /
				((iR - iL) * CellSize);
			const float Hy = (Height[jU * VertsPerRow + i] - Height[jD * VertsPerRow + i]) /
				((jU - jD) * CellSize);
			Normals[Idx] = FVector(-Hx, -Hy, 1.f).GetSafeNormal();

			const float RadiusRatio = FMath::Sqrt(
				Verts[Idx].X * Verts[Idx].X + Verts[Idx].Y * Verts[Idx].Y) / PoolRadius;
			const float Edge = FMath::Clamp((RadiusRatio - 0.78f) / 0.22f, 0.f, 1.f);
			// 泡沫：只留给真正的浪尖。阈值定在 5cm 以上 + 速度项减半：
			// 之前 (|H|-3)*0.12 让全池顶点色都越过材质阈值，蓝色水面上铺满
			// 一层白糖似的白点（r63 实测）。
			const float Foam = FMath::Clamp(
				(FMath::Abs(H) - 5.0f) * 0.10f + FMath::Abs(Velocity[Idx]) * 0.12f +
				Edge * 0.25f, 0.f, 1.f);
			// 入水口冲刷带：以注水口为中心的平滑衰减，写进顶点色 B。
			// 这是纯空间遮罩（不是从高度场导出的），不会带进网格尺度的棋盘纹，
			// 材质用它让落水点周围有一圈翻腾的白沫。
			float Churn = 0.f;
			if (bInflow)
			{
				const float Dx = Verts[Idx].X - InflowLocal.X;
				const float Dy = Verts[Idx].Y - InflowLocal.Y;
				const float D = FMath::Sqrt(Dx * Dx + Dy * Dy);
				Churn = FMath::Clamp(1.f - D / FMath::Max(20.f, InflowRadius * 2.0f),
					0.f, 1.f);
				Churn *= Churn;
			}
			// R = 泡沫强度；G = 水面高度（供材质做深浅分层）；B = 入水口冲刷
			Colors[Idx] = FLinearColor(Foam,
				FMath::Clamp(0.5f - H * 0.02f, 0.f, 1.f), Churn, 1.f);
		}
	}

	Surface->UpdateMeshSection_LinearColor(0, Verts, Normals, UVs, Colors, Tangents);
	bMeshDirty = false;
}

// ─────────────────────────────────────────────
// 落水水珠（第一百一十五轮）
// ─────────────────────────────────────────────

void ARobotCoolantField::SpawnDroplets(int32 Count)
{
	if (!bSplashDroplets || !Droplets || DropletPool.Num() == 0)
	{
		return;
	}

	for (int32 k = 0; k < Count; ++k)
	{
		// 从池里找一个空位
		int32 Slot = INDEX_NONE;
		for (int32 i = 0; i < DropletPool.Num(); ++i)
		{
			if (!DropletPool[i].bAlive)
			{
				Slot = i;
				break;
			}
		}
		if (Slot == INDEX_NONE)
		{
			return;   // 池满，跳过（性能护栏）
		}

		FSplashDroplet& D = DropletPool[Slot];
		// 起点：入水口局部坐标，落在水面上方一点
		const float JitterX = FMath::FRandRange(-12.f, 12.f);
		const float JitterY = FMath::FRandRange(-12.f, 12.f);
		D.Pos = FVector(InflowLocal.X + JitterX, InflowLocal.Y + JitterY,
			BaseZ + 4.f + FMath::FRandRange(0.f, 6.f));

		// 初速度：向上为主 + 水平四散
		const float Ang = FMath::FRandRange(0.f, 2.f * PI);
		const float Spread = DropletSpread * FMath::FRandRange(0.35f, 1.f);
		D.Vel = FVector(FMath::Cos(Ang) * Spread, FMath::Sin(Ang) * Spread,
			DropletLaunchSpeed * FMath::FRandRange(0.65f, 1.25f));
		D.Age = 0.f;
		D.Life = FMath::FRandRange(0.60f, 1.00f);
		D.Scale = FMath::FRandRange(0.55f, 1.45f);   // 大小不一
		D.bAlive = true;
	}
}

void ARobotCoolantField::StepDroplets(float Dt)
{
	if (!bSplashDroplets || DropletPool.Num() == 0)
	{
		return;
	}

	int32 AliveBefore = 0;
	for (const FSplashDroplet& D : DropletPool)
	{
		if (D.bAlive) { ++AliveBefore; }
	}
	// 每 2 秒打印一次存活水珠数（验证粒子真的在生成/消亡，低频避免刷屏）
	{
		static float NextLog = 0.f;
		const float NowT = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
		if (NowT >= NextLog)
		{
			NextLog = NowT + 2.f;
			UE_LOG(LogTemp, Log, TEXT("[水珠] %s 存活=%d 池=%d MaxDroplets=%d"),
				*GetActorLabel(), AliveBefore, DropletPool.Num(), MaxDroplets);
		}
	}

	for (FSplashDroplet& D : DropletPool)
	{
		if (!D.bAlive)
		{
			continue;
		}
		D.Age += Dt;
		// 半隐式欧拉：先更新速度（重力），再更新位置
		D.Vel.Z -= DropletGravity * Dt;
		D.Pos += D.Vel * Dt;

		// 落回水面：消失，并给高度场注入一个极小的涟漪（物理闭环）
		const bool bBelowWater = D.Pos.Z <= BaseZ;
		const bool bExpired = D.Age >= D.Life;
		if (bBelowWater || bExpired)
		{
			D.bAlive = false;
			// 落回水面时注入一个极小的涟漪（物理闭环）。
			// ⚠️ 强度必须很轻：每脉冲多颗水珠，若每颗都强推，整池会被搅出
			//    一层白沫（第一百一十五轮实测）。这里只有 12% 概率、且很弱。
			if (bBelowWater && FMath::FRand() < 0.12f)
			{
				ApplyImpulse(D.Pos.X, D.Pos.Y, -0.12f, 10.f);
			}
		}
	}
	RefreshDroplets();
}

void ARobotCoolantField::RefreshDroplets()
{
	if (!Droplets)
	{
		return;
	}
	Droplets->ClearInstances();
	const float S = DropletRadius / 50.f;   // 引擎 Sphere 半径 50cm，缩放到目标半径
	for (const FSplashDroplet& D : DropletPool)
	{
		if (!D.bAlive)
		{
			continue;
		}
		// 越接近寿命尾端越小（轻微收缩，避免突然消失）
		const float T = FMath::Clamp(D.Age / FMath::Max(D.Life, 0.01f), 0.f, 1.f);
		const float Shrink = 1.f - 0.5f * T * T;
		const float Sc = S * D.Scale * Shrink;
		const FTransform Xf(FRotator::ZeroRotator, D.Pos,
			FVector(Sc, Sc, Sc));
		Droplets->AddInstance(Xf);
	}
}
