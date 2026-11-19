// 余火协议 —— 全局 UI 主题（第一百零七轮）
//
// 之前配色硬编码散落在 RobotHUD.cpp / RobotMainMenu.cpp / RobotEndScreen 等处，
// 同一个"冷白文字"在两处数值都不一样。这里集中成一份共享常量，作为
// "全局主题重构"的基础：所有 Slate 界面从这里取色/取字体/取尺寸。
//
// 视觉语言（沿用项目既定风格）：
//   深钢蓝底  +  琥珀铜橙强调（呼应 M_Copper / 主菜单 ColorAccent）
//   + 冷白主文字 / 灰蓝次文字  +  青蓝数据色（呼应冷却液/弹丸）
// 纯 C++ 头文件，无需 .generated.h，不参与 UHT —— 谁都能 include。
#pragma once

#include "CoreMinimal.h"
#include "Styling/CoreStyle.h"
#include "Styling/SlateColor.h"

namespace RobotTheme
{
	// ── 强调色 ──
	// 琥珀铜橙：主强调。与材质 M_Copper、主菜单标题下划线同源。
	const FLinearColor Accent      (1.00f, 0.72f, 0.30f, 1.f);
	const FLinearColor AccentDim   (0.55f, 0.38f, 0.14f, 1.f);
	// 青蓝：数据/状态辅助色。与冷却液(0.12,0.92,1.0)、弹丸青呼应。
	const FLinearColor Cyan        (0.30f, 0.80f, 1.00f, 1.f);
	const FLinearColor CyanDim     (0.14f, 0.36f, 0.52f, 1.f);

	// ── 文字 ──
	const FLinearColor Text        (0.92f, 0.95f, 1.00f, 1.f); // 冷白主文字
	const FLinearColor TextDim     (0.55f, 0.62f, 0.72f, 1.f); // 灰蓝次文字
	const FLinearColor TextFaint   (0.38f, 0.44f, 0.54f, 1.f); // 更弱的标注

	// ── 面板 / 画刷 ──
	const FLinearColor PanelBg     (0.030f, 0.042f, 0.062f, 0.80f); // 半透信息舱
	const FLinearColor PanelSolid  (0.055f, 0.070f, 0.100f, 0.96f);
	const FLinearColor Backdrop    (0.015f, 0.020f, 0.030f, 0.97f); // 全屏底
	const FLinearColor BarBg       (0.10f, 0.12f, 0.16f, 0.90f);     // 条槽底
	const FLinearColor Rule        (0.20f, 0.27f, 0.36f, 0.55f);     // 装饰分隔线
	const FLinearColor Frame       (0.28f, 0.40f, 0.55f, 0.40f);     // 面板描边

	// ── 语义色 ──
	const FLinearColor Warn        (1.00f, 0.25f, 0.20f, 1.f);       // 过热/警告
	const FLinearColor Okay        (0.30f, 0.85f, 0.55f, 1.f);       // 胜利/正常
	const FLinearColor DangerFlash(0.90f, 0.07f, 0.05f, 1.f);       // 受击暗角

	// 热量条阈值色
	const FLinearColor HeatHot     (1.00f, 0.18f, 0.15f, 1.f);
	const FLinearColor HeatWarm    (1.00f, 0.62f, 0.16f, 1.f);
	const FLinearColor HeatCool    (0.90f, 0.92f, 0.95f, 1.f);
	// 电力条阈值色
	const FLinearColor PowerLow    (1.00f, 0.55f, 0.15f, 1.f);
	const FLinearColor PowerOk     (0.35f, 0.72f, 1.00f, 1.f);

	// ── 尺寸 ──
	constexpr float DesignW = 1280.f;
	constexpr float DesignH = 720.f;
	constexpr float BarW = 330.f;
	constexpr float BarH = 16.f;

	// ── 字体（引擎默认 Roboto，无自定义字体资产）──
	inline FSlateFontInfo Font(int32 Size, bool bBold = false)
	{
		return FCoreStyle::GetDefaultFontStyle(bBold ? "Bold" : "Regular", Size);
	}

	inline FSlateColor Slate(const FLinearColor& C) { return FSlateColor(C); }
}
