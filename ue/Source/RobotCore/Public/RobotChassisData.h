// 机体数据资产 —— 所有可调数值的唯一来源
#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "GameplayTagContainer.h"
#include "RobotTypes.h"
#include "RobotChassisData.generated.h"

class USkeletalMesh;

/**
 * 机体配置。
 *
 * 设计纪律：任何没有 rationale 的数值都不该出现在这里。
 * 三条约束（Mass / PowerCapacity / HeatDissipation）互相牵制，
 * 是防止"一套最优解通吃"的核心机制 —— 去掉任何一条，40 个模块
 * 就退化成 40 张数值贴纸。
 */
UCLASS(BlueprintType)
class ROBOTCORE_API URobotChassisData : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Identity")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Identity")
	EChassisClass ChassisClass = EChassisClass::Medium;

	/** 对应 Blender 导出的 chassis_light / chassis_medium / chassis_heavy */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Identity")
	TSoftObjectPtr<USkeletalMesh> ChassisMesh;

	// ─────────────────────────────────────────────
	// 三条约束
	// ─────────────────────────────────────────────

	/** 质量。直接决定移动速度：Speed = BaseWalkSpeed / Mass */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Constraints", meta = (ClampMin = "0.1"))
	float Mass = 1.5f;

	/** 供电上限。所有主动模块共享这个额度，强制取舍。 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Constraints", meta = (ClampMin = "1.0"))
	float PowerCapacity = 100.f;

	/** 热量上限。达到即触发过热锁定。 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Constraints", meta = (ClampMin = "1.0"))
	float HeatCapacity = 100.f;

	/** 散热速率。连续输出时长的决定因素。 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Constraints", meta = (ClampMin = "0.0"))
	float HeatDissipation = 22.f;

	/** 电力回复速率 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Constraints", meta = (ClampMin = "0.0"))
	float PowerRegen = 13.f;

	// ─────────────────────────────────────────────
	// 运动
	// ─────────────────────────────────────────────

	/** 质量 1.0 时的基准速度，实际速度 = BaseWalkSpeed / Mass */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Movement")
	float BaseWalkSpeed = 232.f;

	/** 冲刺消耗的电力 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Movement")
	float DashPowerCost = 22.f;

	// ─────────────────────────────────────────────
	// 武器（机体耦合的射击参数）
	// ─────────────────────────────────────────────
	//
	// 为什么武器参数在机体数据里：三台机体的散热能力天差地别
	// （34 / 22 / 13），如果武器打同一个热量，节奏会完全不同 ——
	// 轻型机永远不过热、重型机两三发就锁。浏览器原型里
	// 伤害/射速/热量就是按机体配的（loadout 表），UE 版对齐这个设计：
	//
	//   轻型侦察：8/发 · 0.115s · 6.5 热   → 高速低伤、长爆发（约 38 发过热）
	//   中型通用：15/发 · 0.19s · 11.5 热  → 均衡（约 13 发过热）
	//   重型攻坚：27/发 · 0.30s · 18 热    → 慢速高伤、短爆发（约 8 发过热）
	//
	// ⚠️ 射击**不耗电**（WeaponPowerPerShot 默认 0）：电力是机动资源
	// （冲刺 + 模块待机耗电），热量才是射击节奏的约束。
	// 两道成本都压在射击上时数值互相抵消、两种机制同时失效（已实测踩坑）。

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Weapon", meta = (ClampMin = "0.0"))
	float WeaponDamage = 15.f;

	/** 两次射击的最小间隔（秒） */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Weapon", meta = (ClampMin = "0.01"))
	float WeaponFireInterval = 0.19f;

	/** 每发积热 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Weapon", meta = (ClampMin = "0.0"))
	float WeaponHeatPerShot = 11.5f;

	/** 每发耗电。默认 0 = 纯热约束（详见上面注释） */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Weapon", meta = (ClampMin = "0.0"))
	float WeaponPowerPerShot = 0.f;

	// ─────────────────────────────────────────────
	// 插槽
	// ─────────────────────────────────────────────

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Assembly")
	TArray<FModuleSlotDef> Slots;

	// ─────────────────────────────────────────────
	// 派生值
	// ─────────────────────────────────────────────

	/** 按质量换算实际移动速度 */
	UFUNCTION(BlueprintPure, Category = "Robot|Chassis")
	float GetEffectiveWalkSpeed() const
	{
		return Mass > KINDA_SMALL_NUMBER ? BaseWalkSpeed / Mass : BaseWalkSpeed;
	}

	/** 该槽位是否接受这个模块类型 */
	UFUNCTION(BlueprintPure, Category = "Robot|Chassis")
	bool AcceptsModuleInSlot(EModuleSlot Slot, const FGameplayTag& ModuleType) const;

#if WITH_EDITOR
	/** 数据校验：插槽名、数值合理性。在编辑器里点 Validate 即可跑。 */
	virtual EDataValidationResult IsDataValid(class FDataValidationContext& Context) const override;
#endif
};
