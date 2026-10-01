// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ShipFlightModel.h"
#include "ShipQuantumComponent.generated.h"

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

/** The quantum drive's tuning, built from the pawn's Quantum* UPROPERTYs. */
struct FShipQuantumRules
{
	FShipFlightModel::FQuantumDrive Drive;
	float PickDeg = 0.f;
	float AlignDeg = 0.f;
	float MinJumpKm = 0.f;
	float SpoolSeconds = 0.f;
	float CalibrationSeconds = 0.f;
	float EngageHoldSeconds = 0.f;
	float CooldownSeconds = 0.f;
};

/** Where the ship stands this frame, as far as the drive cares. */
struct FShipQuantumContext
{
	FVector Location = FVector::ZeroVector;
	FVector Nose = FVector::ForwardVector;
	bool bLanded = false;
	/** In NAV and not switching away. */
	bool bInNav = false;
};

/**
 * The quantum drive's state (SC-4): destination, blockers, spool, calibration, engage hold, the jump and its fuel,
 * split out of ASpaceshipPawn (Docs/Reviews/2026-09-30_spaceshippawn_split_plan.md).
 *
 * The rules live here; what a jump does to the ship - its velocity and position, camera kicks, sounds, the speed
 * tunnel's flare, the master mode, boost and VTOL - stays on the pawn, which asks for each frame's step and applies
 * it. The tuning stays on the pawn (FShipQuantumRules), the pawn keeps its UFUNCTIONs as forwarders, and there is
 * no tick of its own: the pawn's StepFlight calls Update / StepTravel in the same place as before.
 */
UCLASS(ClassGroup = (Spaceship), meta = (BlueprintSpawnableComponent = "false"))
class GAMESPACE_API UShipQuantumComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UShipQuantumComponent();

	EQuantumState GetState() const { return State; }
	bool IsTraveling() const { return State == EQuantumState::Traveling; }
	EQuantumBlocker GetBlocker() const { return Blocker; }
	float GetSpool() const { return Spool; }
	float GetCalibration() const { return Calibration; }
	float GetFuel() const { return Fuel; }
	bool HasTarget() const { return Target.IsValid(); }
	FText GetTargetName() const { return TargetName; }
	FVector GetTargetCentre() const { return TargetCentre; }
	double GetTargetDistanceCm() const { return TargetDistanceCm; }
	double GetJumpLengthCm() const { return JumpLengthCm; }

	/** 0 just out of a jump .. 1 cooled down (1 when not cooling). */
	float GetCooling(float CooldownSeconds) const;
	/** 0..1 through a jump, 0 outside one. */
	float GetTravelProgress() const;
	/** 0..1 through holding the engage button. */
	float GetEngageHold(float EngageHoldSeconds) const;

	/** The engage button (left mouse); letting go starts the hold over. */
	void SetEngageHeld(bool bHeld);

	/** Tests: spool and calibration full at once. */
	void FinishCharge() { Spool = 1.f; Calibration = 1.f; }
	/** Tests: the fuel, 0..1. */
	void SetFuel(float InFuel) { Fuel = FMath::Clamp(InFuel, 0.f, 1.f); }

	/** What one frame outside a jump asks the pawn to do. */
	struct FFrame
	{
		/** The engage hold has just begun: the charge sound. */
		bool bChargeStarted = false;
		/** Held long enough while ready: jump (the pawn calls BeginJump and adds the effects). */
		bool bEngage = false;
	};

	/**
	 * One flight frame: picks and measures the destination (in a jump it keeps the one it has), then outside a
	 * jump the blockers, spool, calibration, state and engage hold.
	 */
	FFrame Update(float DeltaSeconds, const FShipQuantumContext& Context, const FShipQuantumRules& Rules);

	/** The jump starts: its length, the fuel it burns, Traveling. */
	void BeginJump(const FShipQuantumRules& Rules);

	/** The jump is over (arrived, or why not): cooling, spool and calibration from zero. */
	void EndJump(EQuantumBlocker Reason, const FShipQuantumRules& Rules);

	/** One frame of a jump, straight at the destination. */
	struct FTravelStep
	{
		FVector Direction = FVector::ZeroVector;
		double RemainingCm = 0.0;
		double Speed = 0.0;
		double StepCm = 0.0;
		/** This frame reaches the arrival point (the drive's distance is then zero). */
		bool bArrives = false;
	};

	/** Advances the jump's clock and works out this frame's step; false when the destination is gone. */
	bool StepTravel(float DeltaSeconds, const FVector& Location, double CurrentSpeed, const FShipQuantumRules& Rules,
		FTravelStep& OutStep);

	// --- Shots and tests (DebugEngageQuantum) ------------------------------------------------------------------

	/** The destination whose display name starts with Name (or whose actor name contains it); any body, the one
	 * nearest the nose, when Name is empty. Null when there is none. */
	AActor* FindDestination(const FString& Name, const FVector& Location, const FVector& Nose) const;

	void SetTarget(AActor* Actor) { Target = Actor; }

	/**
	 * Picks the destination in front of the nose and measures it; in a jump it keeps the one it has. Outside a jump
	 * it picks again by the nose, so a SetTarget sticks only when that body is also the one nearest the nose.
	 */
	void UpdateTarget(const FVector& Location, const FVector& Nose, const FShipQuantumRules& Rules);

	/** Part of the jump flown at once: the distance left shrinks by SkipCm. */
	void SkipTravel(double SkipCm) { TargetDistanceCm -= SkipCm; }

	void SetTravelSeconds(float Seconds) { TravelSeconds = Seconds; }

private:
	/** What stops the drive from getting ready now, for the current destination. */
	EQuantumBlocker Evaluate(const FShipQuantumContext& Context, const FShipQuantumRules& Rules) const;

	EQuantumState State = EQuantumState::Idle;
	EQuantumBlocker Blocker = EQuantumBlocker::NoTarget;
	float Spool = 0.f;
	float Calibration = 0.f;
	float CooldownTimer = 0.f;
	float EngageTimer = 0.f;
	bool bEngageHeld = false;
	float Fuel = 1.f;
	/** The destination: its actor, name, centre, radius, and the jump that would reach it. */
	TWeakObjectPtr<AActor> Target;
	FText TargetName;
	FVector TargetCentre = FVector::ZeroVector;
	double TargetRadiusCm = 0.0;
	double TargetDistanceCm = 0.0;
	/** While traveling: the jump's length at the start, for progress and fuel. */
	double JumpLengthCm = 0.0;
	/** Seconds since the jump began, for the acceleration ramp. */
	float TravelSeconds = 0.f;
};
