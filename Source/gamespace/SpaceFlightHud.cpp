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
#include "Components/WidgetSwitcher.h"
#include "HAL/IConsoleManager.h"
#include "Rendering/DrawElements.h"
#include "SpaceshipPawn.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "Styling/CoreStyle.h"
#include "Components/CanvasPanelSlot.h"
#include "Framework/Application/SlateApplication.h"
#include "Fonts/FontMeasure.h"
#include "Rendering/SlateRenderer.h"
#include "Camera/PlayerCameraManager.h"
#include "GameFramework/PlayerController.h"
#include "CelestialBody.h"
#include "Components/StaticMeshComponent.h"
#include "DistantBody.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "EngineUtils.h"
#include "PhysicsEngine/BodySetup.h"
#include "Stats/Stats.h"

// "stat SpaceHud": the drawn instruments' paint.
DECLARE_STATS_GROUP(TEXT("SpaceHud"), STATGROUP_SpaceHud, STATCAT_Advanced);
DECLARE_CYCLE_STAT(TEXT("Radar paint"), STAT_SpaceHudRadarPaint, STATGROUP_SpaceHud);
DECLARE_CYCLE_STAT(TEXT("Ship status paint"), STAT_SpaceHudShipPaint, STATGROUP_SpaceHud);
DECLARE_CYCLE_STAT(TEXT("Symbol paint"), STAT_SpaceHudSymbolPaint, STATGROUP_SpaceHud);
DECLARE_CYCLE_STAT(TEXT("Painted text"), STAT_SpaceHudText, STATGROUP_SpaceHud);

namespace SpaceHudStyle
{
	/**
	 * After the current Star Citizen HUD (Docs/UI/Screenshot 2026-09-17 201854.png and 201804.png):
	 * ice-cyan instruments and near-white text with a faint glow, red for the reserve and reverse
	 * zones and the strafe arrows, orange for the turn rate. (SC-1c followed an older reference in
	 * yellow-green.)
	 */
	const FLinearColor Instrument(0.45f, 0.85f, 1.f, 0.95f);
	const FLinearColor InstrumentBright(0.75f, 0.95f, 1.f, 1.f);
	const FLinearColor Label(0.85f, 0.92f, 1.f, 0.92f);
	/** Tube outlines and ticks: thin cool white, as on the reference's gauges. */
	const FLinearColor Rail(0.75f, 0.87f, 1.f, 0.50f);
	/** Frames and the virtual joystick only. */
	const FLinearColor Cyan(0.30f, 0.88f, 1.f, 0.85f);
	const FLinearColor CyanFaint(0.30f, 0.88f, 1.f, 0.40f);
	const FLinearColor LampOff(0.55f, 0.65f, 0.75f, 0.18f);
	/** Behind pills and inside bar tubes: this is why the reference still reads over bright ground. */
	const FLinearColor Backing(0.01f, 0.03f, 0.05f, 0.55f);
	/** Caution only (G-Safe suspended by boost), never a whole bar. */
	const FLinearColor Amber(1.f, 0.78f, 0.25f, 0.95f);
	const FLinearColor Red(1.f, 0.33f, 0.24f, 0.95f);
	/** The gyro's turn-rate line. */
	const FLinearColor Orange(1.f, 0.55f, 0.25f, 0.95f);
	const FLinearColor NavBlue(0.65f, 0.75f, 1.f, 0.95f);

	/**
	 * The HUD's own faces, after the reference's instrument type: Rajdhani Medium for labels
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

	/**
	 * The player's own face for every HUD and display text: the first .ttf or .otf (by name) in
	 * Content/UI/Fonts/Custom, empty if there is none. That folder is not in git: a font dropped there
	 * may be one that must not be redistributed, and the repository is on GitHub.
	 */
	const FString& CustomFont()
	{
		static const FString Path = []()
		{
			const FString Folder = FPaths::ProjectContentDir() / TEXT("UI/Fonts/Custom");
			TArray<FString> Found;
			IFileManager::Get().FindFiles(Found, *(Folder / TEXT("*.ttf")), true, false);
			IFileManager::Get().FindFiles(Found, *(Folder / TEXT("*.otf")), true, false);
			Found.Sort();
			return Found.Num() > 0 ? Folder / Found[0] : FString();
		}();
		return Path;
	}

	/** Labels, switch pills, gauge titles. */
	FSlateFontInfo LabelFont(float Size)
	{
		return !CustomFont().IsEmpty() ? FSlateFontInfo(CustomFont(), Size) : ProjectFont(TEXT("Rajdhani-Medium.ttf"), TEXT("Regular"), Size);
	}

	/** Speed, G load, percentages. */
	FSlateFontInfo NumberFont(float Size)
	{
		return !CustomFont().IsEmpty() ? FSlateFontInfo(CustomFont(), Size) : ProjectFont(TEXT("ShareTechMono-Regular.ttf"), TEXT("Mono"), Size);
	}

	/** The cockpit displays after the reference's MFDs: deep blue glass, blue chrome, near-white text. */
	const FLinearColor MfdGlass(0.004f, 0.01f, 0.03f, 1.f);
	const FLinearColor MfdBlue(0.3f, 0.55f, 1.f, 0.95f);
	const FLinearColor MfdBlueFaint(0.3f, 0.55f, 1.f, 0.3f);
	const FLinearColor MfdText(0.85f, 0.92f, 1.f, 0.95f);

	/** Rows of the navigation page's body list and of the contacts page. */
	constexpr int32 NavRows = 4;
	constexpr int32 ContactRows = 6;

	/** Every line on the centre column's pages (radar, self status): one thickness, so Slate batches them. */
	constexpr float SmallScreenLine = 1.5f;

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
			// Drawn as a line round the shape: a rounded-box brush with a transparent fill still came out
			// filled in the outline colour under a draw tint, which turned every thin tube, badge and
			// switch into a solid light block.
			TArray<FVector2f> Points;
			const FVector2f Corners[] = { FVector2f(Size.X - Corner, Corner), FVector2f(Size.X - Corner, Size.Y - Corner),
				FVector2f(Corner, Size.Y - Corner), FVector2f(Corner, Corner) };
			for (int32 Index = 0; Index < 4; ++Index)
			{
				const float From = -90.f + 90.f * Index;
				for (int32 Step = 0; Step <= 6; ++Step)
				{
					const float Angle = FMath::DegreesToRadians(From + 15.f * Step);
					Points.Add(Position + Corners[Index] + FVector2f(FMath::Cos(Angle), FMath::Sin(Angle)) * Corner);
				}
			}
			const FVector2f Start = Points[0];
			Points.Add(Start);
			FSlateDrawElement::MakeLines(Out, Layer, Geometry.ToPaintGeometry(), Points, ESlateDrawEffect::None, Outline, true, OutlineWidth);
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

	/** Text drawn by a painting widget, placed by Align (0..1 of its own size) at At. */
	void Text(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geometry, const FVector2f& At, const FString& String,
		const FSlateFontInfo& Font, const FLinearColor& Color, const FVector2f& Align = FVector2f(0.5f, 0.5f))
	{
		SCOPE_CYCLE_COUNTER(STAT_SpaceHudText);
		if (!FSlateApplication::IsInitialized() || String.IsEmpty())
		{
			return;
		}
		const FVector2f Size(FSlateApplication::Get().GetRenderer()->GetFontMeasureService()->Measure(String, Font));
		FSlateDrawElement::MakeText(Out, Layer, Geometry.ToPaintGeometry(Size, FSlateLayoutTransform(At - Size * Align)), String, Font,
			ESlateDrawEffect::None, Color);
	}

	/** A closed or open circle as a polyline. */
	TArray<FVector2f> Circle(const FVector2f& Centre, float Radius, float FromDeg = 0.f, float ToDeg = 360.f, int32 Segments = 32)
	{
		TArray<FVector2f> Points;
		for (int32 Index = 0; Index <= Segments; ++Index)
		{
			const float Angle = FMath::DegreesToRadians(FMath::Lerp(FromDeg, ToDeg, float(Index) / Segments));
			Points.Add(Centre + FVector2f(FMath::Cos(Angle), FMath::Sin(Angle)) * Radius);
		}
		return Points;
	}

	/**
	 * Heading (0 = north: the world's Z axis projected on the local horizon, 90 east), pitch and roll of
	 * a frame against the horizon whose up is Up. At the poles north falls back to the world X axis.
	 */
	void Attitude(const FVector& Up, const FVector& Forward, const FVector& Right, const FVector& FrameUp,
		float& OutHeading, float& OutPitch, float& OutRoll)
	{
		FVector North = FVector::UpVector - Up * (FVector::UpVector | Up);
		if (North.SizeSquared() < 1e-4)
		{
			North = FVector::ForwardVector - Up * (FVector::ForwardVector | Up);
		}
		North.Normalize();
		const FVector East = Up ^ North;
		const FVector Flat = Forward - Up * (Forward | Up);
		OutHeading = Flat.SizeSquared() > 1e-8
			? float(FMath::Fmod(FMath::RadiansToDegrees(FMath::Atan2(Flat | East, Flat | North)) + 360.0, 360.0)) : 0.f;
		OutPitch = float(FMath::RadiansToDegrees(FMath::Asin(FMath::Clamp(Forward | Up, -1.0, 1.0))));
		OutRoll = float(FMath::RadiansToDegrees(FMath::Atan2(-(Right | Up), FrameUp | Up)));
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
	if (bButton)
	{
		// The reference's MFD keys: a dark rounded key with a blue rim, lit keys filled and bright.
		const float Lit01 = FMath::Min(Lit, 1.f);
		GlowRounded(OutDrawElements, LayerId, AllottedGeometry, FVector2f::ZeroVector, Size, 6.f, Color, 0.6f * Lit01 * Breath);
		// Off: a dim blue rim whatever the switch's colour; on: a deep fill in its colour, a bright rim.
		const FLinearColor Off(0.3f, 0.55f, 1.f, 0.4f);
		const FLinearColor Deep(Color.R * 0.3f, Color.G * 0.3f, Color.B * 0.3f, 0.9f);
		RoundedBox(OutDrawElements, LayerId + 1, AllottedGeometry, FVector2f::ZeroVector, Size, 6.f,
			FMath::Lerp(FLinearColor(0.02f, 0.05f, 0.1f, 0.9f), Deep, Lit01), FMath::Lerp(Off, Color, Lit01), 1.5f + Lit01);
		return LayerId + 2;
	}
	if (bBadge)
	{
		// The reference's switch badge (ESP, CPLD): a thin outline round the label, in the switch's colour.
		const FLinearColor Edge = FMath::Lerp(Faded(Label, 0.3f), Color, FMath::Min(Lit, 1.f));
		GlowRounded(OutDrawElements, LayerId, AllottedGeometry, FVector2f::ZeroVector, Size, 2.f, Edge, 0.5f * Lit * Breath);
		RoundedBox(OutDrawElements, LayerId + 1, AllottedGeometry, FVector2f::ZeroVector, Size, 2.f, Faded(Backing, 0.5f), Edge, 1.f);
		return LayerId + 2;
	}
	const float Radius = FMath::Min(Size.Y * 0.35f, 4.f);
	RoundedBox(OutDrawElements, LayerId, AllottedGeometry, FVector2f::ZeroVector, Size, Radius,
		Backing, FMath::Lerp(Faded(Rail, 0.5f), Rail, FMath::Min(Lit, 1.f)), 1.f);

	const float Square = FMath::Clamp(Size.Y - 8.f, 3.f, SquareMax);
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

	if (Segments > 0)
	{
		// The reference's power bars: a column of blocks in a thin frame, lit from the bottom.
		const float Gap = 3.f;
		const float Block = (Length - Gap * (Segments + 1)) / Segments;
		const float Lit = FMath::Clamp(Display, 0.f, 1.f) * Segments;
		const int32 MarkerBlock = Marker >= 0.f ? FMath::CeilToInt32(FMath::Clamp(Marker, 0.f, 1.f) * Segments) : Segments;
		const int32 ReserveBlocks = FMath::CeilToInt32(FMath::Clamp(ReserveZone, 0.f, 1.f) * Segments);
		for (int32 Index = 0; Index < Segments; ++Index)
		{
			const float Along0 = Gap + Index * (Block + Gap);
			const TPair<FVector2f, FVector2f> Box = Place(Along0, Along0 + Block);
			const float Amount = FMath::Clamp(Lit - Index, 0.f, 1.f);
			const FLinearColor Base = Index < ReserveBlocks ? ReserveColor : Index >= MarkerBlock ? Red : FillColor;
			RoundedBox(OutDrawElements, LayerId, AllottedGeometry, Box.Key, Box.Value, 1.5f, Faded(Base, 0.12f * Dim), Faded(Base, 0.25f * Dim), 1.f);
			if (Amount > 0.f)
			{
				const FLinearColor Fill = FMath::Lerp(Base, FLinearColor::White, 0.25f * float(Index) / Segments);
				GlowRounded(OutDrawElements, LayerId + 1, AllottedGeometry, Box.Key, Box.Value, 1.5f, Fill, 0.5f * Amount * Dim * Pulse);
				RoundedBox(OutDrawElements, LayerId + 2, AllottedGeometry, Box.Key, Box.Value, 1.5f, Faded(Fill, (0.35f + 0.6f * Amount) * Dim));
			}
		}
		return LayerId + 3;
	}

	// The fill: bright at the leading edge, deeper at the root, with a halo.
	auto FillPart = [&](float Along0, float Along1, const FLinearColor& Color)
	{
		if (Along1 <= Along0 + 1.f)
		{
			return;
		}
		const TPair<FVector2f, FVector2f> Fill = Place(Along0, Along1);
		GlowRounded(OutDrawElements, LayerId + 1, AllottedGeometry, Fill.Key, Fill.Value, Radius, Color, Dim * Pulse);
		GradientCapsule(OutDrawElements, LayerId + 2, AllottedGeometry, Fill.Key, Fill.Value, Radius,
			Faded(Color, 0.85f * Dim), Faded(FMath::Lerp(Color, FLinearColor::White, 0.22f), Dim), !bHorizontal);
		Rungs(Along0, Along1);
	};
	const float Top = Zero + Span * FMath::Clamp(Display, 0.f, 1.f);
	if (Top > Zero + 1.f)
	{
		// Past the marker (over the speed limiter) the rest of the fill goes red, the way the
		// reference marks the part of a gauge that is outside its allowed range; the reserve at the
		// root is drawn in its own colour.
		const float Allowed = Marker >= 0.f ? FMath::Min(Top, Zero + Span * FMath::Clamp(Marker, 0.f, 1.f)) : Top;
		const float Reserve = Zero + Span * FMath::Clamp(ReserveZone, 0.f, 1.f);
		FillPart(Zero, FMath::Min(Allowed, Reserve), ReserveColor);
		FillPart(FMath::Max(Zero, Reserve), Allowed, FillColor);
		FillPart(Allowed, Top, Red);
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

	// Faint: the reference shows the mouse cursor, hardly a ring.
	Circle(Radius, Faded(CyanFaint, 0.35f));
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
// Symbols
// -------------------------------------------------------------------------------------------

int32 USpaceHudSymbol::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	SCOPE_CYCLE_COUNTER(STAT_SpaceHudSymbolPaint);
	using namespace SpaceHudStyle;
	LayerId = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
	const FVector2f Size = AllottedGeometry.GetLocalSize();
	const FVector2f Centre = Size * 0.5f;
	const float Half = FMath::Min(Size.X, Size.Y) * 0.5f;
	if (Half < 2.f)
	{
		return LayerId;
	}
	const FPaintGeometry Paint = AllottedGeometry.ToPaintGeometry();
	auto Draw = [&](const TArray<FVector2f>& Points, const FLinearColor& InColor, float InThickness, float Glow = 0.5f)
	{
		GlowLines(OutDrawElements, LayerId, Paint, Points, InColor, InThickness, Glow);
	};
	// Screen Y grows downwards; the values' Y grows upwards.
	const FVector2f Flip(1.f, -1.f);
	switch (Symbol)
	{
	case ESpaceHudSymbol::ModeIcon:
	{
		Draw(Circle(Centre, Half - 1.f), Color, Thickness);
		for (int32 Bar = 0; Bar < 4; ++Bar)
		{
			const float X = Centre.X + (Bar - 1.5f) * Half * 0.34f;
			Draw({ FVector2f(X, Centre.Y - Half * 0.42f), FVector2f(X, Centre.Y + Half * 0.42f) }, Color, 1.6f, 0.3f);
		}
		break;
	}
	case ESpaceHudSymbol::Strafe:
	{
		const float Arm = Half - 6.f;
		for (float At = 5.f; At < Arm - 3.f; At += 4.f)
		{
			for (const FVector2f& Dir : { FVector2f(1.f, 0.f), FVector2f(-1.f, 0.f), FVector2f(0.f, 1.f), FVector2f(0.f, -1.f) })
			{
				Draw({ Centre + Dir * At, Centre + Dir * (At + 1.6f) }, Faded(Color, 0.7f), 1.f, 0.f);
			}
		}
		// Arrow heads: dim, lit in the direction the pilot strafes.
		const TPair<FVector2f, float> Heads[] = {
			{ FVector2f(1.f, 0.f), float(Value.X) }, { FVector2f(-1.f, 0.f), float(-Value.X) },
			{ FVector2f(0.f, -1.f), float(Value.Y) }, { FVector2f(0.f, 1.f), float(-Value.Y) } };
		for (const TPair<FVector2f, float>& Head : Heads)
		{
			const FVector2f Tip = Centre + Head.Key * Arm;
			const FVector2f Side(-Head.Key.Y, Head.Key.X);
			const float Lit = FMath::Clamp(Head.Value, 0.f, 1.f);
			Draw({ Tip - Head.Key * 6.f + Side * 5.5f, Tip, Tip - Head.Key * 6.f - Side * 5.5f },
				Faded(Accent, 0.8f + 0.2f * Lit), 1.6f + Lit, 0.5f + Lit);
		}
		const FVector2f Dot = Centre + FVector2f(Value2.X, Value2.Y).GetClampedToMaxSize(1.f) * Flip * (Arm - 6.f);
		RoundedBox(OutDrawElements, LayerId + 1, AllottedGeometry, Dot - FVector2f(2.f, 2.f), FVector2f(4.f, 4.f), 2.f, Color);
		break;
	}
	case ESpaceHudSymbol::Gyro:
	{
		const float Arm = Half - 4.f;
		Draw({ Centre - FVector2f(Arm - 3.f, 0.f), Centre + FVector2f(Arm - 3.f, 0.f) }, Faded(Color, 0.8f), 1.f, 0.2f);
		Draw({ Centre - FVector2f(0.f, Arm - 3.f), Centre + FVector2f(0.f, Arm - 3.f) }, Faded(Color, 0.8f), 1.f, 0.2f);
		for (const FVector2f& Dir : { FVector2f(1.f, 0.f), FVector2f(-1.f, 0.f), FVector2f(0.f, 1.f), FVector2f(0.f, -1.f) })
		{
			Draw(Circle(Centre + Dir * Arm, 2.5f, 0.f, 360.f, 12), Color, 1.f, 0.2f);
		}
		const FVector2f Rate = FVector2f(Value.X, Value.Y).GetClampedToMaxSize(1.f) * Flip * Arm;
		if (Rate.Size() > 1.f)
		{
			Draw({ Centre, Centre + Rate }, Accent, 1.6f, 0.6f);
		}
		RoundedBox(OutDrawElements, LayerId + 1, AllottedGeometry, Centre + Rate - FVector2f(2.f, 2.f), FVector2f(4.f, 4.f), 2.f, Accent);
		break;
	}
	case ESpaceHudSymbol::Shield:
	{
		const TArray<FVector2f> Outline = {
			FVector2f(0.5f, 0.f) * Size, FVector2f(1.f, 0.16f) * Size, FVector2f(0.92f, 0.66f) * Size, FVector2f(0.5f, 1.f) * Size,
			FVector2f(0.08f, 0.66f) * Size, FVector2f(0.f, 0.16f) * Size, FVector2f(0.5f, 0.f) * Size };
		Draw(Outline, Color, 1.2f);
		Text(OutDrawElements, LayerId + 1, AllottedGeometry, Centre + FVector2f(0.f, -0.5f), TEXT("G"), LabelFont(Size.Y * 0.5f), Color);
		break;
	}
	case ESpaceHudSymbol::Ring:
		Draw(Circle(Centre, Half - 1.5f, -60.f, 250.f, 24), Color, 1.4f);
		break;
	case ESpaceHudSymbol::Reticle:
		for (const FVector2f& Dir : { FVector2f(1.f, 0.f), FVector2f(-1.f, 0.f), FVector2f(0.f, 1.f), FVector2f(0.f, -1.f) })
		{
			Draw({ Centre + Dir * 5.f, Centre + Dir * (Half - 2.f) }, Color, 1.4f);
		}
		RoundedBox(OutDrawElements, LayerId + 1, AllottedGeometry, Centre - FVector2f(1.f, 1.f), FVector2f(2.f, 2.f), 1.f, Color);
		break;
	case ESpaceHudSymbol::Plus:
		Draw({ Centre - FVector2f(Half - 1.f, 0.f), Centre + FVector2f(Half - 1.f, 0.f) }, Color, 1.6f);
		Draw({ Centre - FVector2f(0.f, Half - 1.f), Centre + FVector2f(0.f, Half - 1.f) }, Color, 1.6f);
		break;
	case ESpaceHudSymbol::MfdGlass:
	{
		// Deep blue, lighter at the top, like lit glass.
		TArray<FSlateGradientStop> Stops;
		Stops.Add(FSlateGradientStop(FVector2f(0.f, 0.f), FLinearColor(0.035f, 0.08f, 0.18f, 1.f)));
		Stops.Add(FSlateGradientStop(FVector2f(0.f, Size.Y * 0.45f), FLinearColor(0.012f, 0.03f, 0.075f, 1.f)));
		Stops.Add(FSlateGradientStop(FVector2f(0.f, Size.Y), FLinearColor(0.004f, 0.012f, 0.03f, 1.f)));
		FSlateDrawElement::MakeGradient(OutDrawElements, LayerId, AllottedGeometry.ToPaintGeometry(), MoveTemp(Stops), Orient_Horizontal,
			ESlateDrawEffect::None, FVector4f(14.f, 14.f, 14.f, 14.f));
		// A faint pixel grid.
		for (float X = 24.f; X < Size.X; X += 24.f)
		{
			FSlateDrawElement::MakeLines(OutDrawElements, LayerId + 1, Paint, { FVector2f(X, 4.f), FVector2f(X, Size.Y - 4.f) },
				ESlateDrawEffect::None, Faded(Color, 0.035f), false, 1.f);
		}
		for (float Y = 24.f; Y < Size.Y; Y += 24.f)
		{
			FSlateDrawElement::MakeLines(OutDrawElements, LayerId + 1, Paint, { FVector2f(4.f, Y), FVector2f(Size.X - 4.f, Y) },
				ESlateDrawEffect::None, Faded(Color, 0.035f), false, 1.f);
		}
		// Darker towards the edges, as glass set in a bezel.
		const float Edge = 36.f;
		auto Shade = [&](const FVector2f& At, const FVector2f& BoxSize, EOrientation Orientation, bool bDarkFirst)
		{
			TArray<FSlateGradientStop> EdgeStops;
			const FLinearColor Dark(0.f, 0.f, 0.f, 0.55f);
			const FLinearColor Clear(0.f, 0.f, 0.f, 0.f);
			EdgeStops.Add(FSlateGradientStop(FVector2f::ZeroVector, bDarkFirst ? Dark : Clear));
			EdgeStops.Add(FSlateGradientStop(Orientation == Orient_Vertical ? FVector2f(BoxSize.X, 0.f) : FVector2f(0.f, BoxSize.Y), bDarkFirst ? Clear : Dark));
			FSlateDrawElement::MakeGradient(OutDrawElements, LayerId + 2, AllottedGeometry.ToPaintGeometry(BoxSize, FSlateLayoutTransform(At)),
				MoveTemp(EdgeStops), Orientation);
		};
		Shade(FVector2f::ZeroVector, FVector2f(Edge, Size.Y), Orient_Vertical, true);
		Shade(FVector2f(Size.X - Edge, 0.f), FVector2f(Edge, Size.Y), Orient_Vertical, false);
		Shade(FVector2f::ZeroVector, FVector2f(Size.X, Edge), Orient_Horizontal, true);
		Shade(FVector2f(0.f, Size.Y - Edge), FVector2f(Size.X, Edge), Orient_Horizontal, false);
		// A soft reflection across the top of the glass.
		TArray<FSlateGradientStop> Sheen;
		Sheen.Add(FSlateGradientStop(FVector2f::ZeroVector, FLinearColor(0.6f, 0.8f, 1.f, 0.07f)));
		Sheen.Add(FSlateGradientStop(FVector2f(0.f, Size.Y * 0.22f), FLinearColor(0.6f, 0.8f, 1.f, 0.f)));
		FSlateDrawElement::MakeGradient(OutDrawElements, LayerId + 3, AllottedGeometry.ToPaintGeometry(FVector2f(Size.X, Size.Y * 0.22f), FSlateLayoutTransform()),
			MoveTemp(Sheen), Orient_Horizontal, ESlateDrawEffect::None, FVector4f(14.f, 14.f, 0.f, 0.f));
		RoundedBox(OutDrawElements, LayerId + 4, AllottedGeometry, FVector2f(3.f, 3.f), Size - FVector2f(6.f, 6.f), 12.f, FLinearColor::Transparent,
			Faded(Color, 0.4f), 1.5f);
		break;
	}
	case ESpaceHudSymbol::Line:
	{
		TArray<FVector2f> Scaled;
		for (const FVector2D& Point : Points)
		{
			Scaled.Add(FVector2f(Point) * Size);
		}
		if (Scaled.Num() > 1)
		{
			Draw(Scaled, Color, Thickness, 0.3f);
		}
		break;
	}
	}
	return LayerId + 2;
}

// -------------------------------------------------------------------------------------------
// Tapes
// -------------------------------------------------------------------------------------------

FString USpaceHudTape::Format(float InValue) const
{
	float Shown = InValue * LabelScale;
	if (bWrap360)
	{
		Shown = FMath::Fmod(FMath::Fmod(Shown, 360.f) + 360.f, 360.f);
		if (FMath::RoundToInt(Shown) == 360)
		{
			Shown = 0.f;
		}
	}
	return FString::Printf(TEXT("%.*f"), LabelDecimals, Shown);
}

int32 USpaceHudTape::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	using namespace SpaceHudStyle;
	LayerId = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
	const FVector2f Size = AllottedGeometry.GetLocalSize();
	const float Length = bVertical ? Size.Y : Size.X;
	if (Length < 10.f || Span <= 0.f || MajorStep <= 0.f)
	{
		return LayerId;
	}
	const FPaintGeometry Paint = AllottedGeometry.ToPaintGeometry();
	const float PerUnit = Length / Span;
	const float Minor = MajorStep / FMath::Max(MinorPerMajor, 1);
	const float Mark = Length * MarkAt;
	const FSlateFontInfo Small = LabelFont(10.f);
	const float First = FMath::FloorToFloat((Value - Mark / PerUnit) / Minor) * Minor;
	const float Last = Value + (Length - Mark) / PerUnit;
	for (float At = First; At <= Last + Minor * 0.5f; At += Minor)
	{
		// Along the tape from its start (left, or top for the vertical tape, where values are higher).
		const float Along = bVertical ? Mark - (At - Value) * PerUnit : Mark + (At - Value) * PerUnit;
		if (Along < 0.f || Along > Length)
		{
			continue;
		}
		const float Steps = At / MajorStep;
		const bool bMajor = FMath::Abs(Steps - FMath::RoundToFloat(Steps)) < 0.01f;
		const float Tick = bMajor ? 6.f : 3.f;
		if (bVertical)
		{
			FSlateDrawElement::MakeLines(OutDrawElements, LayerId, Paint, { FVector2f(0.f, Along), FVector2f(Tick, Along) },
				ESlateDrawEffect::None, Faded(Color, bMajor ? 0.8f : 0.45f), true, 1.f);
			if (bMajor && FMath::Abs(Along - Mark) > 12.f)
			{
				Text(OutDrawElements, LayerId, AllottedGeometry, FVector2f(12.f, Along), Format(At), Small, Faded(Color, 0.75f), FVector2f(0.f, 0.5f));
			}
		}
		else
		{
			const float Base = 16.f;
			FSlateDrawElement::MakeLines(OutDrawElements, LayerId, Paint, { FVector2f(Along, Base), FVector2f(Along, Base + Tick) },
				ESlateDrawEffect::None, Faded(Color, bMajor ? 0.8f : 0.45f), true, 1.f);
			if (bMajor)
			{
				Text(OutDrawElements, LayerId, AllottedGeometry, FVector2f(Along, Base - 2.f), Format(At), Small, Faded(Color, 0.8f), FVector2f(0.5f, 1.f));
			}
		}
	}
	const FSlateFontInfo Big = LabelFont(12.f);
	if (bVertical)
	{
		// The value in a box at the mark, a caret pointing at it from the ticks.
		const FVector2f BoxAt(4.f, Mark - 8.f);
		const FVector2f BoxSize(Size.X - 6.f, 16.f);
		RoundedBox(OutDrawElements, LayerId + 1, AllottedGeometry, BoxAt, BoxSize, 1.f, Faded(Backing, 0.8f), Color, 1.f);
		Text(OutDrawElements, LayerId + 2, AllottedGeometry, BoxAt + BoxSize * 0.5f, Format(Value), Big, Color);
		GlowLines(OutDrawElements, LayerId + 2, Paint, { FVector2f(-6.f, Mark - 4.f), FVector2f(-2.f, Mark), FVector2f(-6.f, Mark + 4.f) }, Color, 1.2f, 0.4f);
	}
	else
	{
		const float Base = 23.f;
		GlowLines(OutDrawElements, LayerId + 1, Paint, { FVector2f(Mark - 4.f, Base + 4.f), FVector2f(Mark, Base), FVector2f(Mark + 4.f, Base + 4.f) }, Color, 1.4f, 0.5f);
		Text(OutDrawElements, LayerId + 1, AllottedGeometry, FVector2f(Mark, Base + 5.f), Format(Value), Big, Color, FVector2f(0.5f, 0.f));
	}
	return LayerId + 3;
}

// -------------------------------------------------------------------------------------------
// Pitch ladder
// -------------------------------------------------------------------------------------------

FVector2D USpaceHudLadder::LineCentre(float PitchLineDeg, float InPitchDeg, float InRollDeg, float InFovDeg, float ViewWidth)
{
	const double Focal = (ViewWidth * 0.5) / FMath::Tan(FMath::DegreesToRadians(FMath::Clamp(InFovDeg, 10.f, 170.f)) * 0.5);
	const double Offset = FMath::Tan(FMath::DegreesToRadians(FMath::Clamp(PitchLineDeg - InPitchDeg, -85.f, 85.f))) * Focal;
	const double Roll = FMath::DegreesToRadians(InRollDeg);
	// Screen up for the rolled horizon (screen Y grows downwards): banking right turns the world left.
	const FVector2D Up(-FMath::Sin(Roll), -FMath::Cos(Roll));
	return Up * Offset;
}

int32 USpaceHudLadder::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	using namespace SpaceHudStyle;
	LayerId = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
	const FVector2f Size = AllottedGeometry.GetLocalSize();
	if (Size.X < 100.f)
	{
		return LayerId;
	}
	const FPaintGeometry Paint = AllottedGeometry.ToPaintGeometry();
	const FVector2f Centre = Size * 0.5f;
	const float Roll = FMath::DegreesToRadians(RollDeg);
	const FVector2f Right(FMath::Cos(Roll), -FMath::Sin(Roll));
	const FVector2f Up(-FMath::Sin(Roll), -FMath::Cos(Roll));
	const FSlateFontInfo Font = LabelFont(10.f);
	// Only the lines near the nose, as in the reference: the ladder frames the view, it does not fill it.
	for (int32 Line = -90; Line <= 90; Line += 5)
	{
		if (FMath::Abs(Line - PitchDeg) > 7.f)
		{
			continue;
		}
		const FVector2f At = Centre + FVector2f(LineCentre(float(Line), PitchDeg, RollDeg, FovDeg, Size.X));
		if (Line == 0)
		{
			for (const float Side : { -1.f, 1.f })
			{
				GlowLines(OutDrawElements, LayerId, Paint, { At + Right * Side * 95.f, At + Right * Side * 150.f }, Faded(Color, 0.7f), 1.2f, 0.3f);
			}
			continue;
		}
		// A bracket each side: a short stroke with a tick towards the horizon, dashed below it.
		const FVector2f Towards = Line > 0 ? -Up : Up;
		for (const float Side : { -1.f, 1.f })
		{
			const FVector2f Inner = At + Right * Side * 60.f;
			const FVector2f Outer = At + Right * Side * 88.f;
			if (Line > 0)
			{
				GlowLines(OutDrawElements, LayerId, Paint, { Inner, Outer, Outer + Towards * 7.f }, Faded(Color, 0.75f), 1.2f, 0.3f);
			}
			else
			{
				GlowLines(OutDrawElements, LayerId, Paint, { Inner, FMath::Lerp(Inner, Outer, 0.4f) }, Faded(Color, 0.75f), 1.2f, 0.3f);
				GlowLines(OutDrawElements, LayerId, Paint, { FMath::Lerp(Inner, Outer, 0.6f), Outer, Outer + Towards * 7.f }, Faded(Color, 0.75f), 1.2f, 0.3f);
			}
			Text(OutDrawElements, LayerId, AllottedGeometry, Outer + Right * Side * 10.f, FString::FromInt(Line), Font, Faded(Color, 0.75f));
		}
	}
	return LayerId + 1;
}

// -------------------------------------------------------------------------------------------
// Radar
// -------------------------------------------------------------------------------------------

FVector2D USpaceHudRadar::PlotPosition(const FSpaceRadarContact& Contact, float InRangeM)
{
	// A body is only a bearing: on the rim, or nowhere when it is more than 60 degrees above or below the
	// wings - the planet under the ship has no bearing worth showing, even landed on a slope.
	if (Contact.bBody)
	{
		const double Flat = Contact.Position.Size();
		const double Full = FMath::Sqrt(Flat * Flat + double(Contact.HeightM) * Contact.HeightM);
		return Full > 0.0 && Flat / Full >= 0.5 ? Contact.Position / Flat : FVector2D::ZeroVector;
	}
	return Contact.Position / FMath::Max(InRangeM, 1.f);
}

int32 USpaceHudRadar::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	SCOPE_CYCLE_COUNTER(STAT_SpaceHudRadarPaint);
	using namespace SpaceHudStyle;
	LayerId = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
	const FVector2f Size = AllottedGeometry.GetLocalSize();
	const FVector2f Centre = Size * 0.5f;
	const float Radius = FMath::Min(Size.X, Size.Y) * 0.5f - 4.f;
	if (Radius < 10.f)
	{
		return LayerId;
	}
	const FPaintGeometry Paint = AllottedGeometry.ToPaintGeometry();
	// Every line in one thickness and one layer, so that Slate puts them all in one batch. A change of
	// thickness or layer starts a new batch, and every batch re-reserves the window's whole vertex list:
	// drawn with glow passes (three thicknesses a line) over four layers, this page and the self status
	// page cost the displays ~15 ms a frame (19. 9. 2026, Unreal Insights: Slate::AddLineElements).
	const int32 LineLayer = LayerId + 1;
	auto Line = [&](const TArray<FVector2f>& Points, const FLinearColor& InColor)
	{
		FSlateDrawElement::MakeLines(OutDrawElements, LineLayer, Paint, Points, ESlateDrawEffect::None, InColor, true, SmallScreenLine);
	};
	// The disc: a faint fill, the rim, two range rings, the cross and a tick every 30 degrees.
	RoundedBox(OutDrawElements, LayerId, AllottedGeometry, Centre - FVector2f(Radius, Radius), FVector2f(Radius, Radius) * 2.f, Radius,
		Faded(Color, 0.06f));
	Line(Circle(Centre, Radius, 0.f, 360.f, 72), Color);
	for (const float Ring : { 1.f / 3.f, 2.f / 3.f })
	{
		Line(Circle(Centre, Radius * Ring, 0.f, 360.f, 56), Faded(Color, 0.35f));
	}
	Line({ Centre - FVector2f(Radius, 0.f), Centre + FVector2f(Radius, 0.f) }, Faded(Color, 0.22f));
	Line({ Centre - FVector2f(0.f, Radius), Centre + FVector2f(0.f, Radius) }, Faded(Color, 0.22f));
	for (int32 Degrees = 0; Degrees < 360; Degrees += 30)
	{
		const float Angle = FMath::DegreesToRadians(float(Degrees));
		const FVector2f Out(FMath::Sin(Angle), -FMath::Cos(Angle));
		Line({ Centre + Out * Radius, Centre + Out * (Radius - (Degrees % 90 == 0 ? 9.f : 5.f)) }, Faded(Color, 0.8f));
	}
	// The pilot's view ahead (88 degrees), as the reference's radar marks its forward sector.
	for (const float Side : { -1.f, 1.f })
	{
		const float Angle = FMath::DegreesToRadians(44.f) * Side;
		Line({ Centre, Centre + FVector2f(FMath::Sin(Angle), -FMath::Cos(Angle)) * Radius }, Faded(Color, 0.3f));
	}
	// The own ship: a chevron, nose up.
	Line({ Centre + FVector2f(-6.f, 6.f), Centre + FVector2f(0.f, -8.f), Centre + FVector2f(6.f, 6.f), Centre + FVector2f(0.f, 2.f),
		Centre + FVector2f(-6.f, 6.f) }, Accent);

	const FSlateFontInfo Font = LabelFont(17.f);
	for (const FSpaceRadarContact& Contact : Contacts)
	{
		const FVector2D Plot = PlotPosition(Contact, RangeM);
		if (Contact.bBody)
		{
			if (Plot.IsNearlyZero())
			{
				continue;
			}
			// A mark pointing out through the rim, and the body's initial just inside it.
			const FVector2f Towards(float(Plot.X), -float(Plot.Y));
			const FVector2f Across(-Towards.Y, Towards.X);
			const FVector2f At = Centre + Towards * Radius;
			Line({ At + Towards * 3.f, At - Towards * 9.f + Across * 6.f, At - Towards * 9.f - Across * 6.f, At + Towards * 3.f }, Accent);
			Text(OutDrawElements, LineLayer + 1, AllottedGeometry, At - Towards * 22.f, Contact.Label.Left(1).ToUpper(), Font, Faded(Accent, 0.9f));
			continue;
		}
		if (Plot.SizeSquared() > 1.0)
		{
			continue;
		}
		// On the disc where it is, raised on a stalk by its height (half the radius per range).
		const FVector2f Base = Centre + FVector2f(float(Plot.X), -float(Plot.Y)) * Radius;
		const float Lift = FMath::Clamp(Contact.HeightM / FMath::Max(RangeM, 1.f), -1.f, 1.f) * Radius * 0.5f;
		const FVector2f At = Base - FVector2f(0.f, Lift);
		if (FMath::Abs(Lift) > 1.5f)
		{
			Line({ Base, At }, Faded(Accent, 0.5f));
			Line({ Base - FVector2f(2.5f, 0.f), Base + FVector2f(2.5f, 0.f) }, Faded(Accent, 0.5f));
		}
		const float D = 4.5f;
		Line({ At + FVector2f(0.f, -D), At + FVector2f(D, 0.f), At + FVector2f(0.f, D), At + FVector2f(-D, 0.f), At + FVector2f(0.f, -D) }, Accent);
	}
	return LineLayer + 2;
}

// -------------------------------------------------------------------------------------------
// Self status
// -------------------------------------------------------------------------------------------

namespace SpaceShipStatusGeometry
{
	/** The convex hull of points in a plane (monotone chain), counter-clockwise, not closed. */
	TArray<FVector2D> ConvexHull(TArray<FVector2D> Points)
	{
		Points.Sort([](const FVector2D& A, const FVector2D& B) { return A.X < B.X || (A.X == B.X && A.Y < B.Y); });
		if (Points.Num() < 3)
		{
			return Points;
		}
		auto Cross = [](const FVector2D& O, const FVector2D& A, const FVector2D& B) { return (A.X - O.X) * (B.Y - O.Y) - (A.Y - O.Y) * (B.X - O.X); };
		TArray<FVector2D> Hull;
		Hull.SetNum(Points.Num() * 2);
		int32 Count = 0;
		for (int32 Index = 0; Index < Points.Num(); ++Index)
		{
			while (Count >= 2 && Cross(Hull[Count - 2], Hull[Count - 1], Points[Index]) <= 0.0)
			{
				--Count;
			}
			Hull[Count++] = Points[Index];
		}
		for (int32 Index = Points.Num() - 2, Lower = Count + 1; Index >= 0; --Index)
		{
			while (Count >= Lower && Cross(Hull[Count - 2], Hull[Count - 1], Points[Index]) <= 0.0)
			{
				--Count;
			}
			Hull[Count++] = Points[Index];
		}
		Hull.SetNum(FMath::Max(Count - 1, 0));
		return Hull;
	}
}

void USpaceHudShipStatus::SetShip(const AActor* Ship)
{
	Outlines.Reset();
	Engines.Reset();
	Gear.Reset();
	if (!Ship)
	{
		return;
	}
	// From above with the nose up: X to the right (the actor's Y), Y ahead (its X), metres.
	const FTransform ActorTransform = Ship->GetActorTransform();
	auto Plan = [](const FVector& Local) { return FVector2D(Local.Y / 100.0, Local.X / 100.0); };
	TSet<FName> SeenSockets;
	TInlineComponentArray<UStaticMeshComponent*> Meshes(Ship);
	for (const UStaticMeshComponent* Mesh : Meshes)
	{
		const FTransform ToActor = Mesh->GetComponentTransform().GetRelativeTransform(ActorTransform);
		// The hull's collision hulls (the UCX shapes from Blender): the ship's real shape, cheap to draw.
		if (Mesh->GetFName() == TEXT("Hull") && Mesh->GetStaticMesh() && Mesh->GetStaticMesh()->GetBodySetup())
		{
			const FKAggregateGeom& Geometry = Mesh->GetStaticMesh()->GetBodySetup()->AggGeom;
			for (const FKConvexElem& Convex : Geometry.ConvexElems)
			{
				const FTransform ElementToActor = Convex.GetTransform() * ToActor;
				TArray<FVector2D> Points;
				if (Convex.VertexData.Num() >= 3)
				{
					for (const FVector& Vertex : Convex.VertexData)
					{
						Points.Add(Plan(ElementToActor.TransformPosition(Vertex)));
					}
				}
				else
				{
					FVector Corners[8];
					Convex.ElemBox.GetVertices(Corners);
					for (const FVector& Corner : Corners)
					{
						Points.Add(Plan(ElementToActor.TransformPosition(Corner)));
					}
				}
				Outlines.Add(SpaceShipStatusGeometry::ConvexHull(MoveTemp(Points)));
			}
			for (const FKBoxElem& Box : Geometry.BoxElems)
			{
				const FVector Half(Box.X * 0.5, Box.Y * 0.5, Box.Z * 0.5);
				FVector Corners[8];
				FBox(-Half, Half).GetVertices(Corners);
				TArray<FVector2D> Points;
				for (const FVector& Corner : Corners)
				{
					Points.Add(Plan((Box.GetTransform() * ToActor).TransformPosition(Corner)));
				}
				Outlines.Add(SpaceShipStatusGeometry::ConvexHull(MoveTemp(Points)));
			}
		}
		for (const FName& Socket : Mesh->GetAllSocketNames())
		{
			const FString Name = Socket.ToString();
			const bool bEngine = Name.StartsWith(TEXT("Engine_"));
			if ((!bEngine && !Name.StartsWith(TEXT("Gear_"))) || SeenSockets.Contains(Socket))
			{
				continue;
			}
			SeenSockets.Add(Socket);
			const FVector2D At = Plan(ActorTransform.InverseTransformPositionNoScale(Mesh->GetSocketLocation(Socket)));
			(bEngine ? Engines : Gear).Add(At);
		}
	}
}

int32 USpaceHudShipStatus::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	SCOPE_CYCLE_COUNTER(STAT_SpaceHudShipPaint);
	using namespace SpaceHudStyle;
	LayerId = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
	const FVector2f Size = AllottedGeometry.GetLocalSize();
	if (Size.X < 10.f || Size.Y < 10.f || Outlines.Num() == 0)
	{
		return LayerId;
	}
	// Fit the whole ship (and its engines and gear) into the page, keeping its proportions.
	FBox2D Bounds(ForceInit);
	for (const TArray<FVector2D>& Outline : Outlines)
	{
		for (const FVector2D& Point : Outline)
		{
			Bounds += Point;
		}
	}
	for (const FVector2D& Point : Engines)
	{
		Bounds += Point;
	}
	for (const FVector2D& Point : Gear)
	{
		Bounds += Point;
	}
	const FVector2D Extent = Bounds.GetSize();
	const float Margin = 10.f;
	const float Scale = FMath::Min((Size.X - 2.f * Margin) / FMath::Max(float(Extent.X), 0.1f), (Size.Y - 2.f * Margin) / FMath::Max(float(Extent.Y), 0.1f));
	const FVector2D Middle = Bounds.GetCenter();
	const FVector2f Centre = Size * 0.5f;
	auto ToScreen = [&](const FVector2D& Point) { return Centre + FVector2f(float(Point.X - Middle.X), -float(Point.Y - Middle.Y)) * Scale; };
	const FPaintGeometry Paint = AllottedGeometry.ToPaintGeometry();

	// The hulls as a hologram: thin lines, the overlaps reading as the ship's structure. One thickness and
	// one layer for every line, as on the radar (see there: Slate batches them together).
	const int32 LineLayer = LayerId + 1;
	for (const TArray<FVector2D>& Outline : Outlines)
	{
		if (Outline.Num() < 2)
		{
			continue;
		}
		TArray<FVector2f> Points;
		for (const FVector2D& Point : Outline)
		{
			Points.Add(ToScreen(Point));
		}
		const FVector2f First = Points[0];
		Points.Add(First);
		FSlateDrawElement::MakeLines(OutDrawElements, LineLayer, Paint, Points, ESlateDrawEffect::None, Faded(Color, 0.75f), true, SmallScreenLine);
	}
	// Engines: a ring each, filled and trailing a plume behind as they work.
	const float Demand = FMath::Clamp(EngineDemand, 0.f, 1.f);
	for (const FVector2D& Engine : Engines)
	{
		const FVector2f At = ToScreen(Engine);
		RoundedBox(OutDrawElements, LineLayer, AllottedGeometry, At - FVector2f(5.f, 5.f), FVector2f(10.f, 10.f), 5.f,
			Faded(EngineColor, 0.15f + 0.85f * Demand), EngineColor, SmallScreenLine);
		if (Demand > 0.02f)
		{
			GradientCapsule(OutDrawElements, LayerId, AllottedGeometry, At + FVector2f(-3.f, 5.f), FVector2f(6.f, 4.f + 22.f * Demand), 3.f,
				Faded(EngineColor, 0.f), Faded(EngineColor, 0.7f * Demand), true);
		}
	}
	// Gear legs, only while they are out.
	if (GearColor.A > 0.01f)
	{
		for (const FVector2D& Leg : Gear)
		{
			const FVector2f At = ToScreen(Leg);
			RoundedBox(OutDrawElements, LineLayer, AllottedGeometry, At - FVector2f(4.f, 4.f), FVector2f(8.f, 8.f), 1.5f, Faded(GearColor, 0.35f), GearColor, SmallScreenLine);
		}
	}
	return LineLayer + 1;
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
	// A faint cyan halo, as the reference's projected type has, instead of the dark outline SC-1c
	// used: that made every word heavy.
	Font.OutlineSettings.OutlineSize = 1;
	Font.OutlineSettings.OutlineColor = FLinearColor(0.2f, 0.6f, 0.85f, 0.22f);
	Text->SetFont(Font);
	Text->SetColorAndOpacity(FSlateColor(Weight == FName(TEXT("Number")) ? SpaceHudStyle::Instrument : SpaceHudStyle::Label));
	Texts.Add(Name, Text);
	return Text;
}

void USpaceFlightHud::BuildTree()
{
	using namespace SpaceHudStyle;

	UCanvasPanel* Root = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("Root"));
	WidgetTree->RootWidget = Root;

	// Everything is placed from the middle of the screen in 1080p units (the reference's pixels);
	// Slate's DPI scale fits it to other resolutions.
	auto At = [Root](UWidget* Widget, const FVector2D& Position, const FVector2D& Alignment, const FVector2D& Size = FVector2D::ZeroVector)
	{
		UCanvasPanelSlot* Slot = Root->AddChildToCanvas(Widget);
		Slot->SetAnchors(FAnchors(0.5f, 0.5f));
		Slot->SetAlignment(Alignment);
		Slot->SetAutoSize(Size.IsZero());
		if (!Size.IsZero())
		{
			Slot->SetSize(Size);
		}
		Slot->SetPosition(Position);
		return Slot;
	};
	auto Symbol = [&](const FName Name, ESpaceHudSymbol Kind, const FVector2D& Centre, const FVector2D& Size, const FLinearColor& Color)
	{
		USpaceHudSymbol* New = WidgetTree->ConstructWidget<USpaceHudSymbol>(USpaceHudSymbol::StaticClass(), Name);
		New->Symbol = Kind;
		New->Color = Color;
		Parts.Add(Name, New);
		At(New, Centre, FVector2D(0.5, 0.5), Size);
		return New;
	};
	// The thin brackets beside the reference's text blocks, through points given in screen units.
	auto Bracket = [&](const FName Name, const TArray<FVector2D>& Points, const FLinearColor& Color)
	{
		FBox2D Box(ForceInit);
		for (const FVector2D& Point : Points)
		{
			Box += Point;
		}
		Box = Box.ExpandBy(2.0);
		USpaceHudSymbol* New = WidgetTree->ConstructWidget<USpaceHudSymbol>(USpaceHudSymbol::StaticClass(), Name);
		New->Symbol = ESpaceHudSymbol::Line;
		New->Color = Color;
		New->Thickness = 1.f;
		for (const FVector2D& Point : Points)
		{
			New->Points.Add((Point - Box.Min) / Box.GetSize());
		}
		Parts.Add(Name, New);
		At(New, Box.Min, FVector2D::ZeroVector, Box.GetSize());
	};
	auto Words = [&](const FName Name, const TCHAR* Initial, float Size, const FVector2D& Position, const FVector2D& Alignment,
		const FLinearColor& Color = SpaceHudStyle::Label)
	{
		UTextBlock* Text = MakeText(Name, Size, 40, TEXT("Label"));
		Text->SetText(FText::FromString(Initial));
		Text->SetColorAndOpacity(FSlateColor(Color));
		At(Text, Position, Alignment);
		return Text;
	};
	auto Gauge = [this](const FName Name)
	{
		USpaceHudGauge* NewGauge = WidgetTree->ConstructWidget<USpaceHudGauge>(USpaceHudGauge::StaticClass(), Name);
		NewGauge->Ticks = 0;
		Gauges.Add(Name, NewGauge);
		return NewGauge;
	};

	// --- Middle: pitch ladder over the whole view, heading tape, nose reticle, virtual joystick --------
	USpaceHudLadder* Ladder = WidgetTree->ConstructWidget<USpaceHudLadder>(USpaceHudLadder::StaticClass(), TEXT("Ladder"));
	Ladder->Color = Label;
	Parts.Add(TEXT("Ladder"), Ladder);
	if (UCanvasPanelSlot* LadderSlot = Root->AddChildToCanvas(Ladder))
	{
		LadderSlot->SetAnchors(FAnchors(0.f, 0.f, 1.f, 1.f));
		LadderSlot->SetOffsets(FMargin(0.f));
	}
	USpaceHudTape* Heading = WidgetTree->ConstructWidget<USpaceHudTape>(USpaceHudTape::StaticClass(), TEXT("HeadingTape"));
	Heading->bWrap360 = true;
	Heading->Span = 80.f;
	Heading->MajorStep = 20.f;
	Heading->MinorPerMajor = 4;
	Heading->Color = Label;
	Parts.Add(TEXT("HeadingTape"), Heading);
	At(Heading, FVector2D(0.0, -140.0), FVector2D(0.5, 0.0), FVector2D(200.0, 44.0));
	Symbol(TEXT("Reticle"), ESpaceHudSymbol::Reticle, FVector2D::ZeroVector, FVector2D(28.0, 28.0), Label);
	VirtualJoystick = WidgetTree->ConstructWidget<USpaceHudVirtualJoystick>(USpaceHudVirtualJoystick::StaticClass(), TEXT("VirtualJoystick"));
	USizeBox* JoystickBox = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), TEXT("VirtualJoystickBox"));
	JoystickBox->SetWidthOverride(220.f);
	JoystickBox->SetHeightOverride(220.f);
	JoystickBox->AddChild(VirtualJoystick);
	VirtualJoystickBox = JoystickBox;
	At(JoystickBox, FVector2D::ZeroVector, FVector2D(0.5, 0.5));

	// --- Left: master mode, switch badges, strafe cross, speed tube, BOOST / LIMIT rows ------------
	Symbol(TEXT("ModeIcon"), ESpaceHudSymbol::ModeIcon, FVector2D(-306.0, -77.0), FVector2D(22.0, 22.0), Label);
	Words(TEXT("ModeText"), TEXT("SCM"), 12.f, FVector2D(-290.0, -83.0), FVector2D(0.0, 0.5));
	Words(TEXT("SubModeText"), TEXT("FLIGHT"), 10.f, FVector2D(-290.0, -69.0), FVector2D(0.0, 0.5));
	Bracket(TEXT("BracketMode"), { FVector2D(-262.0, -100.0), FVector2D(-262.0, -62.0), FVector2D(-252.0, -50.0) }, Faded(Label, 0.6f));

	UVerticalBox* Badges = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("BadgeBox"));
	for (const TCHAR* LampName : { TEXT("CSTB"), TEXT("CPLD"), TEXT("PREC"), TEXT("BOOST") })
	{
		const FName Key(LampName);
		UOverlay* Badge = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass(), FName(*FString::Printf(TEXT("Badge_%s"), LampName)));
		USpaceHudLamp* NewLamp = WidgetTree->ConstructWidget<USpaceHudLamp>(USpaceHudLamp::StaticClass(), FName(*FString::Printf(TEXT("Lamp_%s"), LampName)));
		NewLamp->bBadge = true;
		NewLamp->Color = Instrument;
		Lamps.Add(Key, NewLamp);
		UTextBlock* LampText = MakeText(FName(*FString::Printf(TEXT("LampLabel_%s"), LampName)), 10.f, 60, TEXT("Label"));
		LampText->SetText(FText::FromString(LampName));
		LampText->SetJustification(ETextJustify::Center);
		LampLabels.Add(Key, LampText);
		if (UOverlaySlot* LampSlot = Badge->AddChildToOverlay(NewLamp))
		{
			LampSlot->SetHorizontalAlignment(HAlign_Fill);
			LampSlot->SetVerticalAlignment(VAlign_Fill);
		}
		if (UOverlaySlot* LabelSlot = Badge->AddChildToOverlay(LampText))
		{
			LabelSlot->SetPadding(FMargin(5.f, 1.f, 5.f, 1.f));
			LabelSlot->SetHorizontalAlignment(HAlign_Center);
			LabelSlot->SetVerticalAlignment(VAlign_Center);
		}
		Parts.Add(Badge->GetFName(), Badge);
		UVerticalBoxSlot* BadgeSlot = Badges->AddChildToVerticalBox(Badge);
		BadgeSlot->SetHorizontalAlignment(HAlign_Center);
		BadgeSlot->SetPadding(FMargin(0.f, 2.f));
	}
	At(Badges, FVector2D(-301.0, -3.0), FVector2D(0.5, 0.5));

	USpaceHudSymbol* Strafe = Symbol(TEXT("Strafe"), ESpaceHudSymbol::Strafe, FVector2D(-250.0, -3.0), FVector2D(56.0, 56.0), Label);
	Strafe->Accent = Red;
	Symbol(TEXT("LimiterPlus"), ESpaceHudSymbol::Plus, FVector2D(-204.0, -14.0), FVector2D(10.0, 10.0), Faded(Label, 0.8f));
	USpaceHudGauge* SpeedGauge = Gauge(TEXT("SpeedGauge"));
	At(SpeedGauge, FVector2D(-190.0, -80.0), FVector2D::ZeroVector, FVector2D(11.0, 132.0));
	Words(TEXT("SpeedValue"), TEXT("0"), 22.f, FVector2D(-184.0, 72.0), FVector2D(0.5, 0.5));
	Words(TEXT("SpeedUnit"), TEXT("m/s"), 11.f, FVector2D(-184.0, 90.0), FVector2D(0.5, 0.5));
	Words(TEXT("RowBoostValue"), TEXT("100%"), 12.f, FVector2D(-300.0, 69.0), FVector2D(1.0, 0.5));
	Words(TEXT("RowBoostLabel"), TEXT("BOOST"), 12.f, FVector2D(-294.0, 69.0), FVector2D(0.0, 0.5));
	Words(TEXT("RowLimitValue"), TEXT("100%"), 12.f, FVector2D(-300.0, 83.0), FVector2D(1.0, 0.5));
	Words(TEXT("RowLimitLabel"), TEXT("LIMIT"), 12.f, FVector2D(-294.0, 83.0), FVector2D(0.0, 0.5));
	Bracket(TEXT("BracketRows"), { FVector2D(-253.0, 40.0), FVector2D(-265.0, 53.0), FVector2D(-265.0, 90.0) }, Faded(Label, 0.6f));

	// --- Right: afterburner tube, altitude tape, gyro and G, status rows ------------------------------
	USpaceHudGauge* Afterburner = Gauge(TEXT("AfterburnerGauge"));
	Afterburner->ReserveZone = 0.25f;
	Afterburner->ReserveColor = Red;
	At(Afterburner, FVector2D(205.0, -77.0), FVector2D::ZeroVector, FVector2D(12.0, 130.0));
	Symbol(TEXT("AbRing"), ESpaceHudSymbol::Ring, FVector2D(177.0, 76.0), FVector2D(13.0, 13.0), Label);
	Words(TEXT("AfterburnerValue"), TEXT("100%"), 22.f, FVector2D(187.0, 75.0), FVector2D(0.0, 0.5));
	Words(TEXT("AfterburnerLabel"), TEXT("AB"), 11.f, FVector2D(211.0, 92.0), FVector2D(0.5, 0.5));

	Words(TEXT("AltitudeUnit"), TEXT("KM"), 12.f, FVector2D(267.0, -71.0), FVector2D(0.5, 0.5));
	USpaceHudTape* Altitude = WidgetTree->ConstructWidget<USpaceHudTape>(USpaceHudTape::StaticClass(), TEXT("AltitudeTape"));
	Altitude->bVertical = true;
	Altitude->Span = 0.2f;
	Altitude->MajorStep = 0.1f;
	Altitude->MinorPerMajor = 5;
	Altitude->LabelDecimals = 2;
	Altitude->MarkAt = 0.47f;
	Altitude->Color = Label;
	Parts.Add(TEXT("AltitudeTape"), Altitude);
	At(Altitude, FVector2D(252.0, -55.0), FVector2D::ZeroVector, FVector2D(44.0, 143.0));

	USpaceHudSymbol* Gyro = Symbol(TEXT("Gyro"), ESpaceHudSymbol::Gyro, FVector2D(321.0, 1.0), FVector2D(50.0, 50.0), Label);
	Gyro->Accent = Orange;
	Symbol(TEXT("Shield"), ESpaceHudSymbol::Shield, FVector2D(303.0, 19.0), FVector2D(14.0, 16.0), Instrument);
	Words(TEXT("GValue"), TEXT("0.0"), 22.f, FVector2D(398.0, -6.0), FVector2D(1.0, 0.5));
	Words(TEXT("GUnit"), TEXT("G"), 15.f, FVector2D(401.0, -1.0), FVector2D(0.0, 0.5));
	Bracket(TEXT("GSeparator"), { FVector2D(360.0, 4.0), FVector2D(398.0, 4.0) }, Faded(Label, 0.6f));
	Words(TEXT("GMax"), TEXT("7.0"), 11.f, FVector2D(380.0, 13.0), FVector2D(0.5, 0.5));

	Words(TEXT("RowGearLabel"), TEXT("GEAR"), 11.f, FVector2D(339.0, -72.0), FVector2D(0.0, 0.5));
	Words(TEXT("RowGearValue"), TEXT("UP"), 11.f, FVector2D(398.0, -72.0), FVector2D(0.0, 0.5));
	Words(TEXT("RowCruiseLabel"), TEXT("CRUISE"), 11.f, FVector2D(339.0, -57.0), FVector2D(0.0, 0.5));
	Words(TEXT("RowCruiseValue"), TEXT("OFF"), 11.f, FVector2D(398.0, -57.0), FVector2D(0.0, 0.5));
	Bracket(TEXT("BracketStatus"), { FVector2D(322.0, -44.0), FVector2D(335.0, -57.0), FVector2D(335.0, -87.0) }, Faded(Label, 0.6f));
	Words(TEXT("RowRAltLabel"), TEXT("R-ALT"), 11.f, FVector2D(341.0, 60.0), FVector2D(0.0, 0.5));
	Words(TEXT("RowRAltValue"), TEXT("-"), 11.f, FVector2D(391.0, 60.0), FVector2D(0.0, 0.5));
	Words(TEXT("RowVsiLabel"), TEXT("VSI"), 11.f, FVector2D(341.0, 74.0), FVector2D(0.0, 0.5));
	Words(TEXT("RowVsiValue"), TEXT("-"), 11.f, FVector2D(391.0, 74.0), FVector2D(0.0, 0.5));
	Words(TEXT("RowAtmoLabel"), TEXT("ATMO"), 11.f, FVector2D(341.0, 88.0), FVector2D(0.0, 0.5));
	Words(TEXT("RowAtmoValue"), TEXT("-"), 11.f, FVector2D(391.0, 88.0), FVector2D(0.0, 0.5));
	Bracket(TEXT("BracketAir"), { FVector2D(325.0, 45.0), FVector2D(337.0, 58.0), FVector2D(337.0, 93.0) }, Faded(Label, 0.6f));

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

	State.bGearDown = Ship->IsGearDeployed();
	State.bGearMoving = Ship->GetGearState() == EGearState::Extending || Ship->GetGearState() == EGearState::Retracting;
	State.bGearWarning = Ship->HasGroundInfo() && Ship->GetLandingBlocker() == ELandingBlocker::GearUp;
	State.bPrecisionOn = Ship->IsPrecisionModeOn();
	State.bPrecisionActive = Ship->IsPrecisionActive();
	State.Stick = Ship->GetMouseStick();
	State.Deadzone = Ship->GetVirtualJoystickDeadzone();

	const ECruiseState Cruise = Ship->GetCruiseState();
	State.CruiseLabel = Cruise == ECruiseState::Spooling ? TEXT("SPOOL") : Cruise == ECruiseState::Active ? TEXT("ON")
		: Cruise == ECruiseState::Dropping ? TEXT("DROP") : TEXT("OFF");
	State.SubModeLabel = Cruise == ECruiseState::Active || Cruise == ECruiseState::Dropping ? TEXT("CRUISE")
		: Cruise == ECruiseState::Spooling ? TEXT("SPOOL") : State.bPrecisionActive ? TEXT("PREC") : TEXT("FLIGHT");
	State.GearLabel = State.bGearMoving ? TEXT("MOVING") : State.bGearDown ? TEXT("DOWN") : TEXT("UP");

	// Across the nose: strafe input, drift (50 m/s full scale) and turn rate (the ship's top rate).
	const FVector Input = Ship->GetLinearInput();
	State.StrafeInput = FVector2D(Input.Y, Input.Z);
	const FVector Local = Ship->GetActorTransform().InverseTransformVectorNoScale(Velocity) / 5000.0;
	State.Drift = FVector2D(Local.Y, Local.Z);
	const FVector Rate = Ship->GetAngularVelocity() / FMath::Max(Ship->GetMaxTurnRate(), 1.f);
	State.TurnRate = FVector2D(Rate.Z, Rate.Y);
	State.EngineDemand = Ship->GetEngineDemand();
	FVector CapPositive, CapNegative;
	Ship->GetThrusterCapacity(CapPositive, CapNegative);
	const double G = 980.665;
	State.ThrustG = Ship->GetThrusterAcceleration() / G;
	State.ThrustCapPositiveG = CapPositive / G;
	State.ThrustCapNegativeG = CapNegative / G;
	State.bLanded = Ship->IsLanded();

	State.bHasEnvironment = Ship->HasEnvironment();
	if (State.bHasEnvironment)
	{
		const FCelestialEnvironment& Environment = Ship->GetEnvironment();
		State.AltitudeAslM = float(Environment.AltitudeAboveSeaLevelCm / 100.0);
		State.AltitudeAglM = float(FMath::Max(Environment.AltitudeAboveTerrainCm, 0.0) / 100.0);
		State.VerticalSpeedMS = float((Velocity | Environment.Up) / 100.0);
		State.AtmosphereDensity = Environment.AtmosphereDensity;
		SpaceHudStyle::Attitude(Environment.Up, Ship->GetActorForwardVector(), Ship->GetActorRightVector(), Ship->GetActorUpVector(),
			State.HeadingDeg, State.PitchDeg, State.RollDeg);
	}
	return State;
}

FSpaceFlightHudState USpaceFlightHud::ApplyView(const FSpaceFlightHudState& State, const ASpaceshipPawn* Ship, FRotator ViewRotation, float FovDeg)
{
	FSpaceFlightHudState Out = State;
	Out.ViewFovDeg = FovDeg;
	if (Ship && Ship->HasEnvironment())
	{
		const FRotationMatrix View(ViewRotation);
		SpaceHudStyle::Attitude(Ship->GetEnvironment().Up, View.GetUnitAxis(EAxis::X), View.GetUnitAxis(EAxis::Y), View.GetUnitAxis(EAxis::Z),
			Out.HeadingDeg, Out.PitchDeg, Out.RollDeg);
	}
	return Out;
}

void USpaceFlightHud::ApplyState(const FSpaceFlightHudState& InState)
{
	using namespace SpaceHudStyle;
	const FSpaceFlightHudState State = SteadyState(InState);
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
	auto Show = [this](const FName Name, bool bShown)
	{
		UWidget* Widget = Parts.FindRef(Name);
		if (!Widget)
		{
			Widget = Texts.FindRef(Name);
		}
		if (Widget)
		{
			Widget->SetVisibility(bShown ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
		}
	};
	auto SetLamp = [this, &Show](const FName Name, bool bLit, const FLinearColor& Color)
	{
		if (USpaceHudLamp* Lamp = Lamps.FindRef(Name))
		{
			// The lamp eases to its new level and flashes once, so a switch is noticed, not blinked.
			Lamp->SetTarget(bLit, Color);
		}
		if (UTextBlock* LabelText = LampLabels.FindRef(Name))
		{
			LabelText->SetColorAndOpacity(FSlateColor(bLit ? (Lamps.FindRef(Name) && Lamps.FindRef(Name)->bBadge ? Color : Label) : Faded(Label, 0.45f)));
		}
		// The reference shows a switch badge only while its switch is on.
		Show(FName(*FString::Printf(TEXT("Badge_%s"), *Name.ToString())), bLit);
		LampLit.Add(Name, bLit);
		LampColors.Add(Name, Color);
	};
	auto SetText = [this](const FName Name, const FString& Value, const FLinearColor& Color)
	{
		if (UTextBlock* Text = Texts.FindRef(Name))
		{
			Text->SetText(FText::FromString(Value));
			Text->SetColorAndOpacity(FSlateColor(Color));
		}
	};

	// --- Master mode and switches --------------------------------------------------------------
	if (UTextBlock* ModeLabel = LampLabels.FindRef(TEXT("MODE")))
	{
		ModeLabel->SetText(FText::FromString(State.ModeLabel));
	}
	const FLinearColor MasterModeColor = State.ModeLabel == TEXT("NAV") ? NavBlue : Instrument;
	// Switching blinks the mode being switched to.
	SetLamp(TEXT("MODE"), !State.bModeSwitching || bBlink, MasterModeColor);
	SetText(TEXT("ModeText"), State.ModeLabel, !State.bModeSwitching || bBlink ? Label : Faded(Label, 0.3f));
	SetText(TEXT("SubModeText"), State.SubModeLabel, Faded(Label, 0.8f));
	if (UTextBlock* CoupledLabel = LampLabels.FindRef(TEXT("CPLD")))
	{
		CoupledLabel->SetText(FText::FromString(State.bSpaceBrake ? TEXT("BRAKE") : TEXT("CPLD")));
	}
	SetLamp(TEXT("CPLD"), State.bCoupled || State.bSpaceBrake, State.bSpaceBrake ? Red : Instrument);
	// G-Safe switched on but suspended by boost: amber.
	SetLamp(TEXT("GSAF"), State.bGSafeOn, State.bGSafeActive ? Instrument : Amber);
	SetLamp(TEXT("CSTB"), State.bComStab, Instrument);
	SetLamp(TEXT("BOOST"), State.bBoostActive, InstrumentBright);
	// Gear: lit down and locked, amber blinking on the way, red blinking low over the ground with it up.
	const FLinearColor GearColor = State.bGearDown ? Instrument : State.bGearWarning && !State.bGearMoving ? Red : Amber;
	SetLamp(TEXT("GEAR"), State.bGearDown || ((State.bGearMoving || State.bGearWarning) && bBlink), GearColor);
	// Precision switched on but not in effect (NAV): amber, like G-Safe suspended by boost.
	SetLamp(TEXT("PREC"), State.bPrecisionOn, State.bPrecisionActive ? Instrument : Amber);
	SetLamp(TEXT("CRUISE"), State.CruiseLabel != TEXT("OFF"), State.CruiseLabel == TEXT("ON") ? Instrument : Amber);
	if (USpaceHudSymbol* Shield = Cast<USpaceHudSymbol>(Parts.FindRef(TEXT("Shield"))))
	{
		Shield->Color = !State.bGSafeOn ? Faded(Label, 0.3f) : State.bGSafeActive ? Instrument : Amber;
	}

	// --- Speed tube, speed, limiter ------------------------------------------------------------------
	if (USpaceHudGauge* Speed = Gauges.FindRef(TEXT("SpeedGauge")))
	{
		Speed->ReverseZone = SpeedReverseZone;
		Speed->Value = State.SpeedFraction;
		Speed->ReverseValue = State.ReverseFraction;
		Speed->Marker = State.LimiterFraction;
		Speed->MarkerColor = Label;
		Speed->FillColor = State.bAfterburnerActive ? InstrumentBright : Instrument;
		// The + rides beside the limiter handle, as in the reference.
		if (UWidget* Plus = Parts.FindRef(TEXT("LimiterPlus")))
		{
			if (UCanvasPanelSlot* PlusSlot = Cast<UCanvasPanelSlot>(Plus->Slot))
			{
				const float Along = SpeedReverseZone + (1.f - SpeedReverseZone) * State.LimiterFraction;
				PlusSlot->SetPosition(FVector2D(-204.0, -80.0 + 132.0 * (1.0 - Along)));
			}
		}
	}
	const FLinearColor SpeedColor = State.ForwardSpeedCmS < -50.f ? Red : Instrument;
	SetText(TEXT("SpeedText"), SpaceHudStyle::Speed(State.SpeedCmS), SpeedColor);
	const bool bKilometres = State.SpeedCmS >= 100000.f;
	SetText(TEXT("SpeedValue"), bKilometres ? FString::Printf(TEXT("%.2f"), State.SpeedCmS / 100000.f) : FString::Printf(TEXT("%.0f"), State.SpeedCmS / 100.f),
		State.ForwardSpeedCmS < -50.f ? Red : Label);
	SetText(TEXT("SpeedUnit"), bKilometres ? TEXT("km/s") : TEXT("m/s"), Faded(Label, 0.8f));
	SetText(TEXT("LimitText"), FString::Printf(TEXT("LIM %s  %3.0f%%"), *SpaceHudStyle::Speed(State.SpeedLimitCmS), State.LimiterFraction * 100.f),
		Faded(Label, 0.75f));
	SetText(TEXT("RowLimitValue"), FString::Printf(TEXT("%.0f%%"), State.LimiterFraction * 100.f), Label);
	SetText(TEXT("SpeedPercent"), FString::Printf(TEXT("%.0f%%"), State.SpeedFraction * 100.f), Label);
	SetText(TEXT("RowBoostValue"), FString::Printf(TEXT("%.0f%%"), State.BoostEnergy * 100.f),
		State.bBoostLocked || State.BoostEnergy < 0.25f ? Red : State.bBoostActive ? InstrumentBright : Label);

	// --- G ----------------------------------------------------------------------------------------------
	const FLinearColor GColor = State.GForce > State.GSafeMaxG + 0.05f ? Red : State.GForce > State.GSafeMaxG * 0.7f ? Amber : Instrument;
	if (USpaceHudGauge* GGauge = Gauges.FindRef(TEXT("GGauge")))
	{
		GGauge->Value = State.GForce / GMeterRangeG;
		GGauge->FillColor = GColor;
		// The G-Safe limit as a mark, while G-Safe is actually limiting.
		GGauge->Marker = State.bGSafeActive ? State.GSafeMaxG / GMeterRangeG : -1.f;
		GGauge->MarkerColor = Faded(Label, 0.8f);
	}
	SetText(TEXT("GText"), FString::Printf(TEXT("%.1f G"), State.GForce), GColor);
	SetText(TEXT("GValue"), FString::Printf(TEXT("%.1f"), State.GForce), GColor == Instrument ? Label : GColor);
	SetText(TEXT("GMax"), FString::Printf(TEXT("%.1f"), State.GSafeMaxG), State.bGSafeActive ? Faded(Label, 0.8f) : Faded(Label, 0.4f));

	// --- Boost and afterburner ---------------------------------------------------------------------
	if (USpaceHudGauge* Boost = Gauges.FindRef(TEXT("BoostGauge")))
	{
		Boost->Value = State.BoostEnergy;
		Boost->ReverseZone = 0.f;
		Boost->FillColor = State.bBoostLocked || State.BoostEnergy < 0.25f ? Red : State.bBoostActive ? InstrumentBright : Instrument;
	}
	SetText(TEXT("BoostText"), FString::Printf(TEXT("%.0f%%"), State.BoostEnergy * 100.f),
		State.bBoostLocked ? Red : State.bBoostActive ? InstrumentBright : Instrument);

	if (USpaceHudGauge* Afterburner = Gauges.FindRef(TEXT("AfterburnerGauge")))
	{
		Afterburner->Value = State.AfterburnerFuel;
		Afterburner->bDim = !State.bAfterburnerAvailable;
		Afterburner->FillColor = State.bAfterburnerLocked ? Red : State.bAfterburnerActive ? InstrumentBright : Instrument;
	}
	FString AfterburnerSuffix;
	FLinearColor AfterburnerColor = Instrument;
	if (!State.bAfterburnerAvailable)
	{
		AfterburnerSuffix = TEXT("SCM");
		AfterburnerColor = Faded(Label, 0.45f);
	}
	else if (State.bAfterburnerLocked)
	{
		AfterburnerSuffix = TEXT("DRY");
		AfterburnerColor = Red;
	}
	else if (State.bAfterburnerActive)
	{
		AfterburnerSuffix = TEXT("BURN");
		AfterburnerColor = InstrumentBright;
	}
	const FString Percent = FString::Printf(TEXT("%.0f%%"), State.AfterburnerFuel * 100.f);
	SetText(TEXT("AfterburnerText"), AfterburnerSuffix.IsEmpty() ? Percent : Percent + TEXT(" ") + AfterburnerSuffix, AfterburnerColor);
	SetText(TEXT("AfterburnerValue"), Percent, AfterburnerColor == Instrument ? Label : AfterburnerColor);
	SetText(TEXT("AfterburnerLabel"), AfterburnerSuffix.IsEmpty() ? TEXT("AB") : TEXT("AB ") + AfterburnerSuffix, Faded(AfterburnerColor == Instrument ? Label : AfterburnerColor, 0.85f));

	// --- Where the ship is: heading, ladder, altitudes, climb, air ---------------------------------
	for (const TCHAR* Name : { TEXT("HeadingTape"), TEXT("Ladder"), TEXT("AltitudeTape"), TEXT("AltitudeUnit") })
	{
		Show(Name, State.bHasEnvironment);
	}
	if (USpaceHudTape* Heading = Cast<USpaceHudTape>(Parts.FindRef(TEXT("HeadingTape"))))
	{
		Heading->Value = State.HeadingDeg;
	}
	if (USpaceHudLadder* Ladder = Cast<USpaceHudLadder>(Parts.FindRef(TEXT("Ladder"))))
	{
		Ladder->PitchDeg = State.PitchDeg;
		Ladder->RollDeg = State.RollDeg;
		Ladder->FovDeg = State.ViewFovDeg;
	}
	if (USpaceHudTape* Altitude = Cast<USpaceHudTape>(Parts.FindRef(TEXT("AltitudeTape"))))
	{
		// Kilometres with two decimals and 100 m between labels low down; whole kilometres high up.
		const bool bHigh = State.AltitudeAslM > 100000.f;
		Altitude->Value = State.AltitudeAslM / 1000.f;
		Altitude->Span = bHigh ? 20.f : 0.2f;
		Altitude->MajorStep = bHigh ? 10.f : 0.1f;
		Altitude->LabelDecimals = bHigh ? 0 : 2;
	}
	const FString None = TEXT("-");
	SetText(TEXT("RowRAltValue"), !State.bHasEnvironment ? None : State.AltitudeAglM < 10000.f ? FString::Printf(TEXT("%.0fm"), State.AltitudeAglM)
		: FString::Printf(TEXT("%.1fkm"), State.AltitudeAglM / 1000.f), Label);
	SetText(TEXT("RowVsiValue"), State.bHasEnvironment ? FString::Printf(TEXT("%+.0fm/s"), State.VerticalSpeedMS) : None, Label);
	SetText(TEXT("RowAtmoValue"), State.bHasEnvironment ? FString::Printf(TEXT("%.3fp"), State.AtmosphereDensity) : None, Label);
	SetText(TEXT("RowGearValue"), State.GearLabel, State.bGearWarning && !State.bGearDown ? (bBlink ? Red : Faded(Red, 0.4f))
		: State.bGearMoving ? Amber : State.bGearDown ? Instrument : Label);
	SetText(TEXT("RowCruiseValue"), State.CruiseLabel, State.CruiseLabel == TEXT("OFF") ? Faded(Label, 0.6f) : Instrument);

	// --- Strafe cross and gyro ---------------------------------------------------------------------------
	if (USpaceHudSymbol* Strafe = Cast<USpaceHudSymbol>(Parts.FindRef(TEXT("Strafe"))))
	{
		Strafe->Value = State.StrafeInput;
		Strafe->Value2 = State.Drift;
	}
	if (USpaceHudSymbol* Gyro = Cast<USpaceHudSymbol>(Parts.FindRef(TEXT("Gyro"))))
	{
		Gyro->Value = State.TurnRate;
	}

	// --- Cockpit radar and self status (the centre column's displays) ------------------------------
	if (USpaceHudRadar* Radar = Cast<USpaceHudRadar>(Parts.FindRef(TEXT("Radar"))))
	{
		Radar->Contacts = State.RadarContacts;
		Radar->RangeM = State.RadarRangeM;
	}
	SetText(TEXT("RadarRange"), State.RadarRangeM < 10000.f ? FString::Printf(TEXT("%.1f KM"), State.RadarRangeM / 1000.f)
		: FString::Printf(TEXT("%.0f KM"), State.RadarRangeM / 1000.f), Label);
	SetText(TEXT("RadarHeading"), State.bHasEnvironment ? FString::Printf(TEXT("%03.0f°"), FMath::Fmod(FMath::RoundToFloat(State.HeadingDeg), 360.f)) : TEXT("---"),
		State.bHasEnvironment ? Label : Faded(Label, 0.5f));
	int32 Near = 0;
	for (const FSpaceRadarContact& Contact : State.RadarContacts)
	{
		Near += Contact.bBody ? 0 : 1;
	}
	SetText(TEXT("RadarCount"), FString::Printf(TEXT("%d"), Near), Near > 0 ? Label : Faded(Label, 0.5f));
	for (const TCHAR* ShipPart : { TEXT("ShipStatus"), TEXT("ShipStatusLarge") })
	if (USpaceHudShipStatus* ShipStatus = Cast<USpaceHudShipStatus>(Parts.FindRef(ShipPart)))
	{
		ShipStatus->EngineDemand = State.EngineDemand;
		ShipStatus->EngineColor = State.bAfterburnerActive || State.bBoostActive ? InstrumentBright : Instrument;
		// Out and locked: lit; on the way: amber, blinking; up: not drawn (red blinking when it is needed).
		ShipStatus->GearColor = State.bGearDown ? Instrument : State.bGearMoving ? (bBlink ? Amber : Faded(Amber, 0.3f))
			: State.bGearWarning ? (bBlink ? Red : FLinearColor::Transparent) : FLinearColor::Transparent;
	}
	SetText(TEXT("ShipGear"), State.GearLabel, State.bGearWarning && !State.bGearDown ? Red : State.bGearMoving ? Amber : Label);
	SetText(TEXT("ShipThrust"), State.bLanded ? TEXT("LANDED") : FString::Printf(TEXT("%.0f%%"), State.EngineDemand * 100.f),
		State.bLanded ? Instrument : Label);

	// --- MFD pages: thrusters, navigation, contacts, self status ------------------------------------------
	auto Distance = [](float Metres)
	{
		return Metres < 1000.f ? FString::Printf(TEXT("%.0f M"), Metres) : Metres < 10000.f ? FString::Printf(TEXT("%.2f KM"), Metres / 1000.f)
			: Metres < 1.0e6f ? FString::Printf(TEXT("%.0f KM"), Metres / 1000.f) : FString::Printf(TEXT("%.1f MM"), Metres / 1.0e6f);
	};
	// Bearing clockwise from the nose, and elevation above the wings, as the reference's contact list.
	auto Bearing = [](const FSpaceRadarContact& Contact)
	{
		return FString::Printf(TEXT("%03.0f\u00B0"), FMath::Fmod(FMath::RoundToFloat(FMath::RadiansToDegrees(float(FMath::Atan2(Contact.Position.X, Contact.Position.Y)))) + 360.f, 360.f));
	};
	auto Elevation = [](const FSpaceRadarContact& Contact)
	{
		return FString::Printf(TEXT("%+.0f\u00B0"), FMath::RadiansToDegrees(float(FMath::Atan2(double(Contact.HeightM), Contact.Position.Size()))));
	};
	struct FThrustAxis { const TCHAR* Name; float Value; float Cap; };
	const FThrustAxis Axes[] = {
		{ TEXT("MAIN"), float(FMath::Max(State.ThrustG.X, 0.0)), float(State.ThrustCapPositiveG.X) },
		{ TEXT("RETRO"), float(FMath::Max(-State.ThrustG.X, 0.0)), float(State.ThrustCapNegativeG.X) },
		{ TEXT("STRAFE"), float(FMath::Abs(State.ThrustG.Y)), float(State.ThrustCapPositiveG.Y) },
		{ TEXT("UP"), float(FMath::Max(State.ThrustG.Z, 0.0)), float(State.ThrustCapPositiveG.Z) },
		{ TEXT("DOWN"), float(FMath::Max(-State.ThrustG.Z, 0.0)), float(State.ThrustCapNegativeG.Z) } };
	for (const FThrustAxis& Axis : Axes)
	{
		if (USpaceHudGauge* Thrust = Gauges.FindRef(FName(*FString::Printf(TEXT("ThrustGauge_%s"), Axis.Name))))
		{
			Thrust->Value = Axis.Cap > 0.01f ? Axis.Value / Axis.Cap : 0.f;
			Thrust->FillColor = State.bBoostActive || State.bAfterburnerActive ? InstrumentBright : Instrument;
		}
		SetText(FName(*FString::Printf(TEXT("ThrustValue_%s"), Axis.Name)), FString::Printf(TEXT("%.1f / %.1f G"), Axis.Value, Axis.Cap),
			Axis.Value > 0.05f ? Label : Faded(Label, 0.6f));
	}
	SetText(TEXT("ThrustStrafeSide"), State.ThrustG.Y > 0.05 ? TEXT("R") : State.ThrustG.Y < -0.05 ? TEXT("L") : TEXT(""), Label);
	SetText(TEXT("ThrustBoost"), State.bBoostActive ? TEXT("BOOST ON") : State.bBoostLocked ? TEXT("BOOST EMPTY") : TEXT("BOOST OFF"),
		State.bBoostActive ? InstrumentBright : State.bBoostLocked ? Red : Faded(Label, 0.7f));
	SetText(TEXT("ThrustGSafe"), State.bGSafeActive ? FString::Printf(TEXT("G-SAFE %.1f G"), State.GSafeMaxG) : State.bGSafeOn ? TEXT("G-SAFE SUSPENDED") : TEXT("G-SAFE OFF"),
		State.bGSafeActive ? Label : Amber);

	SetText(TEXT("NavMode"), State.ModeLabel, !State.bModeSwitching || bBlink ? Label : Faded(Label, 0.3f));
	SetText(TEXT("NavSub"), State.SubModeLabel, Faded(Label, 0.8f));
	SetText(TEXT("NavLimit"), SpaceHudStyle::Speed(State.SpeedLimitCmS), Label);
	SetText(TEXT("NavCruise"), State.CruiseLabel, State.CruiseLabel == TEXT("OFF") ? Faded(Label, 0.6f) : Instrument);
	SetText(TEXT("NavSpeed"), SpaceHudStyle::Speed(State.SpeedCmS), Label);
	TArray<FSpaceRadarContact> Bodies = State.RadarContacts.FilterByPredicate([](const FSpaceRadarContact& Contact) { return Contact.bBody; });
	Bodies.Sort([](const FSpaceRadarContact& A, const FSpaceRadarContact& B) { return A.DistanceM < B.DistanceM; });
	for (int32 Index = 0; Index < NavRows; ++Index)
	{
		const bool bRow = Bodies.IsValidIndex(Index);
		Show(FName(*FString::Printf(TEXT("NavRow_%d"), Index)), bRow);
		if (bRow)
		{
			SetText(FName(*FString::Printf(TEXT("NavName_%d"), Index)), Bodies[Index].Label.ToUpper(), Label);
			SetText(FName(*FString::Printf(TEXT("NavDist_%d"), Index)), Distance(Bodies[Index].DistanceM), Label);
			SetText(FName(*FString::Printf(TEXT("NavBrg_%d"), Index)), Bearing(Bodies[Index]), Faded(Label, 0.85f));
			SetText(FName(*FString::Printf(TEXT("NavElev_%d"), Index)), Elevation(Bodies[Index]), Faded(Label, 0.85f));
		}
	}
	Show(TEXT("NavEmpty"), Bodies.Num() == 0);

	TArray<FSpaceRadarContact> NearContacts = State.RadarContacts.FilterByPredicate([](const FSpaceRadarContact& Contact) { return !Contact.bBody; });
	SetText(TEXT("ContactsRange"), Distance(State.RadarRangeM), Label);
	SetText(TEXT("ContactsCount"), FString::Printf(TEXT("%d"), NearContacts.Num()), NearContacts.Num() > 0 ? Label : Faded(Label, 0.5f));
	for (int32 Index = 0; Index < ContactRows; ++Index)
	{
		const bool bRow = NearContacts.IsValidIndex(Index);
		Show(FName(*FString::Printf(TEXT("ContactRow_%d"), Index)), bRow);
		if (bRow)
		{
			SetText(FName(*FString::Printf(TEXT("ContactName_%d"), Index)), NearContacts[Index].Label, Label);
			SetText(FName(*FString::Printf(TEXT("ContactDist_%d"), Index)), Distance(NearContacts[Index].DistanceM), Label);
			SetText(FName(*FString::Printf(TEXT("ContactBrg_%d"), Index)), Bearing(NearContacts[Index]), Faded(Label, 0.85f));
			SetText(FName(*FString::Printf(TEXT("ContactElev_%d"), Index)), Elevation(NearContacts[Index]), Faded(Label, 0.85f));
		}
	}
	Show(TEXT("ContactsEmpty"), NearContacts.Num() == 0);

	SetText(TEXT("SelfGear"), State.GearLabel, State.bGearWarning && !State.bGearDown ? Red : State.bGearMoving ? Amber : Label);
	SetText(TEXT("SelfEngines"), FString::Printf(TEXT("%.0f%%"), State.EngineDemand * 100.f), Label);
	SetText(TEXT("SelfBoost"), FString::Printf(TEXT("%.0f%%"), State.BoostEnergy * 100.f), State.bBoostLocked ? Red : Label);
	SetText(TEXT("SelfAfterburner"), FString::Printf(TEXT("%.0f%%"), State.AfterburnerFuel * 100.f), State.bAfterburnerLocked ? Red : Label);
	SetText(TEXT("SelfState"), State.bLanded ? TEXT("LANDED") : TEXT("FLYING"), State.bLanded ? Instrument : Label);

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
	const ASpaceshipPawn* Ship = Cast<ASpaceshipPawn>(GetOwningPlayerPawn());
	FSpaceFlightHudState State = MakeState(Ship, HudMode ? HudMode->GetInt() : 1);
	// The HUD is drawn over the view, so its horizon and heading are the view's.
	if (const APlayerController* Player = GetOwningPlayer())
	{
		if (Player->PlayerCameraManager)
		{
			State = ApplyView(State, Ship, Player->PlayerCameraManager->GetCameraRotation(), Player->PlayerCameraManager->GetFOVAngle());
		}
	}
	ApplyState(State);
	DebugAdvance(InDeltaTime);
}

bool USpaceFlightHud::DebugIsShown(FName WidgetName) const
{
	const UWidget* Widget = Parts.FindRef(WidgetName);
	if (!Widget)
	{
		Widget = Texts.FindRef(WidgetName);
	}
	return Widget && Widget->GetVisibility() != ESlateVisibility::Collapsed && Widget->GetVisibility() != ESlateVisibility::Hidden;
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
	// The colour the state gave the switch, whether or not this layout draws it as a lamp.
	OutColor = LampColors.FindRef(Lamp);
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

void USpaceCockpitDisplays::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	UUserWidget::NativeTick(MyGeometry, InDeltaTime);
}

float USpaceCockpitDisplays::Steady(FName Figure, float Value, float Step, float FastChange)
{
	float& Last = LastFigures.FindOrAdd(Figure, Value);
	const bool bFast = FMath::Abs(Value - Last) > FastChange;
	Last = Value;
	return bFast ? FMath::RoundToFloat(Value / Step) * Step : Value;
}

FSpaceFlightHudState USpaceCockpitDisplays::SteadyState(const FSpaceFlightHudState& State)
{
	FSpaceFlightHudState Out = State;
	// Between two updates (StateRateHz, 5 a second): any real change (over 0.5 m/s, 0.05 G) shows tens
	// of m/s and half G steps; the exact figure only once the value holds still. At 3 m/s the last digit
	// still changed with every update while accelerating gently and blended.
	Out.SpeedCmS = Steady(TEXT("Speed"), State.SpeedCmS / 100.f, 10.f, 0.5f) * 100.f;
	Out.GForce = Steady(TEXT("G"), State.GForce, 0.5f, 0.05f);
	// The self status page's thrust in tens of per cent while it changes (and its engines with it).
	Out.EngineDemand = Steady(TEXT("Engine"), State.EngineDemand, 0.1f, 0.01f);
	// The thrusters page's figures in half G while they change.
	Out.ThrustG = FVector(Steady(TEXT("ThrustX"), float(State.ThrustG.X), 0.5f, 0.05f), Steady(TEXT("ThrustY"), float(State.ThrustG.Y), 0.5f, 0.05f),
		Steady(TEXT("ThrustZ"), float(State.ThrustG.Z), 0.5f, 0.05f));
	return Out;
}

void USpaceCockpitDisplays::BuildTree()
{
	using namespace SpaceHudStyle;

	UCanvasPanel* Root = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("Root"));
	WidgetTree->RootWidget = Root;

	auto Sized = [this](const FName Name, UWidget* Content, float Width, float Height)
	{
		USizeBox* Box = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), Name);
		if (Width > 0.f)
		{
			Box->SetWidthOverride(Width);
		}
		if (Height > 0.f)
		{
			Box->SetHeightOverride(Height);
		}
		Box->AddChild(Content);
		return Box;
	};
	auto Vertical = [](UVerticalBox* Box, UWidget* Child, EHorizontalAlignment Align, const FMargin& SlotPadding, bool bFill = false)
	{
		UVerticalBoxSlot* BoxSlot = Box->AddChildToVerticalBox(Child);
		BoxSlot->SetHorizontalAlignment(Align);
		BoxSlot->SetPadding(SlotPadding);
		if (bFill)
		{
			BoxSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		}
	};
	auto Horizontal = [](UHorizontalBox* Box, UWidget* Child, EVerticalAlignment Align, const FMargin& SlotPadding, bool bFill = false)
	{
		UHorizontalBoxSlot* BoxSlot = Box->AddChildToHorizontalBox(Child);
		BoxSlot->SetVerticalAlignment(Align);
		BoxSlot->SetPadding(SlotPadding);
		if (bFill)
		{
			BoxSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		}
	};
	auto Words = [&](const FName Name, const TCHAR* Initial, float Size, const FLinearColor& Color = SpaceHudStyle::MfdText)
	{
		UTextBlock* Text = MakeText(Name, Size, 30, TEXT("Label"));
		Text->SetText(FText::FromString(Initial));
		Text->SetColorAndOpacity(FSlateColor(Color));
		return Text;
	};
	auto Symbol = [this](const FName Name, ESpaceHudSymbol Kind, const FLinearColor& Color)
	{
		USpaceHudSymbol* New = WidgetTree->ConstructWidget<USpaceHudSymbol>(USpaceHudSymbol::StaticClass(), Name);
		New->Symbol = Kind;
		New->Color = Color;
		Parts.Add(Name, New);
		return New;
	};
	auto Rule = [&](const FName Name, float Width, float Alpha = 0.35f)
	{
		USpaceHudSymbol* Line = Symbol(Name, ESpaceHudSymbol::Line, Faded(MfdBlue, Alpha));
		Line->Thickness = 1.5f;
		Line->Points = { FVector2D(0.0, 0.5), FVector2D(1.0, 0.5) };
		return Sized(FName(*(Name.ToString() + TEXT("Box"))), Line, Width, 4.f);
	};
	// A switch as one of the keys beside the reference's MFDs: a rounded key, filled while on.
	auto Key = [&](const TCHAR* LampName, float Width, float Height, bool bButtonStyle)
	{
		const FName KeyName(LampName);
		UOverlay* Overlay = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass(), FName(*FString::Printf(TEXT("Pill_%s"), LampName)));
		USpaceHudLamp* NewLamp = WidgetTree->ConstructWidget<USpaceHudLamp>(USpaceHudLamp::StaticClass(), FName(*FString::Printf(TEXT("Lamp_%s"), LampName)));
		NewLamp->bButton = bButtonStyle;
		NewLamp->bBadge = !bButtonStyle;
		NewLamp->Color = MfdBlue;
		Lamps.Add(KeyName, NewLamp);
		UTextBlock* LampText = MakeText(FName(*FString::Printf(TEXT("LampLabel_%s"), LampName)), 22.f, 60, TEXT("Label"));
		LampText->SetText(FText::FromString(LampName));
		LampText->SetJustification(ETextJustify::Center);
		LampLabels.Add(KeyName, LampText);
		if (UOverlaySlot* LampSlot = Overlay->AddChildToOverlay(NewLamp))
		{
			LampSlot->SetHorizontalAlignment(HAlign_Fill);
			LampSlot->SetVerticalAlignment(VAlign_Fill);
		}
		if (UOverlaySlot* LabelSlot = Overlay->AddChildToOverlay(LampText))
		{
			LabelSlot->SetHorizontalAlignment(HAlign_Center);
			LabelSlot->SetVerticalAlignment(VAlign_Center);
		}
		return Sized(FName(*FString::Printf(TEXT("PillBox_%s"), LampName)), Overlay, Width, Height);
	};
	auto Keys = [&](const FName Name, const TArray<const TCHAR*>& LampNames)
	{
		UVerticalBox* Column = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), Name);
		for (const TCHAR* LampName : LampNames)
		{
			Vertical(Column, Key(LampName, 96.f, 46.f, true), HAlign_Center, FMargin(0.f, 0.f, 0.f, 12.f));
		}
		return Column;
	};
	auto Gauge = [this](const FName Name, int32 Segments)
	{
		USpaceHudGauge* NewGauge = WidgetTree->ConstructWidget<USpaceHudGauge>(USpaceHudGauge::StaticClass(), Name);
		NewGauge->Ticks = 0;
		NewGauge->Segments = Segments;
		Gauges.Add(Name, NewGauge);
		return NewGauge;
	};
	// One screen: glass, a title over a rule, the content, and the reference's page tab between arrows.
	auto Place = [&](UWidget* Widget, const FBox2D& Rect)
	{
		UCanvasPanelSlot* ScreenSlot = Root->AddChildToCanvas(Widget);
		ScreenSlot->SetPosition(Rect.Min);
		ScreenSlot->SetSize(Rect.GetSize());
	};
	// An MFD: its pages in a switcher under the title, the page tab showing which one is up.
	auto Screen = [&](const TCHAR* ScreenName, const FBox2D& Rect, const TArray<UWidget*>& PageWidgets)
	{
		const TCHAR* Title = *PageTitles(PageSwitchers.Num())[0];
		UWidgetSwitcher* Content = WidgetTree->ConstructWidget<UWidgetSwitcher>(UWidgetSwitcher::StaticClass(), FName(*FString::Printf(TEXT("%sSwitcher"), ScreenName)));
		for (UWidget* PageWidget : PageWidgets)
		{
			Content->AddChild(PageWidget);
		}
		PageSwitchers.Add(Content);
		UOverlay* Overlay = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass(), FName(*FString::Printf(TEXT("%sScreen"), ScreenName)));
		if (UOverlaySlot* GlassSlot = Overlay->AddChildToOverlay(Symbol(FName(*FString::Printf(TEXT("%sGlass"), ScreenName)), ESpaceHudSymbol::MfdGlass, MfdBlue)))
		{
			GlassSlot->SetHorizontalAlignment(HAlign_Fill);
			GlassSlot->SetVerticalAlignment(VAlign_Fill);
		}
		UVerticalBox* Column = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), FName(*FString::Printf(TEXT("%sColumn"), ScreenName)));
		Vertical(Column, Words(FName(*FString::Printf(TEXT("%sTitle"), ScreenName)), Title, 26.f, Faded(MfdText, 0.85f)), HAlign_Left, FMargin(4.f, 0.f, 0.f, 4.f));
		Vertical(Column, Rule(FName(*FString::Printf(TEXT("%sRule"), ScreenName)), 0.f), HAlign_Fill, FMargin(0.f, 0.f, 0.f, 10.f));
		Vertical(Column, Content, HAlign_Fill, FMargin(0.f), true);
		UHorizontalBox* Pages = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), FName(*FString::Printf(TEXT("%sPages"), ScreenName)));
		Horizontal(Pages, Words(FName(*FString::Printf(TEXT("%sPrev"), ScreenName)), TEXT("<"), 26.f, MfdBlue), VAlign_Center, FMargin(4.f, 0.f, 12.f, 0.f));
		UOverlay* Tab = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass(), FName(*FString::Printf(TEXT("%sTab"), ScreenName)));
		USpaceHudLamp* TabShape = WidgetTree->ConstructWidget<USpaceHudLamp>(USpaceHudLamp::StaticClass(), FName(*FString::Printf(TEXT("%sTabShape"), ScreenName)));
		TabShape->bButton = true;
		TabShape->Color = MfdBlue;
		TabShape->Intensity = 0.6f;
		TabShape->Target = 0.6f;
		if (UOverlaySlot* ShapeSlot = Tab->AddChildToOverlay(TabShape))
		{
			ShapeSlot->SetHorizontalAlignment(HAlign_Fill);
			ShapeSlot->SetVerticalAlignment(VAlign_Fill);
		}
		if (UOverlaySlot* PageSlot = Tab->AddChildToOverlay(Words(FName(*FString::Printf(TEXT("%sPage"), ScreenName)), Title, 22.f, MfdText)))
		{
			PageSlot->SetHorizontalAlignment(HAlign_Center);
			PageSlot->SetVerticalAlignment(VAlign_Center);
			PageSlot->SetPadding(FMargin(0.f, 3.f));
		}
		Horizontal(Pages, Tab, VAlign_Fill, FMargin(0.f), true);
		Horizontal(Pages, Words(FName(*FString::Printf(TEXT("%sNext"), ScreenName)), TEXT(">"), 26.f, MfdBlue), VAlign_Center, FMargin(12.f, 0.f, 4.f, 0.f));
		Vertical(Column, Sized(FName(*FString::Printf(TEXT("%sPagesBox"), ScreenName)), Pages, 0.f, 38.f), HAlign_Fill, FMargin(0.f, 8.f, 0.f, 0.f));
		if (UOverlaySlot* ColumnSlot = Overlay->AddChildToOverlay(Column))
		{
			ColumnSlot->SetPadding(FMargin(26.f, 16.f, 26.f, 16.f));
			ColumnSlot->SetHorizontalAlignment(HAlign_Fill);
			ColumnSlot->SetVerticalAlignment(VAlign_Fill);
		}
		Place(Overlay, Rect);
	};
	// One of the centre column's small screens: glass and the content, which brings its own header.
	auto SmallScreen = [&](const TCHAR* ScreenName, const FBox2D& Rect, UWidget* Content)
	{
		UOverlay* Overlay = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass(), FName(*FString::Printf(TEXT("%sScreen"), ScreenName)));
		if (UOverlaySlot* GlassSlot = Overlay->AddChildToOverlay(Symbol(FName(*FString::Printf(TEXT("%sGlass"), ScreenName)), ESpaceHudSymbol::MfdGlass, MfdBlue)))
		{
			GlassSlot->SetHorizontalAlignment(HAlign_Fill);
			GlassSlot->SetVerticalAlignment(VAlign_Fill);
		}
		if (UOverlaySlot* ContentSlot = Overlay->AddChildToOverlay(Content))
		{
			ContentSlot->SetPadding(FMargin(12.f, 9.f, 12.f, 9.f));
			ContentSlot->SetHorizontalAlignment(HAlign_Fill);
			ContentSlot->SetVerticalAlignment(VAlign_Fill);
		}
		Place(Overlay, Rect);
	};
	// A small screen's header or footer: a caption on the left, a value on the right.
	auto Line = [&](const FName Name, const TCHAR* Caption, float CaptionSize, const FName ValueName, const FLinearColor& CaptionColor)
	{
		UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), Name);
		Horizontal(Row, Words(FName(*(Name.ToString() + TEXT("Caption"))), Caption, CaptionSize, CaptionColor), VAlign_Center, FMargin(0.f), true);
		if (!ValueName.IsNone())
		{
			Horizontal(Row, Words(ValueName, TEXT("-"), 19.f), VAlign_Center, FMargin(0.f));
		}
		return Row;
	};

	// --- Left display, FLIGHT: like the reference's power page, keys on the side towards the middle -----
	UHorizontalBox* Flight = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("FlightContent"));
	UVerticalBox* FlightMain = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("FlightMain"));
	// The small figures along the top, each over its caption.
	UHorizontalBox* Figures = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("FlightFigures"));
	auto Figure = [&](const TCHAR* Caption, const FName ValueName)
	{
		UVerticalBox* Box = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), FName(*FString::Printf(TEXT("Figure_%s"), Caption)));
		Vertical(Box, Words(ValueName, TEXT("-"), 22.f), HAlign_Center, FMargin(0.f));
		Vertical(Box, Words(FName(*FString::Printf(TEXT("FigureCaption_%s"), Caption)), Caption, 16.f, Faded(MfdText, 0.55f)), HAlign_Center, FMargin(0.f));
		Horizontal(Figures, Box, VAlign_Top, FMargin(0.f), true);
	};
	Figure(TEXT("LIMIT"), TEXT("RowLimitValue"));
	Figure(TEXT("G MAX"), TEXT("GMax"));
	Figure(TEXT("MODE"), TEXT("ModeText"));
	Vertical(FlightMain, Figures, HAlign_Fill, FMargin(0.f, 0.f, 0.f, 6.f));
	Vertical(FlightMain, Rule(TEXT("FlightFiguresRule"), 0.f, 0.2f), HAlign_Fill, FMargin(0.f, 0.f, 0.f, 8.f));
	UHorizontalBox* Readout = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("FlightReadout"));
	UVerticalBox* Big = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("FlightBig"));
	Vertical(Big, Words(TEXT("SpeedValue"), TEXT("0"), 58.f), HAlign_Left, FMargin(0.f));
	Vertical(Big, Words(TEXT("SpeedUnit"), TEXT("m/s"), 20.f, Faded(MfdText, 0.6f)), HAlign_Left, FMargin(2.f, 0.f, 0.f, 14.f));
	Vertical(Big, Words(TEXT("GText"), TEXT("0.0 G"), 34.f), HAlign_Left, FMargin(0.f));
	Horizontal(Readout, Big, VAlign_Top, FMargin(0.f), true);
	auto Bar = [&](const TCHAR* Caption, const FName GaugeName, const FName ValueName)
	{
		UVerticalBox* Box = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), FName(*FString::Printf(TEXT("%sColumn"), *GaugeName.ToString())));
		Vertical(Box, Sized(FName(*FString::Printf(TEXT("%sBox"), *GaugeName.ToString())), Gauge(GaugeName, 8), 34.f, 186.f), HAlign_Center, FMargin(0.f, 0.f, 0.f, 4.f));
		Vertical(Box, Words(FName(*FString::Printf(TEXT("%sTitle"), *GaugeName.ToString())), Caption, 18.f, Faded(MfdText, 0.75f)), HAlign_Center, FMargin(0.f));
		Vertical(Box, Words(ValueName, TEXT("-"), 18.f), HAlign_Center, FMargin(0.f));
		Horizontal(Readout, Box, VAlign_Top, FMargin(8.f, 0.f, 0.f, 0.f));
	};
	Bar(TEXT("SPD"), TEXT("SpeedGauge"), TEXT("SpeedPercent"));
	Bar(TEXT("BST"), TEXT("BoostGauge"), TEXT("BoostText"));
	Bar(TEXT("AB"), TEXT("AfterburnerGauge"), TEXT("AfterburnerValue"));
	Bar(TEXT("G"), TEXT("GGauge"), TEXT("GValue"));
	if (USpaceHudGauge* Afterburner = Gauges.FindRef(TEXT("AfterburnerGauge")))
	{
		Afterburner->ReserveZone = 0.25f;
		Afterburner->ReserveColor = Red;
	}
	Vertical(FlightMain, Readout, HAlign_Fill, FMargin(0.f), true);
	Horizontal(Flight, FlightMain, VAlign_Fill, FMargin(0.f), true);
	Horizontal(Flight, Keys(TEXT("FlightKeys"), { TEXT("CPLD"), TEXT("GSAF"), TEXT("CSTB"), TEXT("BOOST"), TEXT("PREC") }), VAlign_Top,
		FMargin(16.f, 0.f, 0.f, 0.f));
	// --- Left display, page 2: THRUSTERS - what each direction puts out against what it can -----------
	auto AlignedWords = [&](const FName Name, const TCHAR* Initial, float Size, ETextJustify::Type Justify, const FLinearColor& Color = SpaceHudStyle::MfdText)
	{
		UTextBlock* Text = Words(Name, Initial, Size, Color);
		Text->SetJustification(Justify);
		return Text;
	};
	UVerticalBox* ThrustPage = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("ThrustPage"));
	for (const TCHAR* Axis : { TEXT("MAIN"), TEXT("RETRO"), TEXT("STRAFE"), TEXT("UP"), TEXT("DOWN") })
	{
		UHorizontalBox* ThrustLine = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), FName(*FString::Printf(TEXT("ThrustRow_%s"), Axis)));
		Horizontal(ThrustLine, Sized(FName(*FString::Printf(TEXT("ThrustNameBox_%s"), Axis)), Words(FName(*FString::Printf(TEXT("ThrustName_%s"), Axis)), Axis, 21.f), 104.f, 0.f),
			VAlign_Center, FMargin(0.f));
		// The strafe row says which side it fires to.
		Horizontal(ThrustLine, Sized(FName(*FString::Printf(TEXT("ThrustSideBox_%s"), Axis)),
			FCString::Strcmp(Axis, TEXT("STRAFE")) == 0 ? static_cast<UWidget*>(Words(TEXT("ThrustStrafeSide"), TEXT(""), 21.f)) : static_cast<UWidget*>(WidgetTree->ConstructWidget<USpacer>(USpacer::StaticClass())),
			22.f, 0.f), VAlign_Center, FMargin(0.f));
		USpaceHudGauge* ThrustGauge = Gauge(FName(*FString::Printf(TEXT("ThrustGauge_%s"), Axis)), 12);
		ThrustGauge->bHorizontal = true;
		Horizontal(ThrustLine, Sized(FName(*FString::Printf(TEXT("ThrustGaugeBox_%s"), Axis)), ThrustGauge, 0.f, 26.f), VAlign_Center, FMargin(0.f, 0.f, 12.f, 0.f), true);
		Horizontal(ThrustLine, Sized(FName(*FString::Printf(TEXT("ThrustValueBox_%s"), Axis)),
			AlignedWords(FName(*FString::Printf(TEXT("ThrustValue_%s"), Axis)), TEXT("-"), 19.f, ETextJustify::Right), 128.f, 0.f), VAlign_Center, FMargin(0.f));
		Vertical(ThrustPage, ThrustLine, HAlign_Fill, FMargin(0.f, 7.f));
	}
	Vertical(ThrustPage, Rule(TEXT("ThrustRule"), 0.f, 0.2f), HAlign_Fill, FMargin(0.f, 6.f));
	UHorizontalBox* ThrustFooter = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("ThrustFooter"));
	Horizontal(ThrustFooter, Words(TEXT("ThrustBoost"), TEXT("BOOST OFF"), 20.f), VAlign_Center, FMargin(0.f), true);
	Horizontal(ThrustFooter, Words(TEXT("ThrustGSafe"), TEXT("G-SAFE"), 20.f), VAlign_Center, FMargin(0.f));
	Vertical(ThrustPage, ThrustFooter, HAlign_Fill, FMargin(0.f, 4.f));

	// --- Left display, page 3: NAVIGATION - master mode, cruise, and the bodies with range and bearing ---
	UVerticalBox* NavPage = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("NavPage"));
	UHorizontalBox* NavTop = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("NavTop"));
	UVerticalBox* NavModeBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("NavModeBox"));
	Vertical(NavModeBox, Words(TEXT("NavMode"), TEXT("SCM"), 46.f), HAlign_Left, FMargin(0.f));
	Vertical(NavModeBox, Words(TEXT("NavSub"), TEXT("FLIGHT"), 20.f, Faded(MfdText, 0.8f)), HAlign_Left, FMargin(2.f, 0.f, 0.f, 0.f));
	Horizontal(NavTop, NavModeBox, VAlign_Top, FMargin(0.f, 0.f, 24.f, 0.f));
	UVerticalBox* NavFigures = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("NavFigures"));
	for (const TPair<const TCHAR*, const TCHAR*>& NavFigure : { TPair<const TCHAR*, const TCHAR*>(TEXT("SPEED"), TEXT("NavSpeed")),
		TPair<const TCHAR*, const TCHAR*>(TEXT("LIMIT"), TEXT("NavLimit")), TPair<const TCHAR*, const TCHAR*>(TEXT("CRUISE"), TEXT("NavCruise")) })
	{
		UHorizontalBox* FigureLine = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), FName(*FString::Printf(TEXT("NavFigure_%s"), NavFigure.Key)));
		Horizontal(FigureLine, Words(FName(*FString::Printf(TEXT("NavCaption_%s"), NavFigure.Key)), NavFigure.Key, 17.f, Faded(MfdText, 0.55f)), VAlign_Center, FMargin(0.f), true);
		Horizontal(FigureLine, Words(NavFigure.Value, TEXT("-"), 20.f), VAlign_Center, FMargin(0.f));
		Vertical(NavFigures, FigureLine, HAlign_Fill, FMargin(0.f, 1.f));
	}
	Horizontal(NavTop, NavFigures, VAlign_Top, FMargin(0.f), true);
	Vertical(NavPage, NavTop, HAlign_Fill, FMargin(0.f, 0.f, 0.f, 8.f));
	Vertical(NavPage, Rule(TEXT("NavRule"), 0.f, 0.2f), HAlign_Fill, FMargin(0.f, 0.f, 0.f, 4.f));
	auto ListHeader = [&](const FName Name, const TCHAR* First)
	{
		UHorizontalBox* Header = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), Name);
		Horizontal(Header, Words(FName(*(Name.ToString() + TEXT("Name"))), First, 16.f, Faded(MfdText, 0.55f)), VAlign_Center, FMargin(0.f), true);
		Horizontal(Header, Sized(FName(*(Name.ToString() + TEXT("DistBox"))), AlignedWords(FName(*(Name.ToString() + TEXT("Dist"))), TEXT("RANGE"), 16.f, ETextJustify::Right,
			Faded(MfdText, 0.55f)), 120.f, 0.f), VAlign_Center, FMargin(0.f));
		Horizontal(Header, Sized(FName(*(Name.ToString() + TEXT("BrgBox"))), AlignedWords(FName(*(Name.ToString() + TEXT("Brg"))), TEXT("BRG"), 16.f, ETextJustify::Right,
			Faded(MfdText, 0.55f)), 74.f, 0.f), VAlign_Center, FMargin(0.f));
		Horizontal(Header, Sized(FName(*(Name.ToString() + TEXT("ElevBox"))), AlignedWords(FName(*(Name.ToString() + TEXT("Elev"))), TEXT("EL"), 16.f, ETextJustify::Right,
			Faded(MfdText, 0.55f)), 62.f, 0.f), VAlign_Center, FMargin(0.f));
		return Header;
	};
	// A row of a list: name, range, bearing, elevation.
	auto ListRow = [&](UVerticalBox* Into, const FString& Prefix, int32 Index)
	{
		// The row and its rule in one box: a hidden row takes its rule with it.
		const FString Row = FString::Printf(TEXT("%sRow_%d"), *Prefix, Index);
		UVerticalBox* RowBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), FName(*Row));
		Parts.Add(FName(*Row), RowBox);
		UHorizontalBox* ListLine = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), FName(*(Row + TEXT("Line"))));
		Horizontal(ListLine, Words(FName(*FString::Printf(TEXT("%sName_%d"), *Prefix, Index)), TEXT("-"), 20.f), VAlign_Center, FMargin(0.f), true);
		Horizontal(ListLine, Sized(FName(*(Row + TEXT("DistBox"))), AlignedWords(FName(*FString::Printf(TEXT("%sDist_%d"), *Prefix, Index)), TEXT("-"), 20.f, ETextJustify::Right), 120.f, 0.f),
			VAlign_Center, FMargin(0.f));
		Horizontal(ListLine, Sized(FName(*(Row + TEXT("BrgBox"))), AlignedWords(FName(*FString::Printf(TEXT("%sBrg_%d"), *Prefix, Index)), TEXT("-"), 19.f, ETextJustify::Right), 74.f, 0.f),
			VAlign_Center, FMargin(0.f));
		Horizontal(ListLine, Sized(FName(*(Row + TEXT("ElevBox"))), AlignedWords(FName(*FString::Printf(TEXT("%sElev_%d"), *Prefix, Index)), TEXT("-"), 19.f, ETextJustify::Right), 62.f, 0.f),
			VAlign_Center, FMargin(0.f));
		Vertical(RowBox, ListLine, HAlign_Fill, FMargin(0.f, 3.f));
		Vertical(RowBox, Rule(FName(*(Row + TEXT("Rule"))), 0.f, 0.12f), HAlign_Fill, FMargin(0.f, 1.f));
		Vertical(Into, RowBox, HAlign_Fill, FMargin(0.f));
	};
	Vertical(NavPage, ListHeader(TEXT("NavHeader"), TEXT("BODY")), HAlign_Fill, FMargin(0.f, 0.f, 0.f, 2.f));
	for (int32 Index = 0; Index < NavRows; ++Index)
	{
		ListRow(NavPage, TEXT("Nav"), Index);
	}
	Vertical(NavPage, Words(TEXT("NavEmpty"), TEXT("NO BODY NEAR"), 20.f, Faded(MfdText, 0.5f)), HAlign_Left, FMargin(0.f, 6.f));
	Screen(TEXT("Flight"), ScreenRect(TEXT("left")), { Flight, ThrustPage, NavPage });

	// --- Right display, STATUS: keys on the side towards the middle, a list like the contacts page -------
	UHorizontalBox* Status = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("StatusContent"));
	Horizontal(Status, Keys(TEXT("StatusKeys"), { TEXT("MODE"), TEXT("GEAR"), TEXT("CRUISE") }), VAlign_Top, FMargin(0.f, 0.f, 16.f, 0.f));
	UVerticalBox* List = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("StatusList"));
	auto Row = [&](const TCHAR* Name, const FName ValueName)
	{
		UHorizontalBox* Line = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), FName(*FString::Printf(TEXT("Row_%s"), Name)));
		Horizontal(Line, Words(FName(*FString::Printf(TEXT("RowName_%s"), Name)), *FString::Printf(TEXT("> %s"), Name), 20.f), VAlign_Center, FMargin(0.f), true);
		UOverlay* Value = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass(), FName(*FString::Printf(TEXT("RowPill_%s"), Name)));
		USpaceHudLamp* Pill = WidgetTree->ConstructWidget<USpaceHudLamp>(USpaceHudLamp::StaticClass(), FName(*FString::Printf(TEXT("RowPillShape_%s"), Name)));
		Pill->bBadge = true;
		Pill->Color = MfdBlue;
		Pill->Intensity = 1.f;
		Pill->Target = 1.f;
		if (UOverlaySlot* PillSlot = Value->AddChildToOverlay(Pill))
		{
			PillSlot->SetHorizontalAlignment(HAlign_Fill);
			PillSlot->SetVerticalAlignment(VAlign_Fill);
		}
		if (UOverlaySlot* ValueSlot = Value->AddChildToOverlay(Words(ValueName, TEXT("-"), 20.f)))
		{
			ValueSlot->SetHorizontalAlignment(HAlign_Center);
			ValueSlot->SetVerticalAlignment(VAlign_Center);
		}
		Horizontal(Line, Sized(FName(*FString::Printf(TEXT("RowPillBox_%s"), Name)), Value, 118.f, 30.f), VAlign_Center, FMargin(0.f));
		Vertical(List, Line, HAlign_Fill, FMargin(0.f, 2.f));
		Vertical(List, Rule(FName(*FString::Printf(TEXT("RowRule_%s"), Name)), 0.f, 0.15f), HAlign_Fill, FMargin(0.f, 2.f));
	};
	Row(TEXT("FLIGHT"), TEXT("SubModeText"));
	Row(TEXT("GEAR"), TEXT("RowGearValue"));
	Row(TEXT("CRUISE"), TEXT("RowCruiseValue"));
	Row(TEXT("R-ALT"), TEXT("RowRAltValue"));
	Row(TEXT("VSI"), TEXT("RowVsiValue"));
	Row(TEXT("ATMO"), TEXT("RowAtmoValue"));
	Horizontal(Status, List, VAlign_Top, FMargin(0.f), true);
	// --- Right display, page 2: CONTACTS - the radar's contacts as a list, like the reference's -----------
	UVerticalBox* ContactsPage = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("ContactsPage"));
	UHorizontalBox* ContactsTop = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("ContactsTop"));
	Horizontal(ContactsTop, Words(TEXT("ContactsRangeCaption"), TEXT("RANGE"), 17.f, Faded(MfdText, 0.55f)), VAlign_Center, FMargin(0.f, 0.f, 12.f, 0.f));
	Horizontal(ContactsTop, Words(TEXT("ContactsRange"), TEXT("-"), 20.f), VAlign_Center, FMargin(0.f), true);
	Horizontal(ContactsTop, Words(TEXT("ContactsCountCaption"), TEXT("CONTACTS"), 17.f, Faded(MfdText, 0.55f)), VAlign_Center, FMargin(0.f, 0.f, 12.f, 0.f));
	Horizontal(ContactsTop, Words(TEXT("ContactsCount"), TEXT("0"), 20.f), VAlign_Center, FMargin(0.f));
	Vertical(ContactsPage, ContactsTop, HAlign_Fill, FMargin(0.f, 0.f, 0.f, 6.f));
	Vertical(ContactsPage, ListHeader(TEXT("ContactsHeader"), TEXT("CONTACT")), HAlign_Fill, FMargin(0.f, 0.f, 0.f, 2.f));
	for (int32 Index = 0; Index < ContactRows; ++Index)
	{
		ListRow(ContactsPage, TEXT("Contact"), Index);
	}
	Vertical(ContactsPage, Words(TEXT("ContactsEmpty"), TEXT("NO CONTACTS IN RANGE"), 20.f, Faded(MfdText, 0.5f)), HAlign_Left, FMargin(0.f, 6.f));

	// --- Right display, page 3: SELF STATUS - the ship large, with its state beside it -------------------
	UHorizontalBox* SelfPage = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("SelfPage"));
	USpaceHudShipStatus* ShipLarge = WidgetTree->ConstructWidget<USpaceHudShipStatus>(USpaceHudShipStatus::StaticClass(), TEXT("ShipStatusLarge"));
	ShipLarge->Color = MfdBlue;
	Parts.Add(TEXT("ShipStatusLarge"), ShipLarge);
	Horizontal(SelfPage, ShipLarge, VAlign_Fill, FMargin(0.f, 0.f, 16.f, 0.f), true);
	UVerticalBox* SelfList = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("SelfList"));
	for (const TPair<const TCHAR*, const TCHAR*>& SelfFigure : { TPair<const TCHAR*, const TCHAR*>(TEXT("STATE"), TEXT("SelfState")),
		TPair<const TCHAR*, const TCHAR*>(TEXT("GEAR"), TEXT("SelfGear")), TPair<const TCHAR*, const TCHAR*>(TEXT("ENGINES"), TEXT("SelfEngines")),
		TPair<const TCHAR*, const TCHAR*>(TEXT("BOOST"), TEXT("SelfBoost")), TPair<const TCHAR*, const TCHAR*>(TEXT("AB FUEL"), TEXT("SelfAfterburner")) })
	{
		// Caption and value on one line each, tight: five of them fill the page above its tab.
		Vertical(SelfList, Words(FName(*FString::Printf(TEXT("SelfCaption_%s"), SelfFigure.Key)), SelfFigure.Key, 14.f, Faded(MfdText, 0.55f)), HAlign_Left, FMargin(0.f, 1.f, 0.f, 0.f));
		Vertical(SelfList, Words(SelfFigure.Value, TEXT("-"), 20.f), HAlign_Left, FMargin(0.f, 0.f, 0.f, 1.f));
	}
	Horizontal(SelfPage, Sized(TEXT("SelfListBox"), SelfList, 150.f, 0.f), VAlign_Top, FMargin(0.f));
	Screen(TEXT("Status"), ScreenRect(TEXT("right")), { Status, ContactsPage, SelfPage });

	// --- Centre column, top: RADAR, the disc in the middle of the reference's dashboard --------------
	UVerticalBox* RadarPage = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("RadarPage"));
	Vertical(RadarPage, Line(TEXT("RadarHeader"), TEXT("RADAR"), 19.f, TEXT("RadarRange"), Faded(MfdText, 0.85f)), HAlign_Fill, FMargin(2.f, 0.f, 2.f, 2.f));
	Vertical(RadarPage, Rule(TEXT("RadarRule"), 0.f), HAlign_Fill, FMargin(0.f, 0.f, 0.f, 4.f));
	USpaceHudRadar* Radar = WidgetTree->ConstructWidget<USpaceHudRadar>(USpaceHudRadar::StaticClass(), TEXT("Radar"));
	Radar->Color = MfdBlue;
	Radar->Accent = MfdText;
	Parts.Add(TEXT("Radar"), Radar);
	Vertical(RadarPage, Radar, HAlign_Fill, FMargin(0.f), true);
	UHorizontalBox* RadarFooter = Line(TEXT("RadarFooter"), TEXT("HDG"), 16.f, TEXT("RadarHeading"), Faded(MfdText, 0.55f));
	Horizontal(RadarFooter, Words(TEXT("RadarCountCaption"), TEXT("CT"), 16.f, Faded(MfdText, 0.55f)), VAlign_Center, FMargin(14.f, 0.f, 6.f, 0.f));
	Horizontal(RadarFooter, Words(TEXT("RadarCount"), TEXT("0"), 19.f), VAlign_Center, FMargin(0.f));
	Vertical(RadarPage, RadarFooter, HAlign_Fill, FMargin(2.f, 3.f, 2.f, 0.f));
	SmallScreen(TEXT("Radar"), ScreenRect(TEXT("centre_top")), RadarPage);

	// --- Centre column, bottom: SELF STATUS, the ship from above -----------------------------------
	UVerticalBox* ShipPage = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("ShipPage"));
	Vertical(ShipPage, Line(TEXT("ShipHeader"), TEXT("SELF STATUS"), 19.f, NAME_None, Faded(MfdText, 0.85f)), HAlign_Fill, FMargin(2.f, 0.f, 2.f, 2.f));
	Vertical(ShipPage, Rule(TEXT("ShipRule"), 0.f), HAlign_Fill, FMargin(0.f, 0.f, 0.f, 2.f));
	USpaceHudShipStatus* ShipStatus = WidgetTree->ConstructWidget<USpaceHudShipStatus>(USpaceHudShipStatus::StaticClass(), TEXT("ShipStatus"));
	ShipStatus->Color = MfdBlue;
	Parts.Add(TEXT("ShipStatus"), ShipStatus);
	Vertical(ShipPage, ShipStatus, HAlign_Fill, FMargin(0.f), true);
	UHorizontalBox* ShipFooter = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("ShipFooter"));
	// Gear on the left, the engines' thrust (LANDED on the ground) on the right: "GEAR MOVING" and
	// "THR 100%" did not fit side by side on ~11 cm of glass.
	Horizontal(ShipFooter, Words(TEXT("ShipGearCaption"), TEXT("GEAR"), 15.f, Faded(MfdText, 0.55f)), VAlign_Center, FMargin(0.f, 0.f, 5.f, 0.f));
	Horizontal(ShipFooter, Words(TEXT("ShipGear"), TEXT("UP"), 17.f), VAlign_Center, FMargin(0.f), true);
	Horizontal(ShipFooter, Words(TEXT("ShipThrust"), TEXT("0%"), 17.f), VAlign_Center, FMargin(0.f));
	Vertical(ShipPage, ShipFooter, HAlign_Fill, FMargin(2.f, 2.f, 2.f, 0.f));
	SmallScreen(TEXT("Ship"), ScreenRect(TEXT("centre_bottom")), ShipPage);

	SetVisibility(ESlateVisibility::HitTestInvisible);
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

FBox2D USpaceCockpitDisplays::ScreenRect(const FString& Name)
{
	if (Name == TEXT("left"))
	{
		return FBox2D(FVector2D(0.0, 0.0), FVector2D(DisplayWidth, DisplayHeight));
	}
	if (Name == TEXT("right"))
	{
		return FBox2D(FVector2D(DisplayWidth, 0.0), FVector2D(2.0 * DisplayWidth, DisplayHeight));
	}
	if (Name == TEXT("centre_top"))
	{
		return FBox2D(FVector2D(2.0 * DisplayWidth, 0.0), FVector2D(CanvasWidth, CentreTopHeight));
	}
	if (Name == TEXT("centre_bottom"))
	{
		return FBox2D(FVector2D(2.0 * DisplayWidth, CentreTopHeight), FVector2D(CanvasWidth, CanvasHeight));
	}
	return FBox2D(ForceInit);
}

FVector4 USpaceCockpitDisplays::DebugGetScreenRect(const FString& Name)
{
	const FBox2D Rect = ScreenRect(Name);
	return Rect.bIsValid ? FVector4(Rect.Min.X, Rect.Min.Y, Rect.Max.X, Rect.Max.Y) : FVector4(0.0, 0.0, 0.0, 0.0);
}

TArray<FSpaceRadarContact> USpaceCockpitDisplays::MakeRadarContacts(const ASpaceshipPawn* Ship, float RangeM, int32 MaxContacts)
{
	TArray<FSpaceRadarContact> Bodies;
	TArray<FSpaceRadarContact> Near;
	if (!Ship || !Ship->GetWorld())
	{
		return Bodies;
	}
	const FTransform Frame = Ship->GetActorTransform();
	const FVector Origin = Frame.GetLocation();
	const double RangeCm = double(RangeM) * 100.0;
	auto Contact = [&Frame](const FVector& Location, double DistanceCm, bool bBody, const FString& Label)
	{
		const FVector Local = Frame.InverseTransformPositionNoScale(Location);
		FSpaceRadarContact Out;
		Out.Position = FVector2D(Local.Y / 100.0, Local.X / 100.0);
		Out.HeightM = float(Local.Z / 100.0);
		Out.DistanceM = float(DistanceCm / 100.0);
		Out.bBody = bBody;
		Out.Label = Label;
		return Out;
	};
	for (TActorIterator<AActor> It(Ship->GetWorld()); It; ++It)
	{
		const AActor* Actor = *It;
		if (Actor == Ship || Actor->IsHidden())
		{
			continue;
		}
		if (const ACelestialBody* Body = Cast<ACelestialBody>(Actor))
		{
			Bodies.Add(Contact(Body->GetActorLocation(), FMath::Max(Body->GetSurfaceDistance(Origin), 0.0), true, Body->GetDisplayName().ToString()));
			continue;
		}
		if (const ADistantBody* Distant = Cast<ADistantBody>(Actor))
		{
			const double Surface = FVector::Dist(Origin, Distant->GetActorLocation()) - double(Distant->GetRadiusKm()) * 100000.0;
			Bodies.Add(Contact(Distant->GetActorLocation(), FMath::Max(Surface, 0.0), true, Distant->GetDisplayName().ToString()));
			continue;
		}
		// Objects: other ships and characters, and meshes that can be hit (asteroids, stations, wrecks).
		const AStaticMeshActor* MeshActor = Cast<AStaticMeshActor>(Actor);
		const bool bObject = Actor->IsA<APawn>() || (MeshActor && MeshActor->GetStaticMeshComponent() && MeshActor->GetStaticMeshComponent()->GetStaticMesh()
			&& MeshActor->GetActorEnableCollision() && MeshActor->GetStaticMeshComponent()->IsCollisionEnabled());
		if (!bObject)
		{
			continue;
		}
		FVector Centre, Extent;
		Actor->GetActorBounds(true, Centre, Extent);
		// Larger than the whole range (ground, a planet mesh): not a contact.
		if (Extent.Size() > RangeCm)
		{
			continue;
		}
		const double Distance = FVector::Dist(Origin, Centre);
		if (Distance <= RangeCm)
		{
			// What it is, as far as the game knows: a ship, someone on foot, or the mesh's name (ROCK_A).
			FString Label = Actor->IsA<ASpaceshipPawn>() ? TEXT("SHIP") : Actor->IsA<APawn>() ? TEXT("EVA") : FString();
			if (Label.IsEmpty() && MeshActor)
			{
				Label = MeshActor->GetStaticMeshComponent()->GetStaticMesh()->GetName();
				Label.RemoveFromStart(TEXT("SM_"));
				Label = Label.Replace(TEXT("_"), TEXT(" ")).ToUpper();
			}
			Near.Add(Contact(Centre, Distance, false, Label));
		}
	}
	Near.Sort([](const FSpaceRadarContact& A, const FSpaceRadarContact& B) { return A.DistanceM < B.DistanceM; });
	if (Near.Num() > MaxContacts)
	{
		Near.SetNum(FMath::Max(MaxContacts, 0));
	}
	Bodies.Append(Near);
	return Bodies;
}

FSpaceFlightHudState USpaceCockpitDisplays::MakeDisplayState(const ASpaceshipPawn* Ship, float RadarRangeM)
{
	FSpaceFlightHudState State = MakeState(Ship, 1);
	State.RadarRangeM = RadarRangeM;
	State.RadarContacts = MakeRadarContacts(Ship, RadarRangeM);
	return State;
}

void USpaceCockpitDisplays::SetCentreColumn(bool bOn)
{
	for (const TCHAR* Name : { TEXT("RadarScreen"), TEXT("ShipScreen") })
	{
		if (UWidget* Screen = WidgetTree ? WidgetTree->FindWidget(Name) : nullptr)
		{
			Screen->SetVisibility(bOn ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
		}
	}
}

void USpaceCockpitDisplays::SetShip(const AActor* Ship)
{
	for (const TCHAR* ShipPart : { TEXT("ShipStatus"), TEXT("ShipStatusLarge") })
	{
		if (USpaceHudShipStatus* ShipStatus = Cast<USpaceHudShipStatus>(Parts.FindRef(ShipPart)))
		{
			ShipStatus->SetShip(Ship);
		}
	}
}

const TArray<FString>& USpaceCockpitDisplays::PageTitles(int32 Display)
{
	static const TArray<FString> Left = { TEXT("FLIGHT"), TEXT("THRUSTERS"), TEXT("NAVIGATION") };
	static const TArray<FString> Right = { TEXT("STATUS"), TEXT("CONTACTS"), TEXT("SELF STATUS") };
	return Display == 0 ? Left : Right;
}

void USpaceCockpitDisplays::SetPages(int32 LeftPage, int32 RightPage)
{
	const TCHAR* Screens[] = { TEXT("Flight"), TEXT("Status") };
	const int32 Wanted[] = { LeftPage, RightPage };
	for (int32 Display = 0; Display < 2 && Display < PageSwitchers.Num(); ++Display)
	{
		const int32 Page = ((Wanted[Display] % PageCount) + PageCount) % PageCount;
		if (!PageSwitchers[Display] || PageSwitchers[Display]->GetActiveWidgetIndex() == Page)
		{
			continue;
		}
		// Only the page shown is laid out and painted: a page costs nothing while another is up.
		PageSwitchers[Display]->SetActiveWidgetIndex(Page);
		const FText Title = FText::FromString(PageTitles(Display)[Page]);
		for (const TCHAR* Part : { TEXT("Title"), TEXT("Page") })
		{
			if (UTextBlock* Text = Texts.FindRef(FName(*FString::Printf(TEXT("%s%s"), Screens[Display], Part))))
			{
				Text->SetText(Title);
			}
		}
	}
}

int32 USpaceCockpitDisplays::DebugGetPage(int32 Display) const
{
	return PageSwitchers.IsValidIndex(Display) && PageSwitchers[Display] ? PageSwitchers[Display]->GetActiveWidgetIndex() : -1;
}
