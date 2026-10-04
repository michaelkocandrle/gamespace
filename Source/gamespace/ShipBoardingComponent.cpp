// Copyright Epic Games, Inc. All Rights Reserved.

#include "ShipBoardingComponent.h"

#include "Algo/Find.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "PhysicsEngine/BodySetup.h"
#include "PlayerCharacter.h"
#include "SpaceInterior.h"
#include "SpaceshipLog.h"
#include "SpaceshipPawn.h"

namespace ShipWalk
{
	const FName SeatSocket(TEXT("WalkSeat"));
	const FName RampSocket(TEXT("WalkRamp"));
	const FName PilotEyeSocket(TEXT("Cockpit"));
	constexpr double SeatReachCm = 170.0;      // from the pilot's eye socket to the walker's middle
	constexpr double RampReachCm = 220.0;
	constexpr double HoldStillCmS = 100.0;
}

UShipBoardingComponent::UShipBoardingComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

bool UShipBoardingComponent::CanExit() const
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	return Ship->IsLanded() && Ship->IsPlayerControlled() && Ship->PilotCharacterClass != nullptr;
}

double UShipBoardingComponent::GetDistanceToHull(const FVector& Location) const
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	const FVector Local = Ship->HullCollision->GetComponentTransform().InverseTransformPositionNoScale(Location);
	const FVector Extent = Ship->HullCollision->GetScaledBoxExtent();
	const FVector Outside(
		FMath::Max(FMath::Abs(Local.X) - Extent.X, 0.0),
		FMath::Max(FMath::Abs(Local.Y) - Extent.Y, 0.0),
		FMath::Max(FMath::Abs(Local.Z) - Extent.Z, 0.0));
	return Outside.Size();
}

FVector UShipBoardingComponent::ComputeSideExitLocation(const FVector& ShipLocation, const FRotator& ShipRotation, const FVector& HullExtent, float CapsuleRadius, float ClearanceCm)
{
	const FQuat Rotation = ShipRotation.Quaternion();
	return ShipLocation + Rotation.GetRightVector() * (HullExtent.Y + CapsuleRadius + ClearanceCm);
}

TArray<FBox> UShipBoardingComponent::GetHullCollisionBoxes() const
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	// Actor space, unscaled: the hull's collision shapes (UCX hulls and boxes from Blender) through
	// the hull's relative transform; the mesh bounds when it has none; the root box without a mesh.
	TArray<FBox> Boxes;
	const FTransform HullToActor = Ship->Hull->GetRelativeTransform();
	if (const UStaticMesh* Mesh = Ship->Hull->GetStaticMesh())
	{
		if (const UBodySetup* Body = Mesh->GetBodySetup())
		{
			for (const FKConvexElem& Convex : Body->AggGeom.ConvexElems)
			{
				Boxes.Add(Convex.ElemBox.TransformBy(Convex.GetTransform() * HullToActor));
			}
			for (const FKBoxElem& Box : Body->AggGeom.BoxElems)
			{
				const FVector Half(Box.X * 0.5, Box.Y * 0.5, Box.Z * 0.5);
				Boxes.Add(FBox(-Half, Half).TransformBy(Box.GetTransform() * HullToActor));
			}
		}
		if (Boxes.Num() == 0)
		{
			Boxes.Add(Mesh->GetBoundingBox().TransformBy(HullToActor));
		}
	}
	if (Boxes.Num() == 0)
	{
		const FVector Extent = Ship->HullCollision->GetUnscaledBoxExtent();
		Boxes.Add(FBox(-Extent, Extent));
	}
	return Boxes;
}

double UShipBoardingComponent::GetHullClearance(const FVector& Location, float CapsuleRadius, float CapsuleHalfHeight) const
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	// A pilot standing where the landed ship stands: capsule bottom at the lowest point of the hull
	// shapes (the gear), whatever height Location has. Only shapes within that height count, then
	// the gap in the ship's floor plane. Pure geometry, so it also works where collision queries do
	// not (commandlets) and does not depend on the physics scene being up to date.
	const TArray<FBox> Boxes = GetHullCollisionBoxes();
	double Floor = TNumericLimits<double>::Max();
	for (const FBox& Box : Boxes)
	{
		Floor = FMath::Min(Floor, Box.Min.Z);
	}
	const double Top = Floor + 2.0 * CapsuleHalfHeight;
	const FVector Local = Ship->GetActorTransform().InverseTransformPositionNoScale(Location);
	double Clearance = TNumericLimits<double>::Max();
	for (const FBox& Box : Boxes)
	{
		if (Box.Min.Z >= Top || Box.Max.Z <= Floor)
		{
			continue;  // above the pilot's head (or below the feet)
		}
		const double DX = FMath::Max3(Box.Min.X - Local.X, 0.0, Local.X - Box.Max.X);
		const double DY = FMath::Max3(Box.Min.Y - Local.Y, 0.0, Local.Y - Box.Max.Y);
		Clearance = FMath::Min(Clearance, FMath::Sqrt(DX * DX + DY * DY) - CapsuleRadius);
	}
	return Clearance;
}

FVector UShipBoardingComponent::PushClearOfHull(const FVector& Start, const FVector& Direction, float CapsuleRadius, float CapsuleHalfHeight) const
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	const FVector Step = FVector::VectorPlaneProject(Direction, Ship->GetActorUpVector()).GetSafeNormal() * 20.0;
	if (Step.IsNearlyZero())
	{
		return Start;
	}
	FVector Location = Start;
	// Out in 20 cm steps until the capsule clears every hull shape by ExitClearanceCm (40 m at most).
	for (int32 Index = 0; Index < 200 && GetHullClearance(Location, CapsuleRadius, CapsuleHalfHeight) < Ship->ExitClearanceCm; ++Index)
	{
		Location += Step;
	}
	return Location;
}

TArray<FVector> UShipBoardingComponent::GetExitCandidates() const
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	TArray<FVector> Candidates;
	const ACharacter* PilotDefaults = Cast<ACharacter>(Ship->PilotCharacterClass ? Ship->PilotCharacterClass->GetDefaultObject() : nullptr);
	const float CapsuleRadius = PilotDefaults ? PilotDefaults->GetSimpleCollisionRadius() : 42.f;
	const float CapsuleHalfHeight = PilotDefaults ? PilotDefaults->GetSimpleCollisionHalfHeight() : 96.f;

	// The Exit socket says which side and where along the hull; the pilot is then moved sideways
	// until clear of the hull. The first fighter's socket sat 44 cm off the belly, under the edge of the
	// fuselage, which put the pilot practically inside the ship.
	static const FName ExitSockets[] = { FName(TEXT("Exit")), FName(TEXT("SOCKET_Exit")) };
	if (const FName* Socket = Algo::FindByPredicate(ExitSockets, [Ship](const FName& Name) { return Ship->Hull->DoesSocketExist(Name); }))
	{
		const FVector SocketLocation = Ship->Hull->GetSocketLocation(*Socket);
		const double Side = Ship->GetActorTransform().InverseTransformPositionNoScale(SocketLocation).Y;
		const FVector Outward = Ship->GetActorRightVector() * (Side < 0.0 ? -1.0 : 1.0);
		Candidates.Add(PushClearOfHull(SocketLocation, Outward, CapsuleRadius, CapsuleHalfHeight));
	}

	// Then around the hull: its mesh bounds where there is a mesh (wings included), else the box.
	FVector Center = Ship->GetActorLocation();
	FVector Extent = Ship->HullCollision->GetScaledBoxExtent();
	if (const UStaticMesh* Mesh = Ship->Hull->GetStaticMesh())
	{
		const FBox LocalBox = Mesh->GetBoundingBox().TransformBy(Ship->Hull->GetRelativeTransform());
		Center = Ship->GetActorTransform().TransformPosition(LocalBox.GetCenter());
		Extent = LocalBox.GetExtent();
	}
	const FQuat Rotation = Ship->GetActorQuat();
	const TPair<FVector, double> Directions[] = {
		{ Rotation.GetRightVector(), Extent.Y },
		{ -Rotation.GetRightVector(), Extent.Y },
		{ -Rotation.GetForwardVector(), Extent.X },
		{ Rotation.GetForwardVector(), Extent.X },
	};
	for (const double Extra : { 0.0, 300.0, 800.0 })
	{
		for (const TPair<FVector, double>& Direction : Directions)
		{
			Candidates.Add(PushClearOfHull(Center + Direction.Key * (Direction.Value + CapsuleRadius + Ship->ExitClearanceCm + Extra),
				Direction.Key, CapsuleRadius, CapsuleHalfHeight));
		}
	}
	return Candidates;
}

bool UShipBoardingComponent::IsExitSpotFree(const FVector& Location, const FVector& Up, float CapsuleRadius, float CapsuleHalfHeight) const
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	const UWorld* World = Ship->GetWorld();
	if (!World)
	{
		return true;
	}
	// A slightly smaller capsule lifted off the ground: uneven terrain under the feet must not
	// count as blocked, a wall, rock or the hull must. The ship itself is deliberately not
	// ignored; its hull mesh collision is exactly what the pilot must not appear inside.
	const double Lift = 30.0;
	const FCollisionShape Shape = FCollisionShape::MakeCapsule(FMath::Max(CapsuleRadius - 4.f, 10.f), FMath::Max(CapsuleHalfHeight - 10.f, 20.f));
	FCollisionQueryParams Params(SCENE_QUERY_STAT(SpaceshipExitSpot), false);
	return !World->OverlapBlockingTestByChannel(Location + Up * Lift, FQuat::FindBetweenNormals(FVector::UpVector, Up),
		ECC_Pawn, Shape, Params);
}

FTransform UShipBoardingComponent::ComputeExitTransform() const
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	const FVector Up = Ship->bHasEnvironment ? Ship->Environment.Up : Ship->GetActorUpVector();
	const ACharacter* PilotDefaults = Cast<ACharacter>(Ship->PilotCharacterClass ? Ship->PilotCharacterClass->GetDefaultObject() : nullptr);
	const float CapsuleRadius = PilotDefaults ? PilotDefaults->GetSimpleCollisionRadius() : 42.f;
	const float CapsuleHalfHeight = PilotDefaults ? PilotDefaults->GetSimpleCollisionHalfHeight() : 96.f;

	// Facing the ship: the character's camera then sits on the far side, away from the hull, and
	// shows the ship. Facing along the ship's heading put the camera boom into a wing, which
	// pulled the camera in for a moment after getting out.
	auto FacingFrom = [Ship, &Up](const FVector& Location)
	{
		FVector Flat = FVector::VectorPlaneProject(Ship->GetActorLocation() - Location, Up).GetSafeNormal();
		if (Flat.IsNearlyZero())
		{
			Flat = FVector::VectorPlaneProject(Ship->GetActorForwardVector(), Up).GetSafeNormal();
		}
		if (Flat.IsNearlyZero())
		{
			Flat = FVector::VectorPlaneProject(Ship->GetActorUpVector(), Up).GetSafeNormal();
		}
		return FRotationMatrix::MakeFromXZ(Flat, Up).ToQuat();
	};

	auto OnGround = [&](FVector Location)
	{
		// Stand on the terrain there, not at the height of the ship's centre or a hatch in the air.
		FVector SurfacePoint;
		FVector SurfaceNormal;
		if (const ACelestialBody* Body = Ship->NearestBody.Get())
		{
			if (Body->GetSurfaceFrame(Location, CapsuleRadius, SurfacePoint, SurfaceNormal))
			{
				const double AboveGround = (Location - SurfacePoint) | Up;
				Location += Up * (CapsuleHalfHeight + 20.0 - AboveGround);
			}
		}
		return Location;
	};

	const TArray<FVector> Candidates = GetExitCandidates();
	for (const FVector& Candidate : Candidates)
	{
		const FVector Location = OnGround(Candidate);
		if (IsExitSpotFree(Location, Up, CapsuleRadius, CapsuleHalfHeight))
		{
			return FTransform(FacingFrom(Location), Location);
		}
	}
	// Nowhere free (boxed in): the farthest spot beside the ship, where at least the hull is not.
	const FVector Fallback = Candidates.Num() > 0 ? Candidates.Last(3) : Ship->GetActorLocation() + Ship->GetActorRightVector() * 1000.0;
	UE_LOG(LogSpaceship, Warning, TEXT("%s: no free exit spot among %d candidates; using %s"), *Ship->GetName(), Candidates.Num(), *Fallback.ToString());
	const FVector FallbackLocation = OnGround(Fallback);
	return FTransform(FacingFrom(FallbackLocation), FallbackLocation);
}

APawn* UShipBoardingComponent::ExitShip()
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	APlayerController* PlayerController = Cast<APlayerController>(Ship->GetController());
	if (!CanExit() || !PlayerController)
	{
		return nullptr;
	}

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
	const FTransform ExitTransform = ComputeExitTransform();
	APawn* Pilot = Ship->GetWorld()->SpawnActor<APawn>(Ship->PilotCharacterClass, ExitTransform, Params);
	if (!Pilot)
	{
		UE_LOG(LogSpaceship, Warning, TEXT("%s: could not spawn %s at the exit"), *Ship->GetName(), *GetNameSafe(Ship->PilotCharacterClass));
		return nullptr;
	}
	PlayerController->Possess(Pilot);
	if (APlayerCharacter* Character = Cast<APlayerCharacter>(Pilot))
	{
		Character->FaceDirection(ExitTransform.GetRotation().GetForwardVector());
	}
	UE_LOG(LogSpaceship, Log, TEXT("%s: pilot out at %s"), *Ship->GetName(), *ExitTransform.GetLocation().ToString());
	return Pilot;
}

void UShipBoardingComponent::OnBoarded()
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->ClearPilotInput();
	Ship->SnapCameraToShip();
}

bool UShipBoardingComponent::HasWalkInterior() const
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	return Ship->Hull && Ship->Hull->DoesSocketExist(ShipWalk::SeatSocket) && Ship->Hull->DoesSocketExist(ShipWalk::RampSocket);
}

bool UShipBoardingComponent::CanLeaveSeat() const
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	return HasWalkInterior() && Ship->IsPlayerControlled() && Ship->PilotCharacterClass != nullptr
		&& (Ship->IsLanded() || Ship->GetLinearVelocity().Size() < ShipWalk::HoldStillCmS);
}

FTransform UShipBoardingComponent::GetWalkSocketTransform(FName Socket) const
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	if (Ship->Hull && Ship->Hull->DoesSocketExist(Socket))
	{
		const FTransform T = Ship->Hull->GetSocketTransform(Socket, RTS_World);
		return FTransform(T.GetRotation(), T.GetLocation());
	}
	return FTransform(Ship->GetActorRotation(), Ship->GetActorLocation());
}

bool UShipBoardingComponent::IsNearSeat(const FVector& Location) const
{
	return HasWalkInterior() && FVector::Dist(GetWalkSocketTransform(ShipWalk::PilotEyeSocket).GetLocation(), Location) < ShipWalk::SeatReachCm;
}

bool UShipBoardingComponent::IsNearRamp(const FVector& Location) const
{
	return HasWalkInterior() && FVector::Dist(GetWalkSocketTransform(ShipWalk::RampSocket).GetLocation(), Location) < ShipWalk::RampReachCm;
}

void UShipBoardingComponent::SetInteriorWalk(bool bWalking)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	if (bWalking == bInteriorWalked)
	{
		return;
	}
	bInteriorWalked = bWalking;
	// the hull's own collision is a convex shell round the fuselage: a pilot inside it would be pushed out
	if (Ship->Hull)
	{
		Ship->Hull->SetCollisionResponseToChannel(ECC_Pawn, bWalking ? ECR_Ignore : ECR_Block);
	}
	// the rooms: the procedural interior and its kit pieces per polygon, the kit rooms' parts by their boxes
	TArray<UStaticMeshComponent*> Meshes;
	Ship->GetComponents<UStaticMeshComponent>(Meshes);
	FBox Rooms(ForceInit);
	for (UStaticMeshComponent* Mesh : Meshes)
	{
		const FString Name = Mesh->GetName();
		const bool bRoom = Name == TEXT("Interior") || Name == TEXT("InteriorKit") || Name.StartsWith(TEXT("InteriorMod_"));
		if (!bRoom || !Mesh->GetStaticMesh())
		{
			continue;
		}
		if (bWalking)
		{
			Mesh->SetCollisionObjectType(ECC_WorldStatic);
			Mesh->SetCollisionResponseToAllChannels(ECR_Ignore);
			Mesh->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
			Mesh->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
			Mesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
		}
		else
		{
			Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		}
		const FTransform ToActor = Mesh->GetComponentTransform().GetRelativeTransform(Ship->GetActorTransform());
		Rooms += Mesh->GetStaticMesh()->GetBoundingBox().TransformBy(ToActor);
	}
	// gravity along the ship's floor, riding with it (landed or holding still in space)
	if (bWalking && !WalkGravity && Rooms.IsValid && Ship->GetWorld())
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		Params.Owner = Ship;
		const FVector Centre = Ship->GetActorTransform().TransformPosition(Rooms.GetCenter());
		WalkGravity = Ship->GetWorld()->SpawnActor<ASpaceGravityVolume>(ASpaceGravityVolume::StaticClass(), Centre, Ship->GetActorRotation(), Params);
		if (WalkGravity)
		{
			WalkGravity->Volume->SetBoxExtent(Rooms.GetExtent() + FVector(50.0));
			WalkGravity->AttachToActor(Ship, FAttachmentTransformRules::KeepWorldTransform);
		}
	}
	else if (!bWalking && WalkGravity)
	{
		WalkGravity->Destroy();
		WalkGravity = nullptr;
	}
	UE_LOG(LogSpaceship, Log, TEXT("%s: interior %s"), *Ship->GetName(), bWalking ? TEXT("walked (per-polygon collision, gravity)") : TEXT("closed"));
}

APawn* UShipBoardingComponent::LeaveSeat()
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	APlayerController* PlayerController = Cast<APlayerController>(Ship->GetController());
	if (!CanLeaveSeat() || !PlayerController)
	{
		return nullptr;
	}
	SetInteriorWalk(true);
	const FTransform Seat = GetWalkSocketTransform(ShipWalk::SeatSocket);
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
	const FTransform Start(Seat.GetRotation(), Seat.GetLocation() + Ship->GetActorUpVector() * 100.0);
	APawn* Pilot = Ship->GetWorld()->SpawnActor<APawn>(Ship->PilotCharacterClass, Start, Params);
	if (!Pilot)
	{
		SetInteriorWalk(false);
		return nullptr;
	}
	Ship->ClearPilotInput();
	PlayerController->Possess(Pilot);
	if (APlayerCharacter* Character = Cast<APlayerCharacter>(Pilot))
	{
		Character->BoardInterior(Ship, Seat.GetRotation().GetForwardVector());
		// getting up: the view rises from the seat to the standing eye instead of cutting (author 5. 10. 2026)
		PlayerController->SetViewTarget(Ship);
		PlayerController->SetViewTargetWithBlend(Character, Character->GetSeatBlendSeconds(), VTBlend_EaseInOut, 2.0f);
	}
	UE_LOG(LogSpaceship, Log, TEXT("%s: pilot up from the seat at %s"), *Ship->GetName(), *Start.GetLocation().ToString());
	return Pilot;
}
