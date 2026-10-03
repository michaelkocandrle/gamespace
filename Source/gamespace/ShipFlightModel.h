// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

struct FCelestialEnvironment;
enum class ELandingBlocker : uint8;

/**
 * The pure maths of the ship's flight: no state, no world, no UObject. Every tuning value comes in as an argument,
 * so a function gives the same answer for the same numbers, in a headless test or in the tick.
 *
 * First step of splitting ASpaceshipPawn (Docs/Reviews/2026-09-30_spaceshippawn_split_plan.md). The pawn keeps its
 * UFUNCTIONs of the same names - tests, the HUD and the shot runner call them - and forwards here with its UPROPERTY
 * values (the tuning stays on the pawn: Blueprint overrides and <Ship>_setup.json keys name it). The argument types
 * are the pawn's (float), so the results are the same to the bit.
 */
struct GAMESPACE_API FShipFlightModel
{
	/** 1 g in cm/s^2: G-Safe limits and the G-meter. */
	static constexpr double StandardGravityCmS2 = 980.665;

	// --- IFCS ----------------------------------------------------------------------------------------------------

	/**
	 * G-Safe on a thruster command (local cm/s^2, X forward, Z up): vertical to MaxVerticalG, the whole vector to
	 * MaxG. With bLateralFirst (ComStab) sideways and vertical keep what they need and forward gets the rest;
	 * otherwise everything scales down together.
	 */
	static FVector LimitThrustForPilot(const FVector& LocalAcceleration, bool bLateralFirst, float MaxG, float MaxVerticalG);

	// --- Environment ---------------------------------------------------------------------------------------------

	struct FDrag
	{
		float SpaceLinearDamping = 0.f;
		float LinearDamping = 0.f;
		float QuadraticDrag = 0.f;
		float GravityScale = 1.f;
	};

	/** Acceleration the environment puts on a ship with this velocity, cm/s^2: drag and gravity, no thrust. */
	static FVector EnvironmentAcceleration(const FCelestialEnvironment& Environment, const FVector& Velocity, const FDrag& Drag);

	struct FHeat
	{
		float ReferenceSpeed = 1.f;
		float Onset = 0.f;
		float Full = 1.f;
	};

	/** Entry heat target, 0..1, for a speed in cm/s at an atmosphere density. */
	static float HeatTarget(float AtmosphereDensity, float SpeedCmS, const FHeat& Heat);

	// --- Landing -------------------------------------------------------------------------------------------------

	struct FLandingLimits
	{
		float MaxGapCm = 0.f;
		float MaxSlopeDeg = 0.f;
		float MaxSpeed = 0.f;
		float MaxTiltDeg = 0.f;
	};

	/** The touchdown rule on its own: the first blocker for these measurements, or None. */
	static ELandingBlocker EvaluateLanding(float GroundGap, float Speed, float TiltDeg, float SlopeDeg, bool bEngineInput, const FLandingLimits& Limits);

	/**
	 * The touchdown rule with the gear: GearUp unless the gear is down and locked, otherwise EvaluateLanding on the
	 * gap under the pads (hull gap minus GearExtensionCm, pads pressed into the ground count as 0). HullGap < 0 means
	 * nothing below.
	 */
	static ELandingBlocker EvaluateTouchdown(float HullGap, float Speed, float TiltDeg, float SlopeDeg, bool bEngineInput, bool bGearDown,
		float GearExtensionCm, const FLandingLimits& Limits);

	/**
	 * Velocity after one step of Coulomb ground friction: the part along the surface loses at most Friction x the
	 * normal load per second, so a resting ship stays at rest where Friction >= tan(slope) and slides on steeper ground.
	 */
	static FVector ApplyGroundFriction(const FVector& Velocity, const FVector& SurfaceNormal, const FVector& Up, float GravityCmS2,
		float DeltaSeconds, float Friction);

	/** One step of the landed alignment from Current towards the terrain normal (exponential at AlignRate per s). */
	static FRotator LandedRotationStep(const FRotator& Current, const FVector& SurfaceNormal, float DeltaSeconds, float AlignRate);

	/** Keeps the heading, puts the ship's up on Normal. */
	static FQuat LevelOnSurface(const FQuat& Current, const FVector& Normal);

	/** Angle between two directions, degrees. */
	static float AngleBetweenDeg(const FVector& A, const FVector& B);

	/**
	 * The pose of a ship standing on three gear pads (SC-2a, landing on a slope): its up on the plane through the
	 * three ground points, heading kept, and moved along that plane's normal only, so the pads' plane lies
	 * RestHeightCm above the ground's (the gear's reach below its sockets; 0 when the sockets are the pads' soles).
	 * PadsLocal are the pads in actor space. One step: the ground points come from straight below the pads of the
	 * current pose, so call it again with the ground under the new pose to settle it. False when the three ground
	 * points are (nearly) in a line.
	 */
	static bool TripodRest(const FVector& Location, const FQuat& Current, const FVector (&PadsLocal)[3], const FVector (&Ground)[3],
		double RestHeightCm, FVector& OutLocation, FQuat& OutRotation, FVector& OutNormal);

	// --- Gear ----------------------------------------------------------------------------------------------------

	struct FGearShape
	{
		float ExtensionCm = 0.f;
		float FoldDeg = 0.f;
		float PadThicknessCm = 0.f;
		float StrutRadiusCm = 0.f;
		float PadRadiusCm = 0.f;
	};

	/**
	 * One gear leg relative to its socket at a deploy fraction (0 stowed .. 1 down): [0] pivot rotation (X pitch),
	 * [1] sleeve centre, [2] sleeve scale, [3] piston centre, [4] piston scale, [5] pad centre, [6] pad scale - in
	 * the pivot's frame, for the 100 cm engine cylinder. bNose folds forward, the others backward.
	 */
	static TArray<FVector> GearLegPose(float Deploy, bool bNose, const FGearShape& Gear);

	/** How far a modelled gear part sits above its down position at a deploy fraction, cm (eased). */
	static float GearStowOffsetCm(float Deploy, float StowTravelCm);

	// --- VTOL ----------------------------------------------------------------------------------------------------

	/**
	 * How far VTOL turns the hull back towards level this frame, as a local pitch / roll step; zero without VTOL,
	 * without an up, or once level. The whole LevelRate only once VtolBlend is 1.
	 */
	static FRotator VtolLevelStep(const FQuat& ShipRotation, const FVector& WorldUp, float DeltaSeconds, float VtolBlend, float LevelRate);

	// --- Quantum -------------------------------------------------------------------------------------------------

	struct FQuantumDrive
	{
		float RampSeconds = 0.f;
		float AccelerationKmS2 = 0.f;
		float MaxSpeedKmS = 0.f;
		float ExitSpeed = 0.f;
		float ArrivalRadii = 0.f;
		float MinArrivalKm = 0.f;
		float FuelPer1000Km = 0.f;
	};

	/** Where a jump to a body of this radius ends: this far from its surface, cm. */
	static double QuantumArrivalAltitude(double BodyRadiusCm, const FQuantumDrive& Drive);

	/**
	 * Speed in the jump for this remaining distance and current speed, cm/s, SecondsIntoJump into the jump:
	 * accelerates (building up over RampSeconds) to MaxSpeedKmS and brakes so it arrives at ExitSpeed.
	 */
	static double QuantumSpeedAt(double RemainingCm, double CurrentSpeedCmS, float DeltaSeconds, float SecondsIntoJump, const FQuantumDrive& Drive);

	/** Share of a full tank a jump of this length burns, 0..1. */
	static float QuantumFuelUse(double DistanceCm, const FQuantumDrive& Drive);

	/** Whether the straight segment Start-End passes within Radius of Centre (a body in the way). */
	static bool SegmentHitsSphere(const FVector& Start, const FVector& End, const FVector& Centre, double Radius);
};
