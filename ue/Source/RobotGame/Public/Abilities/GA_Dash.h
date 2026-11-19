// GA_Dash —— 冲刺。核心循环里「电力 → 热量 → 过热」链路的第一环。
#pragma once

#include "CoreMinimal.h"
#include "Abilities/RobotGameplayAbility.h"
#include "GA_Dash.generated.h"

/**
 * 冲刺技能。
 *
 * 设计意图（对应制作计划 3.3）：冲刺同时消耗电力、产生热量，
 * 让玩家在"拉近距离/脱离"和"保留散热余量"之间做取舍。
 * 过热时通过 ActivationBlockedTags 直接拒绝施放 —— 不需要在代码里
 * 到处写 if (IsOverheated())，标签系统会统一拦截。
 */
UCLASS()
class ROBOTGAME_API UGA_Dash : public URobotGameplayAbility
{
	GENERATED_BODY()

public:
	UGA_Dash();

	virtual void ActivateAbility(const FGameplayAbilitySpecHandle Handle,
		const FGameplayAbilityActorInfo* ActorInfo,
		const FGameplayAbilityActivationInfo ActivationInfo,
		const FGameplayEventData* TriggerEventData) override;

protected:
	/** 冲刺初速度（cm/s）。质量越大实际位移越小，因为 CMC 会按质量减速。 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Dash", meta = (ClampMin = "0"))
	float DashStrength = 1400.f;

	/** 单次冲刺产生的热量 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Dash", meta = (ClampMin = "0"))
	float HeatPerDash = 12.f;

	/** 冲刺期间的无敌时间（秒） */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Dash", meta = (ClampMin = "0"))
	float InvulnerableTime = 0.22f;
};
