// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CelestialBody.generated.h"

class UStaticMeshComponent;

/**
 * A named body in space - planet, moon, station - that navigation can point at.
 *
 * Deliberately thin for now: a mesh and a display name. The HUD finds the nearest one and shows
 * the distance to its surface.
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
	 * Distance in cm from Location to the body's surface, taken as its bounding sphere. Exact for
	 * spheres, an underestimate for anything elongated. Negative inside the sphere.
	 */
	UFUNCTION(BlueprintPure, Category = "Celestial Body")
	double GetSurfaceDistance(const FVector& Location) const;

protected:
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Celestial Body")
	TObjectPtr<UStaticMeshComponent> Body;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Celestial Body")
	FText DisplayName;
};
