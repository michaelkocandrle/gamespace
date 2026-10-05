// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceDoorPanel.h"

#include "Fonts/SlateFontInfo.h"
#include "Misc/Paths.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"

namespace SpaceDoorPanelLocal
{
	void Line(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geometry, const TArray<FVector2D>& Points, const FLinearColor& Color, float Thickness)
	{
		FSlateDrawElement::MakeLines(Out, Layer, Geometry.ToPaintGeometry(), Points, ESlateDrawEffect::None, Color, true, Thickness);
	}

	FSlateFontInfo Font(float Size)
	{
		static const FString Saira = FPaths::ProjectContentDir() / TEXT("UI/Fonts/Saira-Medium.ttf");
		return FPaths::FileExists(Saira) ? FSlateFontInfo(Saira, Size) : FCoreStyle::GetDefaultFontStyle("Bold", Size);
	}
}

int32 USpaceDoorPanel::NativePaint(const FPaintArgs& Args, const FGeometry& Geometry, const FSlateRect& Culling,
	FSlateWindowElementList& Out, int32 Layer, const FWidgetStyle& Style, bool bParentEnabled) const
{
	using namespace SpaceDoorPanelLocal;
	const FVector2D Size = Geometry.GetLocalSize();
	const float W = float(Size.X), H = float(Size.Y);
	// amber shut, azure open (the travel blends them), brighter under the cursor
	const FLinearColor Amber(1.f, 0.55f, 0.08f, 1.f), Azure(0.2f, 0.75f, 1.f, 1.f);
	FLinearColor Ink = FMath::Lerp(Amber, Azure, FMath::Clamp(Open, 0.f, 1.f));
	const float Glow = 1.f;
	auto Faded = [&](float A) { return FLinearColor(Ink.R, Ink.G, Ink.B, A * Glow); };
	const FSlateBrush* White = FCoreStyle::Get().GetBrush("WhiteBrush");

	// a faint smoked field, the frame of light with heavier corner marks, the emitter's line at the foot
	FSlateDrawElement::MakeBox(Out, Layer, Geometry.ToPaintGeometry(FVector2f(W - 16.f, H - 30.f), FSlateLayoutTransform(FVector2f(8.f, 8.f))),
		White, ESlateDrawEffect::None, FLinearColor(0.f, 0.04f, 0.07f, 0.55f));
	Line(Out, Layer + 1, Geometry, { {8, 8}, {W - 8, 8}, {W - 8, H - 22}, {8, H - 22}, {8, 8} }, Faded(0.7f), 2.5f);
	const float Arm = 22.f;
	for (const FVector2D& C : { FVector2D(8, 8), FVector2D(W - 8, 8), FVector2D(W - 8, H - 22), FVector2D(8, H - 22) })
	{
		const float Sx = C.X < W / 2 ? 1.f : -1.f, Sy = C.Y < H / 2 ? 1.f : -1.f;
		Line(Out, Layer + 2, Geometry, { {C.X + Sx * Arm, C.Y}, C, {C.X, C.Y + Sy * Arm} }, Faded(1.f), 5.f);
	}
	Line(Out, Layer + 2, Geometry, { {W * 0.1, H - 6}, {W * 0.9, H - 6} }, FLinearColor(0.75f, 0.95f, 1.f, 0.9f * Glow), 4.f);
	Line(Out, Layer + 1, Geometry, { {W * 0.05, H - 6}, {W * 0.95, H - 6} }, Faded(0.35f), 10.f);

	// the door's number, a rule
	FSlateDrawElement::MakeText(Out, Layer + 2, Geometry.ToPaintGeometry(FVector2f(W, 40.f), FSlateLayoutTransform(FVector2f(22.f, 20.f))),
		FString::Printf(TEXT("DOOR %02d"), DoorNumber + 1), Font(26.f), ESlateDrawEffect::None, Faded(1.f));
	Line(Out, Layer + 1, Geometry, { {22, 56}, {W - 22, 56} }, Faded(0.4f), 1.5f);

	// the glyph: a touch ring with a lock (shut) or two arrows parting (open)
	const FVector2D C(W / 2, H * 0.47);
	const float R = W * 0.22f;
	TArray<FVector2D> Ring;
	for (int32 K = 0; K <= 40; ++K)
	{
		const float A = 2.f * PI * K / 40;
		Ring.Add(C + FVector2D(FMath::Cos(A), FMath::Sin(A)) * R);
	}
	Line(Out, Layer + 1, Geometry, Ring, Faded(0.3f), 9.f);
	Line(Out, Layer + 2, Geometry, Ring, Faded(1.f), 4.f);
	if (Open < 0.5f && !bOpening)
	{
		// the lock: a body and a shackle
		const float B = R * 0.42f;
		Line(Out, Layer + 2, Geometry, { C + FVector2D(-B, -B * 0.1), C + FVector2D(B, -B * 0.1), C + FVector2D(B, B * 1.05), C + FVector2D(-B, B * 1.05), C + FVector2D(-B, -B * 0.1) }, Faded(1.f), 3.f);
		TArray<FVector2D> Shackle;
		for (int32 K = 0; K <= 12; ++K)
		{
			const float A = PI + PI * K / 12;
			Shackle.Add(C + FVector2D(FMath::Cos(A) * B * 0.62f, -B * 0.1f + FMath::Sin(A) * B * 0.75f));
		}
		Line(Out, Layer + 2, Geometry, Shackle, Faded(1.f), 3.f);
	}
	else
	{
		// two chevrons parting
		const float B = R * 0.32f;
		for (const float S : { -1.f, 1.f })
		{
			const FVector2D Tip = C + FVector2D(S * B * 1.5f, 0.f);
			Line(Out, Layer + 2, Geometry, { Tip + FVector2D(-S * B, -B), Tip, Tip + FVector2D(-S * B, B) }, Faded(1.f), 3.5f);
		}
	}

	// the state
	const FString State = bOpening ? (Open < 0.98f ? TEXT("OPENING") : TEXT("OPEN")) : (Open > 0.02f ? TEXT("CLOSING") : TEXT("CLOSED"));   // (LOCKED + TAP TO OPEN contradicted itself)
	const FSlateFontInfo StateFont = Font(32.f);
	FSlateDrawElement::MakeText(Out, Layer + 2, Geometry.ToPaintGeometry(FVector2f(W, 40.f), FSlateLayoutTransform(FVector2f(22.f, H * 0.66f))),
		State, StateFont, ESlateDrawEffect::None, Faded(1.f));
	FSlateDrawElement::MakeText(Out, Layer + 2, Geometry.ToPaintGeometry(FVector2f(W, 30.f), FSlateLayoutTransform(FVector2f(22.f, H * 0.66f + 44.f))),
		bOpening ? TEXT("TAP TO CLOSE") : TEXT("TAP TO OPEN"), Font(16.f), ESlateDrawEffect::None, Faded(0.8f));
	return Layer + 3;
}
