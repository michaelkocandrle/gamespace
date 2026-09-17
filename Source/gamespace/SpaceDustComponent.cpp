// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceDustComponent.h"

#include "Engine/CollisionProfile.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "Misc/PackageName.h"
#include "UObject/ConstructorHelpers.h"

namespace SpaceDust
{
	/** Built by Tools/Assets/build_space_scene.py. Without it the specks would be opaque grey cubes, so none are shown. */
	const TCHAR* const MaterialPath = TEXT("/Game/Environments/Space/M_SpaceDust.M_SpaceDust");

	/** /Engine/BasicShapes/Cube is 100 cm along each axis. */
	constexpr double CubeSizeCm = 100.0;
}

USpaceDustComponent::USpaceDustComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	// Positioned in world space by UpdateDust, whatever it is attached to.
	SetUsingAbsoluteLocation(true);
	SetUsingAbsoluteRotation(true);
	SetUsingAbsoluteScale(true);
	SetMobility(EComponentMobility::Movable);
	SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
	SetGenerateOverlapEvents(false);
	SetCastShadow(false);
	SetCanEverAffectNavigation(false);
	bAffectDistanceFieldLighting = false;
	bAffectDynamicIndirectLighting = false;
	SetVisibleInRayTracing(false);
	NumCustomDataFloats = 1;

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (Cube.Succeeded())
	{
		SetStaticMesh(Cube.Object);
	}
}

void USpaceDustComponent::BeginPlay()
{
	Super::BeginPlay();
	// Loaded here rather than with a constructor finder: before the scene script has run once the
	// asset does not exist, and a finder would log an error on every editor start.
	UMaterialInterface* Material = FPackageName::DoesPackageExist(TEXT("/Game/Environments/Space/M_SpaceDust"))
		? LoadObject<UMaterialInterface>(nullptr, SpaceDust::MaterialPath)
		: nullptr;
	if (Material)
	{
		SetMaterial(0, Material);
	}
	else
	{
		ParticleCount = 0;
	}
	SetVisibility(false);
}

void USpaceDustComponent::HideDust()
{
	if (!bHidden)
	{
		SetVisibility(false);
		bHidden = true;
	}
}

void USpaceDustComponent::UpdateDust(const FVector& ViewLocation, const FVector& Velocity, float Intensity)
{
	const double Speed = Velocity.Size();
	const float SpeedAlpha = Intensity * float(FMath::Clamp((Speed - FadeInSpeed) / FMath::Max(3.0 * FadeInSpeed, 1.0), 0.0, 1.0));
	if (ParticleCount <= 0 || SpeedAlpha <= 0.001f)
	{
		HideDust();
		return;
	}

	const double Half = BoxHalfSizeCm;
	if (!bCreated)
	{
		FRandomStream Random(0x5DA7);
		Positions.SetNum(ParticleCount);
		Transforms.SetNum(ParticleCount);
		for (int32 Index = 0; Index < ParticleCount; ++Index)
		{
			Positions[Index] = ViewLocation + FVector(Random.FRandRange(-Half, Half), Random.FRandRange(-Half, Half), Random.FRandRange(-Half, Half));
			Transforms[Index] = FTransform(Positions[Index] - ViewLocation);
		}
		SetWorldLocationAndRotation(ViewLocation, FQuat::Identity);
		AddInstances(Transforms, false, false, false);
		bCreated = true;
	}
	if (bHidden)
	{
		SetVisibility(true);
		bHidden = false;
	}

	SetWorldLocationAndRotation(ViewLocation, FQuat::Identity);
	const FVector Direction = Speed > 1.0 ? Velocity / Speed : FVector::ForwardVector;
	const FQuat Align = FRotationMatrix::MakeFromX(Direction).ToQuat();
	const double Length = FMath::Clamp(Speed * StreakSeconds, double(ParticleSizeCm), double(MaxStreakCm));
	const FVector Scale(Length / SpaceDust::CubeSizeCm, ParticleSizeCm / SpaceDust::CubeSizeCm, ParticleSizeCm / SpaceDust::CubeSizeCm);

	auto Wrap = [Half](double Value)
	{
		double Wrapped = FMath::Fmod(Value + Half, 2.0 * Half);
		if (Wrapped < 0.0)
		{
			Wrapped += 2.0 * Half;
		}
		return Wrapped - Half;
	};

	for (int32 Index = 0; Index < Positions.Num(); ++Index)
	{
		FVector Relative = Positions[Index] - ViewLocation;
		Relative.Set(Wrap(Relative.X), Wrap(Relative.Y), Wrap(Relative.Z));
		Positions[Index] = ViewLocation + Relative;
		Transforms[Index] = FTransform(Align, Relative, Scale);

		// Fade out towards the box edge (no popping where specks wrap round) and right at the camera.
		const double Distance = Relative.Size();
		const float Fade = float((1.0 - FMath::SmoothStep(0.55 * Half, Half, Distance)) * FMath::SmoothStep(80.0, 400.0, Distance));
		SetCustomDataValue(Index, 0, Fade * SpeedAlpha, false);
	}
	BatchUpdateInstancesTransforms(0, Transforms, false, true, true);
}
