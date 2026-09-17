// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "SpaceGameMode.generated.h"

/**
 * Default game mode for free flight. Spawns the player as an ASpaceshipPawn.
 *
 * Set as the project-wide default in Config/DefaultEngine.ini, so any level without a
 * World Settings override gets a flyable ship without further wiring.
 *
 * Also holds the world origin rebasing settings read by USpaceOriginRebasingSubsystem. They
 * live here rather than in Project Settings because a UDeveloperSettings class needs a
 * Build.cs change. During PIE, select SpaceGameMode in the Outliner to edit them live.
 */
UCLASS(Config = Game)
class GAMESPACE_API ASpaceGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ASpaceGameMode();

	/** Shift the world origin to the player once they are RebaseDistanceKm away from it. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Space|Origin Rebasing")
	bool bEnableOriginRebasing = true;

	/**
	 * Distance from the current world origin, in km, that triggers a rebase.
	 *
	 * Each rebase costs a frame: every actor moves, and because Chaos cannot shift its physics
	 * scene as a whole, every physics body is teleported individually. Positions are double
	 * precision anyway, so there is no reason to rebase often. 40 km: cruise drive at its 6 km/s
	 * top speed rebases every ~7 s instead of every 1.7 s, and single-precision maths stays within
	 * ~0.5 cm there.
	 */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Space|Origin Rebasing", meta = (ClampMin = "1.0", ClampMax = "20000.0", Units = "km", EditCondition = "bEnableOriginRebasing"))
	float RebaseDistanceKm = 40.f;

	/** Write a LogSpaceOrigin line for every rebase: shift, new origin and how long it took. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Space|Origin Rebasing")
	bool bLogRebases = true;
};
