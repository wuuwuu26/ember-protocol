#include "SalvagePickup.h"

#include "RobotCharacter.h"
#include "RobotSfx.h"

#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "GameFramework/RotatingMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/World.h"

ASalvagePickup::ASalvagePickup()
{
	PrimaryActorTick.bCanEverTick = true;

	Collision = CreateDefaultSubobject<USphereComponent>(TEXT("Collision"));
	Collision->InitSphereRadius(30.f);
	Collision->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Collision->SetCollisionResponseToAllChannels(ECR_Ignore);
	Collision->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	Collision->SetGenerateOverlapEvents(true);
	RootComponent = Collision;

	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	Mesh->SetupAttachment(Collision);
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(
		TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (CubeMesh.Succeeded())
	{
		Mesh->SetStaticMesh(CubeMesh.Object);
		Mesh->SetRelativeScale3D(FVector(0.32f));
		// 倾斜 45°：旋转起来像悬浮的能量菱晶，比正方体更有科幻拾取物特征
		Mesh->SetRelativeRotation(FRotator(45.f, 0.f, 45.f));
	}

	BeaconLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("BeaconLight"));
	BeaconLight->SetupAttachment(Collision);
	BeaconLight->SetIntensity(5000.f);
	BeaconLight->SetAttenuationRadius(260.f);
	BeaconLight->SetLightColor(FLinearColor(1.0f, 0.72f, 0.22f));
	BeaconLight->SetCastShadows(false);

	Spin = CreateDefaultSubobject<URotatingMovementComponent>(TEXT("Spin"));
	Spin->RotationRate = FRotator(0.f, 140.f, 0.f);
}

void ASalvagePickup::BeginPlay()
{
	Super::BeginPlay();

	// 拾取物自发光材质：金琥珀色能量核心，夜景地面上极其醒目
	if (Mesh)
	{
		if (UMaterialInterface* Mat = LoadObject<UMaterialInterface>(nullptr,
				TEXT("/Game/RobotGame/Art/Materials/M_Salvage_Core.M_Salvage_Core")))
		{
			Mesh->SetMaterial(0, Mat);
		}
	}

	if (LifeSeconds > 0.f)
	{
		SetLifeSpan(LifeSeconds);
	}
}

void ASalvagePickup::SetValue(int32 InValue)
{
	Value = FMath::Max(0, InValue);
}

void ASalvagePickup::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (bCollected)
	{
		return;
	}

	// 悬浮上下浮动，强化拾取物的漂浮感
	BobTime += DeltaSeconds;
	if (Mesh)
	{
		Mesh->SetRelativeLocation(FVector(0.f, 0.f, FMath::Sin(BobTime * 3.5f) * 6.f));
	}

	// 找玩家：优先复用已锁定目标，否则每帧取一次（拾取物数量少，开销可接受）
	if (!AttractTarget)
	{
		AttractTarget = UGameplayStatics::GetPlayerPawn(this, 0);
	}
	AActor* Player = AttractTarget;
	if (!Player)
	{
		return;
	}

	const FVector MyLoc = GetActorLocation();
	const FVector PlayerLoc = Player->GetActorLocation();
	const float Distance = FVector::Dist(MyLoc, PlayerLoc);

	if (Distance <= PickupRadius)
	{
		TryCollect(Player);
		return;
	}

	// 吸附：越近拉得越快，让拾取有"被吸进去"的手感
	if (Distance <= AttractRadius)
	{
		const float Alpha = 1.f - (Distance / AttractRadius);
		const FVector Dir = (PlayerLoc - MyLoc).GetSafeNormal();
		AddActorWorldOffset(Dir * AttractSpeed * Alpha * DeltaSeconds, true);
	}
}

bool ASalvagePickup::TryCollect(AActor* Collector)
{
	if (bCollected || !Collector)
	{
		return false;
	}

	// 只有玩家能拾取。用 ARobotCharacter 而不是接口，因为目前只有玩家是它。
	if (ARobotCharacter* Robot = Cast<ARobotCharacter>(Collector))
	{
		Robot->AddSalvage(Value);
		// 拾取音效：两音上行的小铃铛 —— 收集的正反馈
		RobotSfx::PlayAt(this, TEXT("SFX_Pickup"), GetActorLocation(),
			0.75f, 1.f, true);
		// 开发期日志：确认"拾取 → 计数"这一段真的发生
		UE_LOG(LogTemp, Log, TEXT("[拾取] 价值=%d 累计=%d"),
			Value, Robot->GetSalvage());
		bCollected = true;
		Destroy();
		return true;
	}
	return false;
}
