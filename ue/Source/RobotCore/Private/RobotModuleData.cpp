#include "RobotModuleData.h"
#include "Misc/DataValidation.h"

#if WITH_EDITOR
EDataValidationResult URobotModuleData::IsDataValid(FDataValidationContext& Context) const
{
	EDataValidationResult Result = Super::IsDataValid(Context);

	if (DisplayName.IsEmpty())
	{
		Context.AddWarning(FText::FromString(TEXT("模块缺少显示名，改装界面会显示空白")));
	}

	if (!ModuleType.IsValid())
	{
		Context.AddError(FText::FromString(
			TEXT("ModuleType 未设置 —— 改装界面无法筛选，插槽校验也会失效")));
		Result = EDataValidationResult::Invalid;
	}

	// 支柱 P1 的代码化：模块必须提供新的能力，而不只是数值
	const bool bGrantsAbility = GrantedAbilities.Num() > 0;
	const bool bGrantsTraversal = !GrantedTraversalTags.IsEmpty();
	const bool bIsPureUtility =
		FMath::IsNearlyZero(PowerDraw) &&
		FMath::IsNearlyZero(HeatDissipationModifier) &&
		FMath::IsNearlyZero(HeatCapacityModifier);

	if (!bGrantsAbility && !bGrantsTraversal && bIsPureUtility)
	{
		Context.AddWarning(FText::Format(
			FText::FromString(
				TEXT("模块「{0}」既不给技能、不给移动能力、也不改散热/供电 —— "
					 "按设计支柱 P1，只加数值的模块应当砍掉")),
			DisplayName));
	}

	if (Mass <= 0.f)
	{
		Context.AddError(FText::FromString(TEXT("Mass 必须大于 0")));
		Result = EDataValidationResult::Invalid;
	}

	// 高输出模块理应让散热变差，这是取舍成立的前提
	if (PowerDraw > 30.f && HeatDissipationModifier > 0.f)
	{
		Context.AddWarning(FText::FromString(
			TEXT("高耗电模块同时提供散热加成 —— 这会产生无代价的最优解，请确认是有意设计")));
	}

	return Result;
}
#endif
