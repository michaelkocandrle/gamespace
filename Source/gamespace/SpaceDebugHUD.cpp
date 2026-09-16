// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceDebugHUD.h"

#include "CelestialBody.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "PlayerCharacter.h"
#include "QuadSpherePlanet.h"
#include "SpaceOriginRebasingSubsystem.h"
#include "SpaceshipPawn.h"

namespace
{
	/** "TERRAIN" readout: quad-sphere LOD state of the first planet in the level. */
	FString DescribeTerrain(const UWorld* World)
	{
		TActorIterator<AQuadSpherePlanet> It(World);
		if (!It)
		{
			return TEXT("n/a");
		}
		const FQuadSpherePlanetStats& S = It->GetTerrainStats();
		return FString::Printf(TEXT("%d visible / %d built, %d building, depth %d/%d, collision %d (r %.0f m, depth %d, warm-ups %d), LOD %.2f ms"),
			S.VisibleTiles, S.CachedTiles, S.PendingBuilds, S.MaxVisibleDepth, S.MaxDepth, S.CollisionTiles,
			S.CollisionRadiusCm / 100.0, S.CollisionDepth, S.CollisionWarmups, S.SelectionMs);
	}

	/** "ORIGIN" readout: where the world origin is and how far the player is from it. */
	FString DescribeOrigin(const UWorld* World, const APawn& Pawn)
	{
		const USpaceOriginRebasingSubsystem* Rebasing = World->GetSubsystem<USpaceOriginRebasingSubsystem>();
		if (!Rebasing)
		{
			return TEXT("n/a");
		}
		const FVector Origin(Rebasing->GetOriginLocation());
		const double FromOriginKm = Pawn.GetActorLocation().Size() / 100000.0;
		const FString Trigger = Rebasing->IsEnabled()
			? FString::Printf(TEXT("rebase at %.0f km"), Rebasing->GetRebaseDistanceCm() / 100000.0)
			: FString(TEXT("rebasing off"));
		return FString::Printf(TEXT("player %.2f km from origin (%s)   origin %.1f, %.1f, %.1f km"),
			FromOriginKm, *Trigger, Origin.X / 100000.0, Origin.Y / 100000.0, Origin.Z / 100000.0);
	}

	/** "REBASE" readout: how many rebases, how long ago and how long the last one took. */
	FString DescribeRebases(const UWorld* World)
	{
		const USpaceOriginRebasingSubsystem* Rebasing = World->GetSubsystem<USpaceOriginRebasingSubsystem>();
		if (!Rebasing)
		{
			return TEXT("n/a");
		}
		FString Text = Rebasing->GetRebaseCount() == 0
			? FString(TEXT("none yet"))
			: FString::Printf(TEXT("%d x, last %.1f s ago, took %.1f ms, shift %.2f km"),
				Rebasing->GetRebaseCount(), Rebasing->GetSecondsSinceLastRebase(),
				Rebasing->GetLastRebaseMilliseconds(), Rebasing->GetLastShiftCm().Size() / 100000.0);
		if (Rebasing->IsOutOfRebaseRange())
		{
			Text += TEXT("   OUT OF RANGE (> 21474 km)");
		}
		return Text;
	}

	FString FormatDistance(double Centimetres)
	{
		const double Metres = FMath::Max(Centimetres, 0.0) / 100.0;
		return Metres < 1000.0
			? FString::Printf(TEXT("%.0f m"), Metres)
			: FString::Printf(TEXT("%.2f km"), Metres / 1000.0);
	}

	/** "FLIGHT" readout: regime, altitude, air density, gravity and entry heat at the ship. */
	FString DescribeFlight(const ASpaceshipPawn& Ship, FLinearColor& OutColor)
	{
		if (!Ship.HasEnvironment())
		{
			OutColor = FLinearColor(0.6f, 0.6f, 0.6f);
			return TEXT("DEEP SPACE");
		}
		const FCelestialEnvironment& E = Ship.GetEnvironment();
		const TCHAR* Regime = E.Regime == EFlightRegime::Orbit ? TEXT("ORBIT")
			: E.Regime == EFlightRegime::Atmosphere ? TEXT("ATMOSPHERE") : TEXT("SURFACE");
		OutColor = E.Regime == EFlightRegime::Orbit ? FLinearColor(0.6f, 0.8f, 1.f)
			: E.Regime == EFlightRegime::Atmosphere ? FLinearColor(0.5f, 1.f, 1.f) : FLinearColor(1.f, 0.85f, 0.4f);
		FString Text = FString::Printf(TEXT("%s   alt %s AGL / %s ASL   air %3.0f %%   g %.2f m/s2"),
			Regime, *FormatDistance(E.AltitudeAboveTerrainCm), *FormatDistance(E.AltitudeAboveSeaLevelCm),
			E.AtmosphereDensity * 100.f, E.GravityCmS2 / 100.0);
		if (Ship.GetHeat() > 0.02f)
		{
			Text += FString::Printf(TEXT("   HEAT %3.0f %%"), Ship.GetHeat() * 100.f);
			OutColor = FMath::Lerp(OutColor, FLinearColor(1.f, 0.3f, 0.1f), FMath::Min(1.f, Ship.GetHeat() * 2.f));
		}
		return Text;
	}

	/** "LANDING" readout: the touchdown state, or why touchdown is not possible right now. */
	FString DescribeLanding(const ASpaceshipPawn& Ship, FLinearColor& OutColor)
	{
		const ELandingState State = Ship.GetLandingState();
		if (State == ELandingState::Landed)
		{
			OutColor = FLinearColor(0.3f, 1.f, 0.35f);
			return FString::Printf(TEXT("LANDED   slope %.0f deg   (W / Space to take off)"), Ship.GetGroundSlopeDeg());
		}
		if (!Ship.HasGroundInfo())
		{
			OutColor = FLinearColor(0.6f, 0.6f, 0.6f);
			return TEXT("-");
		}

		const FString Gap = Ship.GetGroundGapCm() < 0.f ? FString(TEXT("> 2 m"))
			: FString::Printf(TEXT("%.1f m"), Ship.GetGroundGapCm() / 100.f);
		const FString Measurements = FString::Printf(TEXT("gap %s   slope %.0f deg   tilt %.0f deg"),
			*Gap, Ship.GetGroundSlopeDeg(), Ship.GetGroundTiltDeg());

		if (State == ELandingState::Settling)
		{
			OutColor = FLinearColor(1.f, 0.9f, 0.3f);
			return FString::Printf(TEXT("TOUCHDOWN %3.0f %%   %s"), Ship.GetLandingProgress() * 100.f, *Measurements);
		}

		const TCHAR* Reason = TEXT("");
		switch (Ship.GetLandingBlocker())
		{
		case ELandingBlocker::TooHigh: Reason = TEXT("too high"); break;
		case ELandingBlocker::TooSteep: Reason = TEXT("TOO STEEP"); break;
		case ELandingBlocker::TooFast: Reason = TEXT("too fast"); break;
		case ELandingBlocker::Tilted: Reason = TEXT("level the ship"); break;
		case ELandingBlocker::EngineInput: Reason = TEXT("engines on"); break;
		case ELandingBlocker::TakeoffCooldown: Reason = TEXT("taking off"); break;
		default: break;
		}
		OutColor = Ship.GetLandingBlocker() == ELandingBlocker::TooSteep ? FLinearColor(1.f, 0.45f, 0.2f) : FLinearColor(0.8f, 0.8f, 0.8f);
		return FString::Printf(TEXT("%s   %s"), *Measurements, Reason);
	}

	/** "TARGET" readout for the nearest celestial body: name, surface distance, time to reach it. */
	FString DescribeNearestBody(const UWorld* World, const FVector& ShipLocation, const FVector& Velocity)
	{
		const ACelestialBody* Nearest = nullptr;
		double NearestDistance = TNumericLimits<double>::Max();
		// A handful of bodies at most, so a per-frame walk is cheaper than keeping a registry.
		for (TActorIterator<ACelestialBody> It(World); It; ++It)
		{
			const double Distance = It->GetSurfaceDistance(ShipLocation);
			if (Distance < NearestDistance)
			{
				NearestDistance = Distance;
				Nearest = *It;
			}
		}

		if (!Nearest)
		{
			return TEXT("none");
		}

		// Only the part of the velocity pointing at the body closes the gap.
		const FVector ToBody = (Nearest->GetActorLocation() - ShipLocation).GetSafeNormal();
		const double ClosingSpeed = FVector::DotProduct(Velocity, ToBody);

		FString Eta = TEXT("--:--");
		if (ClosingSpeed > 50.0 && NearestDistance > 0.0)
		{
			const int32 Seconds = FMath::RoundToInt32(NearestDistance / ClosingSpeed);
			Eta = FString::Printf(TEXT("%d:%02d"), Seconds / 60, Seconds % 60);
		}

		return FString::Printf(TEXT("%s   %s   ETA %s"),
			*Nearest->GetDisplayName().ToString(), *FormatDistance(NearestDistance), *Eta);
	}
}

namespace
{
	struct FLine
	{
		const TCHAR* Label;
		FString Value;
		FLinearColor Color;
	};

	const FLinearColor ModeColor(1.f, 1.f, 0.55f);

	void AddShipLines(const UWorld* World, const ASpaceshipPawn& Ship, TArray<FLine>& Lines)
	{
		// Unreal units are centimetres.
		const float SpeedMetres = Ship.GetSpeed() / 100.f;
		FLinearColor FlightColor;
		const FString Flight = DescribeFlight(Ship, FlightColor);
		FLinearColor LandingColor;
		const FString Landing = DescribeLanding(Ship, LandingColor);

		Lines.Add({ TEXT("MODE"), Ship.CanExit() ? TEXT("IN SHIP   [F] get out") : TEXT("IN SHIP"), ModeColor });
		Lines.Add({ TEXT("SPEED"), FString::Printf(TEXT("%6.1f m/s   %5.0f km/h"), SpeedMetres, SpeedMetres * 3.6f), FLinearColor::White });
		Lines.Add({ TEXT("THROTTLE"), FString::Printf(TEXT("%+4.0f %%"), Ship.GetThrottle() * 100.f), FLinearColor::White });
		Lines.Add({ TEXT("BOOST"), Ship.IsBoosting() ? TEXT("ON") : TEXT("off"),
			Ship.IsBoosting() ? FLinearColor(1.f, 0.55f, 0.1f) : FLinearColor(0.6f, 0.6f, 0.6f) });
		Lines.Add({ TEXT("CAMERA"), Ship.IsCockpitView() ? TEXT("Cockpit") : TEXT("Chase"), FLinearColor::White });
		Lines.Add({ TEXT("FLIGHT"), Flight, FlightColor });
		Lines.Add({ TEXT("LANDING"), Landing, LandingColor });
		Lines.Add({ TEXT("TARGET"), DescribeNearestBody(World, Ship.GetActorLocation(), Ship.GetLinearVelocity()), FLinearColor(0.6f, 1.f, 0.7f) });
	}

	void AddCharacterLines(const UWorld* World, const APlayerCharacter& Character, TArray<FLine>& Lines)
	{
		const UCharacterMovementComponent* Movement = Character.GetCharacterMovement();
		const FVector Up = Character.GetGravityUp();
		const FVector Velocity = Movement->Velocity;
		const double Ground = FVector::VectorPlaneProject(Velocity, Up).Size() / 100.0;
		const double Vertical = (Velocity | Up) / 100.0;

		double ShipDistance = 0.0;
		const ASpaceshipPawn* Ship = Character.FindBoardableShip(ShipDistance);
		FString Mode = TEXT("ON FOOT");
		if (Ship)
		{
			Mode += FString::Printf(TEXT("   [F] board ship (%.1f m)"), ShipDistance / 100.0);
		}
		else
		{
			// Where the nearest ship is, landed or not, so it can be found again.
			double Nearest = TNumericLimits<double>::Max();
			bool bLanded = false;
			for (TActorIterator<ASpaceshipPawn> It(World); It; ++It)
			{
				const double Distance = It->GetDistanceToHull(Character.GetActorLocation());
				if (Distance < Nearest)
				{
					Nearest = Distance;
					bLanded = It->IsLanded();
				}
			}
			if (Nearest < TNumericLimits<double>::Max())
			{
				Mode += FString::Printf(TEXT("   ship %.0f m away%s"), Nearest / 100.0, bLanded ? TEXT("") : TEXT(" (not landed)"));
			}
		}
		Lines.Add({ TEXT("MODE"), Mode, ModeColor });

		const TCHAR* State = Movement->IsFalling() ? TEXT("falling") : Movement->IsMovingOnGround() ? TEXT("on ground") : TEXT("other");
		Lines.Add({ TEXT("MOVE"), FString::Printf(TEXT("%s   %4.1f m/s ground, %+5.1f m/s vertical   %s"),
			State, Ground, Vertical, Character.IsSprinting() ? TEXT("SPRINT") : TEXT("walk")), FLinearColor::White });

		if (Character.HasEnvironment())
		{
			const FCelestialEnvironment& E = Character.GetEnvironment();
			Lines.Add({ TEXT("GRAVITY"), FString::Printf(TEXT("%.2f m/s2 (scale %.2f)   up %.2f, %.2f, %.2f   alt %s AGL"),
				E.GravityCmS2 / 100.0, Movement->GravityScale, Up.X, Up.Y, Up.Z, *FormatDistance(E.AltitudeAboveTerrainCm)), FLinearColor(0.5f, 1.f, 1.f) });
		}
		else
		{
			Lines.Add({ TEXT("GRAVITY"), TEXT("no body nearby: world default"), FLinearColor(0.6f, 0.6f, 0.6f) });
		}

		const FFootIKState IK = Character.GetFootIKState();
		Lines.Add({ TEXT("FOOT IK"), IK.bActive
			? FString::Printf(TEXT("pelvis %+5.1f cm   left %+5.1f   right %+5.1f%s"), IK.PelvisOffsetCm, IK.LeftFootOffsetCm, IK.RightFootOffsetCm,
				IK.bClamped ? TEXT("   CLAMPED") : TEXT(""))
			: FString(TEXT("off (not standing on planet terrain)")),
			IK.bClamped ? FLinearColor(1.f, 0.6f, 0.2f) : FLinearColor(0.8f, 0.8f, 0.8f) });
		Lines.Add({ TEXT("TARGET"), DescribeNearestBody(World, Character.GetActorLocation(), Velocity), FLinearColor(0.6f, 1.f, 0.7f) });
	}
}

void ASpaceDebugHUD::DrawHUD()
{
	Super::DrawHUD();

	const APawn* Pawn = GetOwningPawn();
	if (!Pawn || !Canvas || !GEngine)
	{
		return;
	}

	TArray<FLine> Lines;
	if (const ASpaceshipPawn* Ship = Cast<ASpaceshipPawn>(Pawn))
	{
		AddShipLines(GetWorld(), *Ship, Lines);
	}
	else if (const APlayerCharacter* Character = Cast<APlayerCharacter>(Pawn))
	{
		AddCharacterLines(GetWorld(), *Character, Lines);
	}
	else
	{
		Lines.Add({ TEXT("MODE"), Pawn->GetClass()->GetName(), ModeColor });
	}
	Lines.Add({ TEXT("ORIGIN"), DescribeOrigin(GetWorld(), *Pawn), FLinearColor(0.85f, 0.85f, 0.6f) });
	Lines.Add({ TEXT("REBASE"), DescribeRebases(GetWorld()), FLinearColor(0.85f, 0.85f, 0.6f) });
	Lines.Add({ TEXT("TERRAIN"), DescribeTerrain(GetWorld()), FLinearColor(0.85f, 0.7f, 0.5f) });

	UFont* Font = GEngine->GetMediumFont();

	const float LineHeight = Font->GetMaxCharHeight() * TextScale * 1.25f;
	const float ValueColumn = 130.f * TextScale;
	const float Padding = 10.f;

	// Size the backing to the longest value so the target line never spills out of it.
	float WidestValue = 0.f;
	for (const FLine& Line : Lines)
	{
		float Width = 0.f;
		float Height = 0.f;
		GetTextSize(Line.Value, Width, Height, Font, TextScale);
		WidestValue = FMath::Max(WidestValue, Width);
	}

	// Dark backing so the numbers stay readable against a bright sky or a lit asteroid.
	DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.55f), Origin.X - Padding, Origin.Y - Padding,
		ValueColumn + WidestValue + Padding * 2.f, LineHeight * Lines.Num() + Padding * 2.f);

	float Y = Origin.Y;
	for (const FLine& Line : Lines)
	{
		DrawText(Line.Label, FLinearColor(0.55f, 0.8f, 1.f), Origin.X, Y, Font, TextScale);
		DrawText(Line.Value, Line.Color, Origin.X + ValueColumn, Y, Font, TextScale);
		Y += LineHeight;
	}
}
