// Copyright Epic Games, Inc. All Rights Reserved.

#include "ShipSystemsComponent.h"

#include "GameFramework/Actor.h"
#include "SpaceshipLog.h"

bool FShipReserve::Update(float DeltaSeconds, bool bAllowed, const FTuning& Tuning)
{
	const bool bWasActive = bActive;
	if (bLocked && Level >= Tuning.UnlockFraction)
	{
		bLocked = false;
	}
	bActive = bHeld && !bLocked && Level > 0.f && bAllowed;

	if (bActive)
	{
		Level = FMath::Max(0.f, Level - DeltaSeconds / Tuning.DurationSeconds);
		RefillWait = Tuning.RefillDelaySeconds;
		if (Level <= 0.f)
		{
			bLocked = true;
			bActive = false;
		}
	}
	else
	{
		RefillWait = FMath::Max(0.f, RefillWait - DeltaSeconds);
		if (RefillWait <= 0.f)
		{
			Level = FMath::Min(1.f, Level + DeltaSeconds / Tuning.RefillSeconds);
		}
	}
	return bActive && !bWasActive;
}

UShipSystemsComponent::UShipSystemsComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

FString UShipSystemsComponent::ShipName() const
{
	return GetOwner() ? GetOwner()->GetName() : GetName();
}

float UShipSystemsComponent::GetMasterModeSwitchProgress(float SwitchSeconds) const
{
	return bMasterModeSwitching ? FMath::Clamp(MasterModeTimer / FMath::Max(SwitchSeconds, 0.01f), 0.f, 1.f) : 0.f;
}

bool UShipSystemsComponent::RequestMasterMode(EMasterMode Mode)
{
	if (Mode == MasterMode)
	{
		// Already there: cancels a switch the other way.
		bMasterModeSwitching = false;
		MasterModeTimer = 0.f;
		return false;
	}
	if (bMasterModeSwitching && Mode == PendingMasterMode)
	{
		return false;
	}
	PendingMasterMode = Mode;
	bMasterModeSwitching = true;
	MasterModeTimer = 0.f;
	return true;
}

bool UShipSystemsComponent::UpdateMasterMode(float DeltaSeconds, float SwitchSeconds)
{
	if (!bMasterModeSwitching)
	{
		return false;
	}
	MasterModeTimer += DeltaSeconds;
	if (MasterModeTimer < SwitchSeconds)
	{
		return false;
	}
	MasterMode = PendingMasterMode;
	bMasterModeSwitching = false;
	MasterModeTimer = 0.f;
	UE_LOG(LogSpaceship, Log, TEXT("%s: master mode %s"), *ShipName(), MasterMode == EMasterMode::NAV ? TEXT("NAV") : TEXT("SCM"));
	return true;
}

void UShipSystemsComponent::FinishMasterModeSwitch()
{
	if (bMasterModeSwitching)
	{
		MasterMode = PendingMasterMode;
		bMasterModeSwitching = false;
		MasterModeTimer = 0.f;
	}
}

void UShipSystemsComponent::ForceMasterMode(EMasterMode Mode)
{
	MasterMode = Mode;
	bMasterModeSwitching = false;
}

void UShipSystemsComponent::SetSpeedLimiter(float Fraction, float MinFraction)
{
	SpeedLimiterFraction = FMath::Clamp(Fraction, FMath::Min(MinFraction, 1.f), 1.f);
}

void UShipSystemsComponent::AdjustSpeedLimiter(float Notches, float Step, float MinFraction)
{
	// Snapped to whole steps, so a few notches up and down land on round numbers again.
	const float Steps = FMath::RoundToFloat(SpeedLimiterFraction / Step) + Notches;
	SetSpeedLimiter(Steps * Step, MinFraction);
}

bool UShipSystemsComponent::UpdateBoost(float DeltaSeconds, bool bAllowed, const FShipReserve::FTuning& Tuning)
{
	return Boost.Update(DeltaSeconds, bAllowed, Tuning);
}

bool UShipSystemsComponent::UpdateAfterburner(float DeltaSeconds, bool bAllowed, const FShipReserve::FTuning& Tuning,
	float SpoolSeconds, float FadeSeconds)
{
	const bool bLit = Afterburner.Update(DeltaSeconds, bAllowed, Tuning);
	AfterburnerBlend = Afterburner.bActive
		? FMath::Min(1.f, AfterburnerBlend + DeltaSeconds / SpoolSeconds)
		: FMath::Max(0.f, AfterburnerBlend - DeltaSeconds / FadeSeconds);
	return bLit;
}

void UShipSystemsComponent::CutBoostAndAfterburner()
{
	Boost.bActive = false;
	Afterburner.bActive = false;
}

void UShipSystemsComponent::SetVtol(bool bOn)
{
	if (bOn == bVtolMode)
	{
		return;
	}
	// NAV is for travel: asking for VTOL there does nothing, and switching to NAV drops it (UpdateVtol).
	if (bOn && MasterMode != EMasterMode::SCM)
	{
		UE_LOG(LogSpaceship, Log, TEXT("%s: VTOL refused, SCM only"), *ShipName());
		return;
	}
	// SCM only, so never in a quantum jump (NAV).
	bVtolMode = bOn;
	UE_LOG(LogSpaceship, Log, TEXT("%s: VTOL %s"), *ShipName(), bOn ? TEXT("on") : TEXT("off"));
}

void UShipSystemsComponent::UpdateVtol(float DeltaSeconds, float TransitionSeconds)
{
	if (bVtolMode && MasterMode != EMasterMode::SCM)
	{
		bVtolMode = false;
		UE_LOG(LogSpaceship, Log, TEXT("%s: VTOL off (NAV)"), *ShipName());
	}
	const float Target = bVtolMode ? 1.f : 0.f;
	const float Step = DeltaSeconds / FMath::Max(TransitionSeconds, 0.01f);
	VtolBlend = FMath::Clamp(VtolBlend + FMath::Clamp(Target - VtolBlend, -Step, Step), 0.f, 1.f);
}
