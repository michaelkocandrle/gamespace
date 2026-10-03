// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ShipFlightModel.h"
#include "ShipLandingComponent.generated.h"

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
	GearUp,
	/** Standing on its three pads here, the hull would touch the ground (a rock or a ridge under it). */
	Obstructed
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

/** The landing tuning, built from the pawn's Landing* / Gear* / Takeoff* UPROPERTYs. */
struct FShipLandingRules
{
	FShipFlightModel::FLandingLimits Limits;
	float GearExtensionCm = 0.f;
	float ConfirmSeconds = 0.f;
	float TakeoffCooldownSeconds = 0.f;
};

/** The ground under the ship this frame, as the pawn probed it (sweeps need the hull, so they stay there). */
struct FShipGroundProbe
{
	/** Low enough over a walkable body to have looked. */
	bool bValid = false;
	FVector Normal = FVector::UpVector;
	float SlopeDeg = 0.f;
	float TiltDeg = 0.f;
	/** Hull to ground straight down, cm; negative when nothing is within the probe. */
	float GapCm = -1.f;
	/** The pads with the gear down, the belly without it, within the contact tolerance. */
	bool bContact = false;
	/** False when the hull, standing on the pads where the ground is now, would touch the ground. */
	bool bHullClear = true;
};

/**
 * Landing state (SC-2, SC-2a): the touchdown state machine, the ground under the ship, the landing gear and
 * precision mode, split out of ASpaceshipPawn (Docs/Reviews/2026-09-30_spaceshippawn_split_plan.md).
 *
 * The rules live here. What needs the hull or moves the ship - the ground probe (a sweep of the hull's collision),
 * the resting and sliding on the ground, the gear pushing the ship up, and the gear legs one sees - stays on the
 * pawn, which feeds in the probe and reacts to "just landed" / "just took off". The tuning stays on the pawn, its
 * UFUNCTIONs stay as forwarders, and there is no tick of its own: the pawn's StepFlight calls UpdateGear and
 * Update in the same places as before.
 */
UCLASS(ClassGroup = (Spaceship), meta = (BlueprintSpawnableComponent = "false"))
class GAMESPACE_API UShipLandingComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UShipLandingComponent();

	// --- Touchdown -----------------------------------------------------------------------------------------------

	ELandingState GetState() const { return State; }
	bool IsLanded() const { return State == ELandingState::Landed; }
	ELandingBlocker GetBlocker() const { return Blocker; }

	/** Settling progress towards Landed, 0..1. */
	float GetProgress(float ConfirmSeconds) const { return FMath::Clamp(SettleSeconds / FMath::Max(ConfirmSeconds, 0.01f), 0.f, 1.f); }

	/** The ground as last probed. */
	const FShipGroundProbe& GetGround() const { return Ground; }
	bool HasGroundInfo() const { return Ground.bValid; }
	bool HasGroundContact() const { return Ground.bContact; }
	float GetGroundGapCm() const { return Ground.GapCm; }
	float GetGroundSlopeDeg() const { return Ground.SlopeDeg; }
	float GetGroundTiltDeg() const { return Ground.TiltDeg; }
	FVector GetGroundNormal() const { return Ground.Normal; }

	/** The gear pushed the ship up by LiftCm this frame; the gap grows with it. */
	void AddGroundGap(float LiftCm) { Ground.GapCm += LiftCm; }

	/**
	 * Counts the takeoff cooldown down and forgets whether there was ground (valid, gap, contact). Before the probe,
	 * each frame; the probe starts from GetGround(), so the last normal, slope and tilt stay until it finds new ones.
	 */
	void BeginFrame(float DeltaSeconds);

	/** What one frame of the state machine asks the pawn to do. */
	enum class EEvent : uint8 { None, TouchedDown, TookOff };

	/**
	 * One frame, after BeginFrame and the probe: landed, it takes off on engine input or with no ground under it;
	 * otherwise it settles while every touchdown condition holds and lands after ConfirmSeconds of them.
	 */
	EEvent Update(float DeltaSeconds, const FShipGroundProbe& Probe, float Speed, bool bEngineInput, const FShipLandingRules& Rules);

	/** The state change of touching down (the pawn adds the rest: stop turning, the sound, the log). */
	void EnterLanded(const FShipLandingRules& Rules);
	/** The state change of taking off. */
	void ExitLanded(const FShipLandingRules& Rules);

	// --- Landing gear (SC-2a) ------------------------------------------------------------------------------------

	EGearState GetGearState() const { return GearState; }
	bool IsGearDeployed() const { return GearState == EGearState::Deployed; }
	/** Down and locked, or on its way there. */
	bool IsGearGoingDown() const { return GearState == EGearState::Deployed || GearState == EGearState::Extending; }
	float GetGearDeploy() const { return GearDeploy; }
	float GetGearMessageSeconds() const { return GearMessageSeconds; }

	/** Lowers or raises the gear, and precision mode with it; raising is refused while landed. False when refused. */
	bool SetGearDown(bool bDown);

	/** Moves the gear over DeploySeconds; true on the frame it locks down. */
	bool UpdateGear(float DeltaSeconds, float DeploySeconds);

	/** Tests and screenshots: the gear straight into its end position, precision mode with it. */
	void SetGearInstant(bool bDown);

	// --- Precision mode (SC-2a) ----------------------------------------------------------------------------------

	bool IsPrecisionModeOn() const { return bPrecisionMode; }
	void SetPrecisionMode(bool bOn);

private:
	/** For the log lines: the ship's name, as the pawn logged them. */
	FString ShipName() const;

	ELandingState State = ELandingState::Flying;
	ELandingBlocker Blocker = ELandingBlocker::NoSurface;
	/** The blocker last written to the log while touching the ground. */
	ELandingBlocker LoggedBlocker = ELandingBlocker::NoSurface;
	float SettleSeconds = 0.f;
	float TakeoffCooldown = 0.f;
	FShipGroundProbe Ground;

	EGearState GearState = EGearState::Retracted;
	float GearDeploy = 0.f;
	float GearMessageSeconds = 0.f;
	bool bPrecisionMode = false;
};
