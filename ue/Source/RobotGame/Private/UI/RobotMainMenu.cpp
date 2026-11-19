#include "UI/RobotMainMenu.h"
#include "UI/RobotUITheme.h"

#include "RobotPlayerController.h"
#include "RobotCharacter.h"
#include "AssemblyComponent.h"
#include "RobotChassisData.h"
#include "RobotModuleData.h"

#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "HAL/IConsoleManager.h"
#include "GameFramework/GameUserSettings.h"
#include "Kismet/KismetSystemLibrary.h"
#include "GenericPlatform/GenericApplication.h"
#include "Misc/App.h"

#include "Styling/CoreStyle.h"
#include "Styling/SlateBrush.h"
#include "Styling/SlateTypes.h"
#include "Brushes/SlateColorBrush.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SComboBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/Layout/SSpacer.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "RobotMainMenu"

namespace
{
	// 纯色画刷。
	//
	// 注意：FSlateBrush 的带参构造函数是 protected，不能直接 new 出来；
	// 而 FSlateColorBrush 的构造是公有的，它内部把 DrawAs=Image、
	// ImageType=NoImage、TintColor=颜色，正好就是"实心色块"。
	// 切回基类 FSlateBrush 只丢掉派生类新增的成员（它没有），所以安全。
	FSlateBrush MakeSolid(const FLinearColor& C)
	{
		return FSlateColorBrush(C);
	}

	// 配色统一从全局主题取（RobotUITheme.h）。值与此前一致，
	// 只是收敛到单一来源，改动主题时所有界面一起变。
	const FLinearColor ColorText   = RobotTheme::Text;
	const FLinearColor ColorDim    = RobotTheme::TextDim;
	const FLinearColor ColorAccent = RobotTheme::Accent;

	constexpr float DesignW = 1280.f;
	constexpr float DesignH = 720.f;
}

void SRobotMainMenu::Construct(const FArguments& InArgs)
{
	Owner = InArgs._Owner;

	// 调试开关（见 RobotPlayerController 里的说明）：2 = 启动直接停在设置页
	static IConsoleVariable* CVarPage =
		IConsoleManager::Get().FindConsoleVariable(TEXT("Robot.MenuDebug"));
	bShowingSettings = CVarPage && CVarPage->GetInt() == 2;

	BackdropBrush = MakeShared<FSlateBrush>(
		MakeSolid(FLinearColor(0.015f, 0.020f, 0.030f, 0.97f)));
	PanelBrush = MakeShared<FSlateBrush>(
		MakeSolid(FLinearColor(0.055f, 0.070f, 0.100f, 0.96f)));
	AccentBrush = MakeShared<FSlateBrush>(MakeSolid(ColorAccent));
	ButtonBrush = MakeShared<FSlateBrush>(
		MakeSolid(FLinearColor(0.105f, 0.130f, 0.180f, 0.95f)));
	ButtonHoverBrush = MakeShared<FSlateBrush>(
		MakeSolid(FLinearColor(0.170f, 0.235f, 0.330f, 1.f)));
	ButtonPressedBrush = MakeShared<FSlateBrush>(
		MakeSolid(FLinearColor(0.230f, 0.310f, 0.430f, 1.f)));
	RowBrush = MakeShared<FSlateBrush>(
		MakeSolid(FLinearColor(0.030f, 0.040f, 0.060f, 0.85f)));

	ButtonStyle = MakeShared<FButtonStyle>();
	ButtonStyle->SetNormal(*ButtonBrush)
		.SetHovered(*ButtonHoverBrush)
		.SetPressed(*ButtonPressedBrush)
		.SetDisabled(*ButtonBrush);
	ButtonStyle->SetNormalPadding(FMargin(10.f, 4.f));
	ButtonStyle->SetPressedPadding(FMargin(10.f, 5.f, 10.f, 3.f));

	BuildOptions();

	// 布局：全屏底色 + 16:9 设计画布等比缩放。
	// 这样在任何分辨率下内容都完整可见、不会错位 —— 就是"适配屏幕尺寸"的做法。
	ChildSlot
	[
		SNew(SOverlay)

		+ SOverlay::Slot()
		.HAlign(HAlign_Fill)
		.VAlign(VAlign_Fill)
		[
			SNew(SBorder)
			.BorderImage(BackdropBrush.Get())
			.Padding(0.f)
		]

		+ SOverlay::Slot()
		.HAlign(HAlign_Fill)
		.VAlign(VAlign_Fill)
		[
			SNew(SScaleBox)
			.Stretch(EStretch::ScaleToFit)
			.StretchDirection(EStretchDirection::Both)
			[
				SNew(SBox)
				.WidthOverride(DesignW)
				.HeightOverride(DesignH)
				[
					SNew(SVerticalBox)

					+ SVerticalBox::Slot()
					.FillHeight(1.f)
					.HAlign(HAlign_Center)
					.VAlign(VAlign_Center)
					[
						SAssignNew(PageHost, SBox)
						.WidthOverride(780.f)
						[
							BuildPage()
						]
					]
				]
			]
		]
	];
}

// ─────────────────────────────────────────────
// 可选值
// ─────────────────────────────────────────────

void SRobotMainMenu::BuildOptions()
{
	// ── 分辨率 ──
	// 用引擎的"支持的全屏分辨率"列表；拿不到就退回到一份常用档位，
	// 并且永远把当前桌面分辨率插到最前面（用户多半想用它）。
	TArray<FIntPoint> Supported;
	UKismetSystemLibrary::GetSupportedFullscreenResolutions(Supported);

	FDisplayMetrics Metrics;
	FDisplayMetrics::RebuildDisplayMetrics(Metrics);
	const FIntPoint Desktop(Metrics.PrimaryDisplayWidth, Metrics.PrimaryDisplayHeight);

	auto AddRes = [this](const FIntPoint& P)
	{
		for (const TSharedPtr<FIntPoint>& E : ResolutionOptions)
		{
			if (E.IsValid() && E->X == P.X && E->Y == P.Y)
			{
				return;
			}
		}
		if (P.X > 0 && P.Y > 0)
		{
			ResolutionOptions.Add(MakeShared<FIntPoint>(P));
		}
	};

	if (Desktop.X > 0)
	{
		AddRes(Desktop);
	}
	if (Supported.Num() == 0)
	{
		// 退路：常见档位
		AddRes(FIntPoint(1280, 720));
		AddRes(FIntPoint(1366, 768));
		AddRes(FIntPoint(1600, 900));
		AddRes(FIntPoint(1920, 1080));
		AddRes(FIntPoint(2560, 1440));
		AddRes(FIntPoint(3840, 2160));
	}
	else
	{
		// 只保留不超过桌面分辨率的档位，避免选出屏幕装不下的尺寸
		for (const FIntPoint& P : Supported)
		{
			if (Desktop.X <= 0 || (P.X <= Desktop.X && P.Y <= Desktop.Y))
			{
				AddRes(P);
			}
		}
		if (ResolutionOptions.Num() == 0)
		{
			AddRes(Desktop);
		}
	}

	UGameUserSettings* Settings = GEngine ? GEngine->GetGameUserSettings() : nullptr;
	const FIntPoint Current = Settings
		? Settings->GetScreenResolution() : Desktop;

	PendingResolution = ResolutionOptions.Num() > 0
		? ResolutionOptions[0] : MakeShared<FIntPoint>(1280, 720);
	for (const TSharedPtr<FIntPoint>& E : ResolutionOptions)
	{
		if (E.IsValid() && E->X == Current.X && E->Y == Current.Y)
		{
			PendingResolution = E;
			break;
		}
	}

	// ── 显示模式（顺序必须与 EWindowMode 一致：0=全屏 1=无边框 2=窗口化）──
	WindowModeOptions.Add(MakeShared<FString>(TEXT("全屏（独占）")));
	WindowModeOptions.Add(MakeShared<FString>(TEXT("无边框窗口")));
	WindowModeOptions.Add(MakeShared<FString>(TEXT("窗口化")));

	int32 ModeIdx = 2;
	if (Settings)
	{
		ModeIdx = FMath::Clamp((int32)Settings->GetFullscreenMode(), 0, 2);
	}
	PendingWindowMode = WindowModeOptions[ModeIdx];

	// ── 画质 ──
	QualityOptions.Add(MakeShared<FString>(TEXT("低")));
	QualityOptions.Add(MakeShared<FString>(TEXT("中")));
	QualityOptions.Add(MakeShared<FString>(TEXT("高")));
	QualityOptions.Add(MakeShared<FString>(TEXT("极高")));
	int32 QIdx = 3;
	if (Settings)
	{
		QIdx = FMath::Clamp(Settings->GetOverallScalabilityLevel(), 0, 3);
	}
	PendingQuality = QualityOptions[QIdx];

	StatusText = FText::FromString(
		Desktop.X > 0
			? FString::Printf(TEXT("检测到桌面分辨率 %d × %d"), Desktop.X, Desktop.Y)
			: FString(TEXT("未能检测桌面分辨率")));
}

// ─────────────────────────────────────────────
// 小部件
// ─────────────────────────────────────────────

TSharedRef<SWidget> SRobotMainMenu::MakeTitle(const FText& Text, float Size,
	const FLinearColor& Color)
{
	return SNew(STextBlock)
		.Text(Text)
		.Font(FCoreStyle::GetDefaultFontStyle("Bold", (int32)Size))
		.ColorAndOpacity(FSlateColor(Color))
		.Justification(ETextJustify::Center);
}

TSharedRef<SWidget> SRobotMainMenu::MakeButton(const FText& Label,
	FOnClicked OnClicked, float FontSize)
{
	return SNew(SButton)
		.OnClicked(OnClicked)
		.ButtonStyle(ButtonStyle.Get())
		.HAlign(HAlign_Center)
		.VAlign(VAlign_Center)
		.ContentPadding(FMargin(0.f, 13.f))
		[
			SNew(STextBlock)
			.Text(Label)
			.Font(FCoreStyle::GetDefaultFontStyle("Bold", (int32)FontSize))
			.ColorAndOpacity(FSlateColor(ColorText))
			.Justification(ETextJustify::Center)
		];
}

TSharedRef<SWidget> SRobotMainMenu::MakeSettingRow(const FText& Label,
	TSharedRef<SWidget> Control)
{
	return SNew(SBorder)
		.BorderImage(RowBrush.Get())
		.Padding(FMargin(18.f, 10.f))
		[
			SNew(SHorizontalBox)

			+ SHorizontalBox::Slot()
			.FillWidth(1.f)
			.VAlign(VAlign_Center)
			[
				SNew(STextBlock)
				.Text(Label)
				.Font(FCoreStyle::GetDefaultFontStyle("Regular", 18))
				.ColorAndOpacity(FSlateColor(ColorText))
			]

			+ SHorizontalBox::Slot()
			.AutoWidth()
			.VAlign(VAlign_Center)
			[
				Control
			]
		];
}

// ─────────────────────────────────────────────
// 页面
// ─────────────────────────────────────────────

TSharedRef<SWidget> SRobotMainMenu::BuildPage()
{
	return bShowingSettings ? BuildSettingsPage() : BuildMainPage();
}

void SRobotMainMenu::RefreshPage()
{
	if (PageHost.IsValid())
	{
		PageHost->SetContent(BuildPage());
	}
}

TSharedRef<SWidget> SRobotMainMenu::BuildMainPage()
{
	return SNew(SBorder)
		.BorderImage(PanelBrush.Get())
		.Padding(FMargin(56.f, 44.f))
		[
			SNew(SVerticalBox)

			+ SVerticalBox::Slot()
			.AutoHeight()
			.HAlign(HAlign_Center)
			[
				MakeTitle(LOCTEXT("Title", "余火协议"), 58.f, ColorText)
			]

			+ SVerticalBox::Slot()
			.AutoHeight()
			.HAlign(HAlign_Center)
			.Padding(0.f, 2.f, 0.f, 0.f)
			[
				MakeTitle(LOCTEXT("SubTitle", "E M B E R   P R O T O C O L"), 15.f, ColorDim)
			]

			+ SVerticalBox::Slot()
			.AutoHeight()
			.HAlign(HAlign_Center)
			.Padding(0.f, 14.f, 0.f, 0.f)
			[
				MakeTitle(LOCTEXT("Tagline", "拆解 · 过热 · 取舍"), 17.f, ColorAccent)
			]

			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.f, 34.f, 0.f, 0.f)
			[
				MakeButton(LOCTEXT("Start", "开始游戏"),
					FOnClicked::CreateSP(this, &SRobotMainMenu::OnStart))
			]

			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.f, 10.f, 0.f, 0.f)
			[
				MakeButton(LOCTEXT("Settings", "设置"),
					FOnClicked::CreateSP(this, &SRobotMainMenu::OnOpenSettings))
			]

			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.f, 10.f, 0.f, 0.f)
			[
				MakeButton(LOCTEXT("Quit", "退出"),
					FOnClicked::CreateSP(this, &SRobotMainMenu::OnQuit))
			]

			+ SVerticalBox::Slot()
			.AutoHeight()
			.HAlign(HAlign_Center)
			.Padding(0.f, 30.f, 0.f, 0.f)
			[
				MakeTitle(
					LOCTEXT("Keys",
						"WASD 移动   ·   鼠标 视角   ·   左键 射击   ·   空格 冲刺\nM 改装   ·   1/2/3 换机体"),
					14.f, ColorDim)
			]
		];
}

TSharedRef<SWidget> SRobotMainMenu::BuildSettingsPage()
{
	return SNew(SBorder)
		.BorderImage(PanelBrush.Get())
		.Padding(FMargin(48.f, 38.f))
		[
			SNew(SVerticalBox)

			+ SVerticalBox::Slot()
			.AutoHeight()
			.HAlign(HAlign_Center)
			.Padding(0.f, 0.f, 0.f, 24.f)
			[
				MakeTitle(LOCTEXT("SettingsTitle", "显示设置"), 40.f, ColorText)
			]

			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.f, 0.f, 0.f, 10.f)
			[
				MakeSettingRow(LOCTEXT("Res", "分辨率"),
					SNew(SComboBox<TSharedPtr<FIntPoint>>)
					.OptionsSource(&ResolutionOptions)
					.InitiallySelectedItem(PendingResolution)
					.OnGenerateWidget(this, &SRobotMainMenu::MakeResolutionItem)
					.OnSelectionChanged(this, &SRobotMainMenu::OnResolutionPicked)
					[
						SNew(STextBlock)
						.Text(this, &SRobotMainMenu::GetResolutionLabel)
						.Font(FCoreStyle::GetDefaultFontStyle("Regular", 18))
						.ColorAndOpacity(FSlateColor(ColorText))
						.MinDesiredWidth(190.f)
					])
			]

			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.f, 0.f, 0.f, 10.f)
			[
				MakeSettingRow(LOCTEXT("Mode", "显示模式"),
					SNew(SComboBox<TSharedPtr<FString>>)
					.OptionsSource(&WindowModeOptions)
					.InitiallySelectedItem(PendingWindowMode)
					.OnGenerateWidget(this, &SRobotMainMenu::MakeTextItem)
					.OnSelectionChanged(this, &SRobotMainMenu::OnWindowModePicked)
					[
						SNew(STextBlock)
						.Text(this, &SRobotMainMenu::GetWindowModeLabel)
						.Font(FCoreStyle::GetDefaultFontStyle("Regular", 18))
						.ColorAndOpacity(FSlateColor(ColorText))
						.MinDesiredWidth(190.f)
					])
			]

			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.f, 0.f, 0.f, 20.f)
			[
				MakeSettingRow(LOCTEXT("Quality", "画质"),
					SNew(SComboBox<TSharedPtr<FString>>)
					.OptionsSource(&QualityOptions)
					.InitiallySelectedItem(PendingQuality)
					.OnGenerateWidget(this, &SRobotMainMenu::MakeTextItem)
					.OnSelectionChanged(this, &SRobotMainMenu::OnQualityPicked)
					[
						SNew(STextBlock)
						.Text(this, &SRobotMainMenu::GetQualityLabel)
						.Font(FCoreStyle::GetDefaultFontStyle("Regular", 18))
						.ColorAndOpacity(FSlateColor(ColorText))
						.MinDesiredWidth(190.f)
					])
			]

			+ SVerticalBox::Slot()
			.AutoHeight()
			.HAlign(HAlign_Center)
			.Padding(0.f, 0.f, 0.f, 16.f)
			[
				SNew(STextBlock)
				.Text(StatusText)
				.Font(FCoreStyle::GetDefaultFontStyle("Regular", 14))
				.ColorAndOpacity(FSlateColor(ColorAccent))
				.Justification(ETextJustify::Center)
			]

			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.f, 0.f, 0.f, 10.f)
			[
				MakeButton(LOCTEXT("Apply", "应用"),
					FOnClicked::CreateSP(this, &SRobotMainMenu::OnApply))
			]

			+ SVerticalBox::Slot()
			.AutoHeight()
			[
				MakeButton(LOCTEXT("Back", "返回"),
					FOnClicked::CreateSP(this, &SRobotMainMenu::OnCloseSettings))
			]
		];
}

// ─────────────────────────────────────────────
// 下拉框
// ─────────────────────────────────────────────

TSharedRef<SWidget> SRobotMainMenu::MakeResolutionItem(TSharedPtr<FIntPoint> Item)
{
	return SNew(STextBlock)
		.Text(Item.IsValid()
			? FText::FromString(FString::Printf(TEXT("%d × %d"), Item->X, Item->Y))
			: FText::GetEmpty())
		.Font(FCoreStyle::GetDefaultFontStyle("Regular", 17))
		.ColorAndOpacity(FSlateColor(ColorText));
}

TSharedRef<SWidget> SRobotMainMenu::MakeTextItem(TSharedPtr<FString> Item)
{
	return SNew(STextBlock)
		.Text(Item.IsValid() ? FText::FromString(*Item) : FText::GetEmpty())
		.Font(FCoreStyle::GetDefaultFontStyle("Regular", 17))
		.ColorAndOpacity(FSlateColor(ColorText));
}

FText SRobotMainMenu::GetResolutionLabel() const
{
	return PendingResolution.IsValid()
		? FText::FromString(FString::Printf(TEXT("%d × %d"),
			PendingResolution->X, PendingResolution->Y))
		: FText::FromString(TEXT("—"));
}

FText SRobotMainMenu::GetWindowModeLabel() const
{
	return PendingWindowMode.IsValid()
		? FText::FromString(*PendingWindowMode) : FText::FromString(TEXT("—"));
}

FText SRobotMainMenu::GetQualityLabel() const
{
	return PendingQuality.IsValid()
		? FText::FromString(*PendingQuality) : FText::FromString(TEXT("—"));
}

void SRobotMainMenu::OnResolutionPicked(TSharedPtr<FIntPoint> Item, ESelectInfo::Type)
{
	if (Item.IsValid())
	{
		PendingResolution = Item;
	}
}

void SRobotMainMenu::OnWindowModePicked(TSharedPtr<FString> Item, ESelectInfo::Type)
{
	if (Item.IsValid())
	{
		PendingWindowMode = Item;
	}
}

void SRobotMainMenu::OnQualityPicked(TSharedPtr<FString> Item, ESelectInfo::Type)
{
	if (Item.IsValid())
	{
		PendingQuality = Item;
	}
}

// ─────────────────────────────────────────────
// 按钮
// ─────────────────────────────────────────────

FReply SRobotMainMenu::OnKeyDown(const FGeometry& MyGeometry,
	const FKeyEvent& InKeyEvent)
{
	const FKey K = InKeyEvent.GetKey();

	// 确认：手柄 A / Start、回车、空格
	if (K == EKeys::Gamepad_FaceButton_Bottom ||
		K == EKeys::Gamepad_Special_Right ||
		K == EKeys::Enter || K == EKeys::SpaceBar)
	{
		if (bShowingSettings)
		{
			return OnCloseSettings();   // 设置页里确认 = 返回
		}
		return OnStart();
	}

	// 返回：手柄 B
	if (K == EKeys::Gamepad_FaceButton_Right || K == EKeys::Escape)
	{
		if (bShowingSettings)
		{
			return OnCloseSettings();
		}
	}

	return SCompoundWidget::OnKeyDown(MyGeometry, InKeyEvent);
}

FReply SRobotMainMenu::OnStart()
{
	if (ARobotPlayerController* PC = Owner.Get())
	{
		PC->StartGame();
	}
	return FReply::Handled();
}

FReply SRobotMainMenu::OnOpenSettings()
{
	bShowingSettings = true;
	RefreshPage();
	return FReply::Handled();
}

FReply SRobotMainMenu::OnCloseSettings()
{
	bShowingSettings = false;
	RefreshPage();
	return FReply::Handled();
}

FReply SRobotMainMenu::OnQuit()
{
	if (ARobotPlayerController* PC = Owner.Get())
	{
		PC->QuitGameNow();
	}
	return FReply::Handled();
}

FReply SRobotMainMenu::OnApply()
{
	ARobotPlayerController* PC = Owner.Get();
	if (!PC)
	{
		return FReply::Handled();
	}

	const FIntPoint Res = PendingResolution.IsValid()
		? *PendingResolution : FIntPoint(1280, 720);
	const int32 ModeIdx = PendingWindowMode.IsValid()
		? WindowModeOptions.IndexOfByKey(PendingWindowMode) : 1;
	const int32 QIdx = PendingQuality.IsValid()
		? QualityOptions.IndexOfByKey(PendingQuality) : 3;

	const FString Msg = PC->ApplyDisplaySettings(Res, ModeIdx, QIdx);
	StatusText = FText::FromString(Msg);
	return FReply::Handled();
}

// ─────────────────────────────────────────────
// 结算画面
// ─────────────────────────────────────────────

void SRobotEndScreen::Construct(const FArguments& InArgs)
{
	Owner = InArgs._Owner;
	bVictory = InArgs._bVictory;
	Stats = InArgs._StatsText;

	BackdropBrush = MakeShared<FSlateBrush>(
		MakeSolid(FLinearColor(0.01f, 0.015f, 0.025f, 0.82f)));
	PanelBrush = MakeShared<FSlateBrush>(
		MakeSolid(FLinearColor(0.05f, 0.06f, 0.09f, 0.95f)));
	AccentBrush = MakeShared<FSlateBrush>(MakeSolid(
		bVictory ? FLinearColor(0.30f, 0.85f, 0.55f, 1.f)
		         : FLinearColor(0.90f, 0.25f, 0.18f, 1.f)));

	const FText Title = bVictory
		? LOCTEXT("Victory", "任 务 完 成")
		: LOCTEXT("Defeat", "机 体 瘫 痪");
	const FText Hint = LOCTEXT("Restart", "按 回 车 重新部署");

	ChildSlot
	[
		SNew(SScaleBox)
		.Stretch(EStretch::ScaleToFit)
		.StretchDirection(EStretchDirection::Both)
		[
			SNew(SBox)
			.WidthOverride(1280.f)
			.HeightOverride(720.f)
			[
				SNew(SOverlay)

				// 全屏暗幕
				+ SOverlay::Slot()
				.HAlign(HAlign_Fill)
				.VAlign(VAlign_Fill)
				[ SNew(SImage).Image(BackdropBrush.Get()) ]

				// 中央面板
				+ SOverlay::Slot()
				.HAlign(HAlign_Center)
				.VAlign(VAlign_Center)
				[
					SNew(SBorder)
					.BorderImage(PanelBrush.Get())
					.Padding(FMargin(60.f, 42.f))
					[
						SNew(SVerticalBox)

						+ SVerticalBox::Slot()
						.AutoHeight()
						[
							SNew(SBox)
							.HeightOverride(6.f)
							[ SNew(SImage).Image(AccentBrush.Get()) ]
						]

						+ SVerticalBox::Slot()
						.AutoHeight()
						.HAlign(HAlign_Center)
						.Padding(0.f, 20.f, 0.f, 14.f)
						[
							SNew(STextBlock)
							.Text(Title)
							.Font(FCoreStyle::GetDefaultFontStyle("Bold", 46))
							.ColorAndOpacity(FSlateColor(ColorText))
						]

						+ SVerticalBox::Slot()
						.AutoHeight()
						.HAlign(HAlign_Center)
						.Padding(0.f, 0.f, 0.f, 24.f)
						[
							SNew(STextBlock)
							.Text(FText::FromString(Stats))
							.Font(FCoreStyle::GetDefaultFontStyle("Regular", 20))
							.ColorAndOpacity(FSlateColor(ColorDim))
						]

						+ SVerticalBox::Slot()
						.AutoHeight()
						.HAlign(HAlign_Center)
						[
							SNew(STextBlock)
							.Text(Hint)
							.Font(FCoreStyle::GetDefaultFontStyle("Regular", 17))
							.ColorAndOpacity(FSlateColor(ColorAccent))
						]
					]
				]
			]
		]
	];
}

FReply SRobotEndScreen::OnKeyDown(const FGeometry&, const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();
	if (Key == EKeys::Enter || Key == EKeys::SpaceBar)
	{
		if (ARobotPlayerController* PC = Owner.Get())
		{
			PC->RestartMission();
		}
		return FReply::Handled();
	}
	return FReply::Unhandled();
}

// ─────────────────────────────────────────────
// 改装台
// ─────────────────────────────────────────────

namespace
{
	struct FModSlotDesc
	{
		EModuleSlot Slot;
		const TCHAR* Label;
	};

	// 面板里槽位的显示顺序
	const FModSlotDesc GModSlots[] =
	{
		{ EModuleSlot::Head,          TEXT("头部") },
		{ EModuleSlot::Core,          TEXT("核心") },
		{ EModuleSlot::ArmLeft,       TEXT("左臂") },
		{ EModuleSlot::ArmRight,      TEXT("右臂") },
		{ EModuleSlot::ThrusterLeft,  TEXT("左推进器") },
		{ EModuleSlot::ThrusterRight, TEXT("右推进器") },
		{ EModuleSlot::Backpack,      TEXT("背包") },
		{ EModuleSlot::Aux01,         TEXT("辅助 1") },
		{ EModuleSlot::Aux02,         TEXT("辅助 2") },
	};
	constexpr int32 GModSlotCount = UE_ARRAY_COUNT(GModSlots);
}

void SRobotModdingPanel::Construct(const FArguments& InArgs)
{
	Owner = InArgs._Owner;
	Hint = LOCTEXT("ModHintInit",
		"用「<」「>」切换模块　·　M / Esc 关闭　·　手柄：十字键选择 / A 切换 / B 关闭").ToString();

	BackdropBrush = MakeShared<FSlateBrush>(
		MakeSolid(FLinearColor(0.01f, 0.015f, 0.025f, 0.72f)));
	PanelBrush = MakeShared<FSlateBrush>(
		MakeSolid(FLinearColor(0.05f, 0.06f, 0.09f, 0.96f)));
	RowBrush = MakeShared<FSlateBrush>(
		MakeSolid(FLinearColor(0.13f, 0.15f, 0.20f, 0.95f)));
	AccentBrush = MakeShared<FSlateBrush>(
		MakeSolid(FLinearColor(0.20f, 0.45f, 0.75f, 0.95f)));

	SmallButtonStyle = MakeShared<FButtonStyle>();
	SmallButtonStyle->SetNormal(*RowBrush);
	SmallButtonStyle->SetHovered(*AccentBrush);
	SmallButtonStyle->SetPressed(*AccentBrush);

	// 9 行槽位
	TSharedRef<SVerticalBox> RowsHost = SNew(SVerticalBox);
	for (int32 i = 0; i < GModSlotCount; ++i)
	{
		RowsHost->AddSlot()
			.AutoHeight()
			.Padding(0.f, 3.f)
			[
				MakeSlotRow(FText::FromString(GModSlots[i].Label), i)
			];
	}

	ChildSlot
	[
		SNew(SScaleBox)
		.Stretch(EStretch::ScaleToFit)
		.StretchDirection(EStretchDirection::Both)
		[
			SNew(SBox)
			.WidthOverride(1280.f)
			.HeightOverride(720.f)
			[
				SNew(SOverlay)

				+ SOverlay::Slot()
				.HAlign(HAlign_Fill)
				.VAlign(VAlign_Fill)
				[ SNew(SImage).Image(BackdropBrush.Get()) ]

				+ SOverlay::Slot()
				.HAlign(HAlign_Center)
				.VAlign(VAlign_Center)
				[
					SNew(SBox)
					.WidthOverride(760.f)
					[
						SNew(SBorder)
						.BorderImage(PanelBrush.Get())
						.Padding(FMargin(44.f, 30.f))
						[
							SNew(SVerticalBox)

							+ SVerticalBox::Slot()
							.AutoHeight()
							.HAlign(HAlign_Center)
							[
								SNew(STextBlock)
								.Text(LOCTEXT("ModTitle", "改 装 台"))
								.Font(FCoreStyle::GetDefaultFontStyle("Bold", 34))
								.ColorAndOpacity(FSlateColor(ColorText))
							]

							+ SVerticalBox::Slot()
							.AutoHeight()
							.HAlign(HAlign_Center)
							.Padding(0.f, 8.f, 0.f, 10.f)
							[
								SNew(STextBlock)
								.Text(this, &SRobotModdingPanel::StatsLine)
								.Font(FCoreStyle::GetDefaultFontStyle("Regular", 15))
								.ColorAndOpacity(FSlateColor(ColorDim))
							]

							+ SVerticalBox::Slot()
							.AutoHeight()
							.HAlign(HAlign_Center)
							.Padding(0.f, 0.f, 0.f, 10.f)
							[
								SNew(STextBlock)
								.Text(this, &SRobotModdingPanel::WeaponLine)
								.Font(FCoreStyle::GetDefaultFontStyle("Regular", 15))
								.ColorAndOpacity(FSlateColor(ColorAccent))
							]

							+ SVerticalBox::Slot()
							.AutoHeight()
							.Padding(0.f, 0.f, 0.f, 10.f)
							[
								SNew(SBox)
								.HeightOverride(4.f)
								[ SNew(SImage).Image(AccentBrush.Get()) ]
							]

							+ SVerticalBox::Slot()
							.AutoHeight()
							[ RowsHost ]

							+ SVerticalBox::Slot()
							.AutoHeight()
							.HAlign(HAlign_Center)
							.Padding(0.f, 14.f, 0.f, 0.f)
							[
								SNew(STextBlock)
								.Text(this, &SRobotModdingPanel::HintText)
								.Font(FCoreStyle::GetDefaultFontStyle("Regular", 15))
								.ColorAndOpacity(FSlateColor(ColorAccent))
							]

							+ SVerticalBox::Slot()
							.AutoHeight()
							.HAlign(HAlign_Center)
							.Padding(0.f, 14.f, 0.f, 0.f)
							[
								SNew(SButton)
								.ButtonStyle(SmallButtonStyle.Get())
								.OnClicked(FOnClicked::CreateSP(
									this, &SRobotModdingPanel::OnClose))
								[
									SNew(SBox)
									.Padding(FMargin(18.f, 6.f))
									[
										SNew(STextBlock)
										.Text(LOCTEXT("ModClose", "关闭（M / Esc）"))
										.Font(FCoreStyle::GetDefaultFontStyle(
											"Bold", 16))
										.ColorAndOpacity(FSlateColor(ColorText))
									]
								]
							]
						]
					]
				]
			]
		]
	];
}

TSharedRef<SWidget> SRobotModdingPanel::MakeSlotRow(const FText& SlotLabel,
	int32 SlotIndex)
{
	return SNew(SHorizontalBox)

		+ SHorizontalBox::Slot()
		.AutoWidth()
		.VAlign(VAlign_Center)
		.Padding(0.f, 0.f, 12.f, 0.f)
		[
			SNew(SBox)
			.WidthOverride(92.f)
			[
				SNew(STextBlock)
				.Text(SlotLabel)
				.Font(FCoreStyle::GetDefaultFontStyle("Regular", 15))
				.ColorAndOpacity(FSlateColor(ColorDim))
			]
		]

		+ SHorizontalBox::Slot()
		.FillWidth(1.f)
		.VAlign(VAlign_Center)
		[
			SNew(STextBlock)
			.Text(this, &SRobotModdingPanel::ModuleNameAt, SlotIndex)
			.Font(FCoreStyle::GetDefaultFontStyle("Bold", 17))
			.ColorAndOpacity(FSlateColor(ColorText))
		]

		+ SHorizontalBox::Slot()
		.AutoWidth()
		.Padding(4.f, 0.f)
		[
			SNew(SButton)
			.ButtonStyle(SmallButtonStyle.Get())
			.OnClicked(FOnClicked::CreateSP(
				this, &SRobotModdingPanel::OnCycle, SlotIndex, -1))
			[
				SNew(SBox)
				.Padding(FMargin(12.f, 2.f))
				[
					SNew(STextBlock)
					.Text(FText::FromString(TEXT("<")))
					.Font(FCoreStyle::GetDefaultFontStyle("Bold", 18))
					.ColorAndOpacity(FSlateColor(ColorText))
				]
			]
		]

		+ SHorizontalBox::Slot()
		.AutoWidth()
		.Padding(4.f, 0.f)
		[
			SNew(SButton)
			.ButtonStyle(SmallButtonStyle.Get())
			.OnClicked(FOnClicked::CreateSP(
				this, &SRobotModdingPanel::OnCycle, SlotIndex, +1))
			[
				SNew(SBox)
				.Padding(FMargin(12.f, 2.f))
				[
					SNew(STextBlock)
					.Text(FText::FromString(TEXT(">")))
					.Font(FCoreStyle::GetDefaultFontStyle("Bold", 18))
					.ColorAndOpacity(FSlateColor(ColorText))
				]
			]
		];
}

FReply SRobotModdingPanel::OnCycle(int32 SlotIndex, int32 Direction)
{
	if (ARobotPlayerController* PC = Owner.Get())
	{
		if (SlotIndex >= 0 && SlotIndex < GModSlotCount)
		{
			Hint = PC->CycleModule(GModSlots[SlotIndex].Slot, Direction);
		}
	}
	return FReply::Handled();
}

FReply SRobotModdingPanel::OnClose()
{
	if (ARobotPlayerController* PC = Owner.Get())
	{
		PC->ToggleModding();
	}
	return FReply::Handled();
}

FReply SRobotModdingPanel::OnKeyDown(const FGeometry&, const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();

	// ── 关闭：M / Esc / 手柄 B / Start ──
	if (Key == EKeys::M || Key == EKeys::Escape ||
		Key == EKeys::Gamepad_FaceButton_Right ||
		Key == EKeys::Gamepad_Special_Right)
	{
		return OnClose();
	}

	// ── 手柄导航 ──
	// 面板是 9 行槽位，没有鼠标指针时靠"选中行 + 左右切换"操作。
	// 选中行不做高亮（布局里每行是独立构建的，加高亮要重构行控件），
	// 但提示行会实时显示当前选中的槽位名 —— 有反馈就够用了。
	if (Key == EKeys::Gamepad_DPad_Up || Key == EKeys::Gamepad_DPad_Down)
	{
		const int32 Step = (Key == EKeys::Gamepad_DPad_Up) ? -1 : 1;
		SelectedRow = (SelectedRow + GModSlotCount + Step) % GModSlotCount;
		Hint = FString::Printf(TEXT("当前槽位：%s　（A / ←→ 切换模块）"),
			GModSlots[SelectedRow].Label);
		return FReply::Handled();
	}
	if (Key == EKeys::Gamepad_DPad_Left || Key == EKeys::Gamepad_DPad_Right ||
		Key == EKeys::Gamepad_FaceButton_Bottom)
	{
		const int32 Dir = (Key == EKeys::Gamepad_DPad_Left) ? -1 : 1;
		return OnCycle(SelectedRow, Dir);
	}

	return FReply::Unhandled();
}

FText SRobotModdingPanel::StatsLine() const
{
	ARobotPlayerController* PC = Owner.Get();
	ARobotCharacter* R = PC ? Cast<ARobotCharacter>(PC->GetPawn()) : nullptr;
	UAssemblyComponent* A = R ? R->GetAssembly() : nullptr;
	if (!A)
	{
		return LOCTEXT("NoAssembly", "未装载机体");
	}
	return FText::FromString(FString::Printf(
		TEXT("速度 %.0f　·　质量 %.2f　·　供电余量 %+.1f　·　散热 %.1f　·　热容 %.0f"),
		A->GetEffectiveWalkSpeed(), A->GetTotalMass(),
		A->GetPowerHeadroom(), A->GetTotalHeatDissipation(),
		A->GetTotalHeatCapacity()));
}

FText SRobotModdingPanel::HintText() const
{
	return FText::FromString(Hint);
}

FText SRobotModdingPanel::WeaponLine() const
{
	ARobotPlayerController* PC = Owner.Get();
	ARobotCharacter* R = PC ? Cast<ARobotCharacter>(PC->GetPawn()) : nullptr;
	UAssemblyComponent* A = R ? R->GetAssembly() : nullptr;
	if (!A)
	{
		return FText::GetEmpty();
	}
	float Dmg = 0.f, Interval = 0.f, Heat = 0.f;
	A->GetWeaponProfile(Dmg, Interval, Heat);
	// 射速换算成"发/秒"更好读（间隔 0.115s ≈ 8.7 发/秒）
	const float Rps = Interval > KINDA_SMALL_NUMBER ? 1.f / Interval : 0.f;
	return FText::FromString(FString::Printf(
		TEXT("武器：伤害 %.0f　·　%.1f 发/秒　·　积热 %.1f/发（过热约 %.1f 秒）"),
		Dmg, Rps, Heat,
		Heat > KINDA_SMALL_NUMBER ? 100.f / Heat / Rps : 0.f));
}

FText SRobotModdingPanel::ModuleNameAt(int32 SlotIndex) const
{
	if (ARobotPlayerController* PC = Owner.Get())
	{
		if (SlotIndex >= 0 && SlotIndex < GModSlotCount)
		{
			if (URobotModuleData* M = PC->GetMountedModule(GModSlots[SlotIndex].Slot))
			{
				return M->DisplayName;
			}
		}
	}
	return LOCTEXT("EmptySlot", "— 空 —");
}

#undef LOCTEXT_NAMESPACE
