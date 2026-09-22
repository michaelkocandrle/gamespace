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
 * Sparks, not lines (the author, 22. 9. 2026: "just lines, it should look like sparks"): in the
 * reference they spray in tufts from a few hot spots on the hull (the nose and the lower edges),
 * fan out and bend back, thin blue hairs. So a few emitters sit on the hull (points on the hull's
 * collision shapes; a shell of its bounds when it has none) and move every second or so;
 * each spark is shot off its emitter in a cone round the surface normal and is swept back
 * (constant backwards acceleration), which curves it. A spark is drawn as a chain of short
 * segments along the last moments of its path (a curved trail that thins towards its tail), with
 * M_HullSpark (custom data: 0 fade, 1 brightness). The width grows with distance to stay a pixel
 * or two wide.
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

	/** Emitters on the hull at once (the tufts), and how long one stays put, s (random between the two). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "1", ClampMax = "64"))
	int32 EmitterCount = 7;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.05"))
	float EmitterMinSeconds = 0.4f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.05"))
	float EmitterMaxSeconds = 1.3f;

	/** How fast a spark leaves the hull, cm/s, and how wide its cone is (1 = 45 degrees off the normal). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float BurstSpeed = 1800.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0", ClampMax = "4.0"))
	float ConeSpread = 0.7f;

	/** Backwards acceleration that bends the sparks round, cm/s2 (in normal flight scaled by its strength). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float SweepBack = 14000.f;

	/** Life of a spark, s (each gets a random time between the two). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.02"))
	float MinLifeSeconds = 0.25f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.02"))
	float MaxLifeSeconds = 0.6f;

	/** How much of its path a spark shows behind it, s, in how many segments. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.005"))
	float TrailSeconds = 0.09f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "1", ClampMax = "12"))
	int32 TrailSegments = 5;

	/** Thickness, cm, and at least this share of the distance to the camera (0.005: ~4 px at 1600 px, 90 degrees). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.1"))
	float ThicknessCm = 2.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float MinScreenThickness = 0.005f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks")
	FLinearColor QuantumColor = FLinearColor(0.25f, 0.55f, 1.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float QuantumBrightness = 30.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks")
	FLinearColor FlightColor = FLinearColor(0.8f, 0.88f, 1.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float FlightBrightness = 6.f;

	/** Sparks fade out between these distances from the camera (cm): none on the lens in the cockpit. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float CameraFadeNearCm = 500.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0"))
	float CameraFadeFarCm = 1200.f;

	/** Share of the emitters at the front half of the hull: the nose is what cuts through. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hull Sparks", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float NoseBias = 0.6f;

	/** Tests: how many points on the hull the sparks are born at, and whether they came from the collision. */
	UFUNCTION(BlueprintCallable, Category = "Hull Sparks")
	int32 DebugGetSpawnPointCount(bool& bOutFromCollision);

private:
	struct FSpark
	{
		int32 Emitter = 0;
		FVector Origin = FVector::ZeroVector;
		FVector Velocity = FVector::ZeroVector;
		float Age = 0.f;
		float Life = 0.f;
		float Brightness = 1.f;
	};

	struct FEmitter
	{
		int32 Point = 0;
		float TimeLeft = 0.f;
	};

	/** Where a spark is Seconds after its birth, in the hull's space. */
	FVector SparkAt(const FSpark& Spark, float Seconds, float Sweep) const;
	void MoveEmitter(FEmitter& Emitter);
	void FindSpawnPoints();
	void Respawn(FSpark& Spark, bool bRandomAge);

	TWeakObjectPtr<UPrimitiveComponent> Hull;
	TArray<FVector> Points;
	TArray<FVector> Normals;
	/** Indexes into Points: the front ones and the rest, for NoseBias. */
	TArray<int32> FrontPoints;
	TArray<int32> BackPoints;
	bool bPointsFromCollision = false;
	TArray<FEmitter> Emitters;
	TArray<FSpark> Sparks;
	TArray<FTransform> Transforms;
	FRandomStream Random = FRandomStream(0x5A2C);
	TObjectPtr<UMaterialInstanceDynamic> SparkMaterial;
	bool bHidden = true;
};
