// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "SpaceDebugHUD.generated.h"

/**
 * Plain-text flight readout drawn straight onto the canvas: flight regime, landing, drive, camera,
 * distance and ETA to the nearest ACelestialBody (and in full mode speed, IFCS and afterburner
 * numbers). Also creates the UMG flight HUD (USpaceFlightHud, SC-1c) for the local player.
 *
 * The text part is a stopgap for tuning the flight model, deliberately not UMG; it goes in SC-3.
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
	virtual void BeginPlay() override;

	/** Off -> compact -> full -> off. Bound to H by ASpacePlayerController. */
	static void CycleDisplayMode();

protected:
	/** Top-left corner of the readout, as a fraction of the viewport size. */
	UPROPERTY(EditAnywhere, Category = "Debug HUD")
	FVector2D Origin = FVector2D(0.012f, 0.018f);

	/** Font scale at a 1080-pixel-high viewport; scaled with the actual height. */
	UPROPERTY(EditAnywhere, Category = "Debug HUD", meta = (ClampMin = "0.3"))
	float TextScale = 1.0f;

private:
	/** The SC-1c flight HUD (speed gauge, lamps, G meter, boost and afterburner, virtual joystick). */
	UPROPERTY(Transient)
	TObjectPtr<class USpaceFlightHud> FlightHud;

	/** For the FPS counter (settings: show FPS). */
	float SmoothedFrameSeconds = 0.f;
};
