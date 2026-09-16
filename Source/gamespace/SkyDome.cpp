// Copyright Epic Games, Inc. All Rights Reserved.

#include "SkyDome.h"

#include "Camera/PlayerCameraManager.h"
#include "CelestialBody.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/CollisionProfile.h"
#include "Engine/StaticMesh.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	/** /Engine/BasicShapes/Sphere is 100 cm across. */
	constexpr double SphereMeshRadiusCm = 50.0;
}

ASkyDome::ASkyDome()
{
	PrimaryActorTick.bCanEverTick = true;
	// After the camera has been updated for this frame, so the dome is centred on this frame's view.
	PrimaryActorTick.TickGroup = TG_PostUpdateWork;

	Dome = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Dome"));
	SetRootComponent(Dome);
	Dome->SetMobility(EComponentMobility::Movable);
	Dome->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
	// A shell around the whole scene: casting shadows or taking part in GI would darken everything.
	Dome->SetCastShadow(false);
	Dome->bAffectDistanceFieldLighting = false;
	Dome->bAffectDynamicIndirectLighting = false;
	Dome->SetVisibleInRayTracing(false);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (Sphere.Succeeded())
	{
		Dome->SetStaticMesh(Sphere.Object);
	}
}

void ASkyDome::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	SetActorScale3D(FVector(DomeRadiusKm * 100000.0 / SphereMeshRadiusCm));
}

void ASkyDome::BeginPlay()
{
	Super::BeginPlay();
	SkyMaterial = Dome->CreateDynamicMaterialInstance(0);
}

void ASkyDome::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	const APlayerCameraManager* Camera = UGameplayStatics::GetPlayerCameraManager(this, 0);
	if (!Camera)
	{
		return;
	}
	const FVector CameraLocation = Camera->GetCameraLocation();
	SetActorLocation(CameraLocation);

	if (SkyMaterial)
	{
		FCelestialEnvironment Environment;
		bool bHasEnvironment = false;
		ACelestialBody::FindNearest(GetWorld(), CameraLocation, &Environment, &bHasEnvironment);
		const float Amount = bHasEnvironment ? Environment.SkyAmount : 0.f;
		SkyMaterial->SetScalarParameterValue(TEXT("AtmosphereAmount"), Amount);
		if (Amount > 0.f)
		{
			SkyMaterial->SetVectorParameterValue(TEXT("PlanetUp"), FLinearColor(FVector3f(Environment.Up)));
			SkyMaterial->SetVectorParameterValue(TEXT("SkyZenithColor"), Environment.SkyZenithColor);
			SkyMaterial->SetVectorParameterValue(TEXT("SkyHorizonColor"), Environment.SkyHorizonColor);
			SkyMaterial->SetScalarParameterValue(TEXT("SkyBrightness"), Environment.SkyBrightness);
		}
	}
}
