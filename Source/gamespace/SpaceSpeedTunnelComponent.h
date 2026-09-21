// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "SpaceSpeedTunnelComponent.generated.h"

/** One wall of the tunnel: a cylinder round the flight path at this distance from the camera. */
USTRUCT(BlueprintType)
struct FSpeedTunnelLayer
{
	GENERATED_BODY()

	/** Distance of the wall from the flight path through the camera, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "100.0"))
	float RadiusCm = 6000.f;

	/** Everything this wall draws is multiplied by this. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.0"))
	float Brightness = 1.f;

	/** Lanes round the wall; each holds one streak per PeriodCm, so this is the density of streaks. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "1.0"))
	float Lanes = 120.f;

	/** How much of the soft light beams this wall carries (0 none). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.0"))
	float BeamWeight = 0.f;
};

/**
 * The look of high speed, for cruise (21. 9. 2026, the author against two Star Citizen quantum
 * travel frames): streaks radiating from the point the ship flies at, soft cold beams of light
 * converging on it, and a glow at that point.
 *
 * The space dust (USpaceDustComponent) cannot do this on its own. Its specks stand still in the
 * world, which is right up to a few hundred m/s; at cruise the ship covers the whole dust box in a
 * frame, every speck lands somewhere new each frame, and the streaks turn into random flicker. So
 * above FadeInSpeed this takes over: a few open cylinders round the camera, aligned with the flight
 * path, whose material (M_SpeedTunnel) draws the streaks, beams and glow. Seen from inside, a
 * cylinder's wall converges on the vanishing point by plain perspective, so the streaks radiate
 * from it without any screen-space trickery, and the ship itself stays in front of them.
 *
 * The streaks scroll by a distance this component accumulates (not the material's time): their
 * apparent speed follows the ship's but is held below MaxApparentSpeed, because a streak that jumps
 * further than its own length each frame strobes instead of flowing.
 *
 * Per instance custom data: 0 radius, 1 brightness, 2 seed, 3 beam weight, 4 lanes.
 */
UCLASS(ClassGroup = Space, meta = (BlueprintSpawnableComponent))
class GAMESPACE_API USpaceSpeedTunnelComponent : public UInstancedStaticMeshComponent
{
	GENERATED_BODY()

public:
	USpaceSpeedTunnelComponent();

	virtual void BeginPlay() override;

	/** Places the tunnel round ViewLocation for an observer moving at Velocity (cm/s). */
	void UpdateTunnel(const FVector& ViewLocation, const FVector& Velocity, float DeltaSeconds);

	/** Hides the tunnel until the next UpdateTunnel. */
	void HideTunnel();

	/** 0..1: how much of the tunnel is showing at this speed (cm/s). For tests. */
	UFUNCTION(BlueprintPure, Category = "Speed Tunnel")
	float ComputeAlpha(float Speed) const;

	/** How far the streaks scroll per second at this speed (cm/s), for tests. */
	UFUNCTION(BlueprintPure, Category = "Speed Tunnel")
	float ComputeApparentSpeed(float Speed) const;

	/** Streak length at this speed (cm/s), cm. For tests. */
	UFUNCTION(BlueprintPure, Category = "Speed Tunnel")
	float ComputeStreakLength(float Speed) const;

	/** Nothing below this speed, cm/s (500 m/s: above SCM, where the dust starts to give out). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.0"))
	float FadeInSpeed = 50000.f;

	/** Full strength from this speed, cm/s. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.0"))
	float FullSpeed = 250000.f;

	/** The streaks never scroll faster than this, cm/s; see the class comment. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "1.0"))
	float MaxApparentSpeed = 200000.f;

	/** A streak is as long as the apparent distance covered in this time. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.0", Units = "s"))
	float StreakSeconds = 0.05f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "1.0"))
	float MinStreakCm = 2000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "1.0"))
	float MaxStreakCm = 15000.f;

	/** Along the wall, a lane repeats its streak every this many cm. Longer than MaxStreakCm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "100.0"))
	float PeriodCm = 40000.f;

	/** Half the length of the tunnel, cm: how far ahead the streaks reach towards the vanishing point. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "100.0"))
	float HalfLengthCm = 150000.f;

	/**
	 * Half width of a streak on a wall 25 m out, cm; farther walls scale it with their distance, so
	 * every wall's streaks are equally thin on screen. Not a share of the lane, which made the near
	 * wall's streaks (few lanes, close) fat bars; nor one width for all walls, which made the far
	 * ones vanish (both 21. 9. 2026).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.1"))
	float StreakWidthCm = 7.f;

	/** How far a streak's colour may lean towards BeamColor, 0..1: a few cold blue ones among the white. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float StreakColorSpread = 0.5f;

	/** Fraction of the lanes that hold a streak at all; the rest stay dark so the streaks do not form a comb. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float Fill = 0.55f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel")
	FLinearColor StreakColor = FLinearColor(0.85f, 0.92f, 1.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.0"))
	float StreakBrightness = 10.f;

	/** The soft shafts of light converging on the vanishing point. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel")
	FLinearColor BeamColor = FLinearColor(0.35f, 0.6f, 1.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.0"))
	float BeamBrightness = 2.f;

	/** Beams round the tunnel, and how sharply they stand out of the gaps between them. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "1.0"))
	float BeamCount = 24.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.5"))
	float BeamSharpness = 6.f;

	/** The glow on the vanishing point, where the tunnel's far end closes. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel")
	FLinearColor GlowColor = FLinearColor(0.8f, 0.9f, 1.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.0"))
	float GlowBrightness = 2.f;

	/** The walls, nearest first. The near one sweeps past fast and sparse, the far one carries the beams. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel")
	TArray<FSpeedTunnelLayer> Layers;

private:
	void PushParameters(const FVector& Direction, float Alpha, float StreakLength);

	/** The mesh's own bounds: the tunnel is scaled from them, so the pivot of the cylinder does not matter. */
	FBox MeshBounds = FBox(ForceInit);
	TObjectPtr<UMaterialInstanceDynamic> TunnelMaterial;
	double OffsetCm = 0.0;
	bool bHidden = true;
};
