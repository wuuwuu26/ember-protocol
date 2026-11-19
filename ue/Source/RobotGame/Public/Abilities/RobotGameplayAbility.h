// 技能基类 —— 统一访问角色、属性、装配
#pragma once

#include "CoreMinimal.h"
#include "Abilities/GameplayAbility.h"
#include "RobotGameplayAbility.generated.h"

class ARobotCharacter;
class URobotAttributeSet;
class UAssemblyComponent;
class URobotChassisData;

/**
 * 所有机体技能的基类。
 *
 * 提供三件所有技能都需要的事：拿到角色、拿到属性、拿到装配数据。
 * 子类不该自己去找这些 —— 找的写法一旦不统一，后面每个技能都会
 * 各写一套容错逻辑。
 */
UCLASS(Abstract)
class ROBOTGAME_API URobotGameplayAbility : public UGameplayAbility
{
	GENERATED_BODY()

public:
	URobotGameplayAbility();

protected:
	UFUNCTION(BlueprintPure, Category = "Robot|Ability")
	ARobotCharacter* GetRobotCharacter() const;

	UFUNCTION(BlueprintPure, Category = "Robot|Ability")
	URobotAttributeSet* GetRobotAttributes() const;

	UFUNCTION(BlueprintPure, Category = "Robot|Ability")
	UAssemblyComponent* GetAssembly() const;

	UFUNCTION(BlueprintPure, Category = "Robot|Ability")
	const URobotChassisData* GetChassis() const;

	/** 当前是否过热。过热时不应消耗资源，直接拒绝施放。 */
	UFUNCTION(BlueprintPure, Category = "Robot|Ability")
	bool IsOverheated() const;

	// ── 资源结算 ──
	// 用 ApplyModToAttribute 而不是 GameplayEffect 资产：
	// 消耗量来自装配数据（可随模块变化），写死在 GE 里就失去数据驱动能力。
	// 且 ApplyModToAttribute 会正常触发 AttributeSet 的变更回调与状态广播。

	/** 扣电力。返回 false 表示电力不足，调用方应中止施放。 */
	UFUNCTION(BlueprintCallable, Category = "Robot|Ability")
	bool ConsumePower(float Amount);

	/** 加热量。热量达上限会由 AttributeSet 自动打上 State.Overheated 标签。 */
	UFUNCTION(BlueprintCallable, Category = "Robot|Ability")
	void AddHeat(float Amount);
};
