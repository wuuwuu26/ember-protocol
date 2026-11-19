// 每帧绝对定位的浮动文字容器。
//
// 为什么自己写一个 SPanel 而不是用 SCanvas：SCanvas 的子槽位位置是 Slate 属性
// （TAttribute），外部想每帧改它必须拿到 FSlot 指针，而 GetChildren() 里
// 返回的是基类 —— 安全反转又取决于引擎内部容器类型。这里直接写一个
// "只按坐标摆放子控件"的轻量面板，位置存在自己的数组里：完全公开、
// 直接可写、没有类型转换，也不重建 Slate 树。
#pragma once

#include "CoreMinimal.h"
#include "Widgets/SPanel.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

/** 一条浮动标签：文字控件 + 画布坐标 */
struct FRobotFloatLabel
{
	TSharedPtr<class STextBlock> Text;
	FVector2D Position = FVector2D::ZeroVector;
};

/** 面板：按 Position 绝对摆放子控件（子控件尺寸取自身 DesiredSize） */
class SRobotFloatLabelLayer : public SPanel
{
public:
	SLATE_BEGIN_ARGS(SRobotFloatLabelLayer) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	//~ Begin SWidget
	virtual FChildren* GetChildren() override;
	virtual void OnArrangeChildren(const FGeometry& AllottedGeometry,
		FArrangedChildren& ArrangedChildren) const override;
	//~ End SWidget

	/** 追加一条标签（只增不减；位置变化走 SetLabelPosition） */
	int32 AddLabel(TSharedRef<class SWidget> InChild);

	/** 设置第 Index 条标签的位置（画布坐标，以控件中心为准） */
	void SetLabelPosition(int32 Index, const FVector2D& InPosition);

protected:
	virtual FVector2D ComputeDesiredSize(float LayoutScaleMultiplier) const override;

private:
	/** 子控件列表（用引擎的 TSlotlessChildren：已经实现了 FChildren 全部接口） */
	TSharedPtr<class TSlotlessChildren<class SWidget>> ChildList;

	/** 每条标签的中心位置（画布坐标） */
	TArray<FVector2D> Positions;
};
