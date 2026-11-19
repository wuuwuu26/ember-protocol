// 游戏内 HUD —— 纯 C++ Slate，按 16:9 设计画布等比缩放，适配任意分辨率
//
// 替换掉之前的 AddOnScreenDebugMessage：那种按像素定位的调试文字
// 在不同分辨率下会错位、重叠，而且字号不跟随屏幕变化。
#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

class ARobotCharacter;

class SRobotHUD : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SRobotHUD) {}
		SLATE_ARGUMENT(TWeakObjectPtr<class APlayerController>, Owner)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

private:
	ARobotCharacter* GetRobot() const;
	class ARobotPlayerController* GetPC() const;

	// ── 取值（Slate 每帧重算，不用手动刷新）──
	float HeatFraction() const;
	float PowerFraction() const;
	FText HeatLabel() const;
	FText PowerLabel() const;
	FText ChassisLabel() const;
	FText SalvageLabel() const;
	FText OverheatLabel() const;
	EVisibility OverheatVisibility() const;
	FSlateColor HeatColor() const;
	FSlateColor PowerColor() const;

	// ── 战斗反馈 ──

	/** 命中标记（准心外的四角刻度）：0=刚命中 → 1=淡出完毕 */
	float HitMarkerAlpha() const;
	EVisibility HitMarkerVisibility() const;
	FSlateColor HitMarkerColor() const;
	/** 准心本体颜色：命中瞬间变橙 / 击杀变红 */
	FSlateColor CrosshairColor() const;

	/** 受击红色暗角的透明度（0 = 不显示） */
	FSlateColor DamageFlashColor() const;

	/** "残敌 N" 文本 */
	FText EnemyCountLabel() const;

	TSharedRef<SWidget> MakeBar(
		TAttribute<FSlateColor> FillColor,
		TAttribute<float> Fraction,
		TAttribute<FText> Label);

	/** 命中标记的单个 L 形角括号 */
	TSharedRef<SWidget> MakeBracket(EHorizontalAlignment H, EVerticalAlignment V);

	TWeakObjectPtr<APlayerController> Owner;

	TSharedPtr<struct FSlateBrush> PanelBrush;
	TSharedPtr<struct FSlateBrush> BarBgBrush;
	TSharedPtr<struct FSlateBrush> FillBrush;
	TSharedPtr<struct FSlateBrush> WarnBrush;
	TSharedPtr<struct FSlateBrush> CrossBrush;
	TSharedPtr<struct FSlateBrush> AccentBrush;
	TSharedPtr<struct FSlateBrush> RuleBrush;
};
