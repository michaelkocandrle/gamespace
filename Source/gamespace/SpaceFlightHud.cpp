// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceFlightHud.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "HAL/IConsoleManager.h"
#include "Rendering/DrawElements.h"
#include "SpaceshipPawn.h"
#include "Styling/CoreStyle.h"

namespace SpaceHudStyle
{
	// Thin translucent cyan, like the reference's glass frame lines; colours carry the state.
	const FLinearColor Cyan(0.45f, 0.9f, 1.f, 0.9f);
	const FLinearColor CyanFaint(0.45f, 0.9f, 1.f, 0.3f);
	const FLinearColor LampOff(0.45f, 0.9f, 1.f, 0.1f);
	const FLinearColor Green(0.35f, 1.f, 0.55f, 0.85f);
	const FLinearColor Amber(1.f, 0.72f, 0.2f, 0.95f);
	const FLinearColor Red(1.f, 0.3f, 0.22f, 0.95f);
	const FLinearColor NavBlue(0.45f, 0.65f, 1.f, 0.95f);

	const FSlateBrush* White()
	{
		return FCoreStyle::Get().GetBrush("WhiteBrush");
	}

	FLinearColor Faded(FLinearColor Color, float Factor)
	{
		Color.A *= Factor;
		return Color;
	}

	/**
	 * Slate has no additive brush and a scene bloom would light up the whole game, so a "glow" here is
	 * the same stroke drawn two more times, thicker and much fainter: a halo that reads the same way
	 * at HUD line widths and costs two draw calls.
	 */
	void GlowLines(FSlateWindowElementList& Out, int32 Layer, const FPaintGeometry& Geometry, const TArray<FVector2f>& Points,
		const FLinearColor& Color, float Thickness, float Glow)
	{
		if (Glow > 0.01f)
		{
			FSlateDrawElement::MakeLines(Out, Layer, Geometry, Points, ESlateDrawEffect::None, Faded(Color, 0.07f * Glow), true, Thickness + 7.f);
			FSlateDrawElement::MakeLines(Out, Layer, Geometry, Points, ESlateDrawEffect::None, Faded(Color, 0.16f * Glow), true, Thickness + 3.f);
		}
		FSlateDrawElement::MakeLines(Out, Layer, Geometry, Points, ESlateDrawEffect::None, Color, true, Thickness);
	}

	void GlowBox(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geometry, const FVector2f& Centre, float HalfSize,
		const FLinearColor& Color, float Glow)
	{
		auto Box = [&](float Half, const FLinearColor& BoxColor)
		{
			FSlateDrawElement::MakeBox(Out, Layer, Geometry.ToPaintGeometry(FVector2f(Half * 2.f, Half * 2.f),
				FSlateLayoutTransform(Centre - FVector2f(Half, Half))), White(), ESlateDrawEffect::None, BoxColor);
		};
		if (Glow > 0.01f)
		{
			Box(HalfSize + 5.f, Faded(Color, 0.10f * Glow));
			Box(HalfSize + 2.5f, Faded(Color, 0.18f * Glow));
		}
		Box(HalfSize, Color);
	}

	FString Speed(double CmPerSecond)
	{
		const double Metres = CmPerSecond / 100.0;
		return FMath::Abs(Metres) < 1000.0 ? FString::Printf(TEXT("%.0f M/S"), Metres) : FString::Printf(TEXT("%.2f KM/S"), Metres / 1000.0);
	}
}

// -------------------------------------------------------------------------------------------
// Panel with cut corners
// -------------------------------------------------------------------------------------------

int32 USpaceHudPanel::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	using namespace SpaceHudStyle;
	LayerId = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);

	const FVector2f Size = AllottedGeometry.GetLocalSize();
	const float Cut = FMath::Clamp(Chamfer, 0.f, FMath::Min(Size.X, Size.Y) * 0.5f);
	if (Size.X < 4.f || Size.Y < 4.f)
	{
		return LayerId;
	}
	// A barely-there fill so the lines read as a panel without hiding the view: three boxes make the
	// chamfered shape, which Slate cannot fill directly.
	const FLinearColor Fill(0.05f, 0.12f, 0.16f, FillAlpha);
	auto Box = [&](float X0, float Y0, float X1, float Y1)
	{
		FSlateDrawElement::MakeBox(OutDrawElements, LayerId, AllottedGeometry.ToPaintGeometry(FVector2f(X1 - X0, Y1 - Y0),
			FSlateLayoutTransform(FVector2f(X0, Y0))), White(), ESlateDrawEffect::None, Fill);
	};
	Box(0.f, Cut, Size.X, Size.Y - Cut);
	Box(Cut, 0.f, Size.X - Cut, Cut);
	Box(Cut, Size.Y - Cut, Size.X - Cut, Size.Y);

	const TArray<FVector2f> Outline = {
		FVector2f(Cut, 0.f), FVector2f(Size.X - Cut, 0.f), FVector2f(Size.X, Cut),
		FVector2f(Size.X, Size.Y - Cut), FVector2f(Size.X - Cut, Size.Y), FVector2f(Cut, Size.Y),
		FVector2f(0.f, Size.Y - Cut), FVector2f(0.f, Cut), FVector2f(Cut, 0.f) };
	GlowLines(OutDrawElements, LayerId + 1, AllottedGeometry.ToPaintGeometry(), Outline, LineColor, 1.2f, Glow);
	return LayerId + 1;
}

// -------------------------------------------------------------------------------------------
// Status lamp
// -------------------------------------------------------------------------------------------

void USpaceHudLamp::SetTarget(bool bLit, const FLinearColor& InColor)
{
	const float NewTarget = bLit ? 1.f : 0.f;
	if (NewTarget != Target)
	{
		// A change is worth noticing: a short flash, then the lamp eases to its new level.
		Flash = 1.f;
	}
	Target = NewTarget;
	Color = InColor;
}

void USpaceHudLamp::Advance(float DeltaSeconds)
{
	Intensity += (Target - Intensity) * (1.f - FMath::Exp(-12.f * DeltaSeconds));
	Flash *= FMath::Exp(-6.f * DeltaSeconds);
	if (FMath::Abs(Target - Intensity) < 0.002f)
	{
		Intensity = Target;
	}
}

int32 USpaceHudLamp::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	using namespace SpaceHudStyle;
	LayerId = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);

	const FVector2f Size = AllottedGeometry.GetLocalSize();
	const float Half = FMath::Min(Size.X, Size.Y) * 0.5f;
	if (Half < 1.f)
	{
		return LayerId;
	}
	const float Lit = FMath::Clamp(Intensity + 0.5f * Flash * Intensity, 0.f, 1.5f);
	// Dark but never invisible, so the row still reads as a row of switches.
	FLinearColor Core = FMath::Lerp(LampOff, Color, FMath::Min(Lit, 1.f));
	Core.A = FMath::Lerp(LampOff.A, Color.A, FMath::Min(Lit, 1.f));
	GlowBox(OutDrawElements, LayerId, AllottedGeometry, Size * 0.5f, Half, Core, Lit);
	return LayerId + 1;
}

// -------------------------------------------------------------------------------------------
// Gauge
// -------------------------------------------------------------------------------------------

int32 USpaceHudGauge::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	using namespace SpaceHudStyle;
	LayerId = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);

	const FVector2f Size = AllottedGeometry.GetLocalSize();
	// Work along the gauge ("along", 0 at the low end) and across it, then map to widget space.
	const float Length = bHorizontal ? Size.X : Size.Y;
	const float Width = bHorizontal ? Size.Y : Size.X;
	if (Length <= 1.f || Width <= 1.f)
	{
		return LayerId;
	}
	const float Dim = bDim ? 0.4f : 1.f;
	auto Point = [&](float Along, float Across)
	{
		return bHorizontal ? FVector2f(Along, Width - Across) : FVector2f(Across, Length - Along);
	};
	auto Line = [&](float A0, float C0, float A1, float C1, const FLinearColor& Color, float Thickness, float Glow = 0.f)
	{
		const TArray<FVector2f> Points = { Point(A0, C0), Point(A1, C1) };
		GlowLines(OutDrawElements, LayerId + 1, AllottedGeometry.ToPaintGeometry(), Points, Faded(Color, Dim), Thickness, Glow * Dim);
	};
	auto Box = [&](float A0, float A1, float C0, float C1, const FLinearColor& Color)
	{
		if (A1 - A0 < 0.5f)
		{
			return;
		}
		const FVector2f Position = bHorizontal ? FVector2f(A0, Width - C1) : FVector2f(C0, Length - A1);
		const FVector2f BoxSize = bHorizontal ? FVector2f(A1 - A0, C1 - C0) : FVector2f(C1 - C0, A1 - A0);
		FSlateDrawElement::MakeBox(OutDrawElements, LayerId, AllottedGeometry.ToPaintGeometry(BoxSize, FSlateLayoutTransform(Position)),
			White(), ESlateDrawEffect::None, Faded(Color, Dim));
	};

	const float Zero = Length * FMath::Clamp(ReverseZone, 0.f, 0.9f);
	const float Span = Length - Zero;

	// Frame: faint rails along both sides, a brighter cut-corner cap at the top.
	Line(0.f, 0.f, Length - 4.f, 0.f, CyanFaint, 1.f);
	Line(0.f, Width, Length - 4.f, Width, CyanFaint, 1.f);
	Line(Length - 4.f, 0.f, Length, 4.f, Cyan, 1.5f, 0.4f);
	Line(Length - 4.f, Width, Length, Width - 4.f, Cyan, 1.5f, 0.4f);
	Line(Length, 4.f, Length, Width - 4.f, Cyan, 1.5f, 0.4f);
	Line(0.f, 0.f, 0.f, Width, CyanFaint, 1.f);
	for (int32 Index = 1; Index < Ticks; ++Index)
	{
		const float Along = Zero + Span * Index / Ticks;
		Line(Along, 0.f, Along, Width * (Index * 2 == Ticks ? 0.45f : 0.25f), CyanFaint, 1.f);
	}

	// Reverse zone: a faint red band under a bright zero line.
	if (Zero > 0.f)
	{
		Box(0.f, Zero, 0.f, Width, Faded(Red, 0.12f));
		Line(Zero, -3.f, Zero, Width + 3.f, Cyan, 1.5f);
	}

	// Fill: a translucent bar inset from the rails with a bright leading edge.
	const float Inset = FMath::Max(2.f, Width * 0.2f);
	const float Top = Zero + Span * FMath::Clamp(Value, 0.f, 1.f);
	if (Top > Zero + 0.5f)
	{
		Box(Zero, Top, Inset, Width - Inset, Faded(FillColor, 0.45f));
		Line(Top, Inset * 0.5f, Top, Width - Inset * 0.5f, FillColor, 2.f, 1.f);
	}
	const float Bottom = Zero * (1.f - FMath::Clamp(ReverseValue, 0.f, 1.f));
	if (Bottom < Zero - 0.5f)
	{
		Box(Bottom, Zero, Inset, Width - Inset, Faded(Red, 0.6f));
		Line(Bottom, Inset * 0.5f, Bottom, Width - Inset * 0.5f, Red, 2.f);
	}

	// Marker (the limiter's handle, the G-Safe line): a bar wider than the gauge.
	if (Marker >= 0.f)
	{
		const float Along = Zero + Span * FMath::Clamp(Marker, 0.f, 1.f);
		Line(Along, -5.f, Along, Width + 5.f, MarkerColor, 2.5f, 0.8f);
	}
	return LayerId + 1;
}

// -------------------------------------------------------------------------------------------
// Virtual joystick
// -------------------------------------------------------------------------------------------

int32 USpaceHudVirtualJoystick::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	using namespace SpaceHudStyle;
	LayerId = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);

	const FVector2f Size = AllottedGeometry.GetLocalSize();
	const FVector2f Centre = Size * 0.5f;
	const float Radius = FMath::Min(Size.X, Size.Y) * 0.5f - 2.f;
	if (Radius <= 2.f)
	{
		return LayerId;
	}
	auto Draw = [&](const TArray<FVector2f>& Points, const FLinearColor& Color, float Thickness, float Glow = 0.f)
	{
		GlowLines(OutDrawElements, LayerId, AllottedGeometry.ToPaintGeometry(), Points, Color, Thickness, Glow);
	};
	auto Circle = [&](float R, const FLinearColor& Color)
	{
		TArray<FVector2f> Points;
		const int32 Segments = 64;
		for (int32 Index = 0; Index <= Segments; ++Index)
		{
			const float Angle = UE_TWO_PI * Index / Segments;
			Points.Add(Centre + FVector2f(FMath::Cos(Angle), FMath::Sin(Angle)) * R);
		}
		Draw(MoveTemp(Points), Color, 1.f);
	};

	Circle(Radius, Faded(CyanFaint, 0.9f));
	Circle(Radius * FMath::Clamp(Deadzone, 0.f, 1.f), CyanFaint);

	// Stick Y up is screen up.
	const FVector2f CursorAt = Centre + FVector2f(float(Stick.X), float(-Stick.Y)) * Radius;
	const bool bTurning = Stick.Size() > Deadzone;
	const FLinearColor CursorColor = bTurning ? Amber : Faded(Cyan, 0.7f);
	if (bTurning)
	{
		Draw({ Centre, CursorAt }, Faded(Amber, 0.35f), 1.f);
	}
	const float Arm = 7.f;
	Draw({ CursorAt - FVector2f(Arm, 0.f), CursorAt + FVector2f(Arm, 0.f) }, CursorColor, 2.f, bTurning ? 1.f : 0.4f);
	Draw({ CursorAt - FVector2f(0.f, Arm), CursorAt + FVector2f(0.f, Arm) }, CursorColor, 2.f, bTurning ? 1.f : 0.4f);
	return LayerId;
}

// -------------------------------------------------------------------------------------------
// Flight HUD
// -------------------------------------------------------------------------------------------

bool USpaceFlightHud::Initialize()
{
	const bool bResult = Super::Initialize();
	if (WidgetTree && !WidgetTree->RootWidget)
	{
		BuildTree();
	}
	return bResult;
}

UTextBlock* USpaceFlightHud::MakeText(const FName Name, float Size, int32 LetterSpacing, const FName Weight)
{
	UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
	// "Mono" is the engine's DroidSansMono (Slate's built-in typefaces, no asset to import): digits
	// keep their place as speed changes, and it reads as instrument type rather than UI text.
	FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle(Weight, Size);
	Font.LetterSpacing = LetterSpacing;
	// A thin dark outline instead of a drop shadow: readable against the sun and a bright planet
	// from every side.
	Font.OutlineSettings.OutlineSize = 1;
	Font.OutlineSettings.OutlineColor = FLinearColor(0.f, 0.02f, 0.04f, 0.85f);
	Text->SetFont(Font);
	Text->SetColorAndOpacity(FSlateColor(SpaceHudStyle::Cyan));
	Texts.Add(Name, Text);
	return Text;
}

void USpaceFlightHud::BuildTree()
{
	using namespace SpaceHudStyle;

	UCanvasPanel* Root = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("Root"));
	WidgetTree->RootWidget = Root;

	// Everything hangs off the middle of the screen, so it frames the view at any resolution.
	auto Place = [Root](UWidget* Widget, const FVector2D& Offset, const FVector2D& Alignment)
	{
		UCanvasPanelSlot* Slot = Root->AddChildToCanvas(Widget);
		Slot->SetAnchors(FAnchors(0.5f, 0.5f));
		Slot->SetAlignment(Alignment);
		Slot->SetAutoSize(true);
		Slot->SetPosition(Offset);
	};
	auto Sized = [this](const FName Name, UWidget* Content, float Width, float Height)
	{
		USizeBox* Box = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), Name);
		Box->SetWidthOverride(Width);
		Box->SetHeightOverride(Height);
		Box->AddChild(Content);
		return Box;
	};
	auto Lamp = [this](const FName Name)
	{
		USpaceHudLamp* NewLamp = WidgetTree->ConstructWidget<USpaceHudLamp>(USpaceHudLamp::StaticClass(), Name);
		NewLamp->Color = SpaceHudStyle::Cyan;
		Lamps.Add(FName(*Name.ToString().RightChop(5)), NewLamp);  // Lamp_CPLD -> CPLD
		return NewLamp;
	};
	// Content over a cut-corner panel, like the reference's instrument frames.
	auto Panelled = [this](const FName PanelName, UWidget* Content, const FMargin& Inset)
	{
		UOverlay* Overlay = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass(), FName(*FString::Printf(TEXT("%sOverlay"), *PanelName.ToString())));
		USpaceHudPanel* Panel = WidgetTree->ConstructWidget<USpaceHudPanel>(USpaceHudPanel::StaticClass(), PanelName);
		Panel->LineColor = SpaceHudStyle::CyanFaint;
		Overlay->AddChildToOverlay(Panel);
		if (UOverlaySlot* ContentSlot = Overlay->AddChildToOverlay(Content))
		{
			ContentSlot->SetPadding(Inset);
			ContentSlot->SetHorizontalAlignment(HAlign_Fill);
			ContentSlot->SetVerticalAlignment(VAlign_Fill);
		}
		return Overlay;
	};
	auto Frame = [this](const FName Name)
	{
		USpaceHudPanel* Panel = WidgetTree->ConstructWidget<USpaceHudPanel>(USpaceHudPanel::StaticClass(), Name);
		Panel->LineColor = SpaceHudStyle::CyanFaint;
		Panel->FillAlpha = 0.f;
		Panel->Chamfer = 5.f;
		Panel->Glow = 0.3f;
		return Panel;
	};
	auto Gauge = [this](const FName Name, bool bHorizontal, int32 Ticks)
	{
		USpaceHudGauge* NewGauge = WidgetTree->ConstructWidget<USpaceHudGauge>(USpaceHudGauge::StaticClass(), Name);
		NewGauge->bHorizontal = bHorizontal;
		NewGauge->Ticks = Ticks;
		Gauges.Add(Name, NewGauge);
		return NewGauge;
	};
	auto AddToVertical = [](UVerticalBox* Box, UWidget* Child, EHorizontalAlignment Align, const FMargin& SlotPadding)
	{
		UVerticalBoxSlot* Slot = Box->AddChildToVerticalBox(Child);
		Slot->SetHorizontalAlignment(Align);
		Slot->SetPadding(SlotPadding);
	};
	auto AddToHorizontal = [](UHorizontalBox* Box, UWidget* Child, EVerticalAlignment Align, const FMargin& SlotPadding)
	{
		UHorizontalBoxSlot* Slot = Box->AddChildToHorizontalBox(Child);
		Slot->SetVerticalAlignment(Align);
		Slot->SetPadding(SlotPadding);
	};
	const float FrameHeight = 430.f;

	// --- Left of centre: lamps, speed gauge, speed, limit, G meter, then a frame line ---------
	UHorizontalBox* Left = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("LeftCluster"));
	UVerticalBox* LeftContent = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("LeftContent"));
	UVerticalBox* LampBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("LampBox"));
	for (const TCHAR* LampName : { TEXT("MODE"), TEXT("CPLD"), TEXT("GSAF"), TEXT("CSTB"), TEXT("BOOST") })
	{
		const FName Key(LampName);
		UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), FName(*FString::Printf(TEXT("LampRow_%s"), LampName)));
		UTextBlock* Label = MakeText(FName(*FString::Printf(TEXT("LampLabel_%s"), LampName)), 10.f, 180);
		Label->SetText(FText::FromString(LampName));
		LampLabels.Add(Key, Label);
		AddToHorizontal(Row, Label, VAlign_Center, FMargin(0.f, 0.f, 7.f, 0.f));
		AddToHorizontal(Row, Sized(FName(*FString::Printf(TEXT("LampBox_%s"), LampName)),
			Lamp(FName(*FString::Printf(TEXT("Lamp_%s"), LampName))), 8.f, 8.f), VAlign_Center, FMargin(0.f));
		AddToVertical(LampBox, Row, HAlign_Right, FMargin(0.f, 0.f, 0.f, 5.f));
	}
	AddToVertical(LeftContent, Panelled(TEXT("LampPanel"), LampBox, FMargin(10.f, 8.f, 10.f, 3.f)), HAlign_Right, FMargin(0.f, 0.f, 0.f, 10.f));
	UVerticalBox* SpeedBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("SpeedBox"));
	AddToVertical(SpeedBox, Sized(TEXT("SpeedGaugeBox"), Gauge(TEXT("SpeedGauge"), false, 10), 26.f, 280.f), HAlign_Center, FMargin(0.f, 0.f, 0.f, 8.f));
	AddToVertical(SpeedBox, MakeText(TEXT("SpeedText"), 15.f, 30), HAlign_Right, FMargin(0.f));
	AddToVertical(SpeedBox, MakeText(TEXT("LimitText"), 9.f, 40), HAlign_Right, FMargin(0.f, 0.f, 0.f, 7.f));
	UHorizontalBox* GRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("GRow"));
	AddToHorizontal(GRow, Sized(TEXT("GGaugeBox"), Gauge(TEXT("GGauge"), true, 4), 64.f, 8.f), VAlign_Center, FMargin(0.f, 0.f, 8.f, 0.f));
	AddToHorizontal(GRow, MakeText(TEXT("GText"), 12.f, 30), VAlign_Center, FMargin(0.f));
	AddToVertical(SpeedBox, GRow, HAlign_Right, FMargin(0.f));
	AddToVertical(LeftContent, Panelled(TEXT("SpeedPanel"), SpeedBox, FMargin(12.f, 10.f)), HAlign_Right, FMargin(0.f));
	AddToHorizontal(Left, LeftContent, VAlign_Center, FMargin(0.f, 0.f, 14.f, 0.f));
	// The glass frame line beside the cluster, cut at both ends like the reference's canopy frame.
	AddToHorizontal(Left, Sized(TEXT("FrameLeftBox"), Frame(TEXT("FrameLeft")), 10.f, FrameHeight), VAlign_Center, FMargin(0.f));
	Place(Left, FVector2D(-300.0, 30.0), FVector2D(1.0, 0.5));

	// --- Right of centre: a frame line, then boost energy and afterburner fuel gauges ----------
	UHorizontalBox* Right = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("RightCluster"));
	AddToHorizontal(Right, Sized(TEXT("FrameRightBox"), Frame(TEXT("FrameRight")), 10.f, FrameHeight), VAlign_Center, FMargin(0.f, 0.f, 14.f, 0.f));
	UHorizontalBox* Columns = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("RightColumns"));
	auto Column = [&](const TCHAR* Label, const FName GaugeName, const FName TextName, const FMargin& SlotPadding)
	{
		UVerticalBox* Box = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), FName(*FString::Printf(TEXT("%sColumn"), *GaugeName.ToString())));
		UTextBlock* Title = MakeText(FName(*FString::Printf(TEXT("%sTitle"), *GaugeName.ToString())), 9.f, 180);
		Title->SetText(FText::FromString(Label));
		AddToVertical(Box, Title, HAlign_Center, FMargin(0.f, 0.f, 0.f, 6.f));
		AddToVertical(Box, Sized(FName(*FString::Printf(TEXT("%sBox"), *GaugeName.ToString())), Gauge(GaugeName, false, 5), 14.f, 220.f), HAlign_Center, FMargin(0.f, 0.f, 0.f, 7.f));
		AddToVertical(Box, MakeText(TextName, 10.f, 40), HAlign_Center, FMargin(0.f));
		AddToHorizontal(Columns, Box, VAlign_Center, SlotPadding);
	};
	Column(TEXT("BST"), TEXT("BoostGauge"), TEXT("BoostText"), FMargin(0.f, 0.f, 22.f, 0.f));
	Column(TEXT("AB"), TEXT("AfterburnerGauge"), TEXT("AfterburnerText"), FMargin(0.f));
	AddToHorizontal(Right, Panelled(TEXT("PowerPanel"), Columns, FMargin(14.f, 10.f)), VAlign_Center, FMargin(0.f));
	Place(Right, FVector2D(300.0, 30.0), FVector2D(0.0, 0.5));

	// --- Centre: the virtual joystick ----------------------------------------------------------
	VirtualJoystick = WidgetTree->ConstructWidget<USpaceHudVirtualJoystick>(USpaceHudVirtualJoystick::StaticClass(), TEXT("VirtualJoystick"));
	USizeBox* JoystickBox = Sized(TEXT("VirtualJoystickBox"), VirtualJoystick, 240.f, 240.f);
	VirtualJoystickBox = JoystickBox;
	Place(JoystickBox, FVector2D::ZeroVector, FVector2D(0.5, 0.5));

	// A display, never in the way of the mouse or the menus.
	Root->SetVisibility(ESlateVisibility::Collapsed);
	SetVisibility(ESlateVisibility::HitTestInvisible);
}

FSpaceFlightHudState USpaceFlightHud::MakeState(const ASpaceshipPawn* Ship, int32 HudMode)
{
	FSpaceFlightHudState State;
	if (!Ship)
	{
		return State;
	}
	State.bVisible = HudMode > 0;

	const EMasterMode Shown = Ship->GetPendingMasterMode();
	State.bNav = Ship->GetMasterMode() == EMasterMode::NAV;
	State.ModeLabel = Shown == EMasterMode::NAV ? TEXT("NAV") : TEXT("SCM");
	State.bModeSwitching = Ship->IsMasterModeSwitching();
	State.ModeSwitchProgress = Ship->GetMasterModeSwitchProgress();
	State.bCoupled = Ship->IsFlightAssistOn();
	State.bSpaceBrake = Ship->IsSpaceBraking();
	State.bGSafeOn = Ship->IsGSafeOn();
	State.bGSafeActive = Ship->IsGSafeActive();
	State.bComStab = Ship->IsComStabOn();
	State.bBoostActive = Ship->IsBoosting();
	State.bBoostLocked = Ship->IsBoostLocked();
	State.BoostEnergy = Ship->GetBoostEnergy();
	State.bAfterburnerActive = Ship->IsAfterburnerActive();
	State.bAfterburnerLocked = Ship->IsAfterburnerLocked();
	State.bAfterburnerAvailable = Ship->GetMasterMode() == EMasterMode::SCM;
	State.AfterburnerFuel = Ship->GetAfterburnerFuel();

	// The gauge's full height is the mode's top speed as the afterburner currently raises it; the
	// limiter is a mark on that scale, the fill the speed along the nose.
	const FVector Velocity = Ship->GetLinearVelocity();
	State.SpeedCmS = float(Velocity.Size());
	State.ForwardSpeedCmS = float(Velocity | Ship->GetActorForwardVector());
	State.SpeedLimitCmS = Ship->GetSpeedLimit();
	const float Limiter = FMath::Max(Ship->GetSpeedLimiter(), 0.01f);
	State.GaugeScaleCmS = FMath::Max(State.SpeedLimitCmS / Limiter, 1.f);
	State.LimiterFraction = FMath::Clamp(Ship->GetSpeedLimiter(), 0.f, 1.f);
	State.SpeedFraction = FMath::Clamp(State.ForwardSpeedCmS / State.GaugeScaleCmS, 0.f, 1.f);
	// The reverse zone keeps the same speed per pixel as the rest of the gauge.
	const float ReverseSpan = State.GaugeScaleCmS * SpeedReverseZone / (1.f - SpeedReverseZone);
	State.ReverseFraction = FMath::Clamp(-State.ForwardSpeedCmS / ReverseSpan, 0.f, 1.f);
	State.bOverLimit = Ship->GetCruiseState() == ECruiseState::Off && State.SpeedCmS > State.SpeedLimitCmS * 1.02f + 50.f;

	State.GForce = Ship->GetGForce();
	State.GSafeMaxG = Ship->GetGSafeMaxG();

	State.bShowVirtualJoystick = Ship->UsesVirtualJoystick() && !Ship->IsLanded() && !Ship->IsFreeLooking();
	State.Stick = Ship->GetMouseStick();
	State.Deadzone = Ship->GetVirtualJoystickDeadzone();
	return State;
}

void USpaceFlightHud::ApplyState(const FSpaceFlightHudState& State)
{
	using namespace SpaceHudStyle;
	if (!WidgetTree || !WidgetTree->RootWidget)
	{
		return;
	}
	WidgetTree->RootWidget->SetVisibility(State.bVisible ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	if (!State.bVisible)
	{
		return;
	}

	const bool bBlink = FMath::Fmod(Time, 0.5f) < 0.25f;
	auto SetLamp = [this](const FName Name, bool bLit, const FLinearColor& Color)
	{
		if (USpaceHudLamp* Lamp = Lamps.FindRef(Name))
		{
			// The lamp eases to its new level and flashes once, so a switch is noticed, not blinked.
			Lamp->SetTarget(bLit, Color);
		}
		if (UTextBlock* Label = LampLabels.FindRef(Name))
		{
			Label->SetColorAndOpacity(FSlateColor(bLit ? Color : Faded(Cyan, 0.45f)));
		}
		LampLit.Add(Name, bLit);
	};
	auto SetText = [this](const FName Name, const FString& Value, const FLinearColor& Color)
	{
		if (UTextBlock* Text = Texts.FindRef(Name))
		{
			Text->SetText(FText::FromString(Value));
			Text->SetColorAndOpacity(FSlateColor(Color));
		}
	};

	// --- Lamps -------------------------------------------------------------------------------
	if (UTextBlock* ModeLabel = LampLabels.FindRef(TEXT("MODE")))
	{
		ModeLabel->SetText(FText::FromString(State.ModeLabel));
	}
	// Switching blinks the mode being switched to.
	SetLamp(TEXT("MODE"), !State.bModeSwitching || bBlink, State.ModeLabel == TEXT("NAV") ? NavBlue : Cyan);
	if (UTextBlock* CoupledLabel = LampLabels.FindRef(TEXT("CPLD")))
	{
		CoupledLabel->SetText(FText::FromString(State.bSpaceBrake ? TEXT("BRAKE") : TEXT("CPLD")));
	}
	SetLamp(TEXT("CPLD"), State.bCoupled || State.bSpaceBrake, State.bSpaceBrake ? Red : Cyan);
	// G-Safe switched on but suspended by boost: amber.
	SetLamp(TEXT("GSAF"), State.bGSafeOn, State.bGSafeActive ? Cyan : Amber);
	SetLamp(TEXT("CSTB"), State.bComStab, Cyan);
	SetLamp(TEXT("BOOST"), State.bBoostActive, Amber);

	// --- Speed gauge, speed, limit -------------------------------------------------------------
	if (USpaceHudGauge* Speed = Gauges.FindRef(TEXT("SpeedGauge")))
	{
		Speed->ReverseZone = SpeedReverseZone;
		Speed->Value = State.SpeedFraction;
		Speed->ReverseValue = State.ReverseFraction;
		Speed->Marker = State.LimiterFraction;
		Speed->MarkerColor = Cyan;
		Speed->FillColor = State.bAfterburnerActive ? Amber : State.bOverLimit ? Amber : Green;
	}
	SetText(TEXT("SpeedText"), SpaceHudStyle::Speed(State.SpeedCmS), State.ForwardSpeedCmS < -50.f ? Red : Cyan);
	SetText(TEXT("LimitText"), FString::Printf(TEXT("LIM %s  %3.0f%%"), *SpaceHudStyle::Speed(State.SpeedLimitCmS), State.LimiterFraction * 100.f),
		Faded(Cyan, 0.7f));

	// --- G meter ------------------------------------------------------------------------------
	const FLinearColor GColor = State.GForce > State.GSafeMaxG + 0.05f ? Red : State.GForce > State.GSafeMaxG * 0.7f ? Amber : Cyan;
	if (USpaceHudGauge* GGauge = Gauges.FindRef(TEXT("GGauge")))
	{
		GGauge->Value = State.GForce / GMeterRangeG;
		GGauge->FillColor = GColor;
		// The G-Safe limit as a mark, while G-Safe is actually limiting.
		GGauge->Marker = State.bGSafeActive ? State.GSafeMaxG / GMeterRangeG : -1.f;
		GGauge->MarkerColor = Faded(Cyan, 0.8f);
	}
	SetText(TEXT("GText"), FString::Printf(TEXT("%.1f G"), State.GForce), GColor);

	// --- Boost and afterburner ---------------------------------------------------------------------
	if (USpaceHudGauge* Boost = Gauges.FindRef(TEXT("BoostGauge")))
	{
		Boost->Value = State.BoostEnergy;
		Boost->FillColor = State.bBoostLocked ? Red : State.bBoostActive ? Amber : Cyan;
	}
	SetText(TEXT("BoostText"), State.bBoostLocked ? FString::Printf(TEXT("%.0f%% LOW"), State.BoostEnergy * 100.f)
		: FString::Printf(TEXT("%.0f%%"), State.BoostEnergy * 100.f), State.bBoostLocked ? Red : State.bBoostActive ? Amber : Cyan);

	if (USpaceHudGauge* Afterburner = Gauges.FindRef(TEXT("AfterburnerGauge")))
	{
		Afterburner->Value = State.AfterburnerFuel;
		Afterburner->bDim = !State.bAfterburnerAvailable;
		Afterburner->FillColor = State.bAfterburnerLocked ? Red : State.bAfterburnerActive ? Amber : Green;
	}
	FString AfterburnerText = FString::Printf(TEXT("%.0f%%"), State.AfterburnerFuel * 100.f);
	FLinearColor AfterburnerColor = Cyan;
	if (!State.bAfterburnerAvailable)
	{
		AfterburnerText += TEXT(" SCM ONLY");
		AfterburnerColor = Faded(Cyan, 0.45f);
	}
	else if (State.bAfterburnerLocked)
	{
		AfterburnerText += TEXT(" EMPTY");
		AfterburnerColor = Red;
	}
	else if (State.bAfterburnerActive)
	{
		AfterburnerText += TEXT(" BURN");
		AfterburnerColor = Amber;
	}
	SetText(TEXT("AfterburnerText"), AfterburnerText, AfterburnerColor);

	// --- Virtual joystick ---------------------------------------------------------------------------
	if (VirtualJoystickBox)
	{
		VirtualJoystickBox->SetVisibility(State.bShowVirtualJoystick ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	}
	if (VirtualJoystick)
	{
		VirtualJoystick->Stick = State.Stick;
		VirtualJoystick->Deadzone = State.Deadzone;
	}
}

void USpaceFlightHud::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	Time += InDeltaTime;
	// The root panel collapses rather than this widget, so the widget keeps ticking and can come back.
	static const IConsoleVariable* HudMode = IConsoleManager::Get().FindConsoleVariable(TEXT("space.Hud"));
	ApplyState(MakeState(Cast<ASpaceshipPawn>(GetOwningPlayerPawn()), HudMode ? HudMode->GetInt() : 1));
	DebugAdvance(InDeltaTime);
}

TArray<FString> USpaceFlightHud::DebugGetWidgetNames() const
{
	TArray<FString> Names;
	if (WidgetTree)
	{
		WidgetTree->ForEachWidget([&Names](UWidget* Widget) { Names.Add(Widget->GetName()); });
	}
	return Names;
}

bool USpaceFlightHud::DebugIsLampLit(FName Lamp, FLinearColor& OutColor) const
{
	const USpaceHudLamp* Found = Lamps.FindRef(Lamp);
	OutColor = Found ? Found->Color : FLinearColor::Transparent;
	return LampLit.FindRef(Lamp);
}

UTextBlock* USpaceFlightHud::DebugGetTextWidget(FName TextName) const
{
	return Texts.FindRef(TextName);
}

USpaceHudLamp* USpaceFlightHud::DebugGetLamp(FName Lamp) const
{
	return Lamps.FindRef(Lamp);
}

void USpaceFlightHud::DebugAdvance(float Seconds)
{
	for (const TPair<FName, TObjectPtr<USpaceHudLamp>>& Pair : Lamps)
	{
		if (Pair.Value)
		{
			Pair.Value->Advance(Seconds);
		}
	}
}

FString USpaceFlightHud::DebugGetText(FName TextName) const
{
	const UTextBlock* Text = Texts.FindRef(TextName);
	return Text ? Text->GetText().ToString() : FString();
}

USpaceHudGauge* USpaceFlightHud::DebugGetGauge(FName GaugeName) const
{
	return Gauges.FindRef(GaugeName);
}
