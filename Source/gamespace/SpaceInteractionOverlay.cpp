// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceInteractionOverlay.h"

#include "Fonts/FontMeasure.h"
#include "Framework/Application/SlateApplication.h"
#include "HAL/PlatformTime.h"
#include "Misc/Paths.h"
#include "Rendering/DrawElements.h"
#include "Rendering/SlateRenderer.h"
#include "SpaceNotifications.h"
#include "SpacePlayerController.h"
#include "SpaceUserSettings.h"
#include "Styling/CoreStyle.h"

namespace SpaceOverlayStyle
{
	FLinearColor Srgb(uint8 R, uint8 G, uint8 B, float A = 1.f)
	{
		FLinearColor Color = FLinearColor::FromSRGBColor(FColor(R, G, B));
		Color.A = A;
		return Color;
	}

	// SC's visor colours, one cyan family: pale cyan text, bright cyan key caps and frames with a glow, translucent
	// teal glass fills; yellow only for a toast's diamond.
	const FLinearColor Text = Srgb(230, 244, 250);
	const FLinearColor TextCyan = Srgb(168, 220, 245);
	const FLinearColor TextDim = Srgb(120, 150, 160);
	const FLinearColor Cyan = Srgb(95, 214, 245);
	const FLinearColor CyanDim = Srgb(95, 214, 245, 0.45f);
	const FLinearColor Title = Srgb(127, 227, 255);
	const FLinearColor Yellow = Srgb(242, 194, 48);
	const FLinearColor Glass = Srgb(20, 45, 55, 0.62f);
	const FLinearColor CardGlass = Srgb(26, 80, 96, 0.74f);
	const FLinearColor CapFill = Srgb(10, 30, 40, 0.55f);

	FSlateFontInfo Font(bool bMedium, float Size)
	{
		const FString Path = FPaths::ProjectContentDir() / TEXT("UI/Fonts") / (bMedium ? TEXT("Oxanium-Medium.ttf") : TEXT("Oxanium-Regular.ttf"));
		return FPaths::FileExists(Path) ? FSlateFontInfo(Path, Size) : FCoreStyle::GetDefaultFontStyle(bMedium ? TEXT("Bold") : TEXT("Regular"), Size);
	}

	FVector2f Measure(const FString& Value, const FSlateFontInfo& Info)
	{
		return FSlateApplication::IsInitialized()
			? FVector2f(FSlateApplication::Get().GetRenderer()->GetFontMeasureService()->Measure(Value, Info)) : FVector2f(Value.Len() * Info.Size * 0.6f, Info.Size);
	}

	/** Words into lines no wider than Width. */
	TArray<FString> Wrap(const FString& Value, const FSlateFontInfo& Info, float Width)
	{
		TArray<FString> Words, Lines;
		Value.ParseIntoArray(Words, TEXT(" "));
		FString Line;
		for (const FString& Word : Words)
		{
			const FString Candidate = Line.IsEmpty() ? Word : Line + TEXT(" ") + Word;
			if (!Line.IsEmpty() && Measure(Candidate, Info).X > Width)
			{
				Lines.Add(Line);
				Line = Word;
			}
			else
			{
				Line = Candidate;
			}
		}
		if (!Line.IsEmpty())
		{
			Lines.Add(Line);
		}
		return Lines;
	}

	/** A filled convex polygon (white brush, tinted). */
	void Fill(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geometry, const TArray<FVector2f>& Points, const FLinearColor& Color)
	{
		if (Points.Num() < 3 || !FSlateApplication::IsInitialized())
		{
			return;
		}
		const FSlateResourceHandle Handle = FSlateApplication::Get().GetRenderer()->GetResourceHandle(*FCoreStyle::Get().GetBrush("WhiteBrush"));
		const FSlateRenderTransform& Transform = Geometry.GetAccumulatedRenderTransform();
		const FColor Vertex = Color.ToFColor(true);
		TArray<FSlateVertex> Verts;
		TArray<SlateIndex> Indices;
		for (const FVector2f& Point : Points)
		{
			Verts.Add(FSlateVertex::Make(Transform, Point, FVector2f(0.5f, 0.5f), Vertex));
		}
		for (int32 Index = 1; Index + 1 < Points.Num(); ++Index)
		{
			Indices.Add(0);
			Indices.Add(SlateIndex(Index));
			Indices.Add(SlateIndex(Index + 1));
		}
		FSlateDrawElement::MakeCustomVerts(Out, Layer, Handle, Verts, Indices, nullptr, 0, 0);
	}

	TArray<FVector2f> BoxPoints(float X, float Y, float W, float H)
	{
		return { { X, Y }, { X + W, Y }, { X + W, Y + H }, { X, Y + H } };
	}

	/** A rounded box outline (convex, so it also fills as a fan); not closed. */
	TArray<FVector2f> RoundedBox(float X, float Y, float W, float H, float Radius)
	{
		Radius = FMath::Min(Radius, FMath::Min(W, H) * 0.5f);
		const FVector2f Corners[4] = { { X + W - Radius, Y + Radius }, { X + W - Radius, Y + H - Radius }, { X + Radius, Y + H - Radius }, { X + Radius, Y + Radius } };
		TArray<FVector2f> Points;
		for (int32 Corner = 0; Corner < 4; ++Corner)
		{
			for (int32 Step = 0; Step <= 6; ++Step)
			{
				const float A = (-0.5f + Corner * 0.5f + Step / 12.f) * PI;
				Points.Add(Corners[Corner] + FVector2f(FMath::Cos(A), FMath::Sin(A)) * Radius);
			}
		}
		return Points;
	}

	TArray<FVector2f> Closed(TArray<FVector2f> Points)
	{
		if (Points.Num() > 0)
		{
			const FVector2f First = Points[0];
			Points.Add(First);
		}
		return Points;
	}

	TArray<FVector2f> Ring(const FVector2f& Centre, float Radius, int32 Segments = 24)
	{
		TArray<FVector2f> Points;
		for (int32 I = 0; I <= Segments; ++I)
		{
			const float A = 2.f * PI * I / Segments;
			Points.Add(Centre + FVector2f(FMath::Cos(A), FMath::Sin(A)) * Radius);
		}
		return Points;
	}
}

void SSpaceInteractionOverlay::Construct(const FArguments& InArgs)
{
	Owner = InArgs._Owner;
	SetVisibility(EVisibility::HitTestInvisible);
}

int32 SSpaceInteractionOverlay::OnPaint(const FPaintArgs&, const FGeometry& Geometry, const FSlateRect&, FSlateWindowElementList& Out,
	int32 Layer, const FWidgetStyle& Style, bool) const
{
	using namespace SpaceOverlayStyle;
	ASpacePlayerController* Controller = Owner.Get();
	if (!Controller)
	{
		return Layer;
	}
	const FSpaceInteractionView& View = Controller->GetInteractionView();
	if (!View.bVisible)
	{
		return Layer;
	}
	const FVector2f Size = Geometry.GetLocalSize();
	// Viewport pixels to this widget's units (it fills the viewport; Slate scales it by the DPI).
	const float PixelScale = FMath::Max(Geometry.GetAccumulatedLayoutTransform().GetScale(), 0.01f);
	auto ToLocal = [PixelScale](const FVector2D& Screen) { return FVector2f(Screen) / PixelScale; };
	const FPaintGeometry Paint = Geometry.ToPaintGeometry();
	auto Lines = [&](const TArray<FVector2f>& Points, const FLinearColor& Color, float Thickness, int32 AtLayer)
	{
		FSlateDrawElement::MakeLines(Out, AtLayer, Paint, Points, ESlateDrawEffect::None, Color * Style.GetColorAndOpacityTint(), true, Thickness);
	};
	auto Write = [&](const FString& Value, const FVector2f& At, const FSlateFontInfo& Info, const FLinearColor& Color, int32 AtLayer, bool bShadow = true)
	{
		if (bShadow)
		{
			FSlateDrawElement::MakeText(Out, AtLayer, Geometry.ToPaintGeometry(FVector2f(2000.f, 200.f), FSlateLayoutTransform(At + FVector2f(1.f, 1.f))),
				Value, Info, ESlateDrawEffect::None, FLinearColor(0.f, 0.f, 0.f, 0.7f * Color.A));
		}
		FSlateDrawElement::MakeText(Out, AtLayer + 1, Geometry.ToPaintGeometry(FVector2f(2000.f, 200.f), FSlateLayoutTransform(At)),
			Value, Info, ESlateDrawEffect::None, Color * Style.GetColorAndOpacityTint());
	};
	// SC's interact labels lean: the type sheared like an italic (the font has no italic face).
	auto WriteItalic = [&](const FString& Value, const FVector2f& At, const FSlateFontInfo& Info, const FLinearColor& Color, int32 AtLayer)
	{
		const FSlateRenderTransform Local = Concatenate(FShear2D(-0.22f, 0.f), FSlateRenderTransform(At));
		const FSlateRenderTransform Full = Concatenate(Local, Geometry.GetAccumulatedRenderTransform());
		const FSlateLayoutTransform LayoutAt = Concatenate(FSlateLayoutTransform(At), Geometry.GetAccumulatedLayoutTransform());
		FSlateDrawElement::MakeText(Out, AtLayer, FPaintGeometry(LayoutAt, Full, FVector2f(2000.f, 200.f), true), Value, Info,
			ESlateDrawEffect::None, Color * Style.GetColorAndOpacityTint());
	};
	// SC's glow: wider, fainter copies of a line under it.
	auto Glow = [&](const TArray<FVector2f>& Points, const FLinearColor& Color, float Thickness, int32 AtLayer, float Strength = 1.f)
	{
		Lines(Points, Color * FLinearColor(1, 1, 1, 0.12f * Strength), Thickness + 9.f, AtLayer);
		Lines(Points, Color * FLinearColor(1, 1, 1, 0.30f * Strength), Thickness + 4.f, AtLayer);
		Lines(Points, Color, Thickness, AtLayer + 1);
	};
	// SC's key cap: a glowing cyan outlined box with the key in it. Returns its width.
	auto KeyCap = [&](const FString& Key, const FVector2f& TopLeft, float H, float FontSize, int32 AtLayer) -> float
	{
		const FSlateFontInfo Info = Font(true, FontSize);
		const FVector2f TextSize = Measure(Key, Info);
		const float W = FMath::Max(H, TextSize.X + H * 0.55f);
		Fill(Out, AtLayer, Geometry, BoxPoints(TopLeft.X, TopLeft.Y, W, H), CapFill);
		Glow(Closed(BoxPoints(TopLeft.X, TopLeft.Y, W, H)), Cyan, 1.6f, AtLayer + 1);
		Write(Key, { TopLeft.X + (W - TextSize.X) * 0.5f, TopLeft.Y + (H - TextSize.Y) * 0.5f }, Info, Text, AtLayer + 2, false);
		return W;
	};

	// --- The prompt by the object (not in interact mode, where the hotspots speak) ------------------------------------
	if (!View.bInteractMode && View.Target.bValid && View.bTargetOnScreen && View.Target.bVertical)
	{
		// SC's door prompt: the key cap on the door's edge and the word set vertically above it, reading bottom-up
		const FVector2f At = ToLocal(View.TargetScreen);
		const FString Label = View.Target.Label.ToString();
		const FSlateFontInfo Info = Font(true, 17.f);
		const FVector2f TextSize = Measure(Label, Info);
		const float Cap = 36.f;
		KeyCap(TEXT("F"), { At.X - Cap * 0.5f, At.Y - Cap * 0.5f }, Cap, 19.f, Layer);
		const FVector2f Base(At.X - TextSize.Y * 0.5f, At.Y - Cap * 0.5f - 14.f);
		const FSlateRenderTransform Local = Concatenate(FQuat2D(-UE_HALF_PI), FSlateRenderTransform(Base));
		const FSlateRenderTransform Full = Concatenate(Local, Geometry.GetAccumulatedRenderTransform());
		const FSlateLayoutTransform LayoutAt = Concatenate(FSlateLayoutTransform(Base), Geometry.GetAccumulatedLayoutTransform());
		FSlateDrawElement::MakeText(Out, Layer + 3, FPaintGeometry(LayoutAt, Full, FVector2f(2000.f, 200.f), true), Label, Info,
			ESlateDrawEffect::None, Text * Style.GetColorAndOpacityTint());
		// a thin cyan rule along the word, like SC's door strip
		Glow({ { Base.X + TextSize.Y + 6.f, Base.Y }, { Base.X + TextSize.Y + 6.f, Base.Y - TextSize.X } }, Cyan, 1.2f, Layer + 2, 0.7f);
	}
	else if (!View.bInteractMode && View.Target.bValid && View.bTargetOnScreen)
	{
		const FVector2f At = ToLocal(View.TargetScreen);
		const FString Label = View.Target.Label.ToString();
		const FSlateFontInfo Info = Font(true, 14.f);
		const FVector2f TextSize = Measure(Label, Info);
		const float Cap = 36.f;
		// The key cap is anchored on the object; the label and SC's three dots stand above it.
		const float CapTop = At.Y - Cap * 0.5f;
		Write(Label, { At.X - TextSize.X * 0.5f, CapTop - 22.f - TextSize.Y }, Info, View.Target.bAvailable ? Text : TextDim, Layer);
		for (int32 Dot = -1; Dot <= 1; ++Dot)
		{
			Fill(Out, Layer + 1, Geometry, Ring(FVector2f(At.X + Dot * 6.f, CapTop - 12.f), 1.6f, 8), View.Target.bAvailable ? Cyan : TextDim);
		}
		if (View.Target.bAvailable)
		{
			KeyCap(TEXT("F"), { At.X - Cap * 0.5f, CapTop }, Cap, 19.f, Layer);
		}
	}

	// --- Interact mode: the hotspots, the hovered one labelled -----------------------------------------------------------
	if (View.bInteractMode)
	{
		// The interact cursor (author 5. 10. 2026: the boxy hand looked cheap, then "smaller, and over a control fit
		// it to the control"): four short thin ticks round the point the player looks at, no dot; over a control the
		// cursor becomes the control's own frame (the corners below), so the ticks are not drawn.
		if (!View.Hotspots.IsValidIndex(View.Hovered))
		{
			const FVector2f C = ToLocal(View.CursorScreen);
			for (const FVector2f& Dir : { FVector2f(1.f, 0.f), FVector2f(-1.f, 0.f), FVector2f(0.f, 1.f), FVector2f(0.f, -1.f) })
			{
				const TArray<FVector2f> Line = { C + Dir * 3.5f, C + Dir * 7.f };
				Lines(Line, Srgb(5, 12, 16, 0.5f), 2.6f, Layer + 4);
				Lines(Line, Srgb(235, 245, 250, 0.85f), 1.1f, Layer + 5);
			}
		}
		for (int32 Index = 0; Index < View.Hotspots.Num(); ++Index)
		{
			if (!View.HotspotOnScreen.IsValidIndex(Index) || !View.HotspotOnScreen[Index])
			{
				continue;
			}
			const FVector2f At = ToLocal(View.HotspotScreen[Index]);
			const bool bHovered = Index == View.Hovered;
			if (bHovered)
			{
				// SC (the author's captures, 5. 10. 2026): the control under the cursor lights up - here light corners
				// round it at its own size, not a marker dot - and its name stands beside it in light italic caps.
				const float Px = View.HotspotPixelSize.IsValidIndex(Index) ? FMath::Clamp(View.HotspotPixelSize[Index] / PixelScale, 10.f, 260.f) : 30.f;
				// the frame takes the control's shape (SizeCm is its width, Aspect width / height), 3 px clear of it
				const float Aspect = FMath::Clamp(View.Hotspots[Index].Aspect, 0.25f, 4.f);
				const FVector2f Half(Px * 0.5f + 3.f, Px * 0.5f / Aspect + 3.f);
				const float Arm = FMath::Max(4.f, FMath::Min(Half.X, Half.Y) * 0.5f);
				Fill(Out, Layer, Geometry, BoxPoints(At.X - Half.X, At.Y - Half.Y, Half.X * 2.f, Half.Y * 2.f), Srgb(200, 240, 255, 0.07f));
				for (const FVector2f& Sign : { FVector2f(-1.f, -1.f), FVector2f(1.f, -1.f), FVector2f(1.f, 1.f), FVector2f(-1.f, 1.f) })
				{
					const FVector2f Corner = At + Sign * Half;
					Glow({ Corner - FVector2f(Sign.X * Arm, 0.f), Corner, Corner - FVector2f(0.f, Sign.Y * Arm) }, Srgb(210, 245, 255), 1.4f, Layer + 1, 0.9f);
				}
				// no name beside it (author 5. 10. 2026: the labels made no sense there)
			}
			// (the others: nothing - SC marks only the control under the cursor)
		}
	}

	// --- The context key list, bottom right ------------------------------------------------------------------------------
	if (View.Keys.Num() > 0 && View.bHudShown)
	{
		const FSlateFontInfo Info = Font(true, 13.f);
		const float Right = Size.X - 52.f, LineH = 34.f, Cap = 27.f, CapFont = 12.f;
		const float Bottom = Size.Y * 0.86f;
		float Y = Bottom - View.Keys.Num() * LineH;
		for (const FSpaceKeyHint& Hint : View.Keys)
		{
			const float CapW = FMath::Max(Cap, Measure(Hint.Key, Font(true, CapFont)).X + Cap * 0.55f);
			KeyCap(Hint.Key, { Right - CapW, Y }, Cap, CapFont, Layer);
			const FString Label = Hint.Action.ToString();
			const FVector2f TextSize = Measure(Label, Info);
			Write(Label, { Right - CapW - 12.f - TextSize.X, Y + (Cap - TextSize.Y) * 0.5f }, Info, TextCyan, Layer);
			Y += LineH;
		}
	}

	// --- Toasts (top centre) and hint cards (right edge) -----------------------------------------------------------------
	if (USpaceNotifications* Notes = USpaceNotifications::Get(Controller))
	{
		const double Now = FPlatformTime::Seconds();
		auto Fade = [Now](const USpaceNotifications::FEntry& Entry)
		{
			const float Age = float(Now - Entry.StartSeconds);
			return FMath::Clamp(FMath::Min(Age / 0.3f, (Entry.Seconds - Age) / 0.6f), 0.f, 1.f);
		};
		float Y = 64.f;
		for (const USpaceNotifications::FEntry& Toast : Notes->GetToasts())
		{
			const float Alpha = Fade(Toast);
			const FString Label = Toast.Title.ToString();
			const FSlateFontInfo Info = Font(true, 20.f);
			const FVector2f TextSize = Measure(Label, Info);
			const float W = TextSize.X + 24.f + 14.f + 12.f + 24.f, H = 64.f, X = (Size.X - W) * 0.5f;
			const TArray<FVector2f> Pill = RoundedBox(X, Y, W, H, 17.f);
			Fill(Out, Layer, Geometry, Pill, Glass * FLinearColor(1, 1, 1, Alpha));
			Glow(Closed(Pill), Srgb(120, 210, 235, 0.6f * Alpha), 1.5f, Layer + 1, 0.6f * Alpha);
			const FVector2f D(X + 24.f + 7.f, Y + H * 0.5f);
			Lines({ D + FVector2f(-7.f, 0.f), D + FVector2f(0.f, -7.f), D + FVector2f(7.f, 0.f), D + FVector2f(0.f, 7.f), D + FVector2f(-7.f, 0.f) },
				Yellow * FLinearColor(1, 1, 1, Alpha), 2.f, Layer + 1);
			Write(Label, { X + 24.f + 14.f + 12.f, Y + (H - TextSize.Y) * 0.5f }, Info, Text * FLinearColor(1, 1, 1, Alpha), Layer + 1, false);
			Y += H + 8.f;
		}

		float CardY = Size.Y * 0.36f;
		for (const USpaceNotifications::FEntry& Card : Notes->GetHints())
		{
			const float Alpha = Fade(Card);
			const float W = 340.f, Pad = 16.f;
			const FSlateFontInfo TitleInfo = Font(true, 16.f);
			const FSlateFontInfo BodyInfo = Font(true, 13.5f);
			const TArray<FString> Body = Wrap(Card.Body.ToString(), BodyInfo, W - Pad * 2.f);
			const float H = Pad + 26.f + Body.Num() * 21.f + Pad;
			const float X = Size.X - W - 40.f;
			Fill(Out, Layer, Geometry, BoxPoints(X, CardY, W, H), CardGlass * FLinearColor(1, 1, 1, Alpha));
			Lines(Closed(BoxPoints(X, CardY, W, H)), Srgb(120, 210, 235, 0.35f * Alpha), 1.f, Layer + 1);
			Write(Card.Title.ToString().ToUpper(), { X + Pad, CardY + Pad - 2.f }, TitleInfo, Title * FLinearColor(1, 1, 1, Alpha), Layer + 1, false);
			for (int32 Line = 0; Line < Body.Num(); ++Line)
			{
				Write(Body[Line], { X + Pad, CardY + Pad + 26.f + Line * 21.f }, BodyInfo, Text * FLinearColor(1, 1, 1, Alpha), Layer + 1, false);
			}
			CardY += H + 12.f;
		}
	}
	return Layer + 4;
}
