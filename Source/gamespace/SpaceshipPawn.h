// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
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

/**
 * Player-flown spaceship with 6 degrees of freedom: thrust / strafe / lift plus pitch / yaw / roll.
 *
 * Motion is integrated by hand rather than handed to Chaos. For a space game that keeps the feel
 * predictable and cheap to tune. Velocity lives in LinearVelocity and is bled off by
 * LinearDamping, which acts as the flight assist of Elite-style flight models: set it to 0 for
 * true Newtonian drift.
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

	/** Switches between the chase camera and the cockpit camera. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Camera")
	void SetCockpitView(bool bCockpit);

	/**
	 * Puts the chase camera straight back behind the ship instead of letting camera lag glide it
	 * there. Call after teleporting the ship, or the camera trails across the whole jump.
	 */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Camera")
	void SnapCameraToShip();

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

	/** Flight assist: fraction of velocity shed per second. 0 gives true Newtonian drift. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Flight", meta = (ClampMin = "0.0"))
	float LinearDamping = 1.2f;

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

	/** Fills in any unassigned input asset: first from /Game/Input, then procedurally. */
	void ResolveInputAssets();
	void BuildProceduralInputAssets();

	void UpdateAngularMotion(float DeltaSeconds);
	void UpdateLinearMotion(float DeltaSeconds);
	void UpdateEngineAudio(float DeltaSeconds);

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

	/** Smoothed engine load and boost blend, each in [0, 1], driving the engine sound. */
	float EngineLoad = 0.f;
	float EngineBoostBlend = 0.f;

	bool bBoostHeld = false;
	bool bCockpitView = false;

	/** Ticks left with camera lag switched off after SnapCameraToShip. */
	int32 CameraSnapTicks = 0;
};
