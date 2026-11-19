// 余火协议 —— 基础类型与 GameplayTag 声明
#pragma once

#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "Engine/DataAsset.h"
#include "RobotTypes.generated.h"

/**
 * 机体分类。三条约束（质量 / 供电 / 散热）的差异是设计支柱 P1 的落点：
 * 换机体必须改变玩法，而不只是改变数值。
 */
UENUM(BlueprintType)
enum class EChassisClass : uint8
{
	Light   UMETA(DisplayName = "轻型侦察"),
	Medium  UMETA(DisplayName = "中型通用"),
	Heavy   UMETA(DisplayName = "重型攻坚")
};

/** 模块插槽。固定插槽是防止"任意零件自由拼接"导致组合爆炸的第一道闸门。 */
UENUM(BlueprintType)
enum class EModuleSlot : uint8
{
	Head          UMETA(DisplayName = "头部"),
	Core          UMETA(DisplayName = "核心"),
	ArmLeft       UMETA(DisplayName = "左臂"),
	ArmRight      UMETA(DisplayName = "右臂"),
	ThrusterLeft  UMETA(DisplayName = "左推进器"),
	ThrusterRight UMETA(DisplayName = "右推进器"),
	Backpack      UMETA(DisplayName = "背包"),
	Aux01         UMETA(DisplayName = "辅助槽 1"),
	Aux02         UMETA(DisplayName = "辅助槽 2")
};

/** 插槽定义。SocketName 必须与 Blender 导出的挂点命名一致。 */
USTRUCT(BlueprintType)
struct FModuleSlotDef
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Slot")
	EModuleSlot Slot = EModuleSlot::Head;

	/** 骨骼网格体上的 Socket 名，例如 socket_head / socket_arm_L */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Slot")
	FName SocketName;

	/** 该槽位接受的模块类型标签，用于改装界面的筛选 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Slot")
	FGameplayTagContainer AcceptedModuleTypes;
};

/** 单个部位的血量。部位数量随敌人而变，所以不进 GAS AttributeSet。 */
USTRUCT(BlueprintType)
struct FPartHealth
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Part")
	FGameplayTag PartTag;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Part")
	float MaxHealth = 20.f;

	UPROPERTY(BlueprintReadOnly, Category = "Part")
	float CurrentHealth = 20.f;

	/** 摧毁后掉落的废料价值。躯干为 0 —— 它只是伤害承受面，不是收获。 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Part")
	int32 SalvageValue = 5;

	bool IsDestroyed() const { return CurrentHealth <= 0.f; }
	float GetRatio() const { return MaxHealth > 0.f ? CurrentHealth / MaxHealth : 0.f; }
};

/**
 * GameplayTag 声明集中在这里，避免各处硬编码字符串。
 * 在 DefaultGameplayTags.ini 里同步登记这些 Tag。
 */
namespace RobotTags
{
	// 机体
	ROBOTCORE_API FGameplayTag Chassis_Light();
	ROBOTCORE_API FGameplayTag Chassis_Medium();
	ROBOTCORE_API FGameplayTag Chassis_Heavy();

	// 部位
	ROBOTCORE_API FGameplayTag Part_Core();
	ROBOTCORE_API FGameplayTag Part_Torso();
	ROBOTCORE_API FGameplayTag Part_Arm_L();
	ROBOTCORE_API FGameplayTag Part_Arm_R();
	ROBOTCORE_API FGameplayTag Part_Leg_L();
	ROBOTCORE_API FGameplayTag Part_Leg_R();

	// 状态
	ROBOTCORE_API FGameplayTag State_Overheated();
	ROBOTCORE_API FGameplayTag State_Disabled();
	ROBOTCORE_API FGameplayTag State_Repairable();
}
