// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpacePlayerController.h"

#include "AudioDevice.h"
#include "Camera/CameraActor.h"
#include "Components/AudioComponent.h"
#include "Engine/GameViewportClient.h"
#include "Engine/LocalPlayer.h"
#include "EngineUtils.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "HAL/IConsoleManager.h"
#include "InputAction.h"
#include "InputActionValue.h"
#include "InputMappingContext.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetMathLibrary.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Sound/SoundBase.h"
#include "PlayerCharacter.h"
#include "SpaceshipPawn.h"
#include "SpaceDebugHUD.h"
#include "SpaceMenuGameMode.h"
#include "SpaceMenuWidget.h"
#include "SpaceUserSettings.h"
#include "Widgets/SWeakWidget.h"

DEFINE_LOG_CATEGORY_STATIC(LogSpacePlayer, Log, All);

namespace SpacePlayerDefaults
{
	const TCHAR* const UiHoverSoundPath = TEXT("/Game/UI/Audio/SW_UiHover.SW_UiHover");
	const TCHAR* const UiConfirmSoundPath = TEXT("/Game/UI/Audio/SW_UiConfirm.SW_UiConfirm");
	const TCHAR* const MenuMusicPath = TEXT("/Game/UI/Audio/SW_MenuAmbience.SW_MenuAmbience");

	/** Above every pawn context (they use 0-1), so Escape and H always reach the controller. */
	constexpr int32 GlobalContextPriority = 100;

	USoundBase* LoadSound(const TCHAR* Path)
	{
		return Cast<USoundBase>(StaticLoadObject(USoundBase::StaticClass(), nullptr, Path, nullptr, LOAD_NoWarn | LOAD_Quiet));
	}
}

ASpacePlayerController::ASpacePlayerController()
{
	// The title camera drifts while nothing else ticks.
	PrimaryActorTick.bCanEverTick = true;
}

bool ASpacePlayerController::IsTitleScreen() const
{
	const UWorld* World = GetWorld();
	return World && Cast<ASpaceMenuGameMode>(World->GetAuthGameMode()) != nullptr;
}

void ASpacePlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();

	MenuAction = NewObject<UInputAction>(this, TEXT("IA_Menu_Runtime"));
	MenuAction->ValueType = EInputActionValueType::Boolean;
	HudAction = NewObject<UInputAction>(this, TEXT("IA_ToggleHud_Global_Runtime"));
	HudAction->ValueType = EInputActionValueType::Boolean;

	GlobalContext = NewObject<UInputMappingContext>(this, TEXT("IMC_Global_Runtime"));
	GlobalContext->MapKey(MenuAction, EKeys::Escape);
	GlobalContext->MapKey(MenuAction, EKeys::F10);
	GlobalContext->MapKey(MenuAction, EKeys::Gamepad_Special_Right);
	GlobalContext->MapKey(HudAction, EKeys::H);
	// I: walk the Steadfast interior. A letter on purpose - the Czech layout has no [ ] ; keys and
	// F1-F5 are the engine's debug views in a Development build (Docs/WORKFLOW.md 9.1 g).
	InteriorAction = NewObject<UInputAction>(this, TEXT("IA_Interior_Runtime"));
	InteriorAction->ValueType = EInputActionValueType::Boolean;
	GlobalContext->MapKey(InteriorAction, EKeys::I);

	if (UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(InputComponent))
	{
		Input->BindAction(MenuAction, ETriggerEvent::Started, this, &ASpacePlayerController::HandleMenuKey);
		Input->BindAction(HudAction, ETriggerEvent::Started, this, &ASpacePlayerController::HandleToggleHud);
		Input->BindAction(InteriorAction, ETriggerEvent::Started, this, &ASpacePlayerController::HandleInteriorKey);
	}
	else
	{
		UE_LOG(LogSpacePlayer, Error, TEXT("%s: the input component is not an UEnhancedInputComponent; Escape and H will not work."), *GetName());
	}
}

void ASpacePlayerController::BeginPlay()
{
	Super::BeginPlay();
	if (!IsLocalController())
	{
		return;
	}

	using namespace SpacePlayerDefaults;
	UiHoverSound = LoadSound(UiHoverSoundPath);
	UiConfirmSound = LoadSound(UiConfirmSoundPath);
	MenuMusicSound = LoadSound(MenuMusicPath);

	if (const USpaceUserSettings* Settings = USpaceUserSettings::Get())
	{
		Settings->ApplyGameSettings(GetWorld());
	}
	if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
	{
		if (GlobalContext)
		{
			Subsystem->AddMappingContext(GlobalContext, GlobalContextPriority);
		}
	}

	if (IsTitleScreen())
	{
		// The level's camera tagged MenuCamera, drifting around the actor tagged MenuOrbitCenter.
		for (TActorIterator<ACameraActor> It(GetWorld()); It; ++It)
		{
			if (It->ActorHasTag(TEXT("MenuCamera")))
			{
				TitleCamera = *It;
				break;
			}
		}
		for (TActorIterator<AActor> It(GetWorld()); It; ++It)
		{
			if (It->ActorHasTag(TEXT("MenuOrbitCenter")))
			{
				TitleOrbitCenter = It->GetActorLocation();
				break;
			}
		}
		if (AActor* Camera = TitleCamera.Get())
		{
			bAutoManageActiveCameraTarget = false;
			SetViewTarget(Camera);
			TitleCameraOffset = Camera->GetActorLocation() - TitleOrbitCenter;
		}
		ShowMenu(true);
		if (MenuMusicSound)
		{
			MenuMusic = UGameplayStatics::SpawnSound2D(this, MenuMusicSound, USpaceUserSettings::GetMusicVolume());
			if (MenuMusic)
			{
				MenuMusic->FadeIn(2.f, USpaceUserSettings::GetMusicVolume());
			}
		}
	}
	else
	{
		SetInputMode(FInputModeGameOnly());
		SetShowMouseCursor(false);
	}
}

void ASpacePlayerController::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	HideMenu();
	Super::EndPlay(EndPlayReason);
}

void ASpacePlayerController::PlayerTick(float DeltaTime)
{
	Super::PlayerTick(DeltaTime);
	if (IsTitleScreen())
	{
		UpdateTitleCamera(DeltaTime);
	}
}

void ASpacePlayerController::UpdateTitleCamera(float DeltaTime)
{
	AActor* Camera = TitleCamera.Get();
	if (!Camera)
	{
		return;
	}
	TitleTime += DeltaTime;
	// A slow sway around the ship rather than a full orbit, so the backdrop stays in frame.
	const double Yaw = 16.0 * FMath::Sin(TitleTime * 0.06);
	const double Rise = 120.0 * FMath::Sin(TitleTime * 0.045 + 0.8);
	const FVector Location = TitleOrbitCenter + FRotator(0.0, Yaw, 0.0).RotateVector(TitleCameraOffset) + FVector(0.0, 0.0, Rise);
	// Aimed a little to the left of the ship: the menu panel covers the left of the screen.
	FRotator Rotation = UKismetMathLibrary::FindLookAtRotation(Location, TitleOrbitCenter + FVector(0.0, 0.0, 150.0));
	Rotation.Yaw -= 14.0;
	Camera->SetActorLocationAndRotation(Location, Rotation);
}

// -------------------------------------------------------------------------------------------
// Menus
// -------------------------------------------------------------------------------------------

void ASpacePlayerController::ShowMenu(bool bTitleScreen)
{
	HideMenu();
	UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr;
	if (!Viewport)
	{
		return;  // no viewport (commandlet, dedicated server)
	}
	Menu = SNew(SSpaceMenu).Owner(TWeakObjectPtr<ASpacePlayerController>(this)).TitleScreen(bTitleScreen);
	MenuHost = SNew(SWeakWidget).PossiblyNullContent(Menu);
	Viewport->AddViewportWidgetContent(MenuHost.ToSharedRef(), 50);

	FInputModeUIOnly Mode;
	Mode.SetWidgetToFocus(Menu);
	Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
	SetInputMode(Mode);
	SetShowMouseCursor(true);
}

void ASpacePlayerController::HideMenu()
{
	if (MenuHost.IsValid())
	{
		if (UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr)
		{
			Viewport->RemoveViewportWidgetContent(MenuHost.ToSharedRef());
		}
	}
	MenuHost.Reset();
	Menu.Reset();
}

void ASpacePlayerController::OpenPauseMenu()
{
	if (IsTitleScreen() || IsMenuOpen())
	{
		return;
	}
	SetPause(true);
	ShowMenu(false);
	PlayUiSound(true);
}

void ASpacePlayerController::ResumeGame()
{
	HideMenu();
	SetPause(false);
	SetInputMode(FInputModeGameOnly());
	SetShowMouseCursor(false);
	// Keys held when the menu opened would otherwise stay down.
	FlushPressedKeys();
}

void ASpacePlayerController::HandleMenuKey(const FInputActionValue& /*Value*/)
{
	if (!IsMenuOpen())
	{
		OpenPauseMenu();
	}
}

void ASpacePlayerController::HandleToggleHud(const FInputActionValue& /*Value*/)
{
	ASpaceDebugHUD::CycleDisplayMode();
	if (USpaceUserSettings* Settings = USpaceUserSettings::Get())
	{
		if (const IConsoleVariable* Hud = IConsoleManager::Get().FindConsoleVariable(TEXT("space.Hud")))
		{
			Settings->HudMode = Hud->GetInt();
			Settings->SaveSettings();
		}
	}
}

void ASpacePlayerController::StartGame()
{
	if (MenuMusic)
	{
		MenuMusic->FadeOut(0.5f, 0.f);
	}
	UGameplayStatics::OpenLevel(this, GameLevel);
}

void ASpacePlayerController::GoToMainMenu()
{
	SetPause(false);
	UGameplayStatics::OpenLevel(this, TitleLevel);
}

void ASpacePlayerController::QuitGame()
{
	UKismetSystemLibrary::QuitGame(this, this, EQuitPreference::Quit, false);
}

void ASpacePlayerController::PlayUiSound(bool bConfirm)
{
	USoundBase* Sound = bConfirm ? UiConfirmSound.Get() : UiHoverSound.Get();
	if (!Sound)
	{
		return;
	}
	const double Now = FPlatformTime::Seconds();
	if (!bConfirm)
	{
		// Sweeping the mouse over a column of buttons must not rattle.
		if (Now - LastHoverSoundTime < 0.06)
		{
			return;
		}
		LastHoverSoundTime = Now;
	}
	UGameplayStatics::PlaySound2D(this, Sound, USpaceUserSettings::GetEffectsVolume() * (bConfirm ? 0.8f : 0.4f));
}

void ASpacePlayerController::PreviewVolumes(float MasterVolume, float EffectsVolume, float MusicVolume)
{
	if (const UWorld* World = GetWorld())
	{
		if (FAudioDeviceHandle AudioDevice = World->GetAudioDevice())
		{
			AudioDevice->SetTransientPrimaryVolume(FMath::Clamp(MasterVolume, 0.f, 1.f));
		}
	}
	if (MenuMusic)
	{
		MenuMusic->SetVolumeMultiplier(FMath::Clamp(MusicVolume, 0.f, 1.f));
	}
}

// -------------------------------------------------------------------------------------------
// Interior
// -------------------------------------------------------------------------------------------

namespace
{
	const FName InteriorSpawnTag(TEXT("SpaceInteriorSpawn"));

	AActor* FindInteriorSpawn(UWorld* World)
	{
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			if (It->ActorHasTag(InteriorSpawnTag))
			{
				return *It;
			}
		}
		return nullptr;
	}
}

bool ASpacePlayerController::HasInterior() const
{
	return GetWorld() && FindInteriorSpawn(GetWorld()) != nullptr;
}

void ASpacePlayerController::HandleInteriorKey(const FInputActionValue& /*Value*/)
{
	if (!IsMenuOpen() && !IsTitleScreen())
	{
		ToggleInterior();
	}
}

bool ASpacePlayerController::ToggleInterior()
{
	UWorld* World = GetWorld();
	APawn* Current = GetPawn();
	if (!World || IsTitleScreen())
	{
		return false;
	}

	if (bWalkingInterior)
	{
		// Back: into the ship that was being flown, or to where the player stood.
		if (APawn* Ship = ReturnShip.Get())
		{
			UnPossess();
			if (Current)
			{
				Current->Destroy();
			}
			Possess(Ship);
		}
		else if (Current)
		{
			Current->SetActorTransform(ReturnTransform, false, nullptr, ETeleportType::TeleportPhysics);
		}
		bWalkingInterior = false;
		ReturnShip = nullptr;
		return true;
	}

	AActor* Spawn = FindInteriorSpawn(World);
	if (!Spawn || !Current)
	{
		return false;
	}
	const FTransform Start(Spawn->GetActorRotation(), Spawn->GetActorLocation() + Spawn->GetActorUpVector() * 100.0);
	if (APlayerCharacter* Walker = Cast<APlayerCharacter>(Current))
	{
		// Already on foot somewhere else: take the same character across.
		ReturnShip = nullptr;
		ReturnTransform = Walker->GetActorTransform();
		Walker->SetActorTransform(Start, false, nullptr, ETeleportType::TeleportPhysics);
		Walker->FaceDirection(Spawn->GetActorForwardVector());
		bWalkingInterior = true;
		return true;
	}
	const ASpaceshipPawn* Ship = Cast<ASpaceshipPawn>(Current);
	const TSubclassOf<APawn> WalkerClass = Ship ? Ship->GetPilotCharacterClass() : nullptr;
	if (!WalkerClass)
	{
		return false;
	}
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
	APawn* Walker = World->SpawnActor<APawn>(WalkerClass, Start, Params);
	if (!Walker)
	{
		return false;
	}
	ReturnShip = Current;
	UnPossess();
	Possess(Walker);
	if (APlayerCharacter* OnFoot = Cast<APlayerCharacter>(Walker))
	{
		OnFoot->FaceDirection(Spawn->GetActorForwardVector());
	}
	bWalkingInterior = true;
	UE_LOG(LogSpacePlayer, Log, TEXT("%s: walking the interior from %s"), *GetName(), *Start.GetLocation().ToString());
	return true;
}
