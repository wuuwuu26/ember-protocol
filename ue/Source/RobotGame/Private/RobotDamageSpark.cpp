#include "RobotDamageSpark.h"
#include "RobotSfx.h"

#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/World.h"

ARobotDamageSpark::ARobotDamageSpark()
{
	PrimaryActorTick.bCanEverTick = true;

	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));

	SparkMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SparkMesh"));
	SparkMesh->SetupAttachment(RootComponent);
	SparkMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	SparkMesh->SetCastShadow(false);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(
		TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (SphereMesh.Succeeded())
	{
		SparkMesh->SetStaticMesh(SphereMesh.Object);
		SparkMesh->SetRelativeScale3D(FVector(0.04f));
	}

	SparkLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("SparkLight"));
	SparkLight->SetupAttachment(RootComponent);
	SparkLight->SetIntensity(6000.f);
	SparkLight->SetAttenuationRadius(180.f);
	SparkLight->SetLightColor(FLinearColor(0.4f, 0.85f, 1.0f));
	SparkLight->SetCastShadows(false);
}

void ARobotDamageSpark::InitSpark(float InLifeTime)
{
	LifeTime = InLifeTime;
	if (SparkMesh)
	{
		if (UMaterialInterface* Mat = LoadObject<UMaterialInterface>(nullptr,
				TEXT("/Game/RobotGame/Art/Materials/M_Spark_Flash.M_Spark_Flash")))
		{
			SparkMesh->SetMaterial(0, Mat);
		}
	}
}

void ARobotDamageSpark::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	Age += DeltaSeconds;
	if (Age >= LifeTime)
	{
		Destroy();
		return;
	}

	SparkTimer -= DeltaSeconds;
	if (SparkTimer <= 0.f)
	{
		// 随机电火花闪烁节拍（0.04s ~ 0.16s 间歇爆闪）
		SparkTimer = FMath::FRandRange(0.04f, 0.16f);

		const bool bFlash = FMath::RandBool();
		if (SparkLight)
		{
			SparkLight->SetVisibility(bFlash);
			SparkLight->SetIntensity(bFlash ? FMath::FRandRange(4000.f, 9000.f) : 0.f);
		}
		if (SparkMesh)
		{
			SparkMesh->SetVisibility(bFlash);
			if (bFlash)
			{
				// 电火花在断口附近微小爆跳
				const FVector Jitter(
					FMath::FRandRange(-6.f, 6.f),
					FMath::FRandRange(-6.f, 6.f),
					FMath::FRandRange(-6.f, 6.f));
				SparkMesh->SetRelativeLocation(Jitter);
				const float S = FMath::FRandRange(0.02f, 0.08f);
				SparkMesh->SetRelativeScale3D(FVector(S));
			}
		}

		// 偶尔伴随一声极轻微的短路轻响
		if (bFlash && FMath::FRand() < 0.15f)
		{
			RobotSfx::PlayAt(this, TEXT("SFX_Impact"), GetActorLocation(), 0.25f, 2.2f, true);
		}
	}
}
