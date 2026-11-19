#include "RobotAttributeSet.h"
#include "GameplayEffectExtension.h"
#include "RobotTypes.h"

URobotAttributeSet::URobotAttributeSet()
{
	// 初始值只是占位，实际值由 ChassisData 在角色初始化时写入。
	// 未经验证的数值一律视为 PLACEHOLDER。
	InitPower(100.f);
	InitMaxPower(100.f);
	InitPowerRegen(13.f);

	InitHeat(0.f);
	InitMaxHeat(100.f);
	InitHeatDissipationRate(22.f);
}

bool URobotAttributeSet::IsOverheated() const
{
	const float Max = GetMaxHeat();
	return Max > KINDA_SMALL_NUMBER && GetHeat() >= Max;
}

float URobotAttributeSet::GetHeatRatio() const
{
	const float Max = GetMaxHeat();
	return Max > KINDA_SMALL_NUMBER ? FMath::Clamp(GetHeat() / Max, 0.f, 1.f) : 0.f;
}

float URobotAttributeSet::GetRemainingUptime(float HeatPerSecond) const
{
	const float NetHeat = HeatPerSecond - GetHeatDissipationRate();
	if (NetHeat <= KINDA_SMALL_NUMBER)
	{
		// 散热快于积热 —— 可以无限持续输出，这本身就是一个平衡信号
		return TNumericLimits<float>::Max();
	}
	return FMath::Max(0.f, GetMaxHeat() - GetHeat()) / NetHeat;
}

void URobotAttributeSet::PreAttributeChange(const FGameplayAttribute& Attribute,
                                            float& NewValue)
{
	Super::PreAttributeChange(Attribute, NewValue);

	if (Attribute == GetPowerAttribute())
	{
		NewValue = FMath::Clamp(NewValue, 0.f, GetMaxPower());
	}
	else if (Attribute == GetHeatAttribute())
	{
		NewValue = FMath::Clamp(NewValue, 0.f, GetMaxHeat());
	}
	else if (Attribute == GetMaxPowerAttribute())
	{
		NewValue = FMath::Max(NewValue, 1.f);
	}
	else if (Attribute == GetMaxHeatAttribute())
	{
		NewValue = FMath::Max(NewValue, 1.f);
	}
	else if (Attribute == GetHeatDissipationRateAttribute())
	{
		NewValue = FMath::Max(NewValue, 0.f);
	}
}

void URobotAttributeSet::PostGameplayEffectExecute(
	const FGameplayEffectModCallbackData& Data)
{
	Super::PostGameplayEffectExecute(Data);

	if (Data.EvaluatedData.Attribute == GetHeatAttribute())
	{
		// 注意：FGameplayEffectModCallbackData::Target 是 UAbilitySystemComponent&
		// （引用，不是指针）。写成 Data.Target-> 会报 C2679/C2819/C2232。
		if (IsOverheated())
		{
			Data.Target.AddLooseGameplayTag(RobotTags::State_Overheated());
		}
		else
		{
			Data.Target.RemoveLooseGameplayTag(RobotTags::State_Overheated());
		}
	}
}
