// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "SpaceDebugHUD.generated.h"

/**
 * Plain-text flight readout drawn straight onto the canvas: speed, throttle, boost, camera, and
 * distance and ETA to the nearest ACelestialBody.
 *
 * A stopgap for tuning the flight model, deliberately not UMG. It needs no widget asset and no
 * extra module, and gets replaced once a real HUD exists.
 */
UCLASS()
class GAMESPACE_API ASpaceDebugHUD : public AHUD
{
	GENERATED_BODY()

public:
	virtual void DrawHUD() override;

protected:
	/** Top-left corner of the readout, in screen pixels. */
	UPROPERTY(EditAnywhere, Category = "Debug HUD")
	FVector2D Origin = FVector2D(24.f, 24.f);

	/** Multiplies the engine's medium font. */
	UPROPERTY(EditAnywhere, Category = "Debug HUD", meta = (ClampMin = "0.5"))
	float TextScale = 1.5f;
};
