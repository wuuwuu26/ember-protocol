#include "Abilities/GA_Fire.h"

#include "RobotCharacter.h"
#include "RobotProjectile.h"
#include "RobotSfx.h"
#include "RobotTypes.h"
#include "RobotChassisData.h"
#include "AssemblyComponent.h"
#include "RobotModuleData.h"

#include "GameFramework/Character.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "UObject/ConstructorHelpers.h"

UGA_Fire::UGA_Fire()
{
	ActivationBlockedTags.AddTag(RobotTags::State_Overheated());

	// ── 弹丸类：必须在这里给出兜底！──
	//
	// 这是个"沉默了两周"的 bug：技能是**直接从 C++ 类**授予的
	// （DefaultAbilities 里写的是 UGA_Fire::StaticClass()，没有 GA 蓝图），
	// 而 ProjectileClass 只在蓝图里才配 —— 结果玩家的每一次激活都在
	// `if (!ProjectileClass)` 处静默返回：不开火、不耗电、不发热，
	// 所有"装了武器但打不出来"的体验问题都源于这一行。
	// （校验脚本当时只查了"默认技能数 = 2"，没查技能内部的引用。）
	//
	// 现在：优先加载蓝图 BP_Projectile（美术与参数都在它里面配），
	// 加载不到就退回 C++ 类本身 —— "永远有弹可打"。
	static ConstructorHelpers::FClassFinder<ARobotProjectile> BPProjectile(
		TEXT("/Game/RobotGame/Blueprints/BP_Projectile"));
	if (BPProjectile.Succeeded())
	{
		ProjectileClass = BPProjectile.Class;
	}
	else
	{
		ProjectileClass = ARobotProjectile::StaticClass();
	}

	UE_LOG(LogTemp, Log, TEXT("[GA_Fire] 弹丸类 = %s"),
		ProjectileClass ? *ProjectileClass->GetName() : TEXT("空"));
}

void UGA_Fire::ActivateAbility(const FGameplayAbilitySpecHandle Handle,
	const FGameplayAbilityActorInfo* ActorInfo,
	const FGameplayAbilityActivationInfo ActivationInfo,
	const FGameplayEventData* TriggerEventData)
{
	Super::ActivateAbility(Handle, ActorInfo, ActivationInfo, TriggerEventData);

	ACharacter* Character = Cast<ACharacter>(GetAvatarActorFromActorInfo());
	UWorld* World = GetWorld();
	if (!Character || !World || !ProjectileClass)
	{
		EndAbility(Handle, ActorInfo, ActivationInfo, true, true);
		return;
	}

	const float Now = World->GetTimeSeconds();

	// ── 武器数值：统一从装配组件取（机体档位 × 武器臂乘数）──
	//
	// 计算逻辑在 UAssemblyComponent::GetWeaponProfile ——
	// 改装界面的武器读数和这里的开火数值用的是**同一个来源**，
	// 两边各算一份必然对不上（改数据的优先级就乱了）。
	// 下面的类默认值只是没有装配组件时的兜底。
	float Dmg = Damage;
	float Interval = FireInterval;
	float Heat = HeatPerShot;
	float PowerCost = PowerPerShot;
	if (const UAssemblyComponent* Asm = GetAssembly())
	{
		Asm->GetWeaponProfile(Dmg, Interval, Heat);
		if (Asm->Chassis)
		{
			PowerCost = Asm->Chassis->WeaponPowerPerShot;   // 允许 0（纯热约束）
		}
	}

	// 散布冷却（即使这一帧因为射速限制没打出去，也要继续冷却）
	const float CoolDt = FMath::Max(Now - LastFireTime, 0.f);
	SpreadBloom = FMath::Max(0.f, SpreadBloom - SpreadCoolRate * CoolDt);

	// 射速限制
	if (Now - LastFireTime < Interval)
	{
		EndAbility(Handle, ActorInfo, ActivationInfo, true, true);
		return;
	}

	// 电力不足则不开火（PowerCost 为 0 时永远通过）。
	// ConsumePower 内部已做检查，不会扣成负数。
	if (!ConsumePower(PowerCost))
	{
		EndAbility(Handle, ActorInfo, ActivationInfo, true, true);
		return;
	}

	LastFireTime = Now;
	AddHeat(Heat);

	// ── 起点：枪口 ──
	FVector SpawnLoc = Character->GetActorLocation()
		+ Character->GetActorForwardVector() * 80.f;
	FVector AimPoint = SpawnLoc + Character->GetActorForwardVector() * 10000.f;

	if (const ARobotCharacter* Robot = Cast<ARobotCharacter>(Character))
	{
		// 枪口跟着程序化动画走（走路摆臂、开火后坐都会带动它）
		const FTransform Muzzle = Robot->GetMuzzleTransform();
		SpawnLoc = Muzzle.GetLocation();
		// 准心命中点：由相机中心射线决定
		AimPoint = Robot->GetAimPoint();
	}

	// ── 方向：枪口 → 准心命中点 ──
	FVector Dir = (AimPoint - SpawnLoc).GetSafeNormal();
	if (Dir.IsNearlyZero())
	{
		Dir = Character->GetActorForwardVector();
	}

	// ── 散布 ──
	float Spread = SpreadDegrees;
	if (bBloomOnSustainedFire)
	{
		Spread += SpreadBloom;
		SpreadBloom = FMath::Min(SpreadBloom + SpreadBloomPerShot,
			FMath::Max(SpreadDegrees, 0.01f) * 3.f);
	}
	if (Spread > KINDA_SMALL_NUMBER)
	{
		Dir = FMath::VRandCone(Dir, FMath::DegreesToRadians(Spread));
	}

	const FRotator SpawnRot = Dir.Rotation();

	FActorSpawnParameters Params;
	Params.Owner = Character;
	Params.Instigator = Character;
	Params.SpawnCollisionHandlingOverride =
		ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	ARobotProjectile* Projectile = World->SpawnActor<ARobotProjectile>(
		ProjectileClass, SpawnLoc, SpawnRot, Params);
	if (Projectile)
	{
		Projectile->InitProjectile(Dmg, ProjectileSpeed, Character);
	}

	// 开火音效：从枪口位置播（带 3D 衰减），音高随机微抖 ——
	// 连发时如果每发音高完全一样，会听出"复读机"的廉价感。
	RobotSfx::PlayAt(Character, TEXT("SFX_Fire_Player"), SpawnLoc, 0.85f,
		1.f, true);

	// 反馈（后坐 / 镜头抖动）必须按"真的打出一发"来施加，
	// 不能绑在"按下开火键"上 —— 否则连发的第 2 发之后就没有后坐了。
	if (ARobotCharacter* Robot = Cast<ARobotCharacter>(Character))
	{
		Robot->OnWeaponFired(1.f);
	}

	EndAbility(Handle, ActorInfo, ActivationInfo, true, false);
}
