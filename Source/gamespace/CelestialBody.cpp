// Copyright Epic Games, Inc. All Rights Reserved.

#include "CelestialBody.h"

#include "Components/StaticMeshComponent.h"

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
