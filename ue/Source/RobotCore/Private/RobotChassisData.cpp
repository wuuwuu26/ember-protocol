#include "RobotChassisData.h"
#include "Misc/DataValidation.h"

bool URobotChassisData::AcceptsModuleInSlot(EModuleSlot InSlot,
                                            const FGameplayTag& ModuleType) const
{
	for (const FModuleSlotDef& Def : Slots)
	{
		if (Def.Slot != InSlot)
		{
			continue;
		}
		// 空标签容器视为"不限制"——辅助槽通常这样配
		if (Def.AcceptedModuleTypes.IsEmpty())
		{
			return true;
		}
		return Def.AcceptedModuleTypes.HasTag(ModuleType);
	}
	return false;
}

#if WITH_EDITOR
EDataValidationResult URobotChassisData::IsDataValid(FDataValidationContext& Context) const
{
	EDataValidationResult Result = Super::IsDataValid(Context);

	// 三条约束必须同时存在，缺一条整个取舍设计就塌了
	if (Mass <= 0.f)
	{
		Context.AddError(FText::FromString(TEXT("Mass 必须大于 0，否则速度换算会除零")));
		Result = EDataValidationResult::Invalid;
	}
	if (PowerCapacity <= 0.f)
	{
		Context.AddError(FText::FromString(TEXT("PowerCapacity 必须大于 0")));
		Result = EDataValidationResult::Invalid;
	}
	if (HeatDissipation <= 0.f)
	{
		Context.AddWarning(FText::FromString(
			TEXT("HeatDissipation 为 0：该机体将无法连续输出，确认这是有意设计")));
	}

	// 插槽名不能为空，且不能重复
	TSet<FName> SeenSockets;
	TSet<EModuleSlot> SeenSlots;
	for (const FModuleSlotDef& Def : Slots)
	{
		if (Def.SocketName.IsNone())
		{
			Context.AddError(FText::FromString(
				TEXT("插槽缺少 SocketName —— 必须与 Blender 导出的 socket_* 命名一致")));
			Result = EDataValidationResult::Invalid;
		}
		if (SeenSockets.Contains(Def.SocketName))
		{
			Context.AddError(FText::Format(
				FText::FromString(TEXT("SocketName 重复：{0}")),
				FText::FromName(Def.SocketName)));
			Result = EDataValidationResult::Invalid;
		}
		if (SeenSlots.Contains(Def.Slot))
		{
			Context.AddError(FText::Format(
				FText::FromString(TEXT("插槽类型重复：{0}")),
				FText::AsNumber(static_cast<int32>(Def.Slot))));
			Result = EDataValidationResult::Invalid;
		}
		SeenSockets.Add(Def.SocketName);
		SeenSlots.Add(Def.Slot);
	}

	if (Slots.Num() == 0)
	{
		Context.AddWarning(FText::FromString(TEXT("该机体没有任何插槽，将无法改装")));
	}

	return Result;
}
#endif
