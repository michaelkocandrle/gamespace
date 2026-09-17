// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "SpaceMenuGameMode.generated.h"

/**
 * Game mode of the title screen level (/Game/Maps/MainMenu, built by
 * Tools/Assets/build_main_menu.py). No pawn and no HUD: ASpacePlayerController shows the menu
 * and flies the level's MenuCamera.
 */
UCLASS()
class GAMESPACE_API ASpaceMenuGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ASpaceMenuGameMode();

protected:
	/** Nothing to spawn: the player only looks at the scene. */
	virtual void HandleStartingNewPlayer_Implementation(APlayerController* NewPlayer) override;
};
