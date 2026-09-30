// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ShipSystemsComponent.generated.h"

/**
 * The ship's systems state: master mode, speed limiter, G-Safe and ComStab, boost, afterburner and VTOL (SC-1a/1b,
 * SC-2b). Part of splitting ASpaceshipPawn (Docs/Reviews/2026-09-30_spaceshippawn_split_plan.md), filled step by
 * step; step 2 moved VTOL here.
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

	// --- VTOL (SC-2b) --------------------------------------------------------------------------------------------

	/** The switch (G). */
	bool IsVtolOn() const { return bVtolMode; }

	/** 0 fully on the mains .. 1 fully on the lift thrusters. */
	float GetVtolBlend() const { return VtolBlend; }

	/** Switches VTOL; switching on is refused outside SCM (NAV is for travel). */
	void SetVtol(bool bOn, bool bInScm);

	/** Moves the blend towards the switch over TransitionSeconds, and drops VTOL once the ship has left SCM. */
	void UpdateVtol(float DeltaSeconds, bool bInScm, float TransitionSeconds);

	/** Off at once, without the log line: a quantum jump starts (NAV, so never with VTOL on anyway). */
	void ClearVtol() { bVtolMode = false; }

private:
	/** For the log lines: the ship's name, as the pawn logged them. */
	FString ShipName() const;

	bool bVtolMode = false;
	float VtolBlend = 0.f;
};
