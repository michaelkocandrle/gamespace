// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceUserSettings.h"

#include "Scalability.h"

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
	// Full render resolution: the quality level's own scale is below 100 %, and upscaling softens
	// everything - the ship's edges, the cockpit displays and the HUD. Lower it in the settings
	// (Škálování rozlišení) if a machine needs the frames.
	ScalabilityQuality.ResolutionQuality = 100.f;

	MasterVolume = 0.8f;
	EffectsVolume = 1.f;
	MusicVolume = 0.7f;
	MouseSensitivity = 1.f;
	bInvertShipPitch = false;
	HudMode = 1;
	bShowFps = false;
}

void USpaceUserSettings::LoadSettings(bool bForceReload)
{
	Super::LoadSettings(bForceReload);
	MigrateSettings();
}

void USpaceUserSettings::MigrateSettings()
{
	if (SettingsVersion >= CurrentSettingsVersion)
	{
		return;
	}
	// Version 2: the render scale. The engine had left it at 50 % here, so the whole game was drawn at half
	// resolution and upscaled - ships, cockpit displays and the HUD stayed soft whatever else changed
	// (20. 9. 2026). Scalability::SetQualityLevels is what puts it into the sg. console variables, which is
	// what both the renderer and SaveSettings read; setting the struct alone did nothing.
	if (ScalabilityQuality.ResolutionQuality < 100.f)
	{
		UE_LOG(LogTemp, Display, TEXT("Settings: render scale %.0f %% -> 100 %% (an older build saved it)"),
			ScalabilityQuality.ResolutionQuality);
		ScalabilityQuality.ResolutionQuality = 100.f;
		Scalability::SetQualityLevels(ScalabilityQuality);
		ApplyNonResolutionSettings();
	}
	SettingsVersion = CurrentSettingsVersion;
	SaveSettings();
}

void USpaceUserSettings::ApplyGameSettings(const UWorld* World) const
{
	const_cast<USpaceUserSettings*>(this)->MigrateSettings();
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
		Hud->Set(FMath::Clamp(HudMode, 0, 3), ECVF_SetByConsole);
	}
}

int32 USpaceUserSettings::GetGraphicsQualityLevel() const
{
	// Groups only: GetMinQualityLevel leaves ResolutionQuality out. When the groups disagree (edited
	// by hand) the lowest one is the safe thing to show.
	return FMath::Clamp(ScalabilityQuality.GetMinQualityLevel(), 0, 4);
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
