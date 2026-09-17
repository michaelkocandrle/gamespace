// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceUserSettings.h"

#include "AudioDevice.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "HAL/IConsoleManager.h"

USpaceUserSettings::USpaceUserSettings(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
}

USpaceUserSettings* USpaceUserSettings::Get()
{
	return GEngine ? Cast<USpaceUserSettings>(GEngine->GetGameUserSettings()) : nullptr;
}

void USpaceUserSettings::SetToDefaults()
{
	Super::SetToDefaults();
	// Borderless fullscreen: full screen without the slow mode switch, and alt-tab just works.
	FullscreenMode = EWindowMode::WindowedFullscreen;
	LastConfirmedFullscreenMode = EWindowMode::WindowedFullscreen;
	PreferredFullscreenMode = EWindowMode::WindowedFullscreen;
	const FIntPoint Desktop = GetDesktopResolution();
	if (Desktop.X > 0 && Desktop.Y > 0)
	{
		ResolutionSizeX = LastUserConfirmedResolutionSizeX = Desktop.X;
		ResolutionSizeY = LastUserConfirmedResolutionSizeY = Desktop.Y;
	}
	ScalabilityQuality.SetFromSingleQualityLevel(2);

	MasterVolume = 0.8f;
	EffectsVolume = 1.f;
	MusicVolume = 0.7f;
	MouseSensitivity = 1.f;
	bInvertShipPitch = false;
	HudMode = 1;
	bShowFps = false;
}

void USpaceUserSettings::ApplyGameSettings(const UWorld* World) const
{
	if (World)
	{
		if (FAudioDeviceHandle AudioDevice = World->GetAudioDevice())
		{
			AudioDevice->SetTransientPrimaryVolume(FMath::Clamp(MasterVolume, 0.f, 1.f));
		}
	}
	if (IConsoleVariable* Hud = IConsoleManager::Get().FindConsoleVariable(TEXT("space.Hud")))
	{
		// Same priority as the H key and the console, so neither locks the other out.
		Hud->Set(FMath::Clamp(HudMode, 0, 2), ECVF_SetByConsole);
	}
}

float USpaceUserSettings::GetMouseSensitivityScale()
{
	const USpaceUserSettings* Settings = Get();
	return Settings ? FMath::Clamp(Settings->MouseSensitivity, 0.05f, 10.f) : 1.f;
}

bool USpaceUserSettings::IsShipPitchInverted()
{
	const USpaceUserSettings* Settings = Get();
	return Settings && Settings->bInvertShipPitch;
}

float USpaceUserSettings::GetEffectsVolume()
{
	const USpaceUserSettings* Settings = Get();
	return Settings ? FMath::Clamp(Settings->EffectsVolume, 0.f, 1.f) : 1.f;
}

float USpaceUserSettings::GetMusicVolume()
{
	const USpaceUserSettings* Settings = Get();
	return Settings ? FMath::Clamp(Settings->MusicVolume, 0.f, 1.f) : 1.f;
}

bool USpaceUserSettings::ShouldShowFps()
{
	const USpaceUserSettings* Settings = Get();
	return Settings && Settings->bShowFps;
}
