// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "DistantBody.generated.h"

class UStaticMeshComponent;

/**
 * A moon or planet to look at, not to land on: a lit sphere, optionally with rings, optionally
 * orbiting another actor. Real geometry hundreds of kilometres away, so it shifts against the
 * stars as the ship travels - the sky stops reading as a painted backdrop.
 *
 * Not an ACelestialBody: no gravity, atmosphere or terrain, and flight code ignores it. Its
 * sphere mesh keeps simple collision so the ship cannot fly through it.
 *
 * Must stay inside the sky dome (ASkyDome::DomeRadiusKm around the camera) to be visible.
 */
UCLASS()
class GAMESPACE_API ADistantBody : public AActor
{
	GENERATED_BODY()

public:
	ADistantBody();

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void Tick(float DeltaSeconds) override;

	/** Where the orbit puts the body at this game time, relative to the orbit centre, cm. For tests. */
	UFUNCTION(BlueprintCallable, Category = "Distant Body")
	FVector ComputeOrbitOffset(double TimeSeconds) const;

	UFUNCTION(BlueprintPure, Category = "Distant Body")
	const FText& GetDisplayName() const { return DisplayName; }

	UFUNCTION(BlueprintPure, Category = "Distant Body")
	float GetRadiusKm() const { return RadiusKm; }

protected:
	/** Sphere with a radius of 100 cm (SM_PlanetSphere), scaled to RadiusKm. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Distant Body")
	TObjectPtr<UStaticMeshComponent> Body;

	/** Flat ring plane (the engine's 100 cm Plane), scaled to RingOuterRadiusKm. Hidden without rings. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Distant Body")
	TObjectPtr<UStaticMeshComponent> Rings;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Distant Body")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Distant Body", meta = (ClampMin = "0.01", Units = "km"))
	float RadiusKm = 100.f;

	/** Outer edge of the rings; 0 for none. The ring material cuts the inner edge. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Distant Body", meta = (ClampMin = "0.0", Units = "km"))
	float RingOuterRadiusKm = 0.f;

	/** Tilt of the spin axis and rings, degrees about the body's X axis. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Distant Body")
	float AxialTiltDeg = 0.f;

	/** One turn about its axis in this many seconds; 0 does not spin. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Distant Body", meta = (ClampMin = "0.0", Units = "s"))
	float SpinPeriodSeconds = 0.f;

	/** Actor to orbit. None keeps the body where it was placed. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Distant Body|Orbit")
	TObjectPtr<AActor> OrbitCenter;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Distant Body|Orbit", meta = (ClampMin = "0.0", Units = "km"))
	float OrbitRadiusKm = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Distant Body|Orbit", meta = (ClampMin = "1.0", Units = "s"))
	float OrbitPeriodSeconds = 1200.f;

	/** Tilt of the orbit plane against world XY, degrees. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Distant Body|Orbit")
	float OrbitInclinationDeg = 0.f;

	/** Direction the tilted orbit crosses world XY, degrees about world Z. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Distant Body|Orbit")
	float OrbitNodeDeg = 0.f;

	/** Position along the orbit at game time 0, degrees. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Distant Body|Orbit")
	float OrbitPhaseDeg = 0.f;

private:
	void PlaceOnOrbit(double TimeSeconds);
};
