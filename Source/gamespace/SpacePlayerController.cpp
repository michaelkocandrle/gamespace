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
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
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
#include "HAL/PlatformTime.h"
#include "ShipQuantumComponent.h"
#include "SpaceInteraction.h"
#include "SpaceInteractionOverlay.h"
#include "SpaceNotifications.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"

DEFINE_LOG_CATEGORY_STATIC(LogSpacePlayer, Log, All);

namespace SpacePlayerDefaults
{
	const TCHAR* const UiHoverSoundPath = TEXT("/Game/UI/Audio/SW_UiHover.SW_UiHover");
	const TCHAR* const UiConfirmSoundPath = TEXT("/Game/UI/Audio/SW_UiConfirm.SW_UiConfirm");
	const TCHAR* const ButtonPressSoundPath = TEXT("/Game/Ships/Audio/SW_ButtonPress.SW_ButtonPress");
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
	// U ("ukazka"): walk the interior kit showroom in TestSpace (author, 27. 9. 2026)
	ShowroomAction = NewObject<UInputAction>(this, TEXT("IA_Showroom_Runtime"));
	ShowroomAction->ValueType = EInputActionValueType::Boolean;
	GlobalContext->MapKey(ShowroomAction, EKeys::U);

	if (UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(InputComponent))
	{
		Input->BindAction(MenuAction, ETriggerEvent::Started, this, &ASpacePlayerController::HandleMenuKey);
		Input->BindAction(HudAction, ETriggerEvent::Started, this, &ASpacePlayerController::HandleToggleHud);
		Input->BindAction(InteriorAction, ETriggerEvent::Started, this, &ASpacePlayerController::HandleInteriorKey);
		Input->BindAction(ShowroomAction, ETriggerEvent::Started, this, &ASpacePlayerController::HandleShowroomKey);
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
	ButtonPressSound = LoadSound(ButtonPressSoundPath);
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
		StartPrewarm();
		// SC's interaction layer over the game, under the menus (z-order 50).
		if (UGameViewportClient* Viewport = GetWorld()->GetGameViewport())
		{
			InteractionOverlay = SNew(SSpaceInteractionOverlay).Owner(TWeakObjectPtr<ASpacePlayerController>(this));
			InteractionOverlayHost = SNew(SWeakWidget).PossiblyNullContent(InteractionOverlay);
			Viewport->AddViewportWidgetContent(InteractionOverlayHost.ToSharedRef(), 10);
		}
	}
}

void ASpacePlayerController::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	HideMenu();
	if (InteractionOverlayHost.IsValid())
	{
		if (UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr)
		{
			Viewport->RemoveViewportWidgetContent(InteractionOverlayHost.ToSharedRef());
		}
	}
	InteractionOverlayHost.Reset();
	InteractionOverlay.Reset();
	Super::EndPlay(EndPlayReason);
}

void ASpacePlayerController::PlayerTick(float DeltaTime)
{
	Super::PlayerTick(DeltaTime);
	if (IsTitleScreen())
	{
		UpdateTitleCamera(DeltaTime);
	}
	TickEntryWatch();
	TickSeatTransition(DeltaTime);
	if (!IsTitleScreen())
	{
		TickInteraction();
		TickNotifications();
	}
}

void ASpacePlayerController::PlaySeatTransition(const FMinimalViewInfo& From, AActor* To, float Seconds, float ArcCm, float PitchDipDeg)
{
	if (!To || Seconds <= 0.f || !GetWorld())
	{
		return;
	}
	if (!SeatCamera)
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		SeatCamera = GetWorld()->SpawnActor<ACameraActor>(From.Location, From.Rotation, Params);
		if (!SeatCamera)
		{
			return;
		}
		SeatCamera->GetCameraComponent()->bConstrainAspectRatio = false;
	}
	SeatCamera->SetActorLocationAndRotation(From.Location, From.Rotation);
	SeatCamera->GetCameraComponent()->SetFieldOfView(From.FOV);
	SeatFrom = From;
	SeatTo = To;
	SeatSeconds = Seconds;
	SeatElapsed = 0.f;
	SeatArcCm = ArcCm;
	SeatDipDeg = PitchDipDeg;
	SetViewTarget(SeatCamera);
}

void ASpacePlayerController::TickSeatTransition(float DeltaTime)
{
	if (SeatSeconds <= 0.f || !SeatCamera)
	{
		return;
	}
	AActor* To = SeatTo.Get();
	if (!To)
	{
		SeatSeconds = 0.f;
		return;
	}
	SeatElapsed += DeltaTime;
	const float A = FMath::Clamp(SeatElapsed / SeatSeconds, 0.f, 1.f);
	const float E = A * A * A * (A * (A * 6.f - 15.f) + 10.f);       // smootherstep: a body's start and stop
	FMinimalViewInfo ToView;
	To->CalcCamera(DeltaTime, ToView);
	// a quadratic arc over the backrest, in the ship's (or the walker's) up
	const FVector Up = To->GetActorUpVector();
	const FVector Mid = FMath::Lerp(SeatFrom.Location, ToView.Location, 0.5f) + Up * SeatArcCm;
	const FVector P = FMath::Lerp(FMath::Lerp(SeatFrom.Location, Mid, E), FMath::Lerp(Mid, ToView.Location, E), E);
	FRotator R = FQuat::Slerp(SeatFrom.Rotation.Quaternion(), ToView.Rotation.Quaternion(), E).Rotator();
	R.Pitch -= SeatDipDeg * FMath::Sin(A * PI);                      // the head looks down on the way
	R.Roll += SeatDipDeg * 0.25f * FMath::Sin(A * 2.f * PI);          // and sways a little as the body turns
	SeatCamera->SetActorLocationAndRotation(P, R);
	SeatCamera->GetCameraComponent()->SetFieldOfView(FMath::Lerp(SeatFrom.FOV, ToView.FOV, E));
	if (A >= 1.f)
	{
		SeatSeconds = 0.f;
		SetViewTarget(To);
	}
}

bool ASpacePlayerController::IsInteractModeFor(const APawn* Pawn)
{
	const ASpacePlayerController* Controller = Pawn ? Cast<ASpacePlayerController>(Pawn->GetController()) : nullptr;
	return Controller && Controller->bInteractMode;
}

void ASpacePlayerController::DebugSetInteractMode(bool bOn)
{
	SetInteractMode(bOn);
	bInteractHoldUsed = bOn;
}

void ASpacePlayerController::SetInteractMode(bool bOn)
{
	if (bOn == bInteractMode)
	{
		return;
	}
	bInteractMode = bOn;
	// SC (the author, 5. 10. 2026): holding F the player keeps looking round; what is under the cursor at the
	// screen's centre is the target. In the seat the mouse turns the head (free look), it does not steer the ship.
	if (ASpaceshipPawn* Ship = Cast<ASpaceshipPawn>(GetPawn()))
	{
		Ship->SetInteractLook(bOn);
	}
}

void ASpacePlayerController::TickInteraction()
{
	// SC: a tap on F uses the target; holding it a moment is interact mode, released it closes again.
	constexpr double HoldSeconds = 0.3;
	constexpr double HoverPixels = 70.0;
	APawn* const Played = GetPawn();
	const bool bAllowed = Played && !IsMenuOpen();
	const bool bDown = bAllowed && IsInputKeyDown(EKeys::F);
	const double Now = FPlatformTime::Seconds();
	if (bDown && !bInteractKeyWasDown)
	{
		InteractKeyDownSeconds = Now;
		bInteractHoldUsed = false;
	}
	if (bDown && !bInteractMode && Now - InteractKeyDownSeconds >= HoldSeconds)
	{
		SetInteractMode(true);
		bInteractHoldUsed = true;
	}
	if (!bDown && bInteractKeyWasDown)
	{
		if (bInteractMode)
		{
			SetInteractMode(false);
		}
		else if (!bInteractHoldUsed && bAllowed)
		{
			SpaceInteraction::Interact(Played);
		}
	}
	if (!bAllowed && bInteractMode)
	{
		SetInteractMode(false);
	}
	bInteractKeyWasDown = bDown;

	// U in the pilot seat: the ship's power (SC). Alt+U is the kit showroom (HandleShowroomKey).
	const bool bAlt = IsInputKeyDown(EKeys::LeftAlt) || IsInputKeyDown(EKeys::RightAlt);
	const bool bPowerDown = bAllowed && IsInputKeyDown(EKeys::U) && !bAlt;
	if (bPowerDown && !bPowerKeyWasDown)
	{
		if (ASpaceshipPawn* Ship = Cast<ASpaceshipPawn>(Played))
		{
			Ship->TogglePower();
			if (USpaceNotifications* Notes = USpaceNotifications::Get(this); Notes && Ship->GetPowerState() == ESpacePowerState::Off)
			{
				Notes->Toast(NSLOCTEXT("SpaceHints", "PowerOff", "Napájení lodi vypnuto"), 3.f);
			}
		}
	}
	bPowerKeyWasDown = bPowerDown;
	// I in the pilot seat: the engines (SC). Alt+I is the old interior tour (HandleInteriorKey).
	const bool bEnginesDown = bAllowed && IsInputKeyDown(EKeys::I) && !bAlt;
	if (bEnginesDown && !bEnginesKeyWasDown)
	{
		if (ASpaceshipPawn* Ship = Cast<ASpaceshipPawn>(Played))
		{
			Ship->ToggleEngines();
			if (USpaceNotifications* Notes = USpaceNotifications::Get(this))
			{
				Notes->Toast(Ship->AreEnginesWanted() ? (Ship->IsPowered() ? NSLOCTEXT("SpaceHints", "EnginesStart", "Motory startují")
					: NSLOCTEXT("SpaceHints", "EnginesNoPower", "Motory: nejdřív napájení (U)")) : NSLOCTEXT("SpaceHints", "EnginesOff", "Motory vypnuty"), 3.f);
			}
		}
	}
	bEnginesKeyWasDown = bEnginesDown;

	FSpaceInteractionView& View = InteractionView;
	APawn* const Current = GetPawn();  // the tap may just have swapped it
	View.bInteractMode = bInteractMode;
	View.Hovered = INDEX_NONE;
	const IConsoleVariable* Hud = IConsoleManager::Get().FindConsoleVariable(TEXT("space.Hud"));
	// H hides the HUD, not the interaction (author 5. 10. 2026: the cursor vanished with the HUD)
	View.bVisible = Current && !IsMenuOpen();
	View.bHudShown = !Hud || Hud->GetInt() > 0;
	if (!Current)
	{
		View.Hotspots.Reset();
		View.Keys.Reset();
		View.Target = FSpaceInteractTarget();
		return;
	}
	SpaceInteraction::Gather(Current, View.Target, View.Hotspots);
	int32 Width = 0, Height = 0;
	GetViewportSize(Width, Height);
	auto OnScreen = [&](const FVector& World, FVector2D& OutScreen)
	{
		return ProjectWorldLocationToScreen(World, OutScreen, true) && OutScreen.X >= 0.0 && OutScreen.Y >= 0.0
			&& OutScreen.X <= Width && OutScreen.Y <= Height;
	};
	View.bTargetOnScreen = View.Target.bValid && OnScreen(View.Target.WorldLocation, View.TargetScreen);
	View.HotspotScreen.SetNum(View.Hotspots.Num());
	View.HotspotOnScreen.SetNum(View.Hotspots.Num());
	View.HotspotLabelScreen.SetNum(View.Hotspots.Num());
	View.HotspotPixelSize.SetNum(View.Hotspots.Num());
	const float MouseX = Width * 0.5f, MouseY = Height * 0.5f;
	const bool bMouse = bInteractMode;
	View.CursorScreen = FVector2D(MouseX, MouseY);
	const float FocalPx = PlayerCameraManager ? float(Width) * 0.5f / FMath::Tan(FMath::DegreesToRadians(PlayerCameraManager->GetFOVAngle() * 0.5f)) : float(Width) * 0.5f;
	const FVector EyeAt = PlayerCameraManager ? PlayerCameraManager->GetCameraLocation() : FVector::ZeroVector;
	double Best = HoverPixels;
	for (int32 Index = 0; Index < View.Hotspots.Num(); ++Index)
	{
		View.HotspotOnScreen[Index] = OnScreen(View.Hotspots[Index].WorldLocation, View.HotspotScreen[Index]);
		View.HotspotLabelScreen[Index] = View.HotspotScreen[Index];
		View.HotspotPixelSize[Index] = View.Hotspots[Index].SizeCm * FocalPx / FMath::Max(1.f, float(FVector::Dist(EyeAt, View.Hotspots[Index].WorldLocation)));
		if (View.Hotspots[Index].bLabelAnchor)
		{
			FVector2D Anchor;
			if (OnScreen(View.Hotspots[Index].LabelWorldLocation, Anchor))
			{
				View.HotspotLabelScreen[Index] = Anchor;
			}
		}
		if (bMouse && View.HotspotOnScreen[Index])
		{
			const double Distance = FVector2D::Distance(View.HotspotScreen[Index], FVector2D(MouseX, MouseY));
			// the cursor has to be on the control (its own size on screen, at least a finger's width), not just near
			const double Reach = FMath::Max(14.0, View.HotspotPixelSize[Index] * 0.5 + 6.0);
			if (Distance < Best && Distance < Reach)
			{
				Best = Distance;
				View.Hovered = Index;
			}
		}
	}
	if (bInteractMode && View.Hotspots.IsValidIndex(ForcedHover))
	{
		View.Hovered = ForcedHover;
		View.CursorScreen = View.HotspotScreen[ForcedHover];
	}
	if (bInteractMode && View.Hotspots.IsValidIndex(View.Hovered) && View.Hotspots[View.Hovered].Use)
	{
		if (WasInputKeyJustPressed(EKeys::LeftMouseButton))
		{
			PlayButtonPress();
			View.Hotspots[View.Hovered].Use(true);
		}
		else if (WasInputKeyJustPressed(EKeys::RightMouseButton))
		{
			PlayButtonPress();
			View.Hotspots[View.Hovered].Use(false);
		}
	}
	SpaceInteraction::KeyHints(GetPawn(), bInteractMode, View.Target, View.Keys);
}

void ASpacePlayerController::TickNotifications()
{
	USpaceNotifications* Notes = USpaceNotifications::Get(this);
	APawn* const Current = GetPawn();
	if (!Notes || !Current)
	{
		return;
	}
	// The screenshot runner's pictures stay free of cards and toasts.
	FString ShotList;
	if (FParse::Value(FCommandLine::Get(), TEXT("-ShotList="), ShotList))
	{
		return;
	}
	if (ASpaceshipPawn* Ship = Cast<ASpaceshipPawn>(Current))
	{
		Notes->Hint(TEXT("FlightBasics"), NSLOCTEXT("SpaceHints", "FlightTitle", "Ovládání lodi"),
			NSLOCTEXT("SpaceHints", "FlightBody", "W a S tah, A a D úkrok, mezerník a Ctrl nahoru a dolů, Q a E náklon, myš zatáčí. B přepíná SCM a NAV, N vysune podvozek."));
		if (Ship->GetMasterMode() == EMasterMode::NAV && Ship->HasQuantumTarget())
		{
			Notes->Hint(TEXT("Quantum"), NSLOCTEXT("SpaceHints", "QuantumTitle", "Quantum skok"),
				NSLOCTEXT("SpaceHints", "QuantumBody", "Namiř nos na cíl. Pohon se nejdřív roztočí a zkalibruje; až HUD ukáže READY, podrž levé tlačítko myši."));
		}
		if (!Ship->IsLanded() && Ship->HasGroundInfo() && Ship->GetGroundGapCm() >= 0.f && Ship->GetGroundGapCm() < 3000.f)
		{
			Notes->Hint(TEXT("Landing"), NSLOCTEXT("SpaceHints", "LandingTitle", "Přistání"),
				NSLOCTEXT("SpaceHints", "LandingBody", "Vysuň podvozek (N) a klesej (Ctrl). Rámeček nad páskou kurzu řekne, proč loď nepřistává: sklon, nerovný terén nebo rychlost."));
		}
		const bool bTraveling = Ship->GetQuantumState() == EQuantumState::Traveling;
		if (bLastQuantumTraveling && !bTraveling)
		{
			Notes->Toast(NSLOCTEXT("SpaceHints", "QuantumDone", "Quantum skok dokončen"));
		}
		bLastQuantumTraveling = bTraveling;
	}
	else if (APlayerCharacter* Walker = Cast<APlayerCharacter>(Current))
	{
		Notes->Hint(TEXT("Interaction"), NSLOCTEXT("SpaceHints", "InteractTitle", "Interakce"),
			NSLOCTEXT("SpaceHints", "InteractBody", "Krátké F použije věc s popiskem. Podržením F zapneš režim interakce: kurzorem klikáš na obrazovky a ovládání, pravým tlačítkem zpět."));
		ASpaceshipPawn* Inside = Walker->GetInteriorShip();
		if (Inside && !LastInteriorShip.IsValid())
		{
			FString Name = Inside->GetClass()->GetName();
			Name.RemoveFromStart(TEXT("BP_Ship_"));
			Name.RemoveFromEnd(TEXT("_C"));
			Notes->Toast(FText::Format(NSLOCTEXT("SpaceHints", "Boarded", "Jsi na palubě lodi {0}"), FText::FromString(Name.ToUpper())));
		}
		LastInteriorShip = Inside;
		bLastQuantumTraveling = false;
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

void ASpacePlayerController::DebugShowMenu(int32 Page, int32 Tab, bool bScrollToEnd)
{
	if (Page < 0)
	{
		HideMenu();
		return;
	}
	ShowMenu(Page == 0);
	if (Menu.IsValid())
	{
		Menu->ShowTab(ESpaceSettingsTab(FMath::Clamp(Tab, 0, int32(ESpaceSettingsTab::Count) - 1)));
		Menu->ShowPage(ESpaceMenuPage(FMath::Clamp(Page, 0, 3)));
		if (bScrollToEnd)
		{
			// The list scrolled to its end; on the KLÁVESY tab, the on-foot controls instead.
			Menu->ScrollTabToEnd();
			Menu->SetKeysMode(1);
		}
	}
}

namespace SpacePlayerControllerConsole
{
	static FAutoConsoleCommandWithWorldAndArgs InteractModeCommand(
		TEXT("space.InteractMode"),
		TEXT("space.InteractMode 0|1 [hotspot]: interact mode off or on as if F were held, with that hotspot shown hovered (screenshots)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			ASpacePlayerController* Controller = World ? Cast<ASpacePlayerController>(World->GetFirstPlayerController()) : nullptr;
			if (!Controller || Args.Num() < 1)
			{
				return;
			}
			Controller->DebugSetInteractMode(FCString::Atoi(*Args[0]) != 0);
			Controller->DebugForceHover(Args.Num() > 1 ? FCString::Atoi(*Args[1]) : INDEX_NONE);
		}));

	static FAutoConsoleCommandWithWorldAndArgs PowerCommand(
		TEXT("space.Power"),
		TEXT("space.Power 0|1 [instant]: the ship's power off or on (with its start-up unless instant is 1)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			APlayerController* Controller = World ? World->GetFirstPlayerController() : nullptr;
			ASpaceshipPawn* Ship = Controller ? Cast<ASpaceshipPawn>(Controller->GetPawn()) : nullptr;
			if (!Ship)
			{
				// On foot inside: the ship around the pilot.
				if (APlayerCharacter* Walker = Controller ? Cast<APlayerCharacter>(Controller->GetPawn()) : nullptr)
				{
					Ship = Walker->GetInteriorShip();
				}
			}
			if (Ship && Args.Num() >= 1)
			{
				Ship->SetPower(FCString::Atoi(*Args[0]) != 0, Args.Num() > 1 && FCString::Atoi(*Args[1]) != 0);
			}
		}));

	static FAutoConsoleCommandWithWorldAndArgs EnginesCommand(
		TEXT("space.Engines"),
		TEXT("space.Engines 0|1 [instant]: the ship's engines off or on (with their spool unless instant is 1; they need the power)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			APlayerController* Controller = World ? World->GetFirstPlayerController() : nullptr;
			if (ASpaceshipPawn* Ship = Controller ? Cast<ASpaceshipPawn>(Controller->GetPawn()) : nullptr; Ship && Args.Num() >= 1)
			{
				Ship->SetEngines(FCString::Atoi(*Args[0]) != 0, Args.Num() > 1 && FCString::Atoi(*Args[1]) != 0);
			}
		}));

	static FAutoConsoleCommandWithWorldAndArgs NotifyCommand(
		TEXT("space.Notify"),
		TEXT("space.Notify toast <text...> | hint <title>|<body...>: push a toast or a hint card (screenshots and tests)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			USpaceNotifications* Notes = USpaceNotifications::Get(World);
			if (!Notes || Args.Num() < 2)
			{
				return;
			}
			TArray<FString> Rest(Args);
			Rest.RemoveAt(0);
			const FString Text = FString::Join(Rest, TEXT(" "));
			if (Args[0] == TEXT("hint"))
			{
				FString Title, Body;
				if (!Text.Split(TEXT("|"), &Title, &Body))
				{
					Title = Text;
				}
				Notes->DebugHint(Title, Body);
			}
			else
			{
				Notes->DebugToast(Text);
			}
		}));

	static FAutoConsoleCommandWithWorldAndArgs MenuCommand(
		TEXT("space.Menu"),
		TEXT("space.Menu <page> [tab] [1 = list scrolled to its end]: shows a menu page over the game without pausing, for screenshots - 0 title, 1 pause, 2 settings, 3 loading, -1 hides it; tab 0 game, 1 graphics, 2 audio, 3 controls."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			ASpacePlayerController* Controller = World ? Cast<ASpacePlayerController>(World->GetFirstPlayerController()) : nullptr;
			if (!Controller || Args.Num() < 1)
			{
				return;
			}
			Controller->DebugShowMenu(FCString::Atoi(*Args[0]), Args.Num() > 1 ? FCString::Atoi(*Args[1]) : 1, Args.Num() > 2 && FCString::Atoi(*Args[2]) != 0);
		}));
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

void ASpacePlayerController::PlayButtonPress()
{
	if (ButtonPressSound)
	{
		UGameplayStatics::PlaySound2D(this, ButtonPressSound, USpaceUserSettings::GetEffectsVolume() * 0.9f, FMath::FRandRange(0.96f, 1.04f));
	}
	else
	{
		PlayUiSound(true);
	}
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
	const FName ShowroomSpawnTag(TEXT("KitShowroomSpawn"));
	const FName ShowroomAnnexSpawnTag(TEXT("KitShowroomAnnexSpawn"));
	const FName ShowroomStairsSpawnTag(TEXT("KitShowroomStairsSpawn"));
	// the parts factory's corridor test section behind the stair bay (KF-PORTAL-01, 6. 10. 2026)
	const FName ShowroomTestSpawnTag(TEXT("KitShowroomTestSpawn"));

	// MegaLights variant C (author, 27. 9. 2026): interiors are lit through MegaLights with the fixtures' ray-traced
	// shadows (the kit showroom's lights cast shadows in the level); the view from the ship and the planet keep
	// today's lighting until MegaLights is measured there
	// Lumen reflections in interiors: off from 27. 9. 2026 (2.3-2.8 ms on the RTX 2060), variant c since 6. 10. 2026
	// (traced below roughness 0.32 at half resolution, SetInteriorLighting)
	/** space.InteriorLighting asked for the interior lighting (shots with the free camera): the prewarm's end keeps it. */
	bool bInteriorLightingRequested = false;
	/** What SetInteriorLighting set last (ships read it through ASpacePlayerController::IsInteriorLightingOn). */
	bool bInteriorLightingOn = false;

	void SetInteriorLighting(bool bInterior)
	{
		bInteriorLightingOn = bInterior;
		IConsoleManager& Console = IConsoleManager::Get();
		if (IConsoleVariable* MegaLights = Console.FindConsoleVariable(TEXT("r.MegaLights.EnableForProject")))
		{
			MegaLights->Set(bInterior ? 1 : 0, ECVF_SetByCode);
		}
		// 2 samples per pixel instead of 4 (author 29. 9. 2026): -0.6 ms in the Wayfarer's kit corridor (16.67 -> 16.05 ms
		// GPU), a little more grain on dark slopes; MegaLights runs only in interiors, so it is set with it
		if (bInterior)
		{
			if (IConsoleVariable* Samples = Console.FindConsoleVariable(TEXT("r.MegaLights.NumSamplesPerPixel")))
			{
				Samples->Set(2, ECVF_SetByCode);
			}
		}
		// Variant c of the metal reflections (author 6. 10. 2026, Docs/Reviews/2026-10-06_kit_material_board.md): Lumen
		// reflections stay on in interiors too, traced only below roughness 0.32 at half resolution - the polished lips
		// and glass are traced, the matt paint is not (RX 9070, 1440p TSR: +0.6-1.4 ms GPU). Outside the ship's interior
		// the full reflections as before.
		static const float StartMaxRoughness = [&Console]()
		{
			IConsoleVariable* Var = Console.FindConsoleVariable(TEXT("r.Lumen.Reflections.MaxRoughnessToTrace"));
			return Var ? Var->GetFloat() : -1.0f;
		}();
		static const int32 StartDownsample = [&Console]()
		{
			IConsoleVariable* Var = Console.FindConsoleVariable(TEXT("r.Lumen.Reflections.DownsampleFactor"));
			return Var ? Var->GetInt() : 1;
		}();
		if (IConsoleVariable* Reflections = Console.FindConsoleVariable(TEXT("r.Lumen.Reflections.Allow")))
		{
			Reflections->Set(1, ECVF_SetByCode);
		}
		if (IConsoleVariable* MaxRoughness = Console.FindConsoleVariable(TEXT("r.Lumen.Reflections.MaxRoughnessToTrace")))
		{
			MaxRoughness->Set(bInterior ? 0.32f : StartMaxRoughness, ECVF_SetByCode);
		}
		if (IConsoleVariable* Downsample = Console.FindConsoleVariable(TEXT("r.Lumen.Reflections.DownsampleFactor")))
		{
			Downsample->Set(bInterior ? 2 : StartDownsample, ECVF_SetByCode);
		}
	}

	AActor* FindInteriorSpawn(UWorld* World, FName Tag = InteriorSpawnTag)
	{
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			if (It->ActorHasTag(Tag))
			{
				return *It;
			}
		}
		return nullptr;
	}
}

bool ASpacePlayerController::IsInteriorLightingOn()
{
	return bInteriorLightingOn;
}

void ASpacePlayerController::SetShipInteriorLighting(bool bOn)
{
	// the prewarm's end keeps it on while requested
	bInteriorLightingRequested = bOn;
	SetInteriorLighting(bOn);
}

void ASpacePlayerController::ApplyInteriorLighting(bool bInterior)
{
	bInteriorLightingRequested = bInterior;
	SetInteriorLighting(bInterior);
}

void ASpacePlayerController::StartPrewarm()
{
	// MegaLights' first frames stalled the game once (~140 ms: its shaders and the ray-traced shadow pipelines
	// made on first use). The level's first frames are a load anyway: MegaLights on for them, off again before
	// play unless the player is walking an interior (author, 27. 9. 2026). -NoMegaLightsPrewarm measures without.
	UWorld* World = GetWorld();
	if (!World || FParse::Param(FCommandLine::Get(), TEXT("NoMegaLightsPrewarm"))
		|| (!FindInteriorSpawn(World) && !FindInteriorSpawn(World, ShowroomSpawnTag)))
	{
		return;
	}
	SetInteriorLighting(true);
	PrewarmFramesLeft = 30;
	UE_LOG(LogSpacePlayer, Log, TEXT("%s: MegaLights prewarm for %d frames"), *GetName(), PrewarmFramesLeft);
}

void ASpacePlayerController::WatchEntry()
{
	EntryFramesLeft = 120;
	EntryFramesSeen = 0;
	EntryMaxFrameMs = 0.f;
}

void ASpacePlayerController::TickEntryWatch()
{
	if (PrewarmFramesLeft > 0 && --PrewarmFramesLeft == 0)
	{
		// back to what is wanted now: an interior walked or asked for by space.InteriorLighting keeps its lighting
		// (the shots' warm-up command came before the prewarm ended and was switched off - 25 ms frames)
		SetInteriorLighting(bWalkingInterior || bInteriorLightingRequested);
		UE_LOG(LogSpacePlayer, Log, TEXT("%s: MegaLights prewarm done"), *GetName());
	}
	if (EntryFramesLeft <= 0)
	{
		return;
	}
	EntryMaxFrameMs = FMath::Max(EntryMaxFrameMs, float(FApp::GetDeltaTime() * 1000.0));
	++EntryFramesSeen;
	if (--EntryFramesLeft == 0)
	{
		// the numbers a hitch check reads from the log (shots: kit_entry_hitch.json)
		UE_LOG(LogSpacePlayer, Display, TEXT("INTERIOR ENTRY %s: longest frame %.1f ms in the first %d frames"),
			*WalkingSpawnTag.ToString(), EntryMaxFrameMs, EntryFramesSeen);
	}
}

bool ASpacePlayerController::HasInterior() const
{
	return GetWorld() && FindInteriorSpawn(GetWorld()) != nullptr;
}

void ASpacePlayerController::HandleInteriorKey(const FInputActionValue& /*Value*/)
{
	// Alt+I: plain I is the ship's engines since 5. 10. 2026 (SC)
	if (!IsInputKeyDown(EKeys::LeftAlt) && !IsInputKeyDown(EKeys::RightAlt))
	{
		return;
	}
	if (!IsMenuOpen() && !IsTitleScreen())
	{
		ToggleInterior();
	}
}

void ASpacePlayerController::HandleShowroomKey(const FInputActionValue& /*Value*/)
{
	// Alt+U: plain U is the ship's power since 4. 10. 2026 (SC).
	if (!IsInputKeyDown(EKeys::LeftAlt) && !IsInputKeyDown(EKeys::RightAlt))
	{
		return;
	}
	if (!IsMenuOpen() && !IsTitleScreen())
	{
		// U walks a round: the showroom, its annex (the catalogue-only kit parts), the stair bay (batch 3), the parts
		// factory's test section (6. 10. 2026), then back where the player came from (author, 27. 9. 2026)
		static const FName Round[] = {ShowroomSpawnTag, ShowroomAnnexSpawnTag, ShowroomStairsSpawnTag, ShowroomTestSpawnTag};
		int32 Stop = INDEX_NONE;
		for (int32 i = 0; bWalkingInterior && i < UE_ARRAY_COUNT(Round); ++i)
		{
			if (WalkingSpawnTag == Round[i])
			{
				Stop = i;
			}
		}
		if (Stop == INDEX_NONE)
		{
			ToggleInteriorAt(ShowroomSpawnTag);
			return;
		}
		// the next stop the level has, or back when this was the last one
		for (int32 Next = Stop + 1; Next < UE_ARRAY_COUNT(Round); ++Next)
		{
			if (GetWorld() && FindInteriorSpawn(GetWorld(), Round[Next]))
			{
				ToggleInteriorAt(Round[Next]);
				return;
			}
		}
		ToggleInteriorAt(Round[Stop]);
	}
}

bool ASpacePlayerController::ToggleInterior()
{
	return ToggleInteriorAt(InteriorSpawnTag);
}

bool ASpacePlayerController::ToggleInteriorAt(FName SpawnTag)
{
	UWorld* World = GetWorld();
	APawn* Current = GetPawn();
	if (!World || IsTitleScreen())
	{
		return false;
	}

	if (bWalkingInterior && WalkingSpawnTag == SpawnTag)
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
		SetInteriorLighting(false);
		return true;
	}

	AActor* Spawn = FindInteriorSpawn(World, SpawnTag);
	if (!Spawn || !Current)
	{
		return false;
	}
	const FTransform Start(Spawn->GetActorRotation(), Spawn->GetActorLocation() + Spawn->GetActorUpVector() * 100.0);
	if (APlayerCharacter* Walker = Cast<APlayerCharacter>(Current))
	{
		// Already on foot somewhere else: take the same character across. From another interior the way back
		// stays what it was (the ship, or the first spot on foot).
		if (!bWalkingInterior)
		{
			ReturnShip = nullptr;
			ReturnTransform = Walker->GetActorTransform();
		}
		Walker->SetActorTransform(Start, false, nullptr, ETeleportType::TeleportPhysics);
		Walker->FaceDirection(Spawn->GetActorForwardVector());
		bWalkingInterior = true;
		WalkingSpawnTag = SpawnTag;
		SetInteriorLighting(true);
		WatchEntry();
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
	WalkingSpawnTag = SpawnTag;
	SetInteriorLighting(true);
	WatchEntry();
	UE_LOG(LogSpacePlayer, Log, TEXT("%s: walking %s from %s (MegaLights on)"), *GetName(), *SpawnTag.ToString(), *Start.GetLocation().ToString());
	return true;
}
