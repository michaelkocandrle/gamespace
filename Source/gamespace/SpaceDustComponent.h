// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "SpaceDustComponent.generated.h"

/**
 * Specks of dust in a box around the camera, standing still in the world. Flying past them is
 * what makes speed and direction visible against a sky whose stars never move: at walking pace
 * they drift by with parallax, fast they stretch into streaks along the flight path.
 *
 * Every speck lives at a world position; each update wraps it back into the box around the
 * camera, so there are always ParticleCount of them nearby. The mesh is a cube stretched along
 * the velocity; M_SpaceDust (additive, unlit) reads the per-instance fade from custom data 0.
 */
UCLASS(ClassGroup = Space, meta = (BlueprintSpawnableComponent))
class GAMESPACE_API USpaceDustComponent : public UInstancedStaticMeshComponent
{
	GENERATED_BODY()

public:
	USpaceDustComponent();

	virtual void BeginPlay() override;

	/**
	 * Places the dust around ViewLocation for an observer moving at Velocity (cm/s). Intensity
	 * scales the brightness (1 normal, more in cruise).
	 */
	void UpdateDust(const FVector& ViewLocation, const FVector& Velocity, float Intensity);

	/** Hides the dust until the next UpdateDust. */
	void HideDust();

	/** Number of specks. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Space Dust", meta = (ClampMin = "0", ClampMax = "4000"))
	int32 ParticleCount = 400;

	/** Half the edge of the box around the camera, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Space Dust", meta = (ClampMin = "100.0"))
	float BoxHalfSizeCm = 3500.f;

	/** Thickness of a speck, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Space Dust", meta = (ClampMin = "0.1"))
	float ParticleSizeCm = 7.f;

	/** A streak is as long as the distance flown in this time. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Space Dust", meta = (ClampMin = "0.0", Units = "s"))
	float StreakSeconds = 0.035f;

	/** Longest streak, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Space Dust", meta = (ClampMin = "1.0"))
	float MaxStreakCm = 5000.f;

	/** Invisible below this speed, fully visible at four times it, cm/s. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Space Dust", meta = (ClampMin = "0.0"))
	float FadeInSpeed = 800.f;

private:
	TArray<FVector> Positions;
	TArray<FTransform> Transforms;
	bool bCreated = false;
	bool bHidden = true;
};
