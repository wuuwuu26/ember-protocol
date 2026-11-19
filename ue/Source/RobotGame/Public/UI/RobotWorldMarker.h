// 世界空间浮动标记 —— 命中伤害数字 / 部位易伤提示
//
// 为什么不用每个标记一个独立 Slate 控件去"追"世界坐标：
// Slate 没有世界坐标锚点，每加一簇伤害数字就要往视口里塞一个 widget，
// 几十个同时存在时布局开销不可控。这里改成"一个绝对定位面板 + 按需池化"：
// 每帧把世界点投影到 1280x720 设计画布上，再摆放文字。
// 控件数量恒定（上限 18 个），任何分辨率下都不会错位，也不重建 Slate 树。
//
// 数据来源：ARobotPlayerController::GetDamageNumber / GetPartHint。
// 这个控件只管"怎么画"，不持有任何游戏逻辑。
#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

class ARobotPlayerController;
class SRobotFloatLabelLayer;

class SRobotWorldMarkers : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SRobotWorldMarkers) {}
		SLATE_ARGUMENT(TWeakObjectPtr<class APlayerController>, Owner)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	virtual void Tick(const FGeometry& AllottedGeometry,
		const double InCurrentTime, const float InDeltaTime) override;

	/** 画布尺寸（和 HUD 一致：1280x720 设计画布等比缩放） */
	static constexpr float DesignW = 1280.f;
	static constexpr float DesignH = 720.f;

private:
	struct FFloatTextItem
	{
		TSharedPtr<class STextBlock> Label;
	};

	ARobotPlayerController* GetPC() const;

	/** 世界坐标 -> 设计画布坐标。返回 false 表示在相机背后 / 窗口外 */
	bool WorldToCanvas(const FVector& World, FVector2D& OutCanvas) const;

	TWeakObjectPtr<APlayerController> Owner;

	/** 绝对定位的浮动文字层 */
	TSharedPtr<SRobotFloatLabelLayer> Layer;

	/** 池化的文字控件（只增不减，多余时隐藏） */
	TArray<FFloatTextItem> Pool;

	/** 诊断：上一帧的伤害数字数量 */
	int32 LastNumberCount = 0;
};
