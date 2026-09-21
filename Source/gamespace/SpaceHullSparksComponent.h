// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "SpaceHullSparksComponent.generated.h"

/**
 * Streaks that stream off the hull from the nose backwards, as if the ship were cutting through
 * something (21. 9. 2026, the author against the quantum reference video, where blue sparks pour
 * off the ship's edges all through the jump).
 *
 * Two looks from one pool: in a quantum jump many short bright blue sparks; in normal flight a few
 * faint white ones that grow with speed - the author wanted the speed lines "pushed to the ship, to the
 * nose that cuts through and to the engines", and fewer of them, rather than the dust spread round
 * the camera.
 *
 * Each spark is born on the hull (points found at BeginPlay by tracing the hull's collision from
 * outside; a shell of the hull's bounds when that finds nothing), lives a fraction of a second and
 * flows backwards along the ship, drawn with the space dust's material (M_SpaceDust, its own
 * dynamic instance for the colour). Attach to the hull: instances live in its space.
 */
UCLASS(ClassGroup = Space, meta = (BlueprintSpawnableComponent))
class GAMESPACE_API USpaceHullSparksComponent : public UInstancedStaticMeshComponent
{
	GENERATED_BODY()

public:
	USpaceHullSparksComponent();

	virtual void BeginPlay() override;

	/** The hull to find spark points on (its collision). Call before the first update. */
	void SetHull(UPrimitiveComponent* InHull) { Hull = InHull; }

	/**
	 * One frame. Speed is the ship's (cm/s); Quantum 0..1 is the jump's blend. ViewLocation keeps
	 * sparks off the lens in the cockpit.
	 */
	void UpdateSparks(float DeltaSeconds, float Speed, float Quantum, const FVector& ViewLocation);

	/** How many sparks live at once in a jump, and in normal flight at full strength. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0", ClampMax = "2000"))
	int32 QuantumCount = 420;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0", ClampMax = "2000"))
	int32 FlightCount = 60;

	/** Normal flight: nothing below the first speed, full from the second, cm/s. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float FlightFadeInSpeed = 3000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float FlightFullSpeed = 20000.f;

	/** How fast the sparks stream back along the hull, cm/s: in a jump, and at most in normal flight. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float QuantumFlowSpeed = 6000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float FlightFlowSpeed = 4500.f;

	/** How far a spark drifts off the hull while it lives, as a share of its backwards flow. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0", ClampMax = "2.0"))
	float Spread = 0.25f;

	/** Life of a spark, s (each gets a random time between the two). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.02"))
	float MinLifeSeconds = 0.18f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.02"))
	float MaxLifeSeconds = 0.55f;

	/** Streak length, cm, and thickness (seen from the chase camera 25-35 m away, 2 cm was under a pixel). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "1.0"))
	float QuantumLengthCm = 260.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "1.0"))
	float FlightLengthCm = 420.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.1"))
	float ThicknessCm = 5.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks")
	FLinearColor QuantumColor = FLinearColor(0.25f, 0.55f, 1.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float QuantumBrightness = 14.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks")
	FLinearColor FlightColor = FLinearColor(0.8f, 0.88f, 1.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float FlightBrightness = 6.f;

	/** Share of the sparks born at the front half of the hull: the nose is what cuts through. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float NoseBias = 0.6f;

	/** Tests: how many points on the hull the sparks are born at, and whether they came from the collision. */
	UFUNCTION(BlueprintCallable, Category = "Hull Sparks")
	int32 DebugGetSpawnPointCount(bool& bOutFromCollision);

private:
	struct FSpark
	{
		int32 Point = 0;
		float Age = 0.f;
		float Life = 0.f;
		float Pace = 1.f;
		float Brightness = 1.f;
		float Length = 1.f;
	};

	void FindSpawnPoints();
	void Respawn(FSpark& Spark, bool bRandomAge);

	TWeakObjectPtr<UPrimitiveComponent> Hull;
	TArray<FVector> Points;
	TArray<FVector> Normals;
	/** Indexes into Points: the front ones and the rest, for NoseBias. */
	TArray<int32> FrontPoints;
	TArray<int32> BackPoints;
	bool bPointsFromCollision = false;
	TArray<FSpark> Sparks;
	TArray<FTransform> Transforms;
	FRandomStream Random = FRandomStream(0x5A2C);
	TObjectPtr<UMaterialInstanceDynamic> SparkMaterial;
	bool bHidden = true;
};
