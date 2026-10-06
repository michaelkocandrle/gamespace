// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceEngineering.h"

#include "Components/StaticMeshComponent.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"
#include "Components/WidgetComponent.h"
#include "Fonts/FontMeasure.h"
#include "Fonts/SlateFontInfo.h"
#include "Framework/Application/SlateApplication.h"
#include "Misc/App.h"
#include "Misc/Paths.h"
#include "Rendering/DrawElements.h"
#include "SpaceInteraction.h"
#include "Styling/CoreStyle.h"

#define LOCTEXT_NAMESPACE "SpaceEngineering"

// =====================================================================================================================
// The look (measured on the author's captures, 7. 10. 2026): a dark teal glass, ice-cyan ink, light cells for the
// status labels, filled cyan pips and icon keys, an amber edit frame, red only for a fault.
// =====================================================================================================================
namespace SpaceEngLocal
{
	// sRGB sampled from the author's capture (7. 10. 2026; Slate colours are linear: the first palette, written as sRGB
	// numbers, came out pale grey instead of cyan and the glass too light)
	float Lin(uint8 V) { const float C = V / 255.f; return C <= 0.04045f ? C / 12.92f : FMath::Pow((C + 0.055f) / 1.055f, 2.4f); }
	FLinearColor SRGB(uint8 R, uint8 G, uint8 B, float A = 1.f) { return FLinearColor(Lin(R), Lin(G), Lin(B), A); }
	const FLinearColor Glass = SRGB(13, 21, 22);
	const FLinearColor PanelFill = SRGB(18, 26, 26);
	const FLinearColor CardFill = SRGB(38, 56, 59);
	const FLinearColor Cell = SRGB(43, 67, 69);
	const FLinearColor Ink = SRGB(98, 222, 230);        // over-saturated: the filmic tonemapper bleaches bright cyan
	const FLinearColor InkDim = SRGB(70, 128, 132);
	const FLinearColor InkFaint = SRGB(32, 52, 54);
	const FLinearColor PipOff = SRGB(46, 76, 79);
	const FLinearColor PipEdge = SRGB(78, 118, 121);
	const FLinearColor White = SRGB(226, 240, 240);
	const FLinearColor Amber = SRGB(226, 170, 62);
	const FLinearColor Red = SRGB(214, 40, 72);
	const FLinearColor Dark = SRGB(10, 24, 27);
	const FLinearColor KeyFill = SRGB(78, 198, 208);

	FSlateFontInfo Font(float Size, bool bBold = false)
	{
		static const FString Saira = FPaths::ProjectContentDir() / TEXT("UI/Fonts/Saira-Medium.ttf");
		static const FString SairaBold = FPaths::ProjectContentDir() / TEXT("UI/Fonts/Saira-SemiBold.ttf");
		const FString& Path = bBold ? SairaBold : Saira;
		return FPaths::FileExists(Path) ? FSlateFontInfo(Path, Size) : FCoreStyle::GetDefaultFontStyle("Regular", Size);
	}

	/** Slate font sizes are points (96 dpi): the reference's sizes, measured in its pixels, scaled to them. */
	constexpr float TextScale = 0.86f;   // 0.74 fitted the cells but read small from the eye

	/** Drawing in the reference's coordinates (USpaceEngineeringScreen::Ref): boxes, lines, text, brackets. */
	struct FPen
	{
		FSlateWindowElementList& Out;
		const FGeometry& Geo;
		int32 Layer;
		const FSlateBrush* WhiteBrush = FCoreStyle::Get().GetBrush("WhiteBrush");

		static FVector2D P(double X, double Y) { return USpaceEngineeringScreen::Ref(X, Y); }
		static float S(double V) { return float(V * USpaceEngineeringScreen::RefScale); }

		void Fill(double X0, double Y0, double X1, double Y1, const FLinearColor& C, int32 L = 0) const
		{
			const FVector2D A = P(X0, Y0), B = P(X1, Y1);
			FSlateDrawElement::MakeBox(Out, Layer + L, Geo.ToPaintGeometry(FVector2f(B - A), FSlateLayoutTransform(FVector2f(A))), WhiteBrush,
				ESlateDrawEffect::None, C);
		}
		void FillC(const FVector2D& A, const FVector2D& B, const FLinearColor& C, int32 L = 0) const
		{
			FSlateDrawElement::MakeBox(Out, Layer + L, Geo.ToPaintGeometry(FVector2f(B - A), FSlateLayoutTransform(FVector2f(A))), WhiteBrush,
				ESlateDrawEffect::None, C);
		}
		void Lines(const TArray<FVector2D>& RefPts, const FLinearColor& C, float T = 1.5f, int32 L = 1) const
		{
			TArray<FVector2D> Pts;
			for (const FVector2D& Q : RefPts)
			{
				Pts.Add(P(Q.X, Q.Y));
			}
			FSlateDrawElement::MakeLines(Out, Layer + L, Geo.ToPaintGeometry(), Pts, ESlateDrawEffect::None, C, true, T);
		}
		void LinesC(const TArray<FVector2D>& Pts, const FLinearColor& C, float T = 1.5f, int32 L = 1) const
		{
			FSlateDrawElement::MakeLines(Out, Layer + L, Geo.ToPaintGeometry(), Pts, ESlateDrawEffect::None, C, true, T);
		}
		void Rect(double X0, double Y0, double X1, double Y1, const FLinearColor& C, float T = 1.5f, int32 L = 1) const
		{
			Lines({ {X0, Y0}, {X1, Y0}, {X1, Y1}, {X0, Y1}, {X0, Y0} }, C, T, L);
		}
		/** SC's bracket frame: the corners drawn heavier, the sides thin. */
		void Bracket(double X0, double Y0, double X1, double Y1, const FLinearColor& C, double Arm = 14.0, bool bSides = true) const
		{
			if (bSides)
			{
				Rect(X0, Y0, X1, Y1, C * FLinearColor(1, 1, 1, 0.35f), 1.2f);
			}
			Lines({ {X0, Y0 + Arm}, {X0, Y0}, {X0 + Arm, Y0} }, C, 2.2f, 2);
			Lines({ {X1 - Arm, Y0}, {X1, Y0}, {X1, Y0 + Arm} }, C, 2.2f, 2);
			Lines({ {X1, Y1 - Arm}, {X1, Y1}, {X1 - Arm, Y1} }, C, 2.2f, 2);
			Lines({ {X0 + Arm, Y1}, {X0, Y1}, {X0, Y1 - Arm} }, C, 2.2f, 2);
		}
		/** A frame with 45 deg corners (the main panel, the power card). */
		void Chamfer(double X0, double Y0, double X1, double Y1, double Cut, const FLinearColor& C, float T, bool bFill = false,
			const FLinearColor& FillC = FLinearColor::Transparent) const
		{
			if (bFill)
			{
				Fill(X0 + Cut, Y0, X1 - Cut, Y1, FillC);
				Fill(X0, Y0 + Cut, X0 + Cut, Y1 - Cut, FillC);
				Fill(X1 - Cut, Y0 + Cut, X1, Y1 - Cut, FillC);
			}
			Lines({ {X0 + Cut, Y0}, {X1 - Cut, Y0}, {X1, Y0 + Cut}, {X1, Y1 - Cut}, {X1 - Cut, Y1}, {X0 + Cut, Y1}, {X0, Y1 - Cut}, {X0, Y0 + Cut},
				{X0 + Cut, Y0} }, C, T, 2);
		}
		FVector2D Measure(const FString& Text, const FSlateFontInfo& F) const
		{
			if (!FSlateApplication::IsInitialized())
			{
				return FVector2D(Text.Len() * F.Size * 0.55, F.Size * 1.2);
			}
			return FSlateApplication::Get().GetRenderer()->GetFontMeasureService()->Measure(Text, F);
		}
		/** Text at a reference point; Align -1 left, 0 centre, 1 right; the point is the text's vertical middle. */
		void Text(double X, double Y, const FString& Str, double RefSize, const FLinearColor& C, int32 Align = -1, bool bBold = false, int32 L = 3) const
		{
			const FSlateFontInfo F = Font(S(RefSize) * TextScale, bBold);
			const FVector2D Size = Measure(Str, F);
			FVector2D At = P(X, Y) - FVector2D(0.0, Size.Y * 0.5);
			At.X -= Align == 0 ? Size.X * 0.5 : Align > 0 ? Size.X : 0.0;
			FSlateDrawElement::MakeText(Out, Layer + L, Geo.ToPaintGeometry(FVector2f(Size), FSlateLayoutTransform(FVector2f(At))), Str, F,
				ESlateDrawEffect::None, C);
		}
		/** Vertical text (the side tabs), read bottom to top. */
		void TextUp(double X, double Y, const FString& Str, double RefSize, const FLinearColor& C) const
		{
			const FSlateFontInfo F = Font(S(RefSize) * TextScale);
			const FVector2D Size = Measure(Str, F);
			const FVector2D Centre = P(X, Y);
			const FSlateRenderTransform Rotate(FQuat2D(FMath::DegreesToRadians(-90.f)));
			FSlateDrawElement::MakeText(Out, Layer + 3,
				Geo.ToPaintGeometry(FVector2f(Size), FSlateLayoutTransform(FVector2f(Centre - Size * 0.5)), Rotate, FVector2f(0.5f, 0.5f)), Str, F,
				ESlateDrawEffect::None, C);
		}
		void Circle(double X, double Y, double R, const FLinearColor& C, float T = 1.5f, int32 Seg = 28, double A0 = 0.0, double A1 = 360.0) const
		{
			TArray<FVector2D> Pts;
			for (int32 K = 0; K <= Seg; ++K)
			{
				const double A = FMath::DegreesToRadians(A0 + (A1 - A0) * K / Seg);
				Pts.Add({ X + FMath::Cos(A) * R, Y + FMath::Sin(A) * R });
			}
			Lines(Pts, C, T, 3);
		}
	};

	/** The glyphs of the icon keys (drawn dark on the cyan key, reference size ~64 x 40, centre X, Y). */
	void Glyph(const FPen& Pen, int32 Icon, double X, double Y, const FLinearColor& C)
	{
		switch (Icon)
		{
		case 0:     // weapons: three rounds
			for (const double Dx : { -9.0, 0.0, 9.0 })
			{
				Pen.Lines({ {X + Dx, Y + 11}, {X + Dx, Y - 5} }, C, 4.f, 3);
				Pen.Circle(X + Dx, Y - 6, 2.2, C, 3.f, 8);
			}
			break;
		case 1:     // thrusters: three chevrons
			for (const double Dx : { -12.0, -2.0, 8.0 })
			{
				Pen.Lines({ {X + Dx - 4, Y - 8}, {X + Dx + 4, Y}, {X + Dx - 4, Y + 8} }, C, 2.6f, 3);
			}
			break;
		case 2:     // shields
			Pen.Lines({ {X - 11, Y - 10}, {X, Y - 13}, {X + 11, Y - 10}, {X + 10, Y + 2}, {X, Y + 12}, {X - 10, Y + 2}, {X - 11, Y - 10} }, C, 2.2f, 3);
			Pen.Lines({ {X - 5, Y - 6}, {X, Y - 8}, {X + 5, Y - 6}, {X + 4, Y + 1}, {X, Y + 6}, {X - 4, Y + 1}, {X - 5, Y - 6} }, C, 1.6f, 3);
			break;
		case 3:     // quantum: an atom
			for (int32 K = 0; K < 3; ++K)
			{
				TArray<FVector2D> E;
				const double R = FMath::DegreesToRadians(60.0 * K);
				for (int32 S = 0; S <= 24; ++S)
				{
					const double A = 2.0 * PI * S / 24;
					const double Ex = FMath::Cos(A) * 13.0, Ey = FMath::Sin(A) * 5.0;
					E.Add({ X + Ex * FMath::Cos(R) - Ey * FMath::Sin(R), Y + Ex * FMath::Sin(R) + Ey * FMath::Cos(R) });
				}
				Pen.Lines(E, C, 1.8f, 3);
			}
			Pen.Circle(X, Y, 2.2, C, 3.f, 8);
			break;
		case 4:     // life support: a heart with a pulse through it
			Pen.Lines({ {X, Y + 11}, {X - 12, Y - 1}, {X - 12, Y - 7}, {X - 7, Y - 11}, {X - 2, Y - 9}, {X, Y - 6}, {X + 2, Y - 9}, {X + 7, Y - 11},
				{X + 12, Y - 7}, {X + 12, Y - 1}, {X, Y + 11} }, C, 2.4f, 3);
			Pen.Lines({ {X - 10, Y}, {X - 4, Y}, {X - 2, Y - 5}, {X + 1, Y + 5}, {X + 3, Y}, {X + 10, Y} }, CardFill, 1.8f, 4);
			break;
		case 5:     // radar: a dot and three arcs
			Pen.Circle(X - 9, Y + 8, 2.4, C, 3.f, 8);
			for (const double R : { 8.0, 14.0, 20.0 })
			{
				Pen.Circle(X - 9, Y + 8, R, C, 2.2f, 10, -90.0, 0.0);
			}
			break;
		case 6:     // cooler: a fan in a ring
		{
			Pen.Circle(X, Y, 12.0, C, 2.f, 24);
			for (int32 K = 0; K < 4; ++K)
			{
				const double A = FMath::DegreesToRadians(90.0 * K + 20.0);
				Pen.Lines({ {X + FMath::Cos(A) * 2.0, Y + FMath::Sin(A) * 2.0}, {X + FMath::Cos(A + 0.6) * 9.0, Y + FMath::Sin(A + 0.6) * 9.0},
					{X + FMath::Cos(A + 1.2) * 6.0, Y + FMath::Sin(A + 1.2) * 6.0} }, C, 2.4f, 3);
			}
			break;
		}
		default:    // power: a bolt in a ring
			Pen.Circle(X, Y, 13.0, C, 2.f, 24);
			Pen.Lines({ {X + 3, Y - 10}, {X - 5, Y + 1}, {X + 1, Y + 1}, {X - 3, Y + 10}, {X + 5, Y - 2}, {X - 1, Y - 2}, {X + 3, Y - 10} }, C, 2.f, 3);
			break;
		}
	}

	/** The warning triangle of the header (hydrogen fuel empty). */
	void Warning(const FPen& Pen, double X, double Y, const FLinearColor& C)
	{
		for (double R = 0.0; R < 7.0; R += 1.0)
		{
			Pen.Lines({ {X - 8 + R, Y + 7 - R * 0.3}, {X, Y - 8 + R}, {X + 8 - R, Y + 7 - R * 0.3}, {X - 8 + R, Y + 7 - R * 0.3} }, C, 1.6f, 3);
		}
		Pen.Lines({ {X, Y - 3}, {X, Y + 2} }, Dark, 2.f, 4);
		Pen.Lines({ {X, Y + 4}, {X, Y + 5.5} }, Dark, 2.f, 4);
	}

	/** The reference's header cells: label, the segmented bar, the value. */
	struct FHeader
	{
		const TCHAR* Label;
		double X;
	};
	const FHeader Headers[] = { { TEXT("ARMOR"), 215.0 }, { TEXT("HULL"), 392.0 }, { TEXT("COOLING SYSTEM"), 569.0 },
		{ TEXT("LIFE SUPPORT"), 745.0 }, { TEXT("HYDROGEN FUEL"), 920.0 } };

	/** The tabs on the left edge: reference y ranges. */
	const double TabY[3][2] = { { 425.0, 555.0 }, { 568.0, 685.0 }, { 700.0, 820.0 } };
	const TCHAR* TabNames[3] = { TEXT("3D VIEW"), TEXT("CONFIG"), TEXT("PRESETS") };

	/** The edit buttons: reference x ranges at y 345-380. */
	const double ButtonX[3][2] = { { 1340.0, 1463.0 }, { 1475.0, 1597.0 }, { 1607.0, 1800.0 } };
	const TCHAR* ButtonNames[3] = { TEXT("CLEAR ALL"), TEXT("SAVE"), TEXT("SAVE AND APPLY") };

	/** The columns of the systems (reference x centres) - weapons, thrusters, shields, quantum | life support, radar |
	 * coolers. */
	const double Columns[] = { 829.0, 916.0, 1003.0, 1141.0, 1272.0, 1358.0, 1479.0, 1565.0 };
	constexpr double PipBottom = 708.0, PipPitch = 27.0, PipH = 22.0, PipHalfW = 20.0;
	constexpr double PowerX0 = 440.0, PowerX1 = 488.0, PowerBottom = 708.0, PowerPitch = 26.5;
}

using namespace SpaceEngLocal;

// =====================================================================================================================
// Screen
// =====================================================================================================================
int32 USpaceEngineeringScreen::NativePaint(const FPaintArgs& Args, const FGeometry& Geo, const FSlateRect& Culling,
	FSlateWindowElementList& Out, int32 Layer, const FWidgetStyle& Style, bool bParentEnabled) const
{
	const ASpaceEngineeringTerminal* T = Terminal.Get();
	const FPen Pen{ Out, Geo, Layer };
	// the glass: dark teal, fine scan lines, a soft brighter middle
	FSlateDrawElement::MakeBox(Out, Layer, Geo.ToPaintGeometry(), Pen.WhiteBrush, ESlateDrawEffect::None, Glass);
	for (float Y = 0.f; Y < CanvasH; Y += 4.f)
	{
		FSlateDrawElement::MakeBox(Out, Layer, Geo.ToPaintGeometry(FVector2f(CanvasW, 1.f), FSlateLayoutTransform(FVector2f(0.f, Y))),
			Pen.WhiteBrush, ESlateDrawEffect::None, SRGB(30, 48, 50, 0.18f));
	}
	for (int32 K = 0; K < 8; ++K)
	{
		FSlateDrawElement::MakeBox(Out, Layer, Geo.ToPaintGeometry(FVector2f(CanvasW, 12.f), FSlateLayoutTransform(FVector2f(0.f, K * 12.f))),
			Pen.WhiteBrush, ESlateDrawEffect::None, SRGB(40, 90, 95, 0.10f * (8 - K) / 8.f));
	}
	if (!T)
	{
		return Layer + 5;
	}

	// ---- the header: five status cells -------------------------------------------------------------------------------
	Pen.Bracket(205, 140, 1082, 265, Ink, 12.0, false);
	Pen.Lines({ {205, 152}, {205, 140}, {1082, 140}, {1082, 152} }, InkDim, 1.2f);
	Pen.Lines({ {218, 263}, {1070, 263} }, InkDim, 1.2f);
	for (int32 H = 0; H < 5; ++H)
	{
		const double X = Headers[H].X;
		const float Pct = T->Percent(H);
		Pen.Fill(X, 147, X + 160, 175, Cell);
		Pen.Lines({ {X, 147}, {X, 175} }, Ink, 2.f);
		Pen.Text(X + 10, 161, Headers[H].Label, 15.0, White);
		// the bar: thin vertical ticks, lit to the value, the rest dim, red beyond a low value
		const double B0 = X + 15, B1 = X + 150;
		const int32 Ticks = 46;
		for (int32 K = 0; K < Ticks; ++K)
		{
			const double Tx = B0 + (B1 - B0) * K / (Ticks - 1);
			const bool bLit = K < FMath::RoundToInt(Pct / 100.f * Ticks);
			const bool bRedZone = K >= Ticks * 0.75 && H >= 2;
			const FLinearColor C = bLit ? (Pct < 10.f ? Red : White) : (bRedZone ? Red * FLinearColor(0.6f, 0.6f, 0.6f, 0.7f) : InkFaint);
			Pen.Lines({ {Tx, 190}, {Tx, 208} }, C, 2.3f);
		}
		if (Pct <= 0.f)
		{
			Pen.Text(X + 15, 223, TEXT("EMPTY"), 17.0, Red);
		}
		else
		{
			Pen.Text(X + 22, 223, FString::Printf(TEXT("%d%%"), FMath::RoundToInt(Pct)), 16.0, White);
		}
		if (H == 4 && Pct < 15.f)
		{
			Warning(Pen, X + 147, 161, Red);
		}
	}
	// NAV / SCM
	Pen.Bracket(1107, 143, 1203, 265, Ink, 12.0, false);
	Pen.Lines({ {1120, 205}, {1210, 205} }, InkDim, 1.2f);
	Pen.Text(1140, 180, TEXT("NAV"), 20.0, T->bNav ? White : InkDim);
	Pen.Lines({ {1128, 170}, {1128, 190} }, T->bNav ? Ink : InkDim, 2.f);
	Pen.Text(1140, 231, TEXT("SCM"), 20.0, T->bNav ? InkDim : White);
	Pen.Lines({ {1128, 221}, {1128, 241} }, T->bNav ? InkDim : FLinearColor(0.3f, 1.f, 0.5f, 1.f), 3.f);
	// notifications, the bell, close
	Pen.Bracket(1225, 145, 1715, 268, Ink, 14.0, false);
	Pen.Lines({ {1240, 147}, {1700, 147} }, InkFaint, 1.f);
	const bool bNote = T->NotificationTime > 0.f && !T->Notification.IsEmpty();
	Pen.Text(1470, 206, bNote ? T->Notification : TEXT("NOTIFICATIONS EMPTY"), 15.0, bNote ? White : InkDim, 0);
	Pen.Lines({ {1736, 188}, {1736, 176}, {1739, 168}, {1747, 164}, {1755, 168}, {1758, 176}, {1758, 188}, {1762, 192}, {1732, 192}, {1736, 188} }, Ink, 2.f);
	Pen.Lines({ {1743, 204}, {1747, 199}, {1751, 204} }, Ink, 2.f);
	Pen.Lines({ {1800, 165}, {1840, 205} }, White, 2.4f);
	Pen.Lines({ {1840, 165}, {1800, 205} }, White, 2.4f);

	// ---- the side tabs and the main panel --------------------------------------------------------------------------
	const bool bEdit = T->Tab == 1 && T->bEditing;
	const FLinearColor Frame = bEdit ? Amber : Ink;
	for (int32 K = 0; K < 3; ++K)
	{
		const bool bOn = T->Tab == K;
		const double Y0 = TabY[K][0], Y1 = TabY[K][1];
		const FLinearColor C = bOn ? (bEdit ? Amber : Ink) : InkDim;
		Pen.Fill(212, Y0, 252, Y1, bOn ? CardFill : PanelFill);
		Pen.Lines({ {252, Y0}, {214, Y0 + 8}, {212, Y1 - 8}, {252, Y1} }, C, bOn ? 2.2f : 1.4f);
		Pen.TextUp(231, (Y0 + Y1) * 0.5 - 12, TabNames[K], 17.0, bOn ? White : Ink * FLinearColor(0.75f, 0.75f, 0.75f, 1.f));
		// the tab's small glyph under its name
		const double Gy = Y1 - 20;
		if (K == 0)
		{
			Pen.Lines({ {229, Gy - 8}, {223, Gy + 6}, {229, Gy + 2}, {235, Gy + 6}, {229, Gy - 8} }, C, 1.8f);
		}
		else if (K == 1)
		{
			for (int32 B = 0; B < 3; ++B)
			{
				Pen.Fill(223 + B * 5, Gy + 6 - B * 3, 226 + B * 5, Gy + 8, C);
			}
		}
		else
		{
			Pen.Lines({ {223, Gy - 6}, {223, Gy + 6} }, C, 1.6f);
			Pen.Lines({ {229, Gy - 6}, {229, Gy + 6} }, C, 1.6f);
			Pen.Lines({ {235, Gy - 6}, {235, Gy + 6} }, C, 1.6f);
			Pen.Fill(221, Gy - 2, 226, Gy + 1, C);
			Pen.Fill(227, Gy + 2, 232, Gy + 5, C);
			Pen.Fill(233, Gy - 4, 238, Gy - 1, C);
		}
	}
	Pen.Chamfer(232, 330, 1815, 893, 22, Frame, bEdit ? 3.f : 1.6f, true, PanelFill);
	Pen.Fill(250, 330, 1798, 333, Frame * FLinearColor(1, 1, 1, 0.25f));

	if (T->Tab == 1)
	{
		// ---- CONFIG: the edit badge and buttons ------------------------------------------------------------------
		if (bEdit)
		{
			Pen.Fill(915, 342, 1150, 376, Amber);
			Pen.Lines({ {905, 342}, {915, 342}, {915, 376}, {905, 368}, {905, 342} }, Amber, 2.f);
			Pen.Lines({ {1150, 342}, {1160, 342}, {1160, 368}, {1150, 376} }, Amber, 2.f);
			Pen.Text(1020, 359, FString::Printf(TEXT("EDIT / %s"), *T->EditName), 16.0, Dark, 0);
			Pen.Rect(1121, 349, 1141, 369, Dark, 1.6f, 4);
			Pen.Lines({ {1125, 353}, {1137, 365} }, Dark, 1.6f, 4);
			Pen.Lines({ {1137, 353}, {1125, 365} }, Dark, 1.6f, 4);
		}
		else
		{
			Pen.Text(1030, 360, FString::Printf(TEXT("CONFIG / %s"), *T->CurrentConfig), 16.0, InkDim, 0);
		}
		for (int32 B = 0; B < 3; ++B)
		{
			const double X0 = ButtonX[B][0], X1 = ButtonX[B][1];
			Pen.Fill(X0, 345, X1, 380, bEdit ? Dark : PanelFill);
			Pen.Rect(X0, 345, X1, 380, bEdit ? InkDim : InkFaint, 1.4f);
			const FLinearColor C = bEdit ? White : InkFaint;
			const double Ix = X0 + 18;
			if (B == 0)
			{
				Pen.Circle(Ix, 362, 7, C, 2.f, 14, 40, 330);
			}
			else if (B == 1)
			{
				Pen.Fill(Ix - 9, 353, Ix + 9, 371, C);
				Pen.Fill(Ix - 5, 354, Ix + 5, 360, Dark);
			}
			else
			{
				Pen.Lines({ {Ix - 9, 362}, {Ix - 3, 369}, {Ix + 10, 352} }, C, 3.f);
			}
			Pen.Text(X0 + (B == 1 ? 45 : 34), 362, ButtonNames[B], 14.0, C);
		}

		// ---- power sources ----------------------------------------------------------------------------------------
		Pen.Chamfer(410, 415, 700, 845, 10, CardFill, 1.f, true, CardFill);
		const int32 Used = T->UsedPips();
		const bool bDeny = T->DenyFlash > 0.f;
		for (int32 K = 0; K < T->PowerMax; ++K)
		{
			const double Y0 = PowerBottom - K * PowerPitch;
			FLinearColor C = K < Used ? Ink : K < T->PowerOut ? Ink * FLinearColor(0.45f, 0.45f, 0.45f, 1.f) : PipOff;
			if (bDeny && K >= Used - 1 && K < T->PowerOut)
			{
				C = Red;
			}
			Pen.Fill(PowerX0, Y0, PowerX1, Y0 + 22, C);
			Pen.Rect(PowerX0, Y0, PowerX1, Y0 + 22, K < T->PowerOut ? PipEdge : InkFaint, 1.f);
		}
		// the plant's own consumption (4 small pips) and its heat bar
		for (int32 K = 0; K < 4; ++K)
		{
			const double Y0 = PowerBottom - K * 26.0;
			Pen.Fill(508, Y0, 550, Y0 + 20, PipOff);
			Pen.Rect(508, Y0, 550, Y0 + 20, PipEdge, 1.f);
		}
		const float PlantHeat = FMath::Clamp(float(Used) / FMath::Max(1, T->PowerMax), 0.f, 1.f);
		for (int32 K = 0; K < 40; ++K)
		{
			const double Y = 718 - K * 3.0;
			const bool bLit = K < PlantHeat * 40.f;
			Pen.Lines({ {554, Y}, {566, Y} }, bLit ? (K > 33 ? Red : Ink) : InkFaint, 1.4f);
		}
		Pen.Text(568, 724, TEXT("°C"), 9.0, InkDim);
		Pen.Fill(482, 745, 548, 785, KeyFill);
		Pen.Rect(482, 745, 548, 785, Ink, 1.6f);
		Glyph(Pen, -1, 515, 765, Dark);
		Pen.Text(578, 820, TEXT("POWER SOURCES"), 15.0, InkDim, 0);
		// the arrow into the systems and the double rules either side
		Pen.Lines({ {716, 722}, {752, 762}, {716, 802} }, CardFill, 9.f);
		Pen.Lines({ {732, 415}, {732, 715} }, InkDim, 1.f);
		Pen.Lines({ {739, 415}, {739, 715} }, InkDim, 1.f);
		Pen.Lines({ {745, 815}, {745, 860} }, InkDim, 1.f);
		Pen.Lines({ {752, 815}, {752, 860} }, InkDim, 1.f);

		// ---- the systems ------------------------------------------------------------------------------------------
		for (int32 S = 0; S < T->Systems.Num(); ++S)
		{
			const FSpaceEngSystem& Sys = T->Systems[S];
			const double Cx = Columns[S];
			const bool bQuantumLocked = Sys.Icon == 3 && !T->bNav;
			for (int32 K = 0; K < Sys.MaxPips; ++K)
			{
				const double Y0 = PipBottom - K * PipPitch;
				const bool bLit = K < Sys.Pips && Sys.bOn;
				if (Sys.Icon == 0 && K == Sys.MaxPips - 1 && !bLit)
				{
					// weapons' top pip is the capacitor's spare: SC draws it as a dashed outline
					for (double D = 0; D < 40; D += 8)
					{
						Pen.Lines({ {Cx - PipHalfW + D, Y0}, {Cx - PipHalfW + D + 4, Y0} }, InkDim, 1.4f);
						Pen.Lines({ {Cx - PipHalfW + D, Y0 + PipH}, {Cx - PipHalfW + D + 4, Y0 + PipH} }, InkDim, 1.4f);
					}
					Pen.Lines({ {Cx - PipHalfW, Y0}, {Cx - PipHalfW, Y0 + 6} }, InkDim, 1.4f);
					Pen.Lines({ {Cx + PipHalfW, Y0}, {Cx + PipHalfW, Y0 + 6} }, InkDim, 1.4f);
					continue;
				}
				Pen.Fill(Cx - PipHalfW, Y0, Cx + PipHalfW, Y0 + PipH, bLit ? Ink : PipOff);
				// the top lit pip is the one you set: a white rim and a dark slot in it (SC's handle)
				if (bLit && K == Sys.Pips - 1)
				{
					Pen.Rect(Cx - PipHalfW - 2, Y0 - 2, Cx + PipHalfW + 2, Y0 + PipH + 2, White, 2.f);
					Pen.Lines({ {Cx - PipHalfW - 7, Y0 + PipH * 0.5}, {Cx - PipHalfW - 2, Y0 + PipH * 0.5} }, White, 2.f);
				}
				else
				{
					Pen.Rect(Cx - PipHalfW, Y0, Cx + PipHalfW, Y0 + PipH, bLit ? Ink : PipEdge, 1.f);
				}
			}
			// the H marker (where it runs hot)
			if (Sys.HotPips > 0 && Sys.HotPips <= Sys.MaxPips)
			{
				const double Hy = PipBottom - (Sys.HotPips - 1) * PipPitch;
				Pen.Lines({ {Cx - PipHalfW - 10, Hy - 3}, {Cx - PipHalfW - 10, Hy + PipH + 3} }, Amber, 2.f);
				Pen.Text(Cx - PipHalfW - 21, Hy + PipH * 0.5, TEXT("H"), 11.0, Amber, 0);
			}
			// the heat bar beside the column (the coolers have none)
			const double Bx = Cx + PipHalfW + 10;
			if (Sys.Group == 2)
			{
				const bool bKeyOn2 = Sys.bOn;
				Pen.Fill(Cx - 32, 742, Cx + 32, 782, bKeyOn2 ? KeyFill : PipOff);
				Pen.Rect(Cx - 32, 742, Cx + 32, 782, bKeyOn2 ? White * FLinearColor(1, 1, 1, 0.6f) : PipEdge, 1.2f);
				Glyph(Pen, Sys.Icon, Cx, 762, bKeyOn2 ? Dark : InkDim);
				continue;
			}
			const double Top = 592.0;
			const int32 Ticks = 40;
			for (int32 K = 0; K < Ticks; ++K)
			{
				const double Y = 718 - K * (718 - Top) / Ticks;
				const bool bLit = K < Sys.Heat * Ticks;
				const bool bHot = K > Ticks * 0.85;
				Pen.Lines({ {Bx, Y}, {Bx + 10, Y} }, bLit ? (bHot ? Red : Ink) : (bHot ? Red * FLinearColor(0.5f, 0.5f, 0.5f, 0.8f) : InkFaint), 1.4f);
			}
			Pen.Text(Bx + 12, 722, TEXT("°C"), 9.0, InkDim);
			// the key
			const bool bKeyOn = Sys.bOn && !bQuantumLocked;
			Pen.Fill(Cx - 32, 742, Cx + 32, 782, bKeyOn ? KeyFill : PipOff);
			Pen.Rect(Cx - 32, 742, Cx + 32, 782, bKeyOn ? White * FLinearColor(1, 1, 1, 0.6f) : PipEdge, 1.2f);
			Glyph(Pen, Sys.Icon, Cx, 762, bKeyOn ? Dark : InkDim);
		}
		// the quantum drive's mode note, the group rules and labels
		Pen.Text(1070, 752, TEXT("NAV"), 12.0, T->bNav ? White : InkDim, 0);
		Pen.Lines({ {1087, 746}, {1092, 752}, {1087, 758} }, T->bNav ? White : InkDim, 1.4f);
		Pen.Text(1078, 769, TEXT("SCM"), 12.0, T->bNav ? InkDim : White, 0);
		Pen.Lines({ {1058, 763}, {1053, 769}, {1058, 775} }, T->bNav ? InkDim : White, 1.4f);
		Pen.Lines({ {1220, 445}, {1220, 775} }, InkDim, 1.2f);
		Pen.Lines({ {1413, 615}, {1413, 825} }, InkDim, 1.2f);
		Pen.Text(1093, 817, TEXT("CORE SYSTEMS"), 15.0, InkDim, 0);
		Pen.Text(1516, 815, TEXT("COOLANT"), 15.0, InkDim, 0);
	}
	else if (T->Tab == 0)
	{
		// ---- 3D VIEW: the ship's wireframe ----------------------------------------------------------------------------
		// clipped to the panel: the x-ray spilled over the header and the tabs
		const FVector2D ClipA = Ref(240.0, 336.0), ClipB = Ref(1808.0, 888.0);
		Out.PushClip(FSlateClippingZone(FSlateRect(FVector2f(Geo.LocalToAbsolute(ClipA)), FVector2f(Geo.LocalToAbsolute(ClipB)))));
		const FLinearColor Wire(0.30f, 0.75f, 0.80f, 0.22f), WireBright(0.55f, 0.95f, 1.f, 0.55f);
		// the rooms: the corridor's frames and the end room as boxes (the filter ROOMS)
		auto BoxLines = [&](const FVector& C, const FVector& E, const FLinearColor& Col, float Th)
		{
			const FVector Pts[8] = { C + FVector(-E.X, -E.Y, -E.Z), C + FVector(E.X, -E.Y, -E.Z), C + FVector(E.X, E.Y, -E.Z), C + FVector(-E.X, E.Y, -E.Z),
				C + FVector(-E.X, -E.Y, E.Z), C + FVector(E.X, -E.Y, E.Z), C + FVector(E.X, E.Y, E.Z), C + FVector(-E.X, E.Y, E.Z) };
			const int32 Edges[12][2] = { {0,1},{1,2},{2,3},{3,0},{4,5},{5,6},{6,7},{7,4},{0,4},{1,5},{2,6},{3,7} };
			for (const auto& Ed : Edges)
			{
				Pen.LinesC({ T->Project(Pts[Ed[0]]), T->Project(Pts[Ed[1]]) }, Col, Th, 2);
			}
		};
		if (T->Filters[2])
		{
			// the rooms: the ship's own geometry as an x-ray (ASpaceEngineeringTerminal::BuildWire) - every edge twice, a
			// wide faint glow under a thin line, so overlapping layers build up the way SC's 3D view glows
			for (int32 K = 0; K < T->WireA.Num(); ++K)
			{
				const FVector2D A = T->Project(T->WireA[K]), B = T->Project(T->WireB[K]);
				const bool bBright = T->WireKind[K] > 0;
				Pen.LinesC({ A, B }, FLinearColor(0.25f, 0.75f, 0.85f, bBright ? 0.10f : 0.05f), 4.f, 2);
				Pen.LinesC({ A, B }, FLinearColor(0.45f, 0.90f, 1.f, bBright ? 0.55f : 0.24f), 1.1f, 2);
			}
		}
		if (T->Filters[0])
		{
			BoxLines(FVector(300, 0, 105), FVector(4, 55, 105), WireBright, 1.4f);
		}
		// connections from the relay (a fan of lines, SC's power routing)
		const FSpaceEngComponent* Relay = T->Components.Num() > 0 ? &T->Components[0] : nullptr;
		if (T->Filters[3] && Relay)
		{
			const FVector2D From = T->Project(Relay->Centre);
			for (int32 K = 1; K < T->Components.Num(); ++K)
			{
				Pen.LinesC({ From, T->Project(T->Components[K].Centre) }, WireBright, 1.4f, 3);
			}
			for (const FVector& Anchor : T->WireAnchors)
			{
				Pen.LinesC({ From, T->Project(Anchor) }, FLinearColor(0.55f, 0.95f, 1.f, 0.30f), 1.f, 3);
			}
		}
		// the components: bright blocks, the selected one with a ring and its letter
		if (T->Filters[1])
		{
			for (int32 K = 0; K < T->Components.Num(); ++K)
			{
				const FSpaceEngComponent& C = T->Components[K];
				FBox2D Bounds(ForceInit);
				for (int32 I = 0; I < 8; ++I)
				{
					const FVector Corner = C.Centre + FVector(I & 1 ? C.Extent.X : -C.Extent.X, I & 2 ? C.Extent.Y : -C.Extent.Y, I & 4 ? C.Extent.Z : -C.Extent.Z);
					Bounds += T->Project(Corner);
				}
				const bool bSel = K == T->SelectedComponent;
				Pen.FillC(Bounds.Min - FVector2D(10, 10), Bounds.Max + FVector2D(10, 10), FLinearColor(0.3f, 0.85f, 1.f, 0.10f), 3);
				Pen.FillC(Bounds.Min - FVector2D(4, 4), Bounds.Max + FVector2D(4, 4), FLinearColor(0.4f, 0.9f, 1.f, 0.16f), 3);
				Pen.FillC(Bounds.Min, Bounds.Max, FLinearColor(0.55f, 0.95f, 1.f, bSel ? 0.85f : 0.55f), 3);
				BoxLines(C.Centre, C.Extent, FLinearColor(0.75f, 1.f, 1.f, 0.9f), 1.6f);
				if (T->bShowIcons)
				{
					const FVector2D Mid = Bounds.GetCenter();
					const FVector2D Ic(Mid.X + 18.0, Bounds.Max.Y + 2.0);
					TArray<FVector2D> Ring;
					for (int32 S = 0; S <= 16; ++S)
					{
						const double A = 2.0 * PI * S / 16;
						Ring.Add(Ic + FVector2D(FMath::Cos(A), FMath::Sin(A)) * 8.0);
					}
					Pen.LinesC(Ring, FLinearColor(0.3f, 1.f, 0.55f, 1.f), 1.6f, 4);
					const FSlateFontInfo F = Font(9.f, true);
					FSlateDrawElement::MakeText(Out, Layer + 5, Geo.ToPaintGeometry(FVector2f(14.f, 14.f), FSlateLayoutTransform(FVector2f(Ic - FVector2D(3.5, 7.0)))),
						C.Letter, F, ESlateDrawEffect::None, FLinearColor(0.3f, 1.f, 0.55f, 1.f));
					Pen.FillC(Mid + FVector2D(-12, 0) + FVector2D(0, Bounds.GetExtent().Y), Mid + FVector2D(-8, 4) + FVector2D(0, Bounds.GetExtent().Y),
						FLinearColor(0.3f, 1.f, 0.55f, 1.f), 4);
				}
			}
		}
		Out.PopClip();
		// the filters
		Pen.Fill(285, 712, 520, 880, FLinearColor(0.f, 0.f, 0.f, 0.35f));
		Pen.Text(298, 727, TEXT("FILTERS"), 14.0, White);
		const TCHAR* FilterNames[4] = { TEXT("DOORS"), TEXT("SYSTEMS"), TEXT("ROOMS"), TEXT("CONNECTIONS") };
		for (int32 K = 0; K < 4; ++K)
		{
			const double Y = 751 + K * 25.0;
			const bool bOn = T->Filters[K];
			if (bOn)
			{
				Pen.Fill(300, Y - 3, 306, Y + 3, White);
			}
			else
			{
				Pen.Circle(303, Y, 3.5, InkDim, 1.4f, 10);
			}
			Pen.Rect(322, Y - 6, 334, Y + 6, bOn ? Ink : InkFaint, 1.2f);
			Pen.Text(350, Y, FilterNames[K], 13.0, bOn ? Ink : InkFaint);
		}
		Pen.Rect(312, 848, 515, 876, InkDim, 1.2f);
		Pen.Lines({ {335, 868}, {342, 855}, {349, 868}, {335, 868} }, White, 1.8f);
		Pen.Text(362, 862, TEXT("SHOW EMERGENCIES"), 13.0, White);
		// the info card of the selected component
		if (T->Components.IsValidIndex(T->SelectedComponent))
		{
			const FSpaceEngComponent& C = T->Components[T->SelectedComponent];
			Pen.Bracket(1455, 352, 1803, 490, Ink, 12.0, false);
			Pen.Fill(1470, 368, 1790, 422, CardFill);
			Pen.Lines({ {1472, 368}, {1472, 422} }, Ink, 3.f);
			Pen.Text(1510, 396, C.Letter, 30.0, White, 0, true);
			Pen.Text(1545, 386, C.Name, 16.0, White);
			Pen.Text(1545, 406, C.Name.Left(1) + C.Name.Mid(1).ToLower(), 14.0, InkDim);
			Pen.Fill(1486, 438, 1492, 456, White);
			Pen.Text(1510, 447, C.Detail, 15.0, White);
			Pen.Text(1660, 447, C.Value, 15.0, White);
		}
		// show icons
		Pen.Circle(1735, 836, 9, Ink, 1.5f, 16);
		Pen.Text(1735, 837, TEXT("i"), 10.0, Ink, 0);
		Pen.Text(1635, 864, TEXT("SHOW ICONS"), 12.0, T->bShowIcons ? White : InkDim);
		Pen.Rect(1724, 856, 1742, 872, T->bShowIcons ? White : InkDim, 1.2f);
	}
	else
	{
		// ---- PRESETS -------------------------------------------------------------------------------------------------
		Pen.Text(300, 372, TEXT("PRESETS"), 18.0, White);
		Pen.Lines({ {300, 392}, {1780, 392} }, InkDim, 1.f);
		for (int32 K = 0; K < T->Presets.Num(); ++K)
		{
			const double Y0 = 410 + K * 62.0;
			const bool bCur = T->Presets[K].Name == T->CurrentConfig;
			Pen.Fill(300, Y0, 1100, Y0 + 50, bCur ? CardFill : PanelFill);
			Pen.Lines({ {300, Y0}, {300, Y0 + 50} }, bCur ? Ink : InkDim, 3.f);
			Pen.Text(322, Y0 + 25, T->Presets[K].Name, 18.0, bCur ? White : Ink);
			int32 Sum = 0;
			for (const int32 P : T->Presets[K].Pips)
			{
				Sum += P;
			}
			Pen.Text(700, Y0 + 25, FString::Printf(TEXT("%d / %d PIPS   %s"), Sum, T->Presets[K].PowerOut, T->Presets[K].bNav ? TEXT("NAV") : TEXT("SCM")), 14.0, InkDim);
			Pen.Fill(960, Y0 + 9, 1085, Y0 + 41, bCur ? PanelFill : Dark);
			Pen.Rect(960, Y0 + 9, 1085, Y0 + 41, bCur ? InkFaint : Ink, 1.4f);
			Pen.Text(1022, Y0 + 25, bCur ? TEXT("APPLIED") : TEXT("APPLY"), 14.0, bCur ? InkDim : White, 0);
		}
	}

	// ---- the current config and the maker's watermark ----------------------------------------------------------------
	Pen.Bracket(292, 912, 767, 972, Ink, 12.0, false);
	Pen.Lines({ {300, 914}, {760, 914} }, InkFaint, 1.f);
	Pen.Text(328, 930, TEXT("CURRENT CONFIG"), 12.0, InkDim);
	Pen.Text(328, 956, T->CurrentConfig, 23.0, White, -1, true);
	const FLinearColor Mark(0.10f, 0.24f, 0.27f, 0.6f);
	Pen.Lines({ {1030, 935}, {1050, 905}, {1070, 935} }, Mark, 3.f);
	Pen.Lines({ {1040, 935}, {1050, 920}, {1060, 935} }, Mark, 3.f);
	Pen.Text(1050, 962, T->MakerName, 22.0, Mark, 0, true);
	return Layer + 6;
}

// =====================================================================================================================
// Terminal
// =====================================================================================================================
ASpaceEngineeringTerminal::ASpaceEngineeringTerminal()
{
	PrimaryActorTick.bCanEverTick = true;
	Housing = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Housing"));
	SetRootComponent(Housing);
	Screen = CreateDefaultSubobject<UWidgetComponent>(TEXT("Screen"));
	Screen->SetupAttachment(Housing);
	Screen->SetWidgetSpace(EWidgetSpace::World);
	Screen->SetWidgetClass(USpaceEngineeringScreen::StaticClass());
	Screen->SetDrawSize(FVector2D(USpaceEngineeringScreen::CanvasW, USpaceEngineeringScreen::CanvasH));
	Screen->SetPivot(FVector2D(0.5, 0.5));
	Screen->SetBlendMode(EWidgetBlendMode::Opaque);
	Screen->SetTwoSided(false);
	Screen->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Screen->SetCastShadow(false);
	Seed();
}

void ASpaceEngineeringTerminal::Seed()
{
	// SC's power board after the author's capture: weapons, thrusters, shields, quantum | life support, radar | 2 coolers
	auto Add = [this](const TCHAR* Name, int32 Icon, int32 Group, int32 Max, int32 Pips, int32 Hot)
	{
		FSpaceEngSystem S;
		S.Name = Name;
		S.Icon = Icon;
		S.Group = Group;
		S.MaxPips = Max;
		S.Pips = Pips;
		S.HotPips = Hot;
		Systems.Add(S);
	};
	Systems.Reset();
	Add(TEXT("WEAPONS"), 0, 0, 4, 0, 0);
	Add(TEXT("THRUSTERS"), 1, 0, 4, 1, 0);
	Add(TEXT("SHIELDS"), 2, 0, 4, 1, 3);
	Add(TEXT("QUANTUM"), 3, 0, 1, 0, 1);
	Add(TEXT("LIFE SUPPORT"), 4, 1, 1, 1, 1);
	Add(TEXT("RADAR"), 5, 1, 4, 1, 1);
	Add(TEXT("COOLER 1"), 6, 2, 2, 1, 2);
	Add(TEXT("COOLER 2"), 6, 2, 2, 1, 2);
	FSpaceEngPreset Default;
	Default.Name = TEXT("DEFAULT");
	for (const FSpaceEngSystem& S : Systems)
	{
		Default.Pips.Add(S.Pips);
	}
	Presets = { Default };
	// the 3D view's components (ship space, cm): the relay over the corridor, the plant and coolers in the end room
	auto Comp = [this](const TCHAR* Letter, const TCHAR* Name, const TCHAR* Detail, const TCHAR* Value, FVector C, FVector E)
	{
		FSpaceEngComponent K;
		K.Letter = Letter;
		K.Name = Name;
		K.Detail = Detail;
		K.Value = Value;
		K.Centre = C;
		K.Extent = E;
		Components.Add(K);
	};
	Components.Reset();
	Comp(TEXT("R"), TEXT("RELAY"), TEXT("Fuses"), TEXT("2/2"), FVector(-60, 0, 205), FVector(26, 20, 12));
	Comp(TEXT("P"), TEXT("POWER PLANT"), TEXT("Output"), TEXT("10/10"), FVector(280, 0, 50), FVector(40, 38, 50));
	Comp(TEXT("C"), TEXT("COOLER"), TEXT("Coolant"), TEXT("100%"), FVector(280, -105, 32), FVector(22, 18, 32));
	Comp(TEXT("C"), TEXT("COOLER"), TEXT("Coolant"), TEXT("100%"), FVector(280, 105, 32), FVector(22, 18, 32));
	Comp(TEXT("L"), TEXT("LIFE SUPPORT"), TEXT("Filters"), TEXT("4/4"), FVector(-150, 108, 60), FVector(10, 8, 22));
	BuildWire();
}

void ASpaceEngineeringTerminal::BeginPlay()
{
	Super::BeginPlay();
	if (!FApp::CanEverRender())
	{
		return;
	}
	const double Scale = GlassSizeCm.X / USpaceEngineeringScreen::CanvasW;
	Screen->SetRelativeLocation(GlassCentreCm);
	Screen->SetRelativeScale3D(FVector(1.0, Scale, Scale));
	Screen->InitWidget();
	if (USpaceEngineeringScreen* W = Cast<USpaceEngineeringScreen>(Screen->GetUserWidgetObject()))
	{
		W->Terminal = this;
	}
}

void ASpaceEngineeringTerminal::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	Orbit = FMath::Fmod(Orbit + DeltaSeconds * 4.f, 360.f);
	DenyFlash = FMath::Max(0.f, DenyFlash - DeltaSeconds);
	NotificationTime = FMath::Max(0.f, NotificationTime - DeltaSeconds);
	// heat: each system warms towards its share of power, the coolers pull everything down
	int32 Cooling = 0;
	for (const FSpaceEngSystem& S : Systems)
	{
		Cooling += S.Group == 2 && S.bOn ? S.Pips : 0;
	}
	const float CoolShare = Cooling / 4.f;
	for (FSpaceEngSystem& S : Systems)
	{
		const float Load = S.bOn ? float(S.Pips) / FMath::Max(1, S.MaxPips) : 0.f;
		const float Target = S.Group == 2 ? 0.15f + Load * 0.35f : FMath::Clamp(0.12f + Load * 0.95f - CoolShare * 0.35f, 0.05f, 1.f);
		S.Heat = FMath::FInterpTo(S.Heat, Target, DeltaSeconds, 0.6f);
	}
}

int32 ASpaceEngineeringTerminal::UsedPips() const
{
	int32 Used = 0;
	for (const FSpaceEngSystem& S : Systems)
	{
		Used += S.bOn ? S.Pips : 0;
	}
	return Used;
}

float ASpaceEngineeringTerminal::Percent(int32 Header) const
{
	switch (Header)
	{
	case 0: return 100.f;                        // armor (no damage model yet)
	case 1: return 100.f;                        // hull
	case 2:                                      // cooling: the coolers' share of what the systems need
	{
		int32 Cooling = 0, Heat = 0;
		for (const FSpaceEngSystem& S : Systems)
		{
			(S.Group == 2 ? Cooling : Heat) += S.bOn ? S.Pips : 0;
		}
		return FMath::Clamp(100.f * Cooling / FMath::Max(1, Heat + Cooling), 0.f, 100.f);
	}
	case 3:                                      // life support: its pip and the plant's headroom
		return Systems.IsValidIndex(4) && Systems[4].bOn && Systems[4].Pips > 0 ? 100.f : 0.f;
	default: return 100.f;                       // hydrogen fuel (full tanks in the test section)
	}
}

void ASpaceEngineeringTerminal::MarkEdited()
{
	if (!bEditing)
	{
		bEditing = true;
		EditName = FString::Printf(TEXT("NEWPRESET_%d"), Presets.Num());
	}
}

void ASpaceEngineeringTerminal::ClickPip(int32 System, int32 Pip)
{
	if (!Systems.IsValidIndex(System))
	{
		return;
	}
	FSpaceEngSystem& S = Systems[System];
	if (S.Icon == 3 && !bNav)
	{
		Notification = TEXT("QUANTUM DRIVE: SWITCH TO NAV");
		NotificationTime = 3.f;
		return;
	}
	// a click on the top lit pip takes it away, any other sets the level (SC)
	const int32 Want = (Pip + 1 == S.Pips) ? Pip : Pip + 1;
	const int32 Free = PowerOut - (UsedPips() - (S.bOn ? S.Pips : 0));
	if (Want > Free)
	{
		DenyFlash = 0.6f;
		Notification = TEXT("NOT ENOUGH POWER");
		NotificationTime = 2.5f;
		return;
	}
	S.Pips = FMath::Clamp(Want, 0, S.MaxPips);
	S.bOn = true;
	Tab = 1;
	MarkEdited();
}

void ASpaceEngineeringTerminal::ClickPowerPip(int32 Pip)
{
	const int32 Want = (Pip + 1 == PowerOut) ? Pip : Pip + 1;
	if (Want < UsedPips())
	{
		DenyFlash = 0.6f;
		Notification = TEXT("LOWER THE SYSTEMS FIRST");
		NotificationTime = 2.5f;
		return;
	}
	PowerOut = FMath::Clamp(Want, 0, PowerMax);
	MarkEdited();
}

void ASpaceEngineeringTerminal::ToggleSystem(int32 System)
{
	if (Systems.IsValidIndex(System))
	{
		Systems[System].bOn = !Systems[System].bOn;
		MarkEdited();
	}
}

void ASpaceEngineeringTerminal::SetNav(bool bInNav)
{
	bNav = bInNav;
	if (!bNav)
	{
		for (FSpaceEngSystem& S : Systems)
		{
			S.Pips = S.Icon == 3 ? 0 : S.Pips;
		}
	}
	Notification = bNav ? TEXT("NAV MODE") : TEXT("SCM MODE");
	NotificationTime = 2.f;
}

void ASpaceEngineeringTerminal::ClearAll()
{
	for (FSpaceEngSystem& S : Systems)
	{
		S.Pips = 0;
	}
	MarkEdited();
}

void ASpaceEngineeringTerminal::Save(bool bApply)
{
	FSpaceEngPreset P;
	P.Name = bEditing ? EditName : CurrentConfig;
	for (const FSpaceEngSystem& S : Systems)
	{
		P.Pips.Add(S.Pips);
	}
	P.PowerOut = PowerOut;
	P.bNav = bNav;
	const int32 Existing = Presets.IndexOfByPredicate([&](const FSpaceEngPreset& Q) { return Q.Name == P.Name; });
	if (Existing != INDEX_NONE)
	{
		Presets[Existing] = P;
	}
	else
	{
		Presets.Add(P);
	}
	Notification = FString::Printf(TEXT("%s SAVED"), *P.Name);
	NotificationTime = 2.5f;
	if (bApply)
	{
		CurrentConfig = P.Name;
		bEditing = false;
	}
}

void ASpaceEngineeringTerminal::CancelEdit()
{
	const int32 Index = Presets.IndexOfByPredicate([&](const FSpaceEngPreset& Q) { return Q.Name == CurrentConfig; });
	ApplyPreset(Index);
}

void ASpaceEngineeringTerminal::ApplyPreset(int32 Index)
{
	if (!Presets.IsValidIndex(Index))
	{
		return;
	}
	const FSpaceEngPreset& P = Presets[Index];
	for (int32 K = 0; K < Systems.Num() && K < P.Pips.Num(); ++K)
	{
		Systems[K].Pips = P.Pips[K];
		Systems[K].bOn = true;
	}
	PowerOut = P.PowerOut;
	bNav = P.bNav;
	CurrentConfig = P.Name;
	bEditing = false;
}

float ASpaceEngineeringTerminal::ColumnX(int32 System)
{
	return System >= 0 && System < int32(UE_ARRAY_COUNT(Columns)) ? float(Columns[System]) : 0.f;
}

FBox2D ASpaceEngineeringTerminal::PipBox(float CentreX, int32 Pip)
{
	const double Y0 = PipBottom - Pip * PipPitch;
	return FBox2D(USpaceEngineeringScreen::Ref(CentreX - PipHalfW, Y0), USpaceEngineeringScreen::Ref(CentreX + PipHalfW, Y0 + PipH));
}

FVector ASpaceEngineeringTerminal::CanvasToWorld(const FVector2D& Canvas) const
{
	// the widget faces +X; the canvas' x runs to the viewer's right (-Y local), its y down (-Z)
	const FVector Local(GlassCentreCm.X + 0.3,
		GlassCentreCm.Y - (Canvas.X / USpaceEngineeringScreen::CanvasW - 0.5) * GlassSizeCm.X,
		GlassCentreCm.Z - (Canvas.Y / USpaceEngineeringScreen::CanvasH - 0.5) * GlassSizeCm.Y);
	return GetActorTransform().TransformPosition(Local);
}

FVector2D ASpaceEngineeringTerminal::Project(const FVector& P) const
{
	// SC's 3D view looks along the ship from inside its start, a little above the floor: the camera before the first
	// frame, aimed down the corridor at the end room, swaying slowly from side to side
	const double Sway = FMath::Sin(FMath::DegreesToRadians(Orbit * 3.0));
	const FVector Eye(-470.0, 70.0 * Sway, 165.0);
	const FVector Aim(260.0, -40.0 * Sway, 95.0);
	const FVector F = (Aim - Eye).GetSafeNormal();
	const FVector R = FVector::CrossProduct(FVector::UpVector, F).GetSafeNormal();
	const FVector U = FVector::CrossProduct(F, R);
	const FVector D = P - Eye;
	const double Depth = FMath::Max(15.0, FVector::DotProduct(D, F));
	const double Focal = 720.0;
	const FVector2D Centre = USpaceEngineeringScreen::Ref(1030.0, 600.0);
	return Centre + FVector2D(FVector::DotProduct(D, R), -FVector::DotProduct(D, U)) * (Focal / Depth) * USpaceEngineeringScreen::RefScale;
}

void ASpaceEngineeringTerminal::BuildWire()
{
	// the test section as the 3D view draws it (cm, x along the corridor from its middle): the portals' frames (an outer
	// and an inner ring, 30 cm deep), the boots, the wall modules' fields, the floor plates, the ceiling lights, the end
	// room
	WireA.Reset();
	WireB.Reset();
	WireKind.Reset();
	WireAnchors.Reset();
	auto Seg = [this](const FVector& A, const FVector& B, uint8 Kind) { WireA.Add(A); WireB.Add(B); WireKind.Add(Kind); };
	auto Poly = [&](const TArray<FVector>& Pts, bool bClose, uint8 Kind)
	{
		for (int32 K = 0; K + 1 < Pts.Num(); ++K)
		{
			Seg(Pts[K], Pts[K + 1], Kind);
		}
		if (bClose && Pts.Num() > 2)
		{
			Seg(Pts.Last(), Pts[0], Kind);
		}
	};
	const FVector2D Oct[] = { {-120, 0}, {-120, 130}, {-60, 210}, {-60, 230}, {60, 230}, {60, 210}, {120, 130}, {120, 0} };
	auto Ring = [&](double X, double Inset)
	{
		TArray<FVector> Out;
		for (const FVector2D& O : Oct)
		{
			const double Y = O.X - FMath::Sign(O.X) * Inset;
			const double Z = O.Y < 1.0 ? 0.0 : O.Y - (O.Y > 220.0 ? Inset : 0.0);
			Out.Add(FVector(X, Y, Z));
		}
		return Out;
	};
	for (int32 F = 0; F < 5; ++F)
	{
		const double X0 = -300.0 + F * 120.0, X1 = X0 + 30.0;
		const TArray<FVector> A0 = Ring(X0, 0.0), A1 = Ring(X1, 0.0), B0 = Ring(X0, 10.0), B1 = Ring(X1, 10.0);
		Poly(B0, false, 1);
		Poly(B1, false, 1);
		Poly(A0, false, 0);
		Poly(A1, false, 0);
		for (int32 K = 0; K < B0.Num(); ++K)
		{
			Seg(B0[K], B1[K], 0);
			WireAnchors.Add(B0[K]);
		}
		for (const double S : { -1.0, 1.0 })
		{
			const FVector C(X0 + 15.0, S * 103.0, 15.0);
			const FVector E(15.0, 17.0, 0.0);
			Poly({ C + FVector(-E.X, -E.Y, 0), C + FVector(E.X, -E.Y, 0), C + FVector(E.X, E.Y, 0), C + FVector(-E.X, E.Y, 0) }, true, 0);
		}
		if (F == 4)
		{
			break;
		}
		// the wall module up to the next frame: the main field (two levels), the vent band, the slope panel
		const double M0 = X1 + 6.0, M1 = X0 + 120.0 - 6.0;
		for (const double S : { -1.0, 1.0 })
		{
			const double Y = S * 119.0;
			Poly({ FVector(M0, Y, 39), FVector(M1, Y, 39), FVector(M1, Y, 112), FVector(M0, Y, 112) }, true, 0);
			Poly({ FVector(M0 + 4, Y, 45), FVector(M1 - 4, Y, 45), FVector(M1 - 4, Y, 106), FVector(M0 + 4, Y, 106) }, true, 0);
			Poly({ FVector(M0, Y, 13), FVector(M1, Y, 13), FVector(M1, Y, 33), FVector(M0, Y, 33) }, true, 0);
			Poly({ FVector(M0, S * 116.0, 136.0), FVector(M1, S * 116.0, 136.0), FVector(M1, S * 64.0, 205.0), FVector(M0, S * 64.0, 205.0) }, true, 0);
		}
		Poly({ FVector(M0, -55, 0), FVector(M1, -55, 0), FVector(M1, 55, 0), FVector(M0, 55, 0) }, true, 0);
		Poly({ FVector(M0 + 10, -45, 0), FVector(M1 - 10, -45, 0), FVector(M1 - 10, 45, 0), FVector(M0 + 10, 45, 0) }, true, 0);
		const double Lc = (M0 + M1) * 0.5;
		Poly({ FVector(Lc - 25, -6, 229), FVector(Lc + 25, -6, 229), FVector(Lc + 25, 6, 229), FVector(Lc - 25, 6, 229) }, true, 1);
		WireAnchors.Add(FVector(Lc, 0, 229));
	}
	// the end room with the terminal's wall
	const double RX0 = 180.0, RX1 = 360.0, RY = 150.0, RZ = 240.0;
	Poly({ FVector(RX0, -RY, 0), FVector(RX1, -RY, 0), FVector(RX1, RY, 0), FVector(RX0, RY, 0) }, true, 0);
	Poly({ FVector(RX0, -RY, RZ), FVector(RX1, -RY, RZ), FVector(RX1, RY, RZ), FVector(RX0, RY, RZ) }, true, 0);
	for (const FVector2D& C : { FVector2D(RX0, -RY), FVector2D(RX1, -RY), FVector2D(RX1, RY), FVector2D(RX0, RY) })
	{
		Seg(FVector(C.X, C.Y, 0), FVector(C.X, C.Y, RZ), 0);
	}
}

void ASpaceEngineeringTerminal::GatherHotspots(TArray<FSpaceHotspot>& Out)
{
	const double CmPerPx = GlassSizeCm.X / USpaceEngineeringScreen::CanvasW;
	const TWeakObjectPtr<ASpaceEngineeringTerminal> Weak(this);
	auto Spot = [&](const FBox2D& Box, TFunction<void(ASpaceEngineeringTerminal*)> Use)
	{
		FSpaceHotspot S;
		S.WorldLocation = CanvasToWorld(Box.GetCenter());
		const FVector2D Size = Box.GetSize();
		S.SizeCm = float(Size.X * CmPerPx);
		S.Aspect = float(Size.X / FMath::Max(1.0, Size.Y));
		S.Use = [Weak, Use](bool bPrimary)
		{
			if (ASpaceEngineeringTerminal* Live = Weak.Get(); Live && bPrimary)
			{
				Use(Live);
			}
		};
		Out.Add(MoveTemp(S));
	};
	auto RefBox = [](double X0, double Y0, double X1, double Y1) { return FBox2D(USpaceEngineeringScreen::Ref(X0, Y0), USpaceEngineeringScreen::Ref(X1, Y1)); };
	for (int32 K = 0; K < 3; ++K)
	{
		Spot(RefBox(212, TabY[K][0], 252, TabY[K][1]), [K](ASpaceEngineeringTerminal* T) { T->Tab = K; });
	}
	Spot(RefBox(1115, 160, 1200, 200), [](ASpaceEngineeringTerminal* T) { T->SetNav(true); });
	Spot(RefBox(1115, 212, 1200, 252), [](ASpaceEngineeringTerminal* T) { T->SetNav(false); });
	if (Tab == 1)
	{
		for (int32 S = 0; S < Systems.Num(); ++S)
		{
			for (int32 K = 0; K < Systems[S].MaxPips; ++K)
			{
				Spot(PipBox(ColumnX(S), K), [S, K](ASpaceEngineeringTerminal* T) { T->ClickPip(S, K); });
			}
			Spot(RefBox(ColumnX(S) - 32, 742, ColumnX(S) + 32, 782), [S](ASpaceEngineeringTerminal* T) { T->ToggleSystem(S); });
		}
		for (int32 K = 0; K < PowerMax; ++K)
		{
			const double Y0 = PowerBottom - K * PowerPitch;
			Spot(RefBox(PowerX0, Y0, PowerX1, Y0 + 22), [K](ASpaceEngineeringTerminal* T) { T->ClickPowerPip(K); });
		}
		if (bEditing)
		{
			Spot(RefBox(ButtonX[0][0], 345, ButtonX[0][1], 380), [](ASpaceEngineeringTerminal* T) { T->ClearAll(); });
			Spot(RefBox(ButtonX[1][0], 345, ButtonX[1][1], 380), [](ASpaceEngineeringTerminal* T) { T->Save(false); });
			Spot(RefBox(ButtonX[2][0], 345, ButtonX[2][1], 380), [](ASpaceEngineeringTerminal* T) { T->Save(true); });
			Spot(RefBox(1121, 349, 1141, 369), [](ASpaceEngineeringTerminal* T) { T->CancelEdit(); });
		}
	}
	else if (Tab == 0)
	{
		for (int32 K = 0; K < 4; ++K)
		{
			const double Y = 751 + K * 25.0;
			Spot(RefBox(296, Y - 10, 500, Y + 10), [K](ASpaceEngineeringTerminal* T) { T->Filters[K] = !T->Filters[K]; });
		}
		Spot(RefBox(1630, 852, 1745, 874), [](ASpaceEngineeringTerminal* T) { T->bShowIcons = !T->bShowIcons; });
		for (int32 K = 0; K < Components.Num(); ++K)
		{
			const FVector2D C = Project(Components[K].Centre);
			Spot(FBox2D(C - FVector2D(22, 16), C + FVector2D(22, 16)), [K](ASpaceEngineeringTerminal* T) { T->SelectedComponent = K; });
		}
	}
	else
	{
		for (int32 K = 0; K < Presets.Num(); ++K)
		{
			const double Y0 = 410 + K * 62.0;
			Spot(RefBox(960, Y0 + 9, 1085, Y0 + 41), [K](ASpaceEngineeringTerminal* T) { T->ApplyPreset(K); });
		}
	}
}

// Shots and tests drive the terminal without the mouse: space.EngTab <0 3D | 1 CONFIG | 2 PRESETS>,
// space.EngClick <system> <pip> (system -1 = the power sources), space.EngSave <0|1 apply>, space.EngNav <0|1>.
namespace SpaceEngConsole
{
	template <typename F>
	void ForEach(UWorld* World, F&& Fn)
	{
		for (TActorIterator<ASpaceEngineeringTerminal> It(World); It; ++It)
		{
			Fn(**It);
		}
	}
	FAutoConsoleCommandWithWorldAndArgs Tab(TEXT("space.EngTab"), TEXT("space.EngTab <0 3D VIEW | 1 CONFIG | 2 PRESETS>"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& A, UWorld* W)
		{
			ForEach(W, [&](ASpaceEngineeringTerminal& T) { T.Tab = A.Num() > 0 ? FCString::Atoi(*A[0]) : 1; });
		}));
	FAutoConsoleCommandWithWorldAndArgs Click(TEXT("space.EngClick"), TEXT("space.EngClick <system, -1 = power> <pip>"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& A, UWorld* W)
		{
			if (A.Num() >= 2)
			{
				const int32 S = FCString::Atoi(*A[0]), P = FCString::Atoi(*A[1]);
				ForEach(W, [&](ASpaceEngineeringTerminal& T) { S < 0 ? T.ClickPowerPip(P) : T.ClickPip(S, P); });
			}
		}));
	FAutoConsoleCommandWithWorldAndArgs Save(TEXT("space.EngSave"), TEXT("space.EngSave <0 save | 1 save and apply>"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& A, UWorld* W)
		{
			ForEach(W, [&](ASpaceEngineeringTerminal& T) { T.Save(A.Num() > 0 && FCString::Atoi(*A[0]) != 0); });
		}));
	FAutoConsoleCommandWithWorldAndArgs Nav(TEXT("space.EngNav"), TEXT("space.EngNav <0 SCM | 1 NAV>"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& A, UWorld* W)
		{
			ForEach(W, [&](ASpaceEngineeringTerminal& T) { T.SetNav(A.Num() > 0 && FCString::Atoi(*A[0]) != 0); });
		}));
}

#undef LOCTEXT_NAMESPACE
