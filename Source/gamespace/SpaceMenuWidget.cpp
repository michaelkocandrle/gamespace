// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceMenuWidget.h"

#include "Engine/Texture2D.h"
#include "Framework/Application/SlateApplication.h"
#include "ImageUtils.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Misc/Paths.h"
#include "Rendering/DrawElements.h"
#include "Rendering/SlateRenderer.h"
#include "SpacePlayerController.h"
#include "SpaceUserSettings.h"
#include "Styling/CoreStyle.h"
#include "Styling/SlateBrush.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SMenuAnchor.h"
#include "Widgets/Input/SSlider.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SSpacer.h"
#include "Widgets/Layout/SWidgetSwitcher.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SLeafWidget.h"
#include "Widgets/SNullWidget.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "SpaceMenu"

// Sizes are in Slate units at 1080p (Slate scales them with the window), measured from the author's 1440p capture of
// SC 4.10 (starcitizenreference/MenuSettings_OwnCapture_Notes.md).
namespace SpaceMenuStyle
{
	FLinearColor Srgb(uint8 R, uint8 G, uint8 B, float A = 1.f)
	{
		FLinearColor Color = FLinearColor::FromSRGBColor(FColor(R, G, B));
		Color.A = A;
		return Color;
	}

	// SC's slightly warm, green-tinted off-white and its dark greys; the hover bar is SC's dark teal.
	const FLinearColor Text = Srgb(225, 236, 232);
	const FLinearColor TextDim = Srgb(140, 150, 146);
	const FLinearColor Outline = Srgb(205, 214, 209, 0.95f);
	const FLinearColor OutlineHover = Srgb(240, 248, 244);
	const FLinearColor OutlineDim = Srgb(120, 128, 124, 0.9f);
	const FLinearColor ButtonFill = Srgb(67, 76, 71, 0.72f);
	const FLinearColor ButtonHover = Srgb(88, 99, 93, 0.85f);
	const FLinearColor TabActive = Srgb(69, 74, 68);
	const FLinearColor TabHover = Srgb(40, 45, 42);
	const FLinearColor RowHover = Srgb(1, 44, 60);
	const FLinearColor RowHoverEdge = Srgb(28, 104, 128);
	const FLinearColor FieldFill = Srgb(13, 20, 20);
	const FLinearColor FieldEdge = Srgb(62, 72, 70);
	const FLinearColor PlayFill = Srgb(192, 200, 176);
	const FLinearColor PlayHover = Srgb(222, 230, 206);
	const FLinearColor PlayText = Srgb(18, 22, 18);
	const FLinearColor Page = Srgb(0, 2, 0);

	/**
	 * Oxanium (SIL OFL, Content/UI/Fonts, static 400 / 500 cut from the variable font): squarish with rounded corners like
	 * SC's menu face, and unlike Electrolize, the closer match, it has every Czech letter. Read from the file like the
	 * HUD's faces (no font assets in a headless editor); the engine face if the file is missing.
	 */
	FSlateFontInfo Font(bool bMedium, float Size, int32 LetterSpacing = 0)
	{
		const FString Path = FPaths::ProjectContentDir() / TEXT("UI/Fonts") / (bMedium ? TEXT("Oxanium-Medium.ttf") : TEXT("Oxanium-Regular.ttf"));
		FSlateFontInfo Info = FPaths::FileExists(Path) ? FSlateFontInfo(Path, Size)
			: FCoreStyle::GetDefaultFontStyle(bMedium ? TEXT("Bold") : TEXT("Regular"), Size);
		Info.LetterSpacing = LetterSpacing;
		return Info;
	}

	const FSlateBrush* White()
	{
		return FCoreStyle::Get().GetBrush("WhiteBrush");
	}

	/** A button that draws nothing itself: the boxes inside it do. */
	const FButtonStyle& FlatButton()
	{
		static const FButtonStyle Style = FButtonStyle()
			.SetNormal(FSlateNoResource())
			.SetHovered(FSlateNoResource())
			.SetPressed(FSlateNoResource())
			.SetDisabled(FSlateNoResource())
			.SetNormalPadding(FMargin(0.f))
			.SetPressedPadding(FMargin(0.f));
		return Style;
	}

	/** SC's slider: dark track, white rectangular thumb. */
	const FSliderStyle& Slider()
	{
		static const FSliderStyle Style = []()
		{
			FSliderStyle S = FCoreStyle::Get().GetWidgetStyle<FSliderStyle>("Slider");
			const FSlateColorBrush Bar(FieldFill);
			S.SetNormalBarImage(Bar).SetHoveredBarImage(Bar).SetDisabledBarImage(Bar);
			FSlateColorBrush Thumb(FLinearColor::White);
			Thumb.ImageSize = FVector2D(9.0, 22.0);
			S.SetNormalThumbImage(Thumb).SetHoveredThumbImage(Thumb).SetDisabledThumbImage(Thumb);
			S.SetBarThickness(22.f);
			return S;
		}();
		return Style;
	}

	/** A thin white scroll bar on the right, as SC's. */
	const FScrollBarStyle& ScrollBar()
	{
		static const FScrollBarStyle Style = []()
		{
			FScrollBarStyle S = FCoreStyle::Get().GetWidgetStyle<FScrollBarStyle>("ScrollBar");
			const FSlateColorBrush Thumb(Srgb(230, 236, 233));
			S.SetNormalThumbImage(Thumb).SetHoveredThumbImage(Thumb).SetDraggedThumbImage(Thumb);
			S.SetVerticalBackgroundImage(FSlateNoResource()).SetVerticalTopSlotImage(FSlateNoResource()).SetVerticalBottomSlotImage(FSlateNoResource());
			return S;
		}();
		return Style;
	}

	/** 0 means no limit. */
	const int32 FrameLimits[] = { 0, 30, 60, 120, 144, 165, 240 };

	/** SC's named upscaling modes over our TSR render scale (75 % is ours, the default). */
	const float UpscaleScales[] = { 100.f, 77.f, 75.f, 67.f, 58.f, 50.f };

	const FText QualityName(int32 Level)
	{
		static const FText Names[] = { NSLOCTEXT("SpaceMenu", "Low", "Nízká"), NSLOCTEXT("SpaceMenu", "Medium", "Střední"),
			NSLOCTEXT("SpaceMenu", "High", "Vysoká"), NSLOCTEXT("SpaceMenu", "Epic", "Velmi vysoká"), NSLOCTEXT("SpaceMenu", "Cinematic", "Filmová") };
		return Names[FMath::Clamp(Level, 0, 4)];
	}
	const EWindowMode::Type WindowModes[] = { EWindowMode::WindowedFullscreen, EWindowMode::Fullscreen, EWindowMode::Windowed };

	/** A filled convex polygon in the widget's space, optionally textured by Brush (UVs from the size). */
	void Polygon(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geometry, const TArray<FVector2f>& Points,
		const FLinearColor& Color, const FSlateBrush* Brush = nullptr)
	{
		if (Points.Num() < 3 || !FSlateApplication::IsInitialized())
		{
			return;
		}
		const FSlateResourceHandle Handle = FSlateApplication::Get().GetRenderer()->GetResourceHandle(Brush ? *Brush : *White());
		const FSlateRenderTransform& Transform = Geometry.GetAccumulatedRenderTransform();
		const FVector2f Size = Geometry.GetLocalSize();
		const FColor Vertex = Color.ToFColor(true);
		TArray<FSlateVertex> Verts;
		TArray<SlateIndex> Indices;
		for (const FVector2f& Point : Points)
		{
			const FVector2f UV = Brush ? FVector2f(Point.X / FMath::Max(Size.X, 1.f), Point.Y / FMath::Max(Size.Y, 1.f)) : FVector2f(0.5f, 0.5f);
			Verts.Add(FSlateVertex::Make(Transform, Point, UV, Vertex));
		}
		for (int32 Index = 1; Index + 1 < Points.Num(); ++Index)
		{
			Indices.Add(0);
			Indices.Add(SlateIndex(Index));
			Indices.Add(SlateIndex(Index + 1));
		}
		FSlateDrawElement::MakeCustomVerts(Out, Layer, Handle, Verts, Indices, nullptr, 0, 0);
	}

	/** The outline of a box with its bottom-right corner cut by Corner. */
	TArray<FVector2f> CutBox(const FVector2f& Size, float Corner, float Inset = 0.f)
	{
		const float C = FMath::Clamp(Corner, 0.f, FMath::Min(Size.X, Size.Y) * 0.5f);
		const float I = Inset;
		return { { I, I }, { Size.X - I, I }, { Size.X - I, Size.Y - C - I * 0.4f }, { Size.X - C - I * 0.4f, Size.Y - I }, { I, Size.Y - I } };
	}
}

/**
 * SC's box: a fill (or a picture), a thin outline and a cut bottom-right corner, with other colours while the mouse is
 * over it (the box is hit-testable, so it is "hovered" whenever the cursor is over it or its content).
 */
class SSpaceBox : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SSpaceBox)
		: _Fill(FLinearColor::Transparent), _Outline(FLinearColor::Transparent), _HoverFill(FLinearColor(0, 0, 0, -1)),
		  _HoverOutline(FLinearColor(0, 0, 0, -1)), _Corner(10.f), _Thickness(1.5f), _Padding(0.f), _Brush(nullptr) {}
		SLATE_ATTRIBUTE(FLinearColor, Fill)
		SLATE_ATTRIBUTE(FLinearColor, Outline)
		/** Alpha below 0: same as Fill / Outline. */
		SLATE_ATTRIBUTE(FLinearColor, HoverFill)
		SLATE_ATTRIBUTE(FLinearColor, HoverOutline)
		SLATE_ARGUMENT(float, Corner)
		SLATE_ARGUMENT(float, Thickness)
		SLATE_ARGUMENT(FMargin, Padding)
		/** A picture filling the box, cut corner included. */
		SLATE_ARGUMENT(const FSlateBrush*, Brush)
		SLATE_DEFAULT_SLOT(FArguments, Content)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs)
	{
		Fill = InArgs._Fill;
		Outline = InArgs._Outline;
		HoverFill = InArgs._HoverFill;
		HoverOutline = InArgs._HoverOutline;
		Corner = InArgs._Corner;
		Thickness = InArgs._Thickness;
		Brush = InArgs._Brush;
		ChildSlot.Padding(InArgs._Padding)[ InArgs._Content.Widget ];
	}

	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& Geometry, const FSlateRect& Culling, FSlateWindowElementList& Out,
		int32 Layer, const FWidgetStyle& Style, bool bParentEnabled) const override
	{
		const FVector2f Size = Geometry.GetLocalSize();
		const bool bHover = IsHovered();
		const FLinearColor Tint = Style.GetColorAndOpacityTint();
		FLinearColor FillColor = bHover && HoverFill.Get().A >= 0.f ? HoverFill.Get() : Fill.Get();
		FLinearColor LineColor = bHover && HoverOutline.Get().A >= 0.f ? HoverOutline.Get() : Outline.Get();
		if (Brush)
		{
			SpaceMenuStyle::Polygon(Out, Layer, Geometry, SpaceMenuStyle::CutBox(Size, Corner), FLinearColor::White * Tint, Brush);
		}
		if (FillColor.A > 0.001f)
		{
			SpaceMenuStyle::Polygon(Out, Layer, Geometry, SpaceMenuStyle::CutBox(Size, Corner), FillColor * Tint);
		}
		if (LineColor.A > 0.001f)
		{
			TArray<FVector2f> Line = SpaceMenuStyle::CutBox(Size, Corner, Thickness * 0.5f);
			const FVector2f First = Line[0];  // not Line.Add(Line[0]): the reference dies when Add grows the array
			Line.Add(First);
			FSlateDrawElement::MakeLines(Out, Layer + 1, Geometry.ToPaintGeometry(), Line, ESlateDrawEffect::None, LineColor * Tint, true, Thickness);
		}
		return SCompoundWidget::OnPaint(Args, Geometry, Culling, Out, Layer + 2, Style, bParentEnabled);
	}

private:
	TAttribute<FLinearColor> Fill, Outline, HoverFill, HoverOutline;
	float Corner = 10.f;
	float Thickness = 1.5f;
	const FSlateBrush* Brush = nullptr;
};

/** A setting's row: SC's full-width dark teal bar under the mouse. */
class SSpaceRow : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SSpaceRow) {}
		SLATE_DEFAULT_SLOT(FArguments, Content)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs)
	{
		ChildSlot[ InArgs._Content.Widget ];
	}

	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& Geometry, const FSlateRect& Culling, FSlateWindowElementList& Out,
		int32 Layer, const FWidgetStyle& Style, bool bParentEnabled) const override
	{
		if (IsHovered())
		{
			const FVector2f Size = Geometry.GetLocalSize();
			const float Top = 9.f, Bottom = Size.Y - 9.f;
			SpaceMenuStyle::Polygon(Out, Layer, Geometry, { { 0.f, Top }, { Size.X, Top }, { Size.X, Bottom }, { 0.f, Bottom } }, SpaceMenuStyle::RowHover);
			FSlateDrawElement::MakeLines(Out, Layer + 1, Geometry.ToPaintGeometry(), TArray<FVector2f>{ { 0.f, Bottom }, { Size.X, Bottom } },
				ESlateDrawEffect::None, SpaceMenuStyle::RowHoverEdge, true, 1.5f);
			FSlateDrawElement::MakeLines(Out, Layer + 1, Geometry.ToPaintGeometry(), TArray<FVector2f>{ { 0.f, Top }, { Size.X, Top } },
				ESlateDrawEffect::None, SpaceMenuStyle::RowHoverEdge * FLinearColor(1, 1, 1, 0.5f), true, 1.f);
		}
		return SCompoundWidget::OnPaint(Args, Geometry, Culling, Out, Layer + 2, Style, bParentEnabled);
	}
};

/** SC's bold chevron (‹ or ›), drawn, so it does not depend on a font's arrows. */
class SSpaceChevron : public SLeafWidget
{
public:
	SLATE_BEGIN_ARGS(SSpaceChevron) : _Right(true), _Color(FLinearColor::White) {}
		SLATE_ARGUMENT(bool, Right)
		SLATE_ATTRIBUTE(FLinearColor, Color)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs)
	{
		bRight = InArgs._Right;
		Color = InArgs._Color;
	}

	virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(14.0, 20.0); }

	virtual int32 OnPaint(const FPaintArgs&, const FGeometry& Geometry, const FSlateRect&, FSlateWindowElementList& Out,
		int32 Layer, const FWidgetStyle& Style, bool) const override
	{
		const float L = bRight ? 3.5f : 10.5f, R = bRight ? 10.5f : 3.5f;
		FSlateDrawElement::MakeLines(Out, Layer, Geometry.ToPaintGeometry(), TArray<FVector2f>{ { L, 2.5f }, { R, 10.f }, { L, 17.5f } },
			ESlateDrawEffect::None, Color.Get() * Style.GetColorAndOpacityTint(), true, 3.4f);
		return Layer;
	}

private:
	bool bRight = true;
	TAttribute<FLinearColor> Color;
};

/** The logo's emblem between the words: a ring with a four-pointed star, after SC's. */
class SSpaceEmblem : public SLeafWidget
{
public:
	SLATE_BEGIN_ARGS(SSpaceEmblem) {}
	SLATE_END_ARGS()

	void Construct(const FArguments&) {}

	virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(58.0, 58.0); }

	virtual int32 OnPaint(const FPaintArgs&, const FGeometry& Geometry, const FSlateRect&, FSlateWindowElementList& Out,
		int32 Layer, const FWidgetStyle& Style, bool) const override
	{
		const FVector2f Size = Geometry.GetLocalSize();
		const FVector2f C = Size * 0.5f;
		const float R = FMath::Min(Size.X, Size.Y) * 0.5f - 2.f;
		const FLinearColor Color = SpaceMenuStyle::Text * Style.GetColorAndOpacityTint();
		TArray<FVector2f> Ring;
		for (int32 I = 0; I <= 48; ++I)
		{
			const float A = 2.f * PI * I / 48.f;
			Ring.Add(C + FVector2f(FMath::Cos(A), FMath::Sin(A)) * R);
		}
		FSlateDrawElement::MakeLines(Out, Layer, Geometry.ToPaintGeometry(), Ring, ESlateDrawEffect::None, Color, true, 2.f);
		TArray<FVector2f> Inner;
		for (int32 I = 0; I <= 48; ++I)
		{
			const float A = 2.f * PI * I / 48.f;
			Inner.Add(C + FVector2f(FMath::Cos(A), FMath::Sin(A)) * R * 0.78f);
		}
		FSlateDrawElement::MakeLines(Out, Layer, Geometry.ToPaintGeometry(), Inner, ESlateDrawEffect::None, Color, true, 1.2f);
		// The star: four long points and four short ones, as two filled quads per point pair.
		const float Long = R * 0.66f, Short = R * 0.16f;
		for (int32 I = 0; I < 4; ++I)
		{
			const float A = PI * 0.5f * I - PI * 0.5f;
			const FVector2f Tip = C + FVector2f(FMath::Cos(A), FMath::Sin(A)) * Long;
			const FVector2f Left = C + FVector2f(FMath::Cos(A - PI * 0.25f), FMath::Sin(A - PI * 0.25f)) * Short;
			const FVector2f Right = C + FVector2f(FMath::Cos(A + PI * 0.25f), FMath::Sin(A + PI * 0.25f)) * Short;
			SpaceMenuStyle::Polygon(Out, Layer + 1, Geometry, { C, Left, Tip, Right }, Color);
		}
		return Layer + 1;
	}
};

/** Darkens the left of the title screen's live background towards the cards, fading out to the right. */
class SSpaceVignette : public SLeafWidget
{
public:
	SLATE_BEGIN_ARGS(SSpaceVignette) {}
	SLATE_END_ARGS()

	void Construct(const FArguments&) {}

	virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(1.0, 1.0); }

	virtual int32 OnPaint(const FPaintArgs&, const FGeometry& Geometry, const FSlateRect&, FSlateWindowElementList& Out,
		int32 Layer, const FWidgetStyle&, bool) const override
	{
		const float W = Geometry.GetLocalSize().X;
		TArray<FSlateGradientStop> Stops;
		// White text and outlines stand on dark ground in SC (its nebula is dark); ours is a live scene, maybe a bright sky.
		Stops.Add(FSlateGradientStop(FVector2f(0.f, 0.f), FLinearColor(0.f, 0.f, 0.f, 0.80f)));
		Stops.Add(FSlateGradientStop(FVector2f(W * 0.34f, 0.f), FLinearColor(0.f, 0.f, 0.f, 0.62f)));
		Stops.Add(FSlateGradientStop(FVector2f(W * 0.66f, 0.f), FLinearColor(0.f, 0.f, 0.f, 0.f)));
		FSlateDrawElement::MakeGradient(Out, Layer, Geometry.ToPaintGeometry(), MoveTemp(Stops), Orient_Vertical);
		return Layer;
	}
};

/** A horizontal dark band fading out up and down: behind text laid over a picture. */
class SSpaceBand : public SLeafWidget
{
public:
	SLATE_BEGIN_ARGS(SSpaceBand) {}
	SLATE_END_ARGS()

	void Construct(const FArguments&) {}

	virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(1.0, 1.0); }

	virtual int32 OnPaint(const FPaintArgs&, const FGeometry& Geometry, const FSlateRect&, FSlateWindowElementList& Out,
		int32 Layer, const FWidgetStyle&, bool) const override
	{
		const float H = Geometry.GetLocalSize().Y;
		TArray<FSlateGradientStop> Stops;
		Stops.Add(FSlateGradientStop(FVector2f(0.f, 0.f), FLinearColor(0.f, 0.f, 0.f, 0.f)));
		Stops.Add(FSlateGradientStop(FVector2f(0.f, H * 0.5f), FLinearColor(0.f, 0.f, 0.f, 0.55f)));
		Stops.Add(FSlateGradientStop(FVector2f(0.f, H), FLinearColor(0.f, 0.f, 0.f, 0.f)));
		FSlateDrawElement::MakeGradient(Out, Layer, Geometry.ToPaintGeometry(), MoveTemp(Stops), Orient_Horizontal);
		return Layer;
	}
};

// -------------------------------------------------------------------------------------------

void SSpaceMenu::Construct(const FArguments& InArgs)
{
	Owner = InArgs._Owner;
	bTitleScreen = InArgs._TitleScreen;

	UKismetSystemLibrary::GetSupportedFullscreenResolutions(Resolutions);
	if (const USpaceUserSettings* Settings = USpaceUserSettings::Get())
	{
		Resolutions.AddUnique(Settings->GetDesktopResolution());
	}
	Resolutions.RemoveAll([](const FIntPoint& R) { return R.X < 1024 || R.Y < 600; });
	if (Resolutions.Num() == 0)
	{
		Resolutions.Add(FIntPoint(1920, 1080));
	}
	Resolutions.Sort([](const FIntPoint& A, const FIntPoint& B) { return A.X * A.Y < B.X * B.Y; });
	LoadDraft();

	// The play card's picture, read from its file at runtime (staged raw like the fonts: DirectoriesToAlwaysStageAsUFS).
	const FString CardPath = FPaths::ProjectContentDir() / TEXT("UI/Menu/card_play.jpg");
	if (FPaths::FileExists(CardPath))
	{
		if (UTexture2D* Texture = FImageUtils::ImportFileAsTexture2D(CardPath))
		{
			CardTexture.Reset(Texture);
			CardBrush = MakeShared<FSlateBrush>();
			CardBrush->SetResourceObject(Texture);
			CardBrush->ImageSize = FVector2D(Texture->GetSizeX(), Texture->GetSizeY());
		}
	}

	ChildSlot
	[
		SAssignNew(Switcher, SWidgetSwitcher)
		+ SWidgetSwitcher::Slot() [ BuildTitlePage() ]
		+ SWidgetSwitcher::Slot() [ BuildPausePage() ]
		+ SWidgetSwitcher::Slot() [ BuildSettingsPage() ]
		+ SWidgetSwitcher::Slot() [ BuildLoadingPage() ]
	];
	ShowPage(bTitleScreen ? ESpaceMenuPage::Main : ESpaceMenuPage::Pause);
}

void SSpaceMenu::ShowPage(ESpaceMenuPage Page)
{
	if (Page == ESpaceMenuPage::Settings)
	{
		LoadDraft();
	}
	CurrentPage = Page;
	Switcher->SetActiveWidgetIndex(static_cast<int32>(Page));
}

void SSpaceMenu::ScrollTabToEnd()
{
	if (TabScrolls.IsValidIndex(int32(CurrentTab)) && TabScrolls[int32(CurrentTab)].IsValid())
	{
		TabScrolls[int32(CurrentTab)]->ScrollToEnd();
	}
}

void SSpaceMenu::ShowTab(ESpaceSettingsTab Tab)
{
	CurrentTab = Tab;
	if (TabSwitcher.IsValid())
	{
		TabSwitcher->SetActiveWidgetIndex(static_cast<int32>(Tab));
	}
}

FReply SSpaceMenu::OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();
	if (Key == EKeys::Escape || Key == EKeys::F10 || Key == EKeys::Gamepad_Special_Right || Key == EKeys::Gamepad_FaceButton_Right)
	{
		if (CurrentPage == ESpaceMenuPage::Settings)
		{
			CloseSettings();
			return FReply::Handled();
		}
		if (CurrentPage == ESpaceMenuPage::Pause)
		{
			if (ASpacePlayerController* Controller = Owner.Get())
			{
				Controller->ResumeGame();
			}
			return FReply::Handled();
		}
	}
	return SCompoundWidget::OnKeyDown(MyGeometry, InKeyEvent);
}

// -------------------------------------------------------------------------------------------
// Pages
// -------------------------------------------------------------------------------------------

TSharedRef<SWidget> SSpaceMenu::BuildTitlePage()
{
	using namespace SpaceMenuStyle;
	// The logo after SC's: wide, widely spaced capitals with the emblem between the words and a thin line over and
	// under the lettering.
	auto Rule = []() { return SNew(SBox).HeightOverride(2.f)[ SNew(SImage).Image(White()).ColorAndOpacity(Text) ]; };
	auto Word = [](const FText& Value)
	{
		return SNew(STextBlock).Text(Value).Font(Font(true, 46.f, 330)).ColorAndOpacity(Text);
	};
	const TSharedRef<SWidget> Logo = SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot().AutoHeight()[ Rule() ]
			+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 3.f)[ Word(LOCTEXT("LogoGame", "GAME")) ]
			+ SVerticalBox::Slot().AutoHeight()[ Rule() ]
		]
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(10.f, 0.f)[ SNew(SSpaceEmblem) ]
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot().AutoHeight()[ Rule() ]
			+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 3.f)[ Word(LOCTEXT("LogoSpace", "SPACE")) ]
			+ SVerticalBox::Slot().AutoHeight()[ Rule() ]
		];

	return SNew(SOverlay)
		+ SOverlay::Slot()[ SNew(SSpaceVignette) ]
		+ SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Fill).Padding(FMargin(80.f, 40.f, 0.f, 51.f))
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot().AutoHeight()[ Logo ]
			+ SVerticalBox::Slot().AutoHeight().Padding(FMargin(0.f, 30.f, 0.f, 12.f))
			[
				SNew(STextBlock)
				.Text(LOCTEXT("Subtitle", "Vyber si jednu z následujících možností hry Gamespace."))
				.Font(Font(false, 16.f))
				.ColorAndOpacity(Text)
			]
			+ SVerticalBox::Slot().AutoHeight()[ BuildPlayCard() ]
			+ SVerticalBox::Slot().FillHeight(1.f)[ SNew(SSpacer) ]
			+ SVerticalBox::Slot().AutoHeight()
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().AutoWidth()
				[
					MakeButton(LOCTEXT("Quit", "Ukončit hru"), [this]()
					{
						if (ASpacePlayerController* Controller = Owner.Get())
						{
							Controller->QuitGame();
						}
					}, 200.f)
				]
				+ SHorizontalBox::Slot().AutoWidth().Padding(FMargin(15.f, 0.f, 0.f, 0.f))
				[
					MakeButton(LOCTEXT("Settings", "Nastavení"), [this]() { ShowPage(ESpaceMenuPage::Settings); }, 200.f)
				]
			]
		];
}

TSharedRef<SWidget> SSpaceMenu::BuildPlayCard()
{
	using namespace SpaceMenuStyle;
	auto Play = [this]()
	{
		Clicked();
		ShowPage(ESpaceMenuPage::Loading);
		if (ASpacePlayerController* Controller = Owner.Get())
		{
			Controller->StartGame();
		}
		return FReply::Handled();
	};
	// The card is a flat button; its hover shows SC's description strip and brightens the outline.
	TSharedRef<TWeakPtr<SButton>> Card = MakeShared<TWeakPtr<SButton>>();
	auto CardHovered = [Card]() { const TSharedPtr<SButton> Button = Card->Pin(); return Button.IsValid() && Button->IsHovered(); };

	TSharedRef<SButton> Button = SNew(SButton)
		.ButtonStyle(&FlatButton())
		.OnHovered_Lambda([this]() { Hovered(); })
		.OnClicked_Lambda(Play)
		[
			SNew(SBox).WidthOverride(649.f).HeightOverride(498.f)
			[
				SNew(SOverlay)
				+ SOverlay::Slot()
				[
					SNew(SSpaceBox)
					.Brush(CardBrush.Get())
					.Fill(CardBrush.IsValid() ? FLinearColor::Transparent : FieldFill)
					.Outline(Outline)
					.HoverOutline(OutlineHover)
					.Corner(18.f)
					.Thickness(1.6f)
				]
				// The version tab in the top-left corner.
				+ SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Top).Padding(2.f)
				[
					SNew(SSpaceBox).Fill(FLinearColor(0.f, 0.f, 0.f, 0.62f)).Corner(9.f).Padding(FMargin(11.f, 4.f, 20.f, 5.f))
					[
						SNew(STextBlock).Text(LOCTEXT("Version", "Prototyp 0.4: Veyra")).Font(Font(false, 10.5f)).ColorAndOpacity(Text)
					]
				]
				// A soft dark band behind the title, so it reads over a bright sky (critic 4. 10. 2026).
				+ SOverlay::Slot().HAlign(HAlign_Fill).VAlign(VAlign_Center).Padding(FMargin(2.f, 0.f))
				[
					SNew(SBox).HeightOverride(150.f)[ SNew(SSpaceBand) ]
				]
				+ SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)
					[
						SNew(STextBlock).Text(LOCTEXT("JoinUniverse", "VSTOUPIT DO VESMÍRU")).Font(Font(true, 19.f, 40)).ColorAndOpacity(Text)
						.ShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.6f)).ShadowOffset(FVector2D(1.0, 1.0))
					]
					+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(FMargin(0.f, 6.f, 0.f, 0.f))
					[
						SNew(SButton)
						.ButtonStyle(&FlatButton())
						.OnHovered_Lambda([this]() { Hovered(); })
						.OnClicked_Lambda(Play)
						[
							SNew(SSpaceBox).Fill(PlayFill).HoverFill(PlayHover).Corner(0.f).Padding(FMargin(14.f, 3.f, 14.f, 4.f))
							[
								SNew(STextBlock).Text(LOCTEXT("PlayGame", "HRÁT GAMESPACE")).Font(Font(true, 13.f, 30)).ColorAndOpacity(PlayText)
							]
						]
					]
				]
				// SC's one-line description along the bottom while the card is under the mouse.
				+ SOverlay::Slot().HAlign(HAlign_Fill).VAlign(VAlign_Bottom).Padding(FMargin(2.f, 0.f, 20.f, 2.f))
				[
					SNew(SBox)
					.Visibility_Lambda([CardHovered]() { return CardHovered() ? EVisibility::HitTestInvisible : EVisibility::Collapsed; })
					[
						SNew(SSpaceBox).Fill(FLinearColor(0.f, 0.f, 0.f, 0.68f)).Corner(0.f).Padding(FMargin(12.f, 7.f))
						[
							SNew(STextBlock)
							.Text(LOCTEXT("PlayDescription", "Planeta Veyra a loď Wayfarer: let, přistání a výstup na povrch."))
							.Font(Font(false, 12.f))
							.ColorAndOpacity(Text)
						]
					]
				]
			]
		];
	*Card = Button;
	return Button;
}

TSharedRef<SWidget> SSpaceMenu::BuildPausePage()
{
	using namespace SpaceMenuStyle;
	TSharedRef<SVerticalBox> Column = SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight().Padding(FMargin(0.f, 0.f, 0.f, 26.f))
		[
			SNew(STextBlock).Text(LOCTEXT("Paused", "PAUZA")).Font(Font(true, 23.f, 60)).ColorAndOpacity(Text)
		];
	auto Add = [&Column](const TSharedRef<SWidget>& Widget) { Column->AddSlot().AutoHeight().Padding(0.f, 6.f)[ Widget ]; };
	Add(MakeButton(LOCTEXT("Resume", "Pokračovat"), [this]()
	{
		if (ASpacePlayerController* Controller = Owner.Get())
		{
			Controller->ResumeGame();
		}
	}, 330.f));
	// Walk the Steadfast interior, or back (the same as I). Only where there is one.
	if (Owner.IsValid() && Owner->HasInterior())
	{
		Add(MakeButton(Owner->IsWalkingInterior() ? LOCTEXT("InteriorBack", "Zpět z interiéru") : LOCTEXT("Interior", "Prohlídka interiéru"), [this]()
		{
			if (ASpacePlayerController* Controller = Owner.Get())
			{
				Controller->ResumeGame();
				Controller->ToggleInterior();
			}
		}, 330.f));
	}
	Add(MakeButton(LOCTEXT("PauseSettings", "Nastavení"), [this]() { ShowPage(ESpaceMenuPage::Settings); }, 330.f));
	Add(MakeButton(LOCTEXT("MainMenu", "Hlavní menu"), [this]()
	{
		ShowPage(ESpaceMenuPage::Loading);
		if (ASpacePlayerController* Controller = Owner.Get())
		{
			Controller->GoToMainMenu();
		}
	}, 330.f));
	Add(MakeButton(LOCTEXT("PauseQuit", "Ukončit hru"), [this]()
	{
		if (ASpacePlayerController* Controller = Owner.Get())
		{
			Controller->QuitGame();
		}
	}, 330.f));

	return SNew(SOverlay)
		+ SOverlay::Slot()[ SNew(SImage).Image(White()).ColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.55f)) ]
		+ SOverlay::Slot()[ SNew(SSpaceVignette) ]
		+ SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Center).Padding(FMargin(80.f, 0.f))[ Column ];
}

TSharedRef<SWidget> SSpaceMenu::BuildLoadingPage()
{
	using namespace SpaceMenuStyle;
	return SNew(SOverlay)
		+ SOverlay::Slot()[ SNew(SImage).Image(White()).ColorAndOpacity(Page) ]
		+ SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Bottom).Padding(FMargin(0.f, 0.f, 80.f, 60.f))
		[
			SNew(STextBlock).Text(LOCTEXT("Loading", "NAČÍTÁNÍ…")).Font(Font(true, 19.f, 120)).ColorAndOpacity(Text)
		];
}

TSharedRef<SWidget> SSpaceMenu::BuildSettingsPage()
{
	using namespace SpaceMenuStyle;
	TSharedRef<SHorizontalBox> Tabs = SNew(SHorizontalBox);
	const FText TabNames[] = { LOCTEXT("TabGame", "HRA"), LOCTEXT("TabGraphics", "GRAFIKA"), LOCTEXT("TabAudio", "ZVUK"),
		LOCTEXT("TabControls", "OVLÁDÁNÍ") };
	for (int32 Index = 0; Index < int32(ESpaceSettingsTab::Count); ++Index)
	{
		Tabs->AddSlot().FillWidth(1.f).Padding(FMargin(Index == 0 ? 0.f : 10.f, 0.f, Index + 1 == int32(ESpaceSettingsTab::Count) ? 0.f : 10.f, 0.f))
		[
			MakeTab(ESpaceSettingsTab(Index), TabNames[Index])
		];
	}

	SAssignNew(TabSwitcher, SWidgetSwitcher);
	for (int32 Index = 0; Index < int32(ESpaceSettingsTab::Count); ++Index)
	{
		TSharedPtr<SScrollBox> Scroll;
		TabSwitcher->AddSlot()
		[
			SAssignNew(Scroll, SScrollBox)
			.ScrollBarStyle(&ScrollBar())
			.ScrollBarThickness(FVector2D(4.0, 4.0))
			.ScrollBarPadding(FMargin(0.f, 2.f, 2.f, 2.f))
			+ SScrollBox::Slot().Padding(FMargin(0.f, 4.f, 10.f, 4.f))[ BuildTabRows(ESpaceSettingsTab(Index)) ]
		];
		TabScrolls.Add(Scroll);
	}
	TabSwitcher->SetActiveWidgetIndex(static_cast<int32>(CurrentTab));

	// SC: an opaque black page, the title top left, the tabs across the full width, one outlined list, BACK and RESET.
	return SNew(SOverlay)
		+ SOverlay::Slot()[ SNew(SImage).Image(White()).ColorAndOpacity(Page) ]
		+ SOverlay::Slot().Padding(FMargin(39.f, 0.f, 39.f, 39.f))
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot().AutoHeight().Padding(FMargin(3.f, 36.f, 0.f, 0.f))
			[
				SNew(STextBlock).Text(LOCTEXT("SettingsTitle", "NASTAVENÍ")).Font(Font(false, 23.f, 20)).ColorAndOpacity(Text)
			]
			+ SVerticalBox::Slot().AutoHeight().Padding(FMargin(0.f, 34.f, 0.f, 0.f))
			[
				SNew(SBox).HeightOverride(51.f)[ Tabs ]
			]
			+ SVerticalBox::Slot().FillHeight(1.f).Padding(FMargin(0.f, 38.f, 0.f, 0.f))
			[
				SNew(SSpaceBox).Outline(OutlineDim).Corner(0.f).Thickness(1.5f).Padding(FMargin(2.f))
				[
					TabSwitcher.ToSharedRef()
				]
			]
			+ SVerticalBox::Slot().AutoHeight().Padding(FMargin(0.f, 40.f, 0.f, 0.f))
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().AutoWidth()[ MakeButton(LOCTEXT("Back", "Zpět"), [this]() { CloseSettings(); }, 132.f, false) ]
				+ SHorizontalBox::Slot().AutoWidth().Padding(FMargin(20.f, 0.f, 0.f, 0.f))
				[
					MakeButton(LOCTEXT("Reset", "Výchozí"), [this]() { ResetTab(); }, 292.f, false)
				]
			]
		];
}

TSharedRef<SWidget> SSpaceMenu::BuildTabRows(ESpaceSettingsTab Tab)
{
	using namespace SpaceMenuStyle;
	TSharedRef<SVerticalBox> Rows = SNew(SVerticalBox);
	auto Add = [&Rows](const TSharedRef<SWidget>& Row) { Rows->AddSlot().AutoHeight()[ Row ]; };
	auto Percent = [](float Value) { return FText::FromString(FString::Printf(TEXT("%d"), FMath::RoundToInt32(Value * 100.f))); };

	switch (Tab)
	{
	case ESpaceSettingsTab::Game:
		Add(MakeSelectorRow(LOCTEXT("StartFlight", "Let – výchozí řízení"),
			[this]() { return Draft.bStartDecoupled ? 1 : 0; }, [this](int32 I) { Draft.bStartDecoupled = I != 0; }, []() { return 2; },
			[](int32 I) { return I ? LOCTEXT("Decoupled", "Decoupled") : LOCTEXT("Coupled", "Coupled"); }));
		Add(MakeToggleRow(LOCTEXT("DefaultGSafe", "Let – G-Safe"), &Draft.bGSafe));
		Add(MakeToggleRow(LOCTEXT("DefaultComStab", "Let – ComStab"), &Draft.bComStab));
		Add(MakeToggleRow(LOCTEXT("VJoy", "Let – virtuální joystick (VJoy)"), &Draft.bVirtualJoystick));
		Add(MakeSliderRow(LOCTEXT("VJoyDeadzone", "Let – mrtvá zóna VJoy"), &Draft.VJoyDeadzone, 0.f, 0.3f,
			[](float V) { return FText::FromString(FString::Printf(TEXT("%.1f"), V * 100.f)); }));
		Add(MakeDropdownRow(LOCTEXT("FlightPath", "HUD – značka dráhy letu"),
			[this]() { return Draft.bFlightPathMarker ? 0 : 1; }, [this](int32 I) { Draft.bFlightPathMarker = I == 0; }, []() { return 2; },
			[](int32 I) { return I == 0 ? LOCTEXT("Always", "Vždy") : LOCTEXT("Never", "Nikdy"); }));
		Add(MakeSelectorRow(LOCTEXT("Hud", "HUD – režim (klávesa H)"),
			[this]() { return Draft.HudMode; }, [this](int32 I) { Draft.HudMode = I; }, []() { return 4; },
			[](int32 I)
			{
				return I == 0 ? LOCTEXT("HudOff", "Skrytý") : I == 1 ? LOCTEXT("HudFlight", "Jen letový HUD")
					: I == 2 ? LOCTEXT("HudCompact", "S textem") : LOCTEXT("HudFull", "S plným textem");
			}));
		Add(MakeSliderRow(LOCTEXT("CameraShake", "Kamera – třes kamery"), &Draft.CameraShake, 0.f, 2.f,
			[](float V) { return FText::FromString(FString::Printf(TEXT("%.2f"), V)); }));
		Add(MakeToggleRow(LOCTEXT("ShowFps", "Rozhraní – zobrazit FPS"), &Draft.bShowFps));
		break;

	case ESpaceSettingsTab::Graphics:
		Add(MakeDropdownRow(LOCTEXT("Resolution", "Rozlišení"),
			[this]() { return Draft.Resolution; }, [this](int32 I) { Draft.Resolution = I; }, [this]() { return Resolutions.Num(); },
			[this](int32 I)
			{
				const FIntPoint R = Resolutions.IsValidIndex(I) ? Resolutions[I] : FIntPoint::ZeroValue;
				return FText::FromString(FString::Printf(TEXT("%d X %d"), R.X, R.Y));
			}));
		Add(MakeDropdownRow(LOCTEXT("WindowMode", "Režim zobrazení"),
			[this]() { return Draft.WindowMode; }, [this](int32 I) { Draft.WindowMode = I; }, []() { return 3; },
			[](int32 I)
			{
				return I == 0 ? LOCTEXT("Borderless", "Celá obrazovka bez rámečku") : I == 1 ? LOCTEXT("Exclusive", "Celá obrazovka")
					: LOCTEXT("Windowed", "V okně");
			}));
		Add(MakeToggleRow(LOCTEXT("VSync", "Vertikální synchronizace"), &Draft.bVSync));
		Add(MakeDropdownRow(LOCTEXT("FrameLimit", "Limit snímků"),
			[this]() { return Draft.FrameLimit; }, [this](int32 I) { Draft.FrameLimit = I; }, []() { return int32(UE_ARRAY_COUNT(FrameLimits)); },
			[](int32 I)
			{
				return FrameLimits[I] == 0 ? LOCTEXT("NoLimit", "Bez limitu") : FText::FromString(FString::Printf(TEXT("%d FPS"), FrameLimits[I]));
			}));
		Add(MakeDropdownRow(LOCTEXT("Upscaling", "Upscaling"),
			[this]()
			{
				int32 Best = 0;
				for (int32 I = 1; I < UE_ARRAY_COUNT(UpscaleScales); ++I)
				{
					Best = FMath::Abs(UpscaleScales[I] - Draft.ResolutionScale) < FMath::Abs(UpscaleScales[Best] - Draft.ResolutionScale) ? I : Best;
				}
				return Best;
			},
			[this](int32 I) { Draft.ResolutionScale = UpscaleScales[FMath::Clamp(I, 0, int32(UE_ARRAY_COUNT(UpscaleScales)) - 1)]; },
			[]() { return int32(UE_ARRAY_COUNT(UpscaleScales)); },
			[](int32 I)
			{
				static const FText Names[] = { LOCTEXT("UpNative", "Nativní (100 %)"), LOCTEXT("UpUltra", "Ultra kvalita (77 %)"),
					LOCTEXT("UpHigh", "Vysoká kvalita (75 %)"), LOCTEXT("UpQuality", "Kvalita (67 %)"), LOCTEXT("UpBalanced", "Vyvážené (58 %)"),
					LOCTEXT("UpPerformance", "Výkon (50 %)") };
				return Names[FMath::Clamp(I, 0, 5)];
			}));
		Add(MakeSelectorRow(LOCTEXT("UpscalingTechnique", "Technika upscalingu"),
			[]() { return 0; }, [](int32) {}, []() { return 1; }, [](int32) { return LOCTEXT("Tsr", "TSR"); }));
		Add(MakeDropdownRow(LOCTEXT("Quality", "Celková kvalita"),
			[this]() { return AreGroupsCustom() ? 5 : Draft.Quality; },
			[this](int32 I) { Draft.Quality = I; SetGroupsFromPreset(I); }, []() { return 5; },
			[](int32 I) { return I > 4 ? LOCTEXT("Custom", "Vlastní") : QualityName(I); }));
		{
			const FText GroupLabels[] = { LOCTEXT("GroupView", "Dohlednost objektů"), LOCTEXT("GroupShadow", "Stíny"),
				LOCTEXT("GroupGI", "Globální osvětlení"), LOCTEXT("GroupReflection", "Odrazy"), LOCTEXT("GroupTexture", "Textury"),
				LOCTEXT("GroupEffects", "Efekty"), LOCTEXT("GroupPost", "Postprocesy"), LOCTEXT("GroupFoliage", "Vegetace a kameny"),
				LOCTEXT("GroupShading", "Kvalita shaderů") };
			for (int32 Group = 0; Group < 9; ++Group)
			{
				// Global illumination stops at High: it halves the frame rate above (USpaceUserSettings).
				const int32 Levels = Group == 2 ? USpaceUserSettings::MaxGlobalIlluminationQuality + 1 : 5;
				Add(MakeDropdownRow(GroupLabels[Group],
					[this, Group]() { return Draft.Groups[Group]; }, [this, Group](int32 I) { Draft.Groups[Group] = I; },
					[Levels]() { return Levels; }, [](int32 I) { return QualityName(I); }));
			}
		}
		Add(MakeSliderRow(LOCTEXT("Fov", "Zorné pole (kokpit a pěšky)"), &Draft.FieldOfView, 70.f, 110.f,
			[](float V) { return FText::FromString(FString::Printf(TEXT("%d"), FMath::RoundToInt32(V))); }));
		Add(MakeSliderRow(LOCTEXT("Gamma", "Gama"), &Draft.Gamma, 0.f, 100.f,
			[](float V) { return FText::FromString(FString::Printf(TEXT("%d"), FMath::RoundToInt32(V))); }));
		Add(MakeToggleRow(LOCTEXT("MotionBlur", "Rozmazání pohybem"), &Draft.bMotionBlur));
		Add(MakeSliderRow(LOCTEXT("Sharpen", "Ostření"), &Draft.Sharpen, 0.f, 1.f,
			[](float V) { return FText::FromString(FString::Printf(TEXT("%d"), FMath::RoundToInt32(V * 100.f))); }));
		Add(MakeToggleRow(LOCTEXT("Fringe", "Chromatická aberace"), &Draft.bChromaticAberration));
		Add(MakeToggleRow(LOCTEXT("Grain", "Zrnitost obrazu"), &Draft.bFilmGrain));
		break;

	case ESpaceSettingsTab::Audio:
		Add(MakeSliderRow(LOCTEXT("MasterVolume", "Celková hlasitost"), &Draft.MasterVolume, 0.f, 1.f, Percent, true));
		Add(MakeSliderRow(LOCTEXT("EffectsVolume", "Hlasitost efektů a motorů"), &Draft.EffectsVolume, 0.f, 1.f, Percent, true));
		Add(MakeSliderRow(LOCTEXT("MusicVolume", "Hlasitost hudby a ambientu"), &Draft.MusicVolume, 0.f, 1.f, Percent, true));
		Add(MakeToggleRow(LOCTEXT("BackgroundAudio", "Zvuk, když hra není v popředí"), &Draft.bAudioInBackground));
		break;

	case ESpaceSettingsTab::Controls:
		Add(MakeHeading(LOCTEXT("InversionHeading", "Inverze")));
		Add(MakeToggleRow(LOCTEXT("InvertPitch", "      Let – klopení (myš nahoru = nos dolů)"), &Draft.bInvertPitch));
		Add(MakeToggleRow(LOCTEXT("InvertFreeLook", "      Volné rozhlížení – sklon"), &Draft.bInvertFreeLook));
		Add(MakeToggleRow(LOCTEXT("InvertWalk", "      Pěšky – sklon"), &Draft.bInvertWalk));
		Add(MakeHeading(LOCTEXT("SensitivityHeading", "Myš")));
		Add(MakeSliderRow(LOCTEXT("Sensitivity", "      Citlivost myši"), &Draft.MouseSensitivity, 0.25f, 3.f,
			[](float V) { return FText::FromString(FString::Printf(TEXT("%.2f"), V)); }));
		break;

	default:
		break;
	}
	return Rows;
}

// -------------------------------------------------------------------------------------------
// Building blocks
// -------------------------------------------------------------------------------------------

TSharedRef<SWidget> SSpaceMenu::MakeButton(const FText& Label, TFunction<void()> OnClick, float Width, bool bFilled)
{
	using namespace SpaceMenuStyle;
	return SNew(SButton)
		.ButtonStyle(&FlatButton())
		.OnHovered_Lambda([this]() { Hovered(); })
		.OnClicked_Lambda([this, OnClick]()
		{
			Clicked();
			OnClick();
			return FReply::Handled();
		})
		[
			SNew(SBox).WidthOverride(Width).HeightOverride(bFilled ? 43.f : 51.f)
			[
				SNew(SSpaceBox)
				.Fill(bFilled ? ButtonFill : FLinearColor::Transparent)
				.HoverFill(bFilled ? ButtonHover : TabHover)
				.Outline(Outline)
				.HoverOutline(OutlineHover)
				.Corner(13.f)
				.Padding(FMargin(16.f, 0.f))
				[
					SNew(SBox).VAlign(VAlign_Center).HAlign(HAlign_Left)
					[
						SNew(STextBlock).Text(Label.ToUpper()).Font(Font(false, 13.f, 20)).ColorAndOpacity(Text)
					]
				]
			]
		];
}

TSharedRef<SWidget> SSpaceMenu::MakeTab(ESpaceSettingsTab Tab, const FText& Label)
{
	using namespace SpaceMenuStyle;
	auto Active = [this, Tab]() { return CurrentTab == Tab; };
	return SNew(SButton)
		.ButtonStyle(&FlatButton())
		.OnHovered_Lambda([this]() { Hovered(); })
		.OnClicked_Lambda([this, Tab]()
		{
			Clicked();
			ShowTab(Tab);
			return FReply::Handled();
		})
		[
			SNew(SSpaceBox)
			.Fill_Lambda([Active]() { return Active() ? TabActive : FLinearColor::Transparent; })
			.HoverFill_Lambda([Active]() { return Active() ? TabActive : TabHover; })
			.Outline(Outline)
			.HoverOutline(OutlineHover)
			.Corner(13.f)
			.Padding(FMargin(17.f, 0.f))
			[
				SNew(SBox).VAlign(VAlign_Center).HAlign(HAlign_Left)
				[
					SNew(STextBlock).Text(Label).Font(Font(false, 12.5f, 20)).ColorAndOpacity(Text)
				]
			]
		];
}

TSharedRef<SWidget> SSpaceMenu::MakeRow(const FText& Label, const TSharedRef<SWidget>& Control, const TSharedPtr<SWidget>& After)
{
	using namespace SpaceMenuStyle;
	return SNew(SSpaceRow)
		[
			SNew(SBox).HeightOverride(63.f)
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
				[
					SNew(SBox).WidthOverride(581.f).Padding(FMargin(55.f, 0.f, 12.f, 0.f))
					[
						SNew(STextBlock).Text(Label).Font(Font(false, 13.f)).ColorAndOpacity(Text)
					]
				]
				+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
				[
					SNew(SBox).WidthOverride(402.f)[ Control ]
				]
				// A slider's value, right of it as in SC.
				+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(FMargin(14.f, 0.f, 0.f, 0.f))
				[
					After.IsValid() ? After.ToSharedRef() : SNullWidget::NullWidget
				]
				+ SHorizontalBox::Slot().FillWidth(1.f)[ SNew(SSpacer) ]
			]
		];
}

TSharedRef<SWidget> SSpaceMenu::MakeSelectorRow(const FText& Label, TFunction<int32()> GetIndex, TFunction<void(int32)> SetIndex,
	TFunction<int32()> Count, TFunction<FText(int32)> Describe)
{
	using namespace SpaceMenuStyle;
	// No wrapping: the arrow towards the end of the list is dimmed (SC GAME SETTINGS: "Yes" has its right arrow dim,
	// "No" its left one; No comes first).
	auto CanStep = [GetIndex, Count](int32 Direction)
	{
		const int32 Next = GetIndex() + Direction;
		return Next >= 0 && Next < Count();
	};
	auto Arrow = [this, GetIndex, SetIndex, CanStep](bool bRight) -> TSharedRef<SWidget>
	{
		const int32 Direction = bRight ? 1 : -1;
		return SNew(SButton)
			.ButtonStyle(&FlatButton())
			.ContentPadding(FMargin(12.f, 6.f))
			.OnHovered_Lambda([this]() { Hovered(); })
			.OnClicked_Lambda([this, GetIndex, SetIndex, CanStep, Direction]()
			{
				if (CanStep(Direction))
				{
					SetIndex(GetIndex() + Direction);
					Commit();
					Clicked();
				}
				return FReply::Handled();
			})
			[
				SNew(SSpaceChevron).Right(bRight)
				.Color_Lambda([CanStep, Direction]() { return CanStep(Direction) ? Text : FLinearColor(Text.R, Text.G, Text.B, 0.18f); })
			];
	};
	return MakeRow(Label,
		SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[ Arrow(false) ]
		+ SHorizontalBox::Slot().FillWidth(1.f).VAlign(VAlign_Center).HAlign(HAlign_Center)
		[
			SNew(STextBlock).Text_Lambda([GetIndex, Describe]() { return Describe(GetIndex()); }).Font(Font(false, 13.f)).ColorAndOpacity(Text)
		]
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[ Arrow(true) ]);
}

TSharedRef<SWidget> SSpaceMenu::MakeHeading(const FText& Label)
{
	using namespace SpaceMenuStyle;
	// SC's tree node in CONTROLS: a small outlined box with a minus, the title beside it.
	return SNew(SBox).HeightOverride(63.f).Padding(FMargin(55.f, 0.f, 0.f, 0.f)).VAlign(VAlign_Center)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				SNew(SBox).WidthOverride(16.f).HeightOverride(16.f)
				[
					SNew(SSpaceBox).Outline(Outline).Corner(0.f).Thickness(1.f)
					[
						SNew(SBox).HAlign(HAlign_Center).VAlign(VAlign_Center)
						[
							SNew(SBox).WidthOverride(8.f).HeightOverride(1.6f)[ SNew(SImage).Image(White()).ColorAndOpacity(Text) ]
						]
					]
				]
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(FMargin(12.f, 0.f, 0.f, 0.f))
			[
				SNew(STextBlock).Text(Label).Font(Font(true, 13.f)).ColorAndOpacity(Text)
			]
		];
}

TSharedRef<SWidget> SSpaceMenu::MakeToggleRow(const FText& Label, bool* Value)
{
	return MakeSelectorRow(Label, [Value]() { return *Value ? 1 : 0; }, [Value](int32 I) { *Value = I != 0; }, []() { return 2; },
		[](int32 I) { return I ? LOCTEXT("ToggleOn", "Ano") : LOCTEXT("ToggleOff", "Ne"); });
}

TSharedRef<SWidget> SSpaceMenu::MakeDropdownRow(const FText& Label, TFunction<int32()> GetIndex, TFunction<void(int32)> SetIndex,
	TFunction<int32()> Count, TFunction<FText(int32)> Describe)
{
	using namespace SpaceMenuStyle;
	TSharedRef<TWeakPtr<SMenuAnchor>> Anchor = MakeShared<TWeakPtr<SMenuAnchor>>();
	auto Field = [](const TSharedRef<SWidget>& Content, bool bHoverable)
	{
		return SNew(SBox).HeightOverride(30.f)
			[
				SNew(SSpaceBox)
				.Fill(FieldFill)
				.HoverFill(bHoverable ? RowHover : FLinearColor(0, 0, 0, -1))
				.Outline(FieldEdge)
				.HoverOutline(bHoverable ? RowHoverEdge : FLinearColor(0, 0, 0, -1))
				.Corner(0.f)
				.Thickness(1.f)
				[
					Content
				]
			];
	};
	TSharedRef<SMenuAnchor> Menu = SNew(SMenuAnchor)
		.Placement(MenuPlacement_BelowAnchor)
		.Method(EPopupMethod::UseCurrentWindow)
		.OnGetMenuContent_Lambda([this, Anchor, GetIndex, SetIndex, Count, Describe, Field]() -> TSharedRef<SWidget>
		{
			TSharedRef<SVerticalBox> List = SNew(SVerticalBox);
			for (int32 Index = 0; Index < Count(); ++Index)
			{
				List->AddSlot().AutoHeight()
				[
					SNew(SButton)
					.ButtonStyle(&FlatButton())
					.OnHovered_Lambda([this]() { Hovered(); })
					.OnClicked_Lambda([this, Anchor, SetIndex, Index]()
					{
						SetIndex(Index);
						Commit();
						Clicked();
						if (const TSharedPtr<SMenuAnchor> Open = Anchor->Pin())
						{
							Open->SetIsOpen(false);
						}
						return FReply::Handled();
					})
					[
						SNew(SBox).WidthOverride(402.f)
						[
							Field(SNew(SBox).VAlign(VAlign_Center).HAlign(HAlign_Center)
							[
								SNew(STextBlock).Text(Describe(Index)).Font(Font(false, 13.f))
								.ColorAndOpacity(Index == GetIndex() ? FSlateColor(OutlineHover) : FSlateColor(TextDim))
							], true)
						]
					]
				];
			}
			return SNew(SBox).MaxDesiredHeight(380.f)[ SNew(SScrollBox).ScrollBarStyle(&ScrollBar()) + SScrollBox::Slot()[ List ] ];
		})
		[
			SNew(SButton)
			.ButtonStyle(&FlatButton())
			.OnHovered_Lambda([this]() { Hovered(); })
			.OnClicked_Lambda([this, Anchor]()
			{
				if (const TSharedPtr<SMenuAnchor> Open = Anchor->Pin())
				{
					Open->SetIsOpen(!Open->IsOpen());
					Clicked();
				}
				return FReply::Handled();
			})
			[
				Field(SNew(SOverlay)
					+ SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Center).Padding(FMargin(6.f, 0.f))[ SNew(SSpaceChevron).Right(true).Color(Text) ]
					+ SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
					[
						SNew(STextBlock).Text_Lambda([GetIndex, Describe]() { return Describe(GetIndex()); }).Font(Font(false, 13.f)).ColorAndOpacity(Text)
					], false)
			]
		];
	*Anchor = Menu;
	return MakeRow(Label, Menu);
}

TSharedRef<SWidget> SSpaceMenu::MakeSliderRow(const FText& Label, float* Value, float Min, float Max, TFunction<FText(float)> Describe, bool bPreviewVolume)
{
	using namespace SpaceMenuStyle;
	return MakeRow(Label,
		SNew(SBox).HeightOverride(24.f)
			[
				SNew(SSpaceBox).Outline(FieldEdge).Corner(0.f).Thickness(1.f).Padding(FMargin(1.f))
				[
					SNew(SSlider)
					.Style(&Slider())
					.IndentHandle(false)
					.MinValue(Min)
					.MaxValue(Max)
					.Value_Lambda([Value]() { return *Value; })
					.OnValueChanged_Lambda([this, Value, bPreviewVolume](float NewValue)
					{
						*Value = NewValue;
						if (bPreviewVolume)
						{
							if (ASpacePlayerController* Controller = Owner.Get())
							{
								Controller->PreviewVolumes(Draft.MasterVolume, Draft.EffectsVolume, Draft.MusicVolume);
							}
						}
					})
					// Applying (scalability, saving the file) on every pixel of a drag would stall; once, when it ends.
					.OnMouseCaptureEnd_Lambda([this]() { Commit(); })
					.OnControllerCaptureEnd_Lambda([this]() { Commit(); })
				]
			],
		SNew(STextBlock).Text_Lambda([Value, Describe]() { return Describe(*Value); }).Font(Font(false, 13.f)).ColorAndOpacity(Text));
}

// -------------------------------------------------------------------------------------------
// Settings
// -------------------------------------------------------------------------------------------

void SSpaceMenu::LoadDraft()
{
	const USpaceUserSettings* Settings = USpaceUserSettings::Get();
	if (!Settings)
	{
		return;
	}
	const EWindowMode::Type Mode = Settings->GetFullscreenMode();
	Draft.WindowMode = Mode == EWindowMode::WindowedFullscreen ? 0 : Mode == EWindowMode::Fullscreen ? 1 : 2;

	const FIntPoint Current = Draft.WindowMode == 0 ? Settings->GetDesktopResolution() : Settings->GetScreenResolution();
	Draft.Resolution = Resolutions.Num() - 1;
	for (int32 Index = 0; Index < Resolutions.Num(); ++Index)
	{
		if (Resolutions[Index] == Current)
		{
			Draft.Resolution = Index;
		}
	}

	// Not GetOverallScalabilityLevel(): that is -1 whenever the resolution scale is not the preset's
	// default, which made this row show High and the next apply save High over the player's choice.
	Draft.Quality = Settings->GetGraphicsQualityLevel();
	float Normalized = 1.f;
	float Scale = 100.f;
	float MinScale = 50.f;
	float MaxScale = 100.f;
	Settings->GetResolutionScaleInformationEx(Normalized, Scale, MinScale, MaxScale);
	Draft.ResolutionScale = FMath::Clamp(Scale, 50.f, 100.f);
	Draft.bVSync = Settings->IsVSyncEnabled();

	const float Limit = Settings->GetFrameRateLimit();
	Draft.FrameLimit = 0;
	for (int32 Index = 1; Index < UE_ARRAY_COUNT(SpaceMenuStyle::FrameLimits); ++Index)
	{
		if (FMath::IsNearlyEqual(Limit, float(SpaceMenuStyle::FrameLimits[Index]), 0.5f))
		{
			Draft.FrameLimit = Index;
		}
	}

	Draft.MasterVolume = Settings->MasterVolume;
	Draft.EffectsVolume = Settings->EffectsVolume;
	Draft.MusicVolume = Settings->MusicVolume;
	Draft.MouseSensitivity = Settings->MouseSensitivity;
	Draft.bInvertPitch = Settings->bInvertShipPitch;
	Draft.HudMode = FMath::Clamp(Settings->HudMode, 0, 3);
	Draft.bShowFps = Settings->bShowFps;

	Draft.Groups[0] = Settings->GetViewDistanceQuality();
	Draft.Groups[1] = Settings->GetShadowQuality();
	Draft.Groups[2] = Settings->GetGlobalIlluminationQuality();
	Draft.Groups[3] = Settings->GetReflectionQuality();
	Draft.Groups[4] = Settings->GetTextureQuality();
	Draft.Groups[5] = Settings->GetVisualEffectQuality();
	Draft.Groups[6] = Settings->GetPostProcessingQuality();
	Draft.Groups[7] = Settings->GetFoliageQuality();
	Draft.Groups[8] = Settings->GetShadingQuality();
	for (int32& Group : Draft.Groups)
	{
		Group = FMath::Clamp(Group, 0, 4);
	}
	Draft.FieldOfView = Settings->FieldOfView;
	Draft.Gamma = Settings->Gamma;
	Draft.Sharpen = Settings->Sharpen;
	Draft.bMotionBlur = Settings->bMotionBlur;
	Draft.bFilmGrain = Settings->bFilmGrain;
	Draft.bChromaticAberration = Settings->bChromaticAberration;
	Draft.bStartDecoupled = Settings->bStartDecoupled;
	Draft.bGSafe = Settings->bDefaultGSafe;
	Draft.bComStab = Settings->bDefaultComStab;
	Draft.bVirtualJoystick = Settings->bVirtualJoystick;
	Draft.VJoyDeadzone = Settings->VJoyDeadzone;
	Draft.bFlightPathMarker = Settings->bShowFlightPathMarker;
	Draft.CameraShake = Settings->CameraShakeScale;
	Draft.bAudioInBackground = Settings->bAudioInBackground;
	Draft.bInvertFreeLook = Settings->bInvertFreeLookPitch;
	Draft.bInvertWalk = Settings->bInvertWalkPitch;
}

void SSpaceMenu::SetGroupsFromPreset(int32 Preset)
{
	for (int32 Group = 0; Group < 9; ++Group)
	{
		Draft.Groups[Group] = Group == 2 ? FMath::Min(Preset, USpaceUserSettings::MaxGlobalIlluminationQuality) : Preset;
	}
}

bool SSpaceMenu::AreGroupsCustom() const
{
	for (int32 Group = 0; Group < 9; ++Group)
	{
		const int32 Expected = Group == 2 ? FMath::Min(Draft.Quality, USpaceUserSettings::MaxGlobalIlluminationQuality) : Draft.Quality;
		if (Draft.Groups[Group] != Expected)
		{
			return true;
		}
	}
	return false;
}

void SSpaceMenu::Commit()
{
	USpaceUserSettings* Settings = USpaceUserSettings::Get();
	if (!Settings)
	{
		return;
	}
	Settings->SetFullscreenMode(SpaceMenuStyle::WindowModes[FMath::Clamp(Draft.WindowMode, 0, 2)]);
	// Borderless always covers the whole monitor.
	Settings->SetScreenResolution(Draft.WindowMode == 0 || !Resolutions.IsValidIndex(Draft.Resolution)
		? Settings->GetDesktopResolution() : Resolutions[Draft.Resolution]);
	Settings->SetOverallScalabilityLevel(Draft.Quality);
	// Then each group as the page has it (equal to the preset unless one was picked by hand).
	Settings->SetViewDistanceQuality(Draft.Groups[0]);
	Settings->SetShadowQuality(Draft.Groups[1]);
	Settings->SetGlobalIlluminationQuality(FMath::Min(Draft.Groups[2], USpaceUserSettings::MaxGlobalIlluminationQuality));
	Settings->SetReflectionQuality(Draft.Groups[3]);
	Settings->SetTextureQuality(Draft.Groups[4]);
	Settings->SetVisualEffectQuality(Draft.Groups[5]);
	Settings->SetPostProcessingQuality(Draft.Groups[6]);
	Settings->SetFoliageQuality(Draft.Groups[7]);
	Settings->SetShadingQuality(Draft.Groups[8]);
	Settings->SetResolutionScaleValueEx(Draft.ResolutionScale);
	Settings->SetVSyncEnabled(Draft.bVSync);
	Settings->SetFrameRateLimit(float(SpaceMenuStyle::FrameLimits[FMath::Clamp(Draft.FrameLimit, 0, int32(UE_ARRAY_COUNT(SpaceMenuStyle::FrameLimits)) - 1)]));

	Settings->MasterVolume = Draft.MasterVolume;
	Settings->EffectsVolume = Draft.EffectsVolume;
	Settings->MusicVolume = Draft.MusicVolume;
	Settings->MouseSensitivity = Draft.MouseSensitivity;
	Settings->bInvertShipPitch = Draft.bInvertPitch;
	Settings->HudMode = Draft.HudMode;
	Settings->bShowFps = Draft.bShowFps;
	Settings->FieldOfView = Draft.FieldOfView;
	Settings->Gamma = Draft.Gamma;
	Settings->Sharpen = Draft.Sharpen;
	Settings->bMotionBlur = Draft.bMotionBlur;
	Settings->bFilmGrain = Draft.bFilmGrain;
	Settings->bChromaticAberration = Draft.bChromaticAberration;
	Settings->bStartDecoupled = Draft.bStartDecoupled;
	Settings->bDefaultGSafe = Draft.bGSafe;
	Settings->bDefaultComStab = Draft.bComStab;
	Settings->bVirtualJoystick = Draft.bVirtualJoystick;
	Settings->VJoyDeadzone = Draft.VJoyDeadzone;
	Settings->bShowFlightPathMarker = Draft.bFlightPathMarker;
	Settings->CameraShakeScale = Draft.CameraShake;
	Settings->bAudioInBackground = Draft.bAudioInBackground;
	Settings->bInvertFreeLookPitch = Draft.bInvertFreeLook;
	Settings->bInvertWalkPitch = Draft.bInvertWalk;

	// Applies the video mode and scalability and saves GameUserSettings.ini.
	Settings->ApplySettings(false);
	if (ASpacePlayerController* Controller = Owner.Get())
	{
		Settings->ApplyGameSettings(Controller->GetWorld());
		Controller->PreviewVolumes(Settings->MasterVolume, Settings->EffectsVolume, Settings->MusicVolume);
	}
}

void SSpaceMenu::ResetTab()
{
	// Not GetDefault<>(): the class default object is loaded from the player's own GameUserSettings.ini.
	USpaceUserSettings* Defaults = NewObject<USpaceUserSettings>(GetTransientPackage());
	Defaults->SetGameDefaults();
	switch (CurrentTab)
	{
	case ESpaceSettingsTab::Graphics:
	{
		// As USpaceUserSettings::SetToDefaults: borderless at the monitor's resolution, epic at a 75 % render scale.
		Draft.WindowMode = 0;
		const FIntPoint Desktop = USpaceUserSettings::Get() ? USpaceUserSettings::Get()->GetDesktopResolution() : FIntPoint::ZeroValue;
		Draft.Resolution = FMath::Max(Resolutions.IndexOfByKey(Desktop), 0);
		Draft.Quality = USpaceUserSettings::DefaultQualityLevel;
		SetGroupsFromPreset(Draft.Quality);
		Draft.ResolutionScale = USpaceUserSettings::DefaultRenderScale;
		Draft.bVSync = false;
		Draft.FrameLimit = 0;
		Draft.FieldOfView = Defaults->FieldOfView;
		Draft.Gamma = Defaults->Gamma;
		Draft.Sharpen = Defaults->Sharpen;
		Draft.bMotionBlur = Defaults->bMotionBlur;
		Draft.bFilmGrain = Defaults->bFilmGrain;
		Draft.bChromaticAberration = Defaults->bChromaticAberration;
		break;
	}
	case ESpaceSettingsTab::Audio:
		Draft.MasterVolume = Defaults->MasterVolume;
		Draft.EffectsVolume = Defaults->EffectsVolume;
		Draft.MusicVolume = Defaults->MusicVolume;
		Draft.bAudioInBackground = Defaults->bAudioInBackground;
		break;
	case ESpaceSettingsTab::Controls:
		Draft.MouseSensitivity = Defaults->MouseSensitivity;
		Draft.bInvertPitch = Defaults->bInvertShipPitch;
		Draft.bInvertFreeLook = Defaults->bInvertFreeLookPitch;
		Draft.bInvertWalk = Defaults->bInvertWalkPitch;
		break;
	case ESpaceSettingsTab::Game:
		Draft.HudMode = Defaults->HudMode;
		Draft.bShowFps = Defaults->bShowFps;
		Draft.bStartDecoupled = Defaults->bStartDecoupled;
		Draft.bGSafe = Defaults->bDefaultGSafe;
		Draft.bComStab = Defaults->bDefaultComStab;
		Draft.bVirtualJoystick = Defaults->bVirtualJoystick;
		Draft.VJoyDeadzone = Defaults->VJoyDeadzone;
		Draft.bFlightPathMarker = Defaults->bShowFlightPathMarker;
		Draft.CameraShake = Defaults->CameraShakeScale;
		break;
	default:
		break;
	}
	Commit();
}

void SSpaceMenu::CloseSettings()
{
	// Everything is applied as it changes (as SC); Back only leaves.
	ShowPage(bTitleScreen ? ESpaceMenuPage::Main : ESpaceMenuPage::Pause);
}

void SSpaceMenu::Hovered()
{
	if (ASpacePlayerController* Controller = Owner.Get())
	{
		Controller->PlayUiSound(false);
	}
}

void SSpaceMenu::Clicked()
{
	if (ASpacePlayerController* Controller = Owner.Get())
	{
		Controller->PlayUiSound(true);
	}
}

#undef LOCTEXT_NAMESPACE
