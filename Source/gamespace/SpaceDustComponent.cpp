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
	// 0 the fade (distance and speed), 1 the speck's own brightness, 2 its length as a multiplier.
	NumCustomDataFloats = 3;

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
		// A dynamic instance: the shape of a speck is measured from the flight direction and the sizes,
		// and those change every frame (see UpdateDust).
		DustMaterial = UMaterialInstanceDynamic::Create(Material, this);
		SetMaterial(0, DustMaterial ? static_cast<UMaterialInterface*>(DustMaterial) : Material);
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
	const float SpeedAlpha = Intensity * float(FMath::Clamp((Speed - FadeInSpeed) / FMath::Max(3.0 * FadeInSpeed, 1.0), 0.0, 1.0))
		* (1.f - FMath::SmoothStep(FadeOutStartSpeed, FMath::Max(FadeOutEndSpeed, FadeOutStartSpeed + 1.f), float(Speed)));
	if (ParticleCount <= 0 || SpeedAlpha <= 0.001f)
	{
		HideDust();
		return;
	}

	const double Half = BoxHalfSizeCm;
	if (bCreated && Positions.Num() != ParticleCount)
	{
		// The count was changed (space.Dust ParticleCount while tuning): start the field again.
		ClearInstances();
		bCreated = false;
	}
	if (!bCreated)
	{
		FRandomStream Random(0x5DA7);
		Positions.SetNum(ParticleCount);
		Transforms.SetNum(ParticleCount);
		LengthScales.SetNum(ParticleCount);
		Brightnesses.SetNum(ParticleCount);
		for (int32 Index = 0; Index < ParticleCount; ++Index)
		{
			Positions[Index] = ViewLocation + FVector(Random.FRandRange(-Half, Half), Random.FRandRange(-Half, Half), Random.FRandRange(-Half, Half));
			Transforms[Index] = FTransform(Positions[Index] - ViewLocation);
			// Fixed for the speck's life, so it keeps its character as it wraps round the box.
			LengthScales[Index] = 1.f + Random.FRandRange(-LengthSpread, LengthSpread);
			// Cubed: most specks come out faint and a few bright, which is what dust looks like.
			Brightnesses[Index] = 1.f - BrightnessSpread * FMath::Pow(Random.FRand(), 3.f);
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
	const double Across = ParticleSizeCm / SpaceDust::CubeSizeCm;
	if (DustMaterial)
	{
		DustMaterial->SetVectorParameterValue(TEXT("DustDirection"), FLinearColor(Direction));
		DustMaterial->SetScalarParameterValue(TEXT("DustHalfLengthCm"), float(Length * 0.5));
		DustMaterial->SetScalarParameterValue(TEXT("DustHalfWidthCm"), ParticleSizeCm * 0.5f);
	}

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
		const double Stretched = FMath::Max(Length * double(LengthScales[Index]), double(ParticleSizeCm));
		Transforms[Index] = FTransform(Align, Relative, FVector(Stretched / SpaceDust::CubeSizeCm, Across, Across));

		// Fade out towards the box edge (no popping where specks wrap round) and near the camera. Near
		// is measured to the closest point of the streak, not its middle: a 15 m streak whose middle is
		// 8 m away can still have an end right at the lens, and that end is a white wedge across the
		// whole view (1.2 km/s in the chase view, 21. 9. 2026).
		const double Distance = Relative.Size();
		const double HalfStreak = 0.5 * Stretched;
		const FVector Closest = Relative - Direction * FMath::Clamp(FVector::DotProduct(Relative, Direction), -HalfStreak, HalfStreak);
		const float Fade = float((1.0 - FMath::SmoothStep(0.55 * Half, Half, Distance))
			* FMath::SmoothStep(80.0, 400.0, Closest.Size()));
		SetCustomDataValue(Index, 0, Fade * SpeedAlpha, false);
		SetCustomDataValue(Index, 1, Brightnesses[Index], false);
		SetCustomDataValue(Index, 2, LengthScales[Index], false);
	}
	BatchUpdateInstancesTransforms(0, Transforms, false, true, true);
}
