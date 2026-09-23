// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SpaceInterior.generated.h"

class UBoxComponent;
class UStaticMeshComponent;

/**
 * Artificial gravity inside a ship: a box in which a character's "down" is the box's -Z and its
 * strength GravityCmS2, whatever planet is near. APlayerCharacter asks for it before it falls back
 * to the nearest celestial body. Placed by Tools/Assets/import_interior.py around the Steadfast
 * interior.
 */
UCLASS()
class GAMESPACE_API ASpaceGravityVolume : public AActor
{
	GENERATED_BODY()

public:
	ASpaceGravityVolume();

	/** The volume that contains Location, or null. */
	static const ASpaceGravityVolume* FindAt(const UWorld* World, const FVector& Location);

	UFUNCTION(BlueprintPure, Category = "Interior")
	bool ContainsPoint(const FVector& Location) const;

	UFUNCTION(BlueprintPure, Category = "Interior")
	FVector GetUp() const { return GetActorUpVector(); }

	/** cm/s^2; 981 is Earth. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interior", meta = (ClampMin = "0.0"))
	float GravityCmS2 = 981.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Interior")
	TObjectPtr<UBoxComponent> Volume;
};

/**
 * Two leaves that slide apart when a player-controlled pawn comes near, and close behind it. The
 * leaves share one mesh (a single leaf, centred on its origin, thin along X - Tools/Blender/
 * build_steadfast_interior.py exports it as DoorLeaf.glb); the actor's origin is the middle of the
 * threshold and its X the way through. OnConstruction lays the leaves out from the mesh's bounds.
 */
UCLASS()
class GAMESPACE_API ASpaceSlidingDoor : public AActor
{
	GENERATED_BODY()

public:
	ASpaceSlidingDoor();

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	/** Puts both leaves on the leaf mesh and lays them out closed, from the mesh's bounds. */
	UFUNCTION(BlueprintCallable, Category = "Door")
	void LayoutLeaves();

	/** 0 closed, 1 open. */
	UFUNCTION(BlueprintPure, Category = "Door")
	float GetOpenness() const { return Openness; }

	/** Tests and shots: 1 opens, 0 closes, -1 back to automatic. */
	UFUNCTION(BlueprintCallable, Category = "Door")
	void ForceOpen(int32 State) { Forced = State; }

	/** Closed-leaf offset from the actor along Y, and the slide, for a leaf this wide. */
	static FVector ComputeLeafLocation(float LeafWidthCm, float LeafHeightCm, float Side, float Openness);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Door")
	TObjectPtr<UStaticMeshComponent> LeafA;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Door")
	TObjectPtr<UStaticMeshComponent> LeafB;

	/** A pawn nearer than this (to the threshold) opens the door, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door", meta = (ClampMin = "50.0"))
	float TriggerRadiusCm = 260.f;

	/** Seconds from closed to open. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door", meta = (ClampMin = "0.05"))
	float OpenSeconds = 0.55f;

private:
	float Openness = 0.f;
	int32 Forced = -1;
	FVector LeafSize = FVector::ZeroVector;
	void PlaceLeaves();
};
