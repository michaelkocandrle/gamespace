// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameUserSettings.h"
#include "SpaceUserSettings.generated.h"

/**
 * The player's settings: the engine's graphics settings (window mode, resolution, quality, VSync,
 * frame limit) plus the game's own - volumes, mouse sensitivity, pitch inversion, HUD mode and
 * the FPS counter. Saved to GameUserSettings.ini next to the engine's values.
 *
 * Registered as the engine's settings class in DefaultEngine.ini (GameUserSettingsClassName), so
 * GEngine->GetGameUserSettings() is one of these. The settings menu edits it; gameplay code reads
 * it through the static helpers, which fall back to neutral values when there is none (editor
 * tests, commandlets).
 */
UCLASS(config = GameUserSettings, configdonotcheckdefaults)
class GAMESPACE_API USpaceUserSettings : public UGameUserSettings
{
	GENERATED_BODY()

public:
	USpaceUserSettings(const FObjectInitializer& ObjectInitializer);

	/** The engine's settings object as this class, or null. */
	static USpaceUserSettings* Get();

	/** First start: borderless fullscreen at the desktop resolution, high quality, sensible volumes. */
	virtual void SetToDefaults() override;

	/** Applies what the engine does not apply itself: master volume and the HUD mode. */
	void ApplyGameSettings(const UWorld* World) const;

	// Neutral when there are no settings.
	static float GetMouseSensitivityScale();
	static bool IsShipPitchInverted();
	static float GetEffectsVolume();
	static float GetMusicVolume();
	static bool ShouldShowFps();

	/** Everything the game plays, 0..1 (applied to the audio device). */
	UPROPERTY(Config, BlueprintReadOnly, Category = "Settings")
	float MasterVolume = 0.8f;

	/** Engines, boost, cruise, interface. */
	UPROPERTY(Config, BlueprintReadOnly, Category = "Settings")
	float EffectsVolume = 1.f;

	/** Menu ambience. */
	UPROPERTY(Config, BlueprintReadOnly, Category = "Settings")
	float MusicVolume = 0.7f;

	/** Multiplies every mouse sensitivity (ship steering, free look, on foot). */
	UPROPERTY(Config, BlueprintReadOnly, Category = "Settings")
	float MouseSensitivity = 1.f;

	/** Mouse up pitches the ship's nose down, like a flight stick. */
	UPROPERTY(Config, BlueprintReadOnly, Category = "Settings")
	bool bInvertShipPitch = false;

	/** space.Hud at start: 0 hidden, 1 compact, 2 full. H changes and saves it. */
	UPROPERTY(Config, BlueprintReadOnly, Category = "Settings")
	int32 HudMode = 1;

	/** Frame rate in the top right corner. */
	UPROPERTY(Config, BlueprintReadOnly, Category = "Settings")
	bool bShowFps = false;
};
