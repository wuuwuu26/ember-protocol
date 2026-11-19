#include "RobotTypes.h"
#include "Modules/ModuleManager.h"

IMPLEMENT_MODULE(FDefaultGameModuleImpl, RobotCore);

/**
 * Tag 取值统一走这里，避免全工程硬编码字符串。
 *
 * 注意：这里用 bErrorIfNotFound=false。原因是这些 Tag 需要在
 * Config/DefaultGameplayTags.ini 中登记后才存在，而 ini 的加载时机
 * 早于某些静态初始化场景 —— 用 true 会在编辑器启动期直接断言崩溃。
 * 上线前应改为 true，让缺失的 Tag 在开发期就暴露出来。
 */
namespace RobotTags
{
	static FGameplayTag Tag(const TCHAR* Name)
	{
		return FGameplayTag::RequestGameplayTag(FName(Name), /*ErrorIfNotFound=*/false);
	}

	FGameplayTag Chassis_Light()  { return Tag(TEXT("Chassis.Light")); }
	FGameplayTag Chassis_Medium() { return Tag(TEXT("Chassis.Medium")); }
	FGameplayTag Chassis_Heavy()  { return Tag(TEXT("Chassis.Heavy")); }

	FGameplayTag Part_Core()  { return Tag(TEXT("Part.Core")); }
	FGameplayTag Part_Torso() { return Tag(TEXT("Part.Torso")); }
	FGameplayTag Part_Arm_L() { return Tag(TEXT("Part.Arm.L")); }
	FGameplayTag Part_Arm_R() { return Tag(TEXT("Part.Arm.R")); }
	FGameplayTag Part_Leg_L() { return Tag(TEXT("Part.Leg.L")); }
	FGameplayTag Part_Leg_R() { return Tag(TEXT("Part.Leg.R")); }

	FGameplayTag State_Overheated() { return Tag(TEXT("State.Overheated")); }
	FGameplayTag State_Disabled()   { return Tag(TEXT("State.Disabled")); }
	FGameplayTag State_Repairable() { return Tag(TEXT("State.Repairable")); }
}
