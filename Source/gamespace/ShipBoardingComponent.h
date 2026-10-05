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

	// --- Sliding doors (author 5. 10. 2026: SC's doors open; hs_interior.build_door) ------------------------------------

	/** The doorway within ReachCm of a location (its centre socket Control_door<n>), or INDEX_NONE. */
	int32 FindDoorNear(const FVector& Location, float ReachCm, const FVector& Facing = FVector::ZeroVector) const;
	int32 GetDoorCount() const { return DoorOpen.Num(); }
	bool IsDoorOpen(int32 Door) const { return DoorTarget.IsValidIndex(Door) && DoorTarget[Door] > 0.5f; }
	/** 0 closed .. 1 open (tests, shots). */
	float GetDoorOpenAlpha(int32 Door) const { return DoorOpen.IsValidIndex(Door) ? DoorOpen[Door] : 0.f; }
	FVector GetDoorLocation(int32 Door) const;
	/** SC's prompt point: on the shut leaf, near its closing edge (the doorway's centre for a two-leaf door). */
	FVector GetDoorPromptLocation(int32 Door) const;
	void SetDoorOpen(int32 Door, bool bOpen);
	/** Moves the leaves (DoorSeconds), closes an open door after DoorAutoCloseSeconds with nobody in it. */
	void TickDoors(float DeltaSeconds);

private:
	/** The door leaves (components Door<n><A|B>), found on the first tick: open = as imported, closed = moved so their
	 * centre sits on the socket Control_door<n>_<a|b>. */
	void FindDoors();
	struct FDoorLeaf
	{
		TWeakObjectPtr<class UStaticMeshComponent> Mesh;
		int32 Door = 0;
		FVector OpenRel = FVector::ZeroVector;
		FVector ClosedRel = FVector::ZeroVector;
	};
	TArray<FDoorLeaf> DoorLeaves;
	TArray<float> DoorOpen;
	TArray<float> DoorTarget;
	TArray<double> DoorOpenedAt;
	/** Per door, in the ship's frame: the prompt point, or zero = the doorway's centre. */
	TArray<FVector> DoorPrompt;
	bool bDoorsFound = false;
	void ApplyDoorCollision();

	FVector PushClearOfHull(const FVector& Start, const FVector& Direction, float CapsuleRadius, float CapsuleHalfHeight) const;
	bool IsExitSpotFree(const FVector& Location, const FVector& Up, float CapsuleRadius, float CapsuleHalfHeight) const;

	/** Someone walks inside (SetInteriorWalk). */
	bool bInteriorWalked = false;
	/** The gravity volume riding along while the interior is walked. */
	UPROPERTY(Transient)
	TObjectPtr<ASpaceGravityVolume> WalkGravity;
};
