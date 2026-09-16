// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CelestialBody.generated.h"

class UStaticMeshComponent;

/** Where a ship is relative to a body, for the flight model and the HUD. */
UENUM(BlueprintType)
enum class EFlightRegime : uint8
{
	/** Above the atmosphere: no drag, no gravity. */
	Orbit,
	/** Inside the atmosphere, well above the ground. */
	Atmosphere,
	/** Close above the terrain. */
	Surface
};

/** Conditions at one point near a body. Everything blends smoothly with altitude. */
USTRUCT(BlueprintType)
struct FCelestialEnvironment
{
	GENERATED_BODY()

	/** Above the terrain directly below, cm. */
	UPROPERTY(BlueprintReadOnly, Category = "Environment")
	double AltitudeAboveTerrainCm = 0.0;

	/** Above the body's base radius (sea level), cm. Atmosphere and gravity depend on this. */
	UPROPERTY(BlueprintReadOnly, Category = "Environment")
	double AltitudeAboveSeaLevelCm = 0.0;

	/** Unit vector pointing away from the body centre. */
	UPROPERTY(BlueprintReadOnly, Category = "Environment")
	FVector Up = FVector::UpVector;

	/** 0 at the top of the atmosphere and above, 1 at sea level. */
	UPROPERTY(BlueprintReadOnly, Category = "Environment")
	float AtmosphereDensity = 0.f;

	/** Gravity acceleration to apply, cm/s^2, along -Up. Already faded in with altitude. */
	UPROPERTY(BlueprintReadOnly, Category = "Environment")
	double GravityCmS2 = 0.0;

	/** How much the sky shows atmosphere instead of stars, 0..1. */
	UPROPERTY(BlueprintReadOnly, Category = "Environment")
	float SkyAmount = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Environment")
	FLinearColor SkyZenithColor = FLinearColor::Black;

	UPROPERTY(BlueprintReadOnly, Category = "Environment")
	FLinearColor SkyHorizonColor = FLinearColor::Black;

	/** Emissive multiplier for the sky colours, tuned to the fixed exposure. */
	UPROPERTY(BlueprintReadOnly, Category = "Environment")
	float SkyBrightness = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Environment")
	EFlightRegime Regime = EFlightRegime::Orbit;
};

/**
 * A named body in space - planet, moon, station - that navigation can point at.
 *
 * Deliberately thin: a mesh and a display name. The HUD finds the nearest one and shows the
 * distance to its surface. Bodies with an atmosphere or gravity override SampleEnvironment.
 */
UCLASS(Blueprintable)
class GAMESPACE_API ACelestialBody : public AActor
{
	GENERATED_BODY()

public:
	ACelestialBody();

	UFUNCTION(BlueprintPure, Category = "Celestial Body")
	const FText& GetDisplayName() const { return DisplayName; }

	/**
	 * Distance in cm from Location to the body's surface. The default takes the surface as the
	 * Body mesh's bounding sphere: exact for spheres, an underestimate for anything elongated.
	 * Negative inside. Subclasses with real terrain override it.
	 */
	UFUNCTION(BlueprintPure, Category = "Celestial Body")
	virtual double GetSurfaceDistance(const FVector& Location) const;

	/**
	 * Atmosphere, gravity and flight regime at a world location. Returns false for bodies with
	 * neither, which the default does.
	 */
	UFUNCTION(BlueprintPure, Category = "Celestial Body")
	virtual bool SampleEnvironment(const FVector& Location, FCelestialEnvironment& OutEnvironment) const;

	/**
	 * The body whose surface is nearest to Location, and whether it has an environment. Used by
	 * everything that needs "the planet I'm near" without caring which one.
	 */
	static ACelestialBody* FindNearest(const UWorld* World, const FVector& Location, FCelestialEnvironment* OutEnvironment = nullptr, bool* bOutHasEnvironment = nullptr);

protected:
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Celestial Body")
	TObjectPtr<UStaticMeshComponent> Body;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Celestial Body")
	FText DisplayName;
};
