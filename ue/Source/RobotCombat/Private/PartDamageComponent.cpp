#include "PartDamageComponent.h"
#include "PartMapData.h"
#include "RobotTypes.h"

#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "PhysicsEngine/BodyInstance.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Pawn.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

UPartDamageComponent::UPartDamageComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UPartDamageComponent::BeginPlay()
{
	Super::BeginPlay();
	InitializeParts();

	// ── 方向倍率自检 ──
	//
	// 倍率写反了在战斗里只表现为"数字有点怪"，很难靠截图发现。
	// 带 -ExposureProbe 启动时把每个部位的三面倍率打成一张表，一眼就能核对。
	if (FParse::Param(FCommandLine::Get(), TEXT("ExposureProbe")))
	{
		const AActor* Owner = GetOwner();
		const FRotator Yaw(0.f, Owner ? Owner->GetActorRotation().Yaw : 0.f, 0.f);
		const FVector Forward = Yaw.Vector();
		const FVector Right = FRotationMatrix(Yaw).GetUnitAxis(EAxis::Y);

		for (const TPair<FGameplayTag, FPartHealth>& Pair : Parts)
		{
			// 传的是**弹丸飞行方向**：射手在正面时，弹丸朝 -Forward 飞。
			const float Front = GetExposureMultiplier(Pair.Key, -Forward);
			const float Side = GetExposureMultiplier(Pair.Key, -Right);
			const float Back = GetExposureMultiplier(Pair.Key, Forward);
			UE_LOG(LogTemp, Log,
				TEXT("[倍率] 表=%s %s 部位=%s 正面=%.2f 侧面=%.2f 背面=%.2f"),
				*GetNameSafe(PartMap), *GetNameSafe(Owner), *Pair.Key.ToString(),
				Front, Side, Back);
		}
	}
}

void UPartDamageComponent::SetPartMap(UPartMapData* InPartMap)
{
	if (!InPartMap)
	{
		// 传空表示"保留现有表"。Actor 的 BeginPlay 在组件之后执行，
		// 如果这里把表清空，部位系统会在初始化后被静默废掉。
		return;
	}

	PartMap = InPartMap;
	// 换表后立即重建部位血量。用 InitializeParts 而不是增量更新，
	// 因为新旧表的部位集合可能完全不同。
	InitializeParts();

	UE_LOG(LogTemp, Log, TEXT("[%s] 部位表已应用：%d 条规则"),
		*GetNameSafe(GetOwner()), Parts.Num());
}

void UPartDamageComponent::InitializeParts()
{
	Parts.Empty();
	bDisabled = false;

	if (!PartMap)
	{
		if (!bBuildDefaultsIfNoMap)
		{
			UE_LOG(LogTemp, Warning,
				TEXT("[%s] PartDamageComponent 未配置 PartMap，部位系统不会生效"),
				*GetNameSafe(GetOwner()));
			return;
		}

		// 兜底：用代码里的默认规则建一个临时映射表。
		// 这样即使数据资产没配好，部位系统也能工作，不会静默失效。
		UPartMapData* Fallback = NewObject<UPartMapData>(this);
		Fallback->BuildDefaultRules(bUsePlayerRigDefaults);
		PartMap = Fallback;

		// 用 Verbose 而不是 Log：组件的 BeginPlay 早于 Actor 的 BeginPlay，
		// 所以「暂时没有表」是正常时序，随后 Actor 会调用 SetPartMap 覆盖。
		// 打成 Log 会让人误以为配置丢了。
		UE_LOG(LogTemp, Verbose,
			TEXT("[%s] 组件初始化时还没有 PartMap，先用%s骨架的默认规则（%d 条）占位"),
			*GetNameSafe(GetOwner()),
			bUsePlayerRigDefaults ? TEXT("玩家") : TEXT("敌人"),
			Fallback->Rules.Num());
	}

	for (const FPartBoneRule& Rule : PartMap->Rules)
	{
		if (!Rule.PartTag.IsValid())
		{
			UE_LOG(LogTemp, Warning,
				TEXT("[%s] PartMap 中存在未设置 PartTag 的规则，已跳过"),
				*GetNameSafe(PartMap));
			continue;
		}

		FPartHealth Health;
		Health.PartTag = Rule.PartTag;
		Health.MaxHealth = Rule.MaxHealth;
		Health.CurrentHealth = Rule.MaxHealth;
		Health.SalvageValue = Rule.SalvageValue;
		Parts.Add(Rule.PartTag, Health);
	}
}

// ─────────────────────────────────────────────
// 查询
// ─────────────────────────────────────────────

bool UPartDamageComponent::GetPartHealth(const FGameplayTag& PartTag,
                                         FPartHealth& OutHealth) const
{
	if (const FPartHealth* Found = Parts.Find(PartTag))
	{
		OutHealth = *Found;
		return true;
	}
	return false;
}

float UPartDamageComponent::GetPartRatio(const FGameplayTag& PartTag) const
{
	if (const FPartHealth* Found = Parts.Find(PartTag))
	{
		return Found->GetRatio();
	}
	return 0.f;
}

bool UPartDamageComponent::IsPartDestroyed(const FGameplayTag& PartTag) const
{
	if (const FPartHealth* Found = Parts.Find(PartTag))
	{
		return Found->IsDestroyed();
	}
	// 查不到的部位视为已毁 —— 避免"没有这个部位"被当成"完好"
	return true;
}

bool UPartDamageComponent::IsCoreDestroyed() const
{
	return IsPartDestroyed(RobotTags::Part_Core());
}

int32 UPartDamageComponent::GetAlivePartCount() const
{
	int32 Count = 0;
	for (const TPair<FGameplayTag, FPartHealth>& Pair : Parts)
	{
		// 躯干只是伤害承受面，不计入"功能部位"
		if (Pair.Key == RobotTags::Part_Torso())
		{
			continue;
		}
		if (!Pair.Value.IsDestroyed())
		{
			++Count;
		}
	}
	return Count;
}

bool UPartDamageComponent::IsRepairable() const
{
	if (!bIsCompanionCandidate || IsCoreDestroyed())
	{
		return false;
	}
	// 核心存活，但所有功能部位失效 —— 这就是"可修复/可招募"的窗口
	for (const TPair<FGameplayTag, FPartHealth>& Pair : Parts)
	{
		if (Pair.Key == RobotTags::Part_Core() || Pair.Key == RobotTags::Part_Torso())
		{
			continue;
		}
		if (!Pair.Value.IsDestroyed())
		{
			return false;
		}
	}
	return true;
}

// ─────────────────────────────────────────────
// 伤害
// ─────────────────────────────────────────────

FGameplayTag UPartDamageComponent::ApplyDamageByBone(FName BoneName, float Damage)
{
	if (bDisabled || !PartMap)
	{
		return FGameplayTag();
	}

	const FGameplayTag PartTag = PartMap->ResolvePartTag(BoneName);
	if (!PartTag.IsValid())
	{
		// 命中骨骼不在映射表里（例如武器、装饰骨）——不计入部位伤害
		return FGameplayTag();
	}

	ApplyDamageToPart(PartTag, Damage);
	return PartTag;
}

FGameplayTag UPartDamageComponent::ApplyDamageByBoneEx(FName BoneName, float Damage,
	float& OutTaken, bool& bOutBrokePart, bool& bOutCoreDestroyed,
	const FVector& IncomingDirection)
{
	OutTaken = 0.f;
	bOutBrokePart = false;
	bOutCoreDestroyed = false;

	if (bDisabled || !PartMap)
	{
		return FGameplayTag();
	}

	FGameplayTag PartTag;
	if (BoneName.IsNone())
	{
		// 范围伤害（如爆炸/近战冲击）：若未指定骨骼名，优先选取受击方向上最易损的存活外露部位（四肢/躯干）
		for (const auto& Pair : Parts)
		{
			if (Pair.Value.CurrentHealth > 0.f && Pair.Key != RobotTags::Part_Core())
			{
				PartTag = Pair.Key;
				break;
			}
		}
		if (!PartTag.IsValid())
		{
			PartTag = RobotTags::Part_Core();
		}
	}
	else
	{
		PartTag = PartMap->ResolvePartTag(BoneName);
	}

	if (!PartTag.IsValid())
	{
		return FGameplayTag();
	}

	// ── 方向加成 ──
	//
	// 无方向信息时（例如直接调用、脚本测试）按"正面"处理，也就是不加成。
	// 这样这个接口保持向后兼容：旧调用方看到的行为不变。
	float Multiplier = 1.f;
	if (!IncomingDirection.IsNearlyZero())
	{
		Multiplier = GetExposureMultiplier(PartTag, IncomingDirection);
	}
	const float EffectiveDamage = Damage * Multiplier;

	// 先读一份"伤害前"的状态：ApplyDamageToPart 之后血量已经被扣、
	// 部位可能已经进了销毁分支，读不到差值了。
	float HpBefore = 0.f;
	const FPartHealth* Before = Parts.Find(PartTag);
	if (Before)
	{
		HpBefore = Before->CurrentHealth;
	}

	ApplyDamageToPart(PartTag, EffectiveDamage);

	const FPartHealth* After = Parts.Find(PartTag);
	if (!After)
	{
		return PartTag;
	}
	OutTaken = FMath::Max(0.f, HpBefore - After->CurrentHealth);
	bOutBrokePart = HpBefore > 0.f && After->CurrentHealth <= 0.f;
	bOutCoreDestroyed = IsCoreDestroyed();
	return PartTag;
}

float UPartDamageComponent::GetExposureMultiplier(const FGameplayTag& PartTag,
	const FVector& IncomingDirection) const
{
	if (!PartMap || IncomingDirection.IsNearlyZero())
	{
		return 1.f;
	}

	FPartBoneRule Rule;
	if (!PartMap->FindRule(PartTag, Rule))
	{
		return 1.f;
	}

	const AActor* Owner = GetOwner();
	if (!Owner)
	{
		return 1.f;
	}

	// 阈值刻意放宽到 0.55（约 ±56.6°）。收紧到 0.8 的话，玩家必须几乎站到
	// 正后方才能吃到加成 —— 那会让"绕后"退化成卡角度，而不是战术走位。
	// 反过来说，放宽也意味着"随便侧身"就能吃到，所以倍率本身不能给太狠。
	constexpr float FrontDotThreshold = 0.55f;
	constexpr float BackDotThreshold = -0.55f;

	// IncomingDirection 是弹丸飞行方向（射手 → 目标）。
	// 取反得到"目标 → 射手"，再投影到机体前向：
	//   点积 > 0  → 射手在机体前方（正面迎弹，装甲最厚）
	//   点积 < 0  → 射手在机体背后（散热口/电源线暴露）
	const FVector ToShooter = -IncomingDirection.GetSafeNormal();
	const float Dot = FVector::DotProduct(Owner->GetActorForwardVector(), ToShooter);

	float Multiplier = 1.f;
	if (Dot > FrontDotThreshold)
	{
		// 射手在正面 —— 装甲最厚，倍率最低
		Multiplier = Rule.FrontMultiplier;
	}
	else if (Dot < BackDotThreshold)
	{
		// 射手在背后
		Multiplier = Rule.BackMultiplier;
	}
	else
	{
		Multiplier = Rule.SideMultiplier;
	}

	// 数值保护：负倍率会让"挨打回血"，0 倍率会让子弹完全无效。
	// 数据资产是可以在编辑器里随手改的，这里挡一层。
	return FMath::Clamp(Multiplier, 0.1f, 4.f);
}

void UPartDamageComponent::ApplyDamageToPart(const FGameplayTag& PartTag, float Damage)
{
	if (bDisabled || Damage <= 0.f)
	{
		return;
	}

	// 调试：-GodMode 时玩家不吃部位伤害，用于观察 AI 走位 / 录制 / 布光截图。
	// 只对玩家生效 —— 敌人仍然正常掉血，"看敌人怎么绕"才有意义。
	//
	// 第一百零八轮：新增运行时 bInvulnerable（观察者模式用）。
	// 观察者模式下机甲脱离控制仍留在场上挨打，进入时置 true、退出复位。
	// 两种入口任一成立即免伤：启动期的 -GodMode（仅玩家）、运行时的开关。
	if (bInvulnerable)
	{
		return;
	}
	if (const APawn* Pawn = Cast<APawn>(GetOwner()))
	{
		if (Pawn->IsPlayerControlled()
			&& FParse::Param(FCommandLine::Get(), TEXT("GodMode")))
		{
			return;
		}
	}

	FPartHealth* Health = Parts.Find(PartTag);
	if (!Health || Health->IsDestroyed())
	{
		// 已毁部位不再吸收伤害 —— 防止"打腿等于打全身"的溢出
		return;
	}

	Health->CurrentHealth = FMath::Max(0.f, Health->CurrentHealth - Damage);
	OnPartDamaged.Broadcast(PartTag, Health->GetRatio());

	if (Health->IsDestroyed())
	{
		FPartBoneRule Rule;
		if (PartMap && PartMap->FindRule(PartTag, Rule))
		{
			HandlePartDestruction(PartTag, Rule);
		}
		else
		{
			OnPartDestroyed.Broadcast(PartTag);
		}
	}
}

void UPartDamageComponent::RepairAllParts()
{
	for (TPair<FGameplayTag, FPartHealth>& Pair : Parts)
	{
		Pair.Value.CurrentHealth = Pair.Value.MaxHealth;
	}
	bDisabled = false;
}

// ─────────────────────────────────────────────
// 部位摧毁
// ─────────────────────────────────────────────

void UPartDamageComponent::HandlePartDestruction(const FGameplayTag& PartTag,
                                                 const FPartBoneRule& Rule)
{
	AActor* Owner = GetOwner();

	// ── 表现层：隐藏对应骨骼 ──
	// 这是"假拆解"的核心。不用 Chaos 逐块碎裂，因为碎块不可控，
	// 且无法稳定作为可拾取物。掉落的备件由游戏层根据 OnPartDestroyed 生成。
	if (Owner)
	{
		if (USkeletalMeshComponent* SkelMesh =
				Owner->FindComponentByClass<USkeletalMeshComponent>())
		{
			if (const USkeletalMesh* Mesh = SkelMesh->GetSkeletalMeshAsset())
			{
				// USkeletalMesh 上的方法叫 GetRefSkeleton()。
				// GetReferenceSkeleton() 是 USkeleton 上的，写错会报 C2039。
				const FReferenceSkeleton& RefSkeleton = Mesh->GetRefSkeleton();
				const int32 NumBones = RefSkeleton.GetNum();
				for (const FName& Prefix : Rule.BonePrefixes)
				{
					const FString PrefixStr = Prefix.ToString();
					for (int32 BoneIndex = 0; BoneIndex < NumBones; ++BoneIndex)
					{
						const FName BoneName = RefSkeleton.GetBoneName(BoneIndex);
						if (BoneName.ToString().StartsWith(PrefixStr,
								ESearchCase::IgnoreCase))
						{
							SkelMesh->HideBoneByName(BoneName, PBO_None);
						}
					}
				}
			}
		}
	}

	// 广播给游戏层 —— 由它决定生成掉落物、播特效、更新 UI
	OnPartDestroyed.Broadcast(PartTag);

	// ── 判定层 ──
	if (Rule.bDestructionKills)
	{
		// 核心被毁 = 立即死亡。剩余完好部件不掉落，
		// 所以想最大化回收必须先拆四肢再打核心 —— 这是"贪心 vs 安全"的取舍来源。
		bDisabled = true;
		OnActorDisabled.Broadcast();
		return;
	}

	if (GetAlivePartCount() == 0)
	{
		// 功能部位全毁但核心存活 → 瘫痪而非死亡，可交互
		bDisabled = true;
		OnActorDisabled.Broadcast();
	}
}

FVector UPartDamageComponent::ResolveDropLocation(FName BoneName) const
{
	const AActor* Owner = GetOwner();
	if (!Owner)
	{
		return FVector::ZeroVector;
	}
	if (const USkeletalMeshComponent* SkelMesh =
			Owner->FindComponentByClass<USkeletalMeshComponent>())
	{
		return SkelMesh->GetBoneLocation(BoneName, EBoneSpaces::WorldSpace);
	}
	return Owner->GetActorLocation();
}
