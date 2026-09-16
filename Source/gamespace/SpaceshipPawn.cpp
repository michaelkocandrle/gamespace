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
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "InputAction.h"
#include "InputActionValue.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "InputTriggers.h"
#include "Sound/SoundBase.h"
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
	const TCHAR* const MouseLookActionPath = TEXT("/Game/Input/IA_LookMouse.IA_LookMouse");
	const TCHAR* const MouseMappingContextPath = TEXT("/Game/Input/IMC_SpaceshipMouse.IMC_SpaceshipMouse");
	const TCHAR* const EngineLoopSoundPath = TEXT("/Game/Ships/Audio/SW_EngineLoop.SW_EngineLoop");

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
	HullCollision->SetSimulatePhysics(false);
	SetRootComponent(HullCollision);

	Hull = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Hull"));
	Hull->SetupAttachment(HullCollision);
	Hull->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);

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

	EngineAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("EngineAudio"));
	EngineAudio->SetupAttachment(HullCollision);
	// Silent until the engine actually pushes; UpdateEngineAudio starts and stops it.
	EngineAudio->SetAutoActivate(false);
	// The player's own engine: heard the same from chase and cockpit camera, not positioned.
	EngineAudio->bAllowSpatialization = false;
	// Opened up with engine load in UpdateEngineAudio, so light thrust sounds muffled and distant.
	EngineAudio->bEnableLowPassFilter = true;
	EngineAudio->LowPassFilterFrequency = EngineLowPassIdleHz;
}

void ASpaceshipPawn::BeginPlay()
{
	Super::BeginPlay();

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
	Hull->SetOwnerNoSee(bCockpit);
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
	}
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
	if (!MouseLookAction)
	{
		MouseLookAction = LoadOptional<UInputAction>(MouseLookActionPath);
	}
	if (!MouseMappingContext)
	{
		MouseMappingContext = LoadOptional<UInputMappingContext>(MouseMappingContextPath);
	}

	BuildProceduralInputAssets();
}

void ASpaceshipPawn::BuildProceduralInputAssets()
{
	const bool bNeedsAnything = !FlightMappingContext || !ThrustAction || !StrafeAction || !LiftAction
		|| !RollAction || !LookAction || !ToggleCameraAction || !BoostAction || !MouseLookAction
		|| !MouseMappingContext;
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

	// Rotate first so this frame's thrust is applied along the heading the player just commanded.
	UpdateAngularMotion(DeltaSeconds);
	UpdateLinearMotion(DeltaSeconds);
	UpdateEngineAudio(DeltaSeconds);

	if (CameraSnapTicks > 0 && --CameraSnapTicks == 0)
	{
		CameraBoom->bEnableCameraLag = true;
	}
}

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
	const float PitchCommand = Command.Y * (bInvertPitch ? -1.f : 1.f);
	const float YawCommand = Command.X;

	const FVector TargetRates(
		RollInput * RollRate,
		PitchCommand * PitchRate,
		YawCommand * YawRate);

	AngularVelocity = FMath::VInterpTo(AngularVelocity, TargetRates, DeltaSeconds, AngularResponsiveness);

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
	// Boost only drives the main engine forwards; reverse, strafe and lift stay at normal power.
	const float BoostFactor = bBoostHeld ? BoostMultiplier : 1.f;
	const float ThrustFactor = ThrustInput > 0.f ? BoostFactor : 1.f;

	const FVector LocalAcceleration(
		ThrustInput * ThrustAcceleration * ThrustFactor,
		StrafeInput * StrafeAcceleration,
		LiftInput * LiftAcceleration);

	LinearVelocity += GetActorQuat().RotateVector(LocalAcceleration) * DeltaSeconds;

	if (LinearDamping > 0.f)
	{
		// Min() keeps a long frame from overshooting into a reversed velocity.
		LinearVelocity -= LinearVelocity * FMath::Min(LinearDamping * DeltaSeconds, 1.f);
	}

	const float SpeedCap = MaxSpeed * BoostFactor;
	const float Speed = LinearVelocity.Size();
	if (Speed > SpeedCap)
	{
		// Above the cap: while accelerating this is an ordinary clamp, but right after boost
		// is released the excess bleeds off instead of snapping to the unboosted cap.
		const float Excess = (Speed - SpeedCap) * FMath::Min(OverspeedDecay * DeltaSeconds, 1.f);
		const float Target = bBoostHeld ? SpeedCap : Speed - Excess;
		LinearVelocity *= FMath::Max(Target, SpeedCap) / Speed;
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

		// Spend the rest of this frame's movement sliding, so touching a surface does not cost
		// a frame of motion and stutter.
		const FVector Slide = FVector::VectorPlaneProject(Delta * (1.f - Hit.Time), Hit.Normal);
		if (!Slide.IsNearlyZero())
		{
			AddActorWorldOffset(Slide, true);
		}
	}
}

void ASpaceshipPawn::UpdateEngineAudio(float DeltaSeconds)
{
	if (!EngineAudio->GetSound())
	{
		return;
	}

	// How hard the engines work: main thrust counts fully, manoeuvring thrusters partly.
	const float TargetLoad = FMath::Clamp(FMath::Max3(
		FMath::Abs(ThrustInput),
		0.6f * FMath::Max(FMath::Abs(StrafeInput), FMath::Abs(LiftInput)),
		0.3f * FMath::Abs(RollInput)), 0.f, 1.f);
	const float TargetBoost = (bBoostHeld && ThrustInput > 0.f) ? 1.f : 0.f;

	// Eased rather than snapped, so the engine spools up and down instead of clicking.
	EngineLoad = FMath::FInterpTo(EngineLoad, TargetLoad, DeltaSeconds, EngineSpoolRate);
	EngineBoostBlend = FMath::FInterpTo(EngineBoostBlend, TargetBoost, DeltaSeconds, EngineSpoolRate);

	// Below this the sound is inaudible anyway; stopping it makes idle truly silent.
	const float SilenceThreshold = 0.01f;
	if (EngineLoad < SilenceThreshold)
	{
		if (EngineAudio->IsPlaying())
		{
			EngineAudio->Stop();
		}
		return;
	}

	if (!EngineAudio->IsPlaying())
	{
		EngineAudio->Play();
	}

	const float Load = FMath::Min(EngineLoad + 0.35f * EngineBoostBlend, 1.f);
	EngineAudio->SetVolumeMultiplier(EngineVolume * Load);
	EngineAudio->SetPitchMultiplier(
		FMath::Lerp(EngineMinPitch, EngineMaxPitch, EngineLoad) + EngineBoostPitch * EngineBoostBlend);
	// Interpolated in log space, which is how cutoff frequencies are heard.
	EngineAudio->SetLowPassFilterFrequency(FMath::Exp(FMath::Lerp(
		FMath::Loge(EngineLowPassIdleHz), FMath::Loge(EngineLowPassFullHz), Load)));
}
