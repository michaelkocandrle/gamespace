// Copyright Epic Games, Inc. All Rights Reserved.

#include "DistantBody.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/CollisionProfile.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "UObject/ConstructorHelpers.h"

namespace DistantBodyDefaults
{
	/** SM_PlanetSphere and the engine sphere stand-in are both scaled from this radius. */
	constexpr double SphereMeshRadiusCm = 100.0;
	/** /Engine/BasicShapes/Plane is 100 cm across. */
	constexpr double PlaneHalfSizeCm = 50.0;
	constexpr double CmPerKm = 100000.0;
}

ADistantBody::ADistantBody()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_PrePhysics;

	Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
	SetRootComponent(Body);
	Body->SetMobility(EComponentMobility::Movable);
	// Kilometres of shadow caster would only cost shadow-map resolution near the player.
	Body->SetCastShadow(false);
	Body->bAffectDistanceFieldLighting = false;
	Body->SetCollisionProfileName(UCollisionProfile::BlockAll_ProfileName);

	Rings = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Rings"));
	Rings->SetupAttachment(Body);
	Rings->SetCastShadow(false);
	Rings->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
	// Scaled independently of the body sphere.
	Rings->SetUsingAbsoluteScale(true);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (Sphere.Succeeded())
	{
		Body->SetStaticMesh(Sphere.Object);
	}
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Plane(TEXT("/Engine/BasicShapes/Plane.Plane"));
	if (Plane.Succeeded())
	{
		Rings->SetStaticMesh(Plane.Object);
	}
}

void ADistantBody::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	// The engine sphere has a 50 cm radius, SM_PlanetSphere 100 cm: scale by the mesh's own bounds.
	const double MeshRadius = Body->GetStaticMesh() ? FMath::Max(Body->GetStaticMesh()->GetBounds().BoxExtent.X, 1.0) : DistantBodyDefaults::SphereMeshRadiusCm;
	SetActorScale3D(FVector(RadiusKm * DistantBodyDefaults::CmPerKm / MeshRadius));

	const bool bRings = RingOuterRadiusKm > RadiusKm;
	Rings->SetVisibility(bRings);
	Rings->SetWorldScale3D(FVector(RingOuterRadiusKm * DistantBodyDefaults::CmPerKm / DistantBodyDefaults::PlaneHalfSizeCm));
	Body->SetRelativeRotation(FRotator(0.f, 0.f, AxialTiltDeg));

	if (OrbitCenter && OrbitRadiusKm > 0.f)
	{
		PlaceOnOrbit(0.0);
	}
}

FVector ADistantBody::ComputeOrbitOffset(double TimeSeconds) const
{
	const double Angle = FMath::DegreesToRadians(OrbitPhaseDeg) + UE_TWO_PI * TimeSeconds / FMath::Max(OrbitPeriodSeconds, 1.f);
	const FVector InPlane(FMath::Cos(Angle), FMath::Sin(Angle), 0.0);
	// Tilt the orbit about X, then turn the tilted plane about Z to its node direction.
	const FQuat Orientation = FQuat(FVector::UpVector, FMath::DegreesToRadians(OrbitNodeDeg))
		* FQuat(FVector::ForwardVector, FMath::DegreesToRadians(OrbitInclinationDeg));
	return Orientation.RotateVector(InPlane) * (OrbitRadiusKm * DistantBodyDefaults::CmPerKm);
}

void ADistantBody::PlaceOnOrbit(double TimeSeconds)
{
	SetActorLocation(OrbitCenter->GetActorLocation() + ComputeOrbitOffset(TimeSeconds));
}

void ADistantBody::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const double Time = GetWorld()->GetTimeSeconds();
	if (OrbitCenter && OrbitRadiusKm > 0.f)
	{
		// Relative to the centre's current location, so world origin rebasing needs no special care.
		PlaceOnOrbit(Time);
	}
	if (SpinPeriodSeconds > 0.f)
	{
		// Spin about the tilted axis; the rings stay put, they are a flat disc anyway.
		const float Spin = float(FMath::Fmod(Time / SpinPeriodSeconds, 1.0) * 360.0);
		Body->SetRelativeRotation(FQuat(FVector::ForwardVector, FMath::DegreesToRadians(AxialTiltDeg)) * FQuat(FVector::UpVector, FMath::DegreesToRadians(Spin)));
		Rings->SetWorldRotation(FQuat(FVector::ForwardVector, FMath::DegreesToRadians(AxialTiltDeg)));
	}
}
