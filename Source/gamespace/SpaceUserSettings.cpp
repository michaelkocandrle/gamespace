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
	GraphicsQualityLevel = 4;
	ScalabilityQuality.SetFromSingleQualityLevel(GraphicsQualityLevel);
	ApplyQualityRules();

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
	// Version 3: the quality preset. Everything ran at Medium, which is where the engine's anti-aliasing,
	// texture and post process quality sit - the hull up close came out smeared with stepped edges, and the
	// type on the cockpit displays was soft (20. 9. 2026, Tools/Shots/look_sharp.json). Of the eight groups
	// only global illumination costs frames, so the rest go to cinematic and it stays where it was.
	const bool bOldPreset = SettingsVersion < 3;
	if (ScalabilityQuality.ResolutionQuality < 100.f || bOldPreset)
	{
		if (bOldPreset)
		{
			GraphicsQualityLevel = 4;
			ScalabilityQuality.SetFromSingleQualityLevel(GraphicsQualityLevel);
			UE_LOG(LogTemp, Display, TEXT("Settings: graphics preset -> cinematic (an older build saved medium)"));
		}
		else
		{
			UE_LOG(LogTemp, Display, TEXT("Settings: render scale %.0f %% -> 100 %% (an older build saved it)"),
				ScalabilityQuality.ResolutionQuality);
		}
		ApplyQualityRules();
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
	// What the player picked, not what the groups say: the groups never all match the preset, because
	// global illumination is capped and the render scale is held at 100 % (see ApplyQualityRules).
	return FMath::Clamp(GraphicsQualityLevel, 0, 4);
}

void USpaceUserSettings::SetOverallScalabilityLevel(int32 Value)
{
	GraphicsQualityLevel = FMath::Clamp(Value, 0, 4);
	Super::SetOverallScalabilityLevel(GraphicsQualityLevel);
	ApplyQualityRules();
}

void USpaceUserSettings::ApplyQualityRules()
{
	// Full render resolution: the preset's own scale is below 100 % from High down, and upscaling softens
	// everything - the ship's edges, the cockpit displays and the HUD. Lower it in the settings
	// (Škálování rozlišení) if a machine needs the frames.
	ScalabilityQuality.ResolutionQuality = 100.f;
	// Global illumination is the one group worth paying attention to; see MaxGlobalIlluminationQuality.
	ScalabilityQuality.GlobalIlluminationQuality =
		FMath::Min(ScalabilityQuality.GlobalIlluminationQuality, MaxGlobalIlluminationQuality);
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
