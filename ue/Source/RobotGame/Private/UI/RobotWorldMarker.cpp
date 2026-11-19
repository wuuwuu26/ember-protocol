#include "UI/RobotWorldMarker.h"

#include "RobotPlayerController.h"
#include "UI/RobotFloatLabelLayer.h"

#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

#include "Styling/CoreStyle.h"
#include "Styling/SlateTypes.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/Text/STextBlock.h"

void SRobotWorldMarkers::Construct(const FArguments& InArgs)
{
	Owner = InArgs._Owner;

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
				+ SOverlay::Slot()
				.HAlign(HAlign_Fill)
				.VAlign(VAlign_Fill)
				[
					SAssignNew(Layer, SRobotFloatLabelLayer)
				]
			]
		]
	];
}

ARobotPlayerController* SRobotWorldMarkers::GetPC() const
{
	return Cast<ARobotPlayerController>(Owner.Get());
}

bool SRobotWorldMarkers::WorldToCanvas(const FVector& World, FVector2D& OutCanvas) const
{
	if (!GEngine || !GEngine->GameViewport)
	{
		return false;
	}
	FVector2D ViewportSize = FVector2D::ZeroVector;
	GEngine->GameViewport->GetViewportSize(ViewportSize);
	if (ViewportSize.X < 1.f || ViewportSize.Y < 1.f)
	{
		return false;
	}

	FVector2D Screen = FVector2D::ZeroVector;
	if (!UGameplayStatics::ProjectWorldToScreen(Owner.Get(), World, Screen, true))
	{
		return false;
	}

	// SScaleBox(ScaleToFit) 会把 1280x720 等比缩放并居中。
	// 用同一套公式换算，保证和 HUD 的坐标对齐。
	const float Scale = FMath::Min(ViewportSize.X / DesignW,
		ViewportSize.Y / DesignH);
	if (Scale < KINDA_SMALL_NUMBER)
	{
		return false;
	}
	const float OffsetX = (ViewportSize.X - DesignW * Scale) * 0.5f;
	const float OffsetY = (ViewportSize.Y - DesignH * Scale) * 0.5f;

	OutCanvas.X = (Screen.X - OffsetX) / Scale;
	OutCanvas.Y = (Screen.Y - OffsetY) / Scale;
	return true;
}

void SRobotWorldMarkers::Tick(const FGeometry& AllottedGeometry,
	const double InCurrentTime, const float InDeltaTime)
{
	SCompoundWidget::Tick(AllottedGeometry, InCurrentTime, InDeltaTime);

	ARobotPlayerController* PC = GetPC();
	if (!PC || !Layer.IsValid())
	{
		return;
	}

	const int32 NumHints = PC->GetPartHintCount();
	const int32 NumNumbers = PC->GetDamageNumberCount();
	int32 Needed = NumHints + NumNumbers;
	if (Needed > 18)
	{
		// 上限：同时最多 18 个标签。超出的部分直接不画 ——
		// 实战里超过 18 条同屏时画面已经糊了，多画只会更乱。
		Needed = 18;
	}

	int32 Used = 0;

	// ① 部位提示（准心指着敌机时显示"腿部 42%"）
	for (int32 i = 0; i < NumHints && Used < Needed; ++i)
	{
		FVector World;
		FText Label;
		FLinearColor Color;
		if (!PC->GetPartHint(i, World, Label, Color))
		{
			continue;
		}
		FVector2D Canvas;
		if (!WorldToCanvas(World, Canvas))
		{
			continue;
		}

		while (Pool.Num() <= Used)
		{
			FFloatTextItem Item;
			SAssignNew(Item.Label, STextBlock)
				.SimpleTextMode(true)
				.Font(FCoreStyle::GetDefaultFontStyle("Bold", 18))
				.ColorAndOpacity(FSlateColor(FLinearColor::White))
				.ShadowOffset(FVector2D(1.5f, 1.5f))
				.ShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.85f))
				.Justification(ETextJustify::Center);
			Layer->AddLabel(Item.Label.ToSharedRef());
			Pool.Add(Item);
		}

		FFloatTextItem& Item = Pool[Used];
		Item.Label->SetVisibility(EVisibility::HitTestInvisible);
		Item.Label->SetText(Label);
		Item.Label->SetColorAndOpacity(FSlateColor(Color));
		Item.Label->SetFont(FCoreStyle::GetDefaultFontStyle("Regular", 14));
		Layer->SetLabelPosition(Used, Canvas + FVector2D(0.f, -50.f));
		++Used;
	}

	// ② 伤害数字（从命中点往上飘）
	for (int32 i = 0; i < NumNumbers && Used < Needed; ++i)
	{
		FVector World;
		FText Label;
		FLinearColor Color;
		float Alpha = 1.f;
		bool bBig = false;
		float DriftX = 0.f;
		if (!PC->GetDamageNumber(i, World, Label, Color, Alpha, bBig, DriftX))
		{
			continue;
		}
		FVector2D Canvas;
		if (!WorldToCanvas(World, Canvas))
		{
			continue;
		}

		while (Pool.Num() <= Used)
		{
			FFloatTextItem Item;
			SAssignNew(Item.Label, STextBlock)
				.SimpleTextMode(true)
				.Font(FCoreStyle::GetDefaultFontStyle("Bold", 18))
				.ColorAndOpacity(FSlateColor(FLinearColor::White))
				.ShadowOffset(FVector2D(1.5f, 1.5f))
				.ShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.85f))
				.Justification(ETextJustify::Center);
			Layer->AddLabel(Item.Label.ToSharedRef());
			Pool.Add(Item);
		}

		FFloatTextItem& Item = Pool[Used];
		Item.Label->SetVisibility(EVisibility::HitTestInvisible);
		Item.Label->SetText(Label);

		FLinearColor C = Color;
		C.A *= Alpha;
		Item.Label->SetColorAndOpacity(FSlateColor(C));
		Item.Label->SetFont(FCoreStyle::GetDefaultFontStyle("Bold",
			bBig ? 26 : 19));

		// 部位拆解浮得更高，与连发普通数字上下错开，避免重叠
		const float Rise = (1.f - Alpha) * (bBig ? 55.f : 42.f);
		Layer->SetLabelPosition(Used, Canvas + FVector2D(DriftX, -Rise));
		++Used;
	}

	// ③ 多余的隐藏
	for (int32 i = Used; i < Pool.Num(); ++i)
	{
		Pool[i].Label->SetVisibility(EVisibility::Collapsed);
	}

	LastNumberCount = NumNumbers;
}
