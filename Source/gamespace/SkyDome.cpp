// Copyright Epic Games, Inc. All Rights Reserved.

#include "SkyDome.h"

#include "Camera/PlayerCameraManager.h"
#include "CelestialBody.h"
#include "Components/StaticMeshComponent.h"
#include "Components/LightComponent.h"
#include "Engine/CollisionProfile.h"
#include "Components/DirectionalLightComponent.h"
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
		SunBaseIntensity = It->GetLightComponent()->Intensity;
		SunRequestedIntensity = SunWrittenIntensity = SunBaseIntensity;
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

	FCelestialEnvironment Environment;
	bool bHasEnvironment = false;
	const ACelestialBody* Body = ACelestialBody::FindNearest(GetWorld(), CameraLocation, &Environment, &bHasEnvironment);
	const float Amount = bHasEnvironment ? Environment.SkyAmount : 0.f;
	// The geometric horizon dips with altitude: its height (sine of the elevation) is -sqrt(1 - (R / D)^2), R the
	// body's sea-level radius, D the distance from its centre - in orbit the planet hides far less of the sky.
	float Horizon = 0.f;
	if (bHasEnvironment && Body)
	{
		const double Distance = FVector::Distance(CameraLocation, Body->GetActorLocation());
		const double Radius = Distance - Environment.AltitudeAboveSeaLevelCm;
		if (Distance > 1.0 && Radius > 0.0)
		{
			Horizon = -float(FMath::Sqrt(FMath::Max(0.0, 1.0 - FMath::Square(Radius / Distance))));
		}
	}
	UpdateSunShadow(bHasEnvironment, Environment, Horizon);

	if (SkyMaterial)
	{
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
			// Day or night where the camera is: the sun's height over the local horizon and whether it is
			// on at all. The painted sky follows it (the real atmosphere already does, being lit by the sun).
			float Day = 1.f;
			if (const ADirectionalLight* Light = Sun.Get())
			{
				const float Height = FVector::DotProduct(-Light->GetActorForwardVector(), Environment.Up);
				const float On = SunBaseIntensity > 0.f ? FMath::Clamp(SunRequestedIntensity / SunBaseIntensity, 0.f, 1.f) : 1.f;
				Day = FMath::SmoothStep(-0.12f, 0.08f, Height) * On;
			}
			SkyMaterial->SetVectorParameterValue(TEXT("PlanetUp"), FLinearColor(FVector3f(Environment.Up)));
			SkyMaterial->SetVectorParameterValue(TEXT("SkyZenithColor"), Environment.SkyZenithColor);
			SkyMaterial->SetVectorParameterValue(TEXT("SkyHorizonColor"), Environment.SkyHorizonColor);
			SkyMaterial->SetScalarParameterValue(TEXT("SkyBrightness"), Environment.SkyBrightness * FMath::Lerp(NightSkyFloor, 1.f, Day));
		}
	}
}

void ASkyDome::UpdateSunShadow(bool bHasEnvironment, const FCelestialEnvironment& Environment, float Horizon)
{
	ADirectionalLight* const Light = Sun.Get();
	if (!Light)
	{
		return;
	}
	UDirectionalLightComponent* const Component = Cast<UDirectionalLightComponent>(Light->GetLightComponent());
	if (!Component)
	{
		return;
	}
	// Someone else set the intensity since the last frame (the level, space.Sun, quantum travel): that is the
	// new request; the shadow only ever scales the request.
	if (!FMath::IsNearlyEqual(Component->Intensity, SunWrittenIntensity, 1e-4f))
	{
		SunRequestedIntensity = Component->Intensity;
	}
	float Shadow = 1.f;
	if (bHasEnvironment)
	{
		const float Height = FVector::DotProduct(-Light->GetActorForwardVector(), Environment.Up);
		Shadow = FMath::SmoothStep(Horizon + SunShadowZeroHeight, Horizon + SunShadowFullHeight, Height);
	}
	const float Wanted = SunRequestedIntensity * Shadow;
	if (!FMath::IsNearlyEqual(Component->Intensity, Wanted, 1e-4f))
	{
		Component->SetIntensity(Wanted);
	}
	SunWrittenIntensity = Wanted;
}
