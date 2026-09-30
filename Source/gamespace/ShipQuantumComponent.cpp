// Copyright Epic Games, Inc. All Rights Reserved.

#include "ShipQuantumComponent.h"

#include "CelestialBody.h"
#include "DistantBody.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "SpaceCelestialRegistrySubsystem.h"

namespace ShipQuantum
{
	/** A body the quantum drive can jump to. */
	struct FBody
	{
		AActor* Actor = nullptr;
		FText Name;
		FVector Centre = FVector::ZeroVector;
		double RadiusCm = 0.0;
	};

	/**
	 * Every body in the level: the terrain planets (ACelestialBody, radius measured towards Location, so
	 * it is the terrain's there) and the distant ones (ADistantBody: moons, the gas giant).
	 */
	void Gather(const UWorld* World, const FVector& Location, TArray<FBody>& OutBodies)
	{
		OutBodies.Reset();
		if (!World)
		{
			return;
		}
		auto AddCelestial = [&Location, &OutBodies](ACelestialBody& Body)
		{
			const FVector Centre = Body.GetActorLocation();
			const double Radius = FVector::Dist(Location, Centre) - Body.GetSurfaceDistance(Location);
			OutBodies.Add({ &Body, Body.GetDisplayName().IsEmpty() ? FText::FromString(Body.GetName()) : Body.GetDisplayName(), Centre, FMath::Max(Radius, 1.0) });
		};
		auto AddDistant = [&OutBodies](ADistantBody& Body)
		{
			OutBodies.Add({ &Body, Body.GetDisplayName().IsEmpty() ? FText::FromString(Body.GetName()) : Body.GetDisplayName(),
				Body.GetActorLocation(), double(Body.GetRadiusKm()) * 100000.0 });
		};
		// Twice a frame in NAV (target and obstruction): the world's body registry, not a walk of every actor.
		if (USpaceCelestialRegistrySubsystem* Registry = USpaceCelestialRegistrySubsystem::Get(World))
		{
			Registry->ForEachCelestialBody(AddCelestial);
			Registry->ForEachDistantBody(AddDistant);
			return;
		}
		for (TActorIterator<ACelestialBody> It(World); It; ++It)
		{
			AddCelestial(**It);
		}
		for (TActorIterator<ADistantBody> It(World); It; ++It)
		{
			AddDistant(**It);
		}
	}
}

UShipQuantumComponent::UShipQuantumComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

float UShipQuantumComponent::GetCooling(float CooldownSeconds) const
{
	return State == EQuantumState::Cooling
		? FMath::Clamp(1.f - CooldownTimer / FMath::Max(CooldownSeconds, 0.01f), 0.f, 1.f) : 1.f;
}

float UShipQuantumComponent::GetTravelProgress() const
{
	return State == EQuantumState::Traveling && JumpLengthCm > 1.0
		? float(FMath::Clamp(1.0 - TargetDistanceCm / JumpLengthCm, 0.0, 1.0)) : 0.f;
}

float UShipQuantumComponent::GetEngageHold(float EngageHoldSeconds) const
{
	return FMath::Clamp(EngageTimer / FMath::Max(EngageHoldSeconds, 0.01f), 0.f, 1.f);
}

void UShipQuantumComponent::SetEngageHeld(bool bHeld)
{
	bEngageHeld = bHeld;
	if (!bHeld)
	{
		EngageTimer = 0.f;
	}
}

void UShipQuantumComponent::UpdateTarget(const FVector& Location, const FVector& Nose, const FShipQuantumRules& Rules)
{
	TArray<ShipQuantum::FBody> Bodies;
	ShipQuantum::Gather(GetWorld(), Location, Bodies);

	// In a jump the destination is fixed; otherwise it is the body closest to the nose, within QuantumPickDeg.
	const ShipQuantum::FBody* Picked = nullptr;
	if (State == EQuantumState::Traveling)
	{
		Picked = Bodies.FindByPredicate([this](const ShipQuantum::FBody& Body) { return Body.Actor == Target.Get(); });
	}
	else
	{
		double BestCos = FMath::Cos(FMath::DegreesToRadians(double(Rules.PickDeg)));
		for (const ShipQuantum::FBody& Body : Bodies)
		{
			const double Cos = FVector::DotProduct((Body.Centre - Location).GetSafeNormal(), Nose);
			if (Cos > BestCos)
			{
				BestCos = Cos;
				Picked = &Body;
			}
		}
	}

	if (!Picked)
	{
		Target.Reset();
		TargetName = FText::GetEmpty();
		TargetDistanceCm = 0.0;
		return;
	}
	if (Target.Get() != Picked->Actor)
	{
		// A new destination: calibration was for the old one.
		Calibration = 0.f;
	}
	Target = Picked->Actor;
	TargetName = Picked->Name;
	TargetCentre = Picked->Centre;
	TargetRadiusCm = Picked->RadiusCm;
	const double ArrivalFromCentre = Picked->RadiusCm + FShipFlightModel::QuantumArrivalAltitude(Picked->RadiusCm, Rules.Drive);
	TargetDistanceCm = FMath::Max(FVector::Dist(Location, Picked->Centre) - ArrivalFromCentre, 0.0);
}

EQuantumBlocker UShipQuantumComponent::Evaluate(const FShipQuantumContext& Context, const FShipQuantumRules& Rules) const
{
	if (Context.bLanded)
	{
		return EQuantumBlocker::Landed;
	}
	if (!Context.bInNav)
	{
		return EQuantumBlocker::NeedsNav;
	}
	if (!Target.IsValid())
	{
		return EQuantumBlocker::NoTarget;
	}
	if (TargetDistanceCm < double(Rules.MinJumpKm) * 100000.0)
	{
		return EQuantumBlocker::TooClose;
	}
	if (FShipFlightModel::QuantumFuelUse(TargetDistanceCm, Rules.Drive) > Fuel)
	{
		return EQuantumBlocker::NoFuel;
	}
	// Anything on the way to the arrival point, the destination itself included (the far side of a
	// planet). Each body counts with its arrival shell, so the jump never skims a surface.
	const FVector Location = Context.Location;
	const FVector Arrival = TargetCentre + (Location - TargetCentre).GetSafeNormal()
		* (TargetRadiusCm + FShipFlightModel::QuantumArrivalAltitude(TargetRadiusCm, Rules.Drive));
	TArray<ShipQuantum::FBody> Bodies;
	ShipQuantum::Gather(GetWorld(), Location, Bodies);
	for (const ShipQuantum::FBody& Body : Bodies)
	{
		// The body the ship is leaving does not block: the path starts above it and heads away.
		const double Clearance = Body.Actor == Target.Get() ? Body.RadiusCm * 0.99 : Body.RadiusCm;
		if (FVector::Dist(Location, Body.Centre) > Body.RadiusCm * 1.01
			&& FShipFlightModel::SegmentHitsSphere(Location, Arrival, Body.Centre, Clearance))
		{
			return EQuantumBlocker::Obstructed;
		}
	}
	return EQuantumBlocker::None;
}

UShipQuantumComponent::FFrame UShipQuantumComponent::Update(float DeltaSeconds, const FShipQuantumContext& Context,
	const FShipQuantumRules& Rules)
{
	FFrame Frame;
	UpdateTarget(Context.Location, Context.Nose, Rules);

	if (State == EQuantumState::Traveling)
	{
		return Frame;  // the pawn's UpdateQuantumTravel flies it and ends it
	}
	if (State == EQuantumState::Cooling)
	{
		CooldownTimer = FMath::Max(0.f, CooldownTimer - DeltaSeconds);
	}

	Blocker = Evaluate(Context, Rules);
	const bool bSpooling = Blocker != EQuantumBlocker::NeedsNav && Blocker != EQuantumBlocker::Landed
		&& Blocker != EQuantumBlocker::NoTarget;
	// The spool runs in NAV with a destination and holds while blocked; it winds down in SCM.
	Spool = bSpooling
		? FMath::Min(1.f, Spool + DeltaSeconds / FMath::Max(Rules.SpoolSeconds, 0.01f))
		: FMath::Max(0.f, Spool - DeltaSeconds / FMath::Max(Rules.SpoolSeconds, 0.01f));

	// Calibration needs the nose on the destination and falls back fast when it leaves.
	const bool bAligned = Target.IsValid()
		&& FVector::DotProduct((TargetCentre - Context.Location).GetSafeNormal(), Context.Nose)
			>= FMath::Cos(FMath::DegreesToRadians(double(Rules.AlignDeg)));
	Calibration = bSpooling && bAligned && Blocker == EQuantumBlocker::None
		? FMath::Min(1.f, Calibration + DeltaSeconds / FMath::Max(Rules.CalibrationSeconds, 0.01f))
		: FMath::Max(0.f, Calibration - 2.f * DeltaSeconds / FMath::Max(Rules.CalibrationSeconds, 0.01f));

	const bool bCool = State != EQuantumState::Cooling || CooldownTimer <= 0.f;
	if (!bCool)
	{
		State = EQuantumState::Cooling;
	}
	else if (!bSpooling)
	{
		State = EQuantumState::Idle;
	}
	else if (Spool >= 1.f && Calibration >= 1.f && Blocker == EQuantumBlocker::None && bAligned)
	{
		State = EQuantumState::Ready;
	}
	else
	{
		State = EQuantumState::Charging;
	}

	// Engage: the button held for QuantumEngageHoldSeconds while ready.
	if (bEngageHeld && State == EQuantumState::Ready)
	{
		Frame.bChargeStarted = EngageTimer <= 0.f;
		EngageTimer += DeltaSeconds;
		Frame.bEngage = EngageTimer >= Rules.EngageHoldSeconds;
	}
	else if (!bEngageHeld)
	{
		EngageTimer = 0.f;
	}
	return Frame;
}

void UShipQuantumComponent::BeginJump(const FShipQuantumRules& Rules)
{
	State = EQuantumState::Traveling;
	Blocker = EQuantumBlocker::None;
	EngageTimer = 0.f;
	JumpLengthCm = FMath::Max(TargetDistanceCm, 1.0);
	TravelSeconds = 0.f;
	Fuel = FMath::Max(0.f, Fuel - FShipFlightModel::QuantumFuelUse(TargetDistanceCm, Rules.Drive));
}

void UShipQuantumComponent::EndJump(EQuantumBlocker Reason, const FShipQuantumRules& Rules)
{
	State = EQuantumState::Cooling;
	CooldownTimer = Rules.CooldownSeconds;
	Blocker = Reason;
	Spool = 0.f;
	Calibration = 0.f;
	EngageTimer = 0.f;
}

bool UShipQuantumComponent::StepTravel(float DeltaSeconds, const FVector& Location, double CurrentSpeed,
	const FShipQuantumRules& Rules, FTravelStep& OutStep)
{
	if (!Target.IsValid())
	{
		return false;
	}
	OutStep.Direction = (TargetCentre - Location).GetSafeNormal();
	OutStep.RemainingCm = TargetDistanceCm;
	TravelSeconds += DeltaSeconds;
	OutStep.Speed = FShipFlightModel::QuantumSpeedAt(OutStep.RemainingCm, CurrentSpeed, DeltaSeconds, TravelSeconds, Rules.Drive);
	OutStep.StepCm = OutStep.Speed * DeltaSeconds;
	OutStep.bArrives = OutStep.StepCm >= OutStep.RemainingCm;
	if (OutStep.bArrives)
	{
		TargetDistanceCm = 0.0;
	}
	return true;
}

AActor* UShipQuantumComponent::FindDestination(const FString& Name, const FVector& Location, const FVector& Nose) const
{
	TArray<ShipQuantum::FBody> Bodies;
	ShipQuantum::Gather(GetWorld(), Location, Bodies);
	const ShipQuantum::FBody* Picked = nullptr;
	double BestCos = -2.0;
	for (const ShipQuantum::FBody& Body : Bodies)
	{
		if (!Name.IsEmpty())
		{
			if (Body.Name.ToString().StartsWith(Name) || Body.Actor->GetName().Contains(Name))
			{
				Picked = &Body;
				break;
			}
			continue;
		}
		const double Cos = FVector::DotProduct((Body.Centre - Location).GetSafeNormal(), Nose);
		if (Cos > BestCos)
		{
			BestCos = Cos;
			Picked = &Body;
		}
	}
	return Picked ? Picked->Actor : nullptr;
}
