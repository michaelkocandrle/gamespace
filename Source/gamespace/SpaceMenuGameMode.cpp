// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceMenuGameMode.h"

#include "SpacePlayerController.h"

ASpaceMenuGameMode::ASpaceMenuGameMode()
{
	DefaultPawnClass = nullptr;
	PlayerControllerClass = ASpacePlayerController::StaticClass();
}

void ASpaceMenuGameMode::HandleStartingNewPlayer_Implementation(APlayerController* /*NewPlayer*/)
{
}
