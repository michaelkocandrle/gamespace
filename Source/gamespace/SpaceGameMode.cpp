// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceGameMode.h"

#include "SpaceDebugHUD.h"
#include "SpaceshipPawn.h"

ASpaceGameMode::ASpaceGameMode()
{
	// Referenced directly rather than through a Blueprint lookup: this is the C++ default, and a
	// Blueprint child of this game mode can still override it for a specific level.
	DefaultPawnClass = ASpaceshipPawn::StaticClass();
	HUDClass = ASpaceDebugHUD::StaticClass();
}
