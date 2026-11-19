#include "AssemblyComponent.h"
#include "RobotChassisData.h"
#include "RobotModuleData.h"
#include "RobotAttributeSet.h"

#include "AbilitySystemComponent.h"
#include "GameFramework/Actor.h"
// ACharacter 与 UCharacterMovementComponent 必须显式 include ——
// 只用前置声明会在 Cast<ACharacter> 与 GetCharacterMovement() 处
// 报 C2027「使用了未定义类型」。
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"

UAssemblyComponent::UAssemblyComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UAssemblyComponent::BeginPlay()
{
	Super::BeginPlay();
	NotifyChanged();
}

// ─────────────────────────────────────────────
// 装配操作
// ─────────────────────────────────────────────

bool UAssemblyComponent::CanMount(EModuleSlot Slot, URobotModuleData* Module,
                                  FText& OutReason) const
{
	if (!Chassis)
	{
		OutReason = FText::FromString(TEXT("尚未选择机体"));
		return false;
	}
	if (!Module)
	{
		OutReason = FText::FromString(TEXT("模块为空"));
		return false;
	}

	// 槽位必须存在于机体定义里
	const bool bSlotExists = Chassis->Slots.ContainsByPredicate(
		[Slot](const FModuleSlotDef& Def) { return Def.Slot == Slot; });
	if (!bSlotExists)
	{
		OutReason = FText::FromString(TEXT("该机体没有这个插槽"));
		return false;
	}

	// 模块只能装到它声明的槽位类型。
	// 左右臂 / 左右推进器 / 两个辅助槽**视为同类槽位**：模块资产只声明
	// 一侧（如 ArmLeft），两侧都能装 —— 美术设定就是"标准挂载接口、
	// 可互换"，没必要为左右各复制一份模块资产。
	auto SameSlotKind = [](EModuleSlot A, EModuleSlot B)
	{
		if (A == B)
		{
			return true;
		}
		auto In = [](EModuleSlot S, EModuleSlot X, EModuleSlot Y)
		{
			return S == X || S == Y;
		};
		if (In(A, EModuleSlot::ArmLeft, EModuleSlot::ArmRight)
			&& In(B, EModuleSlot::ArmLeft, EModuleSlot::ArmRight))
		{
			return true;
		}
		if (In(A, EModuleSlot::ThrusterLeft, EModuleSlot::ThrusterRight)
			&& In(B, EModuleSlot::ThrusterLeft, EModuleSlot::ThrusterRight))
		{
			return true;
		}
		if (In(A, EModuleSlot::Aux01, EModuleSlot::Aux02)
			&& In(B, EModuleSlot::Aux01, EModuleSlot::Aux02))
		{
			return true;
		}
		return false;
	};
	if (!SameSlotKind(Module->TargetSlot, Slot))
	{
		OutReason = FText::FromString(TEXT("模块类型与插槽不匹配"));
		return false;
	}

	// 机体对该槽位的类型限制
	if (!Chassis->AcceptsModuleInSlot(Slot, Module->ModuleType))
	{
		OutReason = FText::FromString(TEXT("该插槽不接受这类模块"));
		return false;
	}

	// 供电是硬约束 —— 这是三条约束里唯一直接拦装配的一条
	const URobotModuleData* Existing = GetModule(Slot);
	const float ExistingDraw = Existing ? Existing->PowerDraw : 0.f;
	const float ProjectedDraw = GetTotalPowerDraw() - ExistingDraw + Module->PowerDraw;
	if (ProjectedDraw > Chassis->PowerCapacity)
	{
		OutReason = FText::Format(
			FText::FromString(TEXT("供电超载：需要 {0}，上限 {1}")),
			FText::AsNumber(FMath::RoundToInt(ProjectedDraw)),
			FText::AsNumber(FMath::RoundToInt(Chassis->PowerCapacity)));
		return false;
	}

	OutReason = FText::GetEmpty();
	return true;
}

bool UAssemblyComponent::MountModule(EModuleSlot Slot, URobotModuleData* Module)
{
	FText Reason;
	if (!CanMount(Slot, Module, Reason))
	{
		UE_LOG(LogTemp, Verbose, TEXT("装配被拒绝：%s"), *Reason.ToString());
		return false;
	}
	MountedModules.Add(Slot, Module);
	NotifyChanged();
	return true;
}

void UAssemblyComponent::UnmountModule(EModuleSlot Slot)
{
	if (MountedModules.Remove(Slot) > 0)
	{
		NotifyChanged();
	}
}

void UAssemblyComponent::SetChassis(URobotChassisData* NewChassis)
{
	if (Chassis == NewChassis)
	{
		return;
	}
	Chassis = NewChassis;

	// 换机体后原有模块可能不再合法（槽位类型或供电上限变化），
	// 所以要逐个复验并卸下不合法的。
	TArray<EModuleSlot> ToRemove;
	for (const TPair<EModuleSlot, TObjectPtr<URobotModuleData>>& Pair : MountedModules)
	{
		FText Reason;
		if (!Pair.Value || !CanMount(Pair.Key, Pair.Value, Reason))
		{
			ToRemove.Add(Pair.Key);
		}
	}
	for (EModuleSlot Slot : ToRemove)
	{
		MountedModules.Remove(Slot);
	}

	NotifyChanged();
}

URobotModuleData* UAssemblyComponent::GetModule(EModuleSlot Slot) const
{
	const TObjectPtr<URobotModuleData>* Found = MountedModules.Find(Slot);
	return Found ? Found->Get() : nullptr;
}

// ─────────────────────────────────────────────
// 约束汇总
// ─────────────────────────────────────────────

float UAssemblyComponent::GetTotalMass() const
{
	float Total = Chassis ? Chassis->Mass : 0.f;
	for (const TPair<EModuleSlot, TObjectPtr<URobotModuleData>>& Pair : MountedModules)
	{
		if (Pair.Value)
		{
			Total += Pair.Value->Mass;
		}
	}
	return Total;
}

float UAssemblyComponent::GetTotalPowerDraw() const
{
	float Total = 0.f;
	for (const TPair<EModuleSlot, TObjectPtr<URobotModuleData>>& Pair : MountedModules)
	{
		if (Pair.Value)
		{
			Total += Pair.Value->PowerDraw;
		}
	}
	return Total;
}

float UAssemblyComponent::GetPowerHeadroom() const
{
	return Chassis ? (Chassis->PowerCapacity - GetTotalPowerDraw()) : 0.f;
}

float UAssemblyComponent::GetTotalHeatDissipation() const
{
	float Total = Chassis ? Chassis->HeatDissipation : 0.f;
	for (const TPair<EModuleSlot, TObjectPtr<URobotModuleData>>& Pair : MountedModules)
	{
		if (Pair.Value)
		{
			Total += Pair.Value->HeatDissipationModifier;
		}
	}
	return FMath::Max(Total, 0.f);
}

float UAssemblyComponent::GetTotalHeatCapacity() const
{
	float Total = Chassis ? Chassis->HeatCapacity : 0.f;
	for (const TPair<EModuleSlot, TObjectPtr<URobotModuleData>>& Pair : MountedModules)
	{
		if (Pair.Value)
		{
			Total += Pair.Value->HeatCapacityModifier;
		}
	}
	return FMath::Max(Total, 1.f);
}

float UAssemblyComponent::GetEffectiveWalkSpeed() const
{
	if (!Chassis)
	{
		return 0.f;
	}
	const float TotalMass = GetTotalMass();
	return TotalMass > KINDA_SMALL_NUMBER ? Chassis->BaseWalkSpeed / TotalMass : 0.f;
}

void UAssemblyComponent::GetWeaponProfile(float& OutDamage, float& OutFireInterval,
	float& OutHeatPerShot) const
{
	// 兜底值 = 中型档位（机体资产没配武器字段时用）
	OutDamage = 15.f;
	OutFireInterval = 0.19f;
	OutHeatPerShot = 11.5f;

	if (Chassis)
	{
		if (Chassis->WeaponDamage > 0.f)
		{
			OutDamage = Chassis->WeaponDamage;
		}
		if (Chassis->WeaponFireInterval > 0.f)
		{
			OutFireInterval = Chassis->WeaponFireInterval;
		}
		if (Chassis->WeaponHeatPerShot > 0.f)
		{
			OutHeatPerShot = Chassis->WeaponHeatPerShot;
		}
	}

	// 武器臂乘数（左右叠乘）
	const EModuleSlot Arms[] = { EModuleSlot::ArmLeft, EModuleSlot::ArmRight };
	for (const EModuleSlot S : Arms)
	{
		if (const URobotModuleData* M = GetModule(S))
		{
			OutDamage *= M->WeaponDamageMult;
			OutFireInterval *= M->WeaponFireIntervalMult;
			OutHeatPerShot *= M->WeaponHeatMult;
		}
	}
}

FGameplayTagContainer UAssemblyComponent::GetGrantedTraversalTags() const
{
	FGameplayTagContainer Result;
	for (const TPair<EModuleSlot, TObjectPtr<URobotModuleData>>& Pair : MountedModules)
	{
		if (Pair.Value)
		{
			Result.AppendTags(Pair.Value->GrantedTraversalTags);
		}
	}
	return Result;
}

// ─────────────────────────────────────────────
// 写入 GAS
// ─────────────────────────────────────────────

void UAssemblyComponent::ApplyToAbilitySystem(UAbilitySystemComponent* ASC){
	if (!ASC || !Chassis)
	{
		return;
	}

	// 直接改基础值：装配是"配置"，不是战斗中的临时增益，
	// 走 GameplayEffect 反而会让存档与回滚变复杂。
	const float Mass = GetTotalMass();
	const float Speed = GetEffectiveWalkSpeed();

	ASC->SetNumericAttributeBase(URobotAttributeSet::GetMaxPowerAttribute(),
		Chassis->PowerCapacity);
	ASC->SetNumericAttributeBase(URobotAttributeSet::GetPowerRegenAttribute(),
		Chassis->PowerRegen);
	ASC->SetNumericAttributeBase(URobotAttributeSet::GetMaxHeatAttribute(),
		GetTotalHeatCapacity());
	ASC->SetNumericAttributeBase(URobotAttributeSet::GetHeatDissipationRateAttribute(),
		GetTotalHeatDissipation());

	// 当前值不能超过新上限
	const float CurPower = ASC->GetNumericAttribute(URobotAttributeSet::GetPowerAttribute());
	ASC->SetNumericAttributeBase(URobotAttributeSet::GetPowerAttribute(),
		FMath::Min(CurPower, Chassis->PowerCapacity));

	// 质量影响移动 —— 这是"重装真的变笨重"的落点
	if (ACharacter* Char = Cast<ACharacter>(GetOwner()))
	{
		Char->GetCharacterMovement()->MaxWalkSpeed = Speed;
	}

	// 机体标签：供技能与动画查询当前机型
	ASC->RemoveLooseGameplayTag(RobotTags::Chassis_Light());
	ASC->RemoveLooseGameplayTag(RobotTags::Chassis_Medium());
	ASC->RemoveLooseGameplayTag(RobotTags::Chassis_Heavy());

	switch (Chassis->ChassisClass)
	{
	case EChassisClass::Light:
		ASC->AddLooseGameplayTag(RobotTags::Chassis_Light());
		break;
	case EChassisClass::Heavy:
		ASC->AddLooseGameplayTag(RobotTags::Chassis_Heavy());
		break;
	default:
		ASC->AddLooseGameplayTag(RobotTags::Chassis_Medium());
		break;
	}

	UE_LOG(LogTemp, Verbose,
		TEXT("装配已应用：质量 %.2f  速度 %.1f  供电 %d/%d  散热 %.1f"),
		Mass, Speed,
		FMath::RoundToInt(GetTotalPowerDraw()),
		FMath::RoundToInt(Chassis->PowerCapacity),
		GetTotalHeatDissipation());
}

void UAssemblyComponent::NotifyChanged()
{
	OnAssemblyChanged.Broadcast();
}
