// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceshipPawn.h"

#include "Camera/CameraComponent.h"
#include "Components/AudioComponent.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/CollisionProfile.h"
#include "Engine/LocalPlayer.h"
#include "Engine/StaticMesh.h"
#include "Algo/Find.h"
#include "Engine/World.h"
#include "PlayerCharacter.h"
#include "SpaceDebugHUD.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "InputAction.h"
#include "InputActionValue.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "InputTriggers.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Sound/SoundBase.h"
#include "SpaceDustComponent.h"
#include "UObject/ConstructorHelpers.h"

DEFINE_LOG_CATEGORY_STATIC(LogSpaceship, Log, All);

namespace SpaceshipPawnDefaults
{
	/** Authored Enhanced Input assets are looked for here before anything is generated. */
	const TCHAR* const MappingContextPath = TEXT("/Game/Input/IMC_Spaceship.IMC_Spaceship");
	const TCHAR* const ThrustActionPath = TEXT("/Game/Input/IA_Thrust.IA_Thrust");
	const TCHAR* const StrafeActionPath = TEXT("/Game/Input/IA_Strafe.IA_Strafe");
	const TCHAR* const LiftActionPath = TEXT("/Game/Input/IA_Lift.IA_Lift");
	const TCHAR* const RollActionPath = TEXT("/Game/Input/IA_Roll.IA_Roll");
	const TCHAR* const LookActionPath = TEXT("/Game/Input/IA_Look.IA_Look");
	const TCHAR* const ToggleCameraActionPath = TEXT("/Game/Input/IA_ToggleCamera.IA_ToggleCamera");
	const TCHAR* const BoostActionPath = TEXT("/Game/Input/IA_Boost.IA_Boost");
	const TCHAR* const InteractActionPath = TEXT("/Game/Input/IA_Interact.IA_Interact");
	const TCHAR* const FreeLookActionPath = TEXT("/Game/Input/IA_FreeLook.IA_FreeLook");
	const TCHAR* const ToggleHudActionPath = TEXT("/Game/Input/IA_ToggleHud.IA_ToggleHud");
	const TCHAR* const MouseLookActionPath = TEXT("/Game/Input/IA_LookMouse.IA_LookMouse");
	const TCHAR* const MouseMappingContextPath = TEXT("/Game/Input/IMC_SpaceshipMouse.IMC_SpaceshipMouse");
	const TCHAR* const FlightAssistActionPath = TEXT("/Game/Input/IA_FlightAssist.IA_FlightAssist");
	const TCHAR* const CruiseActionPath = TEXT("/Game/Input/IA_CruiseDrive.IA_CruiseDrive");
	const TCHAR* const AllStopActionPath = TEXT("/Game/Input/IA_AllStop.IA_AllStop");
	const TCHAR* const CameraZoomActionPath = TEXT("/Game/Input/IA_CameraZoom.IA_CameraZoom");
	const TCHAR* const EngineLoopSoundPath = TEXT("/Game/Ships/Audio/SW_EngineLoop.SW_EngineLoop");
	const TCHAR* const EngineHumSoundPath = TEXT("/Game/Ships/Audio/SW_EngineHum.SW_EngineHum");
	const TCHAR* const BoostLoopSoundPath = TEXT("/Game/Ships/Audio/SW_BoostLoop.SW_BoostLoop");
	const TCHAR* const CruiseLoopSoundPath = TEXT("/Game/Ships/Audio/SW_CruiseLoop.SW_CruiseLoop");
	const TCHAR* const BoostStartSoundPath = TEXT("/Game/Ships/Audio/SW_BoostStart.SW_BoostStart");
	const TCHAR* const CruiseChargeSoundPath = TEXT("/Game/Ships/Audio/SW_CruiseCharge.SW_CruiseCharge");
	const TCHAR* const CruiseEngageSoundPath = TEXT("/Game/Ships/Audio/SW_CruiseEngage.SW_CruiseEngage");
	const TCHAR* const CruiseDropSoundPath = TEXT("/Game/Ships/Audio/SW_CruiseDrop.SW_CruiseDrop");

	/** The material parameter the ship animates on thruster and strobe slots (M_Ship_Hull). */
	const FName EmissiveStrengthParameter(TEXT("EmissiveStrength"));

	/** Quiet load: a missing asset is the normal case until the designer authors one. */
	template <typename T>
	T* LoadOptional(const TCHAR* Path)
	{
		return Cast<T>(StaticLoadObject(T::StaticClass(), nullptr, Path, nullptr, LOAD_NoWarn | LOAD_Quiet));
	}
}

ASpaceshipPawn::ASpaceshipPawn()
{
	PrimaryActorTick.bCanEverTick = true;

	// The ship steers itself on all three axes, so the controller must not drive our rotation.
	// APawn defaults bUseControllerRotationYaw to true, which would fight the flight model.
	bUseControllerRotationPitch = false;
	bUseControllerRotationYaw = false;
	bUseControllerRotationRoll = false;

	// Sized to the placeholder hull below: the 100 cm cube scaled by (2, 1, 0.35).
	HullCollision = CreateDefaultSubobject<UBoxComponent>(TEXT("HullCollision"));
	HullCollision->SetBoxExtent(FVector(100.f, 50.f, 17.5f));
	HullCollision->SetCollisionProfileName(TEXT("Pawn"));
	// See the header: characters use the hull's real shape, not this box.
	HullCollision->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
	HullCollision->SetSimulatePhysics(false);
	SetRootComponent(HullCollision);

	Hull = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Hull"));
	Hull->SetupAttachment(HullCollision);
	// Query only, and only for pawns, cameras and visibility traces. Moving the ship sweeps the
	// root alone and ignores the ship's own components, so this never affects its flight.
	Hull->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Hull->SetCollisionObjectType(ECC_WorldDynamic);
	Hull->SetCollisionResponseToAllChannels(ECR_Ignore);
	Hull->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
	Hull->SetCollisionResponseToChannel(ECC_Camera, ECR_Block);
	Hull->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	Hull->SetCanEverAffectNavigation(false);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> PlaceholderCube(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (PlaceholderCube.Succeeded())
	{
		Hull->SetStaticMesh(PlaceholderCube.Object);
		// Stretch the 100cm unit cube into something vaguely ship-shaped until real art lands.
		Hull->SetRelativeScale3D(FVector(2.0f, 1.0f, 0.35f));
	}

	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(HullCollision);
	CameraBoom->TargetArmLength = 900.f;
	CameraBoom->SocketOffset = FVector(0.f, 0.f, 200.f);
	// The boom follows the hull, not the controller.
	CameraBoom->bUsePawnControlRotation = false;
	// Pull the camera in when something is between it and the ship. Without this the camera,
	// 9 m back, sank into asteroids smaller than the boom: seen from inside, a mesh's faces are
	// culled, so the rock vanished and the ship appeared to fly through it. The trace ignores
	// the ship itself.
	CameraBoom->bDoCollisionTest = true;
	CameraBoom->ProbeChannel = ECC_Camera;
	CameraBoom->ProbeSize = 25.f;
	CameraBoom->bEnableCameraLag = true;
	CameraBoom->CameraLagSpeed = 8.f;
	// Lag trails by roughly speed / CameraLagSpeed: ~10 m at boost, but a kilometre at orbital
	// speeds, and the whole distance after a teleport. Cap it so the ship stays in frame.
	CameraBoom->CameraLagMaxDistance = 1500.f;

	ChaseCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("ChaseCamera"));
	ChaseCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	ChaseCamera->bUsePawnControlRotation = false;

	// On the unscaled root rather than the hull so it does not inherit the placeholder's scale.
	// The placeholder hull ends at X = 100 cm; the hull is hidden in cockpit view (see
	// SetCockpitView), so sitting just inside the nose never shows its inner faces.
	CockpitCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("CockpitCamera"));
	CockpitCamera->SetupAttachment(HullCollision);
	CockpitCamera->SetRelativeLocation(FVector(90.f, 0.f, 15.f));
	CockpitCamera->SetFieldOfView(90.f);
	CockpitCamera->bUsePawnControlRotation = false;
	// The view comes from the first active camera component, so only one may be active.
	CockpitCamera->SetAutoActivate(false);

	PilotCharacterClass = APlayerCharacter::StaticClass();

	EngineAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("EngineAudio"));
	EngineAudio->SetupAttachment(HullCollision);
	// Silent until the engine actually pushes; UpdateEngineAudio starts and stops it.
	EngineAudio->SetAutoActivate(false);
	// The player's own engine: heard the same from chase and cockpit camera, not positioned.
	EngineAudio->bAllowSpatialization = false;
	// Opened up with engine load in UpdateEngineAudio, so light thrust sounds muffled and distant.
	EngineAudio->bEnableLowPassFilter = true;
	EngineAudio->LowPassFilterFrequency = EngineLowPassIdleHz;

	SpaceDust = CreateDefaultSubobject<USpaceDustComponent>(TEXT("SpaceDust"));
	SpaceDust->SetupAttachment(HullCollision);
}

void ASpaceshipPawn::BeginPlay()
{
	Super::BeginPlay();

	ChaseCameraBaseLocation = ChaseCamera->GetRelativeLocation();
	CockpitCameraBaseLocation = CockpitCamera->GetRelativeLocation();
	BaseArmLength = CameraBoom->TargetArmLength;
	BaseSocketOffset = CameraBoom->SocketOffset;
	BaseChaseFov = ChaseCamera->FieldOfView;
	BaseCockpitFov = CockpitCamera->FieldOfView;

	if (!EngineLoopSound)
	{
		EngineLoopSound = SpaceshipPawnDefaults::LoadOptional<USoundBase>(SpaceshipPawnDefaults::EngineLoopSoundPath);
	}
	if (EngineLoopSound)
	{
		EngineAudio->SetSound(EngineLoopSound);
	}
	else
	{
		UE_LOG(LogSpaceship, Warning, TEXT("%s has no engine sound: %s not found."),
			*GetName(), SpaceshipPawnDefaults::EngineLoopSoundPath);
	}
	SetupAudioLayers();
	SetupShipLights();
}

void ASpaceshipPawn::SnapCameraToShip()
{
	// The spring arm stores its lagged location every update; one update without lag stores the
	// real one. Two ticks, because the arm may update before or after this pawn in a frame.
	CameraBoom->bEnableCameraLag = false;
	CameraSnapTicks = 2;
}

void ASpaceshipPawn::SetCockpitView(bool bCockpit)
{
	bCockpitView = bCockpit;
	ChaseCamera->SetActive(!bCockpit);
	CockpitCamera->SetActive(bCockpit);
	// Only hidden from this pawn's own view: other players and shadows still see the hull.
	Hull->SetOwnerNoSee(bCockpit && bHideHullInCockpit);
}

// -------------------------------------------------------------------------------------------
// Input
// -------------------------------------------------------------------------------------------

void ASpaceshipPawn::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	ResolveInputAssets();

	UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(PlayerInputComponent);
	if (!Input)
	{
		UE_LOG(LogSpaceship, Error,
			TEXT("%s expects an UEnhancedInputComponent. Check DefaultInputComponentClass in DefaultInput.ini."),
			*GetName());
		return;
	}

	auto BindAxis = [this, Input](UInputAction* Action, ESpaceshipAxis Axis)
	{
		if (!Action)
		{
			return;
		}
		Input->BindAction(Action, ETriggerEvent::Triggered, this, &ASpaceshipPawn::HandleAxisTriggered, Axis);
		// Without these the axis would stay latched at its last value after the key comes up.
		Input->BindAction(Action, ETriggerEvent::Completed, this, &ASpaceshipPawn::HandleAxisCompleted, Axis);
		Input->BindAction(Action, ETriggerEvent::Canceled, this, &ASpaceshipPawn::HandleAxisCompleted, Axis);
	};

	BindAxis(ThrustAction, ESpaceshipAxis::Thrust);
	BindAxis(StrafeAction, ESpaceshipAxis::Strafe);
	BindAxis(LiftAction, ESpaceshipAxis::Lift);
	BindAxis(RollAction, ESpaceshipAxis::Roll);

	if (LookAction)
	{
		// No Completed binding: LookInput is cleared every tick, see UpdateAngularMotion.
		Input->BindAction(LookAction, ETriggerEvent::Triggered, this, &ASpaceshipPawn::HandleLook);
	}

	if (MouseLookAction)
	{
		Input->BindAction(MouseLookAction, ETriggerEvent::Triggered, this, &ASpaceshipPawn::HandleMouseLook);
	}

	if (ToggleCameraAction)
	{
		// The action carries a Pressed trigger, so Triggered fires once per key press.
		Input->BindAction(ToggleCameraAction, ETriggerEvent::Triggered, this, &ASpaceshipPawn::HandleToggleCamera);
	}

	if (BoostAction)
	{
		Input->BindAction(BoostAction, ETriggerEvent::Triggered, this, &ASpaceshipPawn::HandleBoost);
		Input->BindAction(BoostAction, ETriggerEvent::Completed, this, &ASpaceshipPawn::HandleBoostCompleted);
		Input->BindAction(BoostAction, ETriggerEvent::Canceled, this, &ASpaceshipPawn::HandleBoostCompleted);
	}

	if (InteractAction)
	{
		Input->BindAction(InteractAction, ETriggerEvent::Started, this, &ASpaceshipPawn::HandleInteract);
	}

	if (!ToggleHudAction)
	{
		ToggleHudAction = SpaceshipPawnDefaults::LoadOptional<UInputAction>(SpaceshipPawnDefaults::ToggleHudActionPath);
	}
	if (ToggleHudAction)
	{
		Input->BindAction(ToggleHudAction, ETriggerEvent::Started, this, &ASpaceshipPawn::HandleToggleHud);
	}

	if (FlightAssistAction)
	{
		Input->BindAction(FlightAssistAction, ETriggerEvent::Started, this, &ASpaceshipPawn::HandleFlightAssist);
	}
	if (CruiseAction)
	{
		Input->BindAction(CruiseAction, ETriggerEvent::Started, this, &ASpaceshipPawn::HandleCruise);
	}
	if (AllStopAction)
	{
		Input->BindAction(AllStopAction, ETriggerEvent::Started, this, &ASpaceshipPawn::HandleAllStop);
	}
	if (CameraZoomAction)
	{
		Input->BindAction(CameraZoomAction, ETriggerEvent::Triggered, this, &ASpaceshipPawn::HandleCameraZoom);
	}

	if (FreeLookAction)
	{
		Input->BindAction(FreeLookAction, ETriggerEvent::Started, this, &ASpaceshipPawn::HandleFreeLookStarted);
		Input->BindAction(FreeLookAction, ETriggerEvent::Completed, this, &ASpaceshipPawn::HandleFreeLookCompleted);
		Input->BindAction(FreeLookAction, ETriggerEvent::Canceled, this, &ASpaceshipPawn::HandleFreeLookCompleted);
	}

	const APlayerController* PlayerController = Cast<APlayerController>(GetController());
	if (!PlayerController)
	{
		return;
	}

	if (UEnhancedInputLocalPlayerSubsystem* Subsystem =
		ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PlayerController->GetLocalPlayer()))
	{
		if (FlightMappingContext)
		{
			Subsystem->AddMappingContext(FlightMappingContext, MappingContextPriority);
		}
		if (MouseMappingContext)
		{
			// One above the flight context: its mouse mapping consumes the mouse there.
			Subsystem->AddMappingContext(MouseMappingContext, MappingContextPriority + 1);
		}
		// The hand-authored IMC_Spaceship may predate F / right mouse button (their add_*.py
		// scripts not run yet): map whatever is missing in a small runtime context.
		auto IsMapped = [this](const UInputAction* Action)
		{
			return FlightMappingContext->GetMappings().ContainsByPredicate(
				[Action](const FEnhancedActionKeyMapping& Mapping) { return Mapping.Action == Action; });
		};
		if (FlightMappingContext && !InteractMappingContext)
		{
			InteractMappingContext = NewObject<UInputMappingContext>(this, FName(TEXT("IMC_SpaceshipExtras_Runtime")));
			if (InteractAction && !IsMapped(InteractAction))
			{
				InteractMappingContext->MapKey(InteractAction, EKeys::F);
			}
			if (FreeLookAction && !IsMapped(FreeLookAction))
			{
				InteractMappingContext->MapKey(FreeLookAction, EKeys::RightMouseButton);
			}
			if (ToggleHudAction && !IsMapped(ToggleHudAction))
			{
				InteractMappingContext->MapKey(ToggleHudAction, EKeys::H);
			}
			if (FlightAssistAction && !IsMapped(FlightAssistAction))
			{
				InteractMappingContext->MapKey(FlightAssistAction, EKeys::V);
			}
			if (CruiseAction && !IsMapped(CruiseAction))
			{
				InteractMappingContext->MapKey(CruiseAction, EKeys::J);
			}
			if (AllStopAction && !IsMapped(AllStopAction))
			{
				InteractMappingContext->MapKey(AllStopAction, EKeys::X);
			}
			if (CameraZoomAction && !IsMapped(CameraZoomAction))
			{
				InteractMappingContext->MapKey(CameraZoomAction, EKeys::MouseWheelAxis);
			}
		}
		if (InteractMappingContext && InteractMappingContext->GetMappings().Num() > 0)
		{
			Subsystem->AddMappingContext(InteractMappingContext, MappingContextPriority);
		}
	}
}

void ASpaceshipPawn::UnPossessed()
{
	// Remove this ship's contexts while the controller is still known: the mouse context would
	// otherwise keep consuming the mouse after the pilot got out.
	if (const APlayerController* PlayerController = Cast<APlayerController>(GetController()))
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem =
			ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PlayerController->GetLocalPlayer()))
		{
			for (UInputMappingContext* Context : { FlightMappingContext.Get(), MouseMappingContext.Get(), InteractMappingContext.Get() })
			{
				if (Context)
				{
					Subsystem->RemoveMappingContext(Context);
				}
			}
		}
	}
	ClearPilotInput();
	Super::UnPossessed();
}

void ASpaceshipPawn::ResolveInputAssets()
{
	using namespace SpaceshipPawnDefaults;

	// Anything the designer assigned on the Blueprint wins; then authored assets in /Game/Input.
	if (!FlightMappingContext)
	{
		FlightMappingContext = LoadOptional<UInputMappingContext>(MappingContextPath);
	}
	if (!ThrustAction)
	{
		ThrustAction = LoadOptional<UInputAction>(ThrustActionPath);
	}
	if (!StrafeAction)
	{
		StrafeAction = LoadOptional<UInputAction>(StrafeActionPath);
	}
	if (!LiftAction)
	{
		LiftAction = LoadOptional<UInputAction>(LiftActionPath);
	}
	if (!RollAction)
	{
		RollAction = LoadOptional<UInputAction>(RollActionPath);
	}
	if (!LookAction)
	{
		LookAction = LoadOptional<UInputAction>(LookActionPath);
	}
	if (!ToggleCameraAction)
	{
		ToggleCameraAction = LoadOptional<UInputAction>(ToggleCameraActionPath);
	}
	if (!BoostAction)
	{
		BoostAction = LoadOptional<UInputAction>(BoostActionPath);
	}
	if (!InteractAction)
	{
		InteractAction = LoadOptional<UInputAction>(InteractActionPath);
	}
	if (!FreeLookAction)
	{
		FreeLookAction = LoadOptional<UInputAction>(FreeLookActionPath);
	}
	if (!MouseLookAction)
	{
		MouseLookAction = LoadOptional<UInputAction>(MouseLookActionPath);
	}
	if (!MouseMappingContext)
	{
		MouseMappingContext = LoadOptional<UInputMappingContext>(MouseMappingContextPath);
	}

	// Newer actions: authored assets once Tools/Assets/add_flight_modes_input.py has run, otherwise
	// runtime stand-ins, mapped through the extras context in SetupPlayerInputComponent.
	auto LoadOrMake = [this](TObjectPtr<UInputAction>& Action, const TCHAR* Path, const TCHAR* RuntimeName, EInputActionValueType ValueType)
	{
		if (!Action)
		{
			Action = LoadOptional<UInputAction>(Path);
		}
		if (!Action)
		{
			Action = NewObject<UInputAction>(this, FName(RuntimeName));
			Action->ValueType = ValueType;
		}
	};
	LoadOrMake(FlightAssistAction, FlightAssistActionPath, TEXT("IA_FlightAssist_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(CruiseAction, CruiseActionPath, TEXT("IA_CruiseDrive_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(AllStopAction, AllStopActionPath, TEXT("IA_AllStop_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(CameraZoomAction, CameraZoomActionPath, TEXT("IA_CameraZoom_Runtime"), EInputActionValueType::Axis1D);

	BuildProceduralInputAssets();
}

void ASpaceshipPawn::BuildProceduralInputAssets()
{
	const bool bNeedsAnything = !FlightMappingContext || !ThrustAction || !StrafeAction || !LiftAction
		|| !RollAction || !LookAction || !ToggleCameraAction || !BoostAction || !MouseLookAction
		|| !MouseMappingContext || !InteractAction || !FreeLookAction;
	if (!bNeedsAnything)
	{
		return;
	}

	UE_LOG(LogSpaceship, Warning,
		TEXT("%s is falling back to procedurally built Enhanced Input objects. Author IMC_Spaceship and the ")
		TEXT("IA_* actions in /Game/Input (or assign them on a Blueprint child) to make the bindings editable."),
		*GetName());

	auto MakeAction = [this](const TCHAR* Name, EInputActionValueType ValueType,
		EInputActionAccumulationBehavior Accumulation) -> UInputAction*
	{
		UInputAction* Action = NewObject<UInputAction>(this, FName(Name));
		Action->ValueType = ValueType;
		Action->AccumulationBehavior = Accumulation;
		return Action;
	};

	// Opposing keys on one axis (W and S) have to cancel, which is what Cumulative does.
	// The default, TakeHighestAbsoluteValue, would pick one of +1 and -1 arbitrarily.
	const EInputActionAccumulationBehavior Opposed = EInputActionAccumulationBehavior::Cumulative;

	if (!ThrustAction)
	{
		ThrustAction = MakeAction(TEXT("IA_Thrust_Runtime"), EInputActionValueType::Axis1D, Opposed);
	}
	if (!StrafeAction)
	{
		StrafeAction = MakeAction(TEXT("IA_Strafe_Runtime"), EInputActionValueType::Axis1D, Opposed);
	}
	if (!LiftAction)
	{
		LiftAction = MakeAction(TEXT("IA_Lift_Runtime"), EInputActionValueType::Axis1D, Opposed);
	}
	if (!RollAction)
	{
		RollAction = MakeAction(TEXT("IA_Roll_Runtime"), EInputActionValueType::Axis1D, Opposed);
	}
	if (!LookAction)
	{
		// Mouse and stick feed the same action, so here the larger of the two should win.
		LookAction = MakeAction(TEXT("IA_Look_Runtime"), EInputActionValueType::Axis2D,
			EInputActionAccumulationBehavior::TakeHighestAbsoluteValue);
	}
	if (!ToggleCameraAction)
	{
		ToggleCameraAction = MakeAction(TEXT("IA_ToggleCamera_Runtime"), EInputActionValueType::Boolean,
			EInputActionAccumulationBehavior::TakeHighestAbsoluteValue);
		ToggleCameraAction->Triggers.Add(NewObject<UInputTriggerPressed>(ToggleCameraAction));
	}
	if (!BoostAction)
	{
		BoostAction = MakeAction(TEXT("IA_Boost_Runtime"), EInputActionValueType::Boolean,
			EInputActionAccumulationBehavior::TakeHighestAbsoluteValue);
	}
	if (!InteractAction)
	{
		InteractAction = MakeAction(TEXT("IA_Interact_Runtime"), EInputActionValueType::Boolean,
			EInputActionAccumulationBehavior::TakeHighestAbsoluteValue);
		InteractAction->Triggers.Add(NewObject<UInputTriggerPressed>(InteractAction));
	}
	if (!FreeLookAction)
	{
		FreeLookAction = MakeAction(TEXT("IA_FreeLook_Runtime"), EInputActionValueType::Boolean,
			EInputActionAccumulationBehavior::TakeHighestAbsoluteValue);
	}
	if (!MouseLookAction)
	{
		MouseLookAction = MakeAction(TEXT("IA_LookMouse_Runtime"), EInputActionValueType::Axis2D,
			EInputActionAccumulationBehavior::TakeHighestAbsoluteValue);
	}
	if (!MouseMappingContext)
	{
		MouseMappingContext = NewObject<UInputMappingContext>(this, FName(TEXT("IMC_SpaceshipMouse_Runtime")));
		MouseMappingContext->MapKey(MouseLookAction, EKeys::Mouse2D);
	}

	// A context the designer supplied is left alone even if it is missing mappings: silently
	// bolting extra keys onto an authored asset would be worse than a context that does nothing.
	if (FlightMappingContext)
	{
		return;
	}

	FlightMappingContext = NewObject<UInputMappingContext>(this, FName(TEXT("IMC_Spaceship_Runtime")));

	struct FDefaultMapping
	{
		const UInputAction* Action;
		FKey Key;
		bool bNegate;
	};

	const FDefaultMapping DefaultMappings[] = {
		{ ThrustAction, EKeys::W,                     false },
		{ ThrustAction, EKeys::S,                     true  },
		{ ThrustAction, EKeys::Gamepad_LeftY,         false },
		{ StrafeAction, EKeys::D,                     false },
		{ StrafeAction, EKeys::A,                     true  },
		{ StrafeAction, EKeys::Gamepad_LeftX,         false },
		{ LiftAction,   EKeys::SpaceBar,              false },
		{ LiftAction,   EKeys::LeftControl,           true  },
		{ RollAction,   EKeys::E,                     false },
		{ RollAction,   EKeys::Q,                     true  },
		{ RollAction,   EKeys::Gamepad_RightShoulder, false },
		{ RollAction,   EKeys::Gamepad_LeftShoulder,  true  },
		// The mouse is mapped in MouseMappingContext, not here.
		{ LookAction,   EKeys::Gamepad_Right2D,       false },
		{ ToggleCameraAction, EKeys::C,               false },
		{ BoostAction,  EKeys::LeftShift,             false },
		{ InteractAction, EKeys::F,                   false },
		{ FreeLookAction, EKeys::RightMouseButton,    false },
	};

	for (const FDefaultMapping& Mapping : DefaultMappings)
	{
		FEnhancedActionKeyMapping& KeyMapping = FlightMappingContext->MapKey(Mapping.Action, Mapping.Key);
		if (Mapping.bNegate)
		{
			KeyMapping.Modifiers.Add(NewObject<UInputModifierNegate>(FlightMappingContext));
		}
	}
}

float& ASpaceshipPawn::AxisInput(ESpaceshipAxis Axis)
{
	switch (Axis)
	{
	case ESpaceshipAxis::Strafe:
		return StrafeInput;
	case ESpaceshipAxis::Lift:
		return LiftInput;
	case ESpaceshipAxis::Roll:
		return RollInput;
	case ESpaceshipAxis::Thrust:
	default:
		return ThrustInput;
	}
}

void ASpaceshipPawn::HandleAxisTriggered(const FInputActionValue& Value, ESpaceshipAxis Axis)
{
	AxisInput(Axis) = Value.Get<float>();
}

void ASpaceshipPawn::HandleAxisCompleted(const FInputActionValue& /*Value*/, ESpaceshipAxis Axis)
{
	AxisInput(Axis) = 0.f;
}

void ASpaceshipPawn::HandleLook(const FInputActionValue& Value)
{
	LookInput = Value.Get<FVector2D>();
}

void ASpaceshipPawn::HandleMouseLook(const FInputActionValue& Value)
{
	// Accumulated: every pixel moved between two ticks counts, however events are batched.
	MouseLookDelta += Value.Get<FVector2D>();
}

void ASpaceshipPawn::HandleToggleCamera(const FInputActionValue& /*Value*/)
{
	SetCockpitView(!bCockpitView);
}

void ASpaceshipPawn::HandleBoost(const FInputActionValue& /*Value*/)
{
	bBoostHeld = true;
}

void ASpaceshipPawn::HandleToggleHud(const FInputActionValue& /*Value*/)
{
	ASpaceDebugHUD::CycleDisplayMode();
}

void ASpaceshipPawn::HandleInteract(const FInputActionValue& /*Value*/)
{
	ExitShip();
}

void ASpaceshipPawn::HandleFlightAssist(const FInputActionValue& /*Value*/)
{
	SetFlightAssist(!bFlightAssist);
}

void ASpaceshipPawn::HandleCruise(const FInputActionValue& /*Value*/)
{
	ToggleCruise();
}

void ASpaceshipPawn::HandleAllStop(const FInputActionValue& /*Value*/)
{
	AllStop();
}

void ASpaceshipPawn::HandleCameraZoom(const FInputActionValue& Value)
{
	// One wheel notch is +-1. Up (positive) brings the camera closer / zooms the cockpit in.
	const float Notches = Value.Get<float>();
	if (bCockpitView)
	{
		CockpitZoomTarget = FMath::Clamp(CockpitZoomTarget + 0.2f * Notches, 0.f, 1.f);
	}
	else
	{
		CameraZoomTarget = FMath::Clamp(CameraZoomTarget * FMath::Pow(1.f - CameraZoomStep, Notches), CameraZoomMin, CameraZoomMax);
	}
}

void ASpaceshipPawn::SetFlightAssist(bool bOn)
{
	if (bOn == bFlightAssist)
	{
		return;
	}
	bFlightAssist = bOn;
	if (bOn)
	{
		// Pick the lever up where the ship already flies, so switching back does not brake or lurch.
		const double Forward = LinearVelocity | GetActorForwardVector();
		ThrottleSetting = float(FMath::Clamp(Forward / FMath::Max(double(MaxSpeed), 1.0), -double(MaxReverseThrottle), 1.0));
		bThrottleDetentHold = false;
	}
	UE_LOG(LogSpaceship, Log, TEXT("%s: flight assist %s"), *GetName(), bOn ? TEXT("on") : TEXT("off"));
}

void ASpaceshipPawn::AllStop()
{
	ThrottleSetting = 0.f;
	bThrottleDetentHold = ThrustInput != 0.f;
}

float ASpaceshipPawn::GetCruiseSpoolProgress() const
{
	return CruiseState == ECruiseState::Spooling ? FMath::Clamp(CruiseTimer / FMath::Max(CruiseSpoolSeconds, 0.01f), 0.f, 1.f)
		: CruiseState == ECruiseState::Active ? 1.f : 0.f;
}

// -------------------------------------------------------------------------------------------
// Free look
// -------------------------------------------------------------------------------------------

void ASpaceshipPawn::HandleFreeLookStarted(const FInputActionValue& /*Value*/)
{
	SetFreeLookHeld(true);
}

void ASpaceshipPawn::HandleFreeLookCompleted(const FInputActionValue& /*Value*/)
{
	SetFreeLookHeld(false);
}

void ASpaceshipPawn::SetFreeLookHeld(bool bHeld)
{
	if (bHeld == bFreeLookHeld)
	{
		return;
	}
	bFreeLookHeld = bHeld;
	// Either way the virtual stick starts centred: on press the ship stops turning at once, on
	// release steering resumes from neutral instead of from wherever the stick was left.
	MouseStick = FVector2D::ZeroVector;
	MouseLookDelta = FVector2D::ZeroVector;
	if (bHeld)
	{
		AngularVelocity.Y = 0.0;
		AngularVelocity.Z = 0.0;
		// Start from where the camera still is (a quick re-press during the swing back).
		FreeLookTarget = FreeLookAngles;
	}
	else
	{
		// Yaw may have gone round several times; the camera looks the same at the unwound angle,
		// and from there it swings back the shorter way.
		FreeLookAngles.X = FMath::UnwindDegrees(FreeLookAngles.X);
		FreeLookTarget = FVector2D::ZeroVector;
	}
}

void ASpaceshipPawn::UpdateFreeLook(float DeltaSeconds)
{
	if (bFreeLookHeld)
	{
		// Mouse up looks up; pitch is not affected by bInvertPitch, which is about steering.
		FreeLookTarget.X += MouseLookDelta.X * FreeLookSensitivity;
		if (FreeLookMaxYawDeg < 180.f)
		{
			FreeLookTarget.X = FMath::Clamp(FreeLookTarget.X, -FreeLookMaxYawDeg, FreeLookMaxYawDeg);
		}
		FreeLookTarget.Y = FMath::Clamp(FreeLookTarget.Y + MouseLookDelta.Y * FreeLookSensitivity, -FreeLookMaxPitchDeg, FreeLookMaxPitchDeg);
		MouseLookDelta = FVector2D::ZeroVector;
		LookInput = FVector2D::ZeroVector;
	}

	const FVector2D Previous = FreeLookAngles;
	const float Rate = bFreeLookHeld ? FreeLookFollowRate : FreeLookReturnRate;
	FreeLookAngles += (FreeLookTarget - FreeLookAngles) * (1.0 - FMath::Exp(-Rate * DeltaSeconds));
	if (!bFreeLookHeld && FreeLookAngles.GetAbsMax() < 0.05)
	{
		FreeLookAngles = FVector2D::ZeroVector;
	}
	if (FreeLookAngles == Previous)
	{
		return;  // nothing moved (the usual case: not free looking)
	}

	// Chase: the boom swings around the ship. Cockpit: the head turns.
	const FRotator Offset(float(FreeLookAngles.Y), float(FreeLookAngles.X), 0.f);
	CameraBoom->SetRelativeRotation(Offset);
	CockpitCamera->SetRelativeRotation(Offset);
}

TArray<FVector> ASpaceshipPawn::DebugSimulateFreeLook(const TArray<FVector>& Frames)
{
	const float Step = 1.f / 60.f;
	TArray<FVector> Result;
	for (const FVector& Frame : Frames)
	{
		SetFreeLookHeld(Frame.Z > 0.5);
		MouseLookDelta += FVector2D(Frame.X, Frame.Y);
		UpdateFreeLook(Step);
		UpdateAngularMotion(Step);
		Result.Add(FVector(FreeLookAngles.X, FreeLookAngles.Y, bFreeLookHeld ? 1.0 : 0.0));
		const FRotator Rotation = GetActorRotation();
		Result.Add(FVector(Rotation.Pitch, Rotation.Yaw, Rotation.Roll));
	}
	return Result;
}

void ASpaceshipPawn::ClearPilotInput()
{
	SetFreeLookHeld(false);
	ThrustInput = 0.f;
	StrafeInput = 0.f;
	LiftInput = 0.f;
	RollInput = 0.f;
	LookInput = FVector2D::ZeroVector;
	MouseLookDelta = FVector2D::ZeroVector;
	MouseStick = FVector2D::ZeroVector;
	bBoostHeld = false;
}

// -------------------------------------------------------------------------------------------
// Exit and boarding
// -------------------------------------------------------------------------------------------

bool ASpaceshipPawn::CanExit() const
{
	return IsLanded() && IsPlayerControlled() && PilotCharacterClass != nullptr;
}

double ASpaceshipPawn::GetDistanceToHull(const FVector& Location) const
{
	const FVector Local = HullCollision->GetComponentTransform().InverseTransformPositionNoScale(Location);
	const FVector Extent = HullCollision->GetScaledBoxExtent();
	const FVector Outside(
		FMath::Max(FMath::Abs(Local.X) - Extent.X, 0.0),
		FMath::Max(FMath::Abs(Local.Y) - Extent.Y, 0.0),
		FMath::Max(FMath::Abs(Local.Z) - Extent.Z, 0.0));
	return Outside.Size();
}

FVector ASpaceshipPawn::ComputeSideExitLocation(const FVector& ShipLocation, const FRotator& ShipRotation, const FVector& HullExtent, float CapsuleRadius, float ClearanceCm)
{
	const FQuat Rotation = ShipRotation.Quaternion();
	return ShipLocation + Rotation.GetRightVector() * (HullExtent.Y + CapsuleRadius + ClearanceCm);
}

TArray<FVector> ASpaceshipPawn::GetExitCandidates() const
{
	TArray<FVector> Candidates;
	static const FName ExitSockets[] = { FName(TEXT("Exit")), FName(TEXT("SOCKET_Exit")) };
	if (const FName* Socket = Algo::FindByPredicate(ExitSockets, [this](const FName& Name) { return Hull->DoesSocketExist(Name); }))
	{
		Candidates.Add(Hull->GetSocketLocation(*Socket));
	}

	// Then around the hull: its mesh bounds where there is a mesh (wings included), else the box.
	const ACharacter* PilotDefaults = Cast<ACharacter>(PilotCharacterClass ? PilotCharacterClass->GetDefaultObject() : nullptr);
	const float CapsuleRadius = PilotDefaults ? PilotDefaults->GetSimpleCollisionRadius() : 42.f;
	FVector Center = GetActorLocation();
	FVector Extent = HullCollision->GetScaledBoxExtent();
	if (const UStaticMesh* Mesh = Hull->GetStaticMesh())
	{
		const FBox LocalBox = Mesh->GetBoundingBox().TransformBy(Hull->GetRelativeTransform());
		Center = GetActorTransform().TransformPosition(LocalBox.GetCenter());
		Extent = LocalBox.GetExtent();
	}
	const FQuat Rotation = GetActorQuat();
	const TPair<FVector, double> Directions[] = {
		{ Rotation.GetRightVector(), Extent.Y },
		{ -Rotation.GetRightVector(), Extent.Y },
		{ -Rotation.GetForwardVector(), Extent.X },
		{ Rotation.GetForwardVector(), Extent.X },
	};
	for (const double Extra : { 0.0, 300.0, 800.0 })
	{
		for (const TPair<FVector, double>& Direction : Directions)
		{
			Candidates.Add(Center + Direction.Key * (Direction.Value + CapsuleRadius + ExitClearanceCm + Extra));
		}
	}
	return Candidates;
}

bool ASpaceshipPawn::IsExitSpotFree(const FVector& Location, const FVector& Up, float CapsuleRadius, float CapsuleHalfHeight) const
{
	const UWorld* World = GetWorld();
	if (!World)
	{
		return true;
	}
	// A slightly smaller capsule lifted off the ground: uneven terrain under the feet must not
	// count as blocked, a wall, rock or the hull must. The ship itself is deliberately not
	// ignored; its hull mesh collision is exactly what the pilot must not appear inside.
	const double Lift = 30.0;
	const FCollisionShape Shape = FCollisionShape::MakeCapsule(FMath::Max(CapsuleRadius - 4.f, 10.f), FMath::Max(CapsuleHalfHeight - 10.f, 20.f));
	FCollisionQueryParams Params(SCENE_QUERY_STAT(SpaceshipExitSpot), false);
	return !World->OverlapBlockingTestByChannel(Location + Up * Lift, FQuat::FindBetweenNormals(FVector::UpVector, Up),
		ECC_Pawn, Shape, Params);
}

FTransform ASpaceshipPawn::ComputeExitTransform() const
{
	const FVector Up = bHasEnvironment ? Environment.Up : GetActorUpVector();
	const ACharacter* PilotDefaults = Cast<ACharacter>(PilotCharacterClass ? PilotCharacterClass->GetDefaultObject() : nullptr);
	const float CapsuleRadius = PilotDefaults ? PilotDefaults->GetSimpleCollisionRadius() : 42.f;
	const float CapsuleHalfHeight = PilotDefaults ? PilotDefaults->GetSimpleCollisionHalfHeight() : 96.f;

	FVector Flat = FVector::VectorPlaneProject(GetActorForwardVector(), Up).GetSafeNormal();
	if (Flat.IsNearlyZero())
	{
		Flat = FVector::VectorPlaneProject(GetActorUpVector(), Up).GetSafeNormal();
	}
	const FQuat Facing = FRotationMatrix::MakeFromXZ(Flat, Up).ToQuat();

	auto OnGround = [&](FVector Location)
	{
		// Stand on the terrain there, not at the height of the ship's centre or a hatch in the air.
		FVector SurfacePoint;
		FVector SurfaceNormal;
		if (const ACelestialBody* Body = NearestBody.Get())
		{
			if (Body->GetSurfaceFrame(Location, CapsuleRadius, SurfacePoint, SurfaceNormal))
			{
				const double AboveGround = (Location - SurfacePoint) | Up;
				Location += Up * (CapsuleHalfHeight + 20.0 - AboveGround);
			}
		}
		return Location;
	};

	const TArray<FVector> Candidates = GetExitCandidates();
	for (const FVector& Candidate : Candidates)
	{
		const FVector Location = OnGround(Candidate);
		if (IsExitSpotFree(Location, Up, CapsuleRadius, CapsuleHalfHeight))
		{
			return FTransform(Facing, Location);
		}
	}
	// Nowhere free (boxed in): the farthest spot beside the ship, where at least the hull is not.
	const FVector Fallback = Candidates.Num() > 0 ? Candidates.Last(3) : GetActorLocation() + GetActorRightVector() * 1000.0;
	UE_LOG(LogSpaceship, Warning, TEXT("%s: no free exit spot among %d candidates; using %s"), *GetName(), Candidates.Num(), *Fallback.ToString());
	return FTransform(Facing, OnGround(Fallback));
}

APawn* ASpaceshipPawn::ExitShip()
{
	APlayerController* PlayerController = Cast<APlayerController>(GetController());
	if (!CanExit() || !PlayerController)
	{
		return nullptr;
	}

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
	const FTransform ExitTransform = ComputeExitTransform();
	APawn* Pilot = GetWorld()->SpawnActor<APawn>(PilotCharacterClass, ExitTransform, Params);
	if (!Pilot)
	{
		UE_LOG(LogSpaceship, Warning, TEXT("%s: could not spawn %s at the exit"), *GetName(), *GetNameSafe(PilotCharacterClass));
		return nullptr;
	}
	PlayerController->Possess(Pilot);
	if (APlayerCharacter* Character = Cast<APlayerCharacter>(Pilot))
	{
		Character->FaceDirection(ExitTransform.GetRotation().GetForwardVector());
	}
	UE_LOG(LogSpaceship, Log, TEXT("%s: pilot out at %s"), *GetName(), *ExitTransform.GetLocation().ToString());
	return Pilot;
}

void ASpaceshipPawn::OnBoarded()
{
	ClearPilotInput();
	SnapCameraToShip();
}

void ASpaceshipPawn::HandleBoostCompleted(const FInputActionValue& /*Value*/)
{
	bBoostHeld = false;
}

// -------------------------------------------------------------------------------------------
// Flight model
// -------------------------------------------------------------------------------------------

void ASpaceshipPawn::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	StepFlight(DeltaSeconds);
	UpdateCameraEffects(DeltaSeconds);
	UpdateEngineAudio(DeltaSeconds);
	UpdateShipLights(DeltaSeconds);
	UpdateSpaceDust(DeltaSeconds);

	if (CameraSnapTicks > 0 && --CameraSnapTicks == 0)
	{
		CameraBoom->bEnableCameraLag = true;
	}
}

void ASpaceshipPawn::StepFlight(float DeltaSeconds)
{
	UpdateEnvironment(DeltaSeconds);
	// The lever before landing: a lever left open counts as engines on.
	UpdateThrottle(DeltaSeconds);
	UpdateLanding(DeltaSeconds);
	UpdateBoost(DeltaSeconds);
	UpdateCruise(DeltaSeconds);
	// Before steering: while held it takes the mouse movement for itself.
	UpdateFreeLook(DeltaSeconds);
	if (LandingState == ELandingState::Landed)
	{
		UpdateLandedMotion(DeltaSeconds);
	}
	else
	{
		// Rotate first so this frame's thrust is applied along the heading the player just commanded.
		UpdateAngularMotion(DeltaSeconds);
		UpdateLinearMotion(DeltaSeconds);
	}
}

FVector ASpaceshipPawn::DebugStepFlight(float DeltaSeconds, float Thrust, float Strafe, float Lift, bool bBoost)
{
	ThrustInput = Thrust;
	StrafeInput = Strafe;
	LiftInput = Lift;
	bBoostHeld = bBoost;
	StepFlight(DeltaSeconds);
	return LinearVelocity;
}

// -------------------------------------------------------------------------------------------
// Throttle, boost and cruise
// -------------------------------------------------------------------------------------------

void ASpaceshipPawn::UpdateThrottle(float DeltaSeconds)
{
	if (!bFlightAssist)
	{
		return;  // decoupled: W / S fire the main engine directly
	}
	if (ThrustInput == 0.f)
	{
		bThrottleDetentHold = false;
		return;
	}
	if (bThrottleDetentHold)
	{
		return;
	}
	const float Previous = ThrottleSetting;
	float Next = FMath::Clamp(Previous + ThrustInput * ThrottleRate * DeltaSeconds, -MaxReverseThrottle, 1.f);
	// A detent at zero: pulling back from forward (or pushing up from reverse) stops the lever at 0
	// until the key is pressed again, so braking to a stop never rolls on into reverse.
	if ((Previous > 0.f && Next < 0.f) || (Previous < 0.f && Next > 0.f))
	{
		Next = 0.f;
		bThrottleDetentHold = true;
	}
	ThrottleSetting = Next;
}

void ASpaceshipPawn::UpdateBoost(float DeltaSeconds)
{
	const bool bWasActive = bBoostActive;
	if (bBoostLocked && BoostEnergy >= BoostUnlockFraction)
	{
		bBoostLocked = false;
	}
	const bool bForward = bFlightAssist ? ThrottleSetting >= 0.f : ThrustInput > 0.f;
	bBoostActive = bBoostHeld && bForward && !bBoostLocked && BoostEnergy > 0.f
		&& CruiseState == ECruiseState::Off && LandingState != ELandingState::Landed;

	if (bBoostActive)
	{
		BoostEnergy = FMath::Max(0.f, BoostEnergy - DeltaSeconds / BoostDurationSeconds);
		BoostRechargeWait = BoostRechargeDelaySeconds;
		if (BoostEnergy <= 0.f)
		{
			bBoostLocked = true;
			bBoostActive = false;
		}
	}
	else
	{
		BoostRechargeWait = FMath::Max(0.f, BoostRechargeWait - DeltaSeconds);
		if (BoostRechargeWait <= 0.f)
		{
			BoostEnergy = FMath::Min(1.f, BoostEnergy + DeltaSeconds / BoostRechargeSeconds);
		}
	}

	if (bBoostActive && !bWasActive)
	{
		CameraKick = FMath::Max(CameraKick, 0.6f);
		PlayOneShot(BoostStartSound);
	}
}

float ASpaceshipPawn::ComputeCruiseSpeedLimit(float AltitudeAboveTerrainCm, float AtmosphereDensity, bool bNearBody) const
{
	if (!bNearBody)
	{
		return CruiseMaxSpeed;
	}
	const double Thin = 1.0 - CruiseAtmosphereSlowdown * FMath::Sqrt(FMath::Clamp(double(AtmosphereDensity), 0.0, 1.0));
	return float(FMath::Clamp(double(AltitudeAboveTerrainCm) * CruiseAltitudeRate * Thin, double(CruiseMinSpeed), double(FMath::Max(CruiseMinSpeed, CruiseMaxSpeed))));
}

ECruiseBlocker ASpaceshipPawn::EvaluateCruiseEngage() const
{
	if (LandingState == ELandingState::Landed)
	{
		return ECruiseBlocker::Landed;
	}
	if (bHasEnvironment && Environment.AltitudeAboveTerrainCm < CruiseMinAltitudeM * 100.0)
	{
		return ECruiseBlocker::TooLow;
	}
	return ECruiseBlocker::None;
}

void ASpaceshipPawn::ToggleCruise()
{
	switch (CruiseState)
	{
	case ECruiseState::Off:
	case ECruiseState::Dropping:
		CruiseBlocker = EvaluateCruiseEngage();
		if (CruiseBlocker != ECruiseBlocker::None)
		{
			CruiseMessageSeconds = 3.f;
			return;
		}
		CruiseState = ECruiseState::Spooling;
		CruiseTimer = 0.f;
		CruiseMessageSeconds = 0.f;
		if (CruiseChargeAudio)
		{
			CruiseChargeAudio->Stop();
		}
		CruiseChargeAudio = PlayOneShot(CruiseChargeSound);
		break;

	case ECruiseState::Spooling:
		CruiseState = ECruiseState::Off;
		CruiseBlocker = ECruiseBlocker::Pilot;
		CruiseMessageSeconds = 2.f;
		if (CruiseChargeAudio)
		{
			CruiseChargeAudio->FadeOut(0.25f, 0.f);
			CruiseChargeAudio = nullptr;
		}
		break;

	case ECruiseState::Active:
		BeginCruiseDrop(ECruiseBlocker::Pilot);
		break;
	}
}

void ASpaceshipPawn::BeginCruiseDrop(ECruiseBlocker Reason)
{
	CruiseState = ECruiseState::Dropping;
	CruiseTimer = 0.f;
	CruiseBlocker = Reason;
	CruiseMessageSeconds = 3.f;
	CameraKick = 1.f;
	PlayOneShot(CruiseDropSound);
	UE_LOG(LogSpaceship, Log, TEXT("%s: cruise drop (%s) at %.0f m/s"), *GetName(),
		Reason == ECruiseBlocker::TooLow ? TEXT("too low") : TEXT("pilot"), LinearVelocity.Size() / 100.0);
}

void ASpaceshipPawn::UpdateCruise(float DeltaSeconds)
{
	CruiseMessageSeconds = FMath::Max(0.f, CruiseMessageSeconds - DeltaSeconds);
	CruiseSpeedLimit = ComputeCruiseSpeedLimit(bHasEnvironment ? float(Environment.AltitudeAboveTerrainCm) : 0.f,
		bHasEnvironment ? Environment.AtmosphereDensity : 0.f, bHasEnvironment);

	switch (CruiseState)
	{
	case ECruiseState::Spooling:
	{
		const ECruiseBlocker Blocker = EvaluateCruiseEngage();
		if (Blocker != ECruiseBlocker::None)
		{
			CruiseState = ECruiseState::Off;
			CruiseBlocker = Blocker;
			CruiseMessageSeconds = 3.f;
			if (CruiseChargeAudio)
			{
				CruiseChargeAudio->FadeOut(0.25f, 0.f);
				CruiseChargeAudio = nullptr;
			}
			break;
		}
		CruiseTimer += DeltaSeconds;
		if (CruiseTimer >= CruiseSpoolSeconds)
		{
			CruiseState = ECruiseState::Active;
			CruiseTimer = 0.f;
			CruiseBlocker = ECruiseBlocker::None;
			// An idle lever would engage the drive at a crawl; start at three quarters.
			ThrottleSetting = FMath::Max(ThrottleSetting, 0.75f);
			bBoostActive = false;
			CameraKick = 1.f;
			CruiseChargeAudio = nullptr;
			PlayOneShot(CruiseEngageSound);
			UE_LOG(LogSpaceship, Log, TEXT("%s: cruise engaged, limit %.0f m/s"), *GetName(), CruiseSpeedLimit / 100.0);
		}
		break;
	}
	case ECruiseState::Active:
		if (bHasEnvironment && Environment.AltitudeAboveTerrainCm < CruiseDropAltitudeM * 100.0)
		{
			BeginCruiseDrop(ECruiseBlocker::TooLow);
		}
		break;

	case ECruiseState::Dropping:
		CruiseTimer += DeltaSeconds;
		if (CruiseTimer >= CruiseDropSeconds)
		{
			CruiseState = ECruiseState::Off;
			CruiseTimer = 0.f;
		}
		break;

	default:
		break;
	}
}

// -------------------------------------------------------------------------------------------
// Motion
// -------------------------------------------------------------------------------------------

void ASpaceshipPawn::UpdateAngularMotion(float DeltaSeconds)
{
	// Mouse as a virtual joystick. Turning the per-frame delta straight into a turn rate (as
	// before) made steering frame-rate dependent: at 120 FPS each frame sees half the pixels, so
	// the same hand movement turned half as fast. Pushing a spring-centred stick instead makes
	// the steady-state deflection depend on mouse speed per second, not per frame.
	MouseStick *= FMath::Exp(-MouseRecenterRate * DeltaSeconds);
	MouseStick += MouseLookDelta * MouseSensitivity;
	MouseStick.X = FMath::Clamp(MouseStick.X, -1., 1.);
	MouseStick.Y = FMath::Clamp(MouseStick.Y, -1., 1.);
	MouseLookDelta = FVector2D::ZeroVector;

	// Stick and mouse are both a fraction of the maximum rotation rate now, so they simply add.
	const FVector2D Command(
		FMath::Clamp(MouseStick.X + LookInput.X, -1., 1.),
		FMath::Clamp(MouseStick.Y + LookInput.Y, -1., 1.));
	const float PitchCommand = bFreeLookHeld ? 0.f : Command.Y * (bInvertPitch ? -1.f : 1.f);
	const float YawCommand = bFreeLookHeld ? 0.f : Command.X;
	// A ship at kilometres per second turns wide.
	const float RateScale = CruiseState == ECruiseState::Active ? CruiseTurnScale : 1.f;

	const FVector TargetRates(
		RollInput * RollRate * RateScale,
		PitchCommand * PitchRate * RateScale,
		YawCommand * YawRate * RateScale);

	AngularVelocity = FMath::VInterpTo(AngularVelocity, TargetRates, DeltaSeconds, AngularResponsiveness);
	if (bFreeLookHeld)
	{
		// Heading frozen where it was; roll (keys) still works, and the flight path is untouched.
		AngularVelocity.Y = 0.0;
		AngularVelocity.Z = 0.0;
	}

	// Local rotation, so pitch/yaw/roll stay relative to the hull. That is what makes this 6DOF
	// rather than an aircraft glued to a horizon, and it sidesteps gimbal lock at the poles.
	AddActorLocalRotation(FRotator(
		AngularVelocity.Y * DeltaSeconds,
		AngularVelocity.Z * DeltaSeconds,
		AngularVelocity.X * DeltaSeconds));

	// A deflected stick re-fires Triggered every frame; clearing means a released stick stops.
	LookInput = FVector2D::ZeroVector;
}

void ASpaceshipPawn::UpdateLinearMotion(float DeltaSeconds)
{
	const FQuat Rotation = GetActorQuat();
	const double Density = bHasEnvironment ? Environment.AtmosphereDensity : 0.0;
	const double DragRate = SpaceLinearDamping + (LinearDamping + QuadraticDrag * LinearVelocity.Size()) * Density;
	const double Gravity = bHasEnvironment ? Environment.GravityCmS2 * GravityScale : 0.0;
	const FVector Up = bHasEnvironment ? FVector(Environment.Up) : FVector::UpVector;
	const float BoostFactor = bBoostActive ? BoostMultiplier : 1.f;

	if (CruiseState == ECruiseState::Active)
	{
		// The drive carries the ship along its nose; thrusters, drag and gravity do not matter at
		// these speeds. Velocity swings onto the nose and the target speed at CruiseResponse.
		const double Target = CruiseSpeedLimit * FMath::Clamp(ThrottleSetting, 0.1f, 1.f);
		const FVector Desired = Rotation.GetForwardVector() * Target;
		LinearVelocity = Desired + (LinearVelocity - Desired) * FMath::Exp(-CruiseResponse * DeltaSeconds);
		// The limit falls as the ground comes closer; never lag behind it on the way down.
		const double Speed = LinearVelocity.Size();
		if (Speed > CruiseSpeedLimit)
		{
			LinearVelocity *= CruiseSpeedLimit / Speed;
		}
		EngineDemand = 0.6f;
	}
	else
	{
		const double ForwardCap = ThrustAcceleration * BoostFactor;
		const double ReverseCap = ThrustAcceleration * ReverseThrustFraction;
		FVector LocalAcceleration;

		if (bFlightAssist)
		{
			// Coupled: the flight computer chases a velocity target with the thrusters it has.
			const double Forward = bBoostActive ? MaxSpeed * BoostMultiplier : ThrottleSetting * MaxSpeed;
			double Lift = LiftInput * LiftSpeedLimit;
			if (LiftInput < 0.f && bHasEnvironment)
			{
				// Descending gets gentler towards the ground, down to LandingDescentSpeed.
				const double Near = FMath::Clamp(Environment.AltitudeAboveTerrainCm / 2000.0, 0.0, 1.0);
				Lift = LiftInput * FMath::Lerp(double(LandingDescentSpeed), double(LiftSpeedLimit), Near);
			}
			const FVector DesiredLocal(Forward, StrafeInput * StrafeSpeedLimit, Lift);
			const FVector VelocityLocal = Rotation.UnrotateVector(LinearVelocity);

			// Hovering over the ground with the engines idle, hold a little less than gravity so the
			// ship sinks onto its gear on its own.
			double GravityHold = 1.0;
			if (bSurfaceValid && GroundGapCm >= 0.f && GroundGapCm < 400.f && FMath::Abs(ThrottleSetting) < 0.05f && LiftInput <= 0.f)
			{
				GravityHold = 1.0 - LandingSettleGravityFraction;
			}
			// Feed forward what the environment will take this frame (drag, gravity), then close the
			// remaining velocity error proportionally.
			const FVector Compensation = Rotation.UnrotateVector(LinearVelocity * DragRate + Up * (Gravity * GravityHold));
			LocalAcceleration = (DesiredLocal - VelocityLocal) * FlightAssistResponse + Compensation;
		}
		else
		{
			LocalAcceleration = FVector(
				ThrustInput * (ThrustInput > 0.f ? ForwardCap : ReverseCap),
				StrafeInput * StrafeAcceleration,
				LiftInput * LiftAcceleration);
		}

		// Every thruster axis has its limit, flight computer or not.
		LocalAcceleration.X = FMath::Clamp(LocalAcceleration.X, -ReverseCap, ForwardCap);
		LocalAcceleration.Y = FMath::Clamp(LocalAcceleration.Y, -double(StrafeAcceleration), double(StrafeAcceleration));
		LocalAcceleration.Z = FMath::Clamp(LocalAcceleration.Z, -double(LiftAcceleration), double(LiftAcceleration));
		EngineDemand = float(FMath::Clamp(FMath::Max3(
			FMath::Abs(LocalAcceleration.X) / (LocalAcceleration.X >= 0.0 ? FMath::Max(ForwardCap, 1.0) : FMath::Max(ReverseCap, 1.0)),
			0.7 * FMath::Abs(LocalAcceleration.Y) / FMath::Max(double(StrafeAcceleration), 1.0),
			0.7 * FMath::Abs(LocalAcceleration.Z) / FMath::Max(double(LiftAcceleration), 1.0)), 0.0, 1.0));

		LinearVelocity += Rotation.RotateVector(LocalAcceleration) * DeltaSeconds;

		// Drag and gravity, the same terms as ComputeEnvironmentAcceleration. Drag is applied as a
		// damping fraction clamped to 1, so a long frame in dense air can stop the ship but never
		// reverse it.
		LinearVelocity -= LinearVelocity * FMath::Min(DragRate * DeltaSeconds, 1.0);
		if (bHasEnvironment)
		{
			LinearVelocity -= Up * (Gravity * DeltaSeconds);
		}
		if (bGroundContact)
		{
			// After gravity, so on a gentle slope friction cancels this frame's pull down the slope
			// completely and the ship stands still instead of creeping.
			LinearVelocity = ApplyGroundFriction(LinearVelocity, GroundNormal, Up, float(Gravity), DeltaSeconds);
		}

		const float Speed = LinearVelocity.Size();
		if (CruiseState == ECruiseState::Dropping)
		{
			// Out of cruise: kilometres per second bleed off quickly down to boosted flight speed.
			const float Cap = MaxSpeed * BoostMultiplier;
			if (Speed > Cap)
			{
				LinearVelocity *= FMath::Max(Cap, Speed * FMath::Exp(-2.5f * DeltaSeconds)) / Speed;
			}
		}
		else
		{
			const float SpeedCap = MaxSpeed * BoostFactor;
			if (Speed > SpeedCap)
			{
				// Above the cap: while accelerating this is an ordinary clamp, but right after boost
				// ends the excess bleeds off instead of snapping to the unboosted cap.
				const float Excess = (Speed - SpeedCap) * FMath::Min(OverspeedDecay * DeltaSeconds, 1.f);
				const float Target = bBoostActive ? SpeedCap : Speed - Excess;
				LinearVelocity *= FMath::Max(Target, SpeedCap) / Speed;
			}
		}
	}

	if (LinearVelocity.IsNearlyZero())
	{
		LinearVelocity = FVector::ZeroVector;
		return;
	}

	const FVector Delta = LinearVelocity * DeltaSeconds;
	FHitResult Hit;
	AddActorWorldOffset(Delta, bSweepMovement, &Hit);

	if (Hit.bBlockingHit)
	{
		// Drop the component of velocity pointing into the surface so the ship slides along it
		// instead of pressing into it and stalling.
		LinearVelocity = FVector::VectorPlaneProject(LinearVelocity, Hit.Normal);
		if (CruiseState == ECruiseState::Active)
		{
			BeginCruiseDrop(ECruiseBlocker::TooLow);
		}

		// Spend the rest of this frame's movement sliding, so touching a surface does not cost
		// a frame of motion and stutter.
		const FVector Slide = FVector::VectorPlaneProject(Delta * (1.f - Hit.Time), Hit.Normal);
		if (!Slide.IsNearlyZero())
		{
			AddActorWorldOffset(Slide, true);
		}
	}
}

FVector ASpaceshipPawn::ComputeEnvironmentAcceleration(const FCelestialEnvironment& InEnvironment, const FVector& Velocity) const
{
	const double DragRate = SpaceLinearDamping + (LinearDamping + QuadraticDrag * Velocity.Size()) * InEnvironment.AtmosphereDensity;
	return -Velocity * DragRate - InEnvironment.Up * (InEnvironment.GravityCmS2 * GravityScale);
}

float ASpaceshipPawn::ComputeHeatTarget(float AtmosphereDensity, float SpeedCmS) const
{
	const double Relative = SpeedCmS / HeatReferenceSpeed;
	const double Heating = AtmosphereDensity * Relative * Relative * Relative;
	return float(FMath::Clamp((Heating - HeatOnset) / FMath::Max(double(HeatFull - HeatOnset), 0.01), 0.0, 1.0));
}

void ASpaceshipPawn::UpdateEnvironment(float DeltaSeconds)
{
	NearestBody = ACelestialBody::FindNearest(GetWorld(), GetActorLocation(), &Environment, &bHasEnvironment);
	const float Target = bHasEnvironment ? ComputeHeatTarget(Environment.AtmosphereDensity, LinearVelocity.Size()) : 0.f;
	Heat = FMath::FInterpTo(Heat, Target, DeltaSeconds, HeatResponse);
}

// -------------------------------------------------------------------------------------------
// Landing
// -------------------------------------------------------------------------------------------

namespace
{
	float AngleBetweenDeg(const FVector& A, const FVector& B)
	{
		return float(FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(A.GetSafeNormal() | B.GetSafeNormal(), -1.0, 1.0))));
	}

	/** Keeps the heading, puts the ship's up on Normal. */
	FQuat LevelOnSurface(const FQuat& Current, const FVector& Normal)
	{
		FVector Forward = FVector::VectorPlaneProject(Current.GetForwardVector(), Normal);
		if (Forward.SizeSquared() < 1e-4)
		{
			// Nose pointing straight at the ground or the sky: keep the up vector's heading instead.
			Forward = FVector::VectorPlaneProject(Current.GetUpVector(), Normal);
		}
		return FRotationMatrix::MakeFromXZ(Forward.GetSafeNormal(), Normal).ToQuat();
	}
}

ELandingBlocker ASpaceshipPawn::EvaluateLanding(float GroundGap, float Speed, float TiltDeg, float SlopeDeg, bool bEngineInput) const
{
	if (GroundGap < 0.f || GroundGap > LandingMaxGapCm)
	{
		return ELandingBlocker::TooHigh;
	}
	if (SlopeDeg > MaxLandingSlopeDeg)
	{
		return ELandingBlocker::TooSteep;
	}
	if (Speed > LandingMaxSpeed)
	{
		return ELandingBlocker::TooFast;
	}
	if (TiltDeg > LandingMaxTiltDeg)
	{
		return ELandingBlocker::Tilted;
	}
	if (bEngineInput)
	{
		return ELandingBlocker::EngineInput;
	}
	return ELandingBlocker::None;
}

FVector ASpaceshipPawn::ApplyGroundFriction(const FVector& Velocity, const FVector& SurfaceNormal, const FVector& Up, float GravityCmS2, float DeltaSeconds) const
{
	// Coulomb friction: the tangential velocity loses at most mu x normal load per second. On a
	// slope where mu >= tan(slope) that is more than gravity adds along it, so a resting ship
	// stays at rest; on steeper ground the remainder makes it slide.
	const double NormalLoad = GravityCmS2 * FMath::Max(0.0, SurfaceNormal | Up);
	const FVector Tangential = FVector::VectorPlaneProject(Velocity, SurfaceNormal);
	const double TangentialSpeed = Tangential.Size();
	if (TangentialSpeed < UE_KINDA_SMALL_NUMBER)
	{
		return Velocity;
	}
	const double Remaining = FMath::Max(0.0, TangentialSpeed - GroundFriction * NormalLoad * DeltaSeconds);
	return Velocity - Tangential * (1.0 - Remaining / TangentialSpeed);
}

FRotator ASpaceshipPawn::ComputeLandedRotationStep(const FRotator& Current, const FVector& SurfaceNormal, float DeltaSeconds) const
{
	const FQuat From = Current.Quaternion();
	const double Alpha = 1.0 - FMath::Exp(-LandingAlignRate * DeltaSeconds);
	return FQuat::Slerp(From, LevelOnSurface(From, SurfaceNormal.GetSafeNormal()), Alpha).GetNormalized().Rotator();
}

bool ASpaceshipPawn::SweepHull(const FVector& Start, const FVector& End, const FQuat& Rotation, FHitResult& OutHit) const
{
	FCollisionQueryParams Params(SCENE_QUERY_STAT(SpaceshipGroundProbe), false, this);
	FCollisionResponseParams Responses;
	HullCollision->InitSweepCollisionParams(Params, Responses);
	return GetWorld()->SweepSingleByChannel(OutHit, Start, End, Rotation, HullCollision->GetCollisionObjectType(),
		HullCollision->GetCollisionShape(), Params, Responses);
}

void ASpaceshipPawn::UpdateLanding(float DeltaSeconds)
{
	TakeoffCooldown = FMath::Max(0.f, TakeoffCooldown - DeltaSeconds);
	bSurfaceValid = false;
	bGroundContact = false;
	GroundGapCm = -1.f;

	// Probe the ground only when it matters: low over a body with a walkable surface.
	const ACelestialBody* Body = NearestBody.Get();
	FVector SurfacePoint;
	if (bHasEnvironment && Body && Environment.AltitudeAboveTerrainCm < LandingProbeAltitudeM * 100.0
		&& Body->GetSurfaceFrame(GetActorLocation(), LandingFootprintRadiusCm, SurfacePoint, GroundNormal))
	{
		bSurfaceValid = true;
		GroundSlopeDeg = AngleBetweenDeg(GroundNormal, Environment.Up);
		GroundTiltDeg = AngleBetweenDeg(GetActorUpVector(), GroundNormal);

		// Straight down with the real hull shape: the gap is what the collision actually sees,
		// wherever on the hull the first contact would be.
		const FVector Start = GetActorLocation();
		const double ProbeLength = FMath::Max(LandingMaxGapCm, GroundContactToleranceCm) + 200.0;
		FHitResult Hit;
		if (SweepHull(Start, Start - Environment.Up * ProbeLength, GetActorQuat(), Hit))
		{
			GroundGapCm = Hit.bStartPenetrating ? 0.f : float(Hit.Distance);
		}
		bGroundContact = GroundGapCm >= 0.f && GroundGapCm <= GroundContactToleranceCm;
	}

	const bool bEngineInput = FMath::Abs(ThrustInput) >= TakeoffInputThreshold || LiftInput >= TakeoffInputThreshold
		|| (bFlightAssist && FMath::Abs(ThrottleSetting) > 0.05f) || CruiseState != ECruiseState::Off;

	if (LandingState == ELandingState::Landed)
	{
		LandingBlocker = ELandingBlocker::None;
		if (bEngineInput || !bSurfaceValid)
		{
			ExitLanded();
		}
		return;
	}

	LandingBlocker = !bSurfaceValid ? ELandingBlocker::NoSurface
		: TakeoffCooldown > 0.f ? ELandingBlocker::TakeoffCooldown
		: EvaluateLanding(GroundGapCm, LinearVelocity.Size(), GroundTiltDeg, GroundSlopeDeg, bEngineInput);

	if (LandingBlocker == ELandingBlocker::None)
	{
		// Every condition has to hold without a break: a bounce restarts the window.
		SettleSeconds += DeltaSeconds;
		LandingState = ELandingState::Settling;
		if (SettleSeconds >= LandingConfirmSeconds)
		{
			EnterLanded();
		}
	}
	else
	{
		SettleSeconds = 0.f;
		LandingState = ELandingState::Flying;
	}
}

void ASpaceshipPawn::EnterLanded()
{
	LandingState = ELandingState::Landed;
	SettleSeconds = LandingConfirmSeconds;
	AngularVelocity = FVector::ZeroVector;
	MouseStick = FVector2D::ZeroVector;
	ThrottleSetting = 0.f;
	bBoostActive = false;
	UE_LOG(LogSpaceship, Log, TEXT("%s landed: slope %.1f deg, tilt %.1f deg, gap %.0f cm"),
		*GetName(), GroundSlopeDeg, GroundTiltDeg, GroundGapCm);
}

void ASpaceshipPawn::ExitLanded()
{
	LandingState = ELandingState::Flying;
	SettleSeconds = 0.f;
	TakeoffCooldown = TakeoffCooldownSeconds;
	LinearVelocity = FVector::ZeroVector;
	UE_LOG(LogSpaceship, Log, TEXT("%s took off"), *GetName());
}

void ASpaceshipPawn::UpdateLandedMotion(float DeltaSeconds)
{
	// Steering does nothing on the ground; drop what the mouse and stick sent, so nothing
	// piles up and jerks the ship at takeoff.
	MouseLookDelta = FVector2D::ZeroVector;
	LookInput = FVector2D::ZeroVector;
	MouseStick = FVector2D::ZeroVector;
	AngularVelocity = FVector::ZeroVector;

	const double Alpha = 1.0 - FMath::Exp(-LandingAlignRate * DeltaSeconds);
	const FQuat Current = GetActorQuat();
	const FQuat Rotation = FQuat::Slerp(Current, LevelOnSurface(Current, GroundNormal), Alpha).GetNormalized();

	// Leftover sliding along the ground dies out instead of stopping dead.
	LinearVelocity = FVector::VectorPlaneProject(LinearVelocity, GroundNormal) * FMath::Exp(-LandedBrakeRate * DeltaSeconds);
	if (LinearVelocity.SizeSquared() < 1.0)
	{
		LinearVelocity = FVector::ZeroVector;
	}
	FVector Location = GetActorLocation() + LinearVelocity * DeltaSeconds;

	// Where the hull, in its new rotation, rests on the collision: sweep it down onto the ground
	// from a metre above, and ease towards that. Keeps the ship sitting on the terrain as it
	// levels out, without sinking in or hovering.
	FHitResult Hit;
	if (SweepHull(Location + GroundNormal * 100.0, Location - GroundNormal * 300.0, Rotation, Hit) && !Hit.bStartPenetrating)
	{
		Location = FMath::Lerp(Location, Hit.Location + GroundNormal * 1.0, Alpha);
	}

	SetActorLocationAndRotation(Location, Rotation);
}

void ASpaceshipPawn::UpdateCameraEffects(float DeltaSeconds)
{
	BoostBlend = FMath::FInterpTo(BoostBlend, bBoostActive ? 1.f : 0.f, DeltaSeconds, 4.f);
	const float CruiseTarget = CruiseState == ECruiseState::Active ? 1.f
		: CruiseState == ECruiseState::Spooling ? 0.2f * GetCruiseSpoolProgress() : 0.f;
	CruiseBlend = FMath::FInterpTo(CruiseBlend, CruiseTarget, DeltaSeconds, CruiseState == ECruiseState::Dropping ? 3.f : 1.5f);
	CameraKick *= FMath::Exp(-5.f * DeltaSeconds);

	// Mouse wheel zoom, eased.
	CameraZoom = FMath::FInterpTo(CameraZoom, CameraZoomTarget, DeltaSeconds, 8.f);
	CockpitZoom = FMath::FInterpTo(CockpitZoom, CockpitZoomTarget, DeltaSeconds, 8.f);
	if (BaseArmLength > 0.f)
	{
		CameraBoom->TargetArmLength = BaseArmLength * CameraZoom;
		// The height above the ship grows slower than the distance, so a far camera does not end
		// up looking steeply down on it.
		CameraBoom->SocketOffset = BaseSocketOffset * FMath::Sqrt(CameraZoom);
	}

	// Speed you can feel: the view widens with boost and much more in cruise.
	const float FovKick = BoostFovKick * BoostBlend + CruiseFovKick * CruiseBlend;
	ChaseCamera->SetFieldOfView(BaseChaseFov + FovKick);
	CockpitCamera->SetFieldOfView(FMath::Lerp(BaseCockpitFov, CockpitZoomFov, CockpitZoom) + 0.6f * FovKick * (1.f - CockpitZoom));

	// Smooth noise rather than random jumps: a rumble, not a flicker. Nothing moves when calm.
	const float Spool = CruiseState == ECruiseState::Spooling ? GetCruiseSpoolProgress() : 0.f;
	const float Amplitude = HeatShakeCm * Heat * Heat + BoostShakeCm * BoostBlend
		+ CruiseShakeCm * (Spool * Spool + 0.25f * CruiseBlend) + KickShakeCm * CameraKick;
	const double Time = GetWorld()->GetTimeSeconds();
	const FVector Shake = Amplitude < 0.01f
		? FVector::ZeroVector
		: FVector(
			FMath::PerlinNoise1D(float(Time * 11.0 + 3.7)),
			FMath::PerlinNoise1D(float(Time * 12.4 + 17.1)),
			FMath::PerlinNoise1D(float(Time * 10.0 + 41.9))) * Amplitude;
	ChaseCamera->SetRelativeLocation(ChaseCameraBaseLocation + Shake);
	CockpitCamera->SetRelativeLocation(CockpitCameraBaseLocation + Shake * 0.25);
}

// -------------------------------------------------------------------------------------------
// Sound
// -------------------------------------------------------------------------------------------

void ASpaceshipPawn::SetupAudioLayers()
{
	using namespace SpaceshipPawnDefaults;
	auto Load = [](TObjectPtr<USoundBase>& Sound, const TCHAR* Path)
	{
		if (!Sound)
		{
			Sound = LoadOptional<USoundBase>(Path);
		}
	};
	Load(EngineHumSound, EngineHumSoundPath);
	Load(BoostLoopSound, BoostLoopSoundPath);
	Load(CruiseLoopSound, CruiseLoopSoundPath);
	Load(BoostStartSound, BoostStartSoundPath);
	Load(CruiseChargeSound, CruiseChargeSoundPath);
	Load(CruiseEngageSound, CruiseEngageSoundPath);
	Load(CruiseDropSound, CruiseDropSoundPath);

	// Created at runtime rather than as default subobjects: nothing to configure per ship, and
	// Blueprints made before these layers existed need no changes.
	auto MakeLayer = [this](USoundBase* Sound, const TCHAR* Name) -> UAudioComponent*
	{
		if (!Sound)
		{
			return nullptr;
		}
		UAudioComponent* Layer = NewObject<UAudioComponent>(this, FName(Name));
		Layer->SetupAttachment(HullCollision);
		Layer->bAutoActivate = false;
		Layer->bAllowSpatialization = false;
		Layer->SetSound(Sound);
		Layer->RegisterComponent();
		return Layer;
	};
	EngineHumAudio = MakeLayer(EngineHumSound, TEXT("EngineHumAudio"));
	BoostAudio = MakeLayer(BoostLoopSound, TEXT("BoostAudio"));
	CruiseAudio = MakeLayer(CruiseLoopSound, TEXT("CruiseAudio"));
}

UAudioComponent* ASpaceshipPawn::PlayOneShot(USoundBase* Sound, float VolumeScale)
{
	const UWorld* World = GetWorld();
	if (!Sound || !World || !World->IsGameWorld() || !IsPlayerControlled())
	{
		return nullptr;
	}
	return UGameplayStatics::SpawnSound2D(this, Sound, OneShotVolume * VolumeScale);
}

void ASpaceshipPawn::UpdateEngineAudio(float DeltaSeconds)
{
	const bool bPiloted = IsPlayerControlled();

	// Eased rather than snapped, so the engines spool up and down instead of clicking. The load is
	// what the thrusters really do: braking and holding altitude are heard too, a steady cruise
	// through empty space is quiet.
	EngineLoad = FMath::FInterpTo(EngineLoad, bPiloted ? EngineDemand : 0.f, DeltaSeconds, EngineSpoolRate);
	EngineBoostBlend = FMath::FInterpTo(EngineBoostBlend, bPiloted && bBoostActive ? 1.f : 0.f, DeltaSeconds, EngineSpoolRate);
	HumBlend = FMath::FInterpTo(HumBlend, bPiloted ? 1.f : 0.f, DeltaSeconds, 1.5f);

	auto Drive = [](UAudioComponent* Layer, float Volume, float Pitch)
	{
		if (!Layer || !Layer->GetSound())
		{
			return;
		}
		// Below this the layer is inaudible anyway; stopping it frees the voice.
		if (Volume < 0.004f)
		{
			if (Layer->IsPlaying())
			{
				Layer->Stop();
			}
			return;
		}
		if (!Layer->IsPlaying())
		{
			Layer->Play();
		}
		Layer->SetVolumeMultiplier(Volume);
		Layer->SetPitchMultiplier(Pitch);
	};

	Drive(EngineHumAudio, EngineHumVolume * HumBlend * (0.85f + 0.3f * EngineLoad), 1.f + 0.04f * EngineLoad + 0.06f * CruiseBlend);

	const float Load = FMath::Min(EngineLoad + 0.35f * EngineBoostBlend, 1.f);
	Drive(EngineAudio, EngineVolume * Load,
		FMath::Lerp(EngineMinPitch, EngineMaxPitch, EngineLoad) + EngineBoostPitch * EngineBoostBlend);
	// Interpolated in log space, which is how cutoff frequencies are heard.
	EngineAudio->SetLowPassFilterFrequency(FMath::Exp(FMath::Lerp(
		FMath::Loge(EngineLowPassIdleHz), FMath::Loge(EngineLowPassFullHz), Load)));

	Drive(BoostAudio, bPiloted ? BoostVolume * BoostBlend : 0.f, 1.f + 0.06f * BoostBlend);
	const float CruiseSpeed = FMath::Clamp(LinearVelocity.Size() / FMath::Max(CruiseMaxSpeed, 1.f), 0.f, 1.f);
	Drive(CruiseAudio, bPiloted ? CruiseVolume * CruiseBlend : 0.f, 0.9f + 0.25f * FMath::Sqrt(CruiseSpeed));
}

// -------------------------------------------------------------------------------------------
// Lights and dust
// -------------------------------------------------------------------------------------------

void ASpaceshipPawn::SetupShipLights()
{
	ThrusterMaterials.Reset();
	StrobeMaterials.Reset();
	if (!Hull->GetStaticMesh())
	{
		return;
	}
	// By slot name, as named in Blender: M_Ship_<Ship>_Emissive for thrusters, _NavWhite strobes.
	const TArray<FName> Slots = Hull->GetMaterialSlotNames();
	for (int32 Index = 0; Index < Slots.Num(); ++Index)
	{
		const FString Name = Slots[Index].ToString();
		const bool bThruster = Name.Contains(TEXT("Emissive")) || Name.Contains(TEXT("Thruster"));
		const bool bStrobe = Name.Contains(TEXT("NavWhite")) || Name.Contains(TEXT("Strobe"));
		if (!bThruster && !bStrobe)
		{
			continue;
		}
		UMaterialInstanceDynamic* Material = Hull->CreateDynamicMaterialInstance(Index);
		const float Base = Material ? Material->K2_GetScalarParameterValue(SpaceshipPawnDefaults::EmissiveStrengthParameter) : 0.f;
		if (Base <= 0.f)
		{
			continue;  // not an M_Ship_Hull glow material; nothing to animate
		}
		FShipGlowMaterial Glow;
		Glow.Material = Material;
		Glow.BaseStrength = Base;
		(bThruster ? ThrusterMaterials : StrobeMaterials).Add(Glow);
	}
}

void ASpaceshipPawn::UpdateShipLights(float DeltaSeconds)
{
	auto Apply = [](FShipGlowMaterial& Glow, float Strength)
	{
		UMaterialInstanceDynamic* Material = Glow.Material.Get();
		// Only on a visible change: every parameter set re-uploads the material's uniforms.
		if (Material && FMath::Abs(Strength - Glow.Applied) > 0.01f * FMath::Max(Glow.BaseStrength, 1.f))
		{
			Material->SetScalarParameterValue(SpaceshipPawnDefaults::EmissiveStrengthParameter, Strength);
			Glow.Applied = Strength;
		}
	};

	const float Thrust = ThrusterIdleGlow + (1.f - ThrusterIdleGlow) * EngineLoad + ThrusterBoostGlow * BoostBlend + ThrusterCruiseGlow * CruiseBlend;
	for (FShipGlowMaterial& Glow : ThrusterMaterials)
	{
		Apply(Glow, Glow.BaseStrength * Thrust);
	}

	// A quick double flash, like aircraft anti-collision strobes.
	const double Phase = FMath::Fmod(GetWorld()->GetTimeSeconds(), double(NavStrobePeriodSeconds));
	const bool bFlash = Phase < 0.06 || (Phase > 0.16 && Phase < 0.22);
	for (FShipGlowMaterial& Glow : StrobeMaterials)
	{
		Apply(Glow, Glow.BaseStrength * (bFlash ? 1.f : 0.03f));
	}
}

void ASpaceshipPawn::UpdateSpaceDust(float DeltaSeconds)
{
	const APlayerController* PlayerController = Cast<APlayerController>(GetController());
	if (!PlayerController || !PlayerController->PlayerCameraManager || LandingState == ELandingState::Landed)
	{
		SpaceDust->HideDust();
		return;
	}
	SpaceDust->UpdateDust(PlayerController->PlayerCameraManager->GetCameraLocation(), LinearVelocity, 1.f + 1.5f * CruiseBlend);
}
