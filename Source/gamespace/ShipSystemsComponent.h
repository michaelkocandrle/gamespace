// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ShipSystemsComponent.generated.h"

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
 * A reserve the pilot draws from while holding a key: the boost's energy and the afterburner's fuel (SC-1b). It
 * drains while in use, locks when empty until it has refilled to UnlockFraction, and refills after a delay.
 */
struct FShipReserve
{
	struct FTuning
	{
		float DurationSeconds = 1.f;
		float RefillSeconds = 1.f;
		float RefillDelaySeconds = 0.f;
		float UnlockFraction = 0.f;
	};

	bool bHeld = false;
	bool bActive = false;
	bool bLocked = false;
	/** 0 empty .. 1 full. */
	float Level = 1.f;
	float RefillWait = 0.f;

	/** One frame. bAllowed is everything the ship needs besides the key and the reserve; true when it just came on. */
	bool Update(float DeltaSeconds, bool bAllowed, const FTuning& Tuning);
};

/**
 * The ship's systems state: master mode, speed limiter, boost, afterburner and VTOL (SC-1a/1b, SC-2b), split out
 * of ASpaceshipPawn (Docs/Reviews/2026-09-30_spaceshippawn_split_plan.md). G-Safe and ComStab stay on the pawn:
 * they are two editable switches (UPROPERTY), not state.
 *
 * Only state and the rules that change it live here. The tuning stays on ASpaceshipPawn (Blueprint overrides and
 * <Ship>_setup.json keys name those UPROPERTYs) and comes in as arguments; the pawn keeps its UFUNCTIONs of the same
 * names for the tests, the HUD and the shot runner, and calls Update* from its own Tick in a fixed order. No tick
 * of its own and nothing in BeginPlay: the headless tests spawn the pawn in the editor world without either.
 */
UCLASS(ClassGroup = (Spaceship), meta = (BlueprintSpawnableComponent = "false"))
class GAMESPACE_API UShipSystemsComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UShipSystemsComponent();

	// --- Master mode (SC-1a) -------------------------------------------------------------------------------------

	EMasterMode GetMasterMode() const { return MasterMode; }
	bool IsMasterModeSwitching() const { return bMasterModeSwitching; }

	/** Where the ship is headed: the mode being switched to, else the current one. */
	EMasterMode GetPendingMasterMode() const { return bMasterModeSwitching ? PendingMasterMode : MasterMode; }

	/** 0..1 through a switch taking SwitchSeconds, 0 when none. */
	float GetMasterModeSwitchProgress(float SwitchSeconds) const;

	/** Starts a switch; true when one started. Asking for the current mode cancels a switch the other way. */
	bool RequestMasterMode(EMasterMode Mode);

	/** Counts a switch down; true on the frame the new mode takes over. */
	bool UpdateMasterMode(float DeltaSeconds, float SwitchSeconds);

	/** A switch in progress done at once (tests). */
	void FinishMasterModeSwitch();

	/** Straight into a mode, cancelling a switch (a quantum jump started from the console). */
	void ForceMasterMode(EMasterMode Mode);

	// --- Speed limiter (SC-1a) -----------------------------------------------------------------------------------

	/** Fraction of the mode's top speed. */
	float GetSpeedLimiter() const { return SpeedLimiterFraction; }
	void SetSpeedLimiter(float Fraction, float MinFraction);

	/** Mouse wheel notches, snapped to whole steps. */
	void AdjustSpeedLimiter(float Notches, float Step, float MinFraction);

	// --- Boost and afterburner (SC-1b) ---------------------------------------------------------------------------

	bool IsBoostActive() const { return Boost.bActive; }
	bool IsBoostLocked() const { return Boost.bLocked; }
	float GetBoostEnergy() const { return Boost.Level; }
	void SetBoostHeld(bool bHeld) { Boost.bHeld = bHeld; }

	/** True on the frame the boost comes on. */
	bool UpdateBoost(float DeltaSeconds, bool bAllowed, const FShipReserve::FTuning& Tuning);

	bool IsAfterburnerActive() const { return Afterburner.bActive; }
	bool IsAfterburnerLocked() const { return Afterburner.bLocked; }
	float GetAfterburnerFuel() const { return Afterburner.Level; }
	void SetAfterburnerHeld(bool bHeld) { Afterburner.bHeld = bHeld; }

	/** How far the afterburner's raised speed limit is in, 0..1. */
	float GetAfterburnerBlend() const { return AfterburnerBlend; }

	/**
	 * True on the frame the afterburner lights. The raised limit spools in over SpoolSeconds and fades out over
	 * FadeSeconds, so running dry or letting go never yanks the ship back to SCM speed.
	 */
	bool UpdateAfterburner(float DeltaSeconds, bool bAllowed, const FShipReserve::FTuning& Tuning, float SpoolSeconds,
		float FadeSeconds);

	/** Both off at once, keys still held: a quantum jump starts, or the ship has landed. */
	void CutBoostAndAfterburner();

	// --- VTOL (SC-2b) --------------------------------------------------------------------------------------------

	/** The switch (G). */
	bool IsVtolOn() const { return bVtolMode; }

	/** 0 fully on the mains .. 1 fully on the lift thrusters. */
	float GetVtolBlend() const { return VtolBlend; }

	/** Switches VTOL; switching on is refused outside SCM (NAV is for travel). */
	void SetVtol(bool bOn);

	/** Moves the blend towards the switch over TransitionSeconds, and drops VTOL once the ship has left SCM. */
	void UpdateVtol(float DeltaSeconds, float TransitionSeconds);

	/** Off at once, without the log line: a quantum jump starts (NAV, so never with VTOL on anyway). */
	void ClearVtol() { bVtolMode = false; }

private:
	/** For the log lines: the ship's name, as the pawn logged them. */
	FString ShipName() const;

	EMasterMode MasterMode = EMasterMode::SCM;
	EMasterMode PendingMasterMode = EMasterMode::SCM;
	bool bMasterModeSwitching = false;
	float MasterModeTimer = 0.f;
	float SpeedLimiterFraction = 1.f;

	FShipReserve Boost;
	FShipReserve Afterburner;
	float AfterburnerBlend = 0.f;

	bool bVtolMode = false;
	float VtolBlend = 0.f;
};
