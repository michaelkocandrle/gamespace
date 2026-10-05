// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceshipPawn.h"
#include "SpaceshipLog.h"

#include "Camera/CameraComponent.h"
#include "Components/AudioComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/LocalLightComponent.h"
#include "HAL/IConsoleManager.h"
#include "CockpitDisplayComponent.h"
#include "Components/BoxComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInterface.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/CollisionProfile.h"
#include "Engine/LocalPlayer.h"
#include "Engine/StaticMesh.h"
#include "Algo/Find.h"
#include "Engine/OverlapResult.h"
#include "Engine/World.h"
#include "PlayerCharacter.h"
#include "SpaceDebugHUD.h"
#include "SpaceInterior.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "InputAction.h"
#include "InputActionValue.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "InputTriggers.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialParameterCollection.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Camera/PlayerCameraManager.h"
#include "PhysicsEngine/BodySetup.h"
#include "Sound/SoundBase.h"
#include "CelestialBody.h"
#include "DistantBody.h"
#include "SpaceCelestialRegistrySubsystem.h"
#include "SpaceDustComponent.h"
#include "SpaceSpeedTunnelComponent.h"
#include "SpaceHullSparksComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "SpacePlayerController.h"
#include "Components/SkyLightComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/SkyLight.h"
#include "SpaceUserSettings.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "EngineUtils.h"

DEFINE_LOG_CATEGORY(LogSpaceship);

namespace SpaceshipPawnDefaults
{
	/** 1 G in cm/s^2. */
	constexpr double StandardGravityCmS2 = FShipFlightModel::StandardGravityCmS2;
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
	// See the header: characters use the hull's real shape, not this box.
	HullCollision->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
	// Cameras too: a pilot who just got out stands inside this box (it spans the wings), and the
	// character's camera boom, starting inside it, was pulled right in to the head until the
	// pilot walked out of it. The hull mesh's own collision still blocks cameras.
	HullCollision->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
	HullCollision->SetSimulatePhysics(false);
	SetRootComponent(HullCollision);

	Hull = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Hull"));
	Hull->SetupAttachment(HullCollision);
	// Query only: pawns, cameras and visibility traces stop on it, and the ship's own movement sweeps its shapes
	// against the world (SweepHullParts; a component query takes the component's responses, hence the world
	// channels). It has no physics body of its own, so nothing else changes.
	Hull->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Hull->SetCollisionObjectType(ECC_WorldDynamic);
	Hull->SetCollisionResponseToAllChannels(ECR_Ignore);
	Hull->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
	Hull->SetCollisionResponseToChannel(ECC_Camera, ECR_Block);
	Hull->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	Hull->SetCollisionResponseToChannel(ECC_WorldStatic, ECR_Block);
	Hull->SetCollisionResponseToChannel(ECC_WorldDynamic, ECR_Block);
	Hull->SetCanEverAffectNavigation(false);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> PlaceholderCube(TEXT("/Engine/BasicShapes/Cube.Cube"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> BasicShapeMaterial(TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	CockpitPartMesh = PlaceholderCube.Object;
	CockpitPartMaterial = BasicShapeMaterial.Object;
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
	CameraBoom->CameraLagSpeed = BaseCameraLagSpeed;
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
	// No motion blur from the seat: the cockpit moves with the eye except for the camera shake (boost,
	// afterburner, heat), and the engine's default blur smeared the whole dashboard and its displays
	// with every shake. The Star Citizen reference keeps the cockpit sharp.
	CockpitCamera->PostProcessSettings.bOverride_MotionBlurAmount = true;
	CockpitCamera->PostProcessSettings.MotionBlurAmount = 0.f;
	CockpitCamera->PostProcessBlendWeight = 1.f;

	for (TObjectPtr<UPointLightComponent>* Light : { &CockpitLight, &CockpitFillLight })
	{
		*Light = CreateDefaultSubobject<UPointLightComponent>(Light == &CockpitLight ? TEXT("CockpitLight") : TEXT("CockpitFillLight"));
		(*Light)->SetupAttachment(HullCollision);
		(*Light)->SetCastShadows(false);
		(*Light)->SetIntensityUnits(ELightUnits::Candelas);
		(*Light)->SetIntensity(0.f);
		(*Light)->SetVisibility(false);
	}
	CockpitDisplays = CreateDefaultSubobject<UCockpitDisplayComponent>(TEXT("CockpitDisplays"));

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

	// The ship's systems state: no transform and no tick of its own (the pawn's Tick drives it).
	Systems = CreateDefaultSubobject<UShipSystemsComponent>(TEXT("ShipSystems"));
	Quantum = CreateDefaultSubobject<UShipQuantumComponent>(TEXT("ShipQuantum"));
	Landing = CreateDefaultSubobject<UShipLandingComponent>(TEXT("ShipLanding"));
	ShipInput = CreateDefaultSubobject<UShipInputComponent>(TEXT("ShipInput"));
	Presentation = CreateDefaultSubobject<UShipPresentationComponent>(TEXT("ShipPresentation"));
	Boarding = CreateDefaultSubobject<UShipBoardingComponent>(TEXT("ShipBoarding"));

	SpaceDust =CreateDefaultSubobject<USpaceDustComponent>(TEXT("SpaceDust"));
	SpaceDust->SetupAttachment(HullCollision);
	SpeedTunnel = CreateDefaultSubobject<USpaceSpeedTunnelComponent>(TEXT("SpeedTunnel"));
	SpeedTunnel->SetupAttachment(HullCollision);
	HullSparks = CreateDefaultSubobject<USpaceHullSparksComponent>(TEXT("HullSparks"));
	HullSparks->SetupAttachment(Hull);
	QuantumGlow = CreateDefaultSubobject<UPointLightComponent>(TEXT("QuantumGlow"));
	QuantumGlow->SetupAttachment(Hull);
	QuantumGlow->SetIntensityUnits(ELightUnits::Candelas);
	QuantumGlow->SetIntensity(0.f);
	QuantumGlow->SetLightColor(FLinearColor(0.3f, 0.55f, 1.f));
	QuantumGlow->SetAttenuationRadius(900.f);
	QuantumGlow->SetCastShadows(false);
	QuantumGlow->SetVisibility(false);

	// A hard reference, so the cooker packs it (engine content loaded by path would be missing).
	static ConstructorHelpers::FObjectFinder<UStaticMesh> GearCylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (GearCylinder.Succeeded())
	{
		GearLegMesh = GearCylinder.Object;
	}
}

void ASpaceshipPawn::BeginPlay()
{
	Super::BeginPlay();
	PowerState = bStartPowered ? ESpacePowerState::On : ESpacePowerState::Off;

	Presentation->LoadViewCollection();

	ChaseCameraBaseLocation = ChaseCamera->GetRelativeLocation();
	CockpitCameraBaseLocation = CockpitCamera->GetRelativeLocation();
	HullSparks->SetHull(Hull);
	// The nose glow sits just ahead of and below the hull's front, whatever the ship.
	if (Hull->GetStaticMesh())
	{
		const FBox Box = Hull->GetStaticMesh()->GetBoundingBox();
		QuantumGlow->SetRelativeLocation(FVector(Box.Max.X + 150.0, 0.0, Box.GetCenter().Z - Box.GetExtent().Z * 0.3));
	}
	Presentation->FindLevelLights();
	BaseArmLength = CameraBoom->TargetArmLength;
	BaseSocketOffset = CameraBoom->SocketOffset;
	BaseChaseFov = ChaseCamera->FieldOfView;
	BaseCockpitFov = CockpitCamera->FieldOfView;
	ApplyUserSettings(true);

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
	Presentation->SetupAudioLayers();
	Presentation->SetupShipLights();
	BuildGearLegs();
	BuildPlaceholderCockpit();
	PlaceCockpitLights();
}

void ASpaceshipPawn::PlaceCockpitLights()
{
	// Cockpit key and fill lights: the hull shadows the cabin (see the properties).
	auto SetupCockpitLight = [this](UPointLightComponent* Light, float IntensityCd, const FVector& Offset)
	{
		if (IntensityCd > 0.f)
		{
			Light->SetRelativeLocation(CockpitCameraBaseLocation + Offset);
			Light->SetIntensity(IntensityCd);
			Light->SetAttenuationRadius(CockpitLightRadiusCm);
			Light->SetLightColor(CockpitLightColor);
			Light->SetSourceRadius(CockpitLightSourceRadiusCm);
			Light->SetSoftSourceRadius(CockpitLightSourceRadiusCm);
			Light->SetVisibility(true);
		}
		else
		{
			Light->SetVisibility(false);
		}
	};
	SetupCockpitLight(CockpitLight, CockpitLightIntensityCd, CockpitLightOffset);
	SetupCockpitLight(CockpitFillLight, CockpitFillIntensityCd, CockpitFillOffset);
	ApplyPowerLights();
}

void ASpaceshipPawn::ApplyPowerLights()
{
	const bool bLit = PowerState != ESpacePowerState::Off;
	CockpitLight->SetVisibility(bLit && CockpitLightIntensityCd > 0.f);
	CockpitFillLight->SetVisibility(bLit && CockpitFillIntensityCd > 0.f);
}

float ASpaceshipPawn::GetPowerBootAlpha() const
{
	switch (PowerState)
	{
	case ESpacePowerState::Off: return 0.f;
	case ESpacePowerState::Booting: return FMath::Clamp(PowerBootElapsed / FMath::Max(PowerBootSeconds, 0.1f), 0.f, 0.999f);
	default: return 1.f;
	}
}

bool ASpaceshipPawn::SetPower(bool bOn, bool bInstant)
{
	if (!bOn && Quantum->GetState() == EQuantumState::Traveling)
	{
		return false;
	}
	const ESpacePowerState Was = PowerState;
	if (!bOn)
	{
		PowerState = ESpacePowerState::Off;
	}
	else if (bInstant)
	{
		PowerState = ESpacePowerState::On;
	}
	else if (PowerState == ESpacePowerState::Off)
	{
		PowerState = ESpacePowerState::Booting;
		PowerBootElapsed = 0.f;
	}
	if (PowerState != Was)
	{
		if (PowerState == ESpacePowerState::Off)
		{
			SetQuantumEngageHeld(false);
			Systems->CutBoostAndAfterburner();
		}
		ApplyPowerLights();
		UE_LOG(LogSpaceship, Log, TEXT("%s: power %s"), *GetName(),
			PowerState == ESpacePowerState::Off ? TEXT("off") : PowerState == ESpacePowerState::Booting ? TEXT("starting up") : TEXT("on"));
	}
	return true;
}

bool ASpaceshipPawn::TogglePower()
{
	return SetPower(PowerState == ESpacePowerState::Off);
}

void ASpaceshipPawn::UpdatePower(float DeltaSeconds)
{
	if (PowerState == ESpacePowerState::Booting)
	{
		PowerBootElapsed += DeltaSeconds;
		if (PowerBootElapsed >= PowerBootSeconds)
		{
			PowerState = ESpacePowerState::On;
			ApplyPowerLights();
			UE_LOG(LogSpaceship, Log, TEXT("%s: power on"), *GetName());
		}
	}
}

bool ASpaceshipPawn::GetPowerControlLocation(FVector& OutLocation) const
{
	// The cockpit generator's socket on the PWR selector (cockpit v2); older builds: from the left display.
	if (GetHullSocketLocation(TEXT("Control_pwr"), OutLocation))
	{
		return true;
	}
	FVector Screen;
	if (!GetHullSocketLocation(TEXT("Display_left"), Screen))
	{
		return false;
	}
	// hs_cockpit.dash: the panel faces the eye (n), right = up x n in Blender's axes; here the same frame in UE's.
	// The PWR rotary is the second of four rows in the left pod's outer control module: 22.75 cm left of the
	// screen's centre, 4.3 cm up, on the module's face ~1.5 cm behind the socket (3 cm before the recess).
	const FVector Normal = (GetPilotEyeLocation() - Screen).GetSafeNormal();
	const FVector Right = (Normal ^ GetActorUpVector()).GetSafeNormal();
	const FVector PanelUp = (Right ^ Normal).GetSafeNormal();
	OutLocation = Screen - Right * 22.75 + PanelUp * 4.3 - Normal * 1.5;
	return true;
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
	if (CockpitFrameRoot)
	{
		CockpitFrameRoot->SetVisibility(bCockpit, true);
	}
	// The canopy glass is right in front of the pilot's eye and would fill the view; the chase camera
	// and everyone else keep it.
	TArray<UStaticMeshComponent*> Meshes;
	GetComponents<UStaticMeshComponent>(Meshes);
	for (UStaticMeshComponent* Mesh : Meshes)
	{
		if (Mesh != Hull && Mesh->GetName().Contains(TEXT("Canopy")))
		{
			Mesh->SetOwnerNoSee(bCockpit && bHideCanopyInCockpit);
		}
	}
}

// -------------------------------------------------------------------------------------------
// Input
// -------------------------------------------------------------------------------------------

void ASpaceshipPawn::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	ShipInput->BindInput(PlayerInputComponent);
}

void ASpaceshipPawn::UnPossessed()
{
	ShipInput->RemoveMappingContexts();
	ClearPilotInput();
	Super::UnPossessed();
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

void ASpaceshipPawn::SetFlightAssist(bool bOn)
{
	if (bOn == bFlightAssist)
	{
		return;
	}
	bFlightAssist = bOn;
	UE_LOG(LogSpaceship, Log, TEXT("%s: %s"), *GetName(), bOn ? TEXT("coupled") : TEXT("decoupled"));
}

void ASpaceshipPawn::SetSpaceBrake(bool bHeld)
{
	bSpaceBrakeHeld = bHeld;
}

float ASpaceshipPawn::GetMasterModeSwitchProgress() const
{
	return Systems->GetMasterModeSwitchProgress(MasterModeSwitchSeconds);
}

void ASpaceshipPawn::RequestMasterMode(EMasterMode Mode)
{
	if (!Systems->RequestMasterMode(Mode))
	{
		return;
	}
	if (Mode == EMasterMode::SCM && Quantum->GetState() == EQuantumState::Traveling)
	{
		// The quantum drive belongs to NAV: leaving NAV drops out of the jump where the ship is.
		EndQuantumJump(EQuantumBlocker::Pilot);
	}
	UE_LOG(LogSpaceship, Log, TEXT("%s: switching to %s"), *GetName(), Mode == EMasterMode::NAV ? TEXT("NAV") : TEXT("SCM"));
}

void ASpaceshipPawn::ToggleMasterMode()
{
	const EMasterMode Target = GetPendingMasterMode();
	RequestMasterMode(Target == EMasterMode::SCM ? EMasterMode::NAV : EMasterMode::SCM);
}

void ASpaceshipPawn::UpdateMasterMode(float DeltaSeconds)
{
	if (Systems->UpdateMasterMode(DeltaSeconds, MasterModeSwitchSeconds))
	{
		Presentation->Kick(0.35f);
	}
}

void ASpaceshipPawn::SetSpeedLimiter(float Fraction)
{
	Systems->SetSpeedLimiter(Fraction, SpeedLimiterMin);
}

void ASpaceshipPawn::AdjustSpeedLimiter(float Notches)
{
	Systems->AdjustSpeedLimiter(Notches, SpeedLimiterStep, SpeedLimiterMin);
}

float ASpaceshipPawn::GetModeMaxSpeed() const
{
	// Precision mode is a smaller SCM for the limiter and the gauge. The hard cap in UpdateLinearMotion
	// stays at the full SCM speed: switched on at speed, the flight computer brakes down with the
	// retro thrusters instead of the overspeed bleed (which would pull ~25 G from SCM speed).
	if (Systems->GetMasterMode() == EMasterMode::NAV)
	{
		return NavMaxSpeed;
	}
	const float Scm = IsPrecisionActive() ? ScmMaxSpeed * PrecisionSpeedFraction : ScmMaxSpeed;
	// VTOL is slower than SCM but never faster than precision mode, which is slower still.
	return FMath::Lerp(Scm, FMath::Min(Scm, VtolMaxSpeed), Systems->GetVtolBlend());
}

float ASpaceshipPawn::GetSpeedLimit() const
{
	// The afterburner's raised limit scales with the limiter too: a half-open limiter gets half of it.
	return GetModeMaxSpeed() * Systems->GetSpeedLimiter() * (1.f + (AfterburnerSpeedMultiplier - 1.f) * Systems->GetAfterburnerBlend());
}

void ASpaceshipPawn::SetGSafe(bool bOn)
{
	bGSafe = bOn;
}

void ASpaceshipPawn::SetComStab(bool bOn)
{
	bComStab = bOn;
}

FVector ASpaceshipPawn::LimitThrustForPilot(const FVector& LocalAcceleration, bool bLateralFirst) const
{
	return FShipFlightModel::LimitThrustForPilot(LocalAcceleration, bLateralFirst, GSafeMaxG, GSafeMaxVerticalG);
}

float ASpaceshipPawn::GetQuantumCooling() const
{
	return Quantum->GetCooling(QuantumCooldownSeconds);
}

float ASpaceshipPawn::GetQuantumTravelProgress() const
{
	return Quantum->GetTravelProgress();
}

float ASpaceshipPawn::GetQuantumEngageHold() const
{
	return Quantum->GetEngageHold(QuantumEngageHoldSeconds);
}

// -------------------------------------------------------------------------------------------
// Free look
// -------------------------------------------------------------------------------------------

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

void ASpaceshipPawn::Interact()
{
	if (bLeaveSeatPending)
	{
		// F again: stay in the seat.
		bLeaveSeatPending = false;
		bSpaceBrakeHeld = false;
		return;
	}
	if (!LeaveSeat() && !RequestLeaveSeatInFlight())
	{
		ExitShip();
	}
}

bool ASpaceshipPawn::CanLeaveSeatInFlight() const
{
	return HasWalkInterior() && PilotCharacterClass != nullptr && IsPowered() && !IsLanded()
		&& Quantum->GetState() != EQuantumState::Traveling && !CanLeaveSeat();
}

bool ASpaceshipPawn::RequestLeaveSeatInFlight()
{
	if (!CanLeaveSeatInFlight())
	{
		return false;
	}
	bLeaveSeatPending = true;
	// Coupled holds the ship still once the pilot is up (decoupled it would drift or fall).
	SetFlightAssist(true);
	UE_LOG(LogSpaceship, Log, TEXT("%s: braking to a hold for the pilot to get up"), *GetName());
	return true;
}

int32 ASpaceshipPawn::FindDoorNear(const FVector& Location, float ReachCm) const { return Boarding->FindDoorNear(Location, ReachCm); }
int32 ASpaceshipPawn::FindDoorAhead(const FVector& Location, const FVector& Facing, float ReachCm) const { return Boarding->FindDoorNear(Location, ReachCm, Facing); }
void ASpaceshipPawn::SetDoorOpen(int32 Door, bool bOpen) { Boarding->SetDoorOpen(Door, bOpen); }
bool ASpaceshipPawn::IsDoorOpen(int32 Door) const { return Boarding->IsDoorOpen(Door); }
int32 ASpaceshipPawn::GetDoorCount() const { return Boarding->GetDoorCount(); }
FVector ASpaceshipPawn::GetDoorLocation(int32 Door) const { return Boarding->GetDoorLocation(Door); }
FVector ASpaceshipPawn::GetDoorPromptLocation(int32 Door) const { return Boarding->GetDoorPromptLocation(Door); }
void ASpaceshipPawn::DebugStepDoors(float DeltaSeconds) { Boarding->TickDoors(DeltaSeconds); }
float ASpaceshipPawn::DebugGetDoorOpenAlpha(int32 Door) const { return Boarding->GetDoorOpenAlpha(Door); }

int32 ASpaceshipPawn::GetMfdPage(int32 Display) const
{
	return CockpitDisplays ? CockpitDisplays->GetPage(Display) : 0;
}

bool ASpaceshipPawn::GetDisplayPoint(int32 Display, const FVector2D& UV, FVector& OutLocation) const
{
	FVector Screen;
	if (!GetHullSocketLocation(Display == 0 ? TEXT("Display_left") : TEXT("Display_right"), Screen))
	{
		return false;
	}
	// The glass faces the eye it was built for (hs_cockpit.oriented: the design eye, socket Cockpit - not the camera,
	// which free look and the seat move; 5. 10. 2026 the hover frames sat a row high); its centre is 3 cm behind the socket.
	FVector DesignEye;
	if (!GetHullSocketLocation(TEXT("Cockpit"), DesignEye))
	{
		DesignEye = GetPilotEyeLocation();
	}
	const FVector Normal = (DesignEye - Screen).GetSafeNormal();
	const FVector Right = (Normal ^ GetActorUpVector()).GetSafeNormal();
	const FVector PanelUp = (Right ^ Normal).GetSafeNormal();
	OutLocation = Screen - Normal * 3.0 + Right * ((UV.X - 0.5) * MfdGlassSizeCm.X) + PanelUp * ((0.5 - UV.Y) * MfdGlassSizeCm.Y);
	return true;
}

void ASpaceshipPawn::CycleMfdPage(int32 Display, int32 Direction)
{
	if (CockpitDisplays)
	{
		CockpitDisplays->CyclePage(Display, Direction);
	}
}

bool ASpaceshipPawn::GetHullSocketLocation(FName Socket, FVector& OutLocation) const
{
	if (!Hull)
	{
		return false;
	}
	const FString Plain = Socket.ToString();
	const FName Candidates[] = { Socket, FName(*(TEXT("SOCKET_") + Plain)) };
	for (const FName& Name : Candidates)
	{
		if (Hull->DoesSocketExist(Name))
		{
			OutLocation = Hull->GetSocketLocation(Name);
			return true;
		}
	}
	return false;
}

FVector ASpaceshipPawn::GetPilotEyeLocation() const
{
	return CockpitCamera ? CockpitCamera->GetComponentLocation() : GetActorLocation();
}

void ASpaceshipPawn::ApplyUserSettings(bool bFlightDefaults)
{
	const USpaceUserSettings* Settings = USpaceUserSettings::Get();
	if (!Settings)
	{
		return;
	}
	bMouseRecenter = !Settings->bVirtualJoystick;
	VJoyDeadzone = FMath::Clamp(Settings->VJoyDeadzone, 0.f, 0.5f);
	if (const float Fov = USpaceUserSettings::GetFieldOfView(); Fov > 0.f)
	{
		BaseCockpitFov = Fov;
	}
	if (bFlightDefaults)
	{
		// The switches as a fresh ship has them; set directly, without the toggles' messages and sounds.
		bFlightAssist = !Settings->bStartDecoupled;
		bGSafe = Settings->bDefaultGSafe;
		bComStab = Settings->bDefaultComStab;
	}
}

void ASpaceshipPawn::UpdateFreeLook(float DeltaSeconds)
{
	if (bFreeLookHeld)
	{
		// Mouse up looks up; pitch is not affected by bInvertPitch, which is about steering.
		const float LookScale = FreeLookSensitivity * USpaceUserSettings::GetMouseSensitivityScale();
		FreeLookTarget.X += MouseLookDelta.X * LookScale;
		if (FreeLookMaxYawDeg < 180.f)
		{
			FreeLookTarget.X = FMath::Clamp(FreeLookTarget.X, -FreeLookMaxYawDeg, FreeLookMaxYawDeg);
		}
		const float PitchSign = USpaceUserSettings::IsFreeLookPitchInverted() ? -1.f : 1.f;
		FreeLookTarget.Y = FMath::Clamp(FreeLookTarget.Y + MouseLookDelta.Y * LookScale * PitchSign, -FreeLookMaxPitchDeg, FreeLookMaxPitchDeg);
		MouseLookDelta = FVector2D::ZeroVector;
		LookInput = FVector2D::ZeroVector;
	}

	const FVector2D Previous = FreeLookAngles;
	const float PreviousFocus = DashboardFocusBlend;
	DashboardFocusBlend = FMath::FInterpTo(DashboardFocusBlend, bDashboardFocusHeld && bDashboardFocusValid ? 1.f : 0.f, DeltaSeconds, DashboardFocusRate);
	if (!bDashboardFocusHeld && DashboardFocusBlend < 0.001f)
	{
		DashboardFocusBlend = 0.f;
	}
	const float Rate = bFreeLookHeld ? FreeLookFollowRate : FreeLookReturnRate;
	FreeLookAngles += (FreeLookTarget - FreeLookAngles) * (1.0 - FMath::Exp(-Rate * DeltaSeconds));
	if (!bFreeLookHeld && FreeLookAngles.GetAbsMax() < 0.05)
	{
		FreeLookAngles = FVector2D::ZeroVector;
	}
	// While focused the head's turn is set every frame: anything that puts the camera straight (getting
	// in, the shots) would otherwise leave the view zoomed in on the sky.
	if (FreeLookAngles == Previous && DashboardFocusBlend == PreviousFocus && DashboardFocusBlend == 0.f && CockpitViewPitchDeg == 0.f)
	{
		return;  // nothing moved (the usual case: not free looking)
	}

	// Chase: the boom swings around the ship. Cockpit: the head turns.
	const FRotator Offset(float(FreeLookAngles.Y), float(FreeLookAngles.X), 0.f);
	CameraBoom->SetRelativeRotation(Offset);
	ApplyCockpitRotation();
}

void ASpaceshipPawn::ApplyCockpitRotation()
{
	// The head turns to the dashboard first, free look on top of that.
	const FQuat Rest = FRotator(CockpitViewPitchDeg, 0.f, 0.f).Quaternion();
	const FQuat Focus = FQuat::Slerp(Rest, DashboardFocusRotation.Quaternion(), DashboardFocusBlend);
	const FRotator Offset(float(FreeLookAngles.Y), float(FreeLookAngles.X), 0.f);
	CockpitCamera->SetRelativeRotation(Focus * Offset.Quaternion());
}

void ASpaceshipPawn::SetDashboardFocus(bool bFocus)
{
	if (bFocus && !bDashboardFocusHeld)
	{
		bDashboardFocusValid = ComputeDashboardFocus(DashboardFocusEye, DashboardFocusRotation, DashboardFocusFov);
	}
	bDashboardFocusHeld = bFocus;
}

bool ASpaceshipPawn::ComputeDashboardFocus(FVector& OutEye, FRotator& OutRotation, float& OutFovDeg) const
{
	// Where the displays are, in the ship's frame (the cockpit camera hangs off the root).
	const FTransform ActorTransform = GetActorTransform();
	TArray<FVector> Displays;
	TInlineComponentArray<UMeshComponent*> Meshes(this);
	for (const UMeshComponent* Mesh : Meshes)
	{
		for (const FName& Socket : Mesh->GetAllSocketNames())
		{
			if (Socket.ToString().StartsWith(TEXT("Display_")))
			{
				Displays.Add(ActorTransform.InverseTransformPositionNoScale(Mesh->GetSocketLocation(Socket)));
			}
		}
	}
	if (Displays.Num() == 0)
	{
		return false;
	}
	FVector Centre = FVector::ZeroVector;
	for (const FVector& Display : Displays)
	{
		Centre += Display / Displays.Num();
	}
	// Before BeginPlay (headless tests) the base is not known yet: the camera is still on it.
	const FVector Eye0 = CockpitCameraBaseLocation.IsZero() ? CockpitCamera->GetRelativeLocation() : CockpitCameraBaseLocation;
	const FVector Towards = (Centre - Eye0).GetSafeNormal();
	OutEye = Eye0 + Towards * DashboardFocusLeanCm;
	OutRotation = (Centre - OutEye).Rotation();
	OutRotation.Roll = 0.f;
	// The narrowest view that still holds every display with a margin, at the window's shape.
	FVector2D Viewport(16.0, 9.0);
	if (GEngine && GEngine->GameViewport)
	{
		GEngine->GameViewport->GetViewportSize(Viewport);
	}
	const double Aspect = Viewport.Y > 0.0 ? Viewport.X / Viewport.Y : 16.0 / 9.0;
	const FVector2D Half = DashboardDisplayHalfSizeCm * (1.0 + DashboardFocusMargin);
	double TanWide = 0.0;
	for (const FVector& Display : Displays)
	{
		const FVector Local = OutRotation.UnrotateVector(Display - OutEye);
		if (Local.X <= 1.0)
		{
			continue;
		}
		TanWide = FMath::Max(TanWide, (FMath::Abs(Local.Y) + Half.X) / Local.X);
		TanWide = FMath::Max(TanWide, (FMath::Abs(Local.Z) + Half.Y) / Local.X * Aspect);
	}
	OutFovDeg = float(FMath::Clamp(2.0 * FMath::RadiansToDegrees(FMath::Atan(TanWide)), 20.0, double(BaseCockpitFov)));
	return true;
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
	Systems->SetBoostHeld(false);
	Systems->SetAfterburnerHeld(false);
	bSpaceBrakeHeld = false;
}

// -------------------------------------------------------------------------------------------
// Exit and boarding
// -------------------------------------------------------------------------------------------

bool ASpaceshipPawn::CanExit() const
{
	return Boarding->CanExit();
}

double ASpaceshipPawn::GetDistanceToHull(const FVector& Location) const
{
	return Boarding->GetDistanceToHull(Location);
}

FVector ASpaceshipPawn::ComputeSideExitLocation(const FVector& ShipLocation, const FRotator& ShipRotation, const FVector& HullExtent, float CapsuleRadius, float ClearanceCm)
{
	return UShipBoardingComponent::ComputeSideExitLocation(ShipLocation, ShipRotation, HullExtent, CapsuleRadius, ClearanceCm);
}

TArray<FBox> ASpaceshipPawn::GetHullCollisionBoxes() const
{
	return Boarding->GetHullCollisionBoxes();
}

double ASpaceshipPawn::GetHullClearance(const FVector& Location, float CapsuleRadius, float CapsuleHalfHeight) const
{
	return Boarding->GetHullClearance(Location, CapsuleRadius, CapsuleHalfHeight);
}

TArray<FVector> ASpaceshipPawn::GetExitCandidates() const
{
	return Boarding->GetExitCandidates();
}

FTransform ASpaceshipPawn::ComputeExitTransform() const
{
	return Boarding->ComputeExitTransform();
}

APawn* ASpaceshipPawn::ExitShip()
{
	return Boarding->ExitShip();
}

void ASpaceshipPawn::OnBoarded()
{
	Boarding->OnBoarded();
}

bool ASpaceshipPawn::HasWalkInterior() const
{
	return Boarding->HasWalkInterior();
}

bool ASpaceshipPawn::CanLeaveSeat() const
{
	return Boarding->CanLeaveSeat();
}

FTransform ASpaceshipPawn::GetWalkSocketTransform(FName Socket) const
{
	return Boarding->GetWalkSocketTransform(Socket);
}

bool ASpaceshipPawn::IsNearSeat(const FVector& Location) const
{
	return Boarding->IsNearSeat(Location);
}

bool ASpaceshipPawn::IsNearRamp(const FVector& Location) const
{
	return Boarding->IsNearRamp(Location);
}

void ASpaceshipPawn::SetInteriorWalk(bool bWalking)
{
	Boarding->SetInteriorWalk(bWalking);
}

APawn* ASpaceshipPawn::LeaveSeat()
{
	return Boarding->LeaveSeat();
}

// -------------------------------------------------------------------------------------------
// Flight model
// -------------------------------------------------------------------------------------------

void ASpaceshipPawn::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	StepFlight(DeltaSeconds);
	Boarding->TickDoors(DeltaSeconds);
	Presentation->UpdateCameraEffects(DeltaSeconds);
	Presentation->UpdateEngineAudio(DeltaSeconds);
	Presentation->UpdateShipLights(DeltaSeconds);
	Presentation->UpdateSpaceDust(DeltaSeconds);
	Presentation->UpdateViewCollection();

	if (CameraSnapTicks > 0 && --CameraSnapTicks == 0)
	{
		CameraBoom->bEnableCameraLag = true;
	}
	// Still enough: up from the seat (once; without a player to stand up the request just ends).
	if (bLeaveSeatPending && CanLeaveSeat())
	{
		bLeaveSeatPending = false;
		bSpaceBrakeHeld = false;
		LeaveSeat();
	}
}

void ASpaceshipPawn::StepFlight(float DeltaSeconds)
{
	UpdatePower(DeltaSeconds);
	if (!IsPowered())
	{
		// No power, no thrusters (and no boost, afterburner or quantum below).
		Systems->SetBoostHeld(false);
		Systems->SetAfterburnerHeld(false);
		bSpaceBrakeHeld = false;
	}
	UpdateEnvironment(DeltaSeconds);
	UpdateMasterMode(DeltaSeconds);
	UpdateVtol(DeltaSeconds);
	UpdateGear(DeltaSeconds);
	UpdateLanding(DeltaSeconds);
	UpdateBoost(DeltaSeconds);
	UpdateAfterburner(DeltaSeconds);
	UpdateQuantum(DeltaSeconds);
	// Before steering: while held it takes the mouse movement for itself.
	UpdateFreeLook(DeltaSeconds);
	if (bLeaveSeatPending && (!CanLeaveSeatInFlight() && !CanLeaveSeat()))
	{
		bLeaveSeatPending = false;
		bSpaceBrakeHeld = false;
	}
	if (bLeaveSeatPending)
	{
		// Braking to a hold: the pilot has let go of the controls.
		ThrustInput = StrafeInput = LiftInput = RollInput = 0.f;
		LookInput = FVector2D::ZeroVector;
		MouseLookDelta = FVector2D::ZeroVector;
		MouseStick = FVector2D::ZeroVector;
		bSpaceBrakeHeld = true;
	}
	if (!IsPowered())
	{
		// The keys and the stick move nothing; free look above still turns the pilot's head.
		ThrustInput = StrafeInput = LiftInput = RollInput = 0.f;
		LookInput = FVector2D::ZeroVector;
		MouseLookDelta = FVector2D::ZeroVector;
		MouseStick = FVector2D::ZeroVector;
	}
	if (Landing->GetState() == ELandingState::Landed)
	{
		UpdateLandedMotion(DeltaSeconds);
	}
	else if (Quantum->GetState() == EQuantumState::Traveling)
	{
		UpdateQuantumTravel(DeltaSeconds);
	}
	else
	{
		// Rotate first so this frame's thrust is applied along the heading the player just commanded.
		UpdateAngularMotion(DeltaSeconds);
		UpdateLinearMotion(DeltaSeconds);
	}
}

// -------------------------------------------------------------------------------------------
// Boost, afterburner and the quantum drive
// -------------------------------------------------------------------------------------------

void ASpaceshipPawn::UpdateBoost(float DeltaSeconds)
{
	// Boost feeds the manoeuvring thrusters and rotation, so it burns energy whenever Shift is held.
	const bool bAllowed = Quantum->GetState() != EQuantumState::Traveling && Landing->GetState() != ELandingState::Landed;
	const FShipReserve::FTuning Tuning{BoostDurationSeconds, BoostRechargeSeconds, BoostRechargeDelaySeconds, BoostUnlockFraction};
	if (Systems->UpdateBoost(DeltaSeconds, bAllowed, Tuning))
	{
		Presentation->Kick(0.3f);
	}
}

void ASpaceshipPawn::UpdateAfterburner(float DeltaSeconds)
{
	// SCM only (NAV already flies at five times SCM speed and has the quantum drive), and only while it
	// can do something: W forward, no spacebrake, flying. VTOL refuses it too - the mains are down to a
	// third and the ship is standing on its lift thrusters (SC-2b).
	const bool bAllowed = ThrustInput > 0.f && !bSpaceBrakeHeld && Systems->GetMasterMode() == EMasterMode::SCM
		&& !IsPrecisionActive() && !Systems->IsVtolOn() && Quantum->GetState() != EQuantumState::Traveling
		&& Landing->GetState() != ELandingState::Landed;
	const FShipReserve::FTuning Tuning{AfterburnerDurationSeconds, AfterburnerRefillSeconds, AfterburnerRefillDelaySeconds,
		AfterburnerUnlockFraction};
	if (Systems->UpdateAfterburner(DeltaSeconds, bAllowed, Tuning, AfterburnerSpoolSeconds, AfterburnerFadeSeconds))
	{
		Presentation->Kick(1.f);
		PlayOneShot(BoostStartSound);
	}
}

bool ASpaceshipPawn::SegmentHitsSphere(const FVector& Start, const FVector& End, const FVector& Centre, double Radius)
{
	return FShipFlightModel::SegmentHitsSphere(Start, End, Centre, Radius);
}

FShipFlightModel::FQuantumDrive ASpaceshipPawn::GetQuantumDrive() const
{
	FShipFlightModel::FQuantumDrive Drive;
	Drive.RampSeconds = QuantumRampSeconds;
	Drive.AccelerationKmS2 = QuantumAccelerationKmS2;
	Drive.MaxSpeedKmS = QuantumMaxSpeedKmS;
	Drive.ExitSpeed = QuantumExitSpeed;
	Drive.ArrivalRadii = QuantumArrivalRadii;
	Drive.MinArrivalKm = QuantumMinArrivalKm;
	Drive.FuelPer1000Km = QuantumFuelPer1000Km;
	return Drive;
}

FShipQuantumRules ASpaceshipPawn::GetQuantumRules() const
{
	FShipQuantumRules Rules;
	Rules.Drive = GetQuantumDrive();
	Rules.PickDeg = QuantumPickDeg;
	Rules.AlignDeg = QuantumAlignDeg;
	Rules.MinJumpKm = QuantumMinJumpKm;
	Rules.SpoolSeconds = QuantumSpoolSeconds;
	Rules.CalibrationSeconds = QuantumCalibrationSeconds;
	Rules.EngageHoldSeconds = QuantumEngageHoldSeconds;
	Rules.CooldownSeconds = QuantumCooldownSeconds;
	return Rules;
}

double ASpaceshipPawn::ComputeQuantumArrivalAltitude(double BodyRadiusCm) const
{
	return FShipFlightModel::QuantumArrivalAltitude(BodyRadiusCm, GetQuantumDrive());
}

double ASpaceshipPawn::ComputeQuantumSpeed(double RemainingCm, double CurrentSpeedCmS, float DeltaSeconds) const
{
	return ComputeQuantumSpeedAt(RemainingCm, CurrentSpeedCmS, DeltaSeconds, 1.0e6f);
}

double ASpaceshipPawn::ComputeQuantumSpeedAt(double RemainingCm, double CurrentSpeedCmS, float DeltaSeconds, float SecondsIntoJump) const
{
	return FShipFlightModel::QuantumSpeedAt(RemainingCm, CurrentSpeedCmS, DeltaSeconds, SecondsIntoJump, GetQuantumDrive());
}

float ASpaceshipPawn::ComputeQuantumFuelUse(double DistanceCm) const
{
	return FShipFlightModel::QuantumFuelUse(DistanceCm, GetQuantumDrive());
}

void ASpaceshipPawn::SetQuantumEngageHeld(bool bHeld)
{
	Quantum->SetEngageHeld(bHeld);
	if (!bHeld && QuantumChargeAudio)
	{
		QuantumChargeAudio->FadeOut(0.2f, 0.f);
		QuantumChargeAudio = nullptr;
	}
}

void ASpaceshipPawn::UpdateQuantum(float DeltaSeconds)
{
	FShipQuantumContext Context;
	Context.Location = GetActorLocation();
	Context.Nose = GetActorForwardVector();
	// Without power the drive cannot spool: treated as the landed case, which blocks it.
	Context.bLanded = Landing->GetState() == ELandingState::Landed || !IsPowered();
	Context.bInNav = Systems->GetMasterMode() == EMasterMode::NAV && !Systems->IsMasterModeSwitching();
	const UShipQuantumComponent::FFrame Frame = Quantum->Update(DeltaSeconds, Context, GetQuantumRules());
	// Engage: the button held for QuantumEngageHoldSeconds while ready.
	if (Frame.bChargeStarted && !QuantumChargeAudio)
	{
		QuantumChargeAudio = PlayOneShot(QuantumChargeSound);
	}
	if (Frame.bEngage)
	{
		BeginQuantumJump();
	}
}

void ASpaceshipPawn::BeginQuantumJump()
{
	Quantum->BeginJump(GetQuantumRules());
	Systems->CutBoostAndAfterburner();
	Systems->ClearVtol();
	// A lighter jolt than a drop-out: the jump now builds up (QuantumRampSeconds) rather than snapping.
	Presentation->SetKick(0.4f);
	QuantumChargeAudio = nullptr;
	PlayOneShot(QuantumEngageSound);
	// The jump's burst of green light (the reference at 4:10).
	SpeedTunnel->TriggerFlare(1.6f);
	UE_LOG(LogSpaceship, Log, TEXT("%s: quantum jump to %s, %.0f km, fuel left %.0f%%"), *GetName(),
		*Quantum->GetTargetName().ToString(), Quantum->GetJumpLengthCm() / 100000.0, Quantum->GetFuel() * 100.f);
}

void ASpaceshipPawn::EndQuantumJump(EQuantumBlocker Reason)
{
	Quantum->EndJump(Reason, GetQuantumRules());
	Presentation->SetKick(1.f);
	// Out at NAV speed at most; the overspeed bleed takes the rest.
	const double Speed = LinearVelocity.Size();
	if (Speed > QuantumExitSpeed)
	{
		LinearVelocity *= QuantumExitSpeed / Speed;
	}
	AngularVelocity = FVector::ZeroVector;
	PlayOneShot(QuantumExitSound);
	UE_LOG(LogSpaceship, Log, TEXT("%s: quantum exit (%s) %.0f km from %s"), *GetName(),
		Reason == EQuantumBlocker::Pilot ? TEXT("pilot") : TEXT("arrived"), Quantum->GetTargetDistanceCm() / 100000.0, *Quantum->GetTargetName().ToString());
}

void ASpaceshipPawn::UpdateQuantumTravel(float DeltaSeconds)
{
	const FVector Location = GetActorLocation();
	UShipQuantumComponent::FTravelStep Travel;
	if (!Quantum->StepTravel(DeltaSeconds, Location, LinearVelocity.Size(), GetQuantumRules(), Travel))
	{
		EndQuantumJump(EQuantumBlocker::NoTarget);
		return;
	}
	const FVector Direction = Travel.Direction;

	// No steering in a jump (the reference says so outright): the nose swings onto the destination.
	const FQuat Facing = FRotationMatrix::MakeFromXZ(Direction, GetActorUpVector()).ToQuat();
	const FQuat Rotation = FQuat::Slerp(GetActorQuat(), Facing, FMath::Min(1.f, 3.f * DeltaSeconds));
	AngularVelocity = FVector::ZeroVector;
	EngineDemand = 0.6f;
	ThrusterAcceleration = FVector::ZeroVector;
	GForce = FMath::FInterpTo(GForce, 0.f, DeltaSeconds, 8.f);

	if (Travel.bArrives)
	{
		SetActorLocationAndRotation(Location + Direction * Travel.RemainingCm, Rotation);
		LinearVelocity = Direction * QuantumExitSpeed;
		EndQuantumJump(EQuantumBlocker::None);
		return;
	}
	LinearVelocity = Direction * Travel.Speed;
	// No sweep: the path was checked for bodies before the jump, and at tens of km/s a sweep per
	// frame against the terrain would cost more than it could ever find.
	SetActorLocationAndRotation(Location + Direction * Travel.StepCm, Rotation);
}

// -------------------------------------------------------------------------------------------
// Motion
// -------------------------------------------------------------------------------------------

void ASpaceshipPawn::UpdateAngularMotion(float DeltaSeconds)
{
	// Mouse steering works on a stick position, never on a per-frame delta turned straight into a
	// turn rate: that made steering frame-rate dependent (at 120 FPS each frame sees half the pixels).
	FVector2D MouseCommand;
	if (bMouseRecenter)
	{
		// Spring-centred stick: the steady deflection depends on mouse speed per second.
		MouseStick *= FMath::Exp(-MouseRecenterRate * DeltaSeconds);
		MouseStick += MouseLookDelta * (MouseSensitivity * USpaceUserSettings::GetMouseSensitivityScale());
		MouseStick.X = FMath::Clamp(MouseStick.X, -1., 1.);
		MouseStick.Y = FMath::Clamp(MouseStick.Y, -1., 1.);
		MouseCommand = MouseStick;
	}
	else
	{
		// Star Citizen virtual joystick: the cursor moves inside the unit circle and stays put.
		MouseStick += MouseLookDelta * (USpaceUserSettings::GetMouseSensitivityScale() / FMath::Max(VJoyCountsToFull, 1.f));
		if (MouseStick.SizeSquared() > 1.0)
		{
			MouseStick.Normalize();
		}
		// Nothing inside the dead zone, then linear from its edge to the rim.
		const double Deflection = MouseStick.Size();
		MouseCommand = Deflection <= VJoyDeadzone ? FVector2D::ZeroVector
			: MouseStick * ((Deflection - VJoyDeadzone) / (FMath::Max(1.0 - VJoyDeadzone, 0.01) * Deflection));
	}
	MouseLookDelta = FVector2D::ZeroVector;

	// Stick and mouse are both a fraction of the maximum rotation rate, so they simply add.
	const FVector2D Command(
		FMath::Clamp(MouseCommand.X + LookInput.X, -1., 1.),
		FMath::Clamp(MouseCommand.Y + LookInput.Y, -1., 1.));
	const bool bInvert = bInvertPitch != USpaceUserSettings::IsShipPitchInverted();
	const float PitchCommand = bFreeLookHeld ? 0.f : Command.Y * (bInvert ? -1.f : 1.f);
	const float YawCommand = bFreeLookHeld ? 0.f : Command.X;
	// NAV turns slower than SCM.
	float RateScale = 1.f;
	if (Systems->GetMasterMode() == EMasterMode::NAV)
	{
		RateScale *= NavTurnScale;
	}
	// Boost feeds the manoeuvring thrusters: faster turns, and faster to start and stop them.
	// Precision mode turns gently, and starts and stops turns as gently.
	const double RotationBoost = (Systems->IsBoostActive() ? BoostRotationMultiplier : 1.0) * (IsPrecisionActive() ? PrecisionTurnScale : 1.0);
	RateScale *= float(RotationBoost);

	FVector TargetRates(
		RollInput * RollRate * RateScale,
		PitchCommand * PitchRate * RateScale,
		YawCommand * YawRate * RateScale);

	const double Speed = LinearVelocity.Size();
	SlipAngleDeg = Speed < ComStabMinSpeed ? 0.f
		: float(FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp((LinearVelocity / Speed) | GetActorForwardVector(), -1.0, 1.0))));
	const bool bCoupledTurns = bFlightAssist || bSpaceBrakeHeld;
	if (bCoupledTurns && IsGSafeActive() && Speed > 1.0)
	{
		// Bending the flight path at rate w takes Speed x w of sideways thrust: keep that under GSafeTurnG.
		const double MaxRateDeg = FMath::RadiansToDegrees(GSafeTurnG * SpaceshipPawnDefaults::StandardGravityCmS2 / Speed);
		auto Limit = [this, MaxRateDeg](double Target, double FullRate)
		{
			const double Allowed = FMath::Max(MaxRateDeg, FullRate * GSafeMinTurnFraction);
			return FMath::Clamp(Target, -Allowed, Allowed);
		};
		TargetRates.Y = Limit(TargetRates.Y, PitchRate * RateScale);
		TargetRates.Z = Limit(TargetRates.Z, YawRate * RateScale);
	}
	if (bCoupledTurns && bComStab && SlipAngleDeg > ComStabSlipStartDeg)
	{
		// Sliding: turn slower so the thrusters can swing the flight path back onto the nose.
		const double Alpha = FMath::Clamp((SlipAngleDeg - ComStabSlipStartDeg) / FMath::Max(ComStabSlipFullDeg - ComStabSlipStartDeg, 0.1f), 0.0, 1.0);
		const double Scale = FMath::Lerp(1.0, double(ComStabMinTurnFraction), Alpha);
		TargetRates.Y *= Scale;
		TargetRates.Z *= Scale;
	}

	// Rotational inertia: ease towards the target rate, but never change it faster than the
	// thrusters can (the per-axis angular acceleration).
	const double Ease = FMath::Min(double(AngularResponsiveness) * DeltaSeconds, 1.0);
	auto StepRate = [DeltaSeconds, Ease](double Current, double Target, double Acceleration)
	{
		const double MaxStep = Acceleration * DeltaSeconds;
		return Current + FMath::Clamp((Target - Current) * Ease, -MaxStep, MaxStep);
	};
	AngularVelocity = FVector(
		StepRate(AngularVelocity.X, TargetRates.X, RollAcceleration * RotationBoost),
		StepRate(AngularVelocity.Y, TargetRates.Y, PitchAcceleration * RotationBoost),
		StepRate(AngularVelocity.Z, TargetRates.Z, YawAcceleration * RotationBoost));
	if (bFreeLookHeld)
	{
		// Heading frozen where it was; roll (keys) still works, and the flight path is untouched.
		AngularVelocity.Y = 0.0;
		AngularVelocity.Z = 0.0;
	}

	// VTOL holds the ship level (SC-2b): with the stick still and gravity to tell it which way is up,
	// pitch and roll are turned back towards the horizon. Any stick input takes it straight back.
	if (bHasEnvironment && FMath::IsNearlyZero(TargetRates.X) && FMath::IsNearlyZero(TargetRates.Y))
	{
		AddActorLocalRotation(ComputeVtolLevelStep(Environment.Up, DeltaSeconds));
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

	{
		// What each thruster direction can do. NAV keeps main and retro but halves manoeuvring; boost
		// strengthens the manoeuvring thrusters (retro included), the afterburner the main ones.
		const double Maneuver = (Systems->GetMasterMode() == EMasterMode::NAV ? NavManeuverScale : 1.0)
			* (Systems->IsBoostActive() ? BoostManeuverMultiplier : 1.0);
		// VTOL (SC-2b): the thrust moves off the mains and onto the lift and lateral thrusters.
		const double Vtol = double(Systems->GetVtolBlend());
		const double VtolMain = FMath::Lerp(1.0, double(VtolThrustFraction), Vtol);
		const double VtolLift = FMath::Lerp(1.0, double(VtolLiftMultiplier), Vtol);
		const double VtolStrafe = FMath::Lerp(1.0, double(VtolStrafeMultiplier), Vtol);
		const double ForwardCap = ThrustAcceleration * (Systems->IsAfterburnerActive() ? AfterburnerThrustMultiplier : 1.0) * VtolMain;
		const double RetroCap = RetroAcceleration * (Systems->IsBoostActive() ? BoostManeuverMultiplier : 1.0) * VtolMain;
		const double StrafeCap = StrafeAcceleration * Maneuver * VtolStrafe;
		const double UpCap = LiftAcceleration * Maneuver * VtolLift;
		const double DownCap = DownAcceleration * Maneuver * VtolLift;
		const double SpeedLimit = GetSpeedLimit();
		const double SpeedBefore = LinearVelocity.Size();
		// The spacebrake is coupled flight towards zero, whatever the coupled switch says.
		const bool bCoupled = bFlightAssist || bSpaceBrakeHeld;
		FVector LocalAcceleration;

		if (bCoupled)
		{
			// Coupled: the keys ask for a velocity, up to the speed limit; what they do not ask for
			// (a released key, every axis under the spacebrake) is braked to zero.
			FVector DesiredLocal = FVector::ZeroVector;
			if (!bSpaceBrakeHeld)
			{
				DesiredLocal = FVector(ThrustInput, StrafeInput, LiftInput) * SpeedLimit;
				if (DesiredLocal.Size() > SpeedLimit)
				{
					DesiredLocal *= SpeedLimit / DesiredLocal.Size();
				}
				if (Systems->GetVtolBlend() > 0.f)
				{
					// In VTOL Space and Ctrl are a climb rate, not another way of reaching the top speed.
					const double ClimbLimit = FMath::Lerp(SpeedLimit, double(VtolClimbSpeed) * Systems->GetSpeedLimiter(), double(Systems->GetVtolBlend()));
					DesiredLocal.Z = FMath::Clamp(DesiredLocal.Z, -ClimbLimit, ClimbLimit);
				}
				if (LiftInput < 0.f && bHasEnvironment)
				{
					// Descending gets gentler towards the ground, down to LandingDescentSpeed.
					const double Near = FMath::Clamp(Environment.AltitudeAboveTerrainCm / 2000.0, 0.0, 1.0);
					const double DescentLimit = FMath::Lerp(double(LandingDescentSpeed), SpeedLimit, Near);
					DesiredLocal.Z = FMath::Max(DesiredLocal.Z, -DescentLimit);
				}
			}
			const FVector VelocityLocal = Rotation.UnrotateVector(LinearVelocity);

			// Hovering over the ground with nothing held, hold a little less than gravity so the ship
			// sinks onto its gear on its own.
			double GravityHold = 1.0;
			if (Landing->HasGroundInfo() && Landing->GetGroundGapCm() >= 0.f && Landing->GetGroundGapCm() - GetGearGroundOffsetCm() < 400.f && ThrustInput == 0.f && LiftInput <= 0.f && !bSpaceBrakeHeld)
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
			// Decoupled: the keys fire the thrusters, nothing else does.
			LocalAcceleration = FVector(
				ThrustInput * (ThrustInput > 0.f ? ForwardCap : RetroCap),
				StrafeInput * StrafeCap,
				LiftInput * (LiftInput > 0.f ? UpCap : DownCap));
		}

		// Every thruster direction has its limit, flight computer or not; then G-Safe on top, unless
		// boost suspends it.
		LocalAcceleration.X = FMath::Clamp(LocalAcceleration.X, -RetroCap, ForwardCap);
		LocalAcceleration.Y = FMath::Clamp(LocalAcceleration.Y, -StrafeCap, StrafeCap);
		LocalAcceleration.Z = FMath::Clamp(LocalAcceleration.Z, -DownCap, UpCap);
		if (IsGSafeActive())
		{
			LocalAcceleration = LimitThrustForPilot(LocalAcceleration, bComStab && bCoupled);
		}
		if (!IsPowered())
		{
			// No power: the ship falls or drifts (SC: a ship powered off in flight drops).
			LocalAcceleration = FVector::ZeroVector;
		}
		// How hard the engines are working, for the glow and the sound. The vertical axis is measured
		// against a hover's worth of thrust (HoverThrustReferenceG), not against what the lift
		// thrusters could do: holding station over Veyra is 0.46 G of a possible 5.5, so against the
		// full capacity it read as 0.06 and hovering looked dead (HANDOFF kapitola 11, SC-2b).
		const double HoverReference = FMath::Max(double(HoverThrustReferenceG) * SpaceshipPawnDefaults::StandardGravityCmS2, 1.0);
		EngineDemand = float(FMath::Clamp(FMath::Max3(
			FMath::Abs(LocalAcceleration.X) / FMath::Max(LocalAcceleration.X >= 0.0 ? ForwardCap : RetroCap, 1.0),
			0.7 * FMath::Abs(LocalAcceleration.Y) / FMath::Max(StrafeCap, 1.0),
			FMath::Abs(LocalAcceleration.Z) / HoverReference), 0.0, 1.0));
		GForce = FMath::FInterpTo(GForce, float(LocalAcceleration.Size() / SpaceshipPawnDefaults::StandardGravityCmS2), DeltaSeconds, 8.f);
		ThrusterAcceleration = LocalAcceleration;
		ThrusterCapPositive = FVector(ForwardCap, StrafeCap, UpCap);
		ThrusterCapNegative = FVector(RetroCap, StrafeCap, DownCap);

		LinearVelocity += Rotation.RotateVector(LocalAcceleration) * DeltaSeconds;

		// Drag and gravity, the same terms as ComputeEnvironmentAcceleration. Drag is applied as a
		// damping fraction clamped to 1, so a long frame in dense air can stop the ship but never
		// reverse it.
		LinearVelocity -= LinearVelocity * FMath::Min(DragRate * DeltaSeconds, 1.0);
		if (bHasEnvironment)
		{
			LinearVelocity -= Up * (Gravity * DeltaSeconds);
		}
		if (Landing->HasGroundContact())
		{
			// After gravity, so on a gentle slope friction cancels this frame's pull down the slope
			// completely and the ship stands still instead of creeping. The load is everything pressing the
			// ship into the ground, thrusters included: holding descend on a slope pressed it in and, with
			// gravity alone as the load, slid it downhill for as long as the key was held.
			const FVector GroundNormal = Landing->GetGroundNormal();
			const FVector Pressing = Rotation.RotateVector(LocalAcceleration) - (bHasEnvironment ? Up * Gravity : FVector::ZeroVector);
			// Never less than the ship's weight, as before: the flight computer's hover thrust takes most of it.
			const float Load = float(FMath::Max(-(Pressing | GroundNormal), Gravity * FMath::Max(0.0, GroundNormal | Up)));
			LinearVelocity = ApplyGroundFriction(LinearVelocity, GroundNormal, GroundNormal, Load, DeltaSeconds);
		}

		const double Speed = LinearVelocity.Size();
		{
			const double ModeTop = Systems->GetMasterMode() == EMasterMode::NAV ? NavMaxSpeed : ScmMaxSpeed;
			const double SpeedCap = ModeTop * (1.0 + (AfterburnerSpeedMultiplier - 1.0) * Systems->GetAfterburnerBlend());
			if (Speed > SpeedCap)
			{
				// Above the mode's top speed (afterburner fading, or leaving NAV for SCM): while the
				// afterburner pushes this is an ordinary clamp, otherwise the excess bleeds off.
				const double Excess = (Speed - SpeedCap) * FMath::Min(double(OverspeedDecay) * DeltaSeconds, 1.0);
				const double Target = Systems->IsAfterburnerActive() ? SpeedCap : Speed - Excess;
				LinearVelocity *= FMath::Max(Target, SpeedCap) / Speed;
			}
			else if (!bCoupled && Speed > SpeedLimit && Speed > SpeedBefore)
			{
				// Decoupled keeps whatever speed it has, but the thrusters cannot push past the limiter.
				LinearVelocity *= FMath::Max(SpeedBefore, SpeedLimit) / Speed;
			}
		}
	}

	ApplyGearSupport(DeltaSeconds);

	if (LinearVelocity.IsNearlyZero())
	{
		LinearVelocity = FVector::ZeroVector;
		return;
	}

	const FVector Delta = LinearVelocity * DeltaSeconds;
	FHitResult Hit;
	MoveHull(Delta, Hit);

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
			FHitResult SlideHit;
			MoveHull(Slide, SlideHit);
		}
	}
}

FShipFlightModel::FDrag ASpaceshipPawn::GetDragTuning() const
{
	FShipFlightModel::FDrag Drag;
	Drag.SpaceLinearDamping = SpaceLinearDamping;
	Drag.LinearDamping = LinearDamping;
	Drag.QuadraticDrag = QuadraticDrag;
	Drag.GravityScale = GravityScale;
	return Drag;
}

FVector ASpaceshipPawn::ComputeEnvironmentAcceleration(const FCelestialEnvironment& InEnvironment, const FVector& Velocity) const
{
	return FShipFlightModel::EnvironmentAcceleration(InEnvironment, Velocity, GetDragTuning());
}

FShipFlightModel::FHeat ASpaceshipPawn::GetHeatTuning() const
{
	FShipFlightModel::FHeat HeatTuning;
	HeatTuning.ReferenceSpeed = HeatReferenceSpeed;
	HeatTuning.Onset = HeatOnset;
	HeatTuning.Full = HeatFull;
	return HeatTuning;
}

float ASpaceshipPawn::ComputeHeatTarget(float AtmosphereDensity, float SpeedCmS) const
{
	return FShipFlightModel::HeatTarget(AtmosphereDensity, SpeedCmS, GetHeatTuning());
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

FShipFlightModel::FLandingLimits ASpaceshipPawn::GetLandingLimits() const
{
	FShipFlightModel::FLandingLimits Limits;
	Limits.MaxGapCm = LandingMaxGapCm;
	Limits.MaxSlopeDeg = MaxLandingSlopeDeg;
	Limits.MaxSpeed = LandingMaxSpeed;
	Limits.MaxTiltDeg = LandingMaxTiltDeg;
	return Limits;
}

FShipLandingRules ASpaceshipPawn::GetLandingRules() const
{
	FShipLandingRules Rules;
	Rules.Limits = GetLandingLimits();
	Rules.GearExtensionCm = GearExtensionCm;
	Rules.ConfirmSeconds = LandingConfirmSeconds;
	Rules.TakeoffCooldownSeconds = TakeoffCooldownSeconds;
	return Rules;
}

ELandingBlocker ASpaceshipPawn::EvaluateTouchdown(float HullGap, float Speed, float TiltDeg, float SlopeDeg, bool bEngineInput, bool bGearDown) const
{
	return FShipFlightModel::EvaluateTouchdown(HullGap, Speed, TiltDeg, SlopeDeg, bEngineInput, bGearDown, GearExtensionCm, GetLandingLimits());
}

bool ASpaceshipPawn::ComputeTripodRest(const FVector& Location, const FRotator& Rotation, const TArray<FVector>& PadsLocal,
	const TArray<FVector>& Ground, float RestHeightCm, FVector& OutLocation, FRotator& OutRotation, FVector& OutNormal)
{
	if (PadsLocal.Num() != 3 || Ground.Num() != 3)
	{
		return false;
	}
	const FVector Pads[3] = { PadsLocal[0], PadsLocal[1], PadsLocal[2] };
	const FVector Points[3] = { Ground[0], Ground[1], Ground[2] };
	FQuat Rest;
	if (!FShipFlightModel::TripodRest(Location, Rotation.Quaternion(), Pads, Points, RestHeightCm, OutLocation, Rest, OutNormal))
	{
		return false;
	}
	OutRotation = Rest.Rotator();
	return true;
}

ELandingBlocker ASpaceshipPawn::EvaluateLanding(float GroundGap, float Speed, float TiltDeg, float SlopeDeg, bool bEngineInput) const
{
	return FShipFlightModel::EvaluateLanding(GroundGap, Speed, TiltDeg, SlopeDeg, bEngineInput, GetLandingLimits());
}

FVector ASpaceshipPawn::ApplyGroundFriction(const FVector& Velocity, const FVector& SurfaceNormal, const FVector& Up, float GravityCmS2, float DeltaSeconds) const
{
	return FShipFlightModel::ApplyGroundFriction(Velocity, SurfaceNormal, Up, GravityCmS2, DeltaSeconds, GroundFriction);
}

FRotator ASpaceshipPawn::ComputeLandedRotationStep(const FRotator& Current, const FVector& SurfaceNormal, float DeltaSeconds) const
{
	return FShipFlightModel::LandedRotationStep(Current, SurfaceNormal, DeltaSeconds, LandingAlignRate);
}

bool ASpaceshipPawn::SweepHull(const FVector& Start, const FVector& End, const FQuat& Rotation, FHitResult& OutHit) const
{
	FCollisionQueryParams Params(SCENE_QUERY_STAT(SpaceshipGroundProbe), false, this);
	FCollisionResponseParams Responses;
	HullCollision->InitSweepCollisionParams(Params, Responses);
	return GetWorld()->SweepSingleByChannel(OutHit, Start, End, Rotation, HullCollision->GetCollisionObjectType(),
		HullCollision->GetCollisionShape(), Params, Responses);
}

bool ASpaceshipPawn::HasHullShapes() const
{
	const UBodySetup* Body = Hull && Hull->GetStaticMesh() ? Hull->GetStaticMesh()->GetBodySetup() : nullptr;
	return Body && Body->AggGeom.GetElementCount() > 0 && Hull->IsCollisionEnabled();
}

bool ASpaceshipPawn::SweepHullParts(const FVector& Start, const FVector& End, const FQuat& Rotation, FHitResult& OutHit) const
{
	if (!HasHullShapes())
	{
		return SweepHull(Start, End, Rotation, OutHit);
	}
	// The hull component's own collision (the UCX hulls from Blender) at the actor pose Start .. End.
	const FTransform AtStart = Hull->GetRelativeTransform() * FTransform(Rotation, Start);
	const FVector Offset = AtStart.GetLocation() - Start;
	TArray<FHitResult> Hits;
	FComponentQueryParams Params(SCENE_QUERY_STAT(SpaceshipHullParts), this);
	GetWorld()->ComponentSweepMulti(Hits, Hull, Start + Offset, End + Offset, AtStart.GetRotation(), Params);
	const FVector Delta = End - Start;
	bool bHit = false;
	for (const FHitResult& Hit : Hits)
	{
		if (!Hit.bBlockingHit || !BlocksShip(Hit.GetComponent()))
		{
			continue;
		}
		// Already inside and on the way out (taking off from a pose the pads hold, a spawn in the ground): let it go.
		if (Hit.bStartPenetrating && (Delta | Hit.Normal) > 0.0)
		{
			continue;
		}
		if (!bHit || Hit.Time < OutHit.Time)
		{
			OutHit = Hit;
			OutHit.Location = Hit.Location - Offset;
			bHit = true;
		}
	}
	return bHit;
}

bool ASpaceshipPawn::BlocksShip(const UPrimitiveComponent* Other) const
{
	// What the root box blocks, and nothing else: the hull mesh also blocks pawns (characters walk on it), but the
	// pilot sitting inside it, or anyone standing next to it, must not stop the ship or its landing.
	return Other && HullCollision->GetCollisionResponseToChannel(Other->GetCollisionObjectType()) == ECR_Block;
}

bool ASpaceshipPawn::HullClearOfGround(const FVector& Location, const FQuat& Rotation, double GearTopLocalZ, FString* OutWhat) const
{
	// Each of the hull's collision shapes as its box in the ship's frame (GetHullCollisionBoxes), except the gear's:
	// those reaching below GearTopLocalZ are the legs and pads, which stand on the ground by design (the Wayfarer's
	// main gear block is 5.3 m wide at the pads' soles and dipped into any bump between them).
	FCollisionQueryParams Params(SCENE_QUERY_STAT(SpaceshipHullClearance), false, this);
	FCollisionResponseParams Responses;
	HullCollision->InitSweepCollisionParams(Params, Responses);
	const ECollisionChannel Channel = HullCollision->GetCollisionObjectType();
	TArray<FOverlapResult> Overlaps;
	for (const FBox& Part : GetHullCollisionBoxes())
	{
		if (Part.Min.Z < GearTopLocalZ)
		{
			continue;
		}
		Overlaps.Reset();
		GetWorld()->OverlapMultiByChannel(Overlaps, Location + Rotation.RotateVector(Part.GetCenter()), Rotation, Channel,
			FCollisionShape::MakeBox(Part.GetExtent()), Params, Responses);
		for (const FOverlapResult& Overlap : Overlaps)
		{
			if (Overlap.bBlockingHit && BlocksShip(Overlap.GetComponent()))
			{
				if (OutWhat)
				{
					*OutWhat = GetNameSafe(Overlap.GetActor()) + TEXT(".") + GetNameSafe(Overlap.GetComponent());
				}
				return false;
			}
		}
	}
	return true;
}

void ASpaceshipPawn::MoveHull(const FVector& Delta, FHitResult& OutHit)
{
	OutHit = FHitResult();
	const FVector Start = GetActorLocation();
	if (!bSweepMovement || !SweepHullParts(Start, Start + Delta, GetActorQuat(), OutHit))
	{
		SetActorLocation(Start + Delta);
		return;
	}
	// Stop a hair short of the contact, as a component sweep does, so the next sweep does not start inside.
	const double Length = Delta.Size();
	const double Time = Length > UE_KINDA_SMALL_NUMBER ? FMath::Max(0.0, double(OutHit.Time) - 0.1 / Length) : 0.0;
	SetActorLocation(Start + Delta * Time);
}

bool ASpaceshipPawn::FindGearPads(FVector (&OutPadsLocal)[3]) const
{
	int32 Found = 0;
	for (const FName& Wanted : GearSocketNames)
	{
		// As written, else with / without the SOCKET_ prefix that the FBX import drops (as BuildGearLegs).
		const FString Plain = Wanted.ToString();
		const FName Candidates[] = { Wanted, FName(*(TEXT("SOCKET_") + Plain)), FName(*Plain.Replace(TEXT("SOCKET_"), TEXT(""))) };
		const FName* Socket = Algo::FindByPredicate(Candidates, [this](const FName& Name) { return Hull->DoesSocketExist(Name); });
		if (Socket)
		{
			OutPadsLocal[Found++] = Hull->GetSocketTransform(*Socket, RTS_Actor).GetLocation();
			if (Found == 3)
			{
				return true;
			}
		}
	}
	return false;
}

int32 ASpaceshipPawn::TracePads(const FVector& Location, const FQuat& Rotation, const FVector (&PadsLocal)[3], const FVector& Up,
	FVector (&OutGround)[3], float (&OutGap)[3]) const
{
	FCollisionQueryParams Params(SCENE_QUERY_STAT(SpaceshipPadProbe), false, this);
	FCollisionResponseParams Responses;
	HullCollision->InitSweepCollisionParams(Params, Responses);
	const ECollisionChannel Channel = HullCollision->GetCollisionObjectType();
	// From above the pad, so a pad already in the ground still finds it.
	constexpr double Above = 300.0;
	const double Below = FMath::Max(LandingMaxGapCm, GroundContactToleranceCm) + GearExtensionCm + 200.0;
	int32 Hits = 0;
	for (int32 I = 0; I < 3; ++I)
	{
		const FVector Pad = Location + Rotation.RotateVector(PadsLocal[I]);
		FHitResult Hit;
		if (GetWorld()->LineTraceSingleByChannel(Hit, Pad + Up * Above, Pad - Up * Below, Channel, Params, Responses) && !Hit.bStartPenetrating)
		{
			OutGround[I] = Hit.ImpactPoint;
			OutGap[I] = float(Hit.Distance - Above);
			++Hits;
		}
		else
		{
			OutGap[I] = -1.f;
		}
	}
	return Hits;
}

bool ASpaceshipPawn::SolveTripodRest(const FVector (&PadsLocal)[3], const FVector& Up, FVector& OutLocation, FQuat& OutRotation, FVector& OutNormal) const
{
	// The ground straight under the pads moves as the ship tilts onto it; three passes settle it to well under a
	// centimetre on Veyra's 2 m collision cells.
	OutLocation = GetActorLocation();
	OutRotation = GetActorQuat();
	const double RestHeight = 1.0 + GetGearGroundOffsetCm();
	for (int32 Pass = 0; Pass < 3; ++Pass)
	{
		FVector Ground[3];
		float Gap[3];
		if (TracePads(OutLocation, OutRotation, PadsLocal, Up, Ground, Gap) < 3
			|| !FShipFlightModel::TripodRest(OutLocation, OutRotation, PadsLocal, Ground, RestHeight, OutLocation, OutRotation, OutNormal))
		{
			return false;
		}
	}
	return true;
}

void ASpaceshipPawn::UpdateLanding(float DeltaSeconds)
{
	Landing->BeginFrame(DeltaSeconds);
	FShipGroundProbe Probe = Landing->GetGround();
	bHasTripodRest = false;

	// Probe the ground only when it matters: low over a body with a walkable surface.
	const ACelestialBody* Body = NearestBody.Get();
	FVector SurfacePoint;
	if (bHasEnvironment && Body && Environment.AltitudeAboveTerrainCm < LandingProbeAltitudeM * 100.0
		&& Body->GetSurfaceFrame(GetActorLocation(), LandingFootprintRadiusCm, SurfacePoint, Probe.Normal))
	{
		Probe.bValid = true;
		const FVector Up = Environment.Up;
		bool bOnPads = false;
		FVector PadsLocal[3];
		if (Landing->IsGearGoingDown() && FindGearPads(PadsLocal))
		{
			// The gear down: the ground straight under each pad (the gap is the lowest pad's), and the pose standing
			// on all three, which gives the slope and whether the hull would clear the ground there.
			FVector Ground[3];
			float Gap[3];
			if (TracePads(GetActorLocation(), GetActorQuat(), PadsLocal, Up, Ground, Gap) == 3)
			{
				bOnPads = true;
				Probe.GapCm = FMath::Max(FMath::Min3(Gap[0], Gap[1], Gap[2]), 0.f);
				FVector Normal;
				bHasTripodRest = SolveTripodRest(PadsLocal, Up, TripodRestLocation, TripodRestRotation, Normal);
				if (bHasTripodRest)
				{
					Probe.Normal = Normal;
					// Shapes reaching to within 50 cm of the pads' soles are the gear itself.
					const double GearTop = FMath::Min3(PadsLocal[0].Z, PadsLocal[1].Z, PadsLocal[2].Z) - GetGearGroundOffsetCm() + 50.0;
					FString What;
					Probe.bHullClear = HullClearOfGround(TripodRestLocation + Normal * LandingHullClearanceCm, TripodRestRotation, GearTop, &What);
					if (!Probe.bHullClear && What != LastObstruction)
					{
						UE_LOG(LogSpaceship, Log, TEXT("%s: standing on the pads here, the hull would touch %s"), *GetName(), *What);
					}
					LastObstruction = Probe.bHullClear ? FString() : What;
				}
			}
		}
		if (!bOnPads)
		{
			// Straight down with the real hull shapes: the gap is what the collision actually sees,
			// wherever on the hull the first contact would be.
			const FVector Start = GetActorLocation();
			const double ProbeLength = FMath::Max(LandingMaxGapCm, GroundContactToleranceCm) + GearExtensionCm + 200.0;
			FHitResult Hit;
			if (SweepHullParts(Start, Start - Up * ProbeLength, GetActorQuat(), Hit))
			{
				Probe.GapCm = Hit.bStartPenetrating ? 0.f : float(Hit.Distance);
			}
		}
		Probe.SlopeDeg = FShipFlightModel::AngleBetweenDeg(Probe.Normal, Up);
		Probe.TiltDeg = FShipFlightModel::AngleBetweenDeg(GetActorUpVector(), Probe.Normal);
		// Touching means the pads with the gear down, the belly without it.
		Probe.bContact = Probe.GapCm >= 0.f && Probe.GapCm - GetGearGroundOffsetCm() <= GroundContactToleranceCm;
	}

	const bool bEngineInput = FMath::Abs(ThrustInput) >= TakeoffInputThreshold || LiftInput >= TakeoffInputThreshold
		|| Quantum->GetState() == EQuantumState::Traveling;

	switch (Landing->Update(DeltaSeconds, Probe, LinearVelocity.Size(), bEngineInput, GetLandingRules()))
	{
	case UShipLandingComponent::EEvent::TouchedDown:
		EnterLanded();
		break;
	case UShipLandingComponent::EEvent::TookOff:
		ExitLanded();
		break;
	default:
		break;
	}
}

void ASpaceshipPawn::EnterLanded()
{
	Landing->EnterLanded(GetLandingRules());
	AngularVelocity = FVector::ZeroVector;
	MouseStick = FVector2D::ZeroVector;
	Systems->CutBoostAndAfterburner();
	PlayOneShot(TouchdownSound, FMath::Clamp(LinearVelocity.Size() / FMath::Max(LandingMaxSpeed, 1.f), 0.4f, 1.f));
	UE_LOG(LogSpaceship, Log, TEXT("%s landed: slope %.1f deg, tilt %.1f deg, gap %.0f cm"),
		*GetName(), Landing->GetGroundSlopeDeg(), Landing->GetGroundTiltDeg(), Landing->GetGroundGapCm());
}

void ASpaceshipPawn::ExitLanded()
{
	Landing->ExitLanded(GetLandingRules());
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

	const FVector GroundNormal = Landing->GetGroundNormal();
	const double Alpha = 1.0 - FMath::Exp(-LandingAlignRate * DeltaSeconds);
	const FQuat Current = GetActorQuat();
	const FQuat Rotation = FQuat::Slerp(Current, FShipFlightModel::LevelOnSurface(Current, GroundNormal), Alpha).GetNormalized();

	// Leftover sliding along the ground dies out instead of stopping dead.
	LinearVelocity = FVector::VectorPlaneProject(LinearVelocity, GroundNormal) * FMath::Exp(-LandedBrakeRate * DeltaSeconds);
	if (LinearVelocity.SizeSquared() < 1.0)
	{
		LinearVelocity = FVector::ZeroVector;
	}
	const FVector Drift = LinearVelocity * DeltaSeconds;
	FVector Location = GetActorLocation() + Drift;

	if (bHasTripodRest)
	{
		// Standing on the three pads: ease into the pose where each one is on the ground (UpdateLanding solved it
		// this frame), whatever the slope does under each leg. No sweep - the pads hold the ship, not its shapes.
		SetActorLocationAndRotation(FMath::Lerp(Location, TripodRestLocation + Drift, Alpha),
			FQuat::Slerp(Current, TripodRestRotation, Alpha).GetNormalized());
		return;
	}

	// Where the hull, in its new rotation, rests on the collision: sweep it down onto the ground
	// from a metre above, and ease towards that. Keeps the ship sitting on the terrain as it
	// levels out, without sinking in or hovering.
	// With the gear down the hull rests GearExtensionCm up, on the pads.
	const double RestHeight = 1.0 + GetGearGroundOffsetCm();
	FHitResult Hit;
	if (SweepHullParts(Location + GroundNormal * 100.0, Location - GroundNormal * (300.0 + RestHeight), Rotation, Hit) && !Hit.bStartPenetrating)
	{
		Location = FMath::Lerp(Location, Hit.Location + GroundNormal * RestHeight, Alpha);
	}

	SetActorLocationAndRotation(Location, Rotation);
}

// -------------------------------------------------------------------------------------------
// Sound
// -------------------------------------------------------------------------------------------

UAudioComponent* ASpaceshipPawn::PlayOneShot(USoundBase* Sound, float VolumeScale)
{
	const UWorld* World = GetWorld();
	if (!Sound || !World || !World->IsGameWorld() || !IsPlayerControlled())
	{
		return nullptr;
	}
	return UGameplayStatics::SpawnSound2D(this, Sound, OneShotVolume * VolumeScale * USpaceUserSettings::GetEffectsVolume());
}

// -------------------------------------------------------------------------------------------
// Landing gear and precision mode (SC-2a)
// -------------------------------------------------------------------------------------------

bool ASpaceshipPawn::SetGearDown(bool bDown)
{
	return Landing->SetGearDown(bDown);
}

void ASpaceshipPawn::ToggleGear()
{
	SetGearDown(!Landing->IsGearGoingDown());
}

void ASpaceshipPawn::SetPrecisionMode(bool bOn)
{
	Landing->SetPrecisionMode(bOn);
}

void ASpaceshipPawn::SetVtol(bool bOn)
{
	Systems->SetVtol(bOn);
}

void ASpaceshipPawn::UpdateVtol(float DeltaSeconds)
{
	Systems->UpdateVtol(DeltaSeconds, VtolTransitionSeconds);
}

FRotator ASpaceshipPawn::ComputeVtolLevelStep(const FVector& WorldUp, float DeltaSeconds) const
{
	return FShipFlightModel::VtolLevelStep(GetActorQuat(), WorldUp, DeltaSeconds, Systems->GetVtolBlend(), VtolLevelRate);
}

float ASpaceshipPawn::GetGearGroundOffsetCm() const
{
	return GearExtensionCm * Landing->GetGearDeploy();
}

void ASpaceshipPawn::UpdateGear(float DeltaSeconds)
{
	if (Landing->UpdateGear(DeltaSeconds, GearDeploySeconds))
	{
		// Locks down with a small jolt, felt in the camera.
		Presentation->Kick(0.15f);
	}
	PoseGearLegs();
}

FShipFlightModel::FGearShape ASpaceshipPawn::GetGearShape() const
{
	FShipFlightModel::FGearShape Gear;
	Gear.ExtensionCm = GearExtensionCm;
	Gear.FoldDeg = GearFoldDeg;
	Gear.PadThicknessCm = GearPadThicknessCm;
	Gear.StrutRadiusCm = GearStrutRadiusCm;
	Gear.PadRadiusCm = GearPadRadiusCm;
	return Gear;
}

TArray<FVector> ASpaceshipPawn::ComputeGearLegPose(float Deploy, bool bNose) const
{
	return FShipFlightModel::GearLegPose(Deploy, bNose, GetGearShape());
}

float ASpaceshipPawn::ComputeGearStowOffsetCm(float Deploy) const
{
	return FShipFlightModel::GearStowOffsetCm(Deploy, GearStowTravelCm);
}

void ASpaceshipPawn::BuildGearLegs()
{
	if (GearLegs.Num() > 0 || ModelledGear.IsValid() || !Hull->GetStaticMesh())
	{
		return;
	}

	// A modelled gear part (the ship's own legs from Blender) wins over the placeholder legs.
	TArray<UStaticMeshComponent*> Meshes;
	GetComponents<UStaticMeshComponent>(Meshes);
	for (UStaticMeshComponent* Mesh : Meshes)
	{
		if (Mesh != Hull && Mesh->GetStaticMesh() && Mesh->GetName().Contains(TEXT("Gear")))
		{
			ModelledGear = Mesh;
			ModelledGearDownLocation = Mesh->GetRelativeLocation();
			// Seen, never touched: the ship's movement and the pilot use the hull's collision.
			Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			GearPosed = -1.f;
			PoseGearLegs();
			UE_LOG(LogSpaceship, Log, TEXT("%s: modelled gear part %s"), *GetName(), *Mesh->GetName());
			return;
		}
	}
	if (!GearLegMesh)
	{
		return;
	}

	// The hull's own materials, found by slot name, so the legs match the paint of the ship.
	auto HullMaterial = [this](const TCHAR* SlotPart) -> UMaterialInterface*
	{
		const TArray<FName> Slots = Hull->GetMaterialSlotNames();
		for (int32 Index = 0; Index < Slots.Num(); ++Index)
		{
			if (Slots[Index].ToString().Contains(SlotPart))
			{
				return Hull->GetMaterial(Index);
			}
		}
		return nullptr;
	};
	UMaterialInterface* const SleeveMaterial = HullMaterial(TEXT("HullDark"));
	UMaterialInterface* const PistonMaterial = HullMaterial(TEXT("BareMetal"));
	UMaterialInterface* const PadMaterial = HullMaterial(TEXT("Rubber"));

	for (const FName& Wanted : GearSocketNames)
	{
		// As written, else with / without the SOCKET_ prefix that the FBX import drops.
		const FString Plain = Wanted.ToString();
		const FName Candidates[] = { Wanted, FName(*(TEXT("SOCKET_") + Plain)), FName(*Plain.Replace(TEXT("SOCKET_"), TEXT(""))) };
		const FName* Found = Algo::FindByPredicate(Candidates, [this](const FName& Name) { return Hull->DoesSocketExist(Name); });
		if (!Found)
		{
			continue;
		}
		const FName Socket = *Found;
		FGearLeg Leg;
		Leg.bNose = Socket.ToString().Contains(TEXT("Nose"));

		USceneComponent* Pivot = NewObject<USceneComponent>(this, FName(*FString::Printf(TEXT("GearPivot_%s"), *Socket.ToString())));
		Pivot->SetupAttachment(Hull, Socket);
		// Sized in centimetres whatever the hull's scale.
		Pivot->SetUsingAbsoluteScale(true);
		Pivot->RegisterComponent();
		Leg.Pivot = Pivot;

		auto MakePart = [this, Pivot, &Socket](const TCHAR* Part, UMaterialInterface* Material)
		{
			UStaticMeshComponent* Mesh = NewObject<UStaticMeshComponent>(this, FName(*FString::Printf(TEXT("Gear%s_%s"), Part, *Socket.ToString())));
			Mesh->SetStaticMesh(GearLegMesh);
			Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Mesh->SetCanEverAffectNavigation(false);
			Mesh->SetupAttachment(Pivot);
			if (Material)
			{
				Mesh->SetMaterial(0, Material);
			}
			Mesh->RegisterComponent();
			return Mesh;
		};
		Leg.Sleeve = MakePart(TEXT("Sleeve"), SleeveMaterial);
		Leg.Piston = MakePart(TEXT("Piston"), PistonMaterial);
		Leg.Pad = MakePart(TEXT("Pad"), PadMaterial);
		GearLegs.Add(Leg);
	}
	GearPosed = -1.f;
	PoseGearLegs();
	UE_LOG(LogSpaceship, Log, TEXT("%s: %d gear leg(s) on the hull sockets"), *GetName(), GearLegs.Num());
}

void ASpaceshipPawn::PoseGearLegs()
{
	const float GearDeploy = Landing->GetGearDeploy();
	if ((GearLegs.Num() == 0 && !ModelledGear.IsValid()) || GearPosed == GearDeploy)
	{
		return;
	}
	GearPosed = GearDeploy;
	if (UStaticMeshComponent* Gear = ModelledGear.Get())
	{
		// Straight up into the belly, hidden once all the way in (for a ship without bay doors that open).
		Gear->SetRelativeLocation(ModelledGearDownLocation + FVector::UpVector * ComputeGearStowOffsetCm(GearDeploy));
		Gear->SetVisibility(GearDeploy > 0.001f);
		return;
	}
	// Stowed legs are hidden: a ship without gear bays has nowhere to fold them into.
	const bool bVisible = GearDeploy > 0.001f;
	for (const FGearLeg& Leg : GearLegs)
	{
		USceneComponent* Pivot = Leg.Pivot.Get();
		if (!Pivot)
		{
			continue;
		}
		const TArray<FVector> Pose = ComputeGearLegPose(GearDeploy, Leg.bNose);
		Pivot->SetRelativeRotation(FRotator(Pose[0].X, Pose[0].Y, Pose[0].Z));
		Pivot->SetVisibility(bVisible, true);
		const TPair<UStaticMeshComponent*, int32> Parts[] = { { Leg.Sleeve.Get(), 1 }, { Leg.Piston.Get(), 3 }, { Leg.Pad.Get(), 5 } };
		for (const TPair<UStaticMeshComponent*, int32>& Part : Parts)
		{
			if (Part.Key)
			{
				Part.Key->SetRelativeLocation(Pose[Part.Value]);
				Part.Key->SetRelativeScale3D(Pose[Part.Value + 1]);
			}
		}
	}
}

void ASpaceshipPawn::ApplyGearSupport(float DeltaSeconds)
{
	const float Offset = GetGearGroundOffsetCm();
	if (!Landing->HasGroundInfo() || Landing->GetGroundGapCm() < 0.f || Offset <= 1.f || DeltaSeconds <= 0.f)
	{
		return;
	}
	const FVector Up = bHasEnvironment ? FVector(Environment.Up) : GetActorUpVector();
	// Room between the pads and the ground; negative: the pads are in it.
	const double Room = double(Landing->GetGroundGapCm()) - Offset;
	const double Vertical = LinearVelocity | Up;
	if (Room < 0.0)
	{
		// The gear came down under a ship resting on its belly: the legs push it up, about as fast as
		// they extend, instead of sinking into the ground.
		const double Lift = FMath::Min(-Room, 1.5 * GearExtensionCm / FMath::Max(GearDeploySeconds, 0.05f) * DeltaSeconds);
		FHitResult LiftHit;
		MoveHull(Up * Lift, LiftHit);
		Landing->AddGroundGap(float(Lift));
		if (Vertical < 0.0)
		{
			LinearVelocity -= Up * Vertical;
		}
		return;
	}
	// Coming down onto the pads: stop where they touch. The hull box alone would let the legs sink in.
	if (Vertical < 0.0 && -Vertical * DeltaSeconds > Room)
	{
		LinearVelocity -= Up * (Vertical + Room / DeltaSeconds);
	}
}


// -------------------------------------------------------------------------------------------
// Placeholder cockpit
// -------------------------------------------------------------------------------------------

namespace SpaceshipCockpitLayout
{
	/** One box of the placeholder cockpit, relative to the pilot's eye (cm, X forward, Y right, Z up). */
	struct FPart
	{
		const TCHAR* Name;
		FVector Centre;
		FVector Size;
		FRotator Rotation;
		FLinearColor Colour;
	};

	/** A box of Thickness from A to B (a pillar or strut). */
	FPart Strut(const TCHAR* Name, const FVector& A, const FVector& B, float Thickness, const FLinearColor& Colour)
	{
		const FVector Axis = B - A;
		return { Name, (A + B) * 0.5, FVector(Thickness, Thickness, Axis.Size()), FRotationMatrix::MakeFromZ(Axis.GetSafeNormal()).Rotator(), Colour };
	}

	/** A box lying on the instrument panel: Along across the panel's slope from its centre, Right sideways. */
	FPart OnPanel(const TCHAR* Name, const FVector& PanelCentre, float SlopeDeg, float Along, float Right, const FVector& Size, const FLinearColor& Colour)
	{
		const FRotator Rotation(SlopeDeg, 0.0, 0.0);
		const FVector Offset = Rotation.RotateVector(FVector(Along, Right, 2.5));
		return { Name, PanelCentre + Offset, Size, Rotation, Colour };
	}

	/**
	 * Laid out against the view at the cockpit's 88 degree field of view (28.5 degrees above and below
	 * the horizon on 16:9), after the Star Citizen references in Docs/UI:
	 * - the instrument panel slopes up away from the pilot; its far edge, with the glare-shield lip, is
	 *   the top of the dashboard at ~17 degrees below the horizon (~78 % of the screen's height, under
	 *   the HUD, which ends at ~75 %), and the panel with its screens fills the band below it;
	 * - the canopy pillars stand ~85 cm ahead at ~29 degrees left and right (~21 % and ~79 % of the
	 *   width), leaning outwards towards the top, framing the HUD;
	 * - the seat is behind the eye and shows only with free look.
	 * The first layout had a flat-topped box whose far edge rose to ~67 % and covered the speed readout,
	 * and pillars 40-60 cm from the eye that filled the screen's sides.
	 */
	TArray<FPart> Parts()
	{
		const FLinearColor Frame(0.030f, 0.033f, 0.038f);
		const FLinearColor Lip(0.060f, 0.066f, 0.075f);
		const FLinearColor Screen(0.012f, 0.050f, 0.080f);
		const FLinearColor Seat(0.045f, 0.045f, 0.050f);
		const FVector PanelCentre(68.5, 0.0, -33.0);
		const float Slope = 17.f;
		return {
			{ TEXT("InstrumentPanel"), PanelCentre, FVector(35.0, 150.0, 4.0), FRotator(Slope, 0.0, 0.0), Frame },
			{ TEXT("DashboardBody"), FVector(72.0, 0.0, -54.0), FVector(36.0, 150.0, 36.0), FRotator::ZeroRotator, Frame },
			{ TEXT("GlareShield"), FVector(86.0, 0.0, -27.5), FVector(6.0, 150.0, 3.0), FRotator::ZeroRotator, Lip },
			OnPanel(TEXT("ScreenLeft"), PanelCentre, Slope, 3.0f, -30.0f, FVector(16.0, 28.0, 1.0), Screen),
			OnPanel(TEXT("ScreenCentre"), PanelCentre, Slope, 3.0f, 0.0f, FVector(14.0, 18.0, 1.0), Screen),
			OnPanel(TEXT("ScreenRight"), PanelCentre, Slope, 3.0f, 30.0f, FVector(16.0, 28.0, 1.0), Screen),
			Strut(TEXT("PillarLeft"), FVector(85.0, -48.0, -27.0), FVector(55.0, -66.0, 50.0), 5.0f, Frame),
			Strut(TEXT("PillarRight"), FVector(85.0, 48.0, -27.0), FVector(55.0, 66.0, 50.0), 5.0f, Frame),
			{ TEXT("SeatBack"), FVector(-38.0, 0.0, -38.0), FVector(10.0, 52.0, 70.0), FRotator(-8.0, 0.0, 0.0), Seat },
			{ TEXT("Headrest"), FVector(-35.0, 0.0, 8.0), FVector(10.0, 30.0, 22.0), FRotator(-8.0, 0.0, 0.0), Seat },
			{ TEXT("SeatCushion"), FVector(-8.0, 0.0, -76.0), FVector(52.0, 52.0, 10.0), FRotator::ZeroRotator, Seat },
		};
	}
}

TArray<FVector> ASpaceshipPawn::GetPlaceholderCockpitCorners() const
{
	TArray<FVector> Corners;
	for (const SpaceshipCockpitLayout::FPart& Part : SpaceshipCockpitLayout::Parts())
	{
		const FTransform Transform(Part.Rotation, Part.Centre);
		for (int32 Index = 0; Index < 8; ++Index)
		{
			const FVector Local((Index & 1 ? 0.5 : -0.5) * Part.Size.X, (Index & 2 ? 0.5 : -0.5) * Part.Size.Y, (Index & 4 ? 0.5 : -0.5) * Part.Size.Z);
			Corners.Add(Transform.TransformPosition(Local));
		}
	}
	return Corners;
}

TArray<FString> ASpaceshipPawn::GetPlaceholderCockpitPartNames() const
{
	TArray<FString> Names;
	for (const SpaceshipCockpitLayout::FPart& Part : SpaceshipCockpitLayout::Parts())
	{
		Names.Add(Part.Name);
	}
	return Names;
}

void ASpaceshipPawn::BuildPlaceholderCockpit()
{
	if (!bPlaceholderCockpit || CockpitFrameRoot || !CockpitPartMesh)
	{
		return;
	}
	CockpitFrameRoot = NewObject<USceneComponent>(this, TEXT("PlaceholderCockpit"));
	// On the root, not on the camera: free look turns the head, the cockpit stays put.
	CockpitFrameRoot->SetupAttachment(HullCollision);
	CockpitFrameRoot->SetRelativeLocation(CockpitCameraBaseLocation);
	CockpitFrameRoot->RegisterComponent();
	for (const SpaceshipCockpitLayout::FPart& Part : SpaceshipCockpitLayout::Parts())
	{
		UStaticMeshComponent* Mesh = NewObject<UStaticMeshComponent>(this, FName(*FString::Printf(TEXT("Cockpit%s"), Part.Name)));
		Mesh->SetStaticMesh(CockpitPartMesh);
		Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Mesh->SetCanEverAffectNavigation(false);
		// Pilot's view only, and no shadows on the hull seen from the chase camera.
		Mesh->SetCastShadow(false);
		Mesh->SetOnlyOwnerSee(true);
		Mesh->SetupAttachment(CockpitFrameRoot);
		Mesh->SetRelativeLocationAndRotation(Part.Centre, Part.Rotation);
		Mesh->SetRelativeScale3D(Part.Size / 100.0);
		if (CockpitPartMaterial)
		{
			UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(CockpitPartMaterial, this);
			Material->SetVectorParameterValue(TEXT("Color"), Part.Colour);
			Mesh->SetMaterial(0, Material);
		}
		Mesh->RegisterComponent();
		CockpitParts.Add(Mesh);
	}
	CockpitFrameRoot->SetVisibility(bCockpitView, true);
	UE_LOG(LogSpaceship, Log, TEXT("%s: placeholder cockpit, %d parts"), *GetName(), CockpitParts.Num());
}
