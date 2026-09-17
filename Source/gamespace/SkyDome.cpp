// Copyright Epic Games, Inc. All Rights Reserved.

#include "SkyDome.h"

#include "Camera/PlayerCameraManager.h"
#include "CelestialBody.h"
#include "Components/StaticMeshComponent.h"
#include "Components/LightComponent.h"
#include "Engine/CollisionProfile.h"
#include "Engine/DirectionalLight.h"
#include "EngineUtils.h"
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
	for (TActorIterator<ADirectionalLight> It(GetWorld()); It; ++It)
	{
		Sun = *It;
		break;
	}
	if (SkyMaterial)
	{
		NebulaBase = SkyMaterial->K2_GetScalarParameterValue(TEXT("NebulaBrightness"));
		SunDiscBase = SkyMaterial->K2_GetScalarParameterValue(TEXT("SunDiscBrightness"));
		SunGlowBase = SkyMaterial->K2_GetScalarParameterValue(TEXT("SunGlowBrightness"));
	}
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
		SkyMaterial->SetScalarParameterValue(TEXT("Twinkle"), FMath::Lerp(SpaceTwinkle, AtmosphereTwinkle, Amount));
		SkyMaterial->SetScalarParameterValue(TEXT("NebulaBrightness"), NebulaBase * NebulaScale);
		SkyMaterial->SetScalarParameterValue(TEXT("SunDiscBrightness"), SunDiscBase * SunScale);
		SkyMaterial->SetScalarParameterValue(TEXT("SunGlowBrightness"), SunGlowBase * SunScale);
		if (const ADirectionalLight* Light = Sun.Get())
		{
			// The light shines along its forward vector; the sun sits the other way.
			const FVector ToSun = -Light->GetActorForwardVector();
			SkyMaterial->SetVectorParameterValue(TEXT("SunDirection"), FLinearColor(FVector3f(ToSun)));
			SkyMaterial->SetVectorParameterValue(TEXT("SunColor"), Light->GetLightComponent()->GetLightColor());
		}
		if (Amount > 0.f)
		{
			SkyMaterial->SetVectorParameterValue(TEXT("PlanetUp"), FLinearColor(FVector3f(Environment.Up)));
			SkyMaterial->SetVectorParameterValue(TEXT("SkyZenithColor"), Environment.SkyZenithColor);
			SkyMaterial->SetVectorParameterValue(TEXT("SkyHorizonColor"), Environment.SkyHorizonColor);
			SkyMaterial->SetScalarParameterValue(TEXT("SkyBrightness"), Environment.SkyBrightness);
		}
	}
}
