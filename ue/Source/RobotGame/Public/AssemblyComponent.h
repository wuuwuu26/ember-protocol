// 机体装配 —— 改装玩法的落点
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "RobotTypes.h"
#include "AssemblyComponent.generated.h"

class URobotChassisData;
class URobotModuleData;
class UAbilitySystemComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnAssemblyChanged);

/**
 * 机体装配组件。
 *
 * 职责：管理"当前机体 + 已装配模块"，并汇总三条约束。
 * 约束汇总之后由 ApplyToAbilitySystem 写入 GAS 属性 ——
 * 这样战斗系统不需要知道模块的存在，只认属性。
 *
 * 三条约束必须互相牵制。任何一条可以被忽略，整套取舍就会塌成
 * "堆最高的数值"。所以 CanMount 对供电做硬校验，对质量做软提示。
 */
UCLASS(ClassGroup = (Robot), meta = (BlueprintSpawnableComponent))
class ROBOTGAME_API UAssemblyComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UAssemblyComponent();

	/** 当前机体。运行时切换机体走 SetChassis，不要直接改这个指针。 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
	TObjectPtr<URobotChassisData> Chassis;

	UPROPERTY(BlueprintReadOnly, Category = "Robot|Assembly")
	TMap<EModuleSlot, TObjectPtr<URobotModuleData>> MountedModules;

	UPROPERTY(BlueprintAssignable, Category = "Robot|Assembly")
	FOnAssemblyChanged OnAssemblyChanged;

	// ── 装配操作 ──

	/** 能否装配。失败时 OutReason 给出面向玩家的原因，可直接显示在改装界面。 */
	UFUNCTION(BlueprintCallable, Category = "Robot|Assembly")
	bool CanMount(EModuleSlot Slot, URobotModuleData* Module, FText& OutReason) const;

	UFUNCTION(BlueprintCallable, Category = "Robot|Assembly")
	bool MountModule(EModuleSlot Slot, URobotModuleData* Module);

	UFUNCTION(BlueprintCallable, Category = "Robot|Assembly")
	void UnmountModule(EModuleSlot Slot);

	UFUNCTION(BlueprintCallable, Category = "Robot|Assembly")
	void SetChassis(URobotChassisData* NewChassis);

	UFUNCTION(BlueprintPure, Category = "Robot|Assembly")
	URobotModuleData* GetModule(EModuleSlot Slot) const;

	// ── 三条约束的汇总 ──

	/** 机体质量 + 所有模块质量 */
	UFUNCTION(BlueprintPure, Category = "Robot|Assembly")
	float GetTotalMass() const;

	/** 所有被动模块的持续耗电 */
	UFUNCTION(BlueprintPure, Category = "Robot|Assembly")
	float GetTotalPowerDraw() const;

	/** 供电余量。负数表示超载，装配界面必须把它显示成红色。 */
	UFUNCTION(BlueprintPure, Category = "Robot|Assembly")
	float GetPowerHeadroom() const;

	UFUNCTION(BlueprintPure, Category = "Robot|Assembly")
	float GetTotalHeatDissipation() const;

	UFUNCTION(BlueprintPure, Category = "Robot|Assembly")
	float GetTotalHeatCapacity() const;

	/** 实际移动速度 = Chassis.BaseWalkSpeed / 总质量 */
	UFUNCTION(BlueprintPure, Category = "Robot|Assembly")
	float GetEffectiveWalkSpeed() const;

	/**
	 * 当前武器档位：机体基础值 × 左右武器臂乘数（叠乘）。
	 * GA_Fire 与改装界面共用这一个来源 —— 两边各算一份必然对不上。
	 */
	void GetWeaponProfile(float& OutDamage, float& OutFireInterval,
		float& OutHeatPerShot) const;

	/** 把三条约束写进 GAS。装配变更后必须调用。 */
	UFUNCTION(BlueprintCallable, Category = "Robot|Assembly")
	void ApplyToAbilitySystem(UAbilitySystemComponent* ASC);

	/** 该模块带来的移动能力标签（攀爬、钩索等），供移动系统查询 */
	UFUNCTION(BlueprintPure, Category = "Robot|Assembly")
	FGameplayTagContainer GetGrantedTraversalTags() const;

protected:
	virtual void BeginPlay() override;

private:
	/** 广播变更并重新应用属性 */
	void NotifyChanged();
};
