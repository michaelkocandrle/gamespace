// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "CelestialBody.h"
#include "SpaceshipPawn.generated.h"

class UAudioComponent;
class UBoxComponent;
class UCameraComponent;
class UMaterialParameterCollection;
class ULocalLightComponent;
class UPointLightComponent;
class UCockpitDisplayComponent;
class UInputAction;
class UInputComponent;
class UInputMappingContext;
class UMaterialInstanceDynamic;
class UMaterialInterface;
class USoundBase;
class USpringArmComponent;
class UStaticMesh;
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
	TakeoffCooldown,
	/** Landing gear not fully down (N). The ship can rest on its belly but never counts as landed. */
	GearUp
};

/** Landing gear (N). Moving between the ends takes GearDeploySeconds. */
UENUM(BlueprintType)
enum class EGearState : uint8
{
	Retracted,
	Extending,
	Deployed,
	Retracting
};

/** A hull material slot whose EmissiveStrength the ship animates (thrusters, strobes). */
struct FShipGlowMaterial
{
	TWeakObjectPtr<UMaterialInstanceDynamic> Material;
	float BaseStrength = 0.f;
	float Applied = -1.f;
};

/**
 * Quantum drive (SC-4), after Star Citizen's quantum travel (starcitizenreference/QuantumTravel_VideoNotes.md):
 * in NAV with a destination picked, the drive spools and calibrates on its own; holding the left mouse
 * button then jumps. It replaced the earlier cruise drive (J), which Star Citizen does not have.
 */
UENUM(BlueprintType)
enum class EQuantumState : uint8
{
	/** Nothing to do: SCM, no destination, or blocked (see EQuantumBlocker). */
	Idle,
	/** Spooling and calibrating: SPOOLING n% / CALIBRATING n% on the HUD. */
	Charging,
	/** Spooled, calibrated and nothing in the way: hold the left mouse button to jump. */
	Ready,
	/** In the jump: the ship cannot be steered and flies straight at the destination. */
	Traveling,
	/** Out of a jump: the drive cools for QuantumCooldownSeconds before the next one. */
	Cooling
};

/** Why the quantum drive will not get ready (or why the last jump ended early). */
UENUM(BlueprintType)
enum class EQuantumBlocker : uint8
{
	None,
	/** The drive only works in NAV (B). */
	NeedsNav,
	/** No destination in front of the nose. */
	NoTarget,
	/** The destination is closer than QuantumMinJumpKm. */
	TooClose,
	/** A body lies between the ship and the destination. */
	Obstructed,
	/** Not enough quantum fuel for the distance. */
	NoFuel,
	Landed,
	/** The pilot left NAV mid-jump. */
	Pilot
};

/** Star Citizen master modes: what the ship is set up for. B switches, taking MasterModeSwitchSeconds. */
UENUM(BlueprintType)
enum class EMasterMode : uint8
{
	/** Space Combat Maneuvering: combat speed, full manoeuvrability. */
	SCM,
	/** Navigation: much higher speed, reduced turning and manoeuvring thrust, quantum drive available. */
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
 * Master modes (B): SCM for combat speed and full manoeuvring, NAV for travel and the quantum drive.
 * G-Safe (K) keeps the pilot under GSafeMaxG and turns the nose slower at high speed; ComStab (L)
 * gives cancelling a slide priority over forward thrust and slows turning while the ship slides.
 *
 * Mouse steering is a Star Citizen virtual joystick: the mouse moves a cursor inside a circle that
 * stays where it is left; its offset from the centre (outside a small dead zone) is the turn rate.
 *
 * Boost (Shift) strengthens the manoeuvring thrusters and rotation and suspends G-Safe while its
 * energy lasts; it recharges after a pause. The afterburner (Tab, SCM only) overloads the main
 * thrusters and raises the speed limit (relative to the limiter) from its own slowly refilling
 * fuel tank. The quantum drive (NAV, SC-4) jumps to the body the nose points at: it spools and
 * calibrates by itself, the left mouse button held jumps, and the ship arrives above the destination
 * and cools down before the next jump.
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

	/** Pilot's translation input this tick, -1..1: X forward, Y strafe right, Z lift up (the HUD's strafe cross). */
	FVector GetLinearInput() const { return FVector(ThrustInput, StrafeInput, LiftInput); }

	/** Rotation rate, deg/s, local: X roll, Y pitch, Z yaw. */
	FVector GetAngularVelocity() const { return AngularVelocity; }

	/** The faster of the pitch and yaw rates, deg/s: full scale of the HUD's rate indicator. */
	float GetMaxTurnRate() const { return FMath::Max(PitchRate, YawRate); }

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

	/** G-Safe's total G limit (GSafeMaxG). */
	UFUNCTION(BlueprintPure, Category = "Spaceship|IFCS")
	float GetGSafeMaxG() const { return GSafeMaxG; }

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

	/**
	 * What the thrusters put out this frame, ship-local cm/s^2 (X ahead, Y right, Z up; negative X is the
	 * retro thrusters), after the per-direction limits and G-Safe. Zero on the ground.
	 */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Flight")
	FVector GetThrusterAcceleration() const { return ThrusterAcceleration; }

	/**
	 * What each thruster direction can do right now, cm/s^2 (boost, the afterburner and NAV included):
	 * OutPositive = main / right strafe / up, OutNegative = retro / left strafe / down (as magnitudes).
	 */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Flight")
	void GetThrusterCapacity(FVector& OutPositive, FVector& OutNegative) const { OutPositive = ThrusterCapPositive; OutNegative = ThrusterCapNegative; }

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

	/** Boost held (Shift). For tests and the screenshot runner; the key does the same. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Boost")
	void SetBoostHeld(bool bHeld) { bBoostHeld = bHeld; }

	/** Tests and screenshots: put the ship at this velocity (world cm/s) without flying there. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	void DebugSetLinearVelocity(const FVector& Velocity) { LinearVelocity = Velocity; }

	/**
	 * Shots and tests: jump at once to the destination whose display name starts with TargetName (any
	 * body when empty: the one nearest the nose), skipping spool, calibration and checks, and fly
	 * TravelFraction of the way before letting the frame run. Returns false when there is no such body.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Debug")
	bool DebugEngageQuantum(const FString& TargetName, float TravelFraction = 0.f);

	/** Tests: spool and calibration full at once (the ship still has to be pointed and unblocked). */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	void DebugFinishQuantumCharge() { QuantumSpool = 1.f; QuantumCalibration = 1.f; }

	/** Tests: set the quantum fuel, 0..1. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	void DebugSetQuantumFuel(float Fuel) { QuantumFuel = FMath::Clamp(Fuel, 0.f, 1.f); }

	/** Tests and screenshots: place the mouse virtual joystick cursor. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	void DebugSetMouseStick(const FVector2D& InStick) { MouseStick = InStick; }

	/**
	 * Tests and screenshots: try a cockpit setup without rebuilding the ship - the eye position
	 * (relative to the hull, cm) and what is hidden from the pilot. An eye of (0,0,0) keeps the one
	 * the Blueprint has.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	void DebugConfigureCockpit(const FVector& EyeLocation, bool bHideHull, bool bHideCanopy);

	/** MPC_ShipView.InsideView as this ship last set it: 1 = the player's camera is inside its interior. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Debug")
	float DebugGetInsideView() const { return InsideView; }

	/** Shots / tuning: cockpit key and fill light, display glow (candela) and a multiplier on the interior's
	 * base colour. Negative leaves that one as it is. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	void DebugSetCockpitLighting(float KeyCd, float FillCd, float DisplayCd, float InteriorTint);

	/** Tests and screenshots: finish a master mode switch at once instead of waiting it out. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	void DebugFinishMasterModeSwitch() { if (bMasterModeSwitching) { MasterMode = PendingMasterMode; bMasterModeSwitching = false; MasterModeTimer = 0.f; } }

	UFUNCTION(BlueprintPure, Category = "Spaceship|Quantum")
	EQuantumState GetQuantumState() const { return QuantumState; }

	/** Why the drive is not getting ready, or why the last jump ended early. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Quantum")
	EQuantumBlocker GetQuantumBlocker() const { return QuantumBlocker; }

	/** Spool, 0..1: fills in NAV with a destination, whether or not the nose is on it. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Quantum")
	float GetQuantumSpool() const { return QuantumSpool; }

	/** Calibration, 0..1: fills only while the nose is within QuantumAlignDeg of the destination. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Quantum")
	float GetQuantumCalibration() const { return QuantumCalibration; }

	/** Cooling after a jump, 0..1 (1 = cool again). */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Quantum")
	float GetQuantumCooling() const;

	/** Share of the jump flown, 0..1, while traveling. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Quantum")
	float GetQuantumTravelProgress() const;

	/** How far the engage button has been held, 0..1 of QuantumEngageHoldSeconds. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Quantum")
	float GetQuantumEngageHold() const;

	/** Quantum fuel, 0..1. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Quantum")
	float GetQuantumFuel() const { return QuantumFuel; }

	/** Destination: whether there is one, its name, where it is (its centre) and how far to where the jump would end, cm. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Quantum")
	bool HasQuantumTarget() const { return QuantumTarget.IsValid(); }

	UFUNCTION(BlueprintPure, Category = "Spaceship|Quantum")
	FText GetQuantumTargetName() const { return QuantumTargetName; }

	UFUNCTION(BlueprintPure, Category = "Spaceship|Quantum")
	FVector GetQuantumTargetLocation() const { return QuantumTargetCentre; }

	UFUNCTION(BlueprintPure, Category = "Spaceship|Quantum")
	double GetQuantumTargetDistance() const { return QuantumTargetDistanceCm; }

	/**
	 * 0..1: how much of the quantum look is showing (the tunnel, the view widening, the drone). Rises
	 * over the first second of a jump and falls over the last.
	 */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Quantum")
	float GetQuantumBlend() const { return QuantumBlend; }

	/** Tests: hold (or let go of) the engage button, as the left mouse button does. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Quantum")
	void SetQuantumEngageHeld(bool bHeld);

	/** Where a jump to a body of this radius ends: this far from its surface, cm. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Quantum")
	double ComputeQuantumArrivalAltitude(double BodyRadiusCm) const;

	/**
	 * Speed in the jump for this remaining distance and current speed, cm/s: accelerates at
	 * QuantumAccelerationKmS2 up to QuantumMaxSpeedKmS and brakes so it arrives at QuantumExitSpeed.
	 */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Quantum")
	double ComputeQuantumSpeed(double RemainingCm, double CurrentSpeedCmS, float DeltaSeconds) const;

	/**
	 * The same, SecondsIntoJump into the jump: the acceleration builds up over QuantumRampSeconds
	 * instead of starting at full (the author, 22. 9. 2026: the jump snapped to full speed).
	 */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Quantum")
	double ComputeQuantumSpeedAt(double RemainingCm, double CurrentSpeedCmS, float DeltaSeconds, float SecondsIntoJump) const;

	/** Share of a full tank a jump of this length burns, 0..1. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Quantum")
	float ComputeQuantumFuelUse(double DistanceCm) const;

	/** Whether the straight segment Start-End passes within Radius of Centre (a body in the way). */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Quantum")
	static bool SegmentHitsSphere(const FVector& Start, const FVector& End, const FVector& Centre, double Radius);

	/** Chase camera distance as a multiple of the Blueprint's arm length. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Camera")
	float GetCameraZoom() const { return CameraZoom; }

	/**
	 * Tests: one flight frame of DeltaSeconds with these held inputs, through the same code as Tick
	 * (environment, throttle, boost, quantum drive, steering, motion). Returns the velocity afterwards.
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

	/**
	 * Dashboard focus, as the reference leans in to read its MFDs: while held (Z or the middle mouse
	 * button) the pilot's head leans towards the dashboard, turns to it and the view narrows until the
	 * displays fill it; released, the view goes back. Free look still works on top.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Camera")
	void SetDashboardFocus(bool bFocus);

	/**
	 * Tuning a ship's material without re-importing and re-packaging (the loop that made look work slow):
	 * sets a parameter on every material of this ship, through dynamic instances made on the first call.
	 * Console: space.ShipMat <Parameter> <Value> and space.ShipMatColor <Parameter> <R> <G> <B>.
	 * Nothing is saved - what looks right goes into <Ship>_setup.json.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	int32 DebugSetMaterialScalar(FName Parameter, float Value);

	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	int32 DebugSetMaterialColor(FName Parameter, FLinearColor Value);

	/** The cockpit view's pitch at rest, degrees (negative looks down). */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Camera")
	void SetCockpitViewPitch(float Degrees) { CockpitViewPitchDeg = FMath::Clamp(Degrees, -20.f, 20.f); }

	/** 0 the normal view .. 1 fully on the dashboard (eased). */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Camera")
	float GetDashboardFocus() const { return DashboardFocusBlend; }

	/**
	 * The focused view, from the Display_* sockets: the eye (actor space, cm), where it looks (relative to
	 * the ship) and the horizontal field of view that holds every display. False without displays.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Camera")
	bool ComputeDashboardFocus(FVector& OutEye, FRotator& OutRotation, float& OutFovDeg) const;

	/** Tests: runs the focus easing for this long. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	void DebugAdvanceDashboardFocus(float Seconds);

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

	/** Who gets out (and who walks the ship's interior). */
	TSubclassOf<APawn> GetPilotCharacterClass() const { return PilotCharacterClass; }

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

	// --- Landing gear and precision mode (SC-2a) --------------------------------------------------

	UFUNCTION(BlueprintPure, Category = "Spaceship|Gear")
	EGearState GetGearState() const { return GearState; }

	/** Gear fully down and locked: the only state the ship can land in. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Gear")
	bool IsGearDeployed() const { return GearState == EGearState::Deployed; }

	/** How far out the gear is, 0 stowed .. 1 down and locked (linear in time). */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Gear")
	float GetGearDeploy() const { return GearDeploy; }

	/**
	 * Lowers (true) or raises the gear; it moves over GearDeploySeconds and can reverse halfway.
	 * Lowering it switches precision mode on, raising it switches it off. Raising is refused while
	 * landed (the ship stands on it). Returns false when refused.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Gear")
	bool SetGearDown(bool bDown);

	/** N: lower or raise the gear. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Gear")
	void ToggleGear();

	/** Seconds the "gear stays down while landed" refusal is still worth showing. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Gear")
	float GetGearMessageSeconds() const { return GearMessageSeconds; }

	/** How far below the hull's collision box the gear reaches right now, cm (GearExtensionCm x deploy). */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Gear")
	float GetGearGroundOffsetCm() const;

	/**
	 * One gear leg relative to its socket at a deploy fraction (0 stowed .. 1 down), as the visible
	 * legs use it: [0] pivot rotation (X pitch, Y yaw, Z roll), [1] sleeve centre, [2] sleeve scale,
	 * [3] piston centre, [4] piston scale, [5] pad centre, [6] pad scale - centres and scales in the
	 * pivot's frame, for the 100 cm engine cylinder. bNose folds forward, the others backward.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Gear")
	TArray<FVector> ComputeGearLegPose(float Deploy, bool bNose) const;

	/** Tests: advance only the gear by DeltaSeconds (the code the tick runs). */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	void DebugStepGear(float DeltaSeconds);

	/** Tests and screenshots: put the gear straight into its end position, no animation. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	void DebugSetGearInstant(bool bDown);

	/** Tests: the landing state machine's bookkeeping, as if the ship had just touched down. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	void DebugForceLanded(bool bLanded);

	/**
	 * Screenshots: swing the chase camera round the ship (free look held at these angles, degrees)
	 * and set its distance as a multiple of the normal one (0 keeps it). Zero angles release it.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	void DebugSetChaseView(float YawDeg, float PitchDeg, float Zoom);

	/**
	 * The placeholder cockpit's parts, relative to the pilot's eye (cm, X forward, Y right, Z up): eight
	 * corners per part, in order. Exactly what the visible parts use; for tests of what they cover.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Camera")
	TArray<FVector> GetPlaceholderCockpitCorners() const;

	/** Names of the placeholder cockpit's parts, in the order of GetPlaceholderCockpitCorners. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Camera")
	TArray<FString> GetPlaceholderCockpitPartNames() const;

	/** Tests: placeholder cockpit parts built at BeginPlay (0 when off). */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Tests")
	int32 DebugGetPlaceholderCockpitPartCount() const { return CockpitParts.Num(); }

	/** Tests: number of placeholder gear legs built on the hull's sockets (0 when the ship has a modelled gear part). */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Tests")
	int32 DebugGetGearLegCount() const { return GearLegs.Num(); }

	/**
	 * How far a modelled gear part sits above its modelled (down) position at a deploy fraction, cm:
	 * GearStowTravelCm stowed, 0 down and locked, eased in between. The gear part uses exactly this.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Gear")
	float ComputeGearStowOffsetCm(float Deploy) const;

	/** Precision mode switched on (gear, or P). In effect only in SCM, see IsPrecisionActive. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Precision")
	bool IsPrecisionModeOn() const { return bPrecisionMode; }

	/** Precision mode in effect: switched on and in SCM (NAV is for travel and ignores it). */
	UFUNCTION(BlueprintPure, Category = "Spaceship|Precision")
	bool IsPrecisionActive() const { return bPrecisionMode && MasterMode == EMasterMode::SCM; }

	UFUNCTION(BlueprintCallable, Category = "Spaceship|Precision")
	void SetPrecisionMode(bool bOn);

	/** P: precision mode on / off by hand (the gear sets it too). */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Precision")
	void TogglePrecisionMode() { SetPrecisionMode(!bPrecisionMode); }

	/**
	 * VTOL (G), SC-2b. The ship stands on its manoeuvring thrusters instead of flying on its main
	 * engines: the mains drop to VtolThrustFraction, the vertical and lateral thrusters gain, the
	 * speed drops to VtolMaxSpeed, Space and Ctrl become a climb rate rather than an acceleration,
	 * and the ship holds itself level. Only in SCM, like the reference's VTOL switch; the afterburner
	 * and the cruise drive are refused while it is on. It comes in and goes out over
	 * VtolTransitionSeconds, so nothing snaps - IsVtolOn is the switch, GetVtolBlend the amount.
	 */
	UFUNCTION(BlueprintPure, Category = "Spaceship|VTOL")
	bool IsVtolOn() const { return bVtolMode; }

	/** 0 fully on the mains .. 1 fully on the lift thrusters. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|VTOL")
	float GetVtolBlend() const { return VtolBlend; }

	/** Switched on and in SCM: NAV is for travel and turns VTOL off. */
	UFUNCTION(BlueprintPure, Category = "Spaceship|VTOL")
	bool IsVtolActive() const { return bVtolMode && MasterMode == EMasterMode::SCM; }

	UFUNCTION(BlueprintCallable, Category = "Spaceship|VTOL")
	void SetVtol(bool bOn);

	/**
	 * How far VTOL turns the hull back towards level this frame, as a local pitch / roll step.
	 * WorldUp is the direction gravity says is up. Zero without VTOL, without an up, or once level.
	 * UpdateAngularMotion uses exactly this; separate so a test can check it without a planet.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|VTOL")
	FRotator ComputeVtolLevelStep(const FVector& WorldUp, float DeltaSeconds) const;

	/** G: VTOL on / off. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|VTOL")
	void ToggleVtol() { SetVtol(!bVtolMode); }

	/**
	 * The touchdown rule with the gear: GearUp unless the gear is down and locked, otherwise
	 * EvaluateLanding on the gap under the pads (hull gap minus GearExtensionCm; pads already pressed
	 * into the ground count as 0). HullGap < 0 means nothing below. The state machine uses exactly this.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Landing")
	ELandingBlocker EvaluateTouchdown(float HullGap, float Speed, float TiltDeg, float SlopeDeg, bool bEngineInput, bool bGearDown) const;

	/**
	 * The touchdown rule on its own: the first blocker for these measurements, or None. The state
	 * machine uses it through EvaluateTouchdown, on the gap under the gear; exposed for tests.
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

	/** The look of a quantum jump: streaks radiating from the flight path, beams and a glow on it. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<class USpaceSpeedTunnelComponent> SpeedTunnel;

	/** Streaks pouring off the hull from the nose back: blue in a quantum jump, a few white ones in flight. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<class USpaceHullSparksComponent> HullSparks;

	/** Blue light at the nose in a quantum jump: the reference's glow under the canopy, and what lights the hull. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<class UPointLightComponent> QuantumGlow;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<USpringArmComponent> CameraBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<UCameraComponent> ChaseCamera;

	/** First-person view from the nose. Inactive until the player toggles to it. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<UCameraComponent> CockpitCamera;

	/**
	 * Cockpit lighting: the hull shadows the cabin, so without it a modelled interior is nearly black.
	 * Placed at the eye + CockpitLightOffset at BeginPlay, casts no shadows, off at intensity 0.
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<UPointLightComponent> CockpitLight;

	/** Cockpit fill light: see CockpitFillIntensityCd. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<UPointLightComponent> CockpitFillLight;

	/** The dashboard displays: flight instruments drawn into the interior's display slot (if it has one). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<UCockpitDisplayComponent> CockpitDisplays;

	/** Engine loop. Started and stopped by UpdateEngineAudio, never auto-activated. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<UAudioComponent> EngineAudio;

	/** What the gear legs are built from (/Engine/BasicShapes/Cylinder): placeholder art until a modelled gear replaces it. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Gear")
	TObjectPtr<UStaticMesh> GearLegMesh;

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

	/**
	 * Hide mesh components whose name contains "Canopy" from the pilot in cockpit view. Meant for a ship
	 * without a modelled interior, whose canopy is a shallow tinted shell that sits ~13 cm from the eye and
	 * fills the whole view (see Tools/Blender/cockpit_view_survey.py). Hidden, the pilot looks out
	 * through the open frame; everyone else, and the chase camera, still see the glass.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera")
	bool bHideCanopyInCockpit = true;

	/**
	 * A stand-in cockpit for ships without a modelled interior: dashboard with screens under the view,
	 * a glare-shield lip, canopy pillars at the sides and a seat behind the pilot, simple dark boxes
	 * placed relative to the pilot's eye and shown only in cockpit view. Without it an AI hull seen
	 * from inside is culled away and the HUD floats in empty space. Off once a real interior exists.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera")
	bool bPlaceholderCockpit = false;

	/** Cockpit light brightness, candela (0: no light). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.0"))
	float CockpitLightIntensityCd = 0.f;

	/** Where the cockpit light sits relative to the pilot's eye, cm (above the dashboard, in front of the face). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera")
	FVector CockpitLightOffset = FVector(45.0, 0.0, 10.0);

	/** How far the cockpit light reaches, cm: the cabin and not the hull around it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "10.0"))
	float CockpitLightRadiusCm = 250.f;

	/** Cockpit light colour: slightly cool, like instrument lighting. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera")
	FLinearColor CockpitLightColor = FLinearColor(0.85f, 0.92f, 1.f);

	/** Size of the cockpit lights, cm: a larger source gives broad, soft highlights instead of a white pinpoint. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.0"))
	float CockpitLightSourceRadiusCm = 0.f;

	/** Fill light, candela (0: none): a second, weaker light from another side so the cabin is not lit or black. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.0"))
	float CockpitFillIntensityCd = 0.f;

	/** Where the fill light sits relative to the pilot's eye, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera")
	FVector CockpitFillOffset = FVector(-20.0, 0.0, 10.0);

	/** Engine cube the placeholder cockpit is built from, and its material (Color parameter). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Camera")
	TObjectPtr<UStaticMesh> CockpitPartMesh;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Camera")
	TObjectPtr<UMaterialInterface> CockpitPartMaterial;

	/** Digital, held: free look (right mouse button). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> FreeLookAction;

	/** Digital, pressed: flight assist on / off (V). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> FlightAssistAction;

	/** Digital, held: quantum jump (left mouse button, held QuantumEngageHoldSeconds). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> QuantumEngageAction;

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

	/** Digital, pressed: landing gear down / up (N). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> LandingGearAction;

	/** Digital, pressed: precision mode on / off (P). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> PrecisionAction;

	/** G: VTOL (SC-2b). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> VtolAction;

	/** Digital, held: dashboard focus (Z, middle mouse button). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> DashboardFocusAction;

	/** Digital, pressed: the left MFD's next page (F1, or [ on a US keyboard; with Alt the previous one). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> MfdLeftAction;

	/** Digital, pressed: the right MFD's next page (F2, or ]; with Alt the previous one). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> MfdRightAction;

	/** Maps keys the authored flight context lacks (F, V, J, X, B, K, L, N, P, right mouse button, wheel). */
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
	float AfterburnerThrustMultiplier = 2.1f;

	/**
	 * Afterburner: the speed limit becomes SCM top speed x this x the speed limiter. Relative to the
	 * limiter, as in Star Citizen: at a 50 % limiter the afterburner reaches 50 % of its full top speed.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Afterburner", meta = (ClampMin = "1.0"))
	float AfterburnerSpeedMultiplier = 2.5f;

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
	float AfterburnerSpoolSeconds = 0.25f;

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
	// Quantum drive (SC-4). Distances are this system's, not Star Citizen's: its bodies are tens to
	// hundreds of km apart, not gigametres, so a jump takes seconds to half a minute as there.
	// ---------------------------------------------------------------------------------------

	/** Spool from cold, s (the video's small ship: about 6 s). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Quantum", meta = (ClampMin = "0.0", Units = "s"))
	float QuantumSpoolSeconds = 6.f;

	/** Calibration with the nose on the destination, s. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Quantum", meta = (ClampMin = "0.0", Units = "s"))
	float QuantumCalibrationSeconds = 2.5f;

	/** The nose must be within this of the destination to calibrate and to jump, degrees. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Quantum", meta = (ClampMin = "0.5", ClampMax = "45.0", Units = "deg"))
	float QuantumAlignDeg = 6.f;

	/** A destination is picked when the nose is within this of it, degrees. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Quantum", meta = (ClampMin = "1.0", ClampMax = "180.0", Units = "deg"))
	float QuantumPickDeg = 35.f;

	/** How long the left mouse button has to be held to jump, s. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Quantum", meta = (ClampMin = "0.0", Units = "s"))
	float QuantumEngageHoldSeconds = 0.6f;

	/** Cooling after a jump, s. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Quantum", meta = (ClampMin = "0.0", Units = "s"))
	float QuantumCooldownSeconds = 10.f;

	/** Top speed in a jump, km/s. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Quantum", meta = (ClampMin = "1.0"))
	float QuantumMaxSpeedKmS = 30.f;

	/** Acceleration and braking in a jump, km/s per second. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Quantum", meta = (ClampMin = "0.1"))
	float QuantumAccelerationKmS2 = 8.f;

	/** How long the jump's acceleration takes to build up to QuantumAccelerationKmS2, s. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Quantum", meta = (ClampMin = "0.0", Units = "s"))
	float QuantumRampSeconds = 2.5f;

	/** The tunnel and the rest of the jump's look are full from this share of top speed. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Quantum", meta = (ClampMin = "0.01", ClampMax = "1.0"))
	float QuantumLookFullSpeedShare = 0.25f;

	/** Speed at the end of a jump, cm/s; NAV flight takes over from there. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Quantum", meta = (ClampMin = "0.0"))
	float QuantumExitSpeed = 30000.f;

	/** A jump ends this many body radii above the surface (a planet: above its atmosphere)... */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Quantum", meta = (ClampMin = "0.0"))
	float QuantumArrivalRadii = 0.6f;

	/** ...but never closer than this, km. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Quantum", meta = (ClampMin = "0.0", Units = "km"))
	float QuantumMinArrivalKm = 15.f;

	/** No jump shorter than this, km. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Quantum", meta = (ClampMin = "0.0", Units = "km"))
	float QuantumMinJumpKm = 20.f;

	/** Share of the tank burnt per 1000 km of jump. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Quantum", meta = (ClampMin = "0.0"))
	float QuantumFuelPer1000Km = 0.12f;

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

	/** The cockpit view's pitch at rest, degrees (negative looks down): framing of the dashboard. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "-20.0", ClampMax = "20.0"))
	float CockpitViewPitchDeg = 0.f;

	/** Dashboard focus: how far the head leans towards the displays, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.0"))
	float DashboardFocusLeanCm = 15.f;

	/** Dashboard focus: room round the displays, as a share of each display's half size (0.1 = 10 %). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.0"))
	float DashboardFocusMargin = 0.08f;

	/** Dashboard focus: half size of a display round its socket, cm (a fighter's MFDs are ~33 x 29 cm). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "1.0"))
	FVector2D DashboardDisplayHalfSizeCm = FVector2D(17.0, 15.0);

	/** Dashboard focus: how fast the view goes in and out (1/s). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.1"))
	float DashboardFocusRate = 7.f;

	/** Degrees added to the field of view at full afterburner... */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.0"))
	float AfterburnerFovKick = 9.f;
	/** Chase camera lag, normally and in a quantum jump (wound up over the ramp, never switched off). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera", meta = (ClampMin = "0.1"))
	float BaseCameraLagSpeed = 8.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera", meta = (ClampMin = "0.1"))
	float QuantumCameraLagSpeed = 40.f;

	/** The exposure the jump is locked to (scene luminance) and the bias on top of it: a jump is dark. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera", meta = (ClampMin = "0.01"))
	float QuantumExposure = 1.6f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	float QuantumExposureBias = -0.8f;

	/**
	 * Exposure bias of the cockpit view outside a jump. The Star Citizen references keep the cockpit
	 * dim against the outside (mean brightness 0.13-0.19, ours was 0.26-0.43 over the planet); -0.7 EV
	 * lands there (Tools/Shots/cockpit_look.json, HANDOFF point 72). The displays are emissive and would
	 * dim with it, so their emissive strength in the ship's <Ship>_setup.json is raised by the same 2^0.7.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	float CockpitExposureBias = -0.7f;

	/** The thruster glow is scaled by this in a jump: at full it blows out against the pinned exposure. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float QuantumThrusterScale = 0.35f;


	/** ...and in a quantum jump. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.0"))
	float QuantumFovKick = 12.f;

	/** Camera shake while boosting, cm (cockpit a quarter). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.0"))
	float BoostShakeCm = 1.f;

	/** Camera shake at full afterburner, cm (cockpit a quarter). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.0"))
	float AfterburnerShakeCm = 4.5f;

	/** Camera shake at the start of a quantum jump, cm; a little stays while traveling. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.0"))
	float QuantumShakeCm = 6.f;

	/**
	 * The sun's share in a quantum jump. In the reference the ship is a dark silhouette lit only by the
	 * tunnel's blue sparks; at full sun it read as a lit model pasted on a background (22. 9. 2026).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float QuantumSunScale = 0.45f;

	/** The level's sky light (fill) is scaled by this in a jump: there is nothing to bounce off in a tunnel. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Quantum", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float QuantumSkyScale = 0.15f;

	/** Brightness of the nose glow at a full jump, candela. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Camera", meta = (ClampMin = "0.0"))
	float QuantumGlowCandela = 60.f;

	/** Short jolt when boost or the afterburner starts, or a quantum jump starts or ends, cm. */
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

	/** ...and in a quantum jump. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Lights", meta = (ClampMin = "0.0"))
	float ThrusterQuantumGlow = 3.f;

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
	// Landing gear and precision mode (SC-2a)
	// ---------------------------------------------------------------------------------------

	/**
	 * How far the deployed gear reaches below the hull's collision box, cm: a landed ship rests this
	 * high on its pads. The legs themselves have no collision; the ground is kept at this distance
	 * from the hull box instead, which is far more robust than three thin cylinders.
	 *
	 * 0 for a ship whose modelled gear is already inside its collision box (the box then
	 * ends at the pads' soles, where the SOCKET_Gear_* empties are). The default is for the
	 * placeholder legs, which hang below the hull.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Gear", meta = (ClampMin = "0.0"))
	float GearExtensionCm = 100.f;

	/**
	 * Modelled gear: a mesh component whose name contains "Gear" (the SM_<Ship>_Gear part from
	 * Blender, see Tools/Blender/split_ship_gear.py) is the gear. Stowed, it rises this far into the
	 * hull, cm, and is hidden; it comes down over GearDeploySeconds. Ships without such a part get
	 * placeholder legs on their gear sockets instead.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Gear", meta = (ClampMin = "0.0"))
	float GearStowTravelCm = 95.f;

	/** Seconds for the gear to go all the way down or up. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Gear", meta = (ClampMin = "0.05", Units = "s"))
	float GearDeploySeconds = 2.f;

	/**
	 * Sockets on the hull mesh that get a leg (SOCKET_Gear_* in Blender; the FBX import drops the
	 * SOCKET_ prefix, and either spelling is found). A name containing "Nose" folds forward, the others back.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Gear")
	TArray<FName> GearSocketNames = { FName(TEXT("Gear_Nose")), FName(TEXT("Gear_L")), FName(TEXT("Gear_R")) };

	/** Radius of the upper strut sleeve, cm. The piston below it is 65 % of that. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Gear", meta = (ClampMin = "1.0"))
	float GearStrutRadiusCm = 10.f;

	/** Radius of the foot pad, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Gear", meta = (ClampMin = "1.0"))
	float GearPadRadiusCm = 30.f;

	/** Thickness of the foot pad, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Gear", meta = (ClampMin = "1.0"))
	float GearPadThicknessCm = 12.f;

	/** How far a stowed leg is swung up under the hull, degrees (nearly flat). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Gear", meta = (ClampMin = "0.0", ClampMax = "90.0"))
	float GearFoldDeg = 85.f;

	/**
	 * Precision mode: top speed as a fraction of the SCM one. The speed limiter still works inside
	 * it, so the wheel sets the approach speed in fine steps (a light fighter: 31.5 m/s, ~1.6 m/s a notch).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Precision", meta = (ClampMin = "0.02", ClampMax = "1.0"))
	float PrecisionSpeedFraction = 0.15f;

	/** VTOL: how long the ship takes to move its thrust from the mains to the lift thrusters, seconds. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|VTOL", meta = (ClampMin = "0.1", ClampMax = "6.0"))
	float VtolTransitionSeconds = 1.5f;

	/** VTOL: what is left of the main engines' thrust. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|VTOL", meta = (ClampMin = "0.05", ClampMax = "1.0"))
	float VtolThrustFraction = 0.35f;

	/** VTOL: the lift thrusters (up and down) gain this much. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|VTOL", meta = (ClampMin = "1.0", ClampMax = "3.0"))
	float VtolLiftMultiplier = 1.5f;

	/** VTOL: the lateral thrusters gain this much. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|VTOL", meta = (ClampMin = "1.0", ClampMax = "3.0"))
	float VtolStrafeMultiplier = 1.3f;

	/** VTOL: top speed, cm/s (the limiter still works inside it). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|VTOL", meta = (ClampMin = "500.0"))
	float VtolMaxSpeed = 6000.f;

	/** VTOL: how fast Space and Ctrl climb and sink, cm/s. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|VTOL", meta = (ClampMin = "100.0"))
	float VtolClimbSpeed = 1500.f;

	/** VTOL: how fast the ship rights itself towards the horizon when the stick is still, deg/s. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|VTOL", meta = (ClampMin = "0.0", ClampMax = "120.0"))
	float VtolLevelRate = 25.f;

	/**
	 * What counts as the engines working hard vertically, in G. Holding a hover is a small fraction of
	 * what the lift thrusters can do (on Veyra ~0.46 G of 5.5 G), so against their full capacity the
	 * glow and the sound stayed at nothing and hovering looked dead (HANDOFF kapitola 11). Against one
	 * G of thrust instead, a hover reads as the work it is.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|VTOL", meta = (ClampMin = "0.2", ClampMax = "6.0"))
	float HoverThrustReferenceG = 1.f;

	/** Precision mode: turn rates and rotational accelerations as a fraction of the normal ones. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Precision", meta = (ClampMin = "0.05", ClampMax = "1.0"))
	float PrecisionTurnScale = 0.45f;

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

	/** Quantum jump drone (the former cruise sounds). /Game/Ships/Audio/SW_CruiseLoop when empty. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Audio")
	TObjectPtr<USoundBase> QuantumLoopSound;

	/** One-shots: boost ignition, quantum engage held (charge), jump, arrival. /Game/Ships/Audio/SW_* when empty. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Audio")
	TObjectPtr<USoundBase> BoostStartSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Audio")
	TObjectPtr<USoundBase> QuantumChargeSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Audio")
	TObjectPtr<USoundBase> QuantumEngageSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Audio")
	TObjectPtr<USoundBase> QuantumExitSound;

	/** Gear touching down when the ship becomes Landed. /Game/Ships/Audio/SW_Touchdown when empty. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Audio")
	TObjectPtr<USoundBase> TouchdownSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Audio", meta = (ClampMin = "0.0"))
	float EngineHumVolume = 0.4f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Audio", meta = (ClampMin = "0.0"))
	float BoostVolume = 0.6f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Audio", meta = (ClampMin = "0.0"))
	float QuantumVolume = 0.55f;

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
	void HandleQuantumEngageStarted(const FInputActionValue& Value);
	void HandleQuantumEngageCompleted(const FInputActionValue& Value);
	void HandleAllStop(const FInputActionValue& Value);
	void HandleAllStopCompleted(const FInputActionValue& Value);
	void HandleCameraZoom(const FInputActionValue& Value);
	void HandleMasterMode(const FInputActionValue& Value);
	void HandleSpeedLimiter(const FInputActionValue& Value);
	void HandleGSafe(const FInputActionValue& Value);
	void HandleComStab(const FInputActionValue& Value);
	void HandleAfterburner(const FInputActionValue& Value);
	void HandleAfterburnerCompleted(const FInputActionValue& Value);
	void HandleLandingGear(const FInputActionValue& Value);
	void HandlePrecision(const FInputActionValue& Value);
	void HandleVtol(const FInputActionValue& Value);
	void HandleDashboardFocusStarted(const FInputActionValue& Value);
	void HandleDashboardFocusCompleted(const FInputActionValue& Value);
	/** The cockpit camera's turn: free look on top of the dashboard focus. */
	void ApplyCockpitRotation();
	void HandleMfdLeft(const FInputActionValue& Value);
	void HandleMfdRight(const FInputActionValue& Value);
	/** Pages an MFD (0 left, 1 right): forward, or back with Alt held. */
	void CycleMfdPage(int32 Display);
	/** Moves the gear towards its commanded end and poses the legs. */
	void UpdateGear(float DeltaSeconds);

	/** Moves VtolBlend towards the switch and drops VTOL when the ship leaves SCM. */
	void UpdateVtol(float DeltaSeconds);
	/** Creates the visible gear legs on the hull's gear sockets (once, at BeginPlay). */
	void BuildGearLegs();
	void PoseGearLegs();
	/** Keeps the deployed gear's pads out of the ground: stops the descent there and lifts a ship resting on its belly. */
	void ApplyGearSupport(float DeltaSeconds);
	/** Creates the placeholder cockpit (bPlaceholderCockpit), once, at BeginPlay. */
	void BuildPlaceholderCockpit();

	/** Puts the cockpit key and fill lights at the eye + their offsets (BeginPlay, and when the eye moves). */
	void PlaceCockpitLights();
	void UpdateAfterburner(float DeltaSeconds);
	/** Alt held on the controlling player's keyboard: the wheel zooms instead of setting the limiter. */
	bool IsAltHeld() const;
	void SetFreeLookHeld(bool bHeld);
	void UpdateFreeLook(float DeltaSeconds);
	void ClearPilotInput();

	void UpdateMasterMode(float DeltaSeconds);
	void UpdateBoost(float DeltaSeconds);
	void UpdateQuantum(float DeltaSeconds);
	/** Picks the destination in front of the nose and measures it (sets QuantumTarget* members). */
	void UpdateQuantumTarget();
	/** What stops the drive from getting ready now, for the current destination. */
	EQuantumBlocker EvaluateQuantum() const;
	void BeginQuantumJump();
	void EndQuantumJump(EQuantumBlocker Reason);
	/** One frame of a jump: straight at the arrival point, no steering, no thrusters. */
	void UpdateQuantumTravel(float DeltaSeconds);
	/** Everything a flight frame does before the camera and sound: shared by Tick and DebugStepFlight. */
	void StepFlight(float DeltaSeconds);
	void UpdateCameraEffects(float DeltaSeconds);
	void UpdateSpaceDust(float DeltaSeconds);
	/**
	 * Glass reflection by where the camera is (author 26. 9. 2026): MPC_ShipView.InsideView = 1 while the
	 * player's camera is inside this ship's interior (the "Interior*" parts' bounds, or the cockpit camera
	 * of a ship without one): the canopy reflects weakly; 0 in the chase camera and outside: strongly.
	 */
	void UpdateViewCollection();
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

	/** See GetThrusterAcceleration / GetThrusterCapacity. */
	FVector ThrusterAcceleration = FVector::ZeroVector;
	FVector ThrusterCapPositive = FVector::ZeroVector;
	FVector ThrusterCapNegative = FVector::ZeroVector;

	bool bSpaceBrakeHeld = false;
	EMasterMode MasterMode = EMasterMode::SCM;
	EMasterMode PendingMasterMode = EMasterMode::SCM;
	bool bMasterModeSwitching = false;
	float MasterModeTimer = 0.f;
	float SpeedLimiterFraction = 1.f;
	float GForce = 0.f;
	float SlipAngleDeg = 0.f;

	EQuantumState QuantumState = EQuantumState::Idle;
	EQuantumBlocker QuantumBlocker = EQuantumBlocker::NoTarget;
	float QuantumSpool = 0.f;
	float QuantumCalibration = 0.f;
	float QuantumCooldownTimer = 0.f;
	float QuantumEngageTimer = 0.f;
	bool bQuantumEngageHeld = false;
	float QuantumFuel = 1.f;
	/** The destination: its actor, name, centre, radius, and the jump that would reach it. */
	TWeakObjectPtr<AActor> QuantumTarget;
	FText QuantumTargetName;
	FVector QuantumTargetCentre = FVector::ZeroVector;
	double QuantumTargetRadiusCm = 0.0;
	double QuantumTargetDistanceCm = 0.0;
	/** While traveling: the jump's length at the start, for progress and fuel. */
	double QuantumJumpLengthCm = 0.0;
	/** Seconds since the jump began, for the acceleration ramp. */
	float QuantumTravelSeconds = 0.f;

	/** Eased 0..1 blends driving camera, lights and sound. */
	float BoostBlend = 0.f;
	float AfterburnerFeel = 0.f;
	/** The level's sun and its own intensity, for QuantumSunScale. */
	TWeakObjectPtr<class UDirectionalLightComponent> QuantumSun;
	float QuantumSunBaseIntensity = -1.f;
	TWeakObjectPtr<class USkyLightComponent> QuantumSky;
	float QuantumSkyBaseIntensity = -1.f;
	float QuantumBlend = 0.f;
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
	TObjectPtr<UAudioComponent> QuantumAudio;
	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> QuantumChargeAudio;

	bool bCockpitView = false;

	FCelestialEnvironment Environment;
	bool bHasEnvironment = false;
	TWeakObjectPtr<ACelestialBody> NearestBody;

	EGearState GearState = EGearState::Retracted;
	float GearDeploy = 0.f;
	float GearMessageSeconds = 0.f;
	bool bPrecisionMode = false;

	/** VTOL switched on (G), and how far the thrust has moved to the lift thrusters, 0..1. */
	bool bVtolMode = false;
	float VtolBlend = 0.f;

	/** One visible gear leg: pivot at the socket, a sleeve, a piston and a foot pad. */
	struct FGearLeg
	{
		TWeakObjectPtr<USceneComponent> Pivot;
		TWeakObjectPtr<UStaticMeshComponent> Sleeve;
		TWeakObjectPtr<UStaticMeshComponent> Piston;
		TWeakObjectPtr<UStaticMeshComponent> Pad;
		bool bNose = false;
	};
	TArray<FGearLeg> GearLegs;
	/** The placeholder cockpit: a root at the pilot's eye and its parts. */
	UPROPERTY(Transient)
	TObjectPtr<USceneComponent> CockpitFrameRoot;
	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> CockpitParts;
	/** The modelled gear part, when the ship has one, and where it sits with the gear down. */
	TWeakObjectPtr<UStaticMeshComponent> ModelledGear;
	FVector ModelledGearDownLocation = FVector::ZeroVector;
	/** Deploy fraction the legs were last posed at (-1: never). */
	float GearPosed = -1.f;

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

	bool bDashboardFocusHeld = false;
	float DashboardFocusBlend = 0.f;
	/** The focused view, computed when the focus starts (the eye can move in shots). */
	bool bDashboardFocusValid = false;
	FVector DashboardFocusEye = FVector::ZeroVector;
	FRotator DashboardFocusRotation = FRotator::ZeroRotator;
	float DashboardFocusFov = 90.f;

	/** Ticks left with camera lag switched off after SnapCameraToShip. */
	int32 CameraSnapTicks = 0;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialParameterCollection> ViewCollection;
	/** The interior parts' bounds in actor space (cm); invalid when the ship has none. */
	FBox InteriorBoundsLocal = FBox(ForceInit);
	bool bInteriorBoundsReady = false;
	float InsideView = 0.f;
	/** The Light_fix_* components (hs_fixture_lights.py), on only while the camera is inside the ship. */
	UPROPERTY(Transient)
	TArray<TObjectPtr<ULocalLightComponent>> FixtureLights;
	bool bFixtureLightsOn = true;
};
