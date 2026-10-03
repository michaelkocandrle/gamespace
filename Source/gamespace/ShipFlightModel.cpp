// Copyright Epic Games, Inc. All Rights Reserved.

#include "ShipFlightModel.h"

#include "CelestialBody.h"
#include "ShipLandingComponent.h"

// The bodies moved here from ASpaceshipPawn unchanged (split step 1, 30. 9. 2026); member reads became arguments.

FVector FShipFlightModel::LimitThrustForPilot(const FVector& LocalAcceleration, bool bLateralFirst, float MaxG, float MaxVerticalG)
{
	const double MaxTotal = FMath::Max(double(MaxG), 0.0) * StandardGravityCmS2;
	const double MaxVertical = FMath::Min(double(MaxVerticalG) * StandardGravityCmS2, MaxTotal);
	FVector Result = LocalAcceleration;
	Result.Z = FMath::Clamp(Result.Z, -MaxVertical, MaxVertical);
	if (Result.Size() <= MaxTotal)
	{
		return Result;
	}
	if (!bLateralFirst)
	{
		return Result.GetSafeNormal() * MaxTotal;
	}
	// Sideways and vertical first: they are what keeps the flight path on the nose.
	const FVector Lateral(0.0, Result.Y, Result.Z);
	const double LateralSize = Lateral.Size();
	if (LateralSize >= MaxTotal)
	{
		return Lateral * (MaxTotal / LateralSize);
	}
	const double Remaining = FMath::Sqrt(MaxTotal * MaxTotal - LateralSize * LateralSize);
	Result.X = FMath::Clamp(Result.X, -Remaining, Remaining);
	return Result;
}

FVector FShipFlightModel::EnvironmentAcceleration(const FCelestialEnvironment& Environment, const FVector& Velocity, const FDrag& Drag)
{
	const double DragRate = Drag.SpaceLinearDamping + (Drag.LinearDamping + Drag.QuadraticDrag * Velocity.Size()) * Environment.AtmosphereDensity;
	return -Velocity * DragRate - Environment.Up * (Environment.GravityCmS2 * Drag.GravityScale);
}

float FShipFlightModel::HeatTarget(float AtmosphereDensity, float SpeedCmS, const FHeat& Heat)
{
	const double Relative = SpeedCmS / Heat.ReferenceSpeed;
	const double Heating = AtmosphereDensity * Relative * Relative * Relative;
	return float(FMath::Clamp((Heating - Heat.Onset) / FMath::Max(double(Heat.Full - Heat.Onset), 0.01), 0.0, 1.0));
}

ELandingBlocker FShipFlightModel::EvaluateLanding(float GroundGap, float Speed, float TiltDeg, float SlopeDeg, bool bEngineInput, const FLandingLimits& Limits)
{
	if (GroundGap < 0.f || GroundGap > Limits.MaxGapCm)
	{
		return ELandingBlocker::TooHigh;
	}
	if (SlopeDeg > Limits.MaxSlopeDeg)
	{
		return ELandingBlocker::TooSteep;
	}
	if (Speed > Limits.MaxSpeed)
	{
		return ELandingBlocker::TooFast;
	}
	if (TiltDeg > Limits.MaxTiltDeg)
	{
		return ELandingBlocker::Tilted;
	}
	if (bEngineInput)
	{
		return ELandingBlocker::EngineInput;
	}
	return ELandingBlocker::None;
}

ELandingBlocker FShipFlightModel::EvaluateTouchdown(float HullGap, float Speed, float TiltDeg, float SlopeDeg, bool bEngineInput, bool bGearDown,
	float GearExtensionCm, const FLandingLimits& Limits)
{
	// First, so the warning shows all the way down through the probe zone, not only at the ground.
	if (!bGearDown)
	{
		return ELandingBlocker::GearUp;
	}
	if (HullGap < 0.f)
	{
		return ELandingBlocker::TooHigh;
	}
	return EvaluateLanding(FMath::Max(HullGap - GearExtensionCm, 0.f), Speed, TiltDeg, SlopeDeg, bEngineInput, Limits);
}

FVector FShipFlightModel::ApplyGroundFriction(const FVector& Velocity, const FVector& SurfaceNormal, const FVector& Up, float GravityCmS2,
	float DeltaSeconds, float Friction)
{
	// Coulomb friction: the tangential velocity loses at most mu x normal load per second. On a
	// slope where mu >= tan(slope) that is more than gravity adds along it, so a resting ship
	// stays at rest; on steeper ground the remainder makes it slide.
	const double NormalLoad = GravityCmS2 * FMath::Max(0.0, SurfaceNormal | Up);
	const FVector Tangential = FVector::VectorPlaneProject(Velocity, SurfaceNormal);
	const double TangentialSpeed = Tangential.Size();
	if (TangentialSpeed < UE_KINDA_SMALL_NUMBER)
	{
		return Velocity;
	}
	const double Remaining = FMath::Max(0.0, TangentialSpeed - Friction * NormalLoad * DeltaSeconds);
	return Velocity - Tangential * (1.0 - Remaining / TangentialSpeed);
}

FRotator FShipFlightModel::LandedRotationStep(const FRotator& Current, const FVector& SurfaceNormal, float DeltaSeconds, float AlignRate)
{
	const FQuat From = Current.Quaternion();
	const double Alpha = 1.0 - FMath::Exp(-AlignRate * DeltaSeconds);
	return FQuat::Slerp(From, LevelOnSurface(From, SurfaceNormal.GetSafeNormal()), Alpha).GetNormalized().Rotator();
}

FQuat FShipFlightModel::LevelOnSurface(const FQuat& Current, const FVector& Normal)
{
	FVector Forward = FVector::VectorPlaneProject(Current.GetForwardVector(), Normal);
	if (Forward.SizeSquared() < 1e-4)
	{
		// Nose pointing straight at the ground or the sky: keep the up vector's heading instead.
		Forward = FVector::VectorPlaneProject(Current.GetUpVector(), Normal);
	}
	return FRotationMatrix::MakeFromXZ(Forward.GetSafeNormal(), Normal).ToQuat();
}

bool FShipFlightModel::TripodRest(const FVector& Location, const FQuat& Current, const FVector (&PadsLocal)[3], const FVector (&Ground)[3],
	double RestHeightCm, FVector& OutLocation, FQuat& OutRotation, FVector& OutNormal)
{
	FVector Normal = FVector::CrossProduct(Ground[1] - Ground[0], Ground[2] - Ground[0]);
	// Pads 3 m apart give a cross product of ~90 000 cm2; under 100 cm2 the points are in a line.
	if (Normal.SizeSquared() < 1e4)
	{
		return false;
	}
	Normal.Normalize();
	if ((Normal | Current.GetUpVector()) < 0.0)
	{
		Normal = -Normal;
	}
	OutNormal = Normal;
	OutRotation = LevelOnSurface(Current, Normal);
	FVector PadsCentre = FVector::ZeroVector;
	for (const FVector& Pad : PadsLocal)
	{
		PadsCentre += OutRotation.RotateVector(Pad) / 3.0;
	}
	const FVector GroundCentre = (Ground[0] + Ground[1] + Ground[2]) / 3.0;
	OutLocation = Location + Normal * (((GroundCentre - (Location + PadsCentre)) | Normal) + RestHeightCm);
	return true;
}

float FShipFlightModel::AngleBetweenDeg(const FVector& A, const FVector& B)
{
	return float(FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(A.GetSafeNormal() | B.GetSafeNormal(), -1.0, 1.0))));
}

TArray<FVector> FShipFlightModel::GearLegPose(float Deploy, bool bNose, const FGearShape& Gear)
{
	// First the leg swings down from under the hull (0 .. 60 % of the travel), then the piston
	// extends to full length (40 .. 100 %): the two overlap, so it reads as one movement.
	auto Ease = [](float X) { X = FMath::Clamp(X, 0.f, 1.f); return X * X * (3.f - 2.f * X); };
	const float Swing = Ease(Deploy / 0.6f);
	const float Extend = Ease((Deploy - 0.4f) / 0.6f);

	// Pitch +90 turns straight down (-Z) into forward (+X): the nose leg folds forward, the main legs back.
	const float Pitch = (bNose ? 1.f : -1.f) * Gear.FoldDeg * (1.f - Swing);

	// Along the leg (pivot frame, Z up, the socket at 0, the pad's sole at -Reach). The sleeve starts
	// inside the hull so no gap shows at the root, wherever the belly is above the socket.
	const double Reach = Gear.ExtensionCm * FMath::Lerp(0.55, 1.0, double(Extend));
	const double Inside = 40.0;
	const double SleeveLength = Inside + 0.45 * Gear.ExtensionCm;
	const double SleeveBottom = Inside - SleeveLength;
	const double PadTop = -Reach + Gear.PadThicknessCm;
	const double PistonTop = SleeveBottom + 10.0;
	const double PistonLength = FMath::Max(PistonTop - PadTop, 1.0);
	const double StrutDiameter = 2.0 * Gear.StrutRadiusCm / 100.0;
	const double PistonDiameter = 0.65 * StrutDiameter;
	const double PadDiameter = 2.0 * Gear.PadRadiusCm / 100.0;

	// The engine cylinder is 100 cm across and 100 cm tall around its centre.
	return {
		FVector(Pitch, 0.0, 0.0),
		FVector(0.0, 0.0, Inside - 0.5 * SleeveLength),
		FVector(StrutDiameter, StrutDiameter, SleeveLength / 100.0),
		FVector(0.0, 0.0, PadTop + 0.5 * PistonLength),
		FVector(PistonDiameter, PistonDiameter, PistonLength / 100.0),
		FVector(0.0, 0.0, -Reach + 0.5 * Gear.PadThicknessCm),
		FVector(PadDiameter, PadDiameter, Gear.PadThicknessCm / 100.0),
	};
}

float FShipFlightModel::GearStowOffsetCm(float Deploy, float StowTravelCm)
{
	const float X = FMath::Clamp(Deploy, 0.f, 1.f);
	return StowTravelCm * (1.f - X * X * (3.f - 2.f * X));
}

FRotator FShipFlightModel::VtolLevelStep(const FQuat& ShipRotation, const FVector& WorldUp, float DeltaSeconds, float VtolBlend, float LevelRate)
{
	if (VtolBlend <= 0.f || LevelRate <= 0.f || WorldUp.IsNearlyZero())
	{
		return FRotator::ZeroRotator;
	}
	// Where the hull's own up points, seen from the hull: level means straight up its Z.
	const FVector LocalUp = ShipRotation.UnrotateVector(WorldUp.GetSafeNormal());
	// Negated: a nose-up hull sees the world's up leaning towards its own nose, and levelling means
	// turning the other way (checked against the measured step in test_vtol_sc2b.py).
	const double PitchError = FMath::RadiansToDegrees(FMath::Atan2(-LocalUp.X, LocalUp.Z));
	const double RollError = FMath::RadiansToDegrees(FMath::Atan2(LocalUp.Y, LocalUp.Z));
	// The whole rate only once VTOL is fully in; half way in, half the authority.
	const double Step = double(LevelRate) * double(VtolBlend) * double(DeltaSeconds);
	return FRotator(FMath::Clamp(PitchError, -Step, Step), 0.0, FMath::Clamp(RollError, -Step, Step));
}

double FShipFlightModel::QuantumArrivalAltitude(double BodyRadiusCm, const FQuantumDrive& Drive)
{
	return FMath::Max(double(Drive.ArrivalRadii) * BodyRadiusCm, double(Drive.MinArrivalKm) * 100000.0);
}

double FShipFlightModel::QuantumSpeedAt(double RemainingCm, double CurrentSpeedCmS, float DeltaSeconds, float SecondsIntoJump, const FQuantumDrive& Drive)
{
	// Braking keeps the full rate (the arrival must be exact); speeding up eases in.
	const double Ramp = Drive.RampSeconds > 0.f ? FMath::Max(0.03, double(FMath::SmoothStep(0.f, Drive.RampSeconds, SecondsIntoJump))) : 1.0;
	const double Accel = double(Drive.AccelerationKmS2) * 100000.0;
	const double Top = double(Drive.MaxSpeedKmS) * 100000.0;
	const double Exit = Drive.ExitSpeed;
	// The speed from which braking at Accel arrives at Exit exactly at the arrival point.
	const double Braking = FMath::Sqrt(Exit * Exit + 2.0 * Accel * FMath::Max(RemainingCm, 0.0));
	const double Rising = FMath::Max(CurrentSpeedCmS, Exit) + Accel * Ramp * DeltaSeconds;
	return FMath::Max(Exit, FMath::Min3(Top, Braking, Rising));
}

float FShipFlightModel::QuantumFuelUse(double DistanceCm, const FQuantumDrive& Drive)
{
	return float(DistanceCm / 1.0e8) * Drive.FuelPer1000Km;
}

bool FShipFlightModel::SegmentHitsSphere(const FVector& Start, const FVector& End, const FVector& Centre, double Radius)
{
	const FVector Segment = End - Start;
	const double LengthSq = Segment.SizeSquared();
	const double T = LengthSq > 0.0 ? FMath::Clamp(FVector::DotProduct(Centre - Start, Segment) / LengthSq, 0.0, 1.0) : 0.0;
	return FVector::DistSquared(Start + Segment * T, Centre) < Radius * Radius;
}
