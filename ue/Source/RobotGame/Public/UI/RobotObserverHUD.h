// 观察者模式 HUD —— 纯 C++ Slate（第一百零七轮）
//
// 进入自由飞行观察相机后覆盖一层工业风 UI：
//   顶部：模式标识条 + 状态灯
//   左上：机位 / 坐标 / 速度 遥测
//   底部：操作提示带
//   四角：取景框装饰（呼应命中标记的 L 形括号语言）
// 数据从 PlayerController 每帧拉取（TAttribute），无需手动刷新。
#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

class SRobotObserverHUD : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SRobotObserverHUD) {}
		SLATE_ARGUMENT(TWeakObjectPtr<class APlayerController>, Owner)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

private:
	class ARobotPlayerController* GetPC() const;

	FText ModeLabel() const;
	FText LocationLabel() const;
	FText RotationLabel() const;
	FText SpeedLabel() const;
	FText HintLabel() const;
	FSlateColor StatusColor() const;

	TWeakObjectPtr<APlayerController> Owner;
	TSharedPtr<struct FSlateBrush> PanelBrush;
	TSharedPtr<struct FSlateBrush> AccentBrush;
	TSharedPtr<struct FSlateBrush> RuleBrush;
};
