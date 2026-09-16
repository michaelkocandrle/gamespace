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
 *
 * Three modes, cycled with H (IA_ToggleHud) or set with the console variable space.Hud:
 * 0 off, 1 compact (the few lines needed while flying or walking, the default), 2 full debug.
 * Text size follows the viewport height, so it reads the same in a small editor viewport and
 * in fullscreen.
 */
UCLASS()
class GAMESPACE_API ASpaceDebugHUD : public AHUD
{
	GENERATED_BODY()

public:
	virtual void DrawHUD() override;

	/** Off -> compact -> full -> off. Bound to H on the ship and the character. */
	static void CycleDisplayMode();

protected:
	/** Top-left corner of the readout, as a fraction of the viewport size. */
	UPROPERTY(EditAnywhere, Category = "Debug HUD")
	FVector2D Origin = FVector2D(0.012f, 0.018f);

	/** Font scale at a 1080-pixel-high viewport; scaled with the actual height. */
	UPROPERTY(EditAnywhere, Category = "Debug HUD", meta = (ClampMin = "0.3"))
	float TextScale = 1.0f;
};
