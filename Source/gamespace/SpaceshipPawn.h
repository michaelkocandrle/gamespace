// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "CelestialBody.h"
#include "SpaceshipPawn.generated.h"

class UAudioComponent;
class UBoxComponent;
class UCameraComponent;
class UInputAction;
class UInputComponent;
class UInputMappingContext;
class UMaterialInstanceDynamic;
class USoundBase;
class USpringArmComponent;
class UStaticMeshComponent;
struct FInputActionValue;

/**
 * Which flight axis an input event feeds. Passed as a bound-delegate payload so that all four
 * one-dimensional axes can share a single handler.
 */
UENUM()
enum class ESpaceshipAxis : uint8
{
	/** +1 forward thrust, -1 reverse. */
	Thrust,
	/** +1 slide right, -1 slide left. */
	Strafe,
	/** +1 rise, -1 descend. */
	Lift,
	/** +1 roll clockwise seen from the cockpit, -1 counter-clockwise. */
	Roll
};

/** Touchdown state machine. */
UENUM(BlueprintType)
enum class ELandingState : uint8
{
	/** Normal flight physics. */
	Flying,
	/** All touchdown conditions hold; waiting out LandingConfirmSeconds. */
	Settling,
	/** Resting on the ground: aligned to the terrain, held in place, flight physics off. */
	Landed
};

/** The first reason the ship cannot touch down right now. */
UENUM(BlueprintType)
enum class ELandingBlocker : uint8
{
	None,
	/** No walkable body below within LandingProbeAltitudeM. */
	NoSurface,
	/** Hull more than LandingMaxGapCm above the ground. */
	TooHigh,
	/** Ground steeper than MaxLandingSlopeDeg. */
	TooSteep,
	/** Faster than LandingMaxSpeed. */
	TooFast,
	/** Hull tilted more than LandingMaxTiltDeg against the ground. */
	Tilted,
	/** Thrust or upward lift held at TakeoffInputThreshold or more. */
	EngineInput,
	/** Just took off; TakeoffCooldownSeconds not over. */
	TakeoffCooldown
};

/** A hull material slot whose EmissiveStrength the ship animates (thrusters, strobes). */
struct FShipGlowMaterial
{
	TWeakObjectPtr<UMaterialInstanceDynamic> Material;
	float BaseStrength = 0.f;
	float Applied = -1.f;
};

/** Cruise drive (J): a fast travel mode for crossing kilometres. */
UENUM(BlueprintType)
enum class ECruiseState : uint8
{
	Off,
	/** Charging for CruiseSpoolSeconds; normal flight goes on meanwhile. */
	Spooling,
	/** Engaged: the ship flies along its nose at up to the cruise speed limit. */
	Active,
	/** Leaving cruise: speed bleeds off to normal flight speed over CruiseDropSeconds. */
	Dropping
};

/** Why cruise cannot engage, or why it last dropped out. */
UENUM(BlueprintType)
enum class ECruiseBlocker : uint8
{
	None,
	Landed,
	/** Too close to the ground: below CruiseMinAltitudeM to engage, CruiseDropAltitudeM while cruising. */
	TooLow,
	/** The pilot switched it off. */
	Pilot,
	/** Cruise only works in NAV master mode (B). */
	NeedsNav
};

/** Star Citizen master modes: what the ship is set up for. B switches, taking MasterModeSwitchSeconds. */
UENUM(BlueprintType)
enum class EMasterMode : uint8
{
	/** Space Combat Maneuvering: combat speed, full manoeuvrability. */
	SCM,
	/** Navigation: much higher speed, reduced turning and manoeuvring thrust, cruise drive available. */
	NAV
};

/**
 * Player-flown spaceship with 6 degrees of freedom: thrust / strafe / lift plus pitch / yaw / roll,
 * flown through an IFCS modelled on Star Citizen's.
 *
 * Coupled / decoupled (V):
 * - Coupled (default): W / S / A / D / Space / Ctrl ask for a velocity while held - up to the speed
 *   limit in that direction. Let go and the flight computer brakes that axis to zero. It also holds
 *   altitude against gravity. Each thruster direction has its own acceleration (main, retro,
 *   strafe, up, down), so hard turns still slide.
 * - Decoupled: the keys fire the thrusters directly and nothing brakes: the ship keeps its velocity
 *   while it turns. Rotation stays computer-controlled in both.
 * - Spacebrake (hold X): brakes to a stop with every thruster, coupled or not.
 *
 * Speed limiter (mouse wheel): a fraction of the master mode's top speed that no key goes past.
 * Master modes (B): SCM for combat speed and full manoeuvring, NAV for travel. Cruise drive (J)
 * works only in NAV, until quantum travel replaces it.
 * G-Safe (K) keeps the pilot under GSafeMaxG and turns the nose slower at high speed; ComStab (L)
 * gives cancelling a slide priority over forward thrust and slows turning while the ship slides.
 *
 * Mouse steering is a Star Citizen virtual joystick: the mouse moves a cursor inside a circle that
 * stays where it is left; its offset from the centre (outside a small dead zone) is the turn rate.
 *
 * Boost (Shift) strengthens the manoeuvring thrusters and rotation and suspends G-Safe while its
 * energy lasts; it recharges after a pause. The afterburner (Tab, SCM only) overloads the main
 * thrusters and raises the speed limit (relative to the limiter) from its own slowly refilling
 * fuel tank. Cruise drive (J) charges for a few seconds and then flies at kilometres per second, as
 * fast as the altitude allows: the limit shrinks towards the ground, so an approach slows down by
 * itself, and cruise drops out close to the surface.
 *
 * Motion is integrated by hand rather than handed to Chaos. For a space game that keeps the feel
 * predictable and cheap to tune. Velocity lives in LinearVelocity.
 *
 * The flight model follows the nearest celestial body's environment (ACelestialBody::
 * SampleEnvironment), blended smoothly with altitude: in space nothing slows the ship (Newtonian
 * drift, SpaceLinearDamping 0); inside an atmosphere, drag (LinearDamping and QuadraticDrag, both
 * scaled by air density) and gravity grow as the ship descends. Fast flight through dense air
 * builds up entry heat, which shakes the camera.
 *
 * Landing: close above walkable ground (ACelestialBody::GetSurfaceFrame), slow, roughly level
 * with the terrain and with the engines idle, the ship settles for LandingConfirmSeconds and then
 * becomes Landed - it eases into alignment with the terrain, sits on it and stops. Thrust or
 * upward lift takes off again. While touching the ground without being landed, Coulomb friction
 * (GroundFriction) holds the ship on slopes up to about atan(GroundFriction).
 *
 * Input uses Enhanced Input. Assign the mapping context and actions on a Blueprint child, or drop
 * assets named IMC_Spaceship / IA_Thrust / ... into /Game/Input and they get picked up
 * automatically. If neither exists, the pawn builds an equivalent set procedurally at possession
 * time so it is flyable out of the box.
 */
UCLASS(Blueprintable)
class GAMESPACE_API ASpaceshipPawn : public APawn
{
	GENERATED_BODY()

public:
	ASpaceshipPawn();

	virtual void Tick(float DeltaSeconds) override;
	virtual void BeginPlay() override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual void UnPossessed() override;

	/** Current world-space velocity in cm/s. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Flight")
	FVector GetLinearVelocity() const { return LinearVelocity; }

	/** Current speed in cm/s. Feed this to a HUD readout. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Flight")
	float GetSpeed() const { return LinearVelocity.Size(); }

	/** Raw thrust input, -1 full reverse to +1 full forward. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Flight")
	float GetThrottle() const { return ThrustInput; }

	/** Coupled flight (the flight computer brakes what the keys do not ask for). */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Flight")
	bool IsFlightAssistOn() const { return bFlightAssist; }

	/** Coupled (true) or decoupled (false). V toggles it. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Flight")
	void SetFlightAssist(bool bOn);

	/** Spacebrake, held (X): brake to a stop with every thruster, coupled or decoupled. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Flight")
	void SetSpaceBrake(bool bHeld);

	UFUNCTION(BlueprintPure, Category = "Spaceship|Flight")
	bool IsSpaceBraking() const { return bSpaceBrakeHeld; }

	/** The master mode in force. While switching it is still the old one. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|IFCS")
	EMasterMode GetMasterMode() const { return MasterMode; }

	UFUNCTION(BlueprintPure, Category = "Spaceship|IFCS")
	bool IsMasterModeSwitching() const { return bMasterModeSwitching; }

	/** The mode being switched to while IsMasterModeSwitching, else the current one. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|IFCS")
	EMasterMode GetPendingMasterMode() const { return bMasterModeSwitching ? PendingMasterMode : MasterMode; }

	/** Switching progress, 0..1; 0 when not switching. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|IFCS")
	float GetMasterModeSwitchProgress() const;

	/** Starts switching to Mode (takes MasterModeSwitchSeconds). Asking for the current mode cancels a switch. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|IFCS")
	void RequestMasterMode(EMasterMode Mode);

	/** B: switch to the other master mode, or cancel a switch in progress. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|IFCS")
	void ToggleMasterMode();

	/** Speed limiter as a fraction of the master mode's top speed, SpeedLimiterMin..1. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|IFCS")
	float GetSpeedLimiter() const { return SpeedLimiterFraction; }

	UFUNCTION(BlueprintCallable, Category = "Spaceship|IFCS")
	void SetSpeedLimiter(float Fraction);

	/** Mouse wheel: +1 per notch up raises the limiter by SpeedLimiterStep. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|IFCS")
	void AdjustSpeedLimiter(float Notches);

	/** Top speed of the current master mode, cm/s (ScmMaxSpeed or NavMaxSpeed). */
	UFUNCTION(BlueprintPure, Category = "Spaceship|IFCS")
	float GetModeMaxSpeed() const;

	/** The speed no key goes past right now: mode top speed x limiter (x the afterburner's share of AfterburnerSpeedMultiplier), cm/s. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|IFCS")
	float GetSpeedLimit() const;

	UFUNCTION(BlueprintCallable, Category = "Spaceship|IFCS")
	void SetGSafe(bool bOn);

	UFUNCTION(BlueprintPure, Category = "Spaceship|IFCS")
	bool IsGSafeOn() const { return bGSafe; }

	UFUNCTION(BlueprintCallable, Category = "Spaceship|IFCS")
	void SetComStab(bool bOn);

	UFUNCTION(BlueprintPure, Category = "Spaceship|IFCS")
	bool IsComStabOn() const { return bComStab; }

	/** Acceleration the thrusters put on the pilot, in G, smoothed. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|IFCS")
	float GetGForce() const { return GForce; }

	/** Angle between the nose and the flight path, degrees; 0 when nearly stopped. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|IFCS")
	float GetSlipAngleDeg() const { return SlipAngleDeg; }

	/**
	 * G-Safe on a thruster command (local cm/s^2, X forward, Z up): vertical to GSafeMaxVerticalG,
	 * the whole vector to GSafeMaxG. With bLateralFirst (ComStab) sideways and vertical keep what
	 * they need and forward gets the rest; otherwise everything scales down together. For tests.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|IFCS")
	FVector LimitThrustForPilot(const FVector& LocalAcceleration, bool bLateralFirst) const;

	/** The virtual joystick cursor, each axis in [-1, 1] inside the unit circle (X right, Y up). */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Handling")
	FVector2D GetMouseStick() const { return MouseStick; }

	/** True when the mouse drives the Star Citizen style virtual joystick (no recentering). */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Handling")
	bool UsesVirtualJoystick() const { return !bMouseRecenter; }

	UFUNCTION(BlueprintPure, Category = "Spaceship|Handling")
	float GetVirtualJoystickDeadzone() const { return VJoyDeadzone; }

	/** How hard the thrusters work this frame, 0..1 of their force. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Flight")
	float GetEngineDemand() const { return EngineDemand; }

	UFUNCTION(BlueprintPure, Category = "Spaceship|Boost")
	bool IsBoosting() const { return bBoostActive; }

	/** Boost energy, 0..1. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Boost")
	float GetBoostEnergy() const { return BoostEnergy; }

	/** Boost ran dry and waits for BoostUnlockFraction of energy. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Boost")
	bool IsBoostLocked() const { return bBoostLocked; }

	/** G-Safe actually limiting right now: switched on (K) and not suspended by boost. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|IFCS")
	bool IsGSafeActive() const { return bGSafe && !bBoostActive; }

	/** Afterburner burning this frame (Tab held, W forward, SCM, fuel left). */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Afterburner")
	bool IsAfterburnerActive() const { return bAfterburnerActive; }

	/** Afterburner fuel, 0..1. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Afterburner")
	float GetAfterburnerFuel() const { return AfterburnerFuel; }

	/** The afterburner ran dry and waits for AfterburnerUnlockFraction of fuel. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Afterburner")
	bool IsAfterburnerLocked() const { return bAfterburnerLocked; }

	/** How much of the afterburner's raised speed limit is in force, 0..1 (spools in, fades out). */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Afterburner")
	float GetAfterburnerBlend() const { return AfterburnerBlend; }

	/** Afterburner held (Tab). Tests call it directly; the key does the same. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Afterburner")
	void SetAfterburnerHeld(bool bHeld) { bAfterburnerHeld = bHeld; }

	UFUNCTION(BlueprintPure, Category = "Spaceship|Cruise")
	ECruiseState GetCruiseState() const { return CruiseState; }

	/** Charging progress while spooling, 0..1. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Cruise")
	float GetCruiseSpoolProgress() const;

	/** Speed cruise allows at the ship's current altitude, cm/s. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Cruise")
	float GetCruiseSpeedLimit() const { return CruiseSpeedLimit; }

	/** Why cruise cannot engage right now (Off), or why it last dropped out. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Cruise")
	ECruiseBlocker GetCruiseBlocker() const { return CruiseBlocker; }

	/** Seconds a cruise refusal or drop stays worth showing. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Cruise")
	float GetCruiseMessageSeconds() const { return CruiseMessageSeconds; }

	/** J: starts charging, cancels charging, or drops out of cruise. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Cruise")
	void ToggleCruise();

	/** Cruise speed limit for these conditions, cm/s. The flight model uses exactly this; for tests. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Cruise")
	float ComputeCruiseSpeedLimit(float AltitudeAboveTerrainCm, float AtmosphereDensity, bool bNearBody) const;

	/** Chase camera distance as a multiple of the Blueprint's arm length. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Camera")
	float GetCameraZoom() const { return CameraZoom; }

	/**
	 * Tests: one flight frame of DeltaSeconds with these held inputs, through the same code as Tick
	 * (environment, throttle, boost, cruise, steering, motion). Returns the velocity afterwards.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	FVector DebugStepFlight(float DeltaSeconds, float Thrust, float Strafe, float Lift, bool bBoost);

	/**
	 * Tests: like DebugStepFlight, with LinearInput (thrust, strafe, lift) and RotationInput (roll,
	 * pitch, yaw) as held stick values in [-1, 1]. The mouse joystick is left as it is.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	FVector DebugStepFlightInput(float DeltaSeconds, const FVector& LinearInput, const FVector& RotationInput, bool bBoost);

	UFUNCTION(BlueprintPure, Category = "Spaceship|Camera")
	bool IsCockpitView() const { return bCockpitView; }

	/** Free look button held: the mouse turns the camera, not the ship. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Camera")
	bool IsFreeLooking() const { return bFreeLookHeld; }

	/** Current camera offset from straight ahead, degrees: X yaw, Y pitch. Eases back to 0 on release. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Camera")
	FVector2D GetFreeLookAngles() const { return FreeLookAngles; }

	/**
	 * Tests: runs the free look and steering code for one 1/60 s frame per entry of Frames, each
	 * (mouse X, mouse Y, button held 0/1). Returns two vectors per frame: (camera yaw, camera pitch,
	 * held) and the ship's rotation (pitch, yaw, roll).
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	TArray<FVector> DebugSimulateFreeLook(const TArray<FVector>& Frames);

	/** Conditions at the ship this frame. Valid only when HasEnvironment() is true. */
	const FCelestialEnvironment& GetEnvironment() const { return Environment; }

	UFUNCTION(BlueprintPure, Category = "Spaceship|Flight")
	bool HasEnvironment() const { return bHasEnvironment; }

	/** Entry heat, 0..1, smoothed. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Flight")
	float GetHeat() const { return Heat; }

	UFUNCTION(BlueprintPure, Category = "Spaceship|Landing")
	ELandingState GetLandingState() const { return LandingState; }

	UFUNCTION(BlueprintPure, Category = "Spaceship|Landing")
	bool IsLanded() const { return LandingState == ELandingState::Landed; }

	UFUNCTION(BlueprintPure, Category = "Spaceship|Landing")
	ELandingBlocker GetLandingBlocker() const { return LandingBlocker; }

	/** Settling progress towards Landed, 0..1. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Landing")
	float GetLandingProgress() const { return FMath::Clamp(SettleSeconds / FMath::Max(LandingConfirmSeconds, 0.01f), 0.f, 1.f); }

	/** Whether the ground below was probed this frame (low enough over a walkable body). */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Landing")
	bool HasGroundInfo() const { return bSurfaceValid; }

	/** Gap between hull and ground straight down, cm; negative when nothing is within the probe. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Landing")
	float GetGroundGapCm() const { return GroundGapCm; }

	/** Terrain slope under the ship, degrees from level. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Landing")
	float GetGroundSlopeDeg() const { return GroundSlopeDeg; }

	/** Angle between the ship's up and the terrain normal, degrees. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Landing")
	float GetGroundTiltDeg() const { return GroundTiltDeg; }

	/**
	 * The touchdown rule on its own: the first blocker for these measurements, or None. The state
	 * machine uses exactly this; exposed for tests.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Landing")
	ELandingBlocker EvaluateLanding(float GroundGap, float Speed, float TiltDeg, float SlopeDeg, bool bEngineInput) const;

	/**
	 * Velocity after one step of ground friction: the part along the surface loses up to
	 * GroundFriction x the gravity pressing the ship onto it. For tests.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Landing")
	FVector ApplyGroundFriction(const FVector& Velocity, const FVector& SurfaceNormal, const FVector& Up, float GravityCmS2, float DeltaSeconds) const;

	/** One step of the landed alignment from Current towards the terrain normal. For tests. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Landing")
	FRotator ComputeLandedRotationStep(const FRotator& Current, const FVector& SurfaceNormal, float DeltaSeconds) const;

	/**
	 * Acceleration in cm/s^2 the environment puts on a ship with this velocity: drag and gravity,
	 * without the pilot's thrust. The flight model uses exactly this; exposed for tests.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Flight")
	FVector ComputeEnvironmentAcceleration(const FCelestialEnvironment& InEnvironment, const FVector& Velocity) const;

	/** Entry heat target, 0..1, for a speed in cm/s at an atmosphere density. For tests. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Flight")
	float ComputeHeatTarget(float AtmosphereDensity, float SpeedCmS) const;

	/** Switches between the chase camera and the cockpit camera. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Camera")
	void SetCockpitView(bool bCockpit);

	/**
	 * Puts the chase camera straight back behind the ship instead of letting camera lag glide it
	 * there. Call after teleporting the ship, or the camera trails across the whole jump.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Camera")
	void SnapCameraToShip();

	// --- Getting out and back in ---------------------------------------------------------------

	/** Landed and flown by a player: F spawns the pilot and hands control to it. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Exit")
	bool CanExit() const;

	/** Spawns PilotCharacterClass at the exit and possesses it. Returns the pilot, or null. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Exit")
	APawn* ExitShip();

	/** Called by the pilot right after it possessed this ship again. */
	void OnBoarded();

	/**
	 * Where the pilot appears: the first free spot of the hull mesh's "Exit" socket (SOCKET_Exit in
	 * Blender, moved sideways until ExitClearanceCm clear of the hull's collision shapes), then
	 * beside, behind and in front of the hull at growing distances (also kept clear). Placed on the
	 * ground, upright to gravity, facing the ship's heading. "Free" is a capsule overlap test
	 * against everything that blocks pawns, including the hull's own collision hulls.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Exit")
	FTransform ComputeExitTransform() const;

	/** Candidate exit spots in the order ComputeExitTransform tries them, before ground placement. For tests. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Exit")
	TArray<FVector> GetExitCandidates() const;

	/**
	 * Gap in cm between a pilot capsule standing beside the landed ship at Location and the nearest
	 * hull collision shape at the pilot's height (negative: overlapping). Pure geometry from the
	 * hull mesh's collision, no physics query.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Exit")
	double GetHullClearance(const FVector& Location, float CapsuleRadius, float CapsuleHalfHeight) const;

	/** The hull's collision shapes as boxes in actor space (unscaled). */
	TArray<FBox> GetHullCollisionBoxes() const;

	/** Distance from Location to the hull collision box, cm; 0 inside. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Exit")
	double GetDistanceToHull(const FVector& Location) const;

	/**
	 * The fallback exit beside the hull: right of a ship with this location and rotation, far
	 * enough that a capsule of CapsuleRadius clears a box of HullExtent. For tests.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Exit")
	static FVector ComputeSideExitLocation(const FVector& ShipLocation, const FRotator& ShipRotation, const FVector& HullExtent, float CapsuleRadius, float ClearanceCm);

protected:
	// ---------------------------------------------------------------------------------------
	// Components
	// ---------------------------------------------------------------------------------------

	/**
	 * Root and the ship's collision for its own movement. Swept movement tests the root component
	 * alone, so the collision shape must be the root: with a plain scene component there, the ship
	 * flew straight through everything. Unscaled, so children do not inherit the hull scale.
	 *
	 * Ignores pawns: the box encloses the whole ship including the air under the wings, and a
	 * pilot getting out inside it was stuck or pushed through the ground. Characters collide with
	 * Hull's own collision hulls instead.
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<UBoxComponent> HullCollision;

	/**
	 * The ship mesh (a placeholder cube until an imported ship replaces it). Its simple collision
	 * (the UCX hulls from Blender) blocks pawns, cameras and visibility traces only: characters
	 * walk around the real shape, and the ship's own movement never sees it.
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<UStaticMeshComponent> Hull;

	/** Streaks of dust around the camera that show speed and direction of flight. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<class USpaceDustComponent> SpaceDust;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<USpringArmComponent> CameraBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<UCameraComponent> ChaseCamera;

	/** First-person view from the nose. Inactive until the player toggles to it. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<UCameraComponent> CockpitCamera;

	/** Engine loop. Started and stopped by UpdateEngineAudio, never auto-activated. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<UAudioComponent> EngineAudio;

	// ---------------------------------------------------------------------------------------
	// Enhanced Input
	// ---------------------------------------------------------------------------------------

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputMappingContext> FlightMappingContext;

	/** Higher priority contexts mask lower ones. Leave at 0 unless a UI context has to win. */
	UPROPERTY(EditDefaultsOnly, Category = "Spaceship|Input")
	int32 MappingContextPriority = 0;

	/** Axis1D. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> ThrustAction;

	/** Axis1D. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> StrafeAction;

	/** Axis1D. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> LiftAction;

	/** Axis1D. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> RollAction;

	/** Axis2D, stick values in [-1, 1]: X steers yaw, Y steers pitch. Gamepad right stick. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> LookAction;

	/**
	 * Axis2D, raw mouse movement in pixels. Separate from LookAction because a mouse delta and a
	 * stick deflection mean different things: movement during one frame versus a position.
	 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> MouseLookAction;

	/**
	 * Maps the mouse to MouseLookAction. Added one priority above FlightMappingContext, so it
	 * consumes the mouse there, where IA_Look still maps it.
	 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputMappingContext> MouseMappingContext;

	/** Digital, with a Pressed trigger so a held key toggles once. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> ToggleCameraAction;

	/** Digital, held. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> BoostAction;

	/** Digital, pressed: exit the ship when landed. Shared with the character (F). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> InteractAction;

	/** Unused since ASpacePlayerController binds H for every pawn; kept so Blueprints that set it still load. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> ToggleHudAction;

	/**
	 * Hide the hull mesh from the pilot in cockpit view. Right for the placeholder cube (the camera
	 * sits inside it); a real ship with a cockpit wants its canopy frame and nose in view.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera")
	bool bHideHullInCockpit = false;

	/** Digital, held: free look (right mouse button). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> FreeLookAction;

	/** Digital, pressed: flight assist on / off (V). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> FlightAssistAction;

	/** Digital, pressed: cruise drive (J). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> CruiseAction;

	/** Digital, held: spacebrake (X). The asset keeps its old name, IA_AllStop. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> AllStopAction;

	/** Axis1D: mouse wheel with Alt held. Chase camera distance, or cockpit zoom. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> CameraZoomAction;

	/** Digital, pressed: SCM / NAV (B). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> MasterModeAction;

	/** Axis1D: mouse wheel without Alt. Speed limiter. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> SpeedLimiterAction;

	/** Digital, pressed: G-Safe on / off (K). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> GSafeAction;

	/** Digital, pressed: ComStab on / off (L). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> ComStabAction;

	/** Digital, held: afterburner (Tab). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> AfterburnerAction;

	/** Maps keys the authored flight context lacks (F, V, J, X, B, K, L, right mouse button, wheel). */
	UPROPERTY(Transient)
	TObjectPtr<UInputMappingContext> InteractMappingContext;

	/** Who gets out. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Exit")
	TSubclassOf<APawn> PilotCharacterClass;

	/** Gap between the hull's collision shapes and the pilot capsule on getting out, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Exit", meta = (ClampMin = "0.0"))
	float ExitClearanceCm = 80.f;

	// ---------------------------------------------------------------------------------------
	// Flight model tuning
	// ---------------------------------------------------------------------------------------

	/** Main thrusters: forward acceleration, cm/s^2 (981 is 1 G). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Flight", meta = (ClampMin = "0.0"))
	float ThrustAcceleration = 7845.f;

	/** Retro thrusters: backward acceleration (braking from forward flight), cm/s^2. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Flight", meta = (ClampMin = "0.0"))
	float RetroAcceleration = 4900.f;

	/** Manoeuvring thrusters: sideways acceleration either way, cm/s^2. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Flight", meta = (ClampMin = "0.0"))
	float StrafeAcceleration = 4900.f;

	/** Manoeuvring thrusters: upward acceleration, cm/s^2. Also what holds the ship against gravity. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Flight", meta = (ClampMin = "0.0"))
	float LiftAcceleration = 5880.f;

	/** Manoeuvring thrusters: downward acceleration, cm/s^2. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Flight", meta = (ClampMin = "0.0"))
	float DownAcceleration = 3920.f;

	/** SCM master mode top speed, cm/s (20000 is 200 m/s). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Flight", meta = (ClampMin = "0.0"))
	float ScmMaxSpeed = 20000.f;

	/** NAV master mode top speed, cm/s (100000 is 1 km/s). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Flight", meta = (ClampMin = "0.0"))
	float NavMaxSpeed = 100000.f;

	/**
	 * Drag at sea-level air density: fraction of velocity shed per second, scaled by density.
	 * Together with QuadraticDrag the defaults give, at sea level: ~62 m/s cruise at full thrust,
	 * ~116 m/s with boost, and ~13 m/s terminal speed falling with the engines off.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Flight", meta = (ClampMin = "0.0"))
	float LinearDamping = 0.4f;

	/**
	 * Fraction of velocity shed per second outside any atmosphere. 0 is true Newtonian drift: the
	 * ship keeps flying until the pilot brakes. Raise it for an arcade-style flight assist.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Flight", meta = (ClampMin = "0.0"))
	float SpaceLinearDamping = 0.f;

	/**
	 * Drag growing with speed squared, per cm, at sea-level density. It is what brakes a fast
	 * entry: at 300 m/s in sea-level air it adds ~36 m/s^2; at 30 m/s only 0.4 m/s^2.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Flight", meta = (ClampMin = "0.0"))
	float QuadraticDrag = 4.0e-5f;

	/** Scales the gravity of the environment. 0 switches gravity off for this ship. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Flight", meta = (ClampMin = "0.0"))
	float GravityScale = 1.f;

	/** Sweep the hull along the movement path instead of tunnelling through geometry. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Flight")
	bool bSweepMovement = true;

	/**
	 * Boost (hold Shift): the manoeuvring thrusters - retro, strafe, up and down - are multiplied by
	 * this. Main thrust and the speed limit are not (that is the afterburner).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Boost", meta = (ClampMin = "1.0"))
	float BoostManeuverMultiplier = 1.6f;

	/** Boost: turn rates and rotational accelerations are multiplied by this. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Boost", meta = (ClampMin = "1.0"))
	float BoostRotationMultiplier = 1.4f;

	/**
	 * How quickly speed above the current cap bleeds off (afterburner fading out, NAV back to SCM),
	 * as a fraction of the excess per second. Avoids a hard velocity snap.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Boost", meta = (ClampMin = "0.0"))
	float OverspeedDecay = 1.5f;

	/** Seconds of boost a full charge lasts. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Boost", meta = (ClampMin = "0.1", Units = "s"))
	float BoostDurationSeconds = 4.5f;

	/** Seconds from empty to full once recharging. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Boost", meta = (ClampMin = "0.1", Units = "s"))
	float BoostRechargeSeconds = 7.f;

	/** Recharging starts this long after boost was last used. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Boost", meta = (ClampMin = "0.0", Units = "s"))
	float BoostRechargeDelaySeconds = 1.f;

	/** After running dry, boost works again once this much energy is back. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Boost", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float BoostUnlockFraction = 0.3f;

	// ---------------------------------------------------------------------------------------
	// Afterburner (hold Tab, SCM only)
	// ---------------------------------------------------------------------------------------

	/** Afterburner: main (forward) thrust is multiplied by this. G-Safe still applies. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Afterburner", meta = (ClampMin = "1.0"))
	float AfterburnerThrustMultiplier = 1.8f;

	/**
	 * Afterburner: the speed limit becomes SCM top speed x this x the speed limiter. Relative to the
	 * limiter, as in Star Citizen: at a 50 % limiter the afterburner reaches 50 % of its full top speed.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Afterburner", meta = (ClampMin = "1.0"))
	float AfterburnerSpeedMultiplier = 2.f;

	/** Seconds of burn a full afterburner tank lasts. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Afterburner", meta = (ClampMin = "0.1", Units = "s"))
	float AfterburnerDurationSeconds = 8.f;

	/** Seconds from an empty to a full tank once refilling; slow on purpose. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Afterburner", meta = (ClampMin = "0.1", Units = "s"))
	float AfterburnerRefillSeconds = 40.f;

	/** Refilling starts this long after the afterburner was last used. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Afterburner", meta = (ClampMin = "0.0", Units = "s"))
	float AfterburnerRefillDelaySeconds = 2.f;

	/** After running dry, the afterburner lights again once this much fuel is back. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Afterburner", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float AfterburnerUnlockFraction = 0.15f;

	/** Seconds for the raised speed limit to come in fully. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Afterburner", meta = (ClampMin = "0.01", Units = "s"))
	float AfterburnerSpoolSeconds = 0.4f;

	/**
	 * Seconds for the raised speed limit to fade back to normal when the afterburner stops (released
	 * or out of fuel), so the ship slows down smoothly instead of braking at full retro.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Afterburner", meta = (ClampMin = "0.01", Units = "s"))
	float AfterburnerFadeSeconds = 4.f;

	// ---------------------------------------------------------------------------------------
	// IFCS: coupled flight, master modes, speed limiter, G-Safe, ComStab
	// ---------------------------------------------------------------------------------------

	/** Coupled flight (see the class comment). V toggles it in game. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|IFCS")
	bool bFlightAssist = true;

	/** How hard the coupled flight computer chases the target velocity, per second of error. Higher is snappier. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|IFCS", meta = (ClampMin = "0.1"))
	float FlightAssistResponse = 3.f;

	/** Seconds a master mode switch (B) takes. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|IFCS", meta = (ClampMin = "0.0", Units = "s"))
	float MasterModeSwitchSeconds = 2.f;

	/** NAV: turn rates as a fraction of the SCM ones. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|IFCS", meta = (ClampMin = "0.05", ClampMax = "1.0"))
	float NavTurnScale = 0.5f;

	/** NAV: strafe, up and down thrust as a fraction of the SCM ones (main and retro stay). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|IFCS", meta = (ClampMin = "0.05", ClampMax = "1.0"))
	float NavManeuverScale = 0.5f;

	/** Speed limiter change per mouse wheel notch, fraction of the mode's top speed. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|IFCS", meta = (ClampMin = "0.01", ClampMax = "0.5"))
	float SpeedLimiterStep = 0.05f;

	/** Lowest speed limiter setting. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|IFCS", meta = (ClampMin = "0.01", ClampMax = "1.0"))
	float SpeedLimiterMin = 0.05f;

	/** G-Safe (K): keep the pilot's G load down. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|IFCS")
	bool bGSafe = true;

	/** G-Safe: most total thruster acceleration on the pilot, G. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|IFCS", meta = (ClampMin = "0.5"))
	float GSafeMaxG = 7.f;

	/** G-Safe: most acceleration along the pilot's spine (up / down), G. The body takes least that way. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|IFCS", meta = (ClampMin = "0.5"))
	float GSafeMaxVerticalG = 5.f;

	/**
	 * G-Safe, coupled: pitch and yaw rates are limited so that bending the flight path at the
	 * current speed would take at most this many G. Fast ships turn wider.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|IFCS", meta = (ClampMin = "0.5"))
	float GSafeTurnG = 14.f;

	/** G-Safe never slows turning below this fraction of the full rates. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|IFCS", meta = (ClampMin = "0.05", ClampMax = "1.0"))
	float GSafeMinTurnFraction = 0.3f;

	/** ComStab (L): fight the slide in turns. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|IFCS")
	bool bComStab = true;

	/** ComStab, coupled: turning starts to slow once nose and flight path are this far apart. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|IFCS", meta = (ClampMin = "0.0", ClampMax = "90.0"))
	float ComStabSlipStartDeg = 8.f;

	/** ComStab: at this slip angle turning is down to ComStabMinTurnFraction. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|IFCS", meta = (ClampMin = "1.0", ClampMax = "180.0"))
	float ComStabSlipFullDeg = 30.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|IFCS", meta = (ClampMin = "0.05", ClampMax = "1.0"))
	float ComStabMinTurnFraction = 0.35f;

	/** Below this speed there is no meaningful flight path, so no slip, cm/s. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|IFCS", meta = (ClampMin = "0.0"))
	float ComStabMinSpeed = 1500.f;

	/**
	 * Highest descent speed commanded near the ground, cm/s. The limit rises to the speed limit by
	 * 20 m above the terrain, so holding Ctrl lowers the ship onto the ground instead of into it.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|IFCS", meta = (ClampMin = "10.0"))
	float LandingDescentSpeed = 250.f;

	/**
	 * With no thrust or lift held and a hull gap under ~4 m, the flight computer holds only this much
	 * less than gravity, so a hovering ship settles gently onto the ground by itself.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|IFCS", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float LandingSettleGravityFraction = 0.25f;

	// ---------------------------------------------------------------------------------------
	// Cruise drive
	// ---------------------------------------------------------------------------------------

	/** Charging time before cruise engages. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Cruise", meta = (ClampMin = "0.0", Units = "s"))
	float CruiseSpoolSeconds = 2.5f;

	/** Cruise speed limit per cm of altitude above the terrain, 1/s: approaching a surface, the altitude shrinks by this fraction every second. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Cruise", meta = (ClampMin = "0.01"))
	float CruiseAltitudeRate = 0.4f;

	/** Cruise never drops below this speed limit, cm/s (250 m/s). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Cruise", meta = (ClampMin = "0.0"))
	float CruiseMinSpeed = 25000.f;

	/**
	 * Top cruise speed, cm/s (6 km/s), also far from any body. Faster flight means more world
	 * origin rebases per second, each a frame of work.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Cruise", meta = (ClampMin = "0.0"))
	float CruiseMaxSpeed = 600000.f;

	/** Thicker air lowers the limit: at full density it is (1 - this) of the altitude limit. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Cruise", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float CruiseAtmosphereSlowdown = 0.85f;

	/** Cruise engages only this high above the terrain. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Cruise", meta = (ClampMin = "0.0", Units = "m"))
	float CruiseMinAltitudeM = 2000.f;

	/** Below this, cruise drops out on its own. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Cruise", meta = (ClampMin = "0.0", Units = "m"))
	float CruiseDropAltitudeM = 1200.f;

	/** How fast the velocity swings onto the nose and the target speed in cruise, per second. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Cruise", meta = (ClampMin = "0.1"))
	float CruiseResponse = 1.2f;

	/** Turn rates in cruise, as a fraction of the normal ones. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Cruise", meta = (ClampMin = "0.05", ClampMax = "1.0"))
	float CruiseTurnScale = 0.45f;

	/** Length of the drop out of cruise, while speed bleeds off. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Cruise", meta = (ClampMin = "0.1", Units = "s"))
	float CruiseDropSeconds = 1.5f;

	/** Maximum pitch rate, deg/s. The hard ceiling on turning, however fast the mouse moves. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling", meta = (ClampMin = "0.0"))
	float PitchRate = 100.f;

	/** Maximum yaw rate, deg/s. Lower than pitch, as on a real aircraft. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling", meta = (ClampMin = "0.0"))
	float YawRate = 75.f;

	/** Maximum roll rate, deg/s. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling", meta = (ClampMin = "0.0"))
	float RollRate = 150.f;

	/** How fast the ship converges on the commanded rotation rate. Lower feels heavier. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling", meta = (ClampMin = "0.1"))
	float AngularResponsiveness = 8.f;

	/** Rotational inertia: the most the pitch rate changes per second, deg/s^2. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling", meta = (ClampMin = "1.0"))
	float PitchAcceleration = 300.f;

	/** The most the yaw rate changes per second, deg/s^2. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling", meta = (ClampMin = "1.0"))
	float YawAcceleration = 220.f;

	/** The most the roll rate changes per second, deg/s^2. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling", meta = (ClampMin = "1.0"))
	float RollAcceleration = 500.f;

	/**
	 * Mouse steering. Off (default): Star Citizen virtual joystick - the mouse moves a cursor in a
	 * circle that stays where it is left. On: the older spring-centred stick that returns to the
	 * middle at MouseRecenterRate once the mouse stops.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling")
	bool bMouseRecenter = false;

	/** Virtual joystick: mouse counts from the centre to the edge of the circle (full turn rate). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling", meta = (ClampMin = "10.0"))
	float VJoyCountsToFull = 300.f;

	/** Virtual joystick: inner part of the circle that turns nothing, fraction of the radius. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling", meta = (ClampMin = "0.0", ClampMax = "0.5"))
	float VJoyDeadzone = 0.06f;

	/**
	 * Spring-centred stick only (bMouseRecenter): stick deflection per pixel. Moving the mouse
	 * steadily at MouseRecenterRate / MouseSensitivity pixels per second holds the stick fully over.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling", meta = (ClampMin = "0.0"))
	float MouseSensitivity = 0.09f;

	/** Spring-centred stick only: how quickly it returns to centre once the mouse stops, per second. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling", meta = (ClampMin = "0.1"))
	float MouseRecenterRate = 12.f;

	/** Flip the pitch axis for players who fly stick-style. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling")
	bool bInvertPitch = false;

	// ---------------------------------------------------------------------------------------
	// Free look (hold right mouse button)
	// ---------------------------------------------------------------------------------------

	/**
	 * Camera degrees per mouse count while free looking. Steering maps a count to 0.09 of full
	 * stick; this is 4x that number, but in degrees, so a flick turns the head well past what the
	 * same flick would turn the ship.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Free Look", meta = (ClampMin = "0.0"))
	float FreeLookSensitivity = 0.36f;

	/**
	 * How far the camera can turn left / right from straight ahead. 180 means all the way round:
	 * the chase camera orbits the ship, and on release it swings back the shorter way.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Free Look", meta = (ClampMin = "0.0", ClampMax = "180.0"))
	float FreeLookMaxYawDeg = 180.f;

	/** How far the camera can turn up / down from straight ahead. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Free Look", meta = (ClampMin = "0.0", ClampMax = "89.0"))
	float FreeLookMaxPitchDeg = 85.f;

	/** How fast the camera follows the mouse while held, per second; smooths raw mouse steps. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Free Look", meta = (ClampMin = "0.1"))
	float FreeLookFollowRate = 20.f;

	/** How fast the camera swings back after release, per second (6: ~95 % in half a second). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Free Look", meta = (ClampMin = "0.1"))
	float FreeLookReturnRate = 6.f;

	// ---------------------------------------------------------------------------------------
	// Camera feel
	// ---------------------------------------------------------------------------------------

	/** Closest chase camera, as a multiple of the arm length set on the Blueprint. Mouse wheel. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.1"))
	float CameraZoomMin = 0.45f;

	/** Farthest chase camera, as a multiple of the Blueprint's arm length. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.1"))
	float CameraZoomMax = 3.f;

	/** Zoom change per wheel notch, as a fraction of the current distance. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.01", ClampMax = "0.5"))
	float CameraZoomStep = 0.12f;

	/** Cockpit field of view fully zoomed in with the wheel, degrees. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "10.0", ClampMax = "120.0"))
	float CockpitZoomFov = 40.f;

	/** Degrees added to the field of view at full afterburner... */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.0"))
	float AfterburnerFovKick = 7.f;

	/** ...and in cruise. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.0"))
	float CruiseFovKick = 16.f;

	/** Camera shake while boosting, cm (cockpit a quarter). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.0"))
	float BoostShakeCm = 1.f;

	/** Camera shake at full afterburner, cm (cockpit a quarter). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.0"))
	float AfterburnerShakeCm = 3.f;

	/** Camera shake at the end of cruise charging, cm; a little stays while cruising. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.0"))
	float CruiseShakeCm = 6.f;

	/** Short jolt when boost or the afterburner starts, cruise engages or drops out, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.0"))
	float KickShakeCm = 9.f;

	// ---------------------------------------------------------------------------------------
	// Ship lights
	// ---------------------------------------------------------------------------------------

	/** Thruster glow at idle, as a fraction of the material's own EmissiveStrength. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Lights", meta = (ClampMin = "0.0"))
	float ThrusterIdleGlow = 0.3f;

	/** Glow added at full afterburner, same units... */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Lights", meta = (ClampMin = "0.0"))
	float ThrusterAfterburnerGlow = 2.f;

	/** ...and in cruise. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Lights", meta = (ClampMin = "0.0"))
	float ThrusterCruiseGlow = 3.f;

	/** Seconds between double flashes of the white navigation strobes. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Lights", meta = (ClampMin = "0.2", Units = "s"))
	float NavStrobePeriodSeconds = 1.4f;

	// ---------------------------------------------------------------------------------------
	// Atmospheric entry
	// ---------------------------------------------------------------------------------------

	/**
	 * Speed that heat is measured against, cm/s. Heating is density x (speed / this)^3. The SCM top
	 * speed (200 m/s): flying at SCM speed stays cool, boost and NAV speeds in thick air heat up.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Entry", meta = (ClampMin = "1.0"))
	float HeatReferenceSpeed = 20000.f;

	/** Heating where heat starts to show... */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Entry", meta = (ClampMin = "0.0"))
	float HeatOnset = 0.5f;

	/** ...and where it is full. Defaults: none cruising low, strong in a 300 m/s dive below ~8 km. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Entry", meta = (ClampMin = "0.0"))
	float HeatFull = 3.0f;

	/** How fast heat follows its target, per second. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Entry", meta = (ClampMin = "0.1"))
	float HeatResponse = 2.f;

	/** Camera shake at full heat, cm. The cockpit camera gets a quarter of it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Entry", meta = (ClampMin = "0.0"))
	float HeatShakeCm = 14.f;

	// ---------------------------------------------------------------------------------------
	// Landing
	// ---------------------------------------------------------------------------------------

	/** Below this height above the terrain the ground is probed every frame. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Landing", meta = (ClampMin = "1.0", Units = "m"))
	float LandingProbeAltitudeM = 30.f;

	/** Touchdown only when the hull is at most this far above the ground. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Landing", meta = (ClampMin = "0.0"))
	float LandingMaxGapCm = 60.f;

	/** Touchdown only below this speed, cm/s. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Landing", meta = (ClampMin = "0.0"))
	float LandingMaxSpeed = 300.f;

	/** Touchdown only with the hull tilted at most this much against the terrain. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Landing", meta = (ClampMin = "0.0", ClampMax = "90.0"))
	float LandingMaxTiltDeg = 30.f;

	/**
	 * Steeper ground refuses touchdown: the ship keeps sliding and has to find a flatter spot.
	 * Keep it at or below atan(GroundFriction), where friction can still hold the ship.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Landing", meta = (ClampMin = "0.0", ClampMax = "60.0"))
	float MaxLandingSlopeDeg = 25.f;

	/** Conditions must hold this long without a break before the ship counts as landed. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Landing", meta = (ClampMin = "0.0", Units = "s"))
	float LandingConfirmSeconds = 0.75f;

	/** How fast a landed ship eases into alignment and onto the ground, per second (6: ~95 % in 0.5 s). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Landing", meta = (ClampMin = "0.1"))
	float LandingAlignRate = 6.f;

	/** How fast leftover sliding stops once landed, per second. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Landing", meta = (ClampMin = "0.1"))
	float LandedBrakeRate = 6.f;

	/**
	 * Friction coefficient while touching the ground (not yet landed). 0.5 holds the ship still
	 * on slopes up to ~26.5 degrees; steeper, it slides.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Landing", meta = (ClampMin = "0.0"))
	float GroundFriction = 0.5f;

	/** Hull within this distance of the ground counts as touching it, for friction. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Landing", meta = (ClampMin = "0.0"))
	float GroundContactToleranceCm = 10.f;

	/** Radius over which the terrain slope under the ship is averaged. About half the hull length. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Landing", meta = (ClampMin = "10.0"))
	float LandingFootprintRadiusCm = 150.f;

	/** Thrust (either way) or upward lift at this input or more takes off, and blocks touchdown. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Landing", meta = (ClampMin = "0.05", ClampMax = "1.0"))
	float TakeoffInputThreshold = 0.5f;

	/** No new touchdown for this long after taking off, so a tap on Space really lifts off. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Landing", meta = (ClampMin = "0.0", Units = "s"))
	float TakeoffCooldownSeconds = 0.75f;

	// ---------------------------------------------------------------------------------------
	// Engine audio
	// ---------------------------------------------------------------------------------------

	/** Looping engine sound. Loaded from /Game/Ships/Audio/SW_EngineLoop when left empty. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Audio")
	TObjectPtr<USoundBase> EngineLoopSound;

	/** Volume at full engine load. Kept moderate: the engine plays for the whole flight. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Audio", meta = (ClampMin = "0.0"))
	float EngineVolume = 0.55f;

	/**
	 * Pitch just above idle, as the engine starts to push. The pitch range is deliberately
	 * narrow: playing the loop faster moves all of it up, and at 1.55x the old range pushed the
	 * rumble into the band where it sounded like a vacuum cleaner.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Audio", meta = (ClampMin = "0.1"))
	float EngineMinPitch = 0.8f;

	/** Pitch at full thrust without boost. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Audio", meta = (ClampMin = "0.1"))
	float EngineMaxPitch = 1.05f;

	/** Pitch added on top while the afterburner burns. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Audio", meta = (ClampMin = "0.0"))
	float EngineBoostPitch = 0.15f;

	/** Low-pass cutoff at the lightest engine load, Hz: a muffled, distant rumble. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Audio", meta = (ClampMin = "20.0"))
	float EngineLowPassIdleHz = 400.f;

	/** Low-pass cutoff at full load or afterburner, Hz. The loop has almost nothing above 1 kHz anyway. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Audio", meta = (ClampMin = "20.0"))
	float EngineLowPassFullHz = 2000.f;

	/** How fast engine volume and pitch follow the controls, per second. Lower spools slower. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Audio", meta = (ClampMin = "0.1"))
	float EngineSpoolRate = 5.f;

	/** Reactor hum while piloted. /Game/Ships/Audio/SW_EngineHum when empty. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Audio")
	TObjectPtr<USoundBase> EngineHumSound;

	/** Roar layer while the afterburner burns. /Game/Ships/Audio/SW_BoostLoop when empty. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Audio")
	TObjectPtr<USoundBase> BoostLoopSound;

	/** Cruise drive drone. /Game/Ships/Audio/SW_CruiseLoop when empty. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Audio")
	TObjectPtr<USoundBase> CruiseLoopSound;

	/** One-shots: boost ignition, cruise charging, cruise engaging, cruise dropping out. /Game/Ships/Audio/SW_* when empty. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Audio")
	TObjectPtr<USoundBase> BoostStartSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Audio")
	TObjectPtr<USoundBase> CruiseChargeSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Audio")
	TObjectPtr<USoundBase> CruiseEngageSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Audio")
	TObjectPtr<USoundBase> CruiseDropSound;

	/** Gear touching down when the ship becomes Landed. /Game/Ships/Audio/SW_Touchdown when empty. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Audio")
	TObjectPtr<USoundBase> TouchdownSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Audio", meta = (ClampMin = "0.0"))
	float EngineHumVolume = 0.4f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Audio", meta = (ClampMin = "0.0"))
	float BoostVolume = 0.6f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Audio", meta = (ClampMin = "0.0"))
	float CruiseVolume = 0.55f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Audio", meta = (ClampMin = "0.0"))
	float OneShotVolume = 0.8f;

	// ---------------------------------------------------------------------------------------
	// Runtime state
	// ---------------------------------------------------------------------------------------

	/** World-space velocity, cm/s. */
	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Spaceship|Flight")
	FVector LinearVelocity = FVector::ZeroVector;

	/** Local-space rotation rate in deg/s: X roll, Y pitch, Z yaw. */
	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Spaceship|Handling")
	FVector AngularVelocity = FVector::ZeroVector;

private:
	void HandleAxisTriggered(const FInputActionValue& Value, ESpaceshipAxis Axis);
	void HandleAxisCompleted(const FInputActionValue& Value, ESpaceshipAxis Axis);
	void HandleLook(const FInputActionValue& Value);
	void HandleMouseLook(const FInputActionValue& Value);
	void HandleToggleCamera(const FInputActionValue& Value);
	void HandleBoost(const FInputActionValue& Value);
	void HandleBoostCompleted(const FInputActionValue& Value);
	void HandleInteract(const FInputActionValue& Value);
	void HandleToggleHud(const FInputActionValue& Value);
	void HandleFreeLookStarted(const FInputActionValue& Value);
	void HandleFreeLookCompleted(const FInputActionValue& Value);
	void HandleFlightAssist(const FInputActionValue& Value);
	void HandleCruise(const FInputActionValue& Value);
	void HandleAllStop(const FInputActionValue& Value);
	void HandleAllStopCompleted(const FInputActionValue& Value);
	void HandleCameraZoom(const FInputActionValue& Value);
	void HandleMasterMode(const FInputActionValue& Value);
	void HandleSpeedLimiter(const FInputActionValue& Value);
	void HandleGSafe(const FInputActionValue& Value);
	void HandleComStab(const FInputActionValue& Value);
	void HandleAfterburner(const FInputActionValue& Value);
	void HandleAfterburnerCompleted(const FInputActionValue& Value);
	void UpdateAfterburner(float DeltaSeconds);
	/** Alt held on the controlling player's keyboard: the wheel zooms instead of setting the limiter. */
	bool IsAltHeld() const;
	void SetFreeLookHeld(bool bHeld);
	void UpdateFreeLook(float DeltaSeconds);
	void ClearPilotInput();

	void UpdateMasterMode(float DeltaSeconds);
	void UpdateBoost(float DeltaSeconds);
	void UpdateCruise(float DeltaSeconds);
	ECruiseBlocker EvaluateCruiseEngage() const;
	void BeginCruiseDrop(ECruiseBlocker Reason);
	/** Everything a flight frame does before the camera and sound: shared by Tick and DebugStepFlight. */
	void StepFlight(float DeltaSeconds);
	void UpdateCameraEffects(float DeltaSeconds);
	void UpdateSpaceDust(float DeltaSeconds);
	void SetupShipLights();
	void UpdateShipLights(float DeltaSeconds);
	void SetupAudioLayers();
	UAudioComponent* PlayOneShot(USoundBase* Sound, float VolumeScale = 1.f);
	bool IsExitSpotFree(const FVector& Location, const FVector& Up, float CapsuleRadius, float CapsuleHalfHeight) const;
	/** Start moved along Direction (flattened onto the ship's floor plane) until GetHullClearance reaches ExitClearanceCm. */
	FVector PushClearOfHull(const FVector& Start, const FVector& Direction, float CapsuleRadius, float CapsuleHalfHeight) const;

	/** Fills in any unassigned input asset: first from /Game/Input, then procedurally. */
	void ResolveInputAssets();
	void BuildProceduralInputAssets();

	void UpdateAngularMotion(float DeltaSeconds);
	void UpdateLinearMotion(float DeltaSeconds);
	void UpdateEngineAudio(float DeltaSeconds);
	void UpdateEnvironment(float DeltaSeconds);
	void UpdateLanding(float DeltaSeconds);
	void UpdateLandedMotion(float DeltaSeconds);
	void EnterLanded();
	void ExitLanded();
	/** Sweeps the hull from Start to End with Rotation, ignoring this ship. */
	bool SweepHull(const FVector& Start, const FVector& End, const FQuat& Rotation, FHitResult& OutHit) const;

	float& AxisInput(ESpaceshipAxis Axis);

	float ThrustInput = 0.f;
	float StrafeInput = 0.f;
	float LiftInput = 0.f;
	float RollInput = 0.f;

	/** Stick look, X yaw, Y pitch. Cleared every tick; a deflected stick re-fires Triggered. */
	FVector2D LookInput = FVector2D::ZeroVector;

	/** Mouse movement in pixels since the last tick. */
	FVector2D MouseLookDelta = FVector2D::ZeroVector;

	/** The mouse virtual joystick, inside the unit circle. */
	FVector2D MouseStick = FVector2D::ZeroVector;

	bool bFreeLookHeld = false;
	/** Where the mouse has pushed the view (X yaw, Y pitch), clamped; 0 when released. */
	FVector2D FreeLookTarget = FVector2D::ZeroVector;
	/** What the cameras show, easing towards FreeLookTarget. */
	FVector2D FreeLookAngles = FVector2D::ZeroVector;

	/** Smoothed engine load and boost blend, each in [0, 1], driving the engine sound. */
	float EngineLoad = 0.f;
	float EngineBoostBlend = 0.f;
	float HumBlend = 0.f;

	bool bBoostHeld = false;
	bool bBoostActive = false;
	bool bBoostLocked = false;
	float BoostEnergy = 1.f;
	float BoostRechargeWait = 0.f;

	bool bAfterburnerHeld = false;
	bool bAfterburnerActive = false;
	bool bAfterburnerLocked = false;
	float AfterburnerFuel = 1.f;
	float AfterburnerRefillWait = 0.f;
	float AfterburnerBlend = 0.f;

	float EngineDemand = 0.f;

	bool bSpaceBrakeHeld = false;
	EMasterMode MasterMode = EMasterMode::SCM;
	EMasterMode PendingMasterMode = EMasterMode::SCM;
	bool bMasterModeSwitching = false;
	float MasterModeTimer = 0.f;
	float SpeedLimiterFraction = 1.f;
	float GForce = 0.f;
	float SlipAngleDeg = 0.f;

	ECruiseState CruiseState = ECruiseState::Off;
	ECruiseBlocker CruiseBlocker = ECruiseBlocker::None;
	float CruiseTimer = 0.f;
	float CruiseSpeedLimit = 0.f;
	float CruiseMessageSeconds = 0.f;

	/** Eased 0..1 blends driving camera, lights and sound. */
	float BoostBlend = 0.f;
	float AfterburnerFeel = 0.f;
	float CruiseBlend = 0.f;
	float CameraKick = 0.f;

	float CameraZoom = 1.f;
	float CameraZoomTarget = 1.f;
	/** Cockpit zoom, 0 normal field of view .. 1 CockpitZoomFov. */
	float CockpitZoom = 0.f;
	float CockpitZoomTarget = 0.f;
	float BaseArmLength = 0.f;
	FVector BaseSocketOffset = FVector::ZeroVector;
	float BaseChaseFov = 90.f;
	float BaseCockpitFov = 90.f;

	TArray<FShipGlowMaterial> ThrusterMaterials;
	TArray<FShipGlowMaterial> StrobeMaterials;

	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> EngineHumAudio;
	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> BoostAudio;
	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> CruiseAudio;
	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> CruiseChargeAudio;

	bool bCockpitView = false;

	FCelestialEnvironment Environment;
	bool bHasEnvironment = false;
	TWeakObjectPtr<ACelestialBody> NearestBody;

	ELandingState LandingState = ELandingState::Flying;
	ELandingBlocker LandingBlocker = ELandingBlocker::NoSurface;
	float SettleSeconds = 0.f;
	float TakeoffCooldown = 0.f;
	bool bSurfaceValid = false;
	bool bGroundContact = false;
	float GroundGapCm = -1.f;
	float GroundSlopeDeg = 0.f;
	float GroundTiltDeg = 0.f;
	FVector GroundNormal = FVector::UpVector;
	float Heat = 0.f;
	FVector ChaseCameraBaseLocation = FVector::ZeroVector;
	FVector CockpitCameraBaseLocation = FVector::ZeroVector;

	/** Ticks left with camera lag switched off after SnapCameraToShip. */
	int32 CameraSnapTicks = 0;
};
