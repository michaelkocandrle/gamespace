// Copyright Epic Games, Inc. All Rights Reserved.

#include "ShipLandingComponent.h"

#include "GameFramework/Actor.h"
#include "SpaceshipLog.h"

UShipLandingComponent::UShipLandingComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

FString UShipLandingComponent::ShipName() const
{
	return GetOwner() ? GetOwner()->GetName() : GetName();
}

void UShipLandingComponent::BeginFrame(float DeltaSeconds)
{
	TakeoffCooldown = FMath::Max(0.f, TakeoffCooldown - DeltaSeconds);
	Ground.bValid = false;
	Ground.bContact = false;
	Ground.GapCm = -1.f;
	Ground.bHullClear = true;
}

UShipLandingComponent::EEvent UShipLandingComponent::Update(float DeltaSeconds, const FShipGroundProbe& Probe, float Speed,
	bool bEngineInput, const FShipLandingRules& Rules)
{
	Ground = Probe;
	if (State == ELandingState::Landed)
	{
		Blocker = ELandingBlocker::None;
		return bEngineInput || !Ground.bValid ? EEvent::TookOff : EEvent::None;
	}

	Blocker = !Ground.bValid ? ELandingBlocker::NoSurface
		: TakeoffCooldown > 0.f ? ELandingBlocker::TakeoffCooldown
		: FShipFlightModel::EvaluateTouchdown(Ground.GapCm, Speed, Ground.TiltDeg, Ground.SlopeDeg, bEngineInput,
			IsGearDeployed(), Rules.GearExtensionCm, Rules.Limits);
	if (Blocker == ELandingBlocker::None && !Ground.bHullClear)
	{
		Blocker = ELandingBlocker::Obstructed;
	}
	// Why a ship at the ground does not land, once per change (landing shots and tests read it from the log).
	if (Blocker != LoggedBlocker && Ground.bContact)
	{
		LoggedBlocker = Blocker;
		UE_LOG(LogSpaceship, Log, TEXT("%s: on the ground, touchdown %s (gap %.0f cm, slope %.1f deg, tilt %.1f deg, speed %.0f cm/s)"),
			*ShipName(), Blocker == ELandingBlocker::None ? TEXT("possible") : *UEnum::GetDisplayValueAsText(Blocker).ToString(),
			Ground.GapCm, Ground.SlopeDeg, Ground.TiltDeg, Speed);
	}

	if (Blocker == ELandingBlocker::None)
	{
		// Every condition has to hold without a break: a bounce restarts the window.
		SettleSeconds += DeltaSeconds;
		State = ELandingState::Settling;
		if (SettleSeconds >= Rules.ConfirmSeconds)
		{
			return EEvent::TouchedDown;
		}
	}
	else
	{
		SettleSeconds = 0.f;
		State = ELandingState::Flying;
	}
	return EEvent::None;
}

void UShipLandingComponent::EnterLanded(const FShipLandingRules& Rules)
{
	State = ELandingState::Landed;
	SettleSeconds = Rules.ConfirmSeconds;
}

void UShipLandingComponent::ExitLanded(const FShipLandingRules& Rules)
{
	State = ELandingState::Flying;
	SettleSeconds = 0.f;
	TakeoffCooldown = Rules.TakeoffCooldownSeconds;
}

bool UShipLandingComponent::SetGearDown(bool bDown)
{
	if (!bDown && State == ELandingState::Landed)
	{
		// The ship stands on it. Take off first.
		GearMessageSeconds = 3.f;
		return false;
	}
	if (bDown == IsGearGoingDown())
	{
		return true;
	}
	GearState = bDown ? EGearState::Extending : EGearState::Retracting;
	GearMessageSeconds = 0.f;
	// Star Citizen puts a ship with its gear down into landing mode; the pilot can still override it (P).
	SetPrecisionMode(bDown);
	UE_LOG(LogSpaceship, Log, TEXT("%s: gear %s"), *ShipName(), bDown ? TEXT("down") : TEXT("up"));
	return true;
}

bool UShipLandingComponent::UpdateGear(float DeltaSeconds, float DeploySeconds)
{
	GearMessageSeconds = FMath::Max(0.f, GearMessageSeconds - DeltaSeconds);
	const float Step = DeltaSeconds / FMath::Max(DeploySeconds, 0.05f);
	if (GearState == EGearState::Extending)
	{
		GearDeploy = FMath::Min(1.f, GearDeploy + Step);
		if (GearDeploy >= 1.f)
		{
			GearState = EGearState::Deployed;
			return true;
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
	return false;
}

void UShipLandingComponent::SetGearInstant(bool bDown)
{
	SetPrecisionMode(bDown);
	GearState = bDown ? EGearState::Deployed : EGearState::Retracted;
	GearDeploy = bDown ? 1.f : 0.f;
}

void UShipLandingComponent::SetPrecisionMode(bool bOn)
{
	if (bOn == bPrecisionMode)
	{
		return;
	}
	bPrecisionMode = bOn;
	UE_LOG(LogSpaceship, Log, TEXT("%s: precision mode %s"), *ShipName(), bOn ? TEXT("on") : TEXT("off"));
}
