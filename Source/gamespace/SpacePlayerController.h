// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "SpaceInteractionOverlay.h"
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

	// --- Interaction (SC, step 1 after the author's captures, 4. 10. 2026) ---------------------------------------------
	// F is read here: a tap does the default action of the target shown by its object, holding it turns on interact
	// mode (a cursor over the game, hotspots to click; the pawns ignore the mouse while it is on).

	/** What the interaction overlay draws this frame. */
	const FSpaceInteractionView& GetInteractionView() const { return InteractionView; }

	UFUNCTION(BlueprintPure, Category = "Interaction")
	bool IsInteractModeOn() const { return bInteractMode; }

	/** Whether the player controlling Pawn is in interact mode (the pawns' mouse handlers ask). */
	static bool IsInteractModeFor(const APawn* Pawn);

	/** Tests and screenshots: interact mode on or off without holding F. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	void DebugSetInteractMode(bool bOn);

	/** Screenshots: show this hotspot as hovered in interact mode (the cursor cannot be placed); -1 follows the mouse. */
	void DebugForceHover(int32 Index) { ForcedHover = Index; }

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

	/**
	 * The same for any walkable place: onto the actor tagged SpawnTag, or back when already walking there. Walking
	 * one interior and asked for another, the player is taken across and the way back stays the original ship.
	 * The interior kit showroom in TestSpace is KitShowroomSpawn, its annex KitShowroomAnnexSpawn, the stair bay
	 * KitShowroomStairsSpawn: U in the game walks showroom -> annex -> stair bay -> back, space.Showroom [annex|stairs].
	 */
	UFUNCTION(BlueprintCallable, Category = "Interior")
	bool ToggleInteriorAt(FName SpawnTag);

	/** The interior lighting state (MegaLights on, Lumen reflections off) or the ship's; walking in and out sets it, and
	 * space.InteriorLighting 0|1 for shots taken with the free camera. */
	static void ApplyInteriorLighting(bool bInterior);

	/** Whether the interior lighting state is on now (walking an interior, the prewarm or space.InteriorLighting 1):
	 * ships read it to take their interior meshes out of the sun's shadows (ASpaceshipPawn::UpdateViewCollection). */
	static bool IsInteriorLightingOn();

	/** The interior lighting (MegaLights, no Lumen reflections) for walking a ship's own interior (the pilot up
	 * from the seat or in up the ramp, APlayerCharacter::BoardInterior) and off again when back in the seat or out. */
	static void SetShipInteriorLighting(bool bOn);

	UFUNCTION(BlueprintPure, Category = "Interior")
	bool IsWalkingInterior() const { return bWalkingInterior; }

	/**
	 * Screenshots (console space.Menu): shows a menu page over whatever is running, without pausing, so the shot runner
	 * keeps ticking. Page 0 title, 1 pause, 2 settings, 3 loading; Tab the settings tab; a negative page hides it.
	 */
	void DebugShowMenu(int32 Page, int32 Tab, bool bScrollToEnd = false);

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
	void HandleShowroomKey(const FInputActionValue& Value);
	void ShowMenu(bool bTitleScreen);
	void TickInteraction();
	void SetInteractMode(bool bOn);
	/** Hint cards the first time something matters, toasts on events (USpaceNotifications). */
	void TickNotifications();
	void HideMenu();
	void UpdateTitleCamera(float DeltaTime);

	TSharedPtr<SSpaceMenu> Menu;
	TSharedPtr<class SSpaceInteractionOverlay> InteractionOverlay;
	TSharedPtr<SWidget> InteractionOverlayHost;
	FSpaceInteractionView InteractionView;
	bool bInteractMode = false;
	int32 ForcedHover = INDEX_NONE;
	bool bInteractKeyWasDown = false;
	bool bInteractHoldUsed = false;
	double InteractKeyDownSeconds = 0.0;
	/** For the event toasts: what the pawn was last frame. */
	TWeakObjectPtr<class ASpaceshipPawn> LastInteriorShip;
	bool bLastQuantumTraveling = false;
	TSharedPtr<SWidget> MenuHost;

	UPROPERTY(Transient)
	TObjectPtr<UInputMappingContext> GlobalContext;
	UPROPERTY(Transient)
	TObjectPtr<UInputAction> MenuAction;
	UPROPERTY(Transient)
	TObjectPtr<UInputAction> HudAction;
	UPROPERTY(Transient)
	TObjectPtr<UInputAction> InteriorAction;
	UPROPERTY(Transient)
	TObjectPtr<UInputAction> ShowroomAction;

	/** Where ToggleInterior goes back to: the ship that was being flown, or a place on foot. */
	TWeakObjectPtr<APawn> ReturnShip;
	FTransform ReturnTransform;
	bool bWalkingInterior = false;
	/** The spawn tag of the place being walked (SpaceInteriorSpawn, KitShowroomSpawn). */
	FName WalkingSpawnTag;
	/** The longest frame in the first frames after walking in (MegaLights' first-use hitch), logged once. */
	int32 EntryFramesLeft = 0;
	int32 EntryFramesSeen = 0;
	float EntryMaxFrameMs = 0.f;
	/** MegaLights on for the first frames of the level, so its first use is not the moment the player walks in. */
	int32 PrewarmFramesLeft = 0;
	void StartPrewarm();
	void WatchEntry();
	void TickEntryWatch();

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
