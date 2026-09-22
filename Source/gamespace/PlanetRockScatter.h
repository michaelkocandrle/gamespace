// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "PlanetTerrain.h"
#include "PlanetRockScatter.generated.h"

class UInstancedStaticMeshComponent;
class UStaticMesh;

/** One kind of rock and how it is scattered. */
USTRUCT(BlueprintType)
struct FPlanetRockKind
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rocks")
	TObjectPtr<UStaticMesh> Mesh;

	/** Average rocks per scatter cell on flat ground and on slopes (rock), before the random count. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rocks", meta = (ClampMin = "0.0"))
	float PerCellFlat = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rocks", meta = (ClampMin = "0.0"))
	float PerCellSlope = 2.f;

	/** Uniform scale range (1 = the scan's own size). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rocks", meta = (ClampMin = "0.01"))
	float MinScale = 0.3f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rocks", meta = (ClampMin = "0.01"))
	float MaxScale = 1.2f;
};

/**
 * Rocks and boulders on a quad-sphere planet's ground near the camera (planets 4/4, after the planet
 * reference video: starcitizenreference/Planets_VideoNotes.md - scattered stones everywhere, big
 * boulders on the slopes).
 *
 * The surface is cut into cells on the terrain's own cube-face grid at CellDepth (about 46 m on
 * Veyra). Each cell's rocks come from a hash of the cell, so they are always the same rocks in the
 * same places; they stand on the exact height field (PlanetTerrain::SurfacePoint), tilted to its
 * normal and sunk in by a fraction of their size. When the camera moves to another cell, all cells
 * within ScatterRadiusM are rebuilt - a few thousand instances, cheap with Nanite meshes. Above
 * MaxAltitudeM nothing is shown: a boulder is a pixel from there.
 *
 * No collision yet: the ship passes through rocks (Docs/HANDOFF.md, known issues).
 */
UCLASS(ClassGroup = Space, meta = (BlueprintSpawnableComponent))
class GAMESPACE_API UPlanetRockScatter : public USceneComponent
{
	GENERATED_BODY()

public:
	UPlanetRockScatter();

	/** The terrain to scatter on; the planet sets it whenever its shape changes (editor included). */
	void SetTerrain(const FPlanetTerrainSettings& InSettings) { Settings = InSettings; }

	/** Makes the instance components for the kinds (BeginPlay). */
	void Initialize(const FPlanetTerrainSettings& InSettings);

	/** One update: CameraLocal is planet-local, AltitudeCm the camera's height above the ground. */
	void UpdateScatter(const FVector& CameraLocal, double AltitudeCm);

	/** Tests: rocks placed in the cells round this planet-local point (as UpdateScatter would), by kind. */
	UFUNCTION(BlueprintCallable, Category = "Rocks")
	TArray<int32> DebugCountRocksAround(const FVector& CameraLocal);

	/** Tests: the planet-local transform of every rock of a kind in one cell round this point. */
	UFUNCTION(BlueprintCallable, Category = "Rocks")
	TArray<FTransform> DebugRocksInCell(const FVector& PointLocal, int32 Kind);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rocks")
	TArray<FPlanetRockKind> Kinds;

	/** Depth of the cube-face grid the cells use (12 on a 120 km planet: ~46 m cells). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rocks", meta = (ClampMin = "4", ClampMax = "20"))
	int32 CellDepth = 12;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rocks", meta = (ClampMin = "10.0", Units = "m"))
	float ScatterRadiusM = 700.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rocks", meta = (ClampMin = "0.0", Units = "m"))
	float MaxAltitudeM = 2500.f;

	/** Slope (1 - cos of the ground's tilt) from which a cell counts as rock: 0.05 is ~18 degrees. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rocks", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float SlopeRockStart = 0.03f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rocks", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float SlopeRockEnd = 0.12f;

	/** How far a rock is sunk into the ground, as a share of its height. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rocks", meta = (ClampMin = "0.0", ClampMax = "0.9"))
	float SinkFraction = 0.25f;

	/** Rocks cluster: this share of cells is nearly empty, which keeps the ground from looking sprinkled. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Rocks", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float EmptyCellShare = 0.35f;

private:
	struct FCellKey
	{
		int32 Face = 0;
		int32 X = 0;
		int32 Y = 0;
		bool operator==(const FCellKey& Other) const { return Face == Other.Face && X == Other.X && Y == Other.Y; }
	};

	void CellsAround(const FVector& CameraLocal, TArray<FCellKey>& OutCells) const;
	void RocksInCell(const FCellKey& Cell, TArray<TArray<FTransform>>& InOut) const;

	FPlanetTerrainSettings Settings;
	bool bInitialized = false;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UInstancedStaticMeshComponent>> Instances;

	/** The cell the camera was in at the last rebuild; INT_MIN when hidden. */
	FCellKey LastCell{ -1, INT_MIN, INT_MIN };
	bool bShown = false;
};
