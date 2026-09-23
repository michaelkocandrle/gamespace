// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "SpacePlayerController.generated.h"

class SSpaceMenu;
class SWidget;
class UAudioComponent;
class UInputAction;
class UInputMappingContext;
class USoundBase;
struct FInputActionValue;

/**
 * The player's controller everywhere: on the title screen (ASpaceMenuGameMode) and in the game
 * (ASpaceGameMode). It owns what does not belong to a pawn:
 *
 * - Global keys in its own mapping context, above every pawn's: Escape (or F10, which works in
 *   PIE where Escape stops the session) opens the pause menu, H cycles the HUD and saves the
 *   choice. Pawns no longer bind H, so it works the same in the ship and on foot.
 * - The menus (SSpaceMenu): title screen with a slowly drifting camera and ambient music, pause
 *   menu with the game paused, settings page on both.
 * - Applying the saved settings (volume, HUD mode) when a level starts.
 */
UCLASS()
class GAMESPACE_API ASpacePlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	ASpacePlayerController();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void SetupInputComponent() override;
	virtual void PlayerTick(float DeltaTime) override;

	/** In the title screen level. */
	UFUNCTION(BlueprintPure, Category = "Menu")
	bool IsTitleScreen() const;

	UFUNCTION(BlueprintPure, Category = "Menu")
	bool IsMenuOpen() const { return Menu.IsValid(); }

	/** Pauses the game and shows the pause menu. Nothing on the title screen. */
	UFUNCTION(BlueprintCallable, Category = "Menu")
	void OpenPauseMenu();

	/** Closes the pause menu and unpauses. */
	UFUNCTION(BlueprintCallable, Category = "Menu")
	void ResumeGame();

	// Menu actions.
	void StartGame();
	void GoToMainMenu();
	void QuitGame();
	/** Hover tick (false) or confirm blip (true), scaled by the effects volume. */
	void PlayUiSound(bool bConfirm);
	/** Hear volume sliders while dragging them, before they are applied. */
	void PreviewVolumes(float MasterVolume, float EffectsVolume, float MusicVolume);

	/**
	 * Into the Steadfast interior on foot (spawned at the actor tagged SpaceInteriorSpawn), or back
	 * where the player came from: the ship they were flying, or the spot they were standing on.
	 * I in the game, space.Interior in the console, a button in the pause menu. False when there
	 * is no interior in the level.
	 */
	UFUNCTION(BlueprintCallable, Category = "Interior")
	bool ToggleInterior();

	UFUNCTION(BlueprintPure, Category = "Interior")
	bool IsWalkingInterior() const { return bWalkingInterior; }

	/** Whether this level has an interior to walk. */
	UFUNCTION(BlueprintPure, Category = "Interior")
	bool HasInterior() const;

protected:
	/** Level "Play" opens. */
	UPROPERTY(EditDefaultsOnly, Category = "Menu")
	FName GameLevel = TEXT("/Game/Maps/TestSpace");

	/** Level "Main menu" opens. */
	UPROPERTY(EditDefaultsOnly, Category = "Menu")
	FName TitleLevel = TEXT("/Game/Maps/MainMenu");

private:
	void HandleMenuKey(const FInputActionValue& Value);
	void HandleToggleHud(const FInputActionValue& Value);
	void HandleInteriorKey(const FInputActionValue& Value);
	void ShowMenu(bool bTitleScreen);
	void HideMenu();
	void UpdateTitleCamera(float DeltaTime);

	TSharedPtr<SSpaceMenu> Menu;
	TSharedPtr<SWidget> MenuHost;

	UPROPERTY(Transient)
	TObjectPtr<UInputMappingContext> GlobalContext;
	UPROPERTY(Transient)
	TObjectPtr<UInputAction> MenuAction;
	UPROPERTY(Transient)
	TObjectPtr<UInputAction> HudAction;
	UPROPERTY(Transient)
	TObjectPtr<UInputAction> InteriorAction;

	/** Where ToggleInterior goes back to: the ship that was being flown, or a place on foot. */
	TWeakObjectPtr<APawn> ReturnShip;
	FTransform ReturnTransform;
	bool bWalkingInterior = false;

	UPROPERTY(Transient)
	TObjectPtr<USoundBase> UiHoverSound;
	UPROPERTY(Transient)
	TObjectPtr<USoundBase> UiConfirmSound;
	UPROPERTY(Transient)
	TObjectPtr<USoundBase> MenuMusicSound;
	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> MenuMusic;

	TWeakObjectPtr<AActor> TitleCamera;
	FVector TitleOrbitCenter = FVector::ZeroVector;
	FVector TitleCameraOffset = FVector::ZeroVector;
	double TitleTime = 0.0;
	double LastHoverSoundTime = -1.0;
};
