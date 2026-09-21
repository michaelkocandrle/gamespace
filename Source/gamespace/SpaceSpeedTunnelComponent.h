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
 * The look of a quantum jump (SC-4, after the reference video in starcitizenreference/
 * QuantumTravel_VideoNotes.md): a dim blue-grey fog tunnel, dark down the middle, a few thin streaks
 * radiating from the point the ship flies at, soft cold beams converging on it, a glow there, and now
 * and then a few broad green flares - strongest at the moment of the jump. It shows only in a jump
 * (UpdateTunnel's Intensity is the pawn's quantum blend): outside quantum Star Citizen has almost no
 * speed lines at all.
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

	/** Places the tunnel round ViewLocation for an observer moving at Velocity (cm/s), at Intensity 0..1. */
	void UpdateTunnel(const FVector& ViewLocation, const FVector& Velocity, float DeltaSeconds, float Intensity);

	/** A flare now, at this strength (the jump itself: 1.5). */
	void TriggerFlare(float Strength);

	/** Hides the tunnel until the next UpdateTunnel. */
	void HideTunnel();

	/** How far the streaks scroll per second at this speed (cm/s), for tests. */
	UFUNCTION(BlueprintPure, Category = "Speed Tunnel")
	float ComputeApparentSpeed(float Speed) const;

	/** Streak length at this speed (cm/s), cm. For tests. */
	UFUNCTION(BlueprintPure, Category = "Speed Tunnel")
	float ComputeStreakLength(float Speed) const;

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
	float Fill = 0.2f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel")
	FLinearColor StreakColor = FLinearColor(0.85f, 0.92f, 1.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.0"))
	float StreakBrightness = 12.f;

	/** The soft shafts of light converging on the vanishing point. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel")
	FLinearColor BeamColor = FLinearColor(0.4f, 0.55f, 1.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.0"))
	float BeamBrightness = 1.2f;

	/** Beams round the tunnel, and how sharply they stand out of the gaps between them. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "1.0"))
	float BeamCount = 16.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.5"))
	float BeamSharpness = 3.f;

	/** The glow on the vanishing point, where the tunnel's far end closes. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel")
	FLinearColor GlowColor = FLinearColor(0.8f, 0.9f, 1.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.0"))
	float GlowBrightness = 2.f;

	/** The lit fog on the walls beside the ship (its colour carries the brightness). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel")
	FLinearColor HazeColor = FLinearColor(0.05f, 0.07f, 0.13f);

	/** The green flares: colour (with brightness), how often (s, a random time between the two) and how long. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel")
	FLinearColor FlareColor = FLinearColor(0.15f, 1.4f, 0.6f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.5", Units = "s"))
	float FlareIntervalMinSeconds = 8.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.5", Units = "s"))
	float FlareIntervalMaxSeconds = 18.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.1", Units = "s"))
	float FlareSeconds = 1.8f;

	/**
	 * The fog behind the streak walls that hides the sky in a jump (M_QuantumFog, a second cylinder):
	 * its distance, how much it covers, and its colour beside the ship and down the middle.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "100.0"))
	float FogRadiusCm = 25000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float FogOpacity = 0.9f;

	/**
	 * The fog's cover down the middle towards the vanishing point, as a share of FogOpacity. Thin fog
	 * everywhere read as a wash (the author, 21. 9. 2026) and thin down the middle showed the
	 * destination planet whole; what reads as a tunnel is dense fog that is dark in the middle and
	 * lit, in shafts, on the walls - the reference's dark hole.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float FogCentreOpacity = 0.95f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel")
	FLinearColor FogNearColor = FLinearColor(0.035f, 0.05f, 0.09f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel")
	FLinearColor FogFarColor = FLinearColor(0.002f, 0.003f, 0.006f);

	/** The walls, nearest first. The near one sweeps past fast and sparse, the far one carries the beams. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Speed Tunnel")
	TArray<FSpeedTunnelLayer> Layers;

private:
	void PushParameters(const FVector& Direction, float Alpha, float StreakLength);
	void UpdateFlare(float DeltaSeconds);

	/** The running flare: time into it (negative: none), its strength and pattern, and the wait for the next. */
	float FlareTime = -1.f;
	float FlareStrength = 1.f;
	float FlareSeed = 1.f;
	float FlareWait = 10.f;
	FRandomStream FlareRandom = FRandomStream(0x0F1A);

	/** The mesh's own bounds: the tunnel is scaled from them, so the pivot of the cylinder does not matter. */
	FBox MeshBounds = FBox(ForceInit);
	TObjectPtr<UMaterialInstanceDynamic> TunnelMaterial;

	/** The fog cylinder, made in BeginPlay when M_QuantumFog exists. */
	UPROPERTY(Transient)
	TObjectPtr<UStaticMeshComponent> Fog;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> FogMaterial;
	double OffsetCm = 0.0;
	bool bHidden = true;
};
