// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SpaceOriginRebasingSubsystem.generated.h"

class APawn;

/**
 * Keeps the local player near the world origin by shifting the origin, using the engine's own
 * UWorld::RequestNewWorldOrigin. The request is applied at the start of the next world tick,
 * outside actor ticking.
 *
 * Positions are double precision throughout (Large World Coordinates are always on in UE 5.1+),
 * so this is not needed for CPU-side precision. It keeps coordinates small for what is still
 * single precision: mesh vertices in component space, GPU particles, material world-position
 * maths, and any float code of our own.
 *
 * Limits:
 * - UWorld::OriginLocation is an FIntVector in cm, so the origin itself can only be placed
 *   within +/-21,474 km of absolute zero. Beyond that, rebasing stops (and says so once) while
 *   the world keeps working in plain LWC coordinates.
 * - Game and PIE worlds only; editor worlds never rebase.
 * - Local only. Not network-aware; would need a design of its own for multiplayer.
 *
 * Settings (enable, distance, logging) live on ASpaceGameMode.
 *
 * Console commands for testing: space.TeleportForwardKm, space.TeleportAbsoluteKm,
 * space.RebaseNow, space.PrintOrigin.
 */
UCLASS()
class GAMESPACE_API USpaceOriginRebasingSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

	/** Current world origin, in absolute cm. Actor locations are relative to this. */
	FIntVector GetOriginLocation() const;

	/** World-relative location (what GetActorLocation returns) to absolute. */
	FVector ToAbsolute(const FVector& WorldLocation) const;

	/** Absolute location to world-relative. */
	FVector ToWorld(const FVector& AbsoluteLocation) const;

	/** Requests an origin at the local player's pawn now, regardless of distance. */
	bool RebaseNow();

	bool IsEnabled() const;
	double GetRebaseDistanceCm() const;
	int32 GetRebaseCount() const { return RebaseCount; }
	double GetSecondsSinceLastRebase() const;
	double GetLastRebaseMilliseconds() const { return LastRebaseMilliseconds; }
	FVector GetLastShiftCm() const { return LastShiftCm; }
	bool IsOutOfRebaseRange() const { return bOutOfRange; }

protected:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;

private:
	APawn* GetLocalPlayerPawn() const;
	bool RequestOriginAt(const FVector& WorldLocation);

	void OnPreWorldOriginOffset(UWorld* InWorld, FIntVector PreviousOrigin, FIntVector NewOrigin);
	void OnPostWorldOriginOffset(UWorld* InWorld, FIntVector PreviousOrigin, FIntVector NewOrigin);

	FDelegateHandle PreOffsetHandle;
	FDelegateHandle PostOffsetHandle;

	bool bRequestPending = false;
	bool bOutOfRange = false;
	int32 RebaseCount = 0;
	double OffsetStartSeconds = 0.0;
	double LastRebaseMilliseconds = 0.0;
	double LastRebaseRealTime = -1.0;
	FVector LastShiftCm = FVector::ZeroVector;
};
