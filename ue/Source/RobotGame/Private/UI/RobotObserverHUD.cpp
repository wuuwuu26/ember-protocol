#include "UI/RobotObserverHUD.h"
#include "UI/RobotUITheme.h"
#include "RobotPlayerController.h"

#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"
#include "Brushes/SlateColorBrush.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "RobotObserverHUD"

namespace
{
	FSlateBrush Solid(const FLinearColor& C) { return FSlateColorBrush(C); }

	// 取景框角标：一个 L 形（横条 + 竖条），贴到某个角
	TSharedRef<SWidget> Corner(FSlateBrush* Brush, const FLinearColor& Color,
		EHorizontalAlignment H, EVerticalAlignment V)
	{
		return SNew(SBox)
			.WidthOverride(26.f)
			.HeightOverride(26.f)
			[
				SNew(SOverlay)
				+ SOverlay::Slot().HAlign(H).VAlign(V)
				[
					SNew(SBox).WidthOverride(26.f).HeightOverride(2.f)
					[ SNew(SImage).Image(Brush).ColorAndOpacity(FSlateColor(Color)) ]
				]
				+ SOverlay::Slot().HAlign(H).VAlign(V)
				[
					SNew(SBox).WidthOverride(2.f).HeightOverride(26.f)
					[ SNew(SImage).Image(Brush).ColorAndOpacity(FSlateColor(Color)) ]
				]
			];
	}
}

void SRobotObserverHUD::Construct(const FArguments& InArgs)
{
	Owner = InArgs._Owner;

	PanelBrush  = MakeShared<FSlateBrush>(Solid(RobotTheme::PanelBg));
	AccentBrush = MakeShared<FSlateBrush>(Solid(RobotTheme::Accent));
	RuleBrush   = MakeShared<FSlateBrush>(Solid(RobotTheme::Rule));

	ChildSlot
	[
		SNew(SScaleBox)
		.Stretch(EStretch::ScaleToFit)
		.StretchDirection(EStretchDirection::Both)
		[
			SNew(SBox)
			.WidthOverride(RobotTheme::DesignW)
			.HeightOverride(RobotTheme::DesignH)
			[
				SNew(SOverlay)

				// ══ 四角取景框 ══
				+ SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Top)
				.Padding(FMargin(20.f, 20.f, 0.f, 0.f))
				[ Corner(AccentBrush.Get(), RobotTheme::Accent, HAlign_Left, VAlign_Top) ]
				+ SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Top)
				.Padding(FMargin(0.f, 20.f, 20.f, 0.f))
				[ Corner(AccentBrush.Get(), RobotTheme::Accent, HAlign_Right, VAlign_Top) ]
				+ SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Bottom)
				.Padding(FMargin(20.f, 0.f, 0.f, 20.f))
				[ Corner(AccentBrush.Get(), RobotTheme::Accent, HAlign_Left, VAlign_Bottom) ]
				+ SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Bottom)
				.Padding(FMargin(0.f, 0.f, 20.f, 20.f))
				[ Corner(AccentBrush.Get(), RobotTheme::Accent, HAlign_Right, VAlign_Bottom) ]

				// ══ 顶部：模式标识条 ══
				+ SOverlay::Slot()
				.HAlign(HAlign_Center)
				.VAlign(VAlign_Top)
				.Padding(FMargin(0.f, 24.f, 0.f, 0.f))
				[
					SNew(SBorder)
					.BorderImage(PanelBrush.Get())
					.Padding(FMargin(20.f, 8.f))
					[
						SNew(SHorizontalBox)
						// 状态灯
						+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
						.Padding(0.f, 0.f, 12.f, 0.f)
						[
							SNew(SBox).WidthOverride(9.f).HeightOverride(9.f)
							[
								SNew(SImage).Image(AccentBrush.Get())
								.ColorAndOpacity(this, &SRobotObserverHUD::StatusColor)
							]
						]
						+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
						[
							SNew(STextBlock)
							.Text(this, &SRobotObserverHUD::ModeLabel)
							.Font(RobotTheme::Font(15, true))
							.ColorAndOpacity(FSlateColor(RobotTheme::Text))
						]
					]
				]

				// ══ 左上：机位遥测 ══
				+ SOverlay::Slot()
				.HAlign(HAlign_Left)
				.VAlign(VAlign_Top)
				.Padding(FMargin(40.f, 74.f, 0.f, 0.f))
				[
					SNew(SBorder)
					.BorderImage(PanelBrush.Get())
					.Padding(FMargin(16.f, 12.f))
					[
						SNew(SVerticalBox)
						// 标题 + 分隔线
						+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 6.f)
						[
							SNew(STextBlock)
							.Text(LOCTEXT("Telemetry", "遥测  /  TELEMETRY"))
							.Font(RobotTheme::Font(11, true))
							.ColorAndOpacity(FSlateColor(RobotTheme::Accent))
						]
						+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 8.f)
						[
							SNew(SBox).HeightOverride(1.f)
							[ SNew(SImage).Image(RuleBrush.Get()) ]
						]
						+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 3.f)
						[ SNew(STextBlock).Text(this, &SRobotObserverHUD::LocationLabel)
							.Font(RobotTheme::Font(12)).ColorAndOpacity(FSlateColor(RobotTheme::Text)) ]
						+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 3.f)
						[ SNew(STextBlock).Text(this, &SRobotObserverHUD::RotationLabel)
							.Font(RobotTheme::Font(12)).ColorAndOpacity(FSlateColor(RobotTheme::TextDim)) ]
						+ SVerticalBox::Slot().AutoHeight()
						[ SNew(STextBlock).Text(this, &SRobotObserverHUD::SpeedLabel)
							.Font(RobotTheme::Font(12)).ColorAndOpacity(FSlateColor(RobotTheme::Cyan)) ]
					]
				]

				// ══ 底部：操作提示带 ══
				+ SOverlay::Slot()
				.HAlign(HAlign_Center)
				.VAlign(VAlign_Bottom)
				.Padding(FMargin(0.f, 0.f, 0.f, 30.f))
				[
					SNew(SBorder)
					.BorderImage(PanelBrush.Get())
					.Padding(FMargin(18.f, 7.f))
					[
						SNew(STextBlock)
						.Text(this, &SRobotObserverHUD::HintLabel)
						.Font(RobotTheme::Font(12))
						.ColorAndOpacity(FSlateColor(RobotTheme::TextDim))
					]
				]
			]
		]
	];
}

// ─────────────────────────────────────────────
// 取值
// ─────────────────────────────────────────────

ARobotPlayerController* SRobotObserverHUD::GetPC() const
{
	return Cast<ARobotPlayerController>(Owner.Get());
}

FText SRobotObserverHUD::ModeLabel() const
{
	return LOCTEXT("Mode", "观察者模式  ·  OBSERVER");
}

FText SRobotObserverHUD::LocationLabel() const
{
	if (const ARobotPlayerController* PC = GetPC())
	{
		const FVector L = PC->GetObserverLocation();
		return FText::FromString(FString::Printf(
			TEXT("坐标  X %+7.0f   Y %+7.0f   Z %+7.0f"), L.X, L.Y, L.Z));
	}
	return FText::GetEmpty();
}

FText SRobotObserverHUD::RotationLabel() const
{
	if (const ARobotPlayerController* PC = GetPC())
	{
		const FRotator R = PC->GetObserverRotation();
		return FText::FromString(FString::Printf(
			TEXT("朝向  俯仰 %+5.1f°   偏航 %+6.1f°"), R.Pitch, R.Yaw));
	}
	return FText::GetEmpty();
}

FText SRobotObserverHUD::SpeedLabel() const
{
	if (const ARobotPlayerController* PC = GetPC())
	{
		return FText::FromString(FString::Printf(
			TEXT("移速  %.0f cm/s"), PC->GetObserverSpeed()));
	}
	return FText::GetEmpty();
}

FText SRobotObserverHUD::HintLabel() const
{
	return LOCTEXT("Hint",
		"W A S D 移动   ·   鼠标 转向   ·   Q E 升降   ·   滚轮 调速   ·   Shift 加速   ·   V 返回机甲");
}

FSlateColor SRobotObserverHUD::StatusColor() const
{
	// 呼吸灯：随时间在强调色与青色间轻微起伏，表示"运行中"
	float T = 0.f;
	if (GEngine && GEngine->GetWorldContexts().Num() > 0)
	{
		if (const UWorld* W = GEngine->GetWorldContexts()[0].World())
		{
			T = FMath::Sin(W->GetTimeSeconds() * 3.f) * 0.5f + 0.5f;
		}
	}
	return FSlateColor(FMath::Lerp(RobotTheme::Accent, RobotTheme::Cyan, T * 0.5f));
}

#undef LOCTEXT_NAMESPACE
