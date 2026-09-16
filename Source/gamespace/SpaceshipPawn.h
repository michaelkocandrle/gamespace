// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "SpaceshipPawn.generated.h"

class UCameraComponent;
class UInputAction;
class UInputComponent;
class UInputMappingContext;
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

protected:
	// ---------------------------------------------------------------------------------------
	// Components
	// ---------------------------------------------------------------------------------------

	/** Unscaled pivot. The hull carries a non-uniform scale, so the camera must not hang off it. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<USceneComponent> ShipRoot;

	/** Placeholder cube standing in for the real ship mesh. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<UStaticMeshComponent> Hull;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<USpringArmComponent> CameraBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<UCameraComponent> ChaseCamera;

	/** First-person view from the nose. Inactive until the player toggles to it. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spaceship|Components")
	TObjectPtr<UCameraComponent> CockpitCamera;

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

	/** Axis2D: X steers yaw, Y steers pitch. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spaceship|Input")
	TObjectPtr<UInputAction> LookAction;

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

	/** Maximum pitch rate, deg/s. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling", meta = (ClampMin = "0.0"))
	float PitchRate = 60.f;

	/** Maximum yaw rate, deg/s. Lower than pitch, as on a real aircraft. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling", meta = (ClampMin = "0.0"))
	float YawRate = 45.f;

	/** Maximum roll rate, deg/s. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling", meta = (ClampMin = "0.0"))
	float RollRate = 110.f;

	/** How fast the ship converges on the commanded rotation rate. Lower feels heavier. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling", meta = (ClampMin = "0.1"))
	float AngularResponsiveness = 6.f;

	/**
	 * Scales the raw look axis. Mouse deltas are pixels per frame, hence the small value.
	 * Higher reaches full turn rate with less mouse movement; the turn rate itself is still
	 * capped by PitchRate / YawRate.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling", meta = (ClampMin = "0.0"))
	float LookSensitivity = 0.15f;

	/** Flip the pitch axis for players who fly stick-style. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spaceship|Handling")
	bool bInvertPitch = false;

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
	void HandleToggleCamera(const FInputActionValue& Value);
	void HandleBoost(const FInputActionValue& Value);
	void HandleBoostCompleted(const FInputActionValue& Value);

	/** Fills in any unassigned input asset: first from /Game/Input, then procedurally. */
	void ResolveInputAssets();
	void BuildProceduralInputAssets();

	void UpdateAngularMotion(float DeltaSeconds);
	void UpdateLinearMotion(float DeltaSeconds);

	float& AxisInput(ESpaceshipAxis Axis);

	float ThrustInput = 0.f;
	float StrafeInput = 0.f;
	float LiftInput = 0.f;
	float RollInput = 0.f;

	/** X yaw, Y pitch. Consumed and cleared every tick because mouse input is a per-frame delta. */
	FVector2D LookInput = FVector2D::ZeroVector;

	bool bBoostHeld = false;
	bool bCockpitView = false;
};
