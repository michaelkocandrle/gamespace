// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "SpaceDustComponent.generated.h"

/**
 * Specks of dust in a box around the camera, standing still in the world. Flying past them is
 * what makes speed and direction visible against a sky whose stars never move: at walking pace
 * they drift by with parallax, fast they stretch into streaks along the flight path.
 *
 * Every speck lives at a world position; each update wraps it back into the box around the
 * camera, so there are always ParticleCount of them nearby. The mesh is a cube stretched along
 * the velocity; M_SpaceDust (additive, unlit) tapers it to a soft point at both ends and reads
 * the per-instance fade from custom data 0 and the per-instance brightness from 1.
 *
 * Each speck keeps its own brightness and length (LengthSpread, BrightnessSpread), because dust
 * that is all one weight and one length reads as a field of identical white sticks rather than as
 * dust (20. 9. 2026, against the reference).
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

	/** Number of specks. 400 until 21. 9. 2026: the field was too thin to read as dust in motion.
	 *  2600 in a 30 m box costs nothing measurable (80 FPS either way, Tools/Shots/dust_tune.json). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Space Dust", meta = (ClampMin = "0", ClampMax = "4000"))
	int32 ParticleCount = 2600;

	/** Half the edge of the box around the camera, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Space Dust", meta = (ClampMin = "100.0"))
	float BoxHalfSizeCm = 3000.f;

	/** Thickness of a speck, cm. The material tapers it, so this is the widest point. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Space Dust", meta = (ClampMin = "0.1"))
	float ParticleSizeCm = 2.4f;

	/** A streak is as long as the distance flown in this time. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Space Dust", meta = (ClampMin = "0.0", Units = "s"))
	float StreakSeconds = 0.014f;

	/** Longest streak, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Space Dust", meta = (ClampMin = "1.0"))
	float MaxStreakCm = 1500.f;

	/** Invisible below this speed, fully visible at four times it, cm/s. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Space Dust", meta = (ClampMin = "0.0"))
	float FadeInSpeed = 800.f;

	/** A speck's length is the common one times 1 +- this: 0.6 means a third as long to nearly twice. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Space Dust", meta = (ClampMin = "0.0", ClampMax = "0.95"))
	float LengthSpread = 0.6f;

	/** A speck's brightness is 1 minus up to this: 0.75 leaves most of them faint and a few bright. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Space Dust", meta = (ClampMin = "0.0", ClampMax = "0.95"))
	float BrightnessSpread = 0.6f;

private:
	TArray<FVector> Positions;
	TArray<FTransform> Transforms;

	/** Per speck, fixed when it is created: how long it is and how bright, both as multipliers. */
	TArray<float> LengthScales;
	TArray<float> Brightnesses;

	/** The material's own instance: the shape of a speck needs the flight direction and the sizes. */
	TObjectPtr<UMaterialInstanceDynamic> DustMaterial;
	bool bCreated = false;
	bool bHidden = true;
};
