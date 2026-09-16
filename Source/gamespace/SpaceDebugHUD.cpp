// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceDebugHUD.h"

#include "CelestialBody.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "EngineUtils.h"
#include "SpaceshipPawn.h"

namespace
{
	FString FormatDistance(double Centimetres)
	{
		const double Metres = FMath::Max(Centimetres, 0.0) / 100.0;
		return Metres < 1000.0
			? FString::Printf(TEXT("%.0f m"), Metres)
			: FString::Printf(TEXT("%.2f km"), Metres / 1000.0);
	}

	/** "TARGET" readout for the nearest celestial body: name, surface distance, time to reach it. */
	FString DescribeNearestBody(const UWorld* World, const ASpaceshipPawn& Ship)
	{
		const FVector ShipLocation = Ship.GetActorLocation();

		const ACelestialBody* Nearest = nullptr;
		double NearestDistance = TNumericLimits<double>::Max();
		// A handful of bodies at most, so a per-frame walk is cheaper than keeping a registry.
		for (TActorIterator<ACelestialBody> It(World); It; ++It)
		{
			const double Distance = It->GetSurfaceDistance(ShipLocation);
			if (Distance < NearestDistance)
			{
				NearestDistance = Distance;
				Nearest = *It;
			}
		}

		if (!Nearest)
		{
			return TEXT("none");
		}

		// Only the part of the velocity pointing at the body closes the gap.
		const FVector ToBody = (Nearest->GetActorLocation() - ShipLocation).GetSafeNormal();
		const double ClosingSpeed = FVector::DotProduct(Ship.GetLinearVelocity(), ToBody);

		FString Eta = TEXT("--:--");
		if (ClosingSpeed > 50.0 && NearestDistance > 0.0)
		{
			const int32 Seconds = FMath::RoundToInt32(NearestDistance / ClosingSpeed);
			Eta = FString::Printf(TEXT("%d:%02d"), Seconds / 60, Seconds % 60);
		}

		return FString::Printf(TEXT("%s   %s   ETA %s"),
			*Nearest->GetDisplayName().ToString(), *FormatDistance(NearestDistance), *Eta);
	}
}

void ASpaceDebugHUD::DrawHUD()
{
	Super::DrawHUD();

	const ASpaceshipPawn* Ship = Cast<ASpaceshipPawn>(GetOwningPawn());
	if (!Ship || !Canvas || !GEngine)
	{
		return;
	}

	UFont* Font = GEngine->GetMediumFont();

	// Unreal units are centimetres.
	const float SpeedMetres = Ship->GetSpeed() / 100.f;

	struct FLine
	{
		const TCHAR* Label;
		FString Value;
		FLinearColor Color;
	};

	const FLine Lines[] = {
		{ TEXT("SPEED"), FString::Printf(TEXT("%6.1f m/s   %5.0f km/h"), SpeedMetres, SpeedMetres * 3.6f), FLinearColor::White },
		{ TEXT("THROTTLE"), FString::Printf(TEXT("%+4.0f %%"), Ship->GetThrottle() * 100.f), FLinearColor::White },
		{ TEXT("BOOST"), Ship->IsBoosting() ? TEXT("ON") : TEXT("off"),
			Ship->IsBoosting() ? FLinearColor(1.f, 0.55f, 0.1f) : FLinearColor(0.6f, 0.6f, 0.6f) },
		{ TEXT("CAMERA"), Ship->IsCockpitView() ? TEXT("Cockpit") : TEXT("Chase"), FLinearColor::White },
		{ TEXT("TARGET"), DescribeNearestBody(GetWorld(), *Ship), FLinearColor(0.6f, 1.f, 0.7f) },
	};

	const float LineHeight = Font->GetMaxCharHeight() * TextScale * 1.25f;
	const float ValueColumn = 130.f * TextScale;
	const float Padding = 10.f;

	// Size the backing to the longest value so the target line never spills out of it.
	float WidestValue = 0.f;
	for (const FLine& Line : Lines)
	{
		float Width = 0.f;
		float Height = 0.f;
		GetTextSize(Line.Value, Width, Height, Font, TextScale);
		WidestValue = FMath::Max(WidestValue, Width);
	}

	// Dark backing so the numbers stay readable against a bright sky or a lit asteroid.
	DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.55f), Origin.X - Padding, Origin.Y - Padding,
		ValueColumn + WidestValue + Padding * 2.f, LineHeight * UE_ARRAY_COUNT(Lines) + Padding * 2.f);

	float Y = Origin.Y;
	for (const FLine& Line : Lines)
	{
		DrawText(Line.Label, FLinearColor(0.55f, 0.8f, 1.f), Origin.X, Y, Font, TextScale);
		DrawText(Line.Value, Line.Color, Origin.X + ValueColumn, Y, Font, TextScale);
		Y += LineHeight;
	}
}
