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

	/**
	 * Settings saved by an older build are brought forward here. Version 1: the render scale. The engine
	 * had left it at 50 % on this machine, so the game drew at half resolution and upscaled - every edge,
	 * the cockpit displays and the HUD were soft (20. 9. 2026, the author's "blurry up close").
	 */
	virtual void LoadSettings(bool bForceReload = false) override;

	/** Brings a saved settings file forward (see LoadSettings); called again when the game applies settings,
	 *  because the engine re-applies the saved scalability state after LoadSettings. */
	UFUNCTION(BlueprintCallable, Category = "Settings")
	void MigrateSettings();

	/** Applies what the engine does not apply itself: master volume and the HUD mode. */
	void ApplyGameSettings(const UWorld* World) const;

	/**
	 * The graphics quality preset the menu shows, 0 low .. 4 cinematic: the lowest scalability group,
	 * ignoring the resolution scale. The engine's GetOverallScalabilityLevel() also compares the
	 * resolution scale with the preset's default and returns -1 ("custom") as soon as the slider is
	 * not at that default - the menu then showed High every time and applying saved High again.
	 */
	UFUNCTION(BlueprintPure, Category = "Settings")
	int32 GetGraphicsQualityLevel() const;

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

	/** space.Hud at start: 0 hidden, 1 flight HUD only, 2 plus compact text, 3 plus full text. H changes and saves it. */
	UPROPERTY(Config, BlueprintReadOnly, Category = "Settings")
	int32 HudMode = 1;

	/** Frame rate in the top right corner. */
	UPROPERTY(Config, BlueprintReadOnly, Category = "Settings")
	bool bShowFps = false;

	/** What the saved settings were last brought forward to (see LoadSettings). */
	UPROPERTY(Config)
	int32 SettingsVersion = 0;

	/** The newest settings version this build knows. */
	static constexpr int32 CurrentSettingsVersion = 2;

	/** Tests: the render scale in per cent (sg.ResolutionQuality) and a way to set it without applying. */
	UFUNCTION(BlueprintCallable, Category = "Settings|Tests")
	float DebugGetRenderScale() const { return ScalabilityQuality.ResolutionQuality; }

	UFUNCTION(BlueprintCallable, Category = "Settings|Tests")
	void DebugSetRenderScale(float Percent) { ScalabilityQuality.ResolutionQuality = Percent; }

	/** Tests: the saved settings version (Config only, so Python cannot read it directly). */
	UFUNCTION(BlueprintCallable, Category = "Settings|Tests")
	int32 DebugGetSettingsVersion() const { return SettingsVersion; }

	UFUNCTION(BlueprintCallable, Category = "Settings|Tests")
	void DebugSetSettingsVersion(int32 InSettingsVersion) { SettingsVersion = InSettingsVersion; }
};
