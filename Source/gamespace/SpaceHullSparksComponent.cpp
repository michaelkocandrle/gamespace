// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceHullSparksComponent.h"

#include "Engine/CollisionProfile.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "Misc/PackageName.h"
#include "UObject/ConstructorHelpers.h"

namespace HullSparks
{
	/** The space dust's material: a soft spindle along DustDirection, with fade, brightness and length per instance. */
	const TCHAR* const MaterialPackage = TEXT("/Game/Environments/Space/M_SpaceDust");
	const TCHAR* const MaterialPath = TEXT("/Game/Environments/Space/M_SpaceDust.M_SpaceDust");
	constexpr double CubeSizeCm = 100.0;
	constexpr int32 TraceAttempts = 900;
}

USpaceHullSparksComponent::USpaceHullSparksComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	// Positions are in the hull's space (attached to it), but never scaled with it.
	SetUsingAbsoluteScale(true);
	SetMobility(EComponentMobility::Movable);
	SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
	SetGenerateOverlapEvents(false);
	SetCastShadow(false);
	SetCanEverAffectNavigation(false);
	bAffectDistanceFieldLighting = false;
	bAffectDynamicIndirectLighting = false;
	SetVisibleInRayTracing(false);
	NumCustomDataFloats = 3;

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (Cube.Succeeded())
	{
		SetStaticMesh(Cube.Object);
	}
}

void USpaceHullSparksComponent::BeginPlay()
{
	Super::BeginPlay();
	UMaterialInterface* Material = FPackageName::DoesPackageExist(HullSparks::MaterialPackage)
		? LoadObject<UMaterialInterface>(nullptr, HullSparks::MaterialPath) : nullptr;
	if (Material)
	{
		SparkMaterial = UMaterialInstanceDynamic::Create(Material, this);
		SetMaterial(0, SparkMaterial);
	}
	SetVisibility(false);
}

void USpaceHullSparksComponent::FindSpawnPoints()
{
	Points.Reset();
	Normals.Reset();
	FrontPoints.Reset();
	BackPoints.Reset();
	// Attached to the hull, so the parent is the hull when SetHull has not run (no BeginPlay: tests).
	UPrimitiveComponent* HullComponent = Hull.IsValid() ? Hull.Get() : Cast<UPrimitiveComponent>(GetAttachParent());
	if (!HullComponent)
	{
		return;
	}
	const FBoxSphereBounds HullBounds = HullComponent->Bounds;
	const FVector Centre = HullBounds.Origin;
	const double Reach = HullBounds.SphereRadius * 1.5;
	FRandomStream Stream(0x7E11);

	// Trace the hull's collision from outside towards the middle, from every side.
	FCollisionQueryParams Params(TEXT("HullSparks"), false);
	for (int32 Attempt = 0; Attempt < HullSparks::TraceAttempts; ++Attempt)
	{
		const FVector Dir = Stream.GetUnitVector();
		FHitResult Hit;
		if (HullComponent->LineTraceComponent(Hit, Centre + Dir * Reach, Centre, Params) && Hit.bBlockingHit)
		{
			Points.Add(GetComponentTransform().InverseTransformPosition(Hit.ImpactPoint));
			Normals.Add(GetComponentTransform().InverseTransformVectorNoScale(Hit.ImpactNormal));
		}
	}
	bPointsFromCollision = Points.Num() >= 32;
	if (!bPointsFromCollision)
	{
		// No collision to trace: a shell of the bounds, a little inside the box so it hugs the ship.
		Points.Reset();
		Normals.Reset();
		const FVector Extent = HullBounds.BoxExtent * 0.85;
		for (int32 Index = 0; Index < 400; ++Index)
		{
			const FVector Dir = Stream.GetUnitVector();
			Points.Add(GetComponentTransform().InverseTransformPosition(Centre + Dir * Extent));
			Normals.Add(GetComponentTransform().InverseTransformVectorNoScale(Dir));
		}
	}
	for (int32 Index = 0; Index < Points.Num(); ++Index)
	{
		(Points[Index].X > 0.0 ? FrontPoints : BackPoints).Add(Index);
	}
}

int32 USpaceHullSparksComponent::DebugGetSpawnPointCount(bool& bOutFromCollision)
{
	if (Points.Num() == 0)
	{
		FindSpawnPoints();
	}
	bOutFromCollision = bPointsFromCollision;
	return Points.Num();
}

void USpaceHullSparksComponent::Respawn(FSpark& Spark, bool bRandomAge)
{
	const TArray<int32>& From = (Random.FRand() < NoseBias && FrontPoints.Num() > 0) || BackPoints.Num() == 0 ? FrontPoints : BackPoints;
	Spark.Point = From.Num() > 0 ? From[Random.RandHelper(From.Num())] : 0;
	Spark.Life = Random.FRandRange(MinLifeSeconds, FMath::Max(MinLifeSeconds, MaxLifeSeconds));
	Spark.Age = bRandomAge ? Random.FRandRange(0.f, Spark.Life) : 0.f;
	Spark.Pace = Random.FRandRange(0.6f, 1.4f);
	// Cubed: most faint, a few bright.
	Spark.Brightness = 1.f - 0.8f * FMath::Pow(Random.FRand(), 3.f);
	Spark.Length = Random.FRandRange(0.4f, 1.3f);
}

void USpaceHullSparksComponent::UpdateSparks(float DeltaSeconds, float Speed, float Quantum, const FVector& ViewLocation)
{
	const float FlightAlpha = FMath::SmoothStep(FlightFadeInSpeed, FMath::Max(FlightFullSpeed, FlightFadeInSpeed + 1.f), Speed) * (1.f - Quantum);
	const float Active = FMath::Lerp(float(FlightCount) * FMath::Min(FlightAlpha * 2.f, 1.f), float(QuantumCount), Quantum);
	const int32 ActiveCount = FMath::CeilToInt(Active);
	if (!SparkMaterial || ActiveCount <= 0 || (Quantum <= 0.001f && FlightAlpha <= 0.001f))
	{
		if (!bHidden)
		{
			SetVisibility(false);
			bHidden = true;
		}
		return;
	}
	if (Points.Num() == 0)
	{
		FindSpawnPoints();
		if (Points.Num() == 0)
		{
			return;
		}
	}

	const int32 Pool = FMath::Max(QuantumCount, FlightCount);
	if (Sparks.Num() != Pool)
	{
		ClearInstances();
		Sparks.SetNum(Pool);
		Transforms.SetNum(Pool);
		for (FSpark& Spark : Sparks)
		{
			Respawn(Spark, true);
		}
		for (int32 Index = 0; Index < Pool; ++Index)
		{
			Transforms[Index] = FTransform::Identity;
		}
		AddInstances(Transforms, false, false, false);
	}

	// White in normal flight, blue in a jump; the colour carries the brightness.
	const FLinearColor Colour = FMath::Lerp(FlightColor * FlightBrightness * FlightAlpha, QuantumColor * QuantumBrightness, Quantum);
	const float Flow = FMath::Lerp(FMath::Min(Speed * 0.5f, FlightFlowSpeed), QuantumFlowSpeed, Quantum);
	const float BaseLength = FMath::Lerp(FlightLengthCm, QuantumLengthCm, Quantum);
	SparkMaterial->SetVectorParameterValue(TEXT("DustDirection"), FLinearColor(GetComponentQuat().GetForwardVector()));
	SparkMaterial->SetScalarParameterValue(TEXT("DustHalfLengthCm"), BaseLength * 0.5f);
	SparkMaterial->SetScalarParameterValue(TEXT("DustHalfWidthCm"), ThicknessCm * 0.5f);
	SparkMaterial->SetVectorParameterValue(TEXT("DustColor"), Colour);
	SparkMaterial->SetScalarParameterValue(TEXT("DustBrightness"), 1.f);

	const FTransform& ToWorld = GetComponentTransform();
	const double Across = ThicknessCm / HullSparks::CubeSizeCm;
	for (int32 Index = 0; Index < Sparks.Num(); ++Index)
	{
		FSpark& Spark = Sparks[Index];
		Spark.Age += DeltaSeconds * Spark.Pace;
		if (Spark.Age >= Spark.Life)
		{
			Respawn(Spark, false);
		}
		const float T = Spark.Age / FMath::Max(Spark.Life, 0.01f);
		const float Travel = Flow * Spark.Age;
		const FVector Normal = Normals.IsValidIndex(Spark.Point) ? Normals[Spark.Point] : FVector::UpVector;
		// Streams back along the ship and lifts a little off the surface as it goes.
		const FVector Local = Points[Spark.Point] + Normal * (ThicknessCm * 3.0 + Travel * Spread) - FVector::ForwardVector * Travel;
		const double Length = BaseLength * Spark.Length;
		Transforms[Index] = FTransform(FQuat::Identity, Local, FVector(Length / HullSparks::CubeSizeCm, Across, Across));

		float Fade = Index < ActiveCount ? FMath::SmoothStep(0.f, 0.15f, T) * FMath::Pow(1.f - T, 1.5f) : 0.f;
		// Nothing on the lens (the cockpit's eye is inside the hull's bounds).
		// 5-12 m: from the cockpit the sparks off the canopy frame crossed the glass as thick bars.
		Fade *= float(FMath::SmoothStep(500.0, 1200.0, FVector::Dist(ToWorld.TransformPosition(Local), ViewLocation)));
		SetCustomDataValue(Index, 0, Fade, false);
		SetCustomDataValue(Index, 1, Spark.Brightness, false);
		SetCustomDataValue(Index, 2, Spark.Length, false);
	}
	BatchUpdateInstancesTransforms(0, Transforms, false, true, true);

	if (bHidden)
	{
		SetVisibility(true);
		bHidden = false;
	}
}
