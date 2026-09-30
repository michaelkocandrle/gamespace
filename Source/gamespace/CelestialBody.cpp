// Copyright Epic Games, Inc. All Rights Reserved.

#include "CelestialBody.h"

#include "Components/StaticMeshComponent.h"
#include "EngineUtils.h"
#include "SpaceCelestialRegistrySubsystem.h"

ACelestialBody::ACelestialBody()
{
	PrimaryActorTick.bCanEverTick = false;

	Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
	SetRootComponent(Body);
	Body->SetCollisionProfileName(TEXT("BlockAll"));
}

double ACelestialBody::GetSurfaceDistance(const FVector& Location) const
{
	const FBoxSphereBounds& Bounds = Body->Bounds;
	return FVector::Dist(Location, Bounds.Origin) - Bounds.SphereRadius;
}

bool ACelestialBody::SampleEnvironment(const FVector& /*Location*/, FCelestialEnvironment& /*OutEnvironment*/) const
{
	return false;
}

bool ACelestialBody::GetSurfaceFrame(const FVector& /*Location*/, double /*FootprintRadiusCm*/, FVector& /*OutSurfacePoint*/, FVector& /*OutNormal*/) const
{
	return false;
}

void ACelestialBody::PostRegisterAllComponents()
{
	Super::PostRegisterAllComponents();
	if (USpaceCelestialRegistrySubsystem* Registry = USpaceCelestialRegistrySubsystem::Get(GetWorld()))
	{
		Registry->Register(this);
	}
}

void ACelestialBody::PostUnregisterAllComponents()
{
	if (USpaceCelestialRegistrySubsystem* Registry = USpaceCelestialRegistrySubsystem::Get(GetWorld()))
	{
		Registry->Unregister(this);
	}
	Super::PostUnregisterAllComponents();
}

ACelestialBody* ACelestialBody::FindNearest(const UWorld* World, const FVector& Location, FCelestialEnvironment* OutEnvironment, bool* bOutHasEnvironment)
{
	ACelestialBody* Nearest = nullptr;
	if (USpaceCelestialRegistrySubsystem* Registry = USpaceCelestialRegistrySubsystem::Get(World))
	{
		// Every frame from the ship, the character, the sky and origin rebasing: the registry, not the world.
		Nearest = Registry->FindNearestCelestialBody(Location);
	}
	else
	{
		// Worlds without subsystems (editor previews): a walk.
		double NearestDistance = TNumericLimits<double>::Max();
		for (TActorIterator<ACelestialBody> It(World); It; ++It)
		{
			const double Distance = It->GetSurfaceDistance(Location);
			if (Distance < NearestDistance)
			{
				NearestDistance = Distance;
				Nearest = *It;
			}
		}
	}

	if (OutEnvironment || bOutHasEnvironment)
	{
		// The terrain sample only for callers that asked for it (the debug HUD and rebasing only want the body).
		FCelestialEnvironment Environment;
		const bool bHasEnvironment = Nearest && Nearest->SampleEnvironment(Location, Environment);
		if (OutEnvironment)
		{
			*OutEnvironment = Environment;
		}
		if (bOutHasEnvironment)
		{
			*bOutHasEnvironment = bHasEnvironment;
		}
	}
	return Nearest;
}
