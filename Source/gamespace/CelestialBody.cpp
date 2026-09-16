// Copyright Epic Games, Inc. All Rights Reserved.

#include "CelestialBody.h"

#include "Components/StaticMeshComponent.h"
#include "EngineUtils.h"

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

ACelestialBody* ACelestialBody::FindNearest(const UWorld* World, const FVector& Location, FCelestialEnvironment* OutEnvironment, bool* bOutHasEnvironment)
{
	ACelestialBody* Nearest = nullptr;
	double NearestDistance = TNumericLimits<double>::Max();
	// A handful of bodies at most, so a walk is cheaper than keeping a registry.
	for (TActorIterator<ACelestialBody> It(World); It; ++It)
	{
		const double Distance = It->GetSurfaceDistance(Location);
		if (Distance < NearestDistance)
		{
			NearestDistance = Distance;
			Nearest = *It;
		}
	}

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
	return Nearest;
}
