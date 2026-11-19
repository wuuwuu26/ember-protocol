#include "RobotExplosiveBarrel.h"

#include "SalvagePickup.h"
#include "RobotSfx.h"
#include "PartDamageComponent.h"

#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Engine/DamageEvents.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "UObject/ConstructorHelpers.h"

ARobotExplosiveBarrel::ARobotExplosiveBarrel()
{
	PrimaryActorTick.bCanEverTick = true;

	BarrelMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BarrelMesh"));
	RootComponent = BarrelMesh;
	BarrelMesh->SetCollisionProfileName(TEXT("BlockAllDynamic"));
	BarrelMesh->SetNotifyRigidBodyCollision(true);
	BarrelMesh->SetCastShadow(true);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> BarrelFinder(
		TEXT("/Game/RobotGame/Art/Props/SM_Prop_FuelBarrel.SM_Prop_FuelBarrel"));
	if (BarrelFinder.Succeeded())
	{
		BarrelMesh->SetStaticMesh(BarrelFinder.Object);
	}

	BlastLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("BlastLight"));
	BlastLight->SetupAttachment(RootComponent);
	BlastLight->SetLightColor(FLinearColor(1.0f, 0.45f, 0.12f));
	BlastLight->SetAttenuationRadius(BlastRadius * 1.5f);
	BlastLight->SetIntensity(0.f);
	BlastLight->SetCastShadows(false);

	SalvageClass = ASalvagePickup::StaticClass();
	CurrentHealth = MaxHealth;
}

float ARobotExplosiveBarrel::TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent,
	class AController* EventInstigator, class AActor* DamageCauser)
{
	if (bExploded || DamageAmount <= 0.f)
	{
		return 0.f;
	}

	CurrentHealth -= DamageAmount;
	UE_LOG(LogTemp, Warning, TEXT("[燃料桶受击] 扣血=%.1f 剩余血量=%.1f 来自=%s"),
		DamageAmount, CurrentHealth, DamageCauser ? *DamageCauser->GetName() : TEXT("未知"));

	if (CurrentHealth <= 0.f)
	{
		Explode(DamageCauser);
	}
	else
	{
		// 受到第一枪时微弱起火预警
		if (BlastLight)
		{
			BlastLight->SetIntensity(12000.f);
		}
		RobotSfx::PlayAt(this, TEXT("SFX_Impact"), GetActorLocation(), 0.8f, 1.2f, true);
	}
	return DamageAmount;
}

void ARobotExplosiveBarrel::Explode(AActor* DamageCauser)
{
	if (bExploded)
	{
		return;
	}
	bExploded = true;
	BlastDecayTime = MaxBlastDecay;

	const FVector Loc = GetActorLocation();
	UWorld* World = GetWorld();

	// 1. 强光冲击波：瞬间点亮 150,000cd 的烈焰橘红强光
	if (BlastLight)
	{
		BlastLight->SetIntensity(150000.f);
	}

	// 2. 爆炸音效：剧烈金属爆炸低音 + 破片撕裂
	RobotSfx::PlayAt(this, TEXT("SFX_Destroy"), Loc, 1.35f, 0.72f, true);
	RobotSfx::PlayAt(this, TEXT("SFX_Impact"), Loc, 1.10f, 0.55f, true);

	// 3. 桶身更换为残骸废铁模型，关闭阻挡碰撞
	if (BarrelMesh)
	{
		if (UStaticMesh* DebrisMesh = LoadObject<UStaticMesh>(nullptr,
				TEXT("/Game/RobotGame/Art/Props/SM_Prop_Debris.SM_Prop_Debris")))
		{
			BarrelMesh->SetStaticMesh(DebrisMesh);
			BarrelMesh->SetRelativeScale3D(FVector(0.55f, 0.55f, 0.35f));
		}
		BarrelMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	}

	// 4. 范围破坏：对 BlastRadius 范围内的角色/部位施加高额范围爆炸伤害
	if (World)
	{
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			AActor* Target = *It;
			if (!Target || Target == this)
			{
				continue;
			}
			const float Dist = FVector::Dist(Loc, Target->GetActorLocation());
			if (Dist > BlastRadius)
			{
				continue;
			}

			const float Falloff = 1.0f - (Dist / BlastRadius);
			const float ActualDmg = BlastDamage * Falloff;

			if (UPartDamageComponent* Parts = Target->FindComponentByClass<UPartDamageComponent>())
			{
				FVector BlastDir = (Target->GetActorLocation() - Loc).GetSafeNormal();
				float Dealt = 0.f;
				bool bBroke = false;
				bool bCoreDead = false;
				// 优先直接炸裂附近机械肢体
				Parts->ApplyDamageByBoneEx(NAME_None, ActualDmg, Dealt, bBroke, bCoreDead, BlastDir);
				UE_LOG(LogTemp, Warning, TEXT("[燃料桶爆炸] 击中目标=%s 距离=%.0f 实际伤害=%.1f"),
					*Target->GetName(), Dist, Dealt);
			}
		}

		// 5. 爆炸冲击震落 2~3 枚金琥珀废料核心
		if (SalvageClass)
		{
			const int32 Drops = FMath::RandRange(2, 3);
			for (int32 i = 0; i < Drops; ++i)
			{
				const FVector Offset(
					FMath::FRandRange(-90.f, 90.f),
					FMath::FRandRange(-90.f, 90.f),
					FMath::FRandRange(30.f, 60.f));
				FActorSpawnParameters SpawnParams;
				SpawnParams.SpawnCollisionHandlingOverride =
					ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
				if (ASalvagePickup* Drop = World->SpawnActor<ASalvagePickup>(
						SalvageClass, Loc + Offset, FRotator::ZeroRotator, SpawnParams))
				{
					Drop->SetValue(FMath::RandRange(6, 10));
				}
			}
		}
	}
}

void ARobotExplosiveBarrel::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (bExploded && BlastDecayTime > 0.f)
	{
		BlastDecayTime -= DeltaSeconds;
		if (BlastLight)
		{
			if (BlastDecayTime <= 0.f)
			{
				BlastLight->SetIntensity(0.f);
			}
			else
			{
				const float T = BlastDecayTime / MaxBlastDecay;
				BlastLight->SetIntensity(150000.f * T * T);
			}
		}
	}
}
