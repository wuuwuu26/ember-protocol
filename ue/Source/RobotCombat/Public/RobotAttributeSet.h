// 电力与热量 —— 战斗节奏的核心杠杆
#pragma once

#include "CoreMinimal.h"
#include "AbilitySystemComponent.h"
#include "AttributeSet.h"
#include "RobotAttributeSet.generated.h"

#define ATTRIBUTE_ACCESSORS(ClassName, PropertyName) \
	GAMEPLAYATTRIBUTE_PROPERTY_GETTER(ClassName, PropertyName) \
	GAMEPLAYATTRIBUTE_VALUE_GETTER(PropertyName) \
	GAMEPLAYATTRIBUTE_VALUE_SETTER(PropertyName) \
	GAMEPLAYATTRIBUTE_VALUE_INITTER(PropertyName)

/**
 * 电力 / 热量属性集。
 *
 * 设计要点：热量是"反向资源"—— 只涨，不自动降。攻击、冲刺、过载都加热量，
 * 热量只能通过散热动作下降。这是"爆发窗口 — 强制停顿"节奏的来源。
 *
 * 如果玩家从不看热量条，说明这个杠杆失效，需要重画，而不是调数值。
 */
UCLASS()
class ROBOTCOMBAT_API URobotAttributeSet : public UAttributeSet
{
	GENERATED_BODY()

public:
	URobotAttributeSet();

	// ── 电力：主动模块的消耗池 ──

	UPROPERTY(BlueprintReadOnly, Category = "Robot|Power")
	FGameplayAttributeData Power;
	ATTRIBUTE_ACCESSORS(URobotAttributeSet, Power);

	UPROPERTY(BlueprintReadOnly, Category = "Robot|Power")
	FGameplayAttributeData MaxPower;
	ATTRIBUTE_ACCESSORS(URobotAttributeSet, MaxPower);

	UPROPERTY(BlueprintReadOnly, Category = "Robot|Power")
	FGameplayAttributeData PowerRegen;
	ATTRIBUTE_ACCESSORS(URobotAttributeSet, PowerRegen);

	// ── 热量：只涨不自动降 ──

	UPROPERTY(BlueprintReadOnly, Category = "Robot|Heat")
	FGameplayAttributeData Heat;
	ATTRIBUTE_ACCESSORS(URobotAttributeSet, Heat);

	UPROPERTY(BlueprintReadOnly, Category = "Robot|Heat")
	FGameplayAttributeData MaxHeat;
	ATTRIBUTE_ACCESSORS(URobotAttributeSet, MaxHeat);

	/** 每秒散热速率。由底盘与辅助模块共同决定。 */
	UPROPERTY(BlueprintReadOnly, Category = "Robot|Heat")
	FGameplayAttributeData HeatDissipationRate;
	ATTRIBUTE_ACCESSORS(URobotAttributeSet, HeatDissipationRate);

	// ── 派生查询 ──

	/** 是否已达过热阈值 */
	UFUNCTION(BlueprintPure, Category = "Robot|Heat")
	bool IsOverheated() const;

	/** 热量占比，用于 UI 与调试 */
	UFUNCTION(BlueprintPure, Category = "Robot|Heat")
	float GetHeatRatio() const;

	/** 在当前散热速率下，还能连续输出多久（秒）。调试与平衡用。 */
	UFUNCTION(BlueprintPure, Category = "Robot|Heat")
	float GetRemainingUptime(float HeatPerSecond) const;

protected:
	/**
	 * 属性变更前拦截。这里做钳制 —— 比在每个 GameplayEffect 里
	 * 单独写 Clamp 更不容易漏。
	 */
	virtual void PreAttributeChange(const FGameplayAttribute& Attribute,
	                                float& NewValue) override;

	virtual void PostGameplayEffectExecute(
		const struct FGameplayEffectModCallbackData& Data) override;
};
