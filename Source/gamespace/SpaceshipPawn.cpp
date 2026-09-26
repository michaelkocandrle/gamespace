// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceshipPawn.h"

#include "Camera/CameraComponent.h"
#include "Components/AudioComponent.h"
#include "Components/PointLightComponent.h"
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
#include "Materials/MaterialParameterCollection.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Camera/PlayerCameraManager.h"
#include "PhysicsEngine/BodySetup.h"
#include "Sound/SoundBase.h"
#include "CelestialBody.h"
#include "DistantBody.h"
#include "SpaceDustComponent.h"
#include "SpaceSpeedTunnelComponent.h"
#include "SpaceHullSparksComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/SkyLight.h"
#include "SpaceUserSettings.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "EngineUtils.h"

namespace
{
	/** space.DashboardFocus 1 / 0: holds the dashboard focus of every ship (shots, testing). */
	FAutoConsoleCommandWithWorldAndArgs DashboardFocusCommand(
		TEXT("space.DashboardFocus"),
		TEXT("space.DashboardFocus 1|0: lean in to the dashboard's displays (Z or the middle mouse button in the game)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			const bool bOn = Args.Num() == 0 || FCString::Atoi(*Args[0]) != 0;
			for (TActorIterator<ASpaceshipPawn> It(World); It; ++It)
			{
				It->SetDashboardFocus(bOn);
			}
		}));

	/** Material parameters of every ship here, live: space.ShipMat <Parameter> <Value>. */
	FAutoConsoleCommandWithWorldAndArgs ShipMaterialCommand(
		TEXT("space.ShipMat"),
		TEXT("space.ShipMat <Parameter> <Value>: set a scalar on every material of the ship (DetailNormalStrength, DetailTileCm, RoughnessScale...). Not saved."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (Args.Num() < 2)
			{
				UE_LOG(LogTemp, Display, TEXT("space.ShipMat <Parameter> <Value>"));
				return;
			}
			int32 Changed = 0;
			for (TActorIterator<ASpaceshipPawn> It(World); It; ++It)
			{
				Changed += It->DebugSetMaterialScalar(FName(*Args[0]), FCString::Atof(*Args[1]));
			}
			UE_LOG(LogTemp, Display, TEXT("space.ShipMat %s = %s on %d materials"), *Args[0], *Args[1], Changed);
		}));

	/** The same for a colour: space.ShipMatColor <Parameter> <R> <G> <B>. */
	FAutoConsoleCommandWithWorldAndArgs ShipMaterialColorCommand(
		TEXT("space.ShipMatColor"),
		TEXT("space.ShipMatColor <Parameter> <R> <G> <B>: set a colour on every material of the ship (BaseColorTint...). Not saved."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (Args.Num() < 4)
			{
				UE_LOG(LogTemp, Display, TEXT("space.ShipMatColor <Parameter> <R> <G> <B>"));
				return;
			}
			const FLinearColor Colour(FCString::Atof(*Args[1]), FCString::Atof(*Args[2]), FCString::Atof(*Args[3]), 1.f);
			int32 Changed = 0;
			for (TActorIterator<ASpaceshipPawn> It(World); It; ++It)
			{
				Changed += It->DebugSetMaterialColor(FName(*Args[0]), Colour);
			}
			UE_LOG(LogTemp, Display, TEXT("space.ShipMatColor %s on %d materials"), *Args[0], Changed);
		}));

	/**
	 * space.Drift <forward> <right> <up>: sets the ship's velocity in its own axes, m/s. For shots of
	 * the HUD in states the shot runner cannot fly into - sliding sideways, going backwards - where
	 * the flight path marker is the whole point. The flight computer takes over again immediately in
	 * coupled flight, so pair it with decoupled.
	 */
	FAutoConsoleCommandWithWorldAndArgs DriftCommand(
		TEXT("space.Drift"),
		TEXT("space.Drift <forward> <right> <up>: set the ship's velocity in its own axes, m/s."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			const FVector Local(Args.Num() > 0 ? FCString::Atof(*Args[0]) * 100.f : 0.f,
				Args.Num() > 1 ? FCString::Atof(*Args[1]) * 100.f : 0.f,
				Args.Num() > 2 ? FCString::Atof(*Args[2]) * 100.f : 0.f);
			for (TActorIterator<ASpaceshipPawn> It(World); It; ++It)
			{
				It->DebugSetLinearVelocity(It->GetActorQuat().RotateVector(Local));
			}
			UE_LOG(LogTemp, Display, TEXT("space.Drift %.0f %.0f %.0f m/s (ship axes)"),
				Local.X / 100.f, Local.Y / 100.f, Local.Z / 100.f);
		}));

	/** space.Quantum <name> [progress]: jump at once (shots, testing a destination without flying to it). */
	FAutoConsoleCommandWithWorldAndArgs QuantumCommand(
		TEXT("space.Quantum"),
		TEXT("space.Quantum <destination name> [0..1 of the way]: quantum jump at once, no spool. space.Quantum ready: spool and calibration full."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			for (TActorIterator<ASpaceshipPawn> It(World); It; ++It)
			{
				if (Args.Num() > 0 && Args[0].Equals(TEXT("ready"), ESearchCase::IgnoreCase))
				{
					It->DebugFinishQuantumCharge();
				}
				else
				{
					It->DebugEngageQuantum(Args.Num() > 0 ? Args[0] : FString(), Args.Num() > 1 ? FCString::Atof(*Args[1]) : 0.f);
				}
			}
		}));

	/** space.Vtol 1 / 0: VTOL on every ship here, for shots that should not depend on a key. */
	FAutoConsoleCommandWithWorldAndArgs VtolCommand(
		TEXT("space.Vtol"),
		TEXT("space.Vtol 1|0: VTOL (G in the game). SCM only."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			const bool bOn = Args.Num() == 0 || FCString::Atoi(*Args[0]) != 0;
			for (TActorIterator<ASpaceshipPawn> It(World); It; ++It)
			{
				It->SetVtol(bOn);
			}
		}));

	/** space.CockpitPitch <deg>: the cockpit view's rest pitch (comparison shots of the framing). */
	FAutoConsoleCommandWithWorldAndArgs CockpitPitchCommand(
		TEXT("space.CockpitPitch"),
		TEXT("space.CockpitPitch <degrees>: tilt the cockpit view at rest (negative looks down)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			for (TActorIterator<ASpaceshipPawn> It(World); It; ++It)
			{
				It->SetCockpitViewPitch(Args.Num() > 0 ? FCString::Atof(*Args[0]) : 0.f);
			}
		}));
}

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
	const TCHAR* const QuantumEngageActionPath = TEXT("/Game/Input/IA_QuantumEngage.IA_QuantumEngage");
	const TCHAR* const AllStopActionPath = TEXT("/Game/Input/IA_AllStop.IA_AllStop");
	const TCHAR* const CameraZoomActionPath = TEXT("/Game/Input/IA_CameraZoom.IA_CameraZoom");
	const TCHAR* const MasterModeActionPath = TEXT("/Game/Input/IA_MasterMode.IA_MasterMode");
	const TCHAR* const SpeedLimiterActionPath = TEXT("/Game/Input/IA_SpeedLimiter.IA_SpeedLimiter");
	const TCHAR* const GSafeActionPath = TEXT("/Game/Input/IA_GSafe.IA_GSafe");
	const TCHAR* const ComStabActionPath = TEXT("/Game/Input/IA_ComStab.IA_ComStab");
	const TCHAR* const AfterburnerActionPath = TEXT("/Game/Input/IA_Afterburner.IA_Afterburner");
	const TCHAR* const LandingGearActionPath = TEXT("/Game/Input/IA_LandingGear.IA_LandingGear");
	const TCHAR* const PrecisionActionPath = TEXT("/Game/Input/IA_Precision.IA_Precision");
	const TCHAR* const VtolActionPath = TEXT("/Game/Input/IA_Vtol.IA_Vtol");
	const TCHAR* const MfdLeftActionPath = TEXT("/Game/Input/IA_MfdLeft.IA_MfdLeft");
	const TCHAR* const DashboardFocusActionPath = TEXT("/Game/Input/IA_DashboardFocus.IA_DashboardFocus");
	const TCHAR* const MfdRightActionPath = TEXT("/Game/Input/IA_MfdRight.IA_MfdRight");

	/** 1 G in cm/s^2. */
	constexpr double StandardGravityCmS2 = 980.665;
	const TCHAR* const EngineLoopSoundPath = TEXT("/Game/Ships/Audio/SW_EngineLoop.SW_EngineLoop");
	const TCHAR* const EngineHumSoundPath = TEXT("/Game/Ships/Audio/SW_EngineHum.SW_EngineHum");
	const TCHAR* const BoostLoopSoundPath = TEXT("/Game/Ships/Audio/SW_BoostLoop.SW_BoostLoop");
	const TCHAR* const CruiseLoopSoundPath = TEXT("/Game/Ships/Audio/SW_CruiseLoop.SW_CruiseLoop");
	const TCHAR* const BoostStartSoundPath = TEXT("/Game/Ships/Audio/SW_BoostStart.SW_BoostStart");
	const TCHAR* const CruiseChargeSoundPath = TEXT("/Game/Ships/Audio/SW_CruiseCharge.SW_CruiseCharge");
	const TCHAR* const CruiseEngageSoundPath = TEXT("/Game/Ships/Audio/SW_CruiseEngage.SW_CruiseEngage");
	const TCHAR* const CruiseDropSoundPath = TEXT("/Game/Ships/Audio/SW_CruiseDrop.SW_CruiseDrop");
	const TCHAR* const TouchdownSoundPath = TEXT("/Game/Ships/Audio/SW_Touchdown.SW_Touchdown");

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
	// Cameras too: a pilot who just got out stands inside this box (it spans the wings), and the
	// character's camera boom, starting inside it, was pulled right in to the head until the
	// pilot walked out of it. The hull mesh's own collision still blocks cameras.
	HullCollision->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
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

	SpaceDust = CreateDefaultSubobject<USpaceDustComponent>(TEXT("SpaceDust"));
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

	// Cooked with the glass material that reads it (ship_materials.py builds both).
	ViewCollection = LoadObject<UMaterialParameterCollection>(nullptr, TEXT("/Game/Ships/Shared/Materials/MPC_ShipView.MPC_ShipView"));

	ChaseCameraBaseLocation = ChaseCamera->GetRelativeLocation();
	CockpitCameraBaseLocation = CockpitCamera->GetRelativeLocation();
	HullSparks->SetHull(Hull);
	// The nose glow sits just ahead of and below the hull's front, whatever the ship.
	if (Hull->GetStaticMesh())
	{
		const FBox Box = Hull->GetStaticMesh()->GetBoundingBox();
		QuantumGlow->SetRelativeLocation(FVector(Box.Max.X + 150.0, 0.0, Box.GetCenter().Z - Box.GetExtent().Z * 0.3));
	}
	for (TActorIterator<ADirectionalLight> It(GetWorld()); It; ++It)
	{
		if (UDirectionalLightComponent* Light = Cast<UDirectionalLightComponent>(It->GetLightComponent()))
		{
			QuantumSun = Light;
			break;
		}
	}
	for (TActorIterator<ASkyLight> It(GetWorld()); It; ++It)
	{
		QuantumSky = It->GetLightComponent();
		break;
	}
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
}

void ASpaceshipPawn::SnapCameraToShip()
{
	// The spring arm stores its lagged location every update; one update without lag stores the
	// real one. Two ticks, because the arm may update before or after this pawn in a frame.
	CameraBoom->bEnableCameraLag = false;
	CameraSnapTicks = 2;
}

void ASpaceshipPawn::UpdateViewCollection()
{
	if (!ViewCollection)
	{
		return;
	}
	if (!bInteriorBoundsReady)
	{
		bInteriorBoundsReady = true;
		TArray<UStaticMeshComponent*> Meshes;
		GetComponents<UStaticMeshComponent>(Meshes);
		for (const UStaticMeshComponent* Mesh : Meshes)
		{
			if (Mesh->GetStaticMesh() && Mesh->GetName().StartsWith(TEXT("Interior")))
			{
				const FTransform ToActor = Mesh->GetComponentTransform().GetRelativeTransform(GetActorTransform());
				InteriorBoundsLocal += Mesh->GetStaticMesh()->GetBoundingBox().TransformBy(ToActor);
			}
		}
	}
	const APlayerCameraManager* Camera = UGameplayStatics::GetPlayerCameraManager(this, 0);
	if (!Camera)
	{
		return;
	}
	bool bInside;
	if (InteriorBoundsLocal.IsValid)
	{
		bInside = InteriorBoundsLocal.IsInside(GetActorTransform().InverseTransformPosition(Camera->GetCameraLocation()));
	}
	else
	{
		bInside = bCockpitView && Camera->GetViewTarget() == this;
	}
	// One collection for the whole world: the ship the camera is in wins the frame, the others only clear
	// it when no ship has claimed it yet this frame.
	static uint64 ClaimedFrame = 0;
	if (bInside)
	{
		ClaimedFrame = GFrameCounter;
	}
	else if (ClaimedFrame == GFrameCounter)
	{
		InsideView = 0.f;
		return;
	}
	InsideView = bInside ? 1.f : 0.f;
	UKismetMaterialLibrary::SetScalarParameterValue(this, ViewCollection, TEXT("InsideView"), InsideView);
	// Seen from inside, the canopy fills the whole view: Lumen's sharp front-layer reflections on it cost ~1.9 ms
	// on the target GPU (RTX 2060, 1080p). Inside the cheap radiance-cache reflection is enough (the "weak"
	// reflection); outside the glass covers a small part of the screen and gets the sharp one.
	static int32 LastFrontLayer = -1;
	const int32 FrontLayer = bInside ? 0 : 1;
	if (FrontLayer != LastFrontLayer)
	{
		LastFrontLayer = FrontLayer;
		if (IConsoleVariable* Var = IConsoleManager::Get().FindConsoleVariable(TEXT("r.Lumen.TranslucencyReflections.FrontLayer.Enable")))
		{
			Var->Set(FrontLayer, ECVF_SetByCode);
		}
	}
}

void ASpaceshipPawn::DebugConfigureCockpit(const FVector& EyeLocation, bool bHideHull, bool bHideCanopy)
{
	if (!EyeLocation.IsNearlyZero())
	{
		CockpitCamera->SetRelativeLocation(EyeLocation);
		// UpdateCameraEffects puts the camera back on its base location (plus shake) every frame, so
		// the base has to move too or the new eye lasts exactly one frame.
		CockpitCameraBaseLocation = EyeLocation;
	}
	bHideHullInCockpit = bHideHull;
	bHideCanopyInCockpit = bHideCanopy;
	if (CockpitFrameRoot)
	{
		// The placeholder cockpit is built around the eye; it moves with it.
		CockpitFrameRoot->SetRelativeLocation(CockpitCameraBaseLocation);
	}
	// So do the cockpit lights, or a shot from another eye would be lit differently.
	PlaceCockpitLights();
	SetCockpitView(bCockpitView);
}

void ASpaceshipPawn::DebugSetCockpitLighting(float KeyCd, float FillCd, float DisplayCd, float InteriorTint)
{
	if (KeyCd >= 0.f)
	{
		CockpitLightIntensityCd = KeyCd;
	}
	if (FillCd >= 0.f)
	{
		CockpitFillIntensityCd = FillCd;
	}
	PlaceCockpitLights();
	if (DisplayCd >= 0.f && CockpitDisplays)
	{
		CockpitDisplays->SetDisplayLightIntensity(DisplayCd);
	}
	if (InteriorTint >= 0.f)
	{
		TArray<UStaticMeshComponent*> Meshes;
		GetComponents(Meshes);
		for (UStaticMeshComponent* Mesh : Meshes)
		{
			if (Mesh->GetName() == TEXT("Interior") && Mesh->GetNumMaterials() > 0)
			{
				UMaterialInstanceDynamic* Dynamic = Mesh->CreateDynamicMaterialInstance(0);
				// The imported instance's own tint times the multiplier, so 1 is the ship as imported.
				FLinearColor Tint = FLinearColor::White;
				if (Dynamic->Parent)
				{
					Dynamic->Parent->GetVectorParameterValue(TEXT("BaseColorTint"), Tint);
				}
				Tint = Tint * InteriorTint;
				Tint.A = 1.f;
				Dynamic->SetVectorParameterValue(TEXT("BaseColorTint"), Tint);
			}
		}
	}
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

	// H (HUD) and Escape (menu) are bound by ASpacePlayerController, the same in the ship and on foot.

	if (FlightAssistAction)
	{
		Input->BindAction(FlightAssistAction, ETriggerEvent::Started, this, &ASpaceshipPawn::HandleFlightAssist);
	}
	if (QuantumEngageAction)
	{
		Input->BindAction(QuantumEngageAction, ETriggerEvent::Started, this, &ASpaceshipPawn::HandleQuantumEngageStarted);
		Input->BindAction(QuantumEngageAction, ETriggerEvent::Completed, this, &ASpaceshipPawn::HandleQuantumEngageCompleted);
		Input->BindAction(QuantumEngageAction, ETriggerEvent::Canceled, this, &ASpaceshipPawn::HandleQuantumEngageCompleted);
	}
	if (AllStopAction)
	{
		Input->BindAction(AllStopAction, ETriggerEvent::Started, this, &ASpaceshipPawn::HandleAllStop);
		Input->BindAction(AllStopAction, ETriggerEvent::Completed, this, &ASpaceshipPawn::HandleAllStopCompleted);
		Input->BindAction(AllStopAction, ETriggerEvent::Canceled, this, &ASpaceshipPawn::HandleAllStopCompleted);
	}
	if (CameraZoomAction)
	{
		Input->BindAction(CameraZoomAction, ETriggerEvent::Triggered, this, &ASpaceshipPawn::HandleCameraZoom);
	}
	if (MasterModeAction)
	{
		Input->BindAction(MasterModeAction, ETriggerEvent::Started, this, &ASpaceshipPawn::HandleMasterMode);
	}
	if (SpeedLimiterAction)
	{
		Input->BindAction(SpeedLimiterAction, ETriggerEvent::Triggered, this, &ASpaceshipPawn::HandleSpeedLimiter);
	}
	if (GSafeAction)
	{
		Input->BindAction(GSafeAction, ETriggerEvent::Started, this, &ASpaceshipPawn::HandleGSafe);
	}
	if (ComStabAction)
	{
		Input->BindAction(ComStabAction, ETriggerEvent::Started, this, &ASpaceshipPawn::HandleComStab);
	}
	if (AfterburnerAction)
	{
		Input->BindAction(AfterburnerAction, ETriggerEvent::Triggered, this, &ASpaceshipPawn::HandleAfterburner);
		Input->BindAction(AfterburnerAction, ETriggerEvent::Completed, this, &ASpaceshipPawn::HandleAfterburnerCompleted);
		Input->BindAction(AfterburnerAction, ETriggerEvent::Canceled, this, &ASpaceshipPawn::HandleAfterburnerCompleted);
	}

	if (LandingGearAction)
	{
		Input->BindAction(LandingGearAction, ETriggerEvent::Started, this, &ASpaceshipPawn::HandleLandingGear);
	}
	if (PrecisionAction)
	{
		Input->BindAction(PrecisionAction, ETriggerEvent::Started, this, &ASpaceshipPawn::HandlePrecision);
	}
	if (VtolAction)
	{
		Input->BindAction(VtolAction, ETriggerEvent::Started, this, &ASpaceshipPawn::HandleVtol);
	}
	if (DashboardFocusAction)
	{
		Input->BindAction(DashboardFocusAction, ETriggerEvent::Started, this, &ASpaceshipPawn::HandleDashboardFocusStarted);
		Input->BindAction(DashboardFocusAction, ETriggerEvent::Completed, this, &ASpaceshipPawn::HandleDashboardFocusCompleted);
		Input->BindAction(DashboardFocusAction, ETriggerEvent::Canceled, this, &ASpaceshipPawn::HandleDashboardFocusCompleted);
	}
	if (MfdLeftAction)
	{
		Input->BindAction(MfdLeftAction, ETriggerEvent::Started, this, &ASpaceshipPawn::HandleMfdLeft);
	}
	if (MfdRightAction)
	{
		Input->BindAction(MfdRightAction, ETriggerEvent::Started, this, &ASpaceshipPawn::HandleMfdRight);
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
			if (FlightAssistAction && !IsMapped(FlightAssistAction))
			{
				InteractMappingContext->MapKey(FlightAssistAction, EKeys::V);
			}
			if (QuantumEngageAction && !IsMapped(QuantumEngageAction))
			{
				InteractMappingContext->MapKey(QuantumEngageAction, EKeys::LeftMouseButton);
			}
			if (AllStopAction && !IsMapped(AllStopAction))
			{
				InteractMappingContext->MapKey(AllStopAction, EKeys::X);
			}
			if (CameraZoomAction && !IsMapped(CameraZoomAction))
			{
				InteractMappingContext->MapKey(CameraZoomAction, EKeys::MouseWheelAxis);
			}
			if (MasterModeAction && !IsMapped(MasterModeAction))
			{
				InteractMappingContext->MapKey(MasterModeAction, EKeys::B);
			}
			if (SpeedLimiterAction && !IsMapped(SpeedLimiterAction))
			{
				InteractMappingContext->MapKey(SpeedLimiterAction, EKeys::MouseWheelAxis);
			}
			if (GSafeAction && !IsMapped(GSafeAction))
			{
				InteractMappingContext->MapKey(GSafeAction, EKeys::K);
			}
			if (ComStabAction && !IsMapped(ComStabAction))
			{
				InteractMappingContext->MapKey(ComStabAction, EKeys::L);
			}
			if (AfterburnerAction && !IsMapped(AfterburnerAction))
			{
				InteractMappingContext->MapKey(AfterburnerAction, EKeys::Tab);
			}
			if (LandingGearAction && !IsMapped(LandingGearAction))
			{
				InteractMappingContext->MapKey(LandingGearAction, EKeys::N);
			}
			if (PrecisionAction && !IsMapped(PrecisionAction))
			{
				InteractMappingContext->MapKey(PrecisionAction, EKeys::P);
			}
			if (VtolAction && !IsMapped(VtolAction))
			{
				InteractMappingContext->MapKey(VtolAction, EKeys::G);
			}
			if (DashboardFocusAction && !IsMapped(DashboardFocusAction))
			{
				InteractMappingContext->MapKey(DashboardFocusAction, EKeys::Z);
				InteractMappingContext->MapKey(DashboardFocusAction, EKeys::MiddleMouseButton);
			}
			if (MfdLeftAction && !IsMapped(MfdLeftAction))
			{
				InteractMappingContext->MapKey(MfdLeftAction, EKeys::F1);
			}
			if (MfdRightAction && !IsMapped(MfdRightAction))
			{
				InteractMappingContext->MapKey(MfdRightAction, EKeys::F2);
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
	LoadOrMake(QuantumEngageAction, QuantumEngageActionPath, TEXT("IA_QuantumEngage_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(AllStopAction, AllStopActionPath, TEXT("IA_AllStop_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(CameraZoomAction, CameraZoomActionPath, TEXT("IA_CameraZoom_Runtime"), EInputActionValueType::Axis1D);
	LoadOrMake(MasterModeAction, MasterModeActionPath, TEXT("IA_MasterMode_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(SpeedLimiterAction, SpeedLimiterActionPath, TEXT("IA_SpeedLimiter_Runtime"), EInputActionValueType::Axis1D);
	LoadOrMake(GSafeAction, GSafeActionPath, TEXT("IA_GSafe_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(ComStabAction, ComStabActionPath, TEXT("IA_ComStab_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(AfterburnerAction, AfterburnerActionPath, TEXT("IA_Afterburner_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(LandingGearAction, LandingGearActionPath, TEXT("IA_LandingGear_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(PrecisionAction, PrecisionActionPath, TEXT("IA_Precision_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(VtolAction, VtolActionPath, TEXT("IA_Vtol_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(DashboardFocusAction, DashboardFocusActionPath, TEXT("IA_DashboardFocus_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(MfdLeftAction, MfdLeftActionPath, TEXT("IA_MfdLeft_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(MfdRightAction, MfdRightActionPath, TEXT("IA_MfdRight_Runtime"), EInputActionValueType::Boolean);

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

void ASpaceshipPawn::HandleQuantumEngageStarted(const FInputActionValue& /*Value*/)
{
	SetQuantumEngageHeld(true);
}

void ASpaceshipPawn::HandleQuantumEngageCompleted(const FInputActionValue& /*Value*/)
{
	SetQuantumEngageHeld(false);
}

void ASpaceshipPawn::HandleAllStop(const FInputActionValue& /*Value*/)
{
	SetSpaceBrake(true);
}

void ASpaceshipPawn::HandleAllStopCompleted(const FInputActionValue& /*Value*/)
{
	SetSpaceBrake(false);
}

void ASpaceshipPawn::HandleMasterMode(const FInputActionValue& /*Value*/)
{
	ToggleMasterMode();
}

void ASpaceshipPawn::HandleSpeedLimiter(const FInputActionValue& Value)
{
	// The wheel is mapped to both the limiter and the zoom; Alt picks the zoom.
	if (!IsAltHeld())
	{
		AdjustSpeedLimiter(Value.Get<float>());
	}
}

void ASpaceshipPawn::HandleGSafe(const FInputActionValue& /*Value*/)
{
	SetGSafe(!bGSafe);
}

void ASpaceshipPawn::HandleAfterburner(const FInputActionValue& /*Value*/)
{
	bAfterburnerHeld = true;
}

void ASpaceshipPawn::HandleAfterburnerCompleted(const FInputActionValue& /*Value*/)
{
	bAfterburnerHeld = false;
}

void ASpaceshipPawn::HandleComStab(const FInputActionValue& /*Value*/)
{
	SetComStab(!bComStab);
}

void ASpaceshipPawn::HandleLandingGear(const FInputActionValue& /*Value*/)
{
	ToggleGear();
}

void ASpaceshipPawn::HandleMfdLeft(const FInputActionValue& /*Value*/)
{
	CycleMfdPage(0);
}

void ASpaceshipPawn::HandleMfdRight(const FInputActionValue& /*Value*/)
{
	CycleMfdPage(1);
}

void ASpaceshipPawn::CycleMfdPage(int32 Display)
{
	// Alt goes back: Shift would be the boost as well.
	const APlayerController* PlayerController = Cast<APlayerController>(GetController());
	const bool bBack = PlayerController && (PlayerController->IsInputKeyDown(EKeys::LeftAlt) || PlayerController->IsInputKeyDown(EKeys::RightAlt));
	if (CockpitDisplays)
	{
		CockpitDisplays->CyclePage(Display, bBack ? -1 : 1);
	}
}

void ASpaceshipPawn::HandlePrecision(const FInputActionValue& /*Value*/)
{
	TogglePrecisionMode();
}

bool ASpaceshipPawn::IsAltHeld() const
{
	const APlayerController* PlayerController = Cast<APlayerController>(GetController());
	return PlayerController && (PlayerController->IsInputKeyDown(EKeys::LeftAlt) || PlayerController->IsInputKeyDown(EKeys::RightAlt));
}

void ASpaceshipPawn::HandleCameraZoom(const FInputActionValue& Value)
{
	if (!IsAltHeld())
	{
		return;  // the plain wheel is the speed limiter
	}
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
	UE_LOG(LogSpaceship, Log, TEXT("%s: %s"), *GetName(), bOn ? TEXT("coupled") : TEXT("decoupled"));
}

void ASpaceshipPawn::SetSpaceBrake(bool bHeld)
{
	bSpaceBrakeHeld = bHeld;
}

float ASpaceshipPawn::GetMasterModeSwitchProgress() const
{
	return bMasterModeSwitching ? FMath::Clamp(MasterModeTimer / FMath::Max(MasterModeSwitchSeconds, 0.01f), 0.f, 1.f) : 0.f;
}

void ASpaceshipPawn::RequestMasterMode(EMasterMode Mode)
{
	if (Mode == MasterMode)
	{
		// Already there: cancels a switch the other way.
		bMasterModeSwitching = false;
		MasterModeTimer = 0.f;
		return;
	}
	if (bMasterModeSwitching && Mode == PendingMasterMode)
	{
		return;
	}
	PendingMasterMode = Mode;
	bMasterModeSwitching = true;
	MasterModeTimer = 0.f;
	if (Mode == EMasterMode::SCM && QuantumState == EQuantumState::Traveling)
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
	if (!bMasterModeSwitching)
	{
		return;
	}
	MasterModeTimer += DeltaSeconds;
	if (MasterModeTimer >= MasterModeSwitchSeconds)
	{
		MasterMode = PendingMasterMode;
		bMasterModeSwitching = false;
		MasterModeTimer = 0.f;
		CameraKick = FMath::Max(CameraKick, 0.35f);
		UE_LOG(LogSpaceship, Log, TEXT("%s: master mode %s"), *GetName(), MasterMode == EMasterMode::NAV ? TEXT("NAV") : TEXT("SCM"));
	}
}

void ASpaceshipPawn::SetSpeedLimiter(float Fraction)
{
	SpeedLimiterFraction = FMath::Clamp(Fraction, FMath::Min(SpeedLimiterMin, 1.f), 1.f);
}

void ASpaceshipPawn::AdjustSpeedLimiter(float Notches)
{
	// Snapped to whole steps, so a few notches up and down land on round numbers again.
	const float Steps = FMath::RoundToFloat(SpeedLimiterFraction / SpeedLimiterStep) + Notches;
	SetSpeedLimiter(Steps * SpeedLimiterStep);
}

float ASpaceshipPawn::GetModeMaxSpeed() const
{
	// Precision mode is a smaller SCM for the limiter and the gauge. The hard cap in UpdateLinearMotion
	// stays at the full SCM speed: switched on at speed, the flight computer brakes down with the
	// retro thrusters instead of the overspeed bleed (which would pull ~25 G from SCM speed).
	if (MasterMode == EMasterMode::NAV)
	{
		return NavMaxSpeed;
	}
	const float Scm = IsPrecisionActive() ? ScmMaxSpeed * PrecisionSpeedFraction : ScmMaxSpeed;
	// VTOL is slower than SCM but never faster than precision mode, which is slower still.
	return FMath::Lerp(Scm, FMath::Min(Scm, VtolMaxSpeed), VtolBlend);
}

float ASpaceshipPawn::GetSpeedLimit() const
{
	// The afterburner's raised limit scales with the limiter too: a half-open limiter gets half of it.
	return GetModeMaxSpeed() * SpeedLimiterFraction * (1.f + (AfterburnerSpeedMultiplier - 1.f) * AfterburnerBlend);
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
	using SpaceshipPawnDefaults::StandardGravityCmS2;
	const double MaxTotal = FMath::Max(double(GSafeMaxG), 0.0) * StandardGravityCmS2;
	const double MaxVertical = FMath::Min(double(GSafeMaxVerticalG) * StandardGravityCmS2, MaxTotal);
	FVector Result = LocalAcceleration;
	Result.Z = FMath::Clamp(Result.Z, -MaxVertical, MaxVertical);
	if (Result.Size() <= MaxTotal)
	{
		return Result;
	}
	if (!bLateralFirst)
	{
		return Result.GetSafeNormal() * MaxTotal;
	}
	// Sideways and vertical first: they are what keeps the flight path on the nose.
	const FVector Lateral(0.0, Result.Y, Result.Z);
	const double LateralSize = Lateral.Size();
	if (LateralSize >= MaxTotal)
	{
		return Lateral * (MaxTotal / LateralSize);
	}
	const double Remaining = FMath::Sqrt(MaxTotal * MaxTotal - LateralSize * LateralSize);
	Result.X = FMath::Clamp(Result.X, -Remaining, Remaining);
	return Result;
}

float ASpaceshipPawn::GetQuantumCooling() const
{
	return QuantumState == EQuantumState::Cooling
		? FMath::Clamp(1.f - QuantumCooldownTimer / FMath::Max(QuantumCooldownSeconds, 0.01f), 0.f, 1.f) : 1.f;
}

float ASpaceshipPawn::GetQuantumTravelProgress() const
{
	return QuantumState == EQuantumState::Traveling && QuantumJumpLengthCm > 1.0
		? float(FMath::Clamp(1.0 - QuantumTargetDistanceCm / QuantumJumpLengthCm, 0.0, 1.0)) : 0.f;
}

float ASpaceshipPawn::GetQuantumEngageHold() const
{
	return FMath::Clamp(QuantumEngageTimer / FMath::Max(QuantumEngageHoldSeconds, 0.01f), 0.f, 1.f);
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
		const float LookScale = FreeLookSensitivity * USpaceUserSettings::GetMouseSensitivityScale();
		FreeLookTarget.X += MouseLookDelta.X * LookScale;
		if (FreeLookMaxYawDeg < 180.f)
		{
			FreeLookTarget.X = FMath::Clamp(FreeLookTarget.X, -FreeLookMaxYawDeg, FreeLookMaxYawDeg);
		}
		FreeLookTarget.Y = FMath::Clamp(FreeLookTarget.Y + MouseLookDelta.Y * LookScale, -FreeLookMaxPitchDeg, FreeLookMaxPitchDeg);
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

void ASpaceshipPawn::HandleDashboardFocusStarted(const FInputActionValue& /*Value*/)
{
	SetDashboardFocus(true);
}

void ASpaceshipPawn::HandleDashboardFocusCompleted(const FInputActionValue& /*Value*/)
{
	SetDashboardFocus(false);
}

int32 ASpaceshipPawn::DebugSetMaterialScalar(FName Parameter, float Value)
{
	int32 Changed = 0;
	TInlineComponentArray<UMeshComponent*> Meshes(this);
	for (UMeshComponent* Mesh : Meshes)
	{
		for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
		{
			UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Mesh->GetMaterial(Slot));
			if (!Dynamic)
			{
				Dynamic = Mesh->CreateDynamicMaterialInstance(Slot);
			}
			if (Dynamic)
			{
				Dynamic->SetScalarParameterValue(Parameter, Value);
				++Changed;
			}
		}
	}
	return Changed;
}

int32 ASpaceshipPawn::DebugSetMaterialColor(FName Parameter, FLinearColor Value)
{
	int32 Changed = 0;
	TInlineComponentArray<UMeshComponent*> Meshes(this);
	for (UMeshComponent* Mesh : Meshes)
	{
		for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
		{
			UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Mesh->GetMaterial(Slot));
			if (!Dynamic)
			{
				Dynamic = Mesh->CreateDynamicMaterialInstance(Slot);
			}
			if (Dynamic)
			{
				Dynamic->SetVectorParameterValue(Parameter, Value);
				++Changed;
			}
		}
	}
	return Changed;
}

void ASpaceshipPawn::SetDashboardFocus(bool bFocus)
{
	if (bFocus && !bDashboardFocusHeld)
	{
		bDashboardFocusValid = ComputeDashboardFocus(DashboardFocusEye, DashboardFocusRotation, DashboardFocusFov);
	}
	bDashboardFocusHeld = bFocus;
}

void ASpaceshipPawn::DebugAdvanceDashboardFocus(float Seconds)
{
	for (float Left = Seconds; Left > 0.f; Left -= 1.f / 60.f)
	{
		UpdateFreeLook(FMath::Min(Left, 1.f / 60.f));
	}
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
	bAfterburnerHeld = false;
	bSpaceBrakeHeld = false;
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

TArray<FBox> ASpaceshipPawn::GetHullCollisionBoxes() const
{
	// Actor space, unscaled: the hull's collision shapes (UCX hulls and boxes from Blender) through
	// the hull's relative transform; the mesh bounds when it has none; the root box without a mesh.
	TArray<FBox> Boxes;
	const FTransform HullToActor = Hull->GetRelativeTransform();
	if (const UStaticMesh* Mesh = Hull->GetStaticMesh())
	{
		if (const UBodySetup* Body = Mesh->GetBodySetup())
		{
			for (const FKConvexElem& Convex : Body->AggGeom.ConvexElems)
			{
				Boxes.Add(Convex.ElemBox.TransformBy(Convex.GetTransform() * HullToActor));
			}
			for (const FKBoxElem& Box : Body->AggGeom.BoxElems)
			{
				const FVector Half(Box.X * 0.5, Box.Y * 0.5, Box.Z * 0.5);
				Boxes.Add(FBox(-Half, Half).TransformBy(Box.GetTransform() * HullToActor));
			}
		}
		if (Boxes.Num() == 0)
		{
			Boxes.Add(Mesh->GetBoundingBox().TransformBy(HullToActor));
		}
	}
	if (Boxes.Num() == 0)
	{
		const FVector Extent = HullCollision->GetUnscaledBoxExtent();
		Boxes.Add(FBox(-Extent, Extent));
	}
	return Boxes;
}

double ASpaceshipPawn::GetHullClearance(const FVector& Location, float CapsuleRadius, float CapsuleHalfHeight) const
{
	// A pilot standing where the landed ship stands: capsule bottom at the lowest point of the hull
	// shapes (the gear), whatever height Location has. Only shapes within that height count, then
	// the gap in the ship's floor plane. Pure geometry, so it also works where collision queries do
	// not (commandlets) and does not depend on the physics scene being up to date.
	const TArray<FBox> Boxes = GetHullCollisionBoxes();
	double Floor = TNumericLimits<double>::Max();
	for (const FBox& Box : Boxes)
	{
		Floor = FMath::Min(Floor, Box.Min.Z);
	}
	const double Top = Floor + 2.0 * CapsuleHalfHeight;
	const FVector Local = GetActorTransform().InverseTransformPositionNoScale(Location);
	double Clearance = TNumericLimits<double>::Max();
	for (const FBox& Box : Boxes)
	{
		if (Box.Min.Z >= Top || Box.Max.Z <= Floor)
		{
			continue;  // above the pilot's head (or below the feet)
		}
		const double DX = FMath::Max3(Box.Min.X - Local.X, 0.0, Local.X - Box.Max.X);
		const double DY = FMath::Max3(Box.Min.Y - Local.Y, 0.0, Local.Y - Box.Max.Y);
		Clearance = FMath::Min(Clearance, FMath::Sqrt(DX * DX + DY * DY) - CapsuleRadius);
	}
	return Clearance;
}

FVector ASpaceshipPawn::PushClearOfHull(const FVector& Start, const FVector& Direction, float CapsuleRadius, float CapsuleHalfHeight) const
{
	const FVector Step = FVector::VectorPlaneProject(Direction, GetActorUpVector()).GetSafeNormal() * 20.0;
	if (Step.IsNearlyZero())
	{
		return Start;
	}
	FVector Location = Start;
	// Out in 20 cm steps until the capsule clears every hull shape by ExitClearanceCm (40 m at most).
	for (int32 Index = 0; Index < 200 && GetHullClearance(Location, CapsuleRadius, CapsuleHalfHeight) < ExitClearanceCm; ++Index)
	{
		Location += Step;
	}
	return Location;
}

TArray<FVector> ASpaceshipPawn::GetExitCandidates() const
{
	TArray<FVector> Candidates;
	const ACharacter* PilotDefaults = Cast<ACharacter>(PilotCharacterClass ? PilotCharacterClass->GetDefaultObject() : nullptr);
	const float CapsuleRadius = PilotDefaults ? PilotDefaults->GetSimpleCollisionRadius() : 42.f;
	const float CapsuleHalfHeight = PilotDefaults ? PilotDefaults->GetSimpleCollisionHalfHeight() : 96.f;

	// The Exit socket says which side and where along the hull; the pilot is then moved sideways
	// until clear of the hull. The first fighter's socket sat 44 cm off the belly, under the edge of the
	// fuselage, which put the pilot practically inside the ship.
	static const FName ExitSockets[] = { FName(TEXT("Exit")), FName(TEXT("SOCKET_Exit")) };
	if (const FName* Socket = Algo::FindByPredicate(ExitSockets, [this](const FName& Name) { return Hull->DoesSocketExist(Name); }))
	{
		const FVector SocketLocation = Hull->GetSocketLocation(*Socket);
		const double Side = GetActorTransform().InverseTransformPositionNoScale(SocketLocation).Y;
		const FVector Outward = GetActorRightVector() * (Side < 0.0 ? -1.0 : 1.0);
		Candidates.Add(PushClearOfHull(SocketLocation, Outward, CapsuleRadius, CapsuleHalfHeight));
	}

	// Then around the hull: its mesh bounds where there is a mesh (wings included), else the box.
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
			Candidates.Add(PushClearOfHull(Center + Direction.Key * (Direction.Value + CapsuleRadius + ExitClearanceCm + Extra),
				Direction.Key, CapsuleRadius, CapsuleHalfHeight));
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

	// Facing the ship: the character's camera then sits on the far side, away from the hull, and
	// shows the ship. Facing along the ship's heading put the camera boom into a wing, which
	// pulled the camera in for a moment after getting out.
	auto FacingFrom = [this, &Up](const FVector& Location)
	{
		FVector Flat = FVector::VectorPlaneProject(GetActorLocation() - Location, Up).GetSafeNormal();
		if (Flat.IsNearlyZero())
		{
			Flat = FVector::VectorPlaneProject(GetActorForwardVector(), Up).GetSafeNormal();
		}
		if (Flat.IsNearlyZero())
		{
			Flat = FVector::VectorPlaneProject(GetActorUpVector(), Up).GetSafeNormal();
		}
		return FRotationMatrix::MakeFromXZ(Flat, Up).ToQuat();
	};

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
			return FTransform(FacingFrom(Location), Location);
		}
	}
	// Nowhere free (boxed in): the farthest spot beside the ship, where at least the hull is not.
	const FVector Fallback = Candidates.Num() > 0 ? Candidates.Last(3) : GetActorLocation() + GetActorRightVector() * 1000.0;
	UE_LOG(LogSpaceship, Warning, TEXT("%s: no free exit spot among %d candidates; using %s"), *GetName(), Candidates.Num(), *Fallback.ToString());
	const FVector FallbackLocation = OnGround(Fallback);
	return FTransform(FacingFrom(FallbackLocation), FallbackLocation);
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
	UpdateViewCollection();

	if (CameraSnapTicks > 0 && --CameraSnapTicks == 0)
	{
		CameraBoom->bEnableCameraLag = true;
	}
}

void ASpaceshipPawn::StepFlight(float DeltaSeconds)
{
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
	if (LandingState == ELandingState::Landed)
	{
		UpdateLandedMotion(DeltaSeconds);
	}
	else if (QuantumState == EQuantumState::Traveling)
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

FVector ASpaceshipPawn::DebugStepFlight(float DeltaSeconds, float Thrust, float Strafe, float Lift, bool bBoost)
{
	ThrustInput = Thrust;
	StrafeInput = Strafe;
	LiftInput = Lift;
	bBoostHeld = bBoost;
	StepFlight(DeltaSeconds);
	return LinearVelocity;
}

FVector ASpaceshipPawn::DebugStepFlightInput(float DeltaSeconds, const FVector& LinearInput, const FVector& RotationInput, bool bBoost)
{
	ThrustInput = float(LinearInput.X);
	StrafeInput = float(LinearInput.Y);
	LiftInput = float(LinearInput.Z);
	RollInput = float(RotationInput.X);
	LookInput = FVector2D(RotationInput.Z, RotationInput.Y);
	bBoostHeld = bBoost;
	StepFlight(DeltaSeconds);
	return LinearVelocity;
}

// -------------------------------------------------------------------------------------------
// Boost, afterburner and the quantum drive
// -------------------------------------------------------------------------------------------

void ASpaceshipPawn::UpdateBoost(float DeltaSeconds)
{
	const bool bWasActive = bBoostActive;
	if (bBoostLocked && BoostEnergy >= BoostUnlockFraction)
	{
		bBoostLocked = false;
	}
	// Boost feeds the manoeuvring thrusters and rotation, so it burns energy whenever Shift is held.
	bBoostActive = bBoostHeld && !bBoostLocked && BoostEnergy > 0.f
		&& QuantumState != EQuantumState::Traveling && LandingState != ELandingState::Landed;

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
		CameraKick = FMath::Max(CameraKick, 0.3f);
	}
}

void ASpaceshipPawn::UpdateAfterburner(float DeltaSeconds)
{
	const bool bWasActive = bAfterburnerActive;
	if (bAfterburnerLocked && AfterburnerFuel >= AfterburnerUnlockFraction)
	{
		bAfterburnerLocked = false;
	}
	// SCM only (NAV already flies at five times SCM speed and has the quantum drive), and only while it
	// can do something: W forward, no spacebrake, flying. VTOL refuses it too - the mains are down to a
	// third and the ship is standing on its lift thrusters (SC-2b).
	bAfterburnerActive = bAfterburnerHeld && ThrustInput > 0.f && !bSpaceBrakeHeld && !bAfterburnerLocked && AfterburnerFuel > 0.f
		&& MasterMode == EMasterMode::SCM && !IsPrecisionActive() && !bVtolMode && QuantumState != EQuantumState::Traveling
		&& LandingState != ELandingState::Landed;

	if (bAfterburnerActive)
	{
		AfterburnerFuel = FMath::Max(0.f, AfterburnerFuel - DeltaSeconds / AfterburnerDurationSeconds);
		AfterburnerRefillWait = AfterburnerRefillDelaySeconds;
		if (AfterburnerFuel <= 0.f)
		{
			bAfterburnerLocked = true;
			bAfterburnerActive = false;
		}
	}
	else
	{
		AfterburnerRefillWait = FMath::Max(0.f, AfterburnerRefillWait - DeltaSeconds);
		if (AfterburnerRefillWait <= 0.f)
		{
			AfterburnerFuel = FMath::Min(1.f, AfterburnerFuel + DeltaSeconds / AfterburnerRefillSeconds);
		}
	}

	// The raised limit spools in quickly and fades out slowly, so running dry or letting go never
	// yanks the ship back to SCM speed.
	AfterburnerBlend = bAfterburnerActive
		? FMath::Min(1.f, AfterburnerBlend + DeltaSeconds / AfterburnerSpoolSeconds)
		: FMath::Max(0.f, AfterburnerBlend - DeltaSeconds / AfterburnerFadeSeconds);

	if (bAfterburnerActive && !bWasActive)
	{
		CameraKick = FMath::Max(CameraKick, 1.f);
		PlayOneShot(BoostStartSound);
	}
}

namespace SpaceshipQuantum
{
	/** A body the quantum drive can jump to. */
	struct FBody
	{
		AActor* Actor = nullptr;
		FText Name;
		FVector Centre = FVector::ZeroVector;
		double RadiusCm = 0.0;
	};

	/**
	 * Every body in the level: the terrain planets (ACelestialBody, radius measured towards Location, so
	 * it is the terrain's there) and the distant ones (ADistantBody: moons, the gas giant).
	 */
	void Gather(const UWorld* World, const FVector& Location, TArray<FBody>& OutBodies)
	{
		OutBodies.Reset();
		if (!World)
		{
			return;
		}
		for (TActorIterator<ACelestialBody> It(World); It; ++It)
		{
			const FVector Centre = It->GetActorLocation();
			const double Radius = FVector::Dist(Location, Centre) - It->GetSurfaceDistance(Location);
			OutBodies.Add({ *It, It->GetDisplayName().IsEmpty() ? FText::FromString(It->GetName()) : It->GetDisplayName(), Centre, FMath::Max(Radius, 1.0) });
		}
		for (TActorIterator<ADistantBody> It(World); It; ++It)
		{
			OutBodies.Add({ *It, It->GetDisplayName().IsEmpty() ? FText::FromString(It->GetName()) : It->GetDisplayName(),
				It->GetActorLocation(), double(It->GetRadiusKm()) * 100000.0 });
		}
	}
}

bool ASpaceshipPawn::SegmentHitsSphere(const FVector& Start, const FVector& End, const FVector& Centre, double Radius)
{
	const FVector Segment = End - Start;
	const double LengthSq = Segment.SizeSquared();
	const double T = LengthSq > 0.0 ? FMath::Clamp(FVector::DotProduct(Centre - Start, Segment) / LengthSq, 0.0, 1.0) : 0.0;
	return FVector::DistSquared(Start + Segment * T, Centre) < Radius * Radius;
}

double ASpaceshipPawn::ComputeQuantumArrivalAltitude(double BodyRadiusCm) const
{
	return FMath::Max(double(QuantumArrivalRadii) * BodyRadiusCm, double(QuantumMinArrivalKm) * 100000.0);
}

double ASpaceshipPawn::ComputeQuantumSpeed(double RemainingCm, double CurrentSpeedCmS, float DeltaSeconds) const
{
	return ComputeQuantumSpeedAt(RemainingCm, CurrentSpeedCmS, DeltaSeconds, 1.0e6f);
}

double ASpaceshipPawn::ComputeQuantumSpeedAt(double RemainingCm, double CurrentSpeedCmS, float DeltaSeconds, float SecondsIntoJump) const
{
	// Braking keeps the full rate (the arrival must be exact); speeding up eases in.
	const double Ramp = QuantumRampSeconds > 0.f ? FMath::Max(0.03, double(FMath::SmoothStep(0.f, QuantumRampSeconds, SecondsIntoJump))) : 1.0;
	const double Accel = double(QuantumAccelerationKmS2) * 100000.0;
	const double Top = double(QuantumMaxSpeedKmS) * 100000.0;
	const double Exit = QuantumExitSpeed;
	// The speed from which braking at Accel arrives at Exit exactly at the arrival point.
	const double Braking = FMath::Sqrt(Exit * Exit + 2.0 * Accel * FMath::Max(RemainingCm, 0.0));
	const double Rising = FMath::Max(CurrentSpeedCmS, Exit) + Accel * Ramp * DeltaSeconds;
	return FMath::Max(Exit, FMath::Min3(Top, Braking, Rising));
}

float ASpaceshipPawn::ComputeQuantumFuelUse(double DistanceCm) const
{
	return float(DistanceCm / 1.0e8) * QuantumFuelPer1000Km;
}

void ASpaceshipPawn::SetQuantumEngageHeld(bool bHeld)
{
	bQuantumEngageHeld = bHeld;
	if (!bHeld)
	{
		QuantumEngageTimer = 0.f;
		if (QuantumChargeAudio)
		{
			QuantumChargeAudio->FadeOut(0.2f, 0.f);
			QuantumChargeAudio = nullptr;
		}
	}
}

void ASpaceshipPawn::UpdateQuantumTarget()
{
	const FVector Location = GetActorLocation();
	const FVector Nose = GetActorForwardVector();
	TArray<SpaceshipQuantum::FBody> Bodies;
	SpaceshipQuantum::Gather(GetWorld(), Location, Bodies);

	// In a jump the destination is fixed; otherwise it is the body closest to the nose, within QuantumPickDeg.
	const SpaceshipQuantum::FBody* Picked = nullptr;
	if (QuantumState == EQuantumState::Traveling)
	{
		Picked = Bodies.FindByPredicate([this](const SpaceshipQuantum::FBody& Body) { return Body.Actor == QuantumTarget.Get(); });
	}
	else
	{
		double BestCos = FMath::Cos(FMath::DegreesToRadians(double(QuantumPickDeg)));
		for (const SpaceshipQuantum::FBody& Body : Bodies)
		{
			const double Cos = FVector::DotProduct((Body.Centre - Location).GetSafeNormal(), Nose);
			if (Cos > BestCos)
			{
				BestCos = Cos;
				Picked = &Body;
			}
		}
	}

	if (!Picked)
	{
		QuantumTarget.Reset();
		QuantumTargetName = FText::GetEmpty();
		QuantumTargetDistanceCm = 0.0;
		return;
	}
	if (QuantumTarget.Get() != Picked->Actor)
	{
		// A new destination: calibration was for the old one.
		QuantumCalibration = 0.f;
	}
	QuantumTarget = Picked->Actor;
	QuantumTargetName = Picked->Name;
	QuantumTargetCentre = Picked->Centre;
	QuantumTargetRadiusCm = Picked->RadiusCm;
	const double ArrivalFromCentre = Picked->RadiusCm + ComputeQuantumArrivalAltitude(Picked->RadiusCm);
	QuantumTargetDistanceCm = FMath::Max(FVector::Dist(Location, Picked->Centre) - ArrivalFromCentre, 0.0);
}

EQuantumBlocker ASpaceshipPawn::EvaluateQuantum() const
{
	if (LandingState == ELandingState::Landed)
	{
		return EQuantumBlocker::Landed;
	}
	if (MasterMode != EMasterMode::NAV || bMasterModeSwitching)
	{
		return EQuantumBlocker::NeedsNav;
	}
	if (!QuantumTarget.IsValid())
	{
		return EQuantumBlocker::NoTarget;
	}
	if (QuantumTargetDistanceCm < double(QuantumMinJumpKm) * 100000.0)
	{
		return EQuantumBlocker::TooClose;
	}
	if (ComputeQuantumFuelUse(QuantumTargetDistanceCm) > QuantumFuel)
	{
		return EQuantumBlocker::NoFuel;
	}
	// Anything on the way to the arrival point, the destination itself included (the far side of a
	// planet). Each body counts with its arrival shell, so the jump never skims a surface.
	const FVector Location = GetActorLocation();
	const FVector Arrival = QuantumTargetCentre + (Location - QuantumTargetCentre).GetSafeNormal()
		* (QuantumTargetRadiusCm + ComputeQuantumArrivalAltitude(QuantumTargetRadiusCm));
	TArray<SpaceshipQuantum::FBody> Bodies;
	SpaceshipQuantum::Gather(GetWorld(), Location, Bodies);
	for (const SpaceshipQuantum::FBody& Body : Bodies)
	{
		// The body the ship is leaving does not block: the path starts above it and heads away.
		const double Clearance = Body.Actor == QuantumTarget.Get() ? Body.RadiusCm * 0.99 : Body.RadiusCm;
		if (FVector::Dist(Location, Body.Centre) > Body.RadiusCm * 1.01 && SegmentHitsSphere(Location, Arrival, Body.Centre, Clearance))
		{
			return EQuantumBlocker::Obstructed;
		}
	}
	return EQuantumBlocker::None;
}

void ASpaceshipPawn::UpdateQuantum(float DeltaSeconds)
{
	UpdateQuantumTarget();

	if (QuantumState == EQuantumState::Traveling)
	{
		return;  // UpdateQuantumTravel flies it and ends it
	}
	if (QuantumState == EQuantumState::Cooling)
	{
		QuantumCooldownTimer = FMath::Max(0.f, QuantumCooldownTimer - DeltaSeconds);
	}

	QuantumBlocker = EvaluateQuantum();
	const bool bSpooling = QuantumBlocker != EQuantumBlocker::NeedsNav && QuantumBlocker != EQuantumBlocker::Landed
		&& QuantumBlocker != EQuantumBlocker::NoTarget;
	// The spool runs in NAV with a destination and holds while blocked; it winds down in SCM.
	QuantumSpool = bSpooling
		? FMath::Min(1.f, QuantumSpool + DeltaSeconds / FMath::Max(QuantumSpoolSeconds, 0.01f))
		: FMath::Max(0.f, QuantumSpool - DeltaSeconds / FMath::Max(QuantumSpoolSeconds, 0.01f));

	// Calibration needs the nose on the destination and falls back fast when it leaves.
	const bool bAligned = QuantumTarget.IsValid()
		&& FVector::DotProduct((QuantumTargetCentre - GetActorLocation()).GetSafeNormal(), GetActorForwardVector())
			>= FMath::Cos(FMath::DegreesToRadians(double(QuantumAlignDeg)));
	QuantumCalibration = bSpooling && bAligned && QuantumBlocker == EQuantumBlocker::None
		? FMath::Min(1.f, QuantumCalibration + DeltaSeconds / FMath::Max(QuantumCalibrationSeconds, 0.01f))
		: FMath::Max(0.f, QuantumCalibration - 2.f * DeltaSeconds / FMath::Max(QuantumCalibrationSeconds, 0.01f));

	const bool bCool = QuantumState != EQuantumState::Cooling || QuantumCooldownTimer <= 0.f;
	if (!bCool)
	{
		QuantumState = EQuantumState::Cooling;
	}
	else if (!bSpooling)
	{
		QuantumState = EQuantumState::Idle;
	}
	else if (QuantumSpool >= 1.f && QuantumCalibration >= 1.f && QuantumBlocker == EQuantumBlocker::None && bAligned)
	{
		QuantumState = EQuantumState::Ready;
	}
	else
	{
		QuantumState = EQuantumState::Charging;
	}

	// Engage: the button held for QuantumEngageHoldSeconds while ready.
	if (bQuantumEngageHeld && QuantumState == EQuantumState::Ready)
	{
		if (QuantumEngageTimer <= 0.f && !QuantumChargeAudio)
		{
			QuantumChargeAudio = PlayOneShot(QuantumChargeSound);
		}
		QuantumEngageTimer += DeltaSeconds;
		if (QuantumEngageTimer >= QuantumEngageHoldSeconds)
		{
			BeginQuantumJump();
		}
	}
	else if (!bQuantumEngageHeld)
	{
		QuantumEngageTimer = 0.f;
	}
}

void ASpaceshipPawn::BeginQuantumJump()
{
	QuantumState = EQuantumState::Traveling;
	QuantumBlocker = EQuantumBlocker::None;
	QuantumEngageTimer = 0.f;
	QuantumJumpLengthCm = FMath::Max(QuantumTargetDistanceCm, 1.0);
	QuantumTravelSeconds = 0.f;
	QuantumFuel = FMath::Max(0.f, QuantumFuel - ComputeQuantumFuelUse(QuantumTargetDistanceCm));
	bBoostActive = false;
	bAfterburnerActive = false;
	bVtolMode = false;
	// A lighter jolt than a drop-out: the jump now builds up (QuantumRampSeconds) rather than snapping.
	CameraKick = 0.4f;
	QuantumChargeAudio = nullptr;
	PlayOneShot(QuantumEngageSound);
	// The jump's burst of green light (the reference at 4:10).
	SpeedTunnel->TriggerFlare(1.6f);
	UE_LOG(LogSpaceship, Log, TEXT("%s: quantum jump to %s, %.0f km, fuel left %.0f%%"), *GetName(),
		*QuantumTargetName.ToString(), QuantumJumpLengthCm / 100000.0, QuantumFuel * 100.f);
}

void ASpaceshipPawn::EndQuantumJump(EQuantumBlocker Reason)
{
	QuantumState = EQuantumState::Cooling;
	QuantumCooldownTimer = QuantumCooldownSeconds;
	QuantumBlocker = Reason;
	QuantumSpool = 0.f;
	QuantumCalibration = 0.f;
	QuantumEngageTimer = 0.f;
	CameraKick = 1.f;
	// Out at NAV speed at most; the overspeed bleed takes the rest.
	const double Speed = LinearVelocity.Size();
	if (Speed > QuantumExitSpeed)
	{
		LinearVelocity *= QuantumExitSpeed / Speed;
	}
	AngularVelocity = FVector::ZeroVector;
	PlayOneShot(QuantumExitSound);
	UE_LOG(LogSpaceship, Log, TEXT("%s: quantum exit (%s) %.0f km from %s"), *GetName(),
		Reason == EQuantumBlocker::Pilot ? TEXT("pilot") : TEXT("arrived"), QuantumTargetDistanceCm / 100000.0, *QuantumTargetName.ToString());
}

void ASpaceshipPawn::UpdateQuantumTravel(float DeltaSeconds)
{
	if (!QuantumTarget.IsValid())
	{
		EndQuantumJump(EQuantumBlocker::NoTarget);
		return;
	}
	const FVector Location = GetActorLocation();
	const FVector Direction = (QuantumTargetCentre - Location).GetSafeNormal();
	const double Remaining = QuantumTargetDistanceCm;
	QuantumTravelSeconds += DeltaSeconds;
	const double Speed = ComputeQuantumSpeedAt(Remaining, LinearVelocity.Size(), DeltaSeconds, QuantumTravelSeconds);
	const double Step = Speed * DeltaSeconds;

	// No steering in a jump (the reference says so outright): the nose swings onto the destination.
	const FQuat Facing = FRotationMatrix::MakeFromXZ(Direction, GetActorUpVector()).ToQuat();
	const FQuat Rotation = FQuat::Slerp(GetActorQuat(), Facing, FMath::Min(1.f, 3.f * DeltaSeconds));
	AngularVelocity = FVector::ZeroVector;
	EngineDemand = 0.6f;
	ThrusterAcceleration = FVector::ZeroVector;
	GForce = FMath::FInterpTo(GForce, 0.f, DeltaSeconds, 8.f);

	if (Step >= Remaining)
	{
		SetActorLocationAndRotation(Location + Direction * Remaining, Rotation);
		LinearVelocity = Direction * QuantumExitSpeed;
		QuantumTargetDistanceCm = 0.0;
		EndQuantumJump(EQuantumBlocker::None);
		return;
	}
	LinearVelocity = Direction * Speed;
	// No sweep: the path was checked for bodies before the jump, and at tens of km/s a sweep per
	// frame against the terrain would cost more than it could ever find.
	SetActorLocationAndRotation(Location + Direction * Step, Rotation);
}

bool ASpaceshipPawn::DebugEngageQuantum(const FString& TargetName, float TravelFraction)
{
	TArray<SpaceshipQuantum::FBody> Bodies;
	SpaceshipQuantum::Gather(GetWorld(), GetActorLocation(), Bodies);
	const SpaceshipQuantum::FBody* Picked = nullptr;
	double BestCos = -2.0;
	for (const SpaceshipQuantum::FBody& Body : Bodies)
	{
		if (!TargetName.IsEmpty())
		{
			if (Body.Name.ToString().StartsWith(TargetName) || Body.Actor->GetName().Contains(TargetName))
			{
				Picked = &Body;
				break;
			}
			continue;
		}
		const double Cos = FVector::DotProduct((Body.Centre - GetActorLocation()).GetSafeNormal(), GetActorForwardVector());
		if (Cos > BestCos)
		{
			BestCos = Cos;
			Picked = &Body;
		}
	}
	if (!Picked)
	{
		UE_LOG(LogSpaceship, Warning, TEXT("%s: no quantum destination '%s'"), *GetName(), *TargetName);
		return false;
	}
	MasterMode = EMasterMode::NAV;
	bMasterModeSwitching = false;
	QuantumTarget = Picked->Actor;
	UpdateQuantumTarget();
	const FVector Direction = (QuantumTargetCentre - GetActorLocation()).GetSafeNormal();
	SetActorRotation(FRotationMatrix::MakeFromXZ(Direction, GetActorUpVector()).ToQuat());
	BeginQuantumJump();
	if (TravelFraction > 0.f)
	{
		const double Skip = QuantumJumpLengthCm * FMath::Clamp(double(TravelFraction), 0.0, 0.95);
		SetActorLocation(GetActorLocation() + Direction * Skip);
		QuantumTargetDistanceCm -= Skip;
	}
	LinearVelocity = Direction * ComputeQuantumSpeed(QuantumTargetDistanceCm, double(QuantumMaxSpeedKmS) * 100000.0, 0.f);
	// Shots part-way through a jump start past the acceleration ramp; at 0 the ramp plays out.
	QuantumTravelSeconds = TravelFraction > 0.f ? QuantumRampSeconds + 1.f : 0.f;
	if (TravelFraction <= 0.f)
	{
		LinearVelocity = Direction * double(QuantumExitSpeed);
	}
	QuantumBlend = TravelFraction > 0.f ? 1.f : 0.f;
	return true;
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
	if (MasterMode == EMasterMode::NAV)
	{
		RateScale *= NavTurnScale;
	}
	// Boost feeds the manoeuvring thrusters: faster turns, and faster to start and stop them.
	// Precision mode turns gently, and starts and stops turns as gently.
	const double RotationBoost = (bBoostActive ? BoostRotationMultiplier : 1.0) * (IsPrecisionActive() ? PrecisionTurnScale : 1.0);
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
		const double Maneuver = (MasterMode == EMasterMode::NAV ? NavManeuverScale : 1.0) * (bBoostActive ? BoostManeuverMultiplier : 1.0);
		// VTOL (SC-2b): the thrust moves off the mains and onto the lift and lateral thrusters.
		const double Vtol = double(VtolBlend);
		const double VtolMain = FMath::Lerp(1.0, double(VtolThrustFraction), Vtol);
		const double VtolLift = FMath::Lerp(1.0, double(VtolLiftMultiplier), Vtol);
		const double VtolStrafe = FMath::Lerp(1.0, double(VtolStrafeMultiplier), Vtol);
		const double ForwardCap = ThrustAcceleration * (bAfterburnerActive ? AfterburnerThrustMultiplier : 1.0) * VtolMain;
		const double RetroCap = RetroAcceleration * (bBoostActive ? BoostManeuverMultiplier : 1.0) * VtolMain;
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
				if (VtolBlend > 0.f)
				{
					// In VTOL Space and Ctrl are a climb rate, not another way of reaching the top speed.
					const double ClimbLimit = FMath::Lerp(SpeedLimit, double(VtolClimbSpeed) * SpeedLimiterFraction, double(VtolBlend));
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
			if (bSurfaceValid && GroundGapCm >= 0.f && GroundGapCm - GetGearGroundOffsetCm() < 400.f && ThrustInput == 0.f && LiftInput <= 0.f && !bSpaceBrakeHeld)
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
		if (bGroundContact)
		{
			// After gravity, so on a gentle slope friction cancels this frame's pull down the slope
			// completely and the ship stands still instead of creeping.
			LinearVelocity = ApplyGroundFriction(LinearVelocity, GroundNormal, Up, float(Gravity), DeltaSeconds);
		}

		const double Speed = LinearVelocity.Size();
		{
			const double ModeTop = MasterMode == EMasterMode::NAV ? NavMaxSpeed : ScmMaxSpeed;
			const double SpeedCap = ModeTop * (1.0 + (AfterburnerSpeedMultiplier - 1.0) * AfterburnerBlend);
			if (Speed > SpeedCap)
			{
				// Above the mode's top speed (afterburner fading, or leaving NAV for SCM): while the
				// afterburner pushes this is an ordinary clamp, otherwise the excess bleeds off.
				const double Excess = (Speed - SpeedCap) * FMath::Min(double(OverspeedDecay) * DeltaSeconds, 1.0);
				const double Target = bAfterburnerActive ? SpeedCap : Speed - Excess;
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

ELandingBlocker ASpaceshipPawn::EvaluateTouchdown(float HullGap, float Speed, float TiltDeg, float SlopeDeg, bool bEngineInput, bool bGearDown) const
{
	// First, so the warning shows all the way down through the probe zone, not only at the ground.
	if (!bGearDown)
	{
		return ELandingBlocker::GearUp;
	}
	if (HullGap < 0.f)
	{
		return ELandingBlocker::TooHigh;
	}
	return EvaluateLanding(FMath::Max(HullGap - GearExtensionCm, 0.f), Speed, TiltDeg, SlopeDeg, bEngineInput);
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
		const double ProbeLength = FMath::Max(LandingMaxGapCm, GroundContactToleranceCm) + GearExtensionCm + 200.0;
		FHitResult Hit;
		if (SweepHull(Start, Start - Environment.Up * ProbeLength, GetActorQuat(), Hit))
		{
			GroundGapCm = Hit.bStartPenetrating ? 0.f : float(Hit.Distance);
		}
		// Touching means the pads with the gear down, the belly without it.
		bGroundContact = GroundGapCm >= 0.f && GroundGapCm - GetGearGroundOffsetCm() <= GroundContactToleranceCm;
	}

	const bool bEngineInput = FMath::Abs(ThrustInput) >= TakeoffInputThreshold || LiftInput >= TakeoffInputThreshold
		|| QuantumState == EQuantumState::Traveling;

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
		: EvaluateTouchdown(GroundGapCm, LinearVelocity.Size(), GroundTiltDeg, GroundSlopeDeg, bEngineInput, IsGearDeployed());

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
	bBoostActive = false;
	bAfterburnerActive = false;
	PlayOneShot(TouchdownSound, FMath::Clamp(LinearVelocity.Size() / FMath::Max(LandingMaxSpeed, 1.f), 0.4f, 1.f));
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
	// With the gear down the hull rests GearExtensionCm up, on the pads.
	const double RestHeight = 1.0 + GetGearGroundOffsetCm();
	FHitResult Hit;
	if (SweepHull(Location + GroundNormal * 100.0, Location - GroundNormal * (300.0 + RestHeight), Rotation, Hit) && !Hit.bStartPenetrating)
	{
		Location = FMath::Lerp(Location, Hit.Location + GroundNormal * RestHeight, Alpha);
	}

	SetActorLocationAndRotation(Location, Rotation);
}

void ASpaceshipPawn::UpdateCameraEffects(float DeltaSeconds)
{
	BoostBlend = FMath::FInterpTo(BoostBlend, bBoostActive ? 1.f : 0.f, DeltaSeconds, 4.f);
	// Asymmetric on purpose: the punch arrives at once, the view settles back slowly. Symmetric easing
	// made lighting the afterburner feel soft, which is most of what "no kick" was about.
	AfterburnerFeel = FMath::FInterpTo(AfterburnerFeel, bAfterburnerActive ? 1.f : 0.f, DeltaSeconds,
		bAfterburnerActive ? 9.f : 2.5f);
	// The quantum look arrives in about a second and leaves faster; the last 5% of a jump fades it out.
	// The jump's look follows its speed, so it builds up with the acceleration ramp instead of snapping
	// on (the author, 22. 9. 2026); the last 5 % of the jump fades it out again.
	const float SpeedShare = float(LinearVelocity.Size() / FMath::Max(double(QuantumMaxSpeedKmS) * 100000.0 * QuantumLookFullSpeedShare, 1.0));
	const float QuantumTarget01 = QuantumState == EQuantumState::Traveling
		? FMath::SmoothStep(0.f, 1.f, FMath::Clamp(SpeedShare, 0.f, 1.f)) * FMath::Clamp((1.f - GetQuantumTravelProgress()) / 0.05f, 0.f, 1.f) : 0.f;
	QuantumBlend = FMath::FInterpTo(QuantumBlend, QuantumTarget01, DeltaSeconds, QuantumTarget01 > QuantumBlend ? 4.f : 4.f);
	CameraKick *= FMath::Exp(-5.f * DeltaSeconds);
	// No camera lag in a quantum jump: even capped at 15 m it trails along the flight path, and
	// looked at from the side (free look) that pushed the ship out of the frame (21. 9. 2026).
	// The lag is not switched off any more, it is wound up: at the moment it went off, the boom
	// snapped to its exact place and the ship jumped across the screen (the author, 22. 9. 2026).
	// Switched off rather than capped at 0 would not do either: a CameraLagMaxDistance of 0 means no
	// cap at all, and the camera was left kilometres behind.
	if (CameraSnapTicks == 0)
	{
		const float Catching = FMath::Max(QuantumState == EQuantumState::Traveling ? 1.f : 0.f, QuantumBlend);
		CameraBoom->bEnableCameraLag = true;
		CameraBoom->CameraLagSpeed = FMath::Lerp(BaseCameraLagSpeed, QuantumCameraLagSpeed, FMath::SmoothStep(0.f, 1.f, Catching));
	}

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

	// A jump is dark: the tunnel is nearly black with a bright point ahead, and letting the eye
	// adapt to it washed the whole frame out to a flat navy blue (the author against the reference,
	// 22. 9. 2026). So the exposure is pinned while the jump lasts.
	for (UCameraComponent* Camera : { ToRawPtr(ChaseCamera), ToRawPtr(CockpitCamera) })
	{
		FPostProcessSettings& Post = Camera->PostProcessSettings;
		Post.bOverride_AutoExposureMinBrightness = QuantumBlend > 0.001f;
		Post.bOverride_AutoExposureMaxBrightness = QuantumBlend > 0.001f;
		const float OwnBias = Camera == CockpitCamera ? CockpitExposureBias : 0.f;
		Post.bOverride_AutoExposureBias = QuantumBlend > 0.001f || OwnBias != 0.f;
		const float Pinned = FMath::Lerp(0.f, QuantumExposure, QuantumBlend);
		Post.AutoExposureMinBrightness = FMath::Max(Pinned, 0.03f);
		Post.AutoExposureMaxBrightness = FMath::Max(Pinned, 0.03f);
		Post.AutoExposureBias = FMath::Lerp(OwnBias, QuantumExposureBias, QuantumBlend);
	}

	// Speed you can feel: the view widens with the afterburner and more in a quantum jump.
	const float FovKick = AfterburnerFovKick * AfterburnerFeel + QuantumFovKick * QuantumBlend;
	ChaseCamera->SetFieldOfView(BaseChaseFov + FovKick);
	const float CockpitFov = FMath::Lerp(BaseCockpitFov, CockpitZoomFov, CockpitZoom) + 0.6f * FovKick * (1.f - CockpitZoom);
	CockpitCamera->SetFieldOfView(FMath::Lerp(CockpitFov, DashboardFocusFov, DashboardFocusBlend));

	// Smooth noise rather than random jumps: a rumble, not a flicker. Nothing moves when calm.
	static const IConsoleVariable* ShakeScale = IConsoleManager::Get().RegisterConsoleVariable(TEXT("space.CameraShake"), 1.f,
		TEXT("Camera shake multiplier (boost, afterburner, quantum, heat, kicks); 0 = none."), ECVF_Default);
	const float Spool = QuantumState == EQuantumState::Ready ? GetQuantumEngageHold() : 0.f;
	const float Amplitude = ShakeScale->GetFloat() * (HeatShakeCm * Heat * Heat + BoostShakeCm * BoostBlend + AfterburnerShakeCm * AfterburnerFeel
		+ QuantumShakeCm * (Spool * Spool + 0.25f * QuantumBlend) + KickShakeCm * CameraKick);
	const double Time = GetWorld()->GetTimeSeconds();
	const FVector Shake = Amplitude < 0.01f
		? FVector::ZeroVector
		: FVector(
			FMath::PerlinNoise1D(float(Time * 11.0 + 3.7)),
			FMath::PerlinNoise1D(float(Time * 12.4 + 17.1)),
			FMath::PerlinNoise1D(float(Time * 10.0 + 41.9))) * Amplitude;
	ChaseCamera->SetRelativeLocation(ChaseCameraBaseLocation + Shake);
	// Dashboard focus leans the head in; the shake stays, a little, on the way.
	CockpitCamera->SetRelativeLocation(FMath::Lerp(CockpitCameraBaseLocation, DashboardFocusEye, DashboardFocusBlend) + Shake * 0.25 * (1.f - 0.6f * DashboardFocusBlend));
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
	Load(QuantumLoopSound, CruiseLoopSoundPath);
	Load(BoostStartSound, BoostStartSoundPath);
	Load(QuantumChargeSound, CruiseChargeSoundPath);
	Load(QuantumEngageSound, CruiseEngageSoundPath);
	Load(QuantumExitSound, CruiseDropSoundPath);
	Load(TouchdownSound, TouchdownSoundPath);

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
	QuantumAudio = MakeLayer(QuantumLoopSound, TEXT("QuantumAudio"));
}

UAudioComponent* ASpaceshipPawn::PlayOneShot(USoundBase* Sound, float VolumeScale)
{
	const UWorld* World = GetWorld();
	if (!Sound || !World || !World->IsGameWorld() || !IsPlayerControlled())
	{
		return nullptr;
	}
	return UGameplayStatics::SpawnSound2D(this, Sound, OneShotVolume * VolumeScale * USpaceUserSettings::GetEffectsVolume());
}

void ASpaceshipPawn::UpdateEngineAudio(float DeltaSeconds)
{
	const bool bPiloted = IsPlayerControlled();

	// Eased rather than snapped, so the engines spool up and down instead of clicking. The load is
	// what the thrusters really do: braking and holding altitude are heard too, a steady coast
	// through empty space is quiet.
	// Coupled, the engines also drone with speed (in a quantum jump: a steady drone), so steady flight is
	// never silent.
	const float LeverLoad = QuantumState == EQuantumState::Traveling ? 0.35f
		: bFlightAssist ? 0.35f * FMath::Clamp(float(LinearVelocity.Size()) / FMath::Max(GetModeMaxSpeed(), 1.f), 0.f, 1.f) : 0.f;
	EngineLoad = FMath::FInterpTo(EngineLoad, bPiloted ? FMath::Max(EngineDemand, LeverLoad) : 0.f, DeltaSeconds, EngineSpoolRate);
	EngineBoostBlend = FMath::FInterpTo(EngineBoostBlend, bPiloted && bAfterburnerActive ? 1.f : 0.f, DeltaSeconds, EngineSpoolRate);
	HumBlend = FMath::FInterpTo(HumBlend, bPiloted ? 1.f : 0.f, DeltaSeconds, 1.5f);

	const float Effects = USpaceUserSettings::GetEffectsVolume();
	auto Drive = [Effects](UAudioComponent* Layer, float Volume, float Pitch)
	{
		Volume *= Effects;
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

	Drive(EngineHumAudio, EngineHumVolume * HumBlend * (0.85f + 0.3f * EngineLoad), 1.f + 0.04f * EngineLoad + 0.06f * QuantumBlend);

	const float Load = FMath::Min(EngineLoad + 0.35f * EngineBoostBlend, 1.f);
	Drive(EngineAudio, EngineVolume * Load,
		FMath::Lerp(EngineMinPitch, EngineMaxPitch, EngineLoad) + EngineBoostPitch * EngineBoostBlend);
	// Interpolated in log space, which is how cutoff frequencies are heard.
	EngineAudio->SetLowPassFilterFrequency(FMath::Exp(FMath::Lerp(
		FMath::Loge(EngineLowPassIdleHz), FMath::Loge(EngineLowPassFullHz), Load)));

	Drive(BoostAudio, bPiloted ? BoostVolume * AfterburnerFeel : 0.f, 1.f + 0.06f * AfterburnerFeel);
	const float QuantumSpeed = FMath::Clamp(float(LinearVelocity.Size() / (double(QuantumMaxSpeedKmS) * 100000.0)), 0.f, 1.f);
	Drive(QuantumAudio, bPiloted ? QuantumVolume * QuantumBlend : 0.f, 0.9f + 0.25f * FMath::Sqrt(QuantumSpeed));
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

	// The jump runs on a pinned, dark exposure, and at full glow the engines read as four headlights
	// instead of the soft blue of the reference (the author, 22. 9. 2026).
	const float Thrust = (ThrusterIdleGlow + (1.f - ThrusterIdleGlow) * EngineLoad + ThrusterAfterburnerGlow * AfterburnerFeel
		+ 0.3f * BoostBlend + ThrusterQuantumGlow * QuantumBlend) * FMath::Lerp(1.f, QuantumThrusterScale, QuantumBlend);
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
		SpeedTunnel->HideTunnel();
		HullSparks->UpdateSparks(DeltaSeconds, 0.f, 0.f, GetActorLocation());
		return;
	}
	// The camera manager still holds last frame's view (it updates after the pawn ticks). At 1.2 km/s
	// that is 20 m behind, which put the dust's "nothing right at the lens" fade 20 m off and let a
	// streak run through the lens as a white wedge (21. 9. 2026). The camera travels with the ship,
	// so this frame's move is added.
	const FVector View = PlayerController->PlayerCameraManager->GetCameraLocation() + LinearVelocity * DeltaSeconds;
	// The dust only as a hint of motion in normal flight, and none in a jump (the tunnel is the look
	// there); Star Citizen shows almost no speed lines outside quantum (the reference video, 21. 9. 2026).
	SpaceDust->UpdateDust(View, LinearVelocity, 1.f - QuantumBlend);
	SpeedTunnel->UpdateTunnel(View, LinearVelocity, DeltaSeconds, QuantumBlend);
	HullSparks->UpdateSparks(DeltaSeconds, float(LinearVelocity.Size()), QuantumBlend, View);

	// The jump's own light: sun down, blue glow at the nose (only the player's ship touches the sun).
	QuantumGlow->SetIntensity(QuantumGlowCandela * QuantumBlend);
	QuantumGlow->SetVisibility(QuantumBlend > 0.01f);
	// The level's fill light goes down with it: inside the tunnel there is nothing to bounce off, and
	// against the pinned exposure the ship came out white instead of a silhouette (the author, 22. 9. 2026).
	if (USkyLightComponent* Sky = QuantumSky.Get())
	{
		if (QuantumBlend > 0.001f || QuantumSkyBaseIntensity >= 0.f)
		{
			if (QuantumSkyBaseIntensity < 0.f)
			{
				QuantumSkyBaseIntensity = Sky->Intensity;
			}
			Sky->SetIntensity(QuantumSkyBaseIntensity * FMath::Lerp(1.f, QuantumSkyScale, QuantumBlend));
			if (QuantumBlend <= 0.001f)
			{
				QuantumSkyBaseIntensity = -1.f;
			}
		}
	}
	if (UDirectionalLightComponent* Sun = QuantumSun.Get())
	{
		if (QuantumBlend > 0.001f || QuantumSunBaseIntensity >= 0.f)
		{
			if (QuantumSunBaseIntensity < 0.f)
			{
				QuantumSunBaseIntensity = Sun->Intensity;
			}
			Sun->SetIntensity(QuantumSunBaseIntensity * FMath::Lerp(1.f, QuantumSunScale, QuantumBlend));
			if (QuantumBlend <= 0.001f)
			{
				// Back to the level's own value; tuning (space.Sun) works again outside jumps.
				QuantumSunBaseIntensity = -1.f;
			}
		}
	}
}

// -------------------------------------------------------------------------------------------
// Landing gear and precision mode (SC-2a)
// -------------------------------------------------------------------------------------------

bool ASpaceshipPawn::SetGearDown(bool bDown)
{
	if (!bDown && LandingState == ELandingState::Landed)
	{
		// The ship stands on it. Take off first.
		GearMessageSeconds = 3.f;
		return false;
	}
	const bool bGoingDown = GearState == EGearState::Deployed || GearState == EGearState::Extending;
	if (bDown == bGoingDown)
	{
		return true;
	}
	GearState = bDown ? EGearState::Extending : EGearState::Retracting;
	GearMessageSeconds = 0.f;
	// Star Citizen puts a ship with its gear down into landing mode; the pilot can still override it (P).
	SetPrecisionMode(bDown);
	UE_LOG(LogSpaceship, Log, TEXT("%s: gear %s"), *GetName(), bDown ? TEXT("down") : TEXT("up"));
	return true;
}

void ASpaceshipPawn::ToggleGear()
{
	const bool bGoingDown = GearState == EGearState::Deployed || GearState == EGearState::Extending;
	SetGearDown(!bGoingDown);
}

void ASpaceshipPawn::SetPrecisionMode(bool bOn)
{
	if (bOn == bPrecisionMode)
	{
		return;
	}
	bPrecisionMode = bOn;
	UE_LOG(LogSpaceship, Log, TEXT("%s: precision mode %s"), *GetName(), bOn ? TEXT("on") : TEXT("off"));
}

void ASpaceshipPawn::SetVtol(bool bOn)
{
	if (bOn == bVtolMode)
	{
		return;
	}
	// NAV is for travel: asking for VTOL there does nothing, and switching to NAV drops it (UpdateVtol).
	if (bOn && MasterMode != EMasterMode::SCM)
	{
		UE_LOG(LogSpaceship, Log, TEXT("%s: VTOL refused, SCM only"), *GetName());
		return;
	}
	// SCM only, so never in a quantum jump (NAV).
	bVtolMode = bOn;
	UE_LOG(LogSpaceship, Log, TEXT("%s: VTOL %s"), *GetName(), bOn ? TEXT("on") : TEXT("off"));
}

void ASpaceshipPawn::UpdateVtol(float DeltaSeconds)
{
	if (bVtolMode && MasterMode != EMasterMode::SCM)
	{
		bVtolMode = false;
		UE_LOG(LogSpaceship, Log, TEXT("%s: VTOL off (NAV)"), *GetName());
	}
	const float Target = bVtolMode ? 1.f : 0.f;
	const float Step = DeltaSeconds / FMath::Max(VtolTransitionSeconds, 0.01f);
	VtolBlend = FMath::Clamp(VtolBlend + FMath::Clamp(Target - VtolBlend, -Step, Step), 0.f, 1.f);
}

FRotator ASpaceshipPawn::ComputeVtolLevelStep(const FVector& WorldUp, float DeltaSeconds) const
{
	if (VtolBlend <= 0.f || VtolLevelRate <= 0.f || WorldUp.IsNearlyZero())
	{
		return FRotator::ZeroRotator;
	}
	// Where the hull's own up points, seen from the hull: level means straight up its Z.
	const FVector LocalUp = GetActorQuat().UnrotateVector(WorldUp.GetSafeNormal());
	// Negated: a nose-up hull sees the world's up leaning towards its own nose, and levelling means
	// turning the other way (checked against the measured step in test_vtol_sc2b.py).
	const double PitchError = FMath::RadiansToDegrees(FMath::Atan2(-LocalUp.X, LocalUp.Z));
	const double RollError = FMath::RadiansToDegrees(FMath::Atan2(LocalUp.Y, LocalUp.Z));
	// The whole rate only once VTOL is fully in; half way in, half the authority.
	const double Step = double(VtolLevelRate) * double(VtolBlend) * double(DeltaSeconds);
	return FRotator(FMath::Clamp(PitchError, -Step, Step), 0.0, FMath::Clamp(RollError, -Step, Step));
}

void ASpaceshipPawn::HandleVtol(const FInputActionValue& Value)
{
	ToggleVtol();
}

float ASpaceshipPawn::GetGearGroundOffsetCm() const
{
	return GearExtensionCm * GearDeploy;
}

void ASpaceshipPawn::DebugStepGear(float DeltaSeconds)
{
	UpdateGear(DeltaSeconds);
}

void ASpaceshipPawn::DebugSetGearInstant(bool bDown)
{
	if (!bDown && LandingState == ELandingState::Landed)
	{
		return;
	}
	SetPrecisionMode(bDown);
	GearState = bDown ? EGearState::Deployed : EGearState::Retracted;
	GearDeploy = bDown ? 1.f : 0.f;
	PoseGearLegs();
}

void ASpaceshipPawn::DebugSetChaseView(float YawDeg, float PitchDeg, float Zoom)
{
	if (Zoom > 0.f)
	{
		CameraZoom = CameraZoomTarget = Zoom;
	}
	if (FMath::IsNearlyZero(YawDeg) && FMath::IsNearlyZero(PitchDeg))
	{
		SetFreeLookHeld(false);
		FreeLookAngles = FreeLookTarget = FVector2D::ZeroVector;
	}
	else
	{
		SetFreeLookHeld(true);
		FreeLookAngles = FreeLookTarget = FVector2D(YawDeg, PitchDeg);
	}
	const FRotator Offset(float(FreeLookAngles.Y), float(FreeLookAngles.X), 0.f);
	CameraBoom->SetRelativeRotation(Offset);
	CockpitCamera->SetRelativeRotation(Offset);
	SnapCameraToShip();
}

void ASpaceshipPawn::DebugForceLanded(bool bLanded)
{
	if (bLanded && LandingState != ELandingState::Landed)
	{
		EnterLanded();
	}
	else if (!bLanded && LandingState == ELandingState::Landed)
	{
		ExitLanded();
	}
}

void ASpaceshipPawn::UpdateGear(float DeltaSeconds)
{
	GearMessageSeconds = FMath::Max(0.f, GearMessageSeconds - DeltaSeconds);
	const float Step = DeltaSeconds / FMath::Max(GearDeploySeconds, 0.05f);
	if (GearState == EGearState::Extending)
	{
		GearDeploy = FMath::Min(1.f, GearDeploy + Step);
		if (GearDeploy >= 1.f)
		{
			GearState = EGearState::Deployed;
			// Locks down with a small jolt, felt in the camera.
			CameraKick = FMath::Max(CameraKick, 0.15f);
		}
	}
	else if (GearState == EGearState::Retracting)
	{
		GearDeploy = FMath::Max(0.f, GearDeploy - Step);
		if (GearDeploy <= 0.f)
		{
			GearState = EGearState::Retracted;
		}
	}
	PoseGearLegs();
}

TArray<FVector> ASpaceshipPawn::ComputeGearLegPose(float Deploy, bool bNose) const
{
	// First the leg swings down from under the hull (0 .. 60 % of the travel), then the piston
	// extends to full length (40 .. 100 %): the two overlap, so it reads as one movement.
	auto Ease = [](float X) { X = FMath::Clamp(X, 0.f, 1.f); return X * X * (3.f - 2.f * X); };
	const float Swing = Ease(Deploy / 0.6f);
	const float Extend = Ease((Deploy - 0.4f) / 0.6f);

	// Pitch +90 turns straight down (-Z) into forward (+X): the nose leg folds forward, the main legs back.
	const float Pitch = (bNose ? 1.f : -1.f) * GearFoldDeg * (1.f - Swing);

	// Along the leg (pivot frame, Z up, the socket at 0, the pad's sole at -Reach). The sleeve starts
	// inside the hull so no gap shows at the root, wherever the belly is above the socket.
	const double Reach = GearExtensionCm * FMath::Lerp(0.55, 1.0, double(Extend));
	const double Inside = 40.0;
	const double SleeveLength = Inside + 0.45 * GearExtensionCm;
	const double SleeveBottom = Inside - SleeveLength;
	const double PadTop = -Reach + GearPadThicknessCm;
	const double PistonTop = SleeveBottom + 10.0;
	const double PistonLength = FMath::Max(PistonTop - PadTop, 1.0);
	const double StrutDiameter = 2.0 * GearStrutRadiusCm / 100.0;
	const double PistonDiameter = 0.65 * StrutDiameter;
	const double PadDiameter = 2.0 * GearPadRadiusCm / 100.0;

	// The engine cylinder is 100 cm across and 100 cm tall around its centre.
	return {
		FVector(Pitch, 0.0, 0.0),
		FVector(0.0, 0.0, Inside - 0.5 * SleeveLength),
		FVector(StrutDiameter, StrutDiameter, SleeveLength / 100.0),
		FVector(0.0, 0.0, PadTop + 0.5 * PistonLength),
		FVector(PistonDiameter, PistonDiameter, PistonLength / 100.0),
		FVector(0.0, 0.0, -Reach + 0.5 * GearPadThicknessCm),
		FVector(PadDiameter, PadDiameter, GearPadThicknessCm / 100.0),
	};
}

float ASpaceshipPawn::ComputeGearStowOffsetCm(float Deploy) const
{
	const float X = FMath::Clamp(Deploy, 0.f, 1.f);
	return GearStowTravelCm * (1.f - X * X * (3.f - 2.f * X));
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
	if (!bSurfaceValid || GroundGapCm < 0.f || Offset <= 1.f || DeltaSeconds <= 0.f)
	{
		return;
	}
	const FVector Up = bHasEnvironment ? FVector(Environment.Up) : GetActorUpVector();
	// Room between the pads and the ground; negative: the pads are in it.
	const double Room = double(GroundGapCm) - Offset;
	const double Vertical = LinearVelocity | Up;
	if (Room < 0.0)
	{
		// The gear came down under a ship resting on its belly: the legs push it up, about as fast as
		// they extend, instead of sinking into the ground.
		const double Lift = FMath::Min(-Room, 1.5 * GearExtensionCm / FMath::Max(GearDeploySeconds, 0.05f) * DeltaSeconds);
		AddActorWorldOffset(Up * Lift, bSweepMovement);
		GroundGapCm += float(Lift);
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
