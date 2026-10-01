// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ShipInputComponent.generated.h"

class UInputComponent;
class UInputMappingContext;
struct FInputActionValue;
enum class ESpaceshipAxis : uint8;

/**
 * The pilot's controls, split out of ASpaceshipPawn (Docs/Reviews/2026-09-30_spaceshippawn_split_plan.md): finding
 * or building the Enhanced Input assets, binding them, the mapping contexts, and the key handlers, which set the
 * ship's input state and call its functions. The input actions stay on the pawn (Blueprint children may assign
 * them), and like the presentation this reads the pawn directly (a friend of ASpaceshipPawn). The pawn's
 * SetupPlayerInputComponent and UnPossessed call BindInput and RemoveMappingContexts.
 */
UCLASS(ClassGroup = (Spaceship), meta = (BlueprintSpawnableComponent = "false"))
class GAMESPACE_API UShipInputComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UShipInputComponent();

	/** Resolves the input assets and binds the handlers on the player's input component; adds the contexts. */
	void BindInput(UInputComponent* PlayerInputComponent);

	/** Takes this ship's contexts off the player again (unpossessed). */
	void RemoveMappingContexts();

private:
	/** Fills in any unassigned input asset: first from /Game/Input, then procedurally. */
	void ResolveInputAssets();
	void BuildProceduralInputAssets();

	void HandleAxisTriggered(const FInputActionValue& Value, ESpaceshipAxis Axis);
	void HandleAxisCompleted(const FInputActionValue& Value, ESpaceshipAxis Axis);
	void HandleLook(const FInputActionValue& Value);
	void HandleMouseLook(const FInputActionValue& Value);
	void HandleToggleCamera(const FInputActionValue& Value);
	void HandleBoost(const FInputActionValue& Value);
	void HandleInteract(const FInputActionValue& Value);
	void HandleFlightAssist(const FInputActionValue& Value);
	void HandleQuantumEngageStarted(const FInputActionValue& Value);
	void HandleQuantumEngageCompleted(const FInputActionValue& Value);
	void HandleAllStop(const FInputActionValue& Value);
	void HandleAllStopCompleted(const FInputActionValue& Value);
	void HandleMasterMode(const FInputActionValue& Value);
	void HandleSpeedLimiter(const FInputActionValue& Value);
	void HandleGSafe(const FInputActionValue& Value);
	void HandleAfterburner(const FInputActionValue& Value);
	void HandleAfterburnerCompleted(const FInputActionValue& Value);
	void HandleComStab(const FInputActionValue& Value);
	void HandleLandingGear(const FInputActionValue& Value);
	void HandleMfdLeft(const FInputActionValue& Value);
	void HandleMfdRight(const FInputActionValue& Value);
	void HandlePrecision(const FInputActionValue& Value);
	void HandleCameraZoom(const FInputActionValue& Value);
	void HandleFreeLookStarted(const FInputActionValue& Value);
	void HandleFreeLookCompleted(const FInputActionValue& Value);
	void HandleDashboardFocusStarted(const FInputActionValue& Value);
	void HandleDashboardFocusCompleted(const FInputActionValue& Value);
	void HandleBoostCompleted(const FInputActionValue& Value);
	void HandleVtol(const FInputActionValue& Value);

	/** Pages an MFD (0 left, 1 right): forward, or back with Alt held. */
	void CycleMfdPage(int32 Display);
	/** Alt held on the controlling player's keyboard: the wheel zooms instead of setting the limiter. */
	bool IsAltHeld() const;

	/** Maps keys the authored flight context lacks (F, V, J, X, B, K, L, N, P, right mouse button, wheel). */
	UPROPERTY(Transient)
	TObjectPtr<UInputMappingContext> InteractMappingContext;
};
