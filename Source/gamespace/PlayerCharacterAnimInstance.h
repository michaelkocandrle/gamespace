// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimInstanceProxy.h"
#include "PlanetTerrain.h"
#include "PlayerCharacterAnimInstance.generated.h"

class UAnimSequence;
class UBlendSpace;

/** What foot IK did on the last evaluated frame, for the HUD and tests. */
USTRUCT(BlueprintType)
struct FFootIKState
{
	GENERATED_BODY()

	/** IK had ground to work with (standing or walking on a planet, or a debug override). */
	UPROPERTY(BlueprintReadOnly, Category = "Foot IK")
	bool bActive = false;

	/** A foot wanted to move further than the limits allow. */
	UPROPERTY(BlueprintReadOnly, Category = "Foot IK")
	bool bClamped = false;

	/** Pelvis shift along the character's up, cm (negative = lowered). */
	UPROPERTY(BlueprintReadOnly, Category = "Foot IK")
	float PelvisOffsetCm = 0.f;

	/** Foot shift along the character's up, cm. */
	UPROPERTY(BlueprintReadOnly, Category = "Foot IK")
	float LeftFootOffsetCm = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Foot IK")
	float RightFootOffsetCm = 0.f;
};

/**
 * Evaluates the player character's pose natively, without an Animation Blueprint.
 *
 * Why native: the template's ABP and foot IK Control Rig assume gravity along world -Z (ground
 * speed from the XY velocity, traces straight down). On a round planet "down" is anywhere; at
 * TestSpace's landing spot it is world +X. Everything here works in the character's own frame.
 *
 * Locomotion: idle / walk / jog sampled directly from the Mannequin sequences, walk and jog kept
 * in step by a shared normalised phase and played at the rate that matches the ground speed (the
 * reference speeds come from the template blend space). Jump start, fall loop and a landing blend
 * on top.
 *
 * Foot IK: capsule collision stands on the planet's coarse collision tiles (~2.4 m cells), while
 * the visible terrain has 33 cm cells. Each foot's ground height is taken from the planet's
 * analytic height field - the same function the visible mesh is built from - not from a trace,
 * so the feet land on what you see. The pelvis drops to let the lower foot reach, both legs are
 * solved with two-bone IK in their animated bend plane, and the feet tilt with the slope. Limits
 * keep it from stretching the legs when the difference is large.
 */
UCLASS(Transient)
class GAMESPACE_API UPlayerCharacterAnimInstance : public UAnimInstance
{
	GENERATED_BODY()

public:
	UPlayerCharacterAnimInstance();

	UFUNCTION(BlueprintPure, Category = "Player Animation")
	FFootIKState GetFootIKState() const { return FootIKReadout; }

	/** Walk and jog reference speeds in use, cm/s. */
	UFUNCTION(BlueprintPure, Category = "Player Animation")
	FVector2D GetLocomotionReferenceSpeeds() const;

	/** Tests: how many times the proxy ran PreUpdate, Update and Evaluate. */
	FIntVector GetProxyCounters() const { return ProxyCounters; }

	/**
	 * Tests only: replaces the character's movement state and, optionally, the ground height under
	 * each foot (cm along the character's up, relative to the capsule floor).
	 */
	void SetDebugOverride(bool bEnable, float GroundSpeed, bool bFalling, bool bOverrideGround, float LeftGroundCm, float RightGroundCm);

	// --- Animations (Mannequin template pack) ---------------------------------------------------

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Player Animation")
	TObjectPtr<UAnimSequence> IdleAnimation;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Player Animation")
	TObjectPtr<UAnimSequence> WalkAnimation;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Player Animation")
	TObjectPtr<UAnimSequence> JogAnimation;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Player Animation")
	TObjectPtr<UAnimSequence> JumpAnimation;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Player Animation")
	TObjectPtr<UAnimSequence> FallLoopAnimation;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Player Animation")
	TObjectPtr<UAnimSequence> LandAnimation;

	/** Where the walk and jog speeds are read from: the sample positions on its Speed axis. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Player Animation")
	TObjectPtr<UBlendSpace> SpeedReferenceBlendSpace;

	/** Used when the blend space does not give a speed for the walk / jog sequence, cm/s. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Player Animation")
	float FallbackWalkSpeed = 200.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Player Animation")
	float FallbackJogSpeed = 500.f;

	// --- Foot IK --------------------------------------------------------------------------------

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Foot IK")
	bool bEnableFootIK = true;

	/** How far the pelvis may drop so the lower foot reaches the ground, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Foot IK", meta = (ClampMin = "0.0"))
	float MaxPelvisDropCm = 40.f;

	/** How far the pelvis may rise when the ground under both feet is above the capsule floor, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Foot IK", meta = (ClampMin = "0.0"))
	float MaxPelvisRaiseCm = 15.f;

	/** How far a single foot may be raised or lowered from its animated height, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Foot IK", meta = (ClampMin = "0.0"))
	float MaxFootOffsetCm = 45.f;

	/** Feet tilt with the terrain up to this angle. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Foot IK", meta = (ClampMin = "0.0", ClampMax = "60.0"))
	float MaxFootTiltDeg = 30.f;

	/** How fast offsets follow the ground, per second; lower is smoother but lags on bumps. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Foot IK", meta = (ClampMin = "0.1"))
	float FootIKInterpSpeed = 18.f;

protected:
	virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
	virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy) override;

private:
	friend struct FPlayerCharacterAnimProxy;

	FFootIKState FootIKReadout;
	FIntVector ProxyCounters = FIntVector::ZeroValue;

	bool bDebugOverride = false;
	float DebugGroundSpeed = 0.f;
	bool bDebugFalling = false;
	bool bDebugOverrideGround = false;
	float DebugLeftGroundCm = 0.f;
	float DebugRightGroundCm = 0.f;
};

/** Anim-thread side of UPlayerCharacterAnimInstance. Game-thread data is copied in PreUpdate. */
struct FPlayerCharacterAnimProxy : public FAnimInstanceProxy
{
	FPlayerCharacterAnimProxy() = default;
	explicit FPlayerCharacterAnimProxy(UAnimInstance* InAnimInstance) : FAnimInstanceProxy(InAnimInstance) {}

	virtual void Initialize(UAnimInstance* InAnimInstance) override;
	virtual void PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds) override;
	virtual void Update(float DeltaSeconds) override;
	virtual bool Evaluate(FPoseContext& Output) override;

private:
	void ApplyFootIK(FPoseContext& Output);
	bool GroundUnderFoot(const FVector& FootComponent, float& OutGroundZ, FVector& OutNormalComponent) const;

	// Copied from the instance on the game thread.
	UAnimSequence* Idle = nullptr;
	UAnimSequence* Walk = nullptr;
	UAnimSequence* Jog = nullptr;
	UAnimSequence* Jump = nullptr;
	UAnimSequence* Fall = nullptr;
	UAnimSequence* Land = nullptr;
	float WalkSpeed = 200.f;
	float JogSpeed = 500.f;

	bool bFootIK = true;
	float MaxPelvisDrop = 40.f;
	float MaxPelvisRaise = 15.f;
	float MaxFootOffset = 45.f;
	float MaxFootTilt = 30.f;
	float IKInterpSpeed = 18.f;

	// Movement state.
	float GroundSpeed = 0.f;
	float VerticalSpeed = 0.f;
	bool bFalling = false;

	// Ground source for foot IK.
	bool bTerrainValid = false;
	FPlanetTerrainSettings Terrain;
	FTransform PlanetToWorld;
	FTransform ComponentToWorld;
	bool bGroundOverride = false;
	float OverrideLeftGround = 0.f;
	float OverrideRightGround = 0.f;

	// Playback state (anim thread).
	float DeltaTime = 0.f;
	double IdleTime = 0.0;
	double Phase = 0.0;
	float MoveBlend = 0.f;
	float JogAlpha = 0.f;
	float AirBlend = 0.f;
	double AirTime = 0.0;
	double LandTime = 100.0;
	bool bWasFalling = false;
	bool bJumpStart = false;
	bool bLanding = false;

	// Foot IK state (anim thread), smoothed.
	float PelvisOffset = 0.f;
	float LeftOffset = 0.f;
	float RightOffset = 0.f;
	FFootIKState LastFootIK;
	int32 PreUpdateCount = 0;
	int32 UpdateCount = 0;
	int32 EvaluateCount = 0;
};
