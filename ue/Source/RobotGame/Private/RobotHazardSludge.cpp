#include "RobotHazardSludge.h"

#include "RobotCharacter.h"
#include "RobotEnemy.h"
#include "RobotAttributeSet.h"
#include "RobotSfx.h"

#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "UObject/ConstructorHelpers.h"

ARobotHazardSludge::ARobotHazardSludge()
{
	PrimaryActorTick.bCanEverTick = true;

	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));

	SludgeMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SludgeMesh"));
	SludgeMesh->SetupAttachment(RootComponent);
	SludgeMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	SludgeMesh->SetCastShadow(false);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> MeshFinder(
		TEXT("/Game/RobotGame/Art/Environment/SM_Env_SludgePool.SM_Env_SludgePool"));
	if (MeshFinder.Succeeded())
	{
		SludgeMesh->SetStaticMesh(MeshFinder.Object);
	}

	HazardArea = CreateDefaultSubobject<USphereComponent>(TEXT("HazardArea"));
	HazardArea->SetupAttachment(RootComponent);
	HazardArea->InitSphereRadius(HazardRadius);
	HazardArea->SetCollisionResponseToAllChannels(ECR_Ignore);
	HazardArea->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	HazardArea->SetGenerateOverlapEvents(true);

	SludgeGlow = CreateDefaultSubobject<UPointLightComponent>(TEXT("SludgeGlow"));
	SludgeGlow->SetupAttachment(RootComponent);
	SludgeGlow->SetRelativeLocation(FVector(0.f, 0.f, 15.f));
	SludgeGlow->SetIntensity(3800.f);
	SludgeGlow->SetAttenuationRadius(190.f);
	SludgeGlow->SetLightColor(FLinearColor(0.12f, 1.0f, 0.55f));
	SludgeGlow->SetCastShadows(false);
}

void ARobotHazardSludge::BeginPlay()
{
	Super::BeginPlay();

	if (SludgeMesh)
	{
		if (UMaterialInterface* Mat = LoadObject<UMaterialInterface>(nullptr,
				TEXT("/Game/RobotGame/Art/Materials/M_Toxic_Fluid.M_Toxic_Fluid")))
		{
			SludgeMesh->SetMaterial(0, Mat);
		}
	}
}

void ARobotHazardSludge::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// 1. 废液呼吸微光扰动
	if (SludgeGlow)
	{
		const float Time = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
		const float SinePulse = FMath::Sin(Time * 2.2f) * 0.18f + 1.0f;
		SludgeGlow->SetIntensity(3800.f * SinePulse);
	}

	// 2. 气泡电解液破裂轻音
	BubbleTimer -= DeltaSeconds;
	if (BubbleTimer <= 0.f)
	{
		BubbleTimer = FMath::FRandRange(2.5f, 5.0f);
		RobotSfx::PlayAt(this, TEXT("SFX_Impact"), GetActorLocation() + FVector(0.f, 0.f, 10.f), 0.35f, 0.45f, true);
	}

	// 3. 危险区域重叠逻辑：对进入废液的角色施加升温过热与泥泞减速
	if (!HazardArea)
	{
		return;
	}

	TArray<AActor*> OverlappingActors;
	HazardArea->GetOverlappingActors(OverlappingActors);

	for (AActor* Actor : OverlappingActors)
	{
		if (!Actor || Actor == this)
		{
			continue;
		}

		// 玩家踏入废液：散热器被化学粘液糊死，急剧升温
		if (ARobotCharacter* Player = Cast<ARobotCharacter>(Actor))
		{
			if (URobotAttributeSet* Attr = Player->GetAttributeSet())
			{
				const float CurrentHeat = Attr->GetHeat();
				const float MaxHeat = Attr->GetMaxHeat();
				// 持续升温
				Attr->SetHeat(FMath::Min(CurrentHeat + HeatPerSecond * DeltaSeconds, MaxHeat));
			}
			if (UCharacterMovementComponent* Move = Player->GetCharacterMovement())
			{
				Move->Velocity *= FMath::Clamp(1.0f - DeltaSeconds * 1.8f, 0.65f, 1.0f);
			}
		}
		// 敌机踏入废液：同样受到阻滞减速与腐蚀
		else if (ARobotEnemy* Enemy = Cast<ARobotEnemy>(Actor))
		{
			if (UCharacterMovementComponent* Move = Enemy->GetCharacterMovement())
			{
				Move->Velocity *= FMath::Clamp(1.0f - DeltaSeconds * 1.8f, 0.65f, 1.0f);
			}
		}
	}
}
