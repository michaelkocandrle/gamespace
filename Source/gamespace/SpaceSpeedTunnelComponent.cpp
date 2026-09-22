// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceSpeedTunnelComponent.h"

#include "Components/DirectionalLightComponent.h"
#include "Components/PointLightComponent.h"
#include "UObject/UObjectIterator.h"
#include "Engine/CollisionProfile.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "Misc/PackageName.h"
#include "UObject/ConstructorHelpers.h"

namespace SpeedTunnel
{
	/** Built by Tools/Assets/build_space_scene.py. Without it the walls would be opaque grey cylinders, so none are shown. */
	const TCHAR* const MaterialPackage = TEXT("/Game/Environments/Space/M_SpeedTunnel");
	const TCHAR* const MaterialPath = TEXT("/Game/Environments/Space/M_SpeedTunnel.M_SpeedTunnel");
	const TCHAR* const BeaconPackage = TEXT("/Game/Environments/Space/M_QuantumBeacon");
	const TCHAR* const BeaconPath = TEXT("/Game/Environments/Space/M_QuantumBeacon.M_QuantumBeacon");
	const TCHAR* const FogPackage = TEXT("/Game/Environments/Space/M_QuantumFog");
	const TCHAR* const FogPath = TEXT("/Game/Environments/Space/M_QuantumFog.M_QuantumFog");
}

USpaceSpeedTunnelComponent::USpaceSpeedTunnelComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	// Positioned in world space by UpdateTunnel, whatever it is attached to.
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
	NumCustomDataFloats = 5;

	// Near and sparse, the main field, far with the beams, fog and flares (Tools/Shots/quantum_tune.json).
	Layers = {
		FSpeedTunnelLayer{2500.f, 1.f, 40.f, 0.f},
		FSpeedTunnelLayer{6000.f, 0.8f, 90.f, 0.5f},
		FSpeedTunnelLayer{15000.f, 0.6f, 160.f, 1.f},
	};

	// A hard reference, so the cooker packs it (engine content loaded by path would be missing).
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (Cylinder.Succeeded())
	{
		SetStaticMesh(Cylinder.Object);
	}
}

void USpaceSpeedTunnelComponent::BeginPlay()
{
	Super::BeginPlay();
	// Loaded here rather than with a constructor finder: before the scene script has run once the
	// asset does not exist, and a finder would log an error on every editor start.
	UMaterialInterface* Material = FPackageName::DoesPackageExist(SpeedTunnel::MaterialPackage)
		? LoadObject<UMaterialInterface>(nullptr, SpeedTunnel::MaterialPath)
		: nullptr;
	if (Material && GetStaticMesh())
	{
		TunnelMaterial = UMaterialInstanceDynamic::Create(Material, this);
		SetMaterial(0, TunnelMaterial ? static_cast<UMaterialInterface*>(TunnelMaterial) : Material);
		MeshBounds = GetStaticMesh()->GetBoundingBox();
		if (!MeshBounds.GetCenter().IsNearlyZero(1.0))
		{
			// The material measures from the instance's origin, so the cylinder has to be centred on it.
			UE_LOG(LogTemp, Warning, TEXT("SpeedTunnel: the cylinder's pivot is off its centre by %s; the tunnel will be misplaced"),
				*MeshBounds.GetCenter().ToString());
		}
	}
	else
	{
		Layers.Reset();
	}
	SetVisibility(false);

	UMaterialInterface* FogBase = FPackageName::DoesPackageExist(SpeedTunnel::FogPackage)
		? LoadObject<UMaterialInterface>(nullptr, SpeedTunnel::FogPath) : nullptr;
	if (FogBase && GetStaticMesh() && GetOwner())
	{
		Fog = NewObject<UStaticMeshComponent>(GetOwner(), TEXT("QuantumFog"));
		// A sphere round the camera, not a cylinder: the cylinder's own silhouette cut a hard straight
		// edge across the frame once the walls were lit (the author, 22. 9. 2026). The fog's colour is
		// a function of the view direction alone, so the shape it is painted on does not matter.
		UStaticMesh* FogSphere = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
		Fog->SetStaticMesh(FogSphere ? FogSphere : ToRawPtr(GetStaticMesh()));
		Fog->SetUsingAbsoluteLocation(true);
		Fog->SetUsingAbsoluteRotation(true);
		Fog->SetUsingAbsoluteScale(true);
		Fog->SetMobility(EComponentMobility::Movable);
		Fog->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
		Fog->SetCastShadow(false);
		Fog->bAffectDistanceFieldLighting = false;
		Fog->bAffectDynamicIndirectLighting = false;
		Fog->SetVisibleInRayTracing(false);
		// Behind the streak walls, which get a higher sort priority below (both are centred on the camera,
		// so distance cannot order them). Not a negative priority on the fog: that sorts it before every
		// other translucent thing too, and the gas giant's rings showed straight through (21. 9. 2026).
		FogMaterial = UMaterialInstanceDynamic::Create(FogBase, this);
		Fog->SetMaterial(0, FogMaterial);
		Fog->SetupAttachment(GetAttachParent());
		Fog->RegisterComponent();
		Fog->SetVisibility(false);
		SetTranslucentSortPriority(10);
	}

	UMaterialInterface* BeaconBase = FPackageName::DoesPackageExist(SpeedTunnel::BeaconPackage)
		? LoadObject<UMaterialInterface>(nullptr, SpeedTunnel::BeaconPath) : nullptr;
	UStaticMesh* Sphere = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (BeaconBase && Sphere && GetOwner())
	{
		// The destination as a point of light at the vanishing point: the tunnel is opaque, so the
		// real body is hidden, and letting it through made it bleed over the frame (the author, 22. 9. 2026).
		Beacon = NewObject<UStaticMeshComponent>(GetOwner(), TEXT("QuantumBeacon"));
		Beacon->SetStaticMesh(Sphere);
		Beacon->SetUsingAbsoluteLocation(true);
		Beacon->SetUsingAbsoluteRotation(true);
		Beacon->SetUsingAbsoluteScale(true);
		Beacon->SetMobility(EComponentMobility::Movable);
		Beacon->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
		Beacon->SetCastShadow(false);
		Beacon->bAffectDistanceFieldLighting = false;
		Beacon->bAffectDynamicIndirectLighting = false;
		Beacon->SetVisibleInRayTracing(false);
		Beacon->SetTranslucentSortPriority(15);
		BeaconMaterial = UMaterialInstanceDynamic::Create(BeaconBase, this);
		Beacon->SetMaterial(0, BeaconMaterial);
		Beacon->SetupAttachment(GetAttachParent());
		Beacon->RegisterComponent();
		Beacon->SetVisibility(false);

		BeaconLight = NewObject<UPointLightComponent>(GetOwner(), TEXT("QuantumBeaconLight"));
		BeaconLight->SetUsingAbsoluteLocation(true);
		BeaconLight->SetMobility(EComponentMobility::Movable);
		BeaconLight->SetCastShadows(false);
		BeaconLight->SetIntensityUnits(ELightUnits::Candelas);
		BeaconLight->SetAttenuationRadius(200000.f);
		BeaconLight->SetupAttachment(GetAttachParent());
		BeaconLight->RegisterComponent();
		BeaconLight->SetVisibility(false);
	}
}

void USpaceSpeedTunnelComponent::HideTunnel()
{
	if (!bHidden)
	{
		SetVisibility(false);
		if (Fog)
		{
			Fog->SetVisibility(false);
		}
		if (Beacon)
		{
			Beacon->SetVisibility(false);
		}
		bHidden = true;
	}
}

void USpaceSpeedTunnelComponent::TriggerFlare(float Strength)
{
	FlareTime = 0.f;
	FlareStrength = Strength;
	FlareSeed = FlareRandom.FRandRange(1.f, 97.f);
	FlareWait = FlareRandom.FRandRange(FlareIntervalMinSeconds, FMath::Max(FlareIntervalMinSeconds, FlareIntervalMaxSeconds));
}

void USpaceSpeedTunnelComponent::UpdateFlare(float DeltaSeconds)
{
	if (FlareTime >= 0.f)
	{
		FlareTime += DeltaSeconds;
		if (FlareTime > FlareSeconds)
		{
			FlareTime = -1.f;
		}
		return;
	}
	FlareWait -= DeltaSeconds;
	if (FlareWait <= 0.f)
	{
		TriggerFlare(1.f);
	}
}

float USpaceSpeedTunnelComponent::ComputeApparentSpeed(float Speed) const
{
	return FMath::Min(Speed, MaxApparentSpeed);
}

float USpaceSpeedTunnelComponent::ComputeStreakLength(float Speed) const
{
	// Never longer than most of a lane's period, or one streak would run into the next.
	const float Longest = FMath::Min(MaxStreakCm, 0.6f * PeriodCm);
	return FMath::Clamp(ComputeApparentSpeed(Speed) * StreakSeconds, FMath::Min(MinStreakCm, Longest), Longest);
}

void USpaceSpeedTunnelComponent::PushParameters(const FVector& Direction, float Alpha, float StreakLength)
{
	const FMatrix Frame = FRotationMatrix::MakeFromX(Direction);
	TunnelMaterial->SetVectorParameterValue(TEXT("TunnelDirection"), FLinearColor(Direction));
	TunnelMaterial->SetVectorParameterValue(TEXT("TunnelRight"), FLinearColor(Frame.GetUnitAxis(EAxis::Y)));
	TunnelMaterial->SetVectorParameterValue(TEXT("TunnelUp"), FLinearColor(Frame.GetUnitAxis(EAxis::Z)));
	TunnelMaterial->SetScalarParameterValue(TEXT("TunnelAlpha"), Alpha);
	TunnelMaterial->SetScalarParameterValue(TEXT("TunnelHalfLengthCm"), HalfLengthCm);
	TunnelMaterial->SetScalarParameterValue(TEXT("TunnelOffsetCm"), float(OffsetCm));
	TunnelMaterial->SetScalarParameterValue(TEXT("TunnelPeriodCm"), PeriodCm);
	TunnelMaterial->SetScalarParameterValue(TEXT("StreakLengthCm"), StreakLength);
	TunnelMaterial->SetScalarParameterValue(TEXT("StreakWidthCm"), StreakWidthCm);
	TunnelMaterial->SetScalarParameterValue(TEXT("StreakColorSpread"), StreakColorSpread);
	TunnelMaterial->SetScalarParameterValue(TEXT("StreakFill"), Fill);
	TunnelMaterial->SetVectorParameterValue(TEXT("StreakColor"), StreakColor);
	TunnelMaterial->SetScalarParameterValue(TEXT("StreakBrightness"), StreakBrightness);
	TunnelMaterial->SetVectorParameterValue(TEXT("BeamColor"), BeamColor);
	TunnelMaterial->SetScalarParameterValue(TEXT("BeamBrightness"), BeamBrightness);
	TunnelMaterial->SetScalarParameterValue(TEXT("BeamCount"), BeamCount);
	TunnelMaterial->SetScalarParameterValue(TEXT("BeamSharpness"), BeamSharpness);
	TunnelMaterial->SetVectorParameterValue(TEXT("GlowColor"), GlowColor);
	TunnelMaterial->SetScalarParameterValue(TEXT("GlowBrightness"), GlowBrightness);
	TunnelMaterial->SetVectorParameterValue(TEXT("HazeColor"), HazeColor);
	TunnelMaterial->SetVectorParameterValue(TEXT("FlareColor"), FlareColor);
	TunnelMaterial->SetScalarParameterValue(TEXT("FlareSeed"), FlareSeed);
	// Quick in, slow out, like the reference's bursts.
	const float Envelope = FlareTime < 0.f ? 0.f
		: FMath::Min(FlareTime / 0.15f, 1.f) * FMath::Square(1.f - FMath::Clamp(FlareTime / FMath::Max(FlareSeconds, 0.1f), 0.f, 1.f));
	TunnelMaterial->SetScalarParameterValue(TEXT("FlareAlpha"), FlareStrength * Envelope);
}

void USpaceSpeedTunnelComponent::UpdateTunnel(const FVector& ViewLocation, const FVector& Velocity, float DeltaSeconds, float Intensity)
{
	const double Speed = Velocity.Size();
	const float Alpha = FMath::Clamp(Intensity, 0.f, 1.f);
	if (!TunnelMaterial || Layers.Num() == 0 || Alpha <= 0.001f || Speed < 1.0)
	{
		HideTunnel();
		return;
	}
	UpdateFlare(DeltaSeconds);

	// The scroll, wrapped at the period so it stays small; the pattern repeats exactly there.
	OffsetCm = FMath::Fmod(OffsetCm + double(ComputeApparentSpeed(float(Speed))) * DeltaSeconds, double(PeriodCm));

	const FVector Direction = Velocity / Speed;
	SetWorldLocationAndRotation(ViewLocation, FRotationMatrix::MakeFromZ(Direction).ToQuat());
	PushParameters(Direction, Alpha, ComputeStreakLength(float(Speed)));

	if (GetInstanceCount() != Layers.Num())
	{
		ClearInstances();
		for (int32 Index = 0; Index < Layers.Num(); ++Index)
		{
			AddInstance(FTransform::Identity, false);
		}
	}
	// The cylinder's axis is its Z; the component's Z runs along the flight path.
	const FVector Extent = MeshBounds.GetExtent();
	for (int32 Index = 0; Index < Layers.Num(); ++Index)
	{
		const FSpeedTunnelLayer& Layer = Layers[Index];
		const FVector Scale(Layer.RadiusCm / FMath::Max(Extent.X, 1.0), Layer.RadiusCm / FMath::Max(Extent.Y, 1.0),
			HalfLengthCm / FMath::Max(Extent.Z, 1.0));
		UpdateInstanceTransform(Index, FTransform(FQuat::Identity, FVector::ZeroVector, Scale), false, false, true);
		SetCustomDataValue(Index, 0, Layer.RadiusCm, false);
		SetCustomDataValue(Index, 1, Layer.Brightness, false);
		SetCustomDataValue(Index, 2, float(Index) * 7.31f + 1.f, false);
		SetCustomDataValue(Index, 3, Layer.BeamWeight, false);
		SetCustomDataValue(Index, 4, Layer.Lanes, false);
	}
	MarkRenderStateDirty();

	if (Fog && FogMaterial)
	{
		// A little longer than the streak walls: the fog now has depth, and its far end must not cover
		// the walls' far end (where the beams converge).
		// Wide enough to hold the streak walls and the beacon inside it.
		const FVector FogExtent = Fog->GetStaticMesh() ? Fog->GetStaticMesh()->GetBounds().BoxExtent : FVector(50.0);
		const double FogScale = FogShellRadiusCm / FMath::Max(FogExtent.GetMax(), 1.0);
		Fog->SetWorldTransform(FTransform(GetComponentQuat(), ViewLocation, FVector(FogScale)));
		FogMaterial->SetVectorParameterValue(TEXT("TunnelDirection"), FLinearColor(Direction));
		FogMaterial->SetScalarParameterValue(TEXT("TunnelHalfLengthCm"), HalfLengthCm);
		FogMaterial->SetScalarParameterValue(TEXT("TunnelAlpha"), Alpha);
		FogMaterial->SetScalarParameterValue(TEXT("FogOpacity"), FogOpacity);
		FogMaterial->SetScalarParameterValue(TEXT("FogCentreOpacity"), FogCentreOpacity);
		FogMaterial->SetScalarParameterValue(TEXT("FogShaftCount"), FogShaftCount);
		FogMaterial->SetScalarParameterValue(TEXT("FogShaftContrast"), FogShaftContrast);
		const FMatrix Frame = FRotationMatrix::MakeFromX(Direction);
		FogMaterial->SetVectorParameterValue(TEXT("TunnelRight"), FLinearColor(Frame.GetUnitAxis(EAxis::Y)));
		FogMaterial->SetVectorParameterValue(TEXT("TunnelUp"), FLinearColor(Frame.GetUnitAxis(EAxis::Z)));
		FogMaterial->SetVectorParameterValue(TEXT("FogNearColor"), FogNearColor);
		FogMaterial->SetVectorParameterValue(TEXT("FogFarColor"), FogFarColor);
		FogMaterial->SetVectorParameterValue(TEXT("FogWarmColor"), FogWarmColor);
		FogMaterial->SetVectorParameterValue(TEXT("FogCoolColor"), FogCoolColor);
		FogMaterial->SetScalarParameterValue(TEXT("FogCloudAmount"), FogCloudAmount);
		FogMaterial->SetScalarParameterValue(TEXT("FogCloudSpeed"), FogCloudSpeed);
		FogMaterial->SetVectorParameterValue(TEXT("FogBandColor"), FogBandColor);
		FogMaterial->SetScalarParameterValue(TEXT("FogBandAmount"), FogBandAmount);
		if (!Sun.IsValid())
		{
			for (TObjectIterator<UDirectionalLightComponent> It; It; ++It)
			{
				if (It->GetWorld() == GetWorld())
				{
					Sun = *It;
					break;
				}
			}
		}
		const FVector SunDirection = Sun.IsValid() ? Sun->GetForwardVector() : FVector::ForwardVector;
		FogMaterial->SetVectorParameterValue(TEXT("FogSunDirection"), FLinearColor(SunDirection));
		FogMaterial->SetScalarParameterValue(TEXT("FogSunAmount"), FogSunAmount);
	}

	if (Beacon && BeaconMaterial)
	{
		// Sized by the angle it should take up from here, so it stays a small point however long the
		// tunnel is; the engine sphere is 100 cm across.
		const double Radius = BeaconDistanceCm * FMath::Tan(FMath::DegreesToRadians(FMath::Max(BeaconSizeDeg, 0.05f) * 0.5f));
		Beacon->SetWorldTransform(FTransform(GetComponentQuat(), ViewLocation + Direction * BeaconDistanceCm,
			FVector(Radius / 50.0)));
		BeaconMaterial->SetVectorParameterValue(TEXT("BeaconColor"), BeaconColor);
		BeaconMaterial->SetScalarParameterValue(TEXT("BeaconBrightness"), BeaconBrightness * Alpha);
		Beacon->SetVisibility(Alpha > 0.01f);
		if (BeaconLight)
		{
			// Close enough to reach the ship: the light sits a ship length ahead, not out at the beacon.
			BeaconLight->SetWorldLocation(ViewLocation + Direction * 6000.0);
			BeaconLight->SetLightColor(BeaconColor);
			BeaconLight->SetIntensity(BeaconLightCandela * Alpha);
			BeaconLight->SetVisibility(Alpha > 0.01f);
		}
	}

	if (bHidden)
	{
		SetVisibility(true);
		if (Fog)
		{
			Fog->SetVisibility(true);
		}
		bHidden = false;
	}
}
