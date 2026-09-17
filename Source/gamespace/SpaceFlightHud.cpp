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
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Misc/Paths.h"
#include "Styling/CoreStyle.h"

namespace SpaceHudStyle
{
	/**
	 * The reference's instruments are yellow-green on near-black, labels near-white, the reserve red;
	 * cyan belongs to the canopy frame lines, not to the readouts. Ours was cyan with amber states,
	 * which is what read as orange.
	 */
	const FLinearColor Green(0.62f, 0.95f, 0.28f, 0.95f);
	const FLinearColor GreenBright(0.80f, 1.f, 0.45f, 1.f);
	const FLinearColor Label(0.86f, 0.93f, 0.90f, 0.95f);
	/** Tube outlines and ticks: thin cool white, as on the reference's gauges. */
	const FLinearColor Rail(0.78f, 0.88f, 0.90f, 0.50f);
	/** Frames and the virtual joystick only. */
	const FLinearColor Cyan(0.30f, 0.88f, 1.f, 0.85f);
	const FLinearColor CyanFaint(0.30f, 0.88f, 1.f, 0.40f);
	const FLinearColor LampOff(0.55f, 0.65f, 0.65f, 0.18f);
	/** Behind pills and inside bar tubes: this is why the reference still reads over bright ground. */
	const FLinearColor Backing(0.02f, 0.04f, 0.04f, 0.62f);
	/** Caution only (G-Safe suspended by boost), never a whole bar. */
	const FLinearColor Amber(1.f, 0.78f, 0.25f, 0.95f);
	const FLinearColor Red(0.95f, 0.26f, 0.18f, 0.95f);
	const FLinearColor NavBlue(0.55f, 0.85f, 1.f, 0.95f);

	/**
	 * The HUD's own faces, after the reference's instrument type: Rajdhani SemiBold for labels
	 * (squarish condensed technical sans) and Share Tech Mono for the numbers, where a fixed width
	 * keeps digits from dancing as speed changes. Both are SIL OFL 1.1, in Content/UI/Fonts with
	 * their licences, staged into the pak by DirectoriesToAlwaysStageAsUFS.
	 *
	 * They are loaded from the file rather than imported as Font assets: the font importer needs a
	 * Slate application, which the headless editor this project scripts with does not have. Each
	 * falls back to an engine face if its file is ever missing, so the HUD never loses its text.
	 */
	FSlateFontInfo ProjectFont(const TCHAR* FileName, const FName Fallback, float Size)
	{
		const FString Path = FPaths::ProjectContentDir() / TEXT("UI/Fonts") / FileName;
		return FPaths::FileExists(Path) ? FSlateFontInfo(Path, Size) : FCoreStyle::GetDefaultFontStyle(Fallback, Size);
	}

	/** Labels, switch pills, gauge titles. */
	FSlateFontInfo LabelFont(float Size)
	{
		return ProjectFont(TEXT("Rajdhani-SemiBold.ttf"), TEXT("Bold"), Size);
	}

	/** Speed, G load, percentages. */
	FSlateFontInfo NumberFont(float Size)
	{
		return ProjectFont(TEXT("ShareTechMono-Regular.ttf"), TEXT("Mono"), Size);
	}

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
	 * the same shape drawn again, larger and much fainter. Two passes read as a halo at HUD line
	 * widths and cost two draw calls.
	 */
	void GlowLines(FSlateWindowElementList& Out, int32 Layer, const FPaintGeometry& Geometry, const TArray<FVector2f>& Points,
		const FLinearColor& Color, float Thickness, float Glow)
	{
		if (Glow > 0.01f)
		{
			FSlateDrawElement::MakeLines(Out, Layer, Geometry, Points, ESlateDrawEffect::None, Faded(Color, 0.06f * Glow), true, Thickness + 6.f);
			FSlateDrawElement::MakeLines(Out, Layer, Geometry, Points, ESlateDrawEffect::None, Faded(Color, 0.14f * Glow), true, Thickness + 2.5f);
		}
		FSlateDrawElement::MakeLines(Out, Layer, Geometry, Points, ESlateDrawEffect::None, Color, true, Thickness);
	}

	/**
	 * A rounded rectangle: the reference draws every bar as a capsule and every switch as a pill.
	 * Fill and outline go in as the draw tint over a white brush - a colour set on the brush itself is
	 * overridden by the tint, which is what made the first pass render solid white panels.
	 */
	void RoundedBox(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geometry, const FVector2f& Position, const FVector2f& Size,
		float Radius, const FLinearColor& Fill, const FLinearColor& Outline = FLinearColor::Transparent, float OutlineWidth = 0.f)
	{
		if (Size.X <= 0.f || Size.Y <= 0.f)
		{
			return;
		}
		const float Corner = FMath::Min(Radius, FMath::Min(Size.X, Size.Y) * 0.5f);
		const FPaintGeometry PaintGeometry = Geometry.ToPaintGeometry(Size, FSlateLayoutTransform(Position));
		if (Fill.A > 0.f)
		{
			const FSlateRoundedBoxBrush FillBrush(FLinearColor::White, Corner, Size);
			FSlateDrawElement::MakeBox(Out, Layer, PaintGeometry, &FillBrush, ESlateDrawEffect::None, Fill);
		}
		if (OutlineWidth > 0.f && Outline.A > 0.f)
		{
			const FSlateRoundedBoxBrush OutlineBrush(FLinearColor::Transparent, Corner, FLinearColor::White, OutlineWidth, Size);
			FSlateDrawElement::MakeBox(Out, Layer, PaintGeometry, &OutlineBrush, ESlateDrawEffect::None, Outline);
		}
	}

	/** Halo around a rounded shape: the same capsule twice, inflated and very faint. */
	void GlowRounded(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geometry, const FVector2f& Position, const FVector2f& Size,
		float Radius, const FLinearColor& Color, float Glow)
	{
		if (Glow <= 0.01f)
		{
			return;
		}
		for (const TPair<float, float>& Pass : { TPair<float, float>(5.f, 0.05f), TPair<float, float>(2.f, 0.11f) })
		{
			const FVector2f Grow(Pass.Key, Pass.Key);
			RoundedBox(Out, Layer, Geometry, Position - Grow, Size + Grow * 2.f, Radius + Pass.Key, Faded(Color, Pass.Value * Glow));
		}
	}

	/**
	 * A bar fill the way the reference draws it: bright at the leading edge, deeper at the root, with
	 * rounded ends. A flat single colour is what made ours look like a progress bar.
	 */
	void GradientCapsule(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geometry, const FVector2f& Position, const FVector2f& Size,
		float Radius, const FLinearColor& Root, const FLinearColor& Edge, bool bVertical)
	{
		if (Size.X <= 0.f || Size.Y <= 0.f)
		{
			return;
		}
		TArray<FSlateGradientStop> Stops;
		// Vertical bars fill upwards, so the bright edge is at the top (stop 0 is the left/top).
		Stops.Add(FSlateGradientStop(FVector2f(0.f, 0.f), bVertical ? Edge : Root));
		Stops.Add(FSlateGradientStop(bVertical ? FVector2f(0.f, Size.Y * 0.55f) : FVector2f(Size.X * 0.45f, 0.f), FMath::Lerp(Root, Edge, 0.35f)));
		Stops.Add(FSlateGradientStop(bVertical ? FVector2f(0.f, Size.Y) : FVector2f(Size.X, 0.f), bVertical ? Root : Edge));
		const float Corner = FMath::Min(Radius, FMath::Min(Size.X, Size.Y) * 0.5f);
		FSlateDrawElement::MakeGradient(Out, Layer, Geometry.ToPaintGeometry(Size, FSlateLayoutTransform(Position)), MoveTemp(Stops),
			bVertical ? Orient_Horizontal : Orient_Vertical, ESlateDrawEffect::None, FVector4f(Corner, Corner, Corner, Corner));
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
	if (Size.X < 4.f || Size.Y < 4.f)
	{
		return LayerId;
	}
	// The reference frames a group with short corner brackets, not with a filled panel: the view stays
	// clear and the HUD reads as projected glass rather than as a window.
	const float Arm = FMath::Min(14.f, FMath::Min(Size.X, Size.Y) * 0.35f);
	const float Cut = FMath::Min(Chamfer, Arm * 0.7f);
	if (FillAlpha > 0.f)
	{
		RoundedBox(OutDrawElements, LayerId, AllottedGeometry, FVector2f::ZeroVector, Size, 3.f, FLinearColor(0.03f, 0.09f, 0.13f, FillAlpha));
	}
	auto Bracket = [&](const FVector2f& Corner, float DirX, float DirY)
	{
		const TArray<FVector2f> Points = {
			Corner + FVector2f(DirX * Arm, 0.f),
			Corner + FVector2f(DirX * Cut, 0.f),
			Corner + FVector2f(0.f, DirY * Cut),
			Corner + FVector2f(0.f, DirY * Arm) };
		GlowLines(OutDrawElements, LayerId + 1, AllottedGeometry.ToPaintGeometry(), Points, LineColor, 1.2f, Glow);
	};
	Bracket(FVector2f(0.f, 0.f), 1.f, 1.f);
	Bracket(FVector2f(Size.X, 0.f), -1.f, 1.f);
	Bracket(FVector2f(0.f, Size.Y), 1.f, -1.f);
	Bracket(FVector2f(Size.X, Size.Y), -1.f, -1.f);
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

void USpaceHudGauge::Advance(float DeltaSeconds)
{
	// The bar springs after the number instead of tracking it exactly: a fast change reads as motion,
	// a steady value still settles precisely.
	const float Rate = 1.f - FMath::Exp(-11.f * DeltaSeconds);
	Display += (Value - Display) * Rate;
	DisplayReverse += (ReverseValue - DisplayReverse) * Rate;
	if (FMath::Abs(Value - Display) < 0.0015f)
	{
		Display = Value;
	}
	if (FMath::Abs(ReverseValue - DisplayReverse) < 0.0015f)
	{
		DisplayReverse = ReverseValue;
	}
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
	if (Size.X < 4.f || Size.Y < 4.f)
	{
		return LayerId;
	}
	// In the reference a switch is a pill around its label (ESP, CPLD, LOCK), lit by its outline and
	// a faint inner fill, not a square block beside the text.
	// The reference's switch: a dark box with a thin cool-white edge, its label in near-white and a
	// small square lamp inside on the right. The box keeps its colour; the square carries the state.
	const float Lit = FMath::Clamp(Intensity + 0.6f * Flash * Intensity, 0.f, 1.5f);
	const float Breath = FMath::Lerp(1.f, Pulse, FMath::Min(Lit, 1.f));
	const float Radius = FMath::Min(Size.Y * 0.35f, 4.f);
	RoundedBox(OutDrawElements, LayerId, AllottedGeometry, FVector2f::ZeroVector, Size, Radius,
		Backing, FMath::Lerp(Faded(Rail, 0.5f), Rail, FMath::Min(Lit, 1.f)), 1.f);

	const float Square = FMath::Clamp(Size.Y - 8.f, 3.f, 6.f);
	const FVector2f At(Size.X - Square - 4.f, (Size.Y - Square) * 0.5f);
	GlowRounded(OutDrawElements, LayerId + 1, AllottedGeometry, At, FVector2f(Square, Square), 1.f, Color, Lit * 0.9f * Breath);
	RoundedBox(OutDrawElements, LayerId + 2, AllottedGeometry, At, FVector2f(Square, Square), 1.f,
		FMath::Lerp(LampOff, Color, FMath::Min(Lit, 1.f)));
	return LayerId + 3;
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
	const float Length = bHorizontal ? Size.X : Size.Y;
	const float Width = bHorizontal ? Size.Y : Size.X;
	if (Length <= 2.f || Width <= 2.f)
	{
		return LayerId;
	}
	const float Dim = bDim ? 0.4f : 1.f;
	const float Radius = Width * 0.5f;
	// Along the gauge: 0 at the low end. Vertical bars grow upwards, horizontal ones to the right.
	auto Place = [&](float Along0, float Along1) -> TPair<FVector2f, FVector2f>
	{
		return bHorizontal
			? TPair<FVector2f, FVector2f>(FVector2f(Along0, 0.f), FVector2f(Along1 - Along0, Width))
			: TPair<FVector2f, FVector2f>(FVector2f(0.f, Length - Along1), FVector2f(Width, Along1 - Along0));
	};

	const float Zero = Length * FMath::Clamp(ReverseZone, 0.f, 0.9f);
	const float Span = Length - Zero;

	/** The fill is not solid in the reference: it is a stack of thin rungs inside the tube. */
	auto Rungs = [&](float Along0, float Along1)
	{
		for (float At = Along0 + 4.f; At < Along1 - 1.f; At += 4.f)
		{
			const TArray<FVector2f> Line = bHorizontal
				? TArray<FVector2f>({ FVector2f(At, 1.f), FVector2f(At, Width - 1.f) })
				: TArray<FVector2f>({ FVector2f(1.f, Length - At), FVector2f(Width - 1.f, Length - At) });
			FSlateDrawElement::MakeLines(OutDrawElements, LayerId + 3, AllottedGeometry.ToPaintGeometry(), Line,
				ESlateDrawEffect::None, Faded(Backing, 0.6f * Dim), false, 1.f);
		}
	};

	// The tube: a thin capsule outline with an almost black inside, like the reference's bars.
	RoundedBox(OutDrawElements, LayerId, AllottedGeometry, FVector2f::ZeroVector, Size, Radius,
		Faded(Backing, Dim), Faded(Rail, Dim), 1.f);

	// Ticks up the outside, as on the reference's gauges.
	if (!bHorizontal && Ticks > 1)
	{
		for (int32 Index = 1; Index < Ticks; ++Index)
		{
			const float Along = Zero + Span * Index / Ticks;
			const TArray<FVector2f> Tick = { FVector2f(-4.f, Length - Along), FVector2f(-1.f, Length - Along) };
			FSlateDrawElement::MakeLines(OutDrawElements, LayerId + 1, AllottedGeometry.ToPaintGeometry(), Tick,
				ESlateDrawEffect::None, Faded(Rail, (Index * 2 == Ticks ? 0.9f : 0.5f) * Dim), true, 1.f);
		}
	}

	// Reverse zone (flying backwards): a red root, as the reference marks its reserve.
	if (Zero > 1.f)
	{
		const TPair<FVector2f, FVector2f> Band = Place(0.f, Zero);
		RoundedBox(OutDrawElements, LayerId + 1, AllottedGeometry, Band.Key, Band.Value, Radius, Faded(Red, 0.16f * Dim));
	}

	// The fill: bright at the leading edge, deeper at the root, with a halo.
	const float Top = Zero + Span * FMath::Clamp(Display, 0.f, 1.f);
	if (Top > Zero + 1.f)
	{
		// Past the marker (over the speed limiter) the rest of the fill goes red, the way the
		// reference marks the part of a gauge that is outside its allowed range.
		const float Allowed = Marker >= 0.f ? FMath::Min(Top, Zero + Span * FMath::Clamp(Marker, 0.f, 1.f)) : Top;
		const TPair<FVector2f, FVector2f> Fill = Place(Zero, Allowed);
		GlowRounded(OutDrawElements, LayerId + 1, AllottedGeometry, Fill.Key, Fill.Value, Radius, FillColor, Dim * Pulse);
		GradientCapsule(OutDrawElements, LayerId + 2, AllottedGeometry, Fill.Key, Fill.Value, Radius,
			Faded(FillColor, 0.85f * Dim), Faded(FMath::Lerp(FillColor, FLinearColor::White, 0.22f), Dim), !bHorizontal);
		Rungs(Zero, Allowed);
		if (Top > Allowed + 1.f)
		{
			const TPair<FVector2f, FVector2f> Over = Place(Allowed, Top);
			GlowRounded(OutDrawElements, LayerId + 1, AllottedGeometry, Over.Key, Over.Value, Radius, Red, Dim * Pulse);
			GradientCapsule(OutDrawElements, LayerId + 2, AllottedGeometry, Over.Key, Over.Value, Radius,
				Faded(Red, 0.85f * Dim), Faded(FMath::Lerp(Red, FLinearColor::White, 0.2f), Dim), !bHorizontal);
			Rungs(Allowed, Top);
		}
	}
	const float Bottom = Zero * (1.f - FMath::Clamp(DisplayReverse, 0.f, 1.f));
	if (Bottom < Zero - 1.f)
	{
		const TPair<FVector2f, FVector2f> Fill = Place(Bottom, Zero);
		GlowRounded(OutDrawElements, LayerId + 1, AllottedGeometry, Fill.Key, Fill.Value, Radius, Red, Dim);
		GradientCapsule(OutDrawElements, LayerId + 2, AllottedGeometry, Fill.Key, Fill.Value, Radius,
			Faded(Red, 0.9f * Dim), Faded(FMath::Lerp(Red, FLinearColor::White, 0.2f), Dim), !bHorizontal);
		Rungs(Bottom, Zero);
	}

	// The handle: the reference hangs the limiter off the tube as a short bar with a nub.
	if (Marker >= 0.f)
	{
		const float Along = Zero + Span * FMath::Clamp(Marker, 0.f, 1.f);
		const float Reach = Width * 1.7f;
		const TArray<FVector2f> Bar = bHorizontal
			? TArray<FVector2f>({ FVector2f(Along, -Reach * 0.6f), FVector2f(Along, Width + Reach * 0.6f) })
			: TArray<FVector2f>({ FVector2f(-Reach * 0.2f, Length - Along), FVector2f(Width + Reach, Length - Along) });
		GlowLines(OutDrawElements, LayerId + 4, AllottedGeometry.ToPaintGeometry(), Bar, MarkerColor, 1.4f, 0.7f * Dim);
		const FVector2f Nub(3.f, 3.f);
		const FVector2f NubAt = bHorizontal
			? FVector2f(Along - Nub.X * 0.5f, Width + Reach * 0.6f - Nub.Y)
			: FVector2f(Width + Reach - Nub.X, Length - Along - Nub.Y * 0.5f);
		RoundedBox(OutDrawElements, LayerId + 4, AllottedGeometry, NubAt, Nub, 1.f, Faded(MarkerColor, Dim));
	}
	return LayerId + 5;
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
	// "Label" and "Number" are the HUD's own faces from Content/UI/Fonts; anything else is Slate's own.
	FSlateFontInfo Font = Weight == FName(TEXT("Label")) ? SpaceHudStyle::LabelFont(Size)
		: Weight == FName(TEXT("Number")) ? SpaceHudStyle::NumberFont(Size)
		: FCoreStyle::GetDefaultFontStyle(Weight, Size);
	Font.LetterSpacing = LetterSpacing;
	// A thin dark outline instead of a drop shadow: readable against the sun and a bright planet
	// from every side.
	Font.OutlineSettings.OutlineSize = 1;
	Font.OutlineSettings.OutlineColor = FLinearColor(0.f, 0.02f, 0.04f, 0.95f);
	Text->SetFont(Font);
	Text->SetColorAndOpacity(FSlateColor(Weight == FName(TEXT("Number")) ? SpaceHudStyle::Green : SpaceHudStyle::Label));
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
		Panel->LineColor = SpaceHudStyle::Cyan;
		Panel->FillAlpha = 0.f;
		Panel->Glow = 0.35f;
		if (UOverlaySlot* PanelSlot = Overlay->AddChildToOverlay(Panel))
		{
			PanelSlot->SetHorizontalAlignment(HAlign_Fill);
			PanelSlot->SetVerticalAlignment(VAlign_Fill);
		}
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
		Panel->Chamfer = 3.f;
		Panel->Glow = 0.25f;
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
		UTextBlock* LampText = MakeText(FName(*FString::Printf(TEXT("LampLabel_%s"), LampName)), 9.f, 120, TEXT("Label"));
		LampText->SetText(FText::FromString(LampName));
		LampText->SetJustification(ETextJustify::Center);
		LampLabels.Add(Key, LampText);
		UOverlay* Pill = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass(), FName(*FString::Printf(TEXT("Pill_%s"), LampName)));
		if (UOverlaySlot* LampSlot = Pill->AddChildToOverlay(Lamp(FName(*FString::Printf(TEXT("Lamp_%s"), LampName)))))
		{
			LampSlot->SetHorizontalAlignment(HAlign_Fill);
			LampSlot->SetVerticalAlignment(VAlign_Fill);
		}
		if (UOverlaySlot* LabelSlot = Pill->AddChildToOverlay(LampText))
		{
			LabelSlot->SetPadding(FMargin(7.f, 2.f, 15.f, 3.f));
			LabelSlot->SetHorizontalAlignment(HAlign_Center);
			LabelSlot->SetVerticalAlignment(VAlign_Center);
		}
		AddToHorizontal(Row, Pill, VAlign_Center, FMargin(0.f));
		AddToVertical(LampBox, Row, HAlign_Right, FMargin(0.f, 0.f, 0.f, 5.f));
	}
	AddToVertical(LeftContent, Panelled(TEXT("LampPanel"), LampBox, FMargin(10.f, 8.f, 10.f, 3.f)), HAlign_Right, FMargin(0.f, 0.f, 0.f, 10.f));
	UVerticalBox* SpeedBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("SpeedBox"));
	AddToVertical(SpeedBox, Sized(TEXT("SpeedGaugeBox"), Gauge(TEXT("SpeedGauge"), false, 10), 11.f, 230.f), HAlign_Center, FMargin(0.f, 0.f, 0.f, 10.f));
	AddToVertical(SpeedBox, MakeText(TEXT("SpeedText"), 15.f, 20, TEXT("Number")), HAlign_Center, FMargin(0.f, 0.f, 0.f, 1.f));
	AddToVertical(SpeedBox, MakeText(TEXT("LimitText"), 9.f, 40, TEXT("Number")), HAlign_Center, FMargin(0.f, 0.f, 0.f, 8.f));
	UHorizontalBox* GRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("GRow"));
	AddToHorizontal(GRow, Sized(TEXT("GGaugeBox"), Gauge(TEXT("GGauge"), true, 4), 52.f, 6.f), VAlign_Center, FMargin(0.f, 0.f, 8.f, 0.f));
	AddToHorizontal(GRow, MakeText(TEXT("GText"), 11.f, 20, TEXT("Number")), VAlign_Center, FMargin(0.f));
	AddToVertical(SpeedBox, GRow, HAlign_Right, FMargin(0.f));
	AddToVertical(LeftContent, Panelled(TEXT("SpeedPanel"), SpeedBox, FMargin(12.f, 10.f)), HAlign_Right, FMargin(0.f));
	AddToHorizontal(Left, LeftContent, VAlign_Center, FMargin(0.f, 0.f, 14.f, 0.f));
	// The glass frame line beside the cluster, cut at both ends like the reference's canopy frame.
	AddToHorizontal(Left, Sized(TEXT("FrameLeftBox"), Frame(TEXT("FrameLeft")), 10.f, FrameHeight), VAlign_Center, FMargin(0.f));
	Place(Left, FVector2D(-250.0, 20.0), FVector2D(1.0, 0.5));

	// --- Right of centre: a frame line, then boost energy and afterburner fuel gauges ----------
	UHorizontalBox* Right = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("RightCluster"));
	AddToHorizontal(Right, Sized(TEXT("FrameRightBox"), Frame(TEXT("FrameRight")), 10.f, FrameHeight), VAlign_Center, FMargin(0.f, 0.f, 14.f, 0.f));
	UHorizontalBox* Columns = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("RightColumns"));
	auto Column = [&](const TCHAR* Caption, const FName GaugeName, const FName TextName, const FMargin& SlotPadding)
	{
		UVerticalBox* Box = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), FName(*FString::Printf(TEXT("%sColumn"), *GaugeName.ToString())));
		UTextBlock* Title = MakeText(FName(*FString::Printf(TEXT("%sTitle"), *GaugeName.ToString())), 8.f, 160, TEXT("Label"));
		Title->SetText(FText::FromString(Caption));
		AddToVertical(Box, Title, HAlign_Center, FMargin(0.f, 0.f, 0.f, 6.f));
		AddToVertical(Box, Sized(FName(*FString::Printf(TEXT("%sBox"), *GaugeName.ToString())), Gauge(GaugeName, false, 5), 9.f, 180.f), HAlign_Center, FMargin(0.f, 0.f, 0.f, 8.f));
		AddToVertical(Box, MakeText(TextName, 9.f, 20, TEXT("Number")), HAlign_Center, FMargin(0.f));
		AddToHorizontal(Columns, Box, VAlign_Center, SlotPadding);
	};
	Column(TEXT("BST"), TEXT("BoostGauge"), TEXT("BoostText"), FMargin(0.f, 0.f, 22.f, 0.f));
	Column(TEXT("AB"), TEXT("AfterburnerGauge"), TEXT("AfterburnerText"), FMargin(0.f));
	AddToHorizontal(Right, Panelled(TEXT("PowerPanel"), Columns, FMargin(14.f, 10.f)), VAlign_Center, FMargin(0.f));
	Place(Right, FVector2D(250.0, 20.0), FVector2D(0.0, 0.5));

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
		if (UTextBlock* LabelText = LampLabels.FindRef(Name))
		{
			LabelText->SetColorAndOpacity(FSlateColor(bLit ? Label : Faded(Label, 0.45f)));
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
	SetLamp(TEXT("MODE"), !State.bModeSwitching || bBlink, State.ModeLabel == TEXT("NAV") ? NavBlue : Green);
	if (UTextBlock* CoupledLabel = LampLabels.FindRef(TEXT("CPLD")))
	{
		CoupledLabel->SetText(FText::FromString(State.bSpaceBrake ? TEXT("BRAKE") : TEXT("CPLD")));
	}
	SetLamp(TEXT("CPLD"), State.bCoupled || State.bSpaceBrake, State.bSpaceBrake ? Red : Green);
	// G-Safe switched on but suspended by boost: amber.
	SetLamp(TEXT("GSAF"), State.bGSafeOn, State.bGSafeActive ? Green : Amber);
	SetLamp(TEXT("CSTB"), State.bComStab, Green);
	SetLamp(TEXT("BOOST"), State.bBoostActive, GreenBright);

	// --- Speed gauge, speed, limit -------------------------------------------------------------
	if (USpaceHudGauge* Speed = Gauges.FindRef(TEXT("SpeedGauge")))
	{
		Speed->ReverseZone = SpeedReverseZone;
		Speed->Value = State.SpeedFraction;
		Speed->ReverseValue = State.ReverseFraction;
		Speed->Marker = State.LimiterFraction;
		Speed->MarkerColor = Label;
		Speed->FillColor = State.bAfterburnerActive ? GreenBright : Green;
	}
	SetText(TEXT("SpeedText"), SpaceHudStyle::Speed(State.SpeedCmS), State.ForwardSpeedCmS < -50.f ? Red : Green);
	SetText(TEXT("LimitText"), FString::Printf(TEXT("LIM %s  %3.0f%%"), *SpaceHudStyle::Speed(State.SpeedLimitCmS), State.LimiterFraction * 100.f),
		Faded(Label, 0.75f));

	// --- G meter ------------------------------------------------------------------------------
	const FLinearColor GColor = State.GForce > State.GSafeMaxG + 0.05f ? Red : State.GForce > State.GSafeMaxG * 0.7f ? Amber : Green;
	if (USpaceHudGauge* GGauge = Gauges.FindRef(TEXT("GGauge")))
	{
		GGauge->Value = State.GForce / GMeterRangeG;
		GGauge->FillColor = GColor;
		// The G-Safe limit as a mark, while G-Safe is actually limiting.
		GGauge->Marker = State.bGSafeActive ? State.GSafeMaxG / GMeterRangeG : -1.f;
		GGauge->MarkerColor = Faded(Label, 0.8f);
	}
	SetText(TEXT("GText"), FString::Printf(TEXT("%.1f G"), State.GForce), GColor);

	// --- Boost and afterburner ---------------------------------------------------------------------
	if (USpaceHudGauge* Boost = Gauges.FindRef(TEXT("BoostGauge")))
	{
		Boost->Value = State.BoostEnergy;
		Boost->ReverseZone = 0.f;
		Boost->FillColor = State.bBoostLocked || State.BoostEnergy < 0.25f ? Red : State.bBoostActive ? GreenBright : Green;
	}
	SetText(TEXT("BoostText"), FString::Printf(TEXT("%.0f%%"), State.BoostEnergy * 100.f),
		State.bBoostLocked ? Red : State.bBoostActive ? GreenBright : Green);

	if (USpaceHudGauge* Afterburner = Gauges.FindRef(TEXT("AfterburnerGauge")))
	{
		Afterburner->Value = State.AfterburnerFuel;
		Afterburner->bDim = !State.bAfterburnerAvailable;
		Afterburner->FillColor = State.bAfterburnerLocked || State.AfterburnerFuel < 0.25f ? Red
			: State.bAfterburnerActive ? GreenBright : Green;
	}
	FString AfterburnerText = FString::Printf(TEXT("%.0f%%"), State.AfterburnerFuel * 100.f);
	FLinearColor AfterburnerColor = Green;
	if (!State.bAfterburnerAvailable)
	{
		AfterburnerText += TEXT(" SCM");
		AfterburnerColor = Faded(Label, 0.45f);
	}
	else if (State.bAfterburnerLocked)
	{
		AfterburnerText += TEXT(" DRY");
		AfterburnerColor = Red;
	}
	else if (State.bAfterburnerActive)
	{
		AfterburnerText += TEXT(" BURN");
		AfterburnerColor = GreenBright;
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
	// One clock for every animation, advanced here so tests can step it without Slate.
	Time += Seconds;
	// A slow, shallow breath: at 0.55 Hz and 8 % it is felt rather than seen, which is the point.
	const float Breath = 1.f + 0.08f * FMath::Sin(Time * 0.55f * UE_TWO_PI);
	for (const TPair<FName, TObjectPtr<USpaceHudLamp>>& Pair : Lamps)
	{
		if (Pair.Value)
		{
			Pair.Value->Pulse = Breath;
			Pair.Value->Advance(Seconds);
		}
	}
	for (const TPair<FName, TObjectPtr<USpaceHudGauge>>& Pair : Gauges)
	{
		if (Pair.Value)
		{
			Pair.Value->Pulse = Breath;
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
