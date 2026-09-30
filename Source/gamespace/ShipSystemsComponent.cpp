// Copyright Epic Games, Inc. All Rights Reserved.

#include "ShipSystemsComponent.h"

#include "GameFramework/Actor.h"
#include "SpaceshipLog.h"

UShipSystemsComponent::UShipSystemsComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

FString UShipSystemsComponent::ShipName() const
{
	return GetOwner() ? GetOwner()->GetName() : GetName();
}

void UShipSystemsComponent::SetVtol(bool bOn, bool bInScm)
{
	if (bOn == bVtolMode)
	{
		return;
	}
	// NAV is for travel: asking for VTOL there does nothing, and switching to NAV drops it (UpdateVtol).
	if (bOn && !bInScm)
	{
		UE_LOG(LogSpaceship, Log, TEXT("%s: VTOL refused, SCM only"), *ShipName());
		return;
	}
	// SCM only, so never in a quantum jump (NAV).
	bVtolMode = bOn;
	UE_LOG(LogSpaceship, Log, TEXT("%s: VTOL %s"), *ShipName(), bOn ? TEXT("on") : TEXT("off"));
}

void UShipSystemsComponent::UpdateVtol(float DeltaSeconds, bool bInScm, float TransitionSeconds)
{
	if (bVtolMode && !bInScm)
	{
		bVtolMode = false;
		UE_LOG(LogSpaceship, Log, TEXT("%s: VTOL off (NAV)"), *ShipName());
	}
	const float Target = bVtolMode ? 1.f : 0.f;
	const float Step = DeltaSeconds / FMath::Max(TransitionSeconds, 0.01f);
	VtolBlend = FMath::Clamp(VtolBlend + FMath::Clamp(Target - VtolBlend, -Step, Step), 0.f, 1.f);
}
