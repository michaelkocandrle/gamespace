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
 * Two looks from one pool: in a quantum jump dense bright blue sparks; in normal flight a few
 * faint white ones that grow with speed.
 *
 * Not a burst from one point (the author, 22. 9. 2026: "it looks like a static radial explosion of
 * sparks from one spot by the engine"): in the reference the stuff FLOWS and WAVES behind the ship
 * like a plasma, along the whole length of the hull, wrapping round its sides. So every spark is
 * born anywhere on the hull (points on its collision shapes; a shell of its bounds when it has
 * none), leaves the surface slowly and is carried back along the ship, weaving on two turbulence
 * waves that widen as it goes. A spark is drawn as a chain of short segments along the last
 * moments of its path, with M_HullSpark (custom data: 0 fade, 1 brightness). The width grows with
 * distance to stay a pixel or two wide.
 * Attach to the hull: instances live in its space.
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

	/** How many sparks live at once in a jump, and in normal flight at full strength (each is TrailSegments instances). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0", ClampMax = "2000"))
	int32 QuantumCount = 260;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0", ClampMax = "2000"))
	int32 FlightCount = 40;

	/** Normal flight: nothing below the first speed, full from the second, cm/s. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float FlightFadeInSpeed = 3000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float FlightFullSpeed = 20000.f;

	/** How fast the flow carries a spark back along the hull, cm/s, and how fast it lifts off it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float FlowSpeed = 2600.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float LiftSpeed = 320.f;

	/** Turbulence: how far a spark weaves off the flow (cm, reached at the end of its life) and how fast. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float TurbulenceCm = 70.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float TurbulenceRate = 4.5f;

	/** Backwards acceleration that bends the sparks round, cm/s2 (in normal flight scaled by its strength). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float SweepBack = 9000.f;

	/** Life of a spark, s (each gets a random time between the two). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.02"))
	float MinLifeSeconds = 0.45f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.02"))
	float MaxLifeSeconds = 0.95f;

	/** How much of its path a spark shows behind it, s, in how many segments. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.005"))
	float TrailSeconds = 0.3f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "1", ClampMax = "12"))
	int32 TrailSegments = 7;

	/** However fast a spark ends up going, its trail is never longer than this (cm): with the sweep it
	 * grew into a rail across the whole screen, and in the reference the plume stays by the hull. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "10.0"))
	float MaxTrailCm = 2000.f;

	/** Thickness, cm, and at least this share of the distance to the camera (0.005: ~4 px at 1600 px, 90 degrees). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.1"))
	float ThicknessCm = 2.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float MinScreenThickness = 0.0035f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks")
	FLinearColor QuantumColor = FLinearColor(0.1f, 0.35f, 1.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float QuantumBrightness = 90.f;

	/** What a spark looks like while it is still hot, and how fast it cools (higher = cools sooner). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks")
	FLinearColor HotColor = FLinearColor(0.55f, 0.68f, 0.95f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.1"))
	float HeatFalloff = 4.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks")
	FLinearColor FlightColor = FLinearColor(0.8f, 0.88f, 1.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float FlightBrightness = 6.f;

	/** Sparks fade out between these distances from the camera (cm): none on the lens in the cockpit. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float CameraFadeNearCm = 900.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float CameraFadeFarCm = 2600.f;

	/** Share of the emitters at the front half of the hull: the nose is what cuts through. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float NoseBias = 0.75f;

	/** Tests: how many points on the hull the sparks are born at, and whether they came from the collision. */
	UFUNCTION(BlueprintCallable, Category = "Hull Sparks")
	int32 DebugGetSpawnPointCount(bool& bOutFromCollision);

private:
	struct FSpark
	{
		FVector Origin = FVector::ZeroVector;
		/** Along the flow (back along the hull, a little off it) and the two the waves run on. */
		FVector Velocity = FVector::ZeroVector;
		FVector WaveA = FVector::ZeroVector;
		FVector WaveB = FVector::ZeroVector;
		float RateA = 1.f;
		float RateB = 1.f;
		float PhaseA = 0.f;
		float PhaseB = 0.f;
		float Turbulence = 1.f;
		float Age = 0.f;
		float Life = 0.f;
		float Brightness = 1.f;
	};

	/** Where a spark is Seconds after its birth, in the hull's space. */
	FVector SparkAt(const FSpark& Spark, float Seconds, float Sweep) const;
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
