#include "UI/RobotHUD.h"
#include "UI/RobotUITheme.h"

#include "RobotCharacter.h"
#include "RobotPlayerController.h"
#include "RobotAttributeSet.h"
#include "AssemblyComponent.h"
#include "RobotChassisData.h"

#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"

#include "Styling/CoreStyle.h"
#include "Brushes/SlateColorBrush.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "RobotHUD"

namespace
{
	FSlateBrush MakeSolid(const FLinearColor& C)
	{
		return FSlateColorBrush(C);
	}

	// 配色/尺寸统一从全局主题取（RobotUITheme.h），不再各写各的字面量。
	// 这里保留短别名，避免改动文件里大量已有的裸引用。
	const FLinearColor ColorText = RobotTheme::Text;
	const FLinearColor ColorDim  = RobotTheme::TextDim;

	// 设计画布：与主菜单一致，整块内容等比缩放到实际视口
	constexpr float DesignW = RobotTheme::DesignW;
	constexpr float DesignH = RobotTheme::DesignH;

	constexpr float BarW = RobotTheme::BarW;
	constexpr float BarH = RobotTheme::BarH;
}

void SRobotHUD::Construct(const FArguments& InArgs)
{
	Owner = InArgs._Owner;

	PanelBrush = MakeShared<FSlateBrush>(MakeSolid(RobotTheme::PanelBg));
	BarBgBrush = MakeShared<FSlateBrush>(MakeSolid(RobotTheme::BarBg));
	FillBrush = MakeShared<FSlateBrush>(MakeSolid(FLinearColor::White));
	WarnBrush = MakeShared<FSlateBrush>(MakeSolid(RobotTheme::Warn));
	CrossBrush = MakeShared<FSlateBrush>(MakeSolid(FLinearColor(1.f, 1.f, 1.f, 0.75f)));
	AccentBrush = MakeShared<FSlateBrush>(MakeSolid(RobotTheme::Accent));
	RuleBrush = MakeShared<FSlateBrush>(MakeSolid(RobotTheme::Rule));

	ChildSlot
	[
		SNew(SScaleBox)
		.Stretch(EStretch::ScaleToFit)
		.StretchDirection(EStretchDirection::Both)
		[
			SNew(SBox)
			.WidthOverride(DesignW)
			.HeightOverride(DesignH)
			[
				SNew(SOverlay)

				// ── 左下：状态面板（热量 / 电力 / 废料 / 机体一体化整合）──
				//
				// 之前分成两个独立的悬浮面板，因绝对像素 Padding 发生重叠穿透。
				// 合并为一个高质感机能风半透信息舱，层次分明，且不遮挡角色脚步。
				+ SOverlay::Slot()
				.HAlign(HAlign_Left)
				.VAlign(VAlign_Bottom)
				.Padding(FMargin(28.f, 0.f, 0.f, 26.f))
				[
					SNew(SBorder)
					.BorderImage(PanelBrush.Get())
					.Padding(FMargin(0.f))
					[
						SNew(SVerticalBox)

						// ══ 工业风顶栏：铜橙细条 + 系统标题 ══
						+ SVerticalBox::Slot()
						.AutoHeight()
						[
							SNew(SBox)
							.HeightOverride(3.f)
							[ SNew(SImage).Image(AccentBrush.Get()) ]
						]
						+ SVerticalBox::Slot()
						.AutoHeight()
						.Padding(18.f, 8.f, 18.f, 2.f)
						[
							SNew(STextBlock)
							.Text(LOCTEXT("SysTitle", "机 体 状 态   /   SYSTEM"))
							.Font(RobotTheme::Font(10, true))
							.ColorAndOpacity(FSlateColor(RobotTheme::Accent))
						]
						+ SVerticalBox::Slot()
						.AutoHeight()
						.Padding(18.f, 0.f, 18.f, 0.f)
						[
							SNew(SBox).HeightOverride(1.f)
							[ SNew(SImage).Image(RuleBrush.Get()) ]
						]

						// 顶部栏：机体型号 + 废料收集计数
						+ SVerticalBox::Slot()
						.AutoHeight()
						.Padding(18.f, 10.f, 18.f, 10.f)
						[
							SNew(SHorizontalBox)

							+ SHorizontalBox::Slot()
							.AutoWidth()
							[
								SNew(STextBlock)
								.Text(this, &SRobotHUD::ChassisLabel)
								.Font(RobotTheme::Font(16, true))
								.ColorAndOpacity(FSlateColor(RobotTheme::Text))
							]

							+ SHorizontalBox::Slot()
							.FillWidth(1.f)
							.HAlign(HAlign_Right)
							.VAlign(VAlign_Center)
							[
								SNew(STextBlock)
								.Text(this, &SRobotHUD::SalvageLabel)
								.Font(RobotTheme::Font(14, true))
								.ColorAndOpacity(FSlateColor(RobotTheme::Accent))
							]
						]

						// 热量进度槽
						+ SVerticalBox::Slot()
						.AutoHeight()
						.Padding(18.f, 0.f, 18.f, 0.f)
						[
							MakeBar(
								TAttribute<FSlateColor>::CreateSP(this, &SRobotHUD::HeatColor),
								TAttribute<float>::CreateSP(this, &SRobotHUD::HeatFraction),
								TAttribute<FText>::CreateSP(this, &SRobotHUD::HeatLabel))
						]

						// 电力进度槽
						+ SVerticalBox::Slot()
						.AutoHeight()
						.Padding(18.f, 8.f, 18.f, 14.f)
						[
							MakeBar(
								TAttribute<FSlateColor>::CreateSP(this, &SRobotHUD::PowerColor),
								TAttribute<float>::CreateSP(this, &SRobotHUD::PowerFraction),
								TAttribute<FText>::CreateSP(this, &SRobotHUD::PowerLabel))
						]
					]
				]

				// ── 中央准星 ──
				//
				// 每个方向上画两条：深色描边（粗 4px）+ 白色准星（2px）。
				// 只有白色的话，对着亮地面（本作地板是浅灰金属板）时会"消失"，
				// 描边保证任何亮度背景上都看得见。
				+ SOverlay::Slot()
				.HAlign(HAlign_Center)
				.VAlign(VAlign_Center)
				[
					SNew(SBox)
					.WidthOverride(22.f)
					.HeightOverride(22.f)
					[
						SNew(SOverlay)

						// 横（描边）
						+ SOverlay::Slot()
						.HAlign(HAlign_Center)
						.VAlign(VAlign_Center)
						[
							SNew(SBox)
							.WidthOverride(22.f)
							.HeightOverride(4.f)
							[
								SNew(SImage)
								.Image(CrossBrush.Get())
								.ColorAndOpacity(FSlateColor(
									FLinearColor(0.02f, 0.03f, 0.05f, 0.55f)))
							]
						]

						// 竖（描边）
						+ SOverlay::Slot()
						.HAlign(HAlign_Center)
						.VAlign(VAlign_Center)
						[
							SNew(SBox)
							.WidthOverride(4.f)
							.HeightOverride(22.f)
							[
								SNew(SImage)
								.Image(CrossBrush.Get())
								.ColorAndOpacity(FSlateColor(
									FLinearColor(0.02f, 0.03f, 0.05f, 0.55f)))
							]
						]

						+ SOverlay::Slot()
						.HAlign(HAlign_Center)
						.VAlign(VAlign_Center)
						[
							SNew(SBox)
							.WidthOverride(22.f)
							.HeightOverride(2.f)
							[
								SNew(SImage)
								.Image(CrossBrush.Get())
								.ColorAndOpacity(this, &SRobotHUD::CrosshairColor)
							]
						]

						+ SOverlay::Slot()
						.HAlign(HAlign_Center)
						.VAlign(VAlign_Center)
						[
							SNew(SBox)
							.WidthOverride(2.f)
							.HeightOverride(22.f)
							[
								SNew(SImage)
								.Image(CrossBrush.Get())
								.ColorAndOpacity(this, &SRobotHUD::CrosshairColor)
							]
						]
					]
				]

				// ── 命中标记：准心外的四角括号（命中瞬间出现、0.2 秒淡出）──
				//
				// 用"四角括号"而不是旋转 45° 的 X —— Slate 里给基础控件
				// 做旋转要挂 RenderTransform（pivot 还得手动调），
				// 而四个 L 形括号零风险、辨识度一样高。
				+ SOverlay::Slot()
				.HAlign(HAlign_Center)
				.VAlign(VAlign_Center)
				[
					SNew(SBox)
					.WidthOverride(64.f)
					.HeightOverride(64.f)
					.Visibility(this, &SRobotHUD::HitMarkerVisibility)
					[
						SNew(SOverlay)

						+ SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Top)
						[ MakeBracket(HAlign_Left, VAlign_Top) ]
						+ SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Top)
						[ MakeBracket(HAlign_Right, VAlign_Top) ]
						+ SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Bottom)
						[ MakeBracket(HAlign_Left, VAlign_Bottom) ]
						+ SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Bottom)
						[ MakeBracket(HAlign_Right, VAlign_Bottom) ]
					]
				]

				// ── 右上：残敌计数 ──
				+ SOverlay::Slot()
				.HAlign(HAlign_Right)
				.VAlign(VAlign_Top)
				.Padding(FMargin(0.f, 28.f, 30.f, 0.f))
				[
					SNew(SBorder)
					.BorderImage(PanelBrush.Get())
					.Padding(FMargin(0.f))
					[
						SNew(SVerticalBox)
						+ SVerticalBox::Slot().AutoHeight()
						[ SNew(SBox).HeightOverride(2.f)
							[ SNew(SImage).Image(AccentBrush.Get()) ] ]
						+ SVerticalBox::Slot().AutoHeight()
						.Padding(16.f, 8.f)
						[
							SNew(STextBlock)
							.Text(this, &SRobotHUD::EnemyCountLabel)
							.Font(RobotTheme::Font(17, true))
							.ColorAndOpacity(FSlateColor(RobotTheme::Text))
						]
					]
				]

				// ── 顶部中：过热警告 ──
				+ SOverlay::Slot()
				.HAlign(HAlign_Center)
				.VAlign(VAlign_Top)
				.Padding(FMargin(0.f, 96.f, 0.f, 0.f))
				[
					SNew(SBorder)
					.BorderImage(WarnBrush.Get())
					.Padding(FMargin(22.f, 8.f))
					.Visibility(this, &SRobotHUD::OverheatVisibility)
					[
						SNew(STextBlock)
						.Text(this, &SRobotHUD::OverheatLabel)
						.Font(RobotTheme::Font(24, true))
						.ColorAndOpacity(FSlateColor(FLinearColor::White))
					]
				]

				// ── 全屏：受击红色暗角（透明度由 DamageFlashColor 驱动，无事件时全透明）──
				+ SOverlay::Slot()
				.HAlign(HAlign_Fill)
				.VAlign(VAlign_Fill)
				[
					SNew(SImage)
					.Image(FillBrush.Get())
					.ColorAndOpacity(this, &SRobotHUD::DamageFlashColor)
				]
			]
		]
	];
}

TSharedRef<SWidget> SRobotHUD::MakeBar(TAttribute<FSlateColor> FillColor,
	TAttribute<float> Fraction, TAttribute<FText> Label)
{
	return SNew(SVerticalBox)

		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0.f, 0.f, 0.f, 3.f)
		[
			SNew(STextBlock)
			.Text(Label)
			.Font(RobotTheme::Font(14, false))
			.ColorAndOpacity(FSlateColor(RobotTheme::TextDim))
		]

		+ SVerticalBox::Slot()
		.AutoHeight()
		[
			SNew(SBox)
			.WidthOverride(BarW)
			.HeightOverride(BarH)
			[
				SNew(SOverlay)

				+ SOverlay::Slot()
				.HAlign(HAlign_Fill)
				.VAlign(VAlign_Fill)
				[ SNew(SImage).Image(BarBgBrush.Get()) ]

				+ SOverlay::Slot()
				.HAlign(HAlign_Left)
				.VAlign(VAlign_Fill)
				[
					// 用 WidthOverride 绑一个 lambda 实现"按比例填充"：
					// 比找引擎的 SProgressBar 样式更可控，也不依赖主题
					SNew(SBox)
					.WidthOverride(TAttribute<FOptionalSize>::CreateLambda(
						[Fraction]()
						{
							const float F = FMath::Clamp(Fraction.Get(), 0.f, 1.f);
							return FOptionalSize(F * BarW);
						}))
					[
						SNew(SImage)
						.Image(FillBrush.Get())
						.ColorAndOpacity(FillColor)
					]
				]
			]
		];
}

TSharedRef<SWidget> SRobotHUD::MakeBracket(EHorizontalAlignment H,
	EVerticalAlignment V)
{
	// 一个 L 形角括号 = 一根横条 + 一根竖条，都贴同一个角。
	// 横条宽 = 容器宽、竖条高 = 容器高 —— 对齐方向自然把 L 的缺口
	// 朝向外侧，四个角拼起来就是一个"取景框"式的命中标记。
	return SNew(SBox)
		.WidthOverride(16.f)
		.HeightOverride(16.f)
		[
			SNew(SOverlay)

			+ SOverlay::Slot()
			.HAlign(HAlign_Fill)
			.VAlign(V)
			[
				SNew(SBox)
				.HeightOverride(3.f)
				[
					SNew(SImage)
					.Image(CrossBrush.Get())
					.ColorAndOpacity(this, &SRobotHUD::HitMarkerColor)
				]
			]

			+ SOverlay::Slot()
			.HAlign(H)
			.VAlign(VAlign_Fill)
			[
				SNew(SBox)
				.WidthOverride(3.f)
				[
					SNew(SImage)
					.Image(CrossBrush.Get())
					.ColorAndOpacity(this, &SRobotHUD::HitMarkerColor)
				]
			]
		];
}

// ─────────────────────────────────────────────
// 取值
// ─────────────────────────────────────────────

ARobotCharacter* SRobotHUD::GetRobot() const
{
	if (const APlayerController* PC = Owner.Get())
	{
		return Cast<ARobotCharacter>(PC->GetPawn());
	}
	return nullptr;
}

ARobotPlayerController* SRobotHUD::GetPC() const
{
	return Cast<ARobotPlayerController>(Owner.Get());
}

float SRobotHUD::HeatFraction() const
{
	if (const ARobotCharacter* R = GetRobot())
	{
		if (const URobotAttributeSet* S = R->GetAttributeSet())
		{
			return S->GetHeatRatio();
		}
	}
	return 0.f;
}

float SRobotHUD::PowerFraction() const
{
	if (const ARobotCharacter* R = GetRobot())
	{
		if (const URobotAttributeSet* S = R->GetAttributeSet())
		{
			const float Max = FMath::Max(S->GetMaxPower(), 1.f);
			return FMath::Clamp(S->GetPower() / Max, 0.f, 1.f);
		}
	}
	return 0.f;
}

FText SRobotHUD::HeatLabel() const
{
	const int32 Pct = FMath::RoundToInt(HeatFraction() * 100.f);
	const bool bOver = [this]()
	{
		if (const ARobotCharacter* R = GetRobot())
		{
			if (const URobotAttributeSet* S = R->GetAttributeSet())
			{
				return S->IsOverheated();
			}
		}
		return false;
	}();
	return FText::FromString(FString::Printf(
		TEXT("热量  %d%%%s"), Pct, bOver ? TEXT("  ·  过热锁定") : TEXT("")));
}

FText SRobotHUD::PowerLabel() const
{
	const float F = PowerFraction();
	const int32 Pct = FMath::RoundToInt(F * 100.f);
	// 电力过低时给一条明确文字 —— 冲刺/开火都会因为没电而失效，
	// 玩家必须知道"为什么打不出去"。
	const TCHAR* Suffix = (F < 0.25f) ? TEXT("  ·  电力不足") : TEXT("");
	return FText::FromString(FString::Printf(TEXT("电力  %d%%%s"), Pct, Suffix));
}

FText SRobotHUD::ChassisLabel() const
{
	if (const ARobotCharacter* R = GetRobot())
	{
		if (const UAssemblyComponent* A = R->GetAssembly())
		{
			if (A->Chassis)
			{
				return A->Chassis->DisplayName;
			}
		}
	}
	return LOCTEXT("NoChassis", "未装载机体");
}

FText SRobotHUD::SalvageLabel() const
{
	if (const ARobotCharacter* R = GetRobot())
	{
		return FText::FromString(FString::Printf(TEXT("回收废料  %d"), R->GetSalvage()));
	}
	return FText::GetEmpty();
}

FText SRobotHUD::OverheatLabel() const
{
	return LOCTEXT("Overheat", "过 热 锁 定");
}

EVisibility SRobotHUD::OverheatVisibility() const
{
	if (const ARobotCharacter* R = GetRobot())
	{
		if (const URobotAttributeSet* S = R->GetAttributeSet())
		{
			return S->IsOverheated() ? EVisibility::HitTestInvisible
			                         : EVisibility::Collapsed;
		}
	}
	return EVisibility::Collapsed;
}

FSlateColor SRobotHUD::HeatColor() const
{
	const float F = HeatFraction();
	if (F >= 0.99f) { return FSlateColor(RobotTheme::HeatHot); }
	if (F >= 0.75f) { return FSlateColor(RobotTheme::HeatWarm); }
	return FSlateColor(RobotTheme::HeatCool);
}

FSlateColor SRobotHUD::PowerColor() const
{
	const float F = PowerFraction();
	if (F < 0.25f) { return FSlateColor(RobotTheme::PowerLow); }
	return FSlateColor(RobotTheme::PowerOk);
}

// ─────────────────────────────────────────────
// 战斗反馈
// ─────────────────────────────────────────────

namespace
{
	// 命中标记与受击闪红的生命周期（秒）
	constexpr float HitMarkerLife = 0.22f;
	constexpr float DamageFlashLife = 0.55f;
}

float SRobotHUD::HitMarkerAlpha() const
{
	if (const ARobotPlayerController* PC = GetPC())
	{
		const float Age = PC->GetHitMarkerAge();
		if (Age >= 0.f && Age < HitMarkerLife)
		{
			const float T = 1.f - Age / HitMarkerLife;
			// 平方衰减：出现时干脆，淡出时快
			return T * T;
		}
	}
	return 0.f;
}

EVisibility SRobotHUD::HitMarkerVisibility() const
{
	return HitMarkerAlpha() > 0.01f
		? EVisibility::HitTestInvisible : EVisibility::Collapsed;
}

FSlateColor SRobotHUD::HitMarkerColor() const
{
	const float A = HitMarkerAlpha();
	if (const ARobotPlayerController* PC = GetPC())
	{
		if (PC->WasLastHitKill())
		{
			// 击杀：红
			return FSlateColor(FLinearColor(1.f, 0.28f, 0.20f, A));
		}
	}
	// 普通命中：橙
	return FSlateColor(FLinearColor(1.f, 0.74f, 0.26f, A));
}

FSlateColor SRobotHUD::CrosshairColor() const
{
	if (HitMarkerAlpha() > 0.01f)
	{
		if (const ARobotPlayerController* PC = GetPC())
		{
			if (PC->WasLastHitKill())
			{
				return FSlateColor(FLinearColor(1.f, 0.35f, 0.25f, 1.f));
			}
		}
		return FSlateColor(FLinearColor(1.f, 0.80f, 0.32f, 1.f));
	}
	return FSlateColor(FLinearColor(1.f, 1.f, 1.f, 0.75f));
}

FSlateColor SRobotHUD::DamageFlashColor() const
{
	if (const ARobotPlayerController* PC = GetPC())
	{
		const float Age = PC->GetDamageFlashAge();
		if (Age >= 0.f && Age < DamageFlashLife)
		{
			const float T = 1.f - Age / DamageFlashLife;
			// 前段最亮、后段快速退场；峰值透明度 0.26 —— 够醒目、
			// 又不至于把战场遮住（0.5 以上会看不清敌人）
			return FSlateColor(FLinearColor(0.90f, 0.07f, 0.05f, 0.26f * T * T));
		}
	}
	return FSlateColor(FLinearColor(0.f, 0.f, 0.f, 0.f));
}

FText SRobotHUD::EnemyCountLabel() const
{
	const ARobotPlayerController* PC = GetPC();
	const int32 N = PC ? PC->GetAliveEnemyCount() : 0;
	if (N <= 0)
	{
		return LOCTEXT("AreaClear", "区域已清空");
	}
	return FText::FromString(FString::Printf(TEXT("残敌  %d"), N));
}

#undef LOCTEXT_NAMESPACE
