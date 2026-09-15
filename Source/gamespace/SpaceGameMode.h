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
 */
UCLASS()
class GAMESPACE_API ASpaceGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ASpaceGameMode();
};
