// Copyright Epic Games, Inc. All Rights Reserved.

#include "SkyDome.h"

#include "Camera/PlayerCameraManager.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/CollisionProfile.h"
#include "Engine/StaticMesh.h"
#include "Kismet/GameplayStatics.h"
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

void ASkyDome::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (const APlayerCameraManager* Camera = UGameplayStatics::GetPlayerCameraManager(this, 0))
	{
		SetActorLocation(Camera->GetCameraLocation());
	}
}
