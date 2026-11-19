#include "UI/RobotFloatLabelLayer.h"

#include "Layout/ArrangedChildren.h"
#include "Layout/Children.h"
#include "Widgets/SBoxPanel.h"

void SRobotFloatLabelLayer::Construct(const FArguments& InArgs)
{
	// 用引擎现成的 TSlotlessChildren：它已经实现了 FChildren 的全部纯虚函数，
	// 而且子控件列表是 public 的 add。我们只需要自己管"每个子控件摆在哪"。
	ChildList = MakeShared<TSlotlessChildren<SWidget>>(this);
}

FChildren* SRobotFloatLabelLayer::GetChildren()
{
	return ChildList.Get();
}

int32 SRobotFloatLabelLayer::AddLabel(TSharedRef<SWidget> InChild)
{
	const int32 Index = ChildList->Add(InChild);
	Positions.SetNum(FMath::Max(Positions.Num(), Index + 1));
	return Index;
}

void SRobotFloatLabelLayer::SetLabelPosition(int32 Index, const FVector2D& InPosition)
{
	if (Positions.IsValidIndex(Index))
	{
		Positions[Index] = InPosition;
	}
}

void SRobotFloatLabelLayer::OnArrangeChildren(const FGeometry& AllottedGeometry,
	FArrangedChildren& ArrangedChildren) const
{
	if (!ChildList.IsValid())
	{
		return;
	}
	const int32 Count = ChildList->Num();
	for (int32 i = 0; i < Count; ++i)
	{
		const TSharedRef<SWidget>& Child = ChildList->GetChildAt(i);
		const EVisibility ChildVis = Child->GetVisibility();
		if (!ArrangedChildren.Accepts(ChildVis))
		{
			continue;
		}
		const FVector2D Pos = Positions.IsValidIndex(i)
			? Positions[i] : FVector2D::ZeroVector;
		const FVector2D Size = Child->GetDesiredSize();
		// 以 Pos 为**中心**摆放：伤害数字从命中点正上方冒出来。
		// MakeChild 的第三个参数是"布局缩放补偿"，1.0 = 用局部单位。
		ArrangedChildren.AddWidget(ChildVis,
			AllottedGeometry.MakeChild(Child, Pos - Size * 0.5f, Size, 1.f));
	}
}

FVector2D SRobotFloatLabelLayer::ComputeDesiredSize(float) const
{
	// 本身不占布局空间（由外层 SBox 固定 1280x720 撑开）
	return FVector2D::ZeroVector;
}
