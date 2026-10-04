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
	 * The game's own settings (everything but video mode and scalability) to their defaults. Written out here, not
	 * copied from the class default object: that one is loaded from the player's GameUserSettings.ini, so it holds
	 * their saved values, not the defaults (the menu's RESET read the player's own values back, 4. 10. 2026).
	 */
	UFUNCTION(BlueprintCallable, Category = "Settings")
	void SetGameDefaults();

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

	/**
	 * Applies what the engine does not apply itself: master volume and the HUD mode, the image settings (console
	 * variables, display gamma), background audio, and the camera and handling settings of the ships and characters
	 * in the world (their flight defaults only when a ship spawns).
	 */
	void ApplyGameSettings(const UWorld* World) const;

	/**
	 * The graphics quality preset the menu shows, 0 low .. 4 cinematic: the lowest scalability group,
	 * ignoring the resolution scale. The engine's GetOverallScalabilityLevel() also compares the
	 * resolution scale with the preset's default and returns -1 ("custom") as soon as the slider is
	 * not at that default - the menu then showed High every time and applying saved High again.
	 */
	UFUNCTION(BlueprintPure, Category = "Settings")
	int32 GetGraphicsQualityLevel() const;

	/**
	 * The menu's quality preset, and the two rules the game keeps on top of it (see the .cpp): the render
	 * scale stays at 100 %, and global illumination is capped, because it is the only scalability group
	 * that costs anything here.
	 */
	virtual void SetOverallScalabilityLevel(int32 Value) override;

private:
	/** The render scale and the global illumination cap, applied on top of whatever preset was set. */
	void ApplyQualityRules();

public:

	// Neutral when there are no settings.
	static float GetMouseSensitivityScale();
	static bool IsShipPitchInverted();
	static float GetEffectsVolume();
	static float GetMusicVolume();
	static bool ShouldShowFps();
	static bool IsFreeLookPitchInverted();
	static bool IsWalkPitchInverted();
	static bool ShouldShowFlightPathMarker();
	static float GetCameraShakeScale();
	/** The player's field of view for the cockpit and on foot, degrees; 0 without settings (keep your own). */
	static float GetFieldOfView();

	// --- Settings after SC 4.10's OPTIONS MENU (4. 10. 2026), only where the game has the system behind them ---------

	/** Game: a new ship starts decoupled (V switches in flight). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Settings")
	bool bStartDecoupled = false;

	/** Game: a new ship starts with G-Safe on (K). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Settings")
	bool bDefaultGSafe = true;

	/** Game: a new ship starts with ComStab on (L). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Settings")
	bool bDefaultComStab = true;

	/** Game: steer with the virtual joystick (SC's VJoy); off, the mouse is a spring-centred stick. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Settings")
	bool bVirtualJoystick = true;

	/** Game: the virtual joystick's dead zone, fraction of its radius. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Settings")
	float VJoyDeadzone = 0.06f;

	/** Game: the HUD's flight path marker (SC's Pilot Velocity Indicator). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Settings")
	bool bShowFlightPathMarker = true;

	/** Game: camera shake (heat, boost, afterburner, quantum), x. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Settings")
	float CameraShakeScale = 1.f;

	/** Graphics: field of view in the cockpit and on foot, degrees. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Settings")
	float FieldOfView = 88.f;

	/** Graphics: motion blur. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Settings")
	bool bMotionBlur = true;

	/** Graphics: film grain. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Settings")
	bool bFilmGrain = true;

	/** Graphics: chromatic aberration (the lens's colour fringe). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Settings")
	bool bChromaticAberration = true;

	/**
	 * Graphics: sharpening, 0..1 (r.Tonemapper.Sharpen 0..2). 0.3 is the 0.6 the game always had: TSR resolves a soft
	 * image, and it puts the edge back on the cockpit's type and the hull's rivets without ringing (20. 9. 2026,
	 * Tools/Shots/look_sharp.json).
	 */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Settings")
	float Sharpen = DefaultSharpen;

	/** Graphics: gamma, 0..100, 50 = the display's 2.2. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Settings")
	float Gamma = 50.f;

	/** Audio: keep playing sound while the game is in the background. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Settings")
	bool bAudioInBackground = false;

	/** Game: hint cards the first time something matters (SC's Show Hints). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Settings")
	bool bShowHints = true;

	/** Controls: free look (hold Alt / C) pitch inverted. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Settings")
	bool bInvertFreeLookPitch = false;

	/** Controls: on foot, looking pitch inverted. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Settings")
	bool bInvertWalkPitch = false;

	/** Display gamma for a Gamma setting of 0..100 (50 = 2.2, 0 = 1.8, 100 = 2.6). */
	/** Tests: ApplyGameSettings without a world (console variables, gamma, background audio). */
	UFUNCTION(BlueprintCallable, Category = "Settings")
	void DebugApplyGameSettings() { ApplyGameSettings(nullptr); }

	static float DisplayGammaFor(float GammaSetting) { return 2.2f + (FMath::Clamp(GammaSetting, 0.f, 100.f) - 50.f) / 50.f * 0.4f; }

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

	/**
	 * Set while MigrateSettings runs. Applying the settings can reload them - UGameUserSettings::ValidateSettings
	 * calls LoadSettings while the engine's own Version is missing, as with no GameUserSettings.ini yet - and
	 * LoadSettings migrates, so without it a fresh install recursed until the stack overflowed (30. 9. 2026).
	 */
	bool bMigrating = false;

	/** The preset the player picked, 0 low .. 4 cinematic. The scalability groups follow from it. */
	UPROPERTY(Config, BlueprintReadOnly, Category = "Settings")
	int32 GraphicsQualityLevel = DefaultQualityLevel;

	/**
	 * How far global illumination is allowed to go. Measured on 20. 9. 2026 with Tools/Shots/look_groups.json:
	 * of the eight groups it is the only one that costs anything - at cinematic the frame rate halves (85 ->
	 * 46 FPS) - and in these scenes, lit by a sun and a sky light, nothing in the pictures changed. Worth
	 * revisiting when there are dark interiors or night sides, where indirect light does the work.
	 */
	static constexpr int32 MaxGlobalIlluminationQuality = 2;

	/** The newest settings version this build knows. */
	static constexpr int32 CurrentSettingsVersion = 5;
	/** New and migrated settings: epic, drawn at 75 % and upscaled by TSR (see MigrateSettings). */
	static constexpr int32 DefaultQualityLevel = 3;
	static constexpr float DefaultRenderScale = 75.f;
	/** Sharpening the game always had (r.Tonemapper.Sharpen 0.6). */
	static constexpr float DefaultSharpen = 0.3f;

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
