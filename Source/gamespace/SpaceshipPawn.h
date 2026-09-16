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

/**
 * Player-flown spaceship with 6 degrees of freedom: thrust / strafe / lift plus pitch / yaw / roll.
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

	UFUNCTION(BlueprintPure, Category = "Spaceship|Boost")
	bool IsBoosting() const { return bBoostHeld; }

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
	 * Where the pilot appears: the hull mesh's "Exit" socket (SOCKET_Exit in Blender) if it has
	 * one, otherwise beside the ship on its right. Placed on the ground, upright to gravity, facing
	 * the ship's heading.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Exit")
	FTransform ComputeExitTransform() const;

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
	 * Root and the only collision of the ship. Swept movement tests the root component alone, so
	 * the collision shape must be the root: with a plain scene component there, the ship flew
	 * straight through everything. Unscaled, so children do not inherit the hull scale.
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<UBoxComponent> HullCollision;

	/** Placeholder cube standing in for the real ship mesh. Visual only, no collision. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<UStaticMeshComponent> Hull;

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

	/** Digital, pressed: cycle the debug HUD (H). */
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

	/** Maps F / right mouse button when the authored flight context lacks them. */
	UPROPERTY(Transient)
	TObjectPtr<UInputMappingContext> InteractMappingContext;

	/** Who gets out. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Exit")
	TSubclassOf<APawn> PilotCharacterClass;

	/** Gap between hull and pilot capsule for the side exit, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Exit", meta = (ClampMin = "0.0"))
	float ExitClearanceCm = 80.f;

	// ---------------------------------------------------------------------------------------
	// Flight model tuning
	// ---------------------------------------------------------------------------------------

	/** Forward and reverse acceleration, cm/s^2. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Flight", meta = (ClampMin = "0.0"))
	float ThrustAcceleration = 4000.f;

	/** Lateral acceleration, cm/s^2. Deliberately weaker than main thrust. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Flight", meta = (ClampMin = "0.0"))
	float StrafeAcceleration = 1800.f;

	/** Vertical acceleration, cm/s^2. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Flight", meta = (ClampMin = "0.0"))
	float LiftAcceleration = 1800.f;

	/** Hard speed cap in cm/s. 12000 cm/s is 120 m/s. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Flight", meta = (ClampMin = "0.0"))
	float MaxSpeed = 12000.f;

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
	 * While boost is held, forward thrust acceleration and MaxSpeed are multiplied by this.
	 * With flight assist on, cruise speed settles at ThrustAcceleration / LinearDamping, so the
	 * multiplier scales cruise speed directly: 2.5 takes the defaults from ~33 to ~83 m/s.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Boost", meta = (ClampMin = "1.0"))
	float BoostMultiplier = 2.5f;

	/**
	 * How quickly speed above the current cap bleeds off once boost is released, as a fraction
	 * of the excess per second. Avoids a hard velocity snap at the moment Shift comes up.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Boost", meta = (ClampMin = "0.0"))
	float OverspeedDecay = 1.5f;

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

	/**
	 * Mouse steering is a virtual joystick: moving the mouse pushes the stick, and the stick
	 * springs back to centre at MouseRecenterRate. This value is stick deflection per pixel.
	 *
	 * Moving the mouse steadily at MouseRecenterRate / MouseSensitivity pixels per second holds
	 * the stick fully over, i.e. turns at PitchRate / YawRate. The defaults reach full rate at
	 * roughly 130 px/s, independent of frame rate.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling", meta = (ClampMin = "0.0"))
	float MouseSensitivity = 0.09f;

	/** How quickly the virtual stick returns to centre once the mouse stops, per second. */
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

	/** How far the camera can turn left / right from straight ahead. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Free Look", meta = (ClampMin = "0.0", ClampMax = "179.0"))
	float FreeLookMaxYawDeg = 110.f;

	/** How far the camera can turn up / down from straight ahead. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Free Look", meta = (ClampMin = "0.0", ClampMax = "89.0"))
	float FreeLookMaxPitchDeg = 70.f;

	/** How fast the camera follows the mouse while held, per second; smooths raw mouse steps. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Free Look", meta = (ClampMin = "0.1"))
	float FreeLookFollowRate = 20.f;

	/** How fast the camera swings back after release, per second (6: ~95 % in half a second). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Free Look", meta = (ClampMin = "0.1"))
	float FreeLookReturnRate = 6.f;

	// ---------------------------------------------------------------------------------------
	// Atmospheric entry
	// ---------------------------------------------------------------------------------------

	/** Speed that heat is measured against, cm/s. Heating is density x (speed / this)^3. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Entry", meta = (ClampMin = "1.0"))
	float HeatReferenceSpeed = 10000.f;

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

	/** Pitch added on top while boosting forward. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Audio", meta = (ClampMin = "0.0"))
	float EngineBoostPitch = 0.15f;

	/** Low-pass cutoff at the lightest engine load, Hz: a muffled, distant rumble. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Audio", meta = (ClampMin = "20.0"))
	float EngineLowPassIdleHz = 400.f;

	/** Low-pass cutoff at full load or boost, Hz. The loop has almost nothing above 1 kHz anyway. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Audio", meta = (ClampMin = "20.0"))
	float EngineLowPassFullHz = 2000.f;

	/** How fast engine volume and pitch follow the controls, per second. Lower spools slower. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Audio", meta = (ClampMin = "0.1"))
	float EngineSpoolRate = 5.f;

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
	void SetFreeLookHeld(bool bHeld);
	void UpdateFreeLook(float DeltaSeconds);
	void ClearPilotInput();

	/** Fills in any unassigned input asset: first from /Game/Input, then procedurally. */
	void ResolveInputAssets();
	void BuildProceduralInputAssets();

	void UpdateAngularMotion(float DeltaSeconds);
	void UpdateLinearMotion(float DeltaSeconds);
	void UpdateEngineAudio(float DeltaSeconds);
	void UpdateEnvironment(float DeltaSeconds);
	void UpdateHeatShake();
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

	/** The mouse virtual joystick, each axis in [-1, 1]. */
	FVector2D MouseStick = FVector2D::ZeroVector;

	bool bFreeLookHeld = false;
	/** Where the mouse has pushed the view (X yaw, Y pitch), clamped; 0 when released. */
	FVector2D FreeLookTarget = FVector2D::ZeroVector;
	/** What the cameras show, easing towards FreeLookTarget. */
	FVector2D FreeLookAngles = FVector2D::ZeroVector;

	/** Smoothed engine load and boost blend, each in [0, 1], driving the engine sound. */
	float EngineLoad = 0.f;
	float EngineBoostBlend = 0.f;

	bool bBoostHeld = false;
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
