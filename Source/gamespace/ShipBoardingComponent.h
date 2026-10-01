// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ShipBoardingComponent.generated.h"

class ASpaceGravityVolume;

/**
 * Getting out of the ship, walking through it and boarding it again (author 29. 9. 2026: "a ship you can walk
 * through"), split out of ASpaceshipPawn (Docs/Reviews/2026-09-30_spaceshippawn_split_plan.md): exit spots clear of
 * the hull, the walk sockets, the walked interior's collision and its gravity volume.
 *
 * It works on the hull's parts and the pilot class, so like the presentation it reads the pawn directly (a friend of
 * ASpaceshipPawn); the function bodies are the pawn's as they were. The pawn keeps every one of these functions as a
 * forwarder of the same name, since the pilot, the HUD, the interior and the tests call them there. State here: who
 * walks inside and the gravity volume riding along.
 */
UCLASS(ClassGroup = (Spaceship), meta = (BlueprintSpawnableComponent = "false"))
class GAMESPACE_API UShipBoardingComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UShipBoardingComponent();

	/** Documented on the pawn's functions of the same names. */
	bool CanExit() const;
	double GetDistanceToHull(const FVector& Location) const;
	static FVector ComputeSideExitLocation(const FVector& ShipLocation, const FRotator& ShipRotation, const FVector& HullExtent, float CapsuleRadius, float ClearanceCm);
	TArray<FBox> GetHullCollisionBoxes() const;
	double GetHullClearance(const FVector& Location, float CapsuleRadius, float CapsuleHalfHeight) const;
	TArray<FVector> GetExitCandidates() const;
	FTransform ComputeExitTransform() const;
	APawn* ExitShip();
	void OnBoarded();
	bool HasWalkInterior() const;
	bool CanLeaveSeat() const;
	FTransform GetWalkSocketTransform(FName Socket) const;
	bool IsNearSeat(const FVector& Location) const;
	bool IsNearRamp(const FVector& Location) const;
	void SetInteriorWalk(bool bWalking);
	APawn* LeaveSeat();

	bool IsInteriorWalked() const { return bInteriorWalked; }

private:
	FVector PushClearOfHull(const FVector& Start, const FVector& Direction, float CapsuleRadius, float CapsuleHalfHeight) const;
	bool IsExitSpotFree(const FVector& Location, const FVector& Up, float CapsuleRadius, float CapsuleHalfHeight) const;

	/** Someone walks inside (SetInteriorWalk). */
	bool bInteriorWalked = false;
	/** The gravity volume riding along while the interior is walked. */
	UPROPERTY(Transient)
	TObjectPtr<ASpaceGravityVolume> WalkGravity;
};
