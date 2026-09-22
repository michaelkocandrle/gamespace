// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceHullSparksComponent.h"

#include "Engine/CollisionProfile.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "PhysicsEngine/BodySetup.h"
#include "Materials/MaterialInterface.h"
#include "Misc/PackageName.h"
#include "UObject/ConstructorHelpers.h"

namespace HullSparks
{
	/** M_HullSpark: a hot core in a faint halo along each instance's own direction (custom data 3-5). */
	const TCHAR* const MaterialPackage = TEXT("/Game/Environments/Space/M_HullSpark");
	const TCHAR* const MaterialPath = TEXT("/Game/Environments/Space/M_HullSpark.M_HullSpark");
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
	// 0 fade, 1 brightness (flickers). M_HullSpark measures the rest on the cube itself.
	NumCustomDataFloats = 2;
	// Over the quantum tunnel's fog (sort priority 0, fully opaque, centred on the camera): with equal
	// priorities the fog sorted after the sparks now and then and drew them over as black streaks.
	SetTranslucentSortPriority(20);

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
	FRandomStream Stream(0x7E11);

	// The hull's collision shapes (UCX hulls and boxes from Blender), read as geometry: from random
	// spots round the ship, the nearest point on them and its normal. Line traces against the hull
	// found nothing (the shapes are convex elements, and the tests run without a physics scene), so
	// the sparks came out of a box round the ship, in mid-air (22. 9. 2026).
	const UStaticMeshComponent* MeshComponent = Cast<UStaticMeshComponent>(HullComponent);
	const UBodySetup* Body = MeshComponent && MeshComponent->GetStaticMesh() ? MeshComponent->GetStaticMesh()->GetBodySetup() : nullptr;
	if (Body)
	{
		const FTransform BodyToWorld = HullComponent->GetComponentTransform();
		const FVector Extent = HullBounds.BoxExtent * 1.1;
		for (int32 Attempt = 0; Attempt < HullSparks::TraceAttempts; ++Attempt)
		{
			const FVector From = Centre + FVector(Stream.FRandRange(-1.f, 1.f), Stream.FRandRange(-1.f, 1.f), Stream.FRandRange(-1.f, 1.f)) * Extent;
			FVector Closest;
			FVector Normal;
			// 0 inside a shape: no surface to pour from there.
			if (Body->GetClosestPointAndNormal(From, BodyToWorld, Closest, Normal, true) > 1.f && !Normal.IsNearlyZero())
			{
				Points.Add(GetComponentTransform().InverseTransformPosition(Closest));
				Normals.Add(GetComponentTransform().InverseTransformVectorNoScale(Normal.GetSafeNormal()));
			}
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

void USpaceHullSparksComponent::MoveEmitter(FEmitter& Emitter)
{
	const TArray<int32>& From = (Random.FRand() < NoseBias && FrontPoints.Num() > 0) || BackPoints.Num() == 0 ? FrontPoints : BackPoints;
	Emitter.Point = From.Num() > 0 ? From[Random.RandHelper(From.Num())] : 0;
	Emitter.TimeLeft = Random.FRandRange(EmitterMinSeconds, FMath::Max(EmitterMinSeconds, EmitterMaxSeconds));
}

void USpaceHullSparksComponent::Respawn(FSpark& Spark, bool bRandomAge)
{
	Spark.Emitter = Emitters.Num() > 0 ? Random.RandHelper(Emitters.Num()) : 0;
	const int32 Point = Emitters.IsValidIndex(Spark.Emitter) ? Emitters[Spark.Emitter].Point : 0;
	const FVector Normal = Normals.IsValidIndex(Point) ? Normals[Point] : FVector::UpVector;
	FVector Side = FVector::CrossProduct(Normal, FVector::ForwardVector).GetSafeNormal();
	if (Side.IsNearlyZero())
	{
		Side = FVector::RightVector;
	}
	const FVector Up = FVector::CrossProduct(Normal, Side);
	// A tuft: all from one spot (a few cm apart), in a cone round the normal, a little backwards.
	Spark.Origin = (Points.IsValidIndex(Point) ? Points[Point] : FVector::ZeroVector) + Normal * 5.0
		+ Side * Random.FRandRange(-8.f, 8.f) + Up * Random.FRandRange(-8.f, 8.f);
	const FVector Dir = Normal * Random.FRandRange(0.3f, 1.f)
		+ (Side * Random.FRandRange(-1.f, 1.f) + Up * Random.FRandRange(-1.f, 1.f)) * ConeSpread
		- FVector::ForwardVector * Random.FRandRange(0.f, 0.6f);
	Spark.Velocity = Dir.GetSafeNormal(UE_SMALL_NUMBER, Normal) * BurstSpeed * Random.FRandRange(0.4f, 1.f);
	Spark.Life = Random.FRandRange(MinLifeSeconds, FMath::Max(MinLifeSeconds, MaxLifeSeconds));
	Spark.Age = bRandomAge ? Random.FRandRange(0.f, Spark.Life) : 0.f;
	// Cubed: most faint, a few bright.
	Spark.Brightness = 1.f - 0.8f * FMath::Pow(Random.FRand(), 3.f);
}

FVector USpaceHullSparksComponent::SparkAt(const FSpark& Spark, float Seconds, float Sweep) const
{
	const double T = FMath::Max(Seconds, 0.f);
	return Spark.Origin + Spark.Velocity * T - FVector::ForwardVector * (0.5 * Sweep * T * T);
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

	if (Emitters.Num() != EmitterCount)
	{
		Emitters.SetNum(EmitterCount);
		for (FEmitter& Emitter : Emitters)
		{
			MoveEmitter(Emitter);
		}
	}
	for (FEmitter& Emitter : Emitters)
	{
		Emitter.TimeLeft -= DeltaSeconds;
		if (Emitter.TimeLeft <= 0.f)
		{
			MoveEmitter(Emitter);
		}
	}

	const int32 Segments = FMath::Clamp(TrailSegments, 1, 12);
	const int32 Pool = FMath::Max(QuantumCount, FlightCount);
	if (Sparks.Num() != Pool || Transforms.Num() != Pool * Segments)
	{
		ClearInstances();
		Sparks.SetNum(Pool);
		for (FSpark& Spark : Sparks)
		{
			Respawn(Spark, true);
		}
		Transforms.Init(FTransform::Identity, Pool * Segments);
		AddInstances(Transforms, false, false, false);
	}

	// White in normal flight, blue in a jump; the colour carries the brightness.
	const FLinearColor Colour = FMath::Lerp(FlightColor * FlightBrightness * FlightAlpha, QuantumColor * QuantumBrightness, Quantum);
	const float Sweep = SweepBack * FMath::Max(Quantum, FlightAlpha);
	SparkMaterial->SetVectorParameterValue(TEXT("DustColor"), Colour);
	SparkMaterial->SetScalarParameterValue(TEXT("DustBrightness"), 1.f);

	const FTransform& ToWorld = GetComponentTransform();
	const float Step = TrailSeconds / float(Segments);
	for (int32 Index = 0; Index < Sparks.Num(); ++Index)
	{
		FSpark& Spark = Sparks[Index];
		Spark.Age += DeltaSeconds;
		if (Spark.Age >= Spark.Life)
		{
			Respawn(Spark, false);
		}
		const float T = Spark.Age / FMath::Max(Spark.Life, 0.01f);
		float SparkFade = Index < ActiveCount ? FMath::SmoothStep(0.f, 0.1f, T) * FMath::Pow(1.f - T, 1.5f) : 0.f;
		const FVector Head = SparkAt(Spark, Spark.Age, Sweep);
		// Nothing on the lens (the cockpit's eye is inside the hull's bounds).
		const double Distance = FVector::Dist(ToWorld.TransformPosition(Head), ViewLocation);
		SparkFade *= float(FMath::SmoothStep(double(CameraFadeNearCm), double(FMath::Max(CameraFadeFarCm, CameraFadeNearCm + 1.f)), Distance));
		// At least a pixel or so wide; drawn wider than the spark is, so dimmer.
		const double Width = FMath::Max(double(ThicknessCm), Distance * MinScreenThickness);
		const float Dim = float(FMath::Sqrt(ThicknessCm / Width));
		// Flicker every frame: sparks crackle, lines do not.
		const float Own = Spark.Brightness * Random.FRandRange(0.35f, 1.f) * Dim;

		FVector Newer = Head;
		for (int32 Segment = 0; Segment < Segments; ++Segment)
		{
			const int32 Instance = Index * Segments + Segment;
			const FVector Older = SparkAt(Spark, Spark.Age - Step * float(Segment + 1), Sweep);
			const FVector Along = Newer - Older;
			const double Length = Along.Size();
			const FVector Dir = Length > UE_KINDA_SMALL_NUMBER ? Along / Length : FVector::ForwardVector;
			// Overlap the joints so the chain reads as one curve (at 1.15 it was a dotted line).
			const double Drawn = Length * 1.5 + Width * 2.0;
			Transforms[Instance] = FTransform(FRotationMatrix::MakeFromX(Dir).ToQuat(), (Newer + Older) * 0.5,
				FVector(Drawn / HullSparks::CubeSizeCm, Width / HullSparks::CubeSizeCm, Width / HullSparks::CubeSizeCm));
			// Brightest at the head, thinning out towards the tail; nothing from before the spark was born.
			const float Fade = Length > 0.5 ? SparkFade * (1.f - float(Segment) / float(Segments)) : 0.f;
			SetCustomDataValue(Instance, 0, Fade, false);
			SetCustomDataValue(Instance, 1, Own, false);
			Newer = Older;
		}
	}
	BatchUpdateInstancesTransforms(0, Transforms, false, true, true);

	if (bHidden)
	{
		SetVisibility(true);
		bHidden = false;
	}
}
