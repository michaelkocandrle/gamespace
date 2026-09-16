// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceDebugHUD.h"

#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "SpaceshipPawn.h"

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
	};

	const float LineHeight = Font->GetMaxCharHeight() * TextScale * 1.25f;
	const float ValueColumn = 130.f * TextScale;
	const float Padding = 10.f;

	// Dark backing so the numbers stay readable against a bright sky or a lit asteroid.
	DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.55f), Origin.X - Padding, Origin.Y - Padding,
		ValueColumn + 260.f * TextScale + Padding * 2.f, LineHeight * UE_ARRAY_COUNT(Lines) + Padding * 2.f);

	float Y = Origin.Y;
	for (const FLine& Line : Lines)
	{
		DrawText(Line.Label, FLinearColor(0.55f, 0.8f, 1.f), Origin.X, Y, Font, TextScale);
		DrawText(Line.Value, Line.Color, Origin.X + ValueColumn, Y, Font, TextScale);
		Y += LineHeight;
	}
}
