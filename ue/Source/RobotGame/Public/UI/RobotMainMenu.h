// 主菜单 —— 纯 C++ Slate，不依赖任何 UMG 资产
//
// 为什么用 Slate 而不是 UMG：项目里一个 UMG 资产都没有，而脚本创建
// UserWidget 资产这条路不通（UE 没给 Python 暴露 WidgetBlueprintFactory）。
// Slate 完全写在 C++ 里，不需要任何资产，改一行代码就能改界面。
#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

class ARobotPlayerController;
class SBox;

/**
 * 主菜单：标题 + 开始游戏 / 设置 / 退出；设置页里可调分辨率、
 * 显示模式、画质，并显示当前桌面分辨率。
 */
class SRobotMainMenu : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SRobotMainMenu) {}
		SLATE_ARGUMENT(TWeakObjectPtr<ARobotPlayerController>, Owner)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	/** 当前是否停在设置页（外部用不到，调试方便） */
	bool IsShowingSettings() const { return bShowingSettings; }

	// ── 手柄支持 ──
	// 菜单是用 FInputModeUIOnly 显示的，键盘/手柄事件先到 Slate，
	// 到不了 PlayerController 的 InputComponent。所以"确认/返回"必须
	// 在这个控件里处理，否则插着手柄根本进不了游戏。
	virtual bool SupportsKeyboardFocus() const override { return true; }
	virtual FReply OnKeyDown(const FGeometry& MyGeometry,
		const FKeyEvent& InKeyEvent) override;

private:
	// ── 页面搭建 ──
	TSharedRef<SWidget> BuildPage();
	TSharedRef<SWidget> BuildMainPage();
	TSharedRef<SWidget> BuildSettingsPage();
	void RefreshPage();

	TSharedRef<SWidget> MakeTitle(const FText& Text, float Size,
		const FLinearColor& Color);
	TSharedRef<SWidget> MakeButton(const FText& Label, FOnClicked OnClicked,
		float FontSize = 24.f);
	TSharedRef<SWidget> MakeSettingRow(const FText& Label,
		TSharedRef<SWidget> Control);
	TSharedRef<SWidget> MakeResolutionItem(TSharedPtr<FIntPoint> Item);
	TSharedRef<SWidget> MakeTextItem(TSharedPtr<FString> Item);

	// ── 按钮回调 ──
	FReply OnStart();
	FReply OnOpenSettings();
	FReply OnCloseSettings();
	FReply OnQuit();
	FReply OnApply();

	// ── 下拉框回调 ──
	void OnResolutionPicked(TSharedPtr<FIntPoint> Item, ESelectInfo::Type);
	void OnWindowModePicked(TSharedPtr<FString> Item, ESelectInfo::Type);
	void OnQualityPicked(TSharedPtr<FString> Item, ESelectInfo::Type);
	FText GetResolutionLabel() const;
	FText GetWindowModeLabel() const;
	FText GetQualityLabel() const;

	void BuildOptions();

	TWeakObjectPtr<ARobotPlayerController> Owner;

	bool bShowingSettings = false;
	TSharedPtr<SBox> PageHost;

	// 设置项
	TArray<TSharedPtr<FIntPoint>> ResolutionOptions;
	TArray<TSharedPtr<FString>> WindowModeOptions;
	TArray<TSharedPtr<FString>> QualityOptions;

	TSharedPtr<FIntPoint> PendingResolution;
	TSharedPtr<FString> PendingWindowMode;
	TSharedPtr<FString> PendingQuality;

	FText StatusText;

	// Slate 不接管画刷生命周期，必须自己持有
	TSharedPtr<struct FSlateBrush> BackdropBrush;
	TSharedPtr<struct FSlateBrush> PanelBrush;
	TSharedPtr<struct FSlateBrush> AccentBrush;
	TSharedPtr<struct FSlateBrush> ButtonBrush;
	TSharedPtr<struct FSlateBrush> ButtonHoverBrush;
	TSharedPtr<struct FSlateBrush> ButtonPressedBrush;
	TSharedPtr<struct FSlateBrush> RowBrush;
	TSharedPtr<struct FButtonStyle> ButtonStyle;
};

/**
 * 结算画面：胜利 / 失败时覆盖全屏，按回车重新开始。
 *
 * 为什么需要：垂直切片之前没有任何"目标与结算"——
 * 敌人打完就没了、自己被打瘫就卡在那儿，玩家不知道"这局算不算完"。
 * 一个明确的结算画面是"这是游戏"和"这是个技术演示"之间的分界线。
 */
class SRobotEndScreen : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SRobotEndScreen) {}
		SLATE_ARGUMENT(TWeakObjectPtr<ARobotPlayerController>, Owner)
		SLATE_ARGUMENT(bool, bVictory)
		SLATE_ARGUMENT(FString, StatsText)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	/** 面板要能拿到键盘焦点（回车重开靠它） */
	virtual bool SupportsKeyboardFocus() const override { return true; }
	virtual FReply OnKeyDown(const FGeometry& MyGeometry,
		const FKeyEvent& InKeyEvent) override;

private:
	TWeakObjectPtr<ARobotPlayerController> Owner;
	bool bVictory = false;
	FString Stats;

	TSharedPtr<struct FSlateBrush> BackdropBrush;
	TSharedPtr<struct FSlateBrush> PanelBrush;
	TSharedPtr<struct FSlateBrush> AccentBrush;
};

/**
 * 改装台面板（M 键打开）。
 *
 * 设计支柱 P1"改装改变玩法"的载体：9 个槽位逐个显示当前模块，
 * 用 &lt; &gt; 循环切换候选模块；装配失败时把 CanMount 给出的
 * 玩家可读原因显示在提示行（供电超载会直接说明差多少）。
 * 顶部实时显示三条约束的汇总（质量/速度/供电余量/散热）。
 */
class SRobotModdingPanel : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SRobotModdingPanel) {}
		SLATE_ARGUMENT(TWeakObjectPtr<ARobotPlayerController>, Owner)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	virtual bool SupportsKeyboardFocus() const override { return true; }
	virtual FReply OnKeyDown(const FGeometry& MyGeometry,
		const FKeyEvent& InKeyEvent) override;

private:
	/** 一行：槽位名 + 当前模块 + 两个切换按钮 */
	TSharedRef<SWidget> MakeSlotRow(const FText& SlotLabel, int32 SlotIndex);

	/** 按钮回调 */
	FReply OnCycle(int32 SlotIndex, int32 Direction);
	FReply OnClose();

	/** 顶部汇总行（质量/速度/供电/散热/热容） */
	FText StatsLine() const;
	/** 顶部武器行（伤害/间隔/每发积热，含武器臂乘数） */
	FText WeaponLine() const;
	/** 提示行：最近一次操作结果 / 失败原因 */
	FText HintText() const;
	/** 槽位当前模块名 */
	FText ModuleNameAt(int32 SlotIndex) const;

	TWeakObjectPtr<ARobotPlayerController> Owner;

	/** 手柄选中的槽位（0..8）。键盘/鼠标玩家用不到，手柄靠它导航 */
	int32 SelectedRow = 0;

	/** 提示行内容（Slate 每帧重读） */
	FString Hint;

	TSharedPtr<struct FSlateBrush> BackdropBrush;
	TSharedPtr<struct FSlateBrush> PanelBrush;
	TSharedPtr<struct FSlateBrush> RowBrush;
	TSharedPtr<struct FSlateBrush> AccentBrush;
	TSharedPtr<struct FButtonStyle> SmallButtonStyle;
};
