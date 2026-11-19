// 模块数据资产
#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "GameplayTagContainer.h"
#include "RobotTypes.h"
// 必须带出完整定义，UHT 生成的 .gen.cpp 里要引用 Z_Construct_UClass_UGameplayAbility。
#include "Abilities/GameplayAbility.h"
#include "RobotModuleData.generated.h"

class UStaticMesh;
class USkeletalMesh;

/**
 * 可换装模块。
 *
 * 设计纪律（支柱 P1）：每个模块必须回答"它带来了什么新的移动方式或
 * 战斗解法"。只加数值的模块一律砍掉 —— 这条规则写在代码里，
 * 由 IsDataValid 强制检查。
 */
UCLASS(BlueprintType)
class ROBOTCORE_API URobotModuleData : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Identity")
	FText DisplayName;

	/** 模块类型标签，例如 Module.Type.Arm.Weapon */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Identity")
	FGameplayTag ModuleType;

	/** 只能装在哪些槽位 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Identity")
	EModuleSlot TargetSlot = EModuleSlot::Head;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Identity")
	TSoftObjectPtr<UStaticMesh> ModuleMesh;

	// ─────────────────────────────────────────────
	// 对三条约束的影响
	// ─────────────────────────────────────────────

	/** 自身质量，累加到机体总质量 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Constraints")
	float Mass = 0.2f;

	/** 持续耗电（被动模块）。主动模块的瞬时消耗走 GAS 技能。 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Constraints")
	float PowerDraw = 0.f;

	/** 散热加成（可为负 —— 高输出模块应该让散热变差） */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Constraints")
	float HeatDissipationModifier = 0.f;

	/** 热量容量加成 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Constraints")
	float HeatCapacityModifier = 0.f;

	// ─────────────────────────────────────────────
	// 武器臂乘数（只有武器臂模块使用，其它模块保持 1.0）
	// ─────────────────────────────────────────────
	//
	// 机体提供武器"档位"（伤害/射速/积热都按机体配），武器臂在其上做乘法：
	//   加农臂：伤害 ×1.45、射速变慢 ×1.40 —— 慢速重炮
	//   采矿臂：伤害 ×0.75、射速变快 ×0.70 —— 高速点射
	// 左右两条臂的乘数**叠乘**（双臂加农 = 1.45² ≈ 2.1 倍伤害、射速减半），
	// 这让"装什么臂"成为真实的输出风格选择，而不只是三条约束的加减。

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Weapon")
	float WeaponDamageMult = 1.0f;

	/** 射速间隔乘数：<1 = 更快，>1 = 更慢 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Weapon")
	float WeaponFireIntervalMult = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Weapon")
	float WeaponHeatMult = 1.0f;

	// ─────────────────────────────────────────────
	// 解锁与经济
	// ─────────────────────────────────────────────

	/** 制造所需材料 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Economy")
	int32 MaterialCost = 40;

	/**
	 * 是否需要稀有核心才能解锁。
	 * 稀有核心只来自具名敌人与关键任务，数量有限、不可刷 ——
	 * 这是阻止"拆解无限产出 → 材料通胀"的第一道闸门。
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Economy")
	bool bRequiresRareCore = false;

	/** 该模块赋予的技能（GAS） */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Gameplay")
	TArray<TSoftClassPtr<UGameplayAbility>> GrantedAbilities;

	/** 该模块让机体获得的新移动能力标签，例如 Traversal.Climb.Magnetic */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Gameplay")
	FGameplayTagContainer GrantedTraversalTags;

#if WITH_EDITOR
	virtual EDataValidationResult IsDataValid(class FDataValidationContext& Context) const override;
#endif
};
