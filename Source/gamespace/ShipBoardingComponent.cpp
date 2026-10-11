// Copyright Epic Games, Inc. All Rights Reserved.

#include "ShipBoardingComponent.h"

#include "HAL/PlatformTime.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundAttenuation.h"
#include "Sound/SoundBase.h"
#include "SpaceUserSettings.h"
#include "Components/WidgetComponent.h"
#include "Misc/App.h"
#include "SpaceDoorPanel.h"

#include "Algo/Find.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "PhysicsEngine/BodySetup.h"
#include "PlayerCharacter.h"
#include "Camera/PlayerCameraManager.h"
#include "SpacePlayerController.h"
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

namespace ShipDoors
{
	constexpr float DoorSeconds = 0.9f;
	constexpr double AutoCloseSeconds = 6.0;
	constexpr double KeepOpenNearCm = 140.0;
}

void UShipBoardingComponent::FindDoors()
{
	bDoorsFound = true;
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	TArray<UStaticMeshComponent*> Meshes;
	Ship->GetComponents<UStaticMeshComponent>(Meshes);
	for (UStaticMeshComponent* Mesh : Meshes)
	{
		const FString Name = Mesh->GetName();
		if (!Name.StartsWith(TEXT("Door")) || !Mesh->GetStaticMesh() || Name.Len() < 6)
		{
			continue;
		}
		const FString Tail = Name.Mid(4);                               // "<n><A|B>"
		const TCHAR Letter = FChar::ToLower(Tail[Tail.Len() - 1]);
		const int32 Door = FCString::Atoi(*Tail.LeftChop(1));
		FVector Closed;
		if (!Ship->GetHullSocketLocation(FName(*FString::Printf(TEXT("Control_door%d_%c"), Door, Letter)), Closed))
		{
			continue;
		}
		FDoorLeaf Leaf;
		Leaf.Mesh = Mesh;
		Leaf.Door = Door;
		Leaf.OpenRel = Mesh->GetRelativeLocation();
		// the leaf is imported open: closing moves its centre onto the socket (in the parent's space)
		const FVector Delta = Closed - Mesh->Bounds.Origin;
		const USceneComponent* Parent = Mesh->GetAttachParent();
		Leaf.ClosedRel = Leaf.OpenRel + (Parent ? Parent->GetComponentTransform().InverseTransformVectorNoScale(Delta) : Delta);
		DoorLeaves.Add(Leaf);
		if (DoorOpen.Num() <= Door)
		{
			DoorOpen.SetNumZeroed(Door + 1);
			DoorTarget.SetNumZeroed(Door + 1);
			DoorOpenedAt.SetNumZeroed(Door + 1);
			DoorPrompt.SetNumZeroed(Door + 1);
		}
		// one leaf: SC puts OPEN [F] by the edge that closes, 12 cm in from it
		const FVector Slide = (Mesh->Bounds.Origin - Closed).GetSafeNormal();
		const double Half = FMath::Abs(FVector::DotProduct(Mesh->Bounds.BoxExtent, Slide.GetAbs()));
		const FVector Edge = Closed - Slide * FMath::Max(Half - 12.0, 0.0);
		DoorPrompt[Door] = DoorPrompt[Door].IsZero() && Letter == TEXT('a') ? Ship->GetActorTransform().InverseTransformPosition(Edge) : FVector::ZeroVector;
	}
	for (const FDoorLeaf& Leaf : DoorLeaves)
	{
		Leaf.Mesh->SetRelativeLocation(Leaf.ClosedRel);                  // the game starts with the doors shut
	}
	ApplyDoorCollision();
	// the holographic touch panels beside the doorways (a world-space widget each, facing forward like the leaf)
	DoorPanels.SetNum(DoorOpen.Num());
	for (int32 Door = 0; Door < DoorOpen.Num(); ++Door)
	{
		FVector At;
		if (!FApp::CanEverRender() || !Ship->GetHullSocketLocation(FName(*FString::Printf(TEXT("Control_door%d_panel"), Door)), At))
		{
			continue;
		}
		UWidgetComponent* Panel = NewObject<UWidgetComponent>(Ship, FName(*FString::Printf(TEXT("DoorPanel%d"), Door)));
		Panel->SetupAttachment(Ship->GetRootComponent());
		Panel->SetWidgetSpace(EWidgetSpace::World);
		Panel->SetWidgetClass(USpaceDoorPanel::StaticClass());
		Panel->SetDrawSize(FVector2D(240.0, 330.0));
		Panel->SetPivot(FVector2D(0.5, 0.5));
		Panel->SetBlendMode(EWidgetBlendMode::Transparent);
		Panel->SetTwoSided(false);
		Panel->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Panel->SetCastShadow(false);
		Panel->RegisterComponent();
		// 11 cm further out than the socket: the kit's wall face stands proud of the bulkhead plane (at the socket the
		// hologram was inside the wall)
		// toward the doorway by 6 cm and 12 cm up: over the junction box, under the room's sign (critic 5. 10.)
		FVector Toward = FVector::VectorPlaneProject(GetDoorLocation(Door) - At, Ship->GetActorUpVector());
		Toward = FVector::VectorPlaneProject(Toward, Ship->GetActorForwardVector()).GetSafeNormal();
		Panel->SetWorldLocation(At + Ship->GetActorForwardVector() * 11.0 + Ship->GetActorUpVector() * 12.0 + Toward * 6.0);
		Panel->SetWorldRotation(Ship->GetActorRotation());              // facing the ship's forward, like the leaf's face
		Panel->SetWorldScale3D(FVector(1.0, 0.065, 0.065));              // 240 x 330 px = 15.6 x 21.5 cm
		DoorPanels[Door] = Panel;
	}
	UpdateDoorPanels();
}

void UShipBoardingComponent::UpdateDoorPanels()
{
	for (int32 Door = 0; Door < DoorPanels.Num(); ++Door)
	{
		if (UWidgetComponent* Panel = DoorPanels[Door])
		{
			if (USpaceDoorPanel* Widget = Cast<USpaceDoorPanel>(Panel->GetUserWidgetObject()))
			{
				Widget->DoorNumber = Door;
				Widget->Open = DoorOpen.IsValidIndex(Door) ? DoorOpen[Door] : 0.f;
				Widget->bOpening = DoorTarget.IsValidIndex(Door) && DoorTarget[Door] > 0.5f;
			}
		}
	}
}

bool UShipBoardingComponent::GetDoorPanelLocation(int32 Door, FVector& OutLocation) const
{
	if (!DoorPanels.IsValidIndex(Door) || !DoorPanels[Door])
	{
		return CastChecked<ASpaceshipPawn>(GetOwner())->GetHullSocketLocation(FName(*FString::Printf(TEXT("Control_door%d_panel"), Door)), OutLocation);
	}
	OutLocation = DoorPanels[Door]->GetComponentLocation();
	return true;
}

void UShipBoardingComponent::SetDoorPanelHovered(int32 Door, bool bHovered)
{
	if (DoorPanels.IsValidIndex(Door) && DoorPanels[Door])
	{
		if (USpaceDoorPanel* Widget = Cast<USpaceDoorPanel>(DoorPanels[Door]->GetUserWidgetObject()))
		{
			Widget->bHovered = bHovered;
		}
	}
}

int32 UShipBoardingComponent::FindDoorNear(const FVector& Location, float ReachCm, const FVector& Facing) const
{
	int32 Best = INDEX_NONE;
	double BestDistance = ReachCm;
	const FVector Up = GetOwner()->GetActorUpVector();
	const FVector Ahead = FVector::VectorPlaneProject(Facing, Up).GetSafeNormal();
	for (int32 Door = 0; Door < DoorOpen.Num(); ++Door)
	{
		const FVector ToDoor = FVector::VectorPlaneProject(GetDoorLocation(Door) - Location, Up);
		// with a view: only the doors in front of the walker (not the one just passed behind him)
		if (!Ahead.IsZero() && ToDoor.SizeSquared() > FMath::Square(30.0) && FVector::DotProduct(ToDoor.GetSafeNormal(), Ahead) < 0.35)
		{
			continue;
		}
		const double Distance = FVector::Dist(GetDoorLocation(Door), Location);
		if (Distance < BestDistance)
		{
			BestDistance = Distance;
			Best = Door;
		}
	}
	return Best;
}

FVector UShipBoardingComponent::GetDoorLocation(int32 Door) const
{
	FVector At = FVector::ZeroVector;
	CastChecked<ASpaceshipPawn>(GetOwner())->GetHullSocketLocation(FName(*FString::Printf(TEXT("Control_door%d"), Door)), At);
	return At;
}

FVector UShipBoardingComponent::GetDoorPromptLocation(int32 Door) const
{
	FVector At = GetDoorLocation(Door);
	if (DoorPrompt.IsValidIndex(Door) && !DoorPrompt[Door].IsZero())
	{
		// at the leaf's edge, the height of the doorway's socket
		const FTransform ShipT = GetOwner()->GetActorTransform();
		FVector Local = DoorPrompt[Door];
		Local.Z = ShipT.InverseTransformPosition(At).Z;
		At = ShipT.TransformPosition(Local);
	}
	return At;
}

void UShipBoardingComponent::SetDoorOpen(int32 Door, bool bOpen)
{
	if (!DoorTarget.IsValidIndex(Door))
	{
		return;
	}
	DoorTarget[Door] = bOpen ? 1.f : 0.f;
	if (bOpen)
	{
		DoorOpenedAt[Door] = FPlatformTime::Seconds();
	}
}

void UShipBoardingComponent::TickDoors(float DeltaSeconds)
{
	if (!bDoorsFound)
	{
		FindDoors();
	}
	if (DoorLeaves.IsEmpty())
	{
		return;
	}
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	const APawn* Walker = Ship->GetWorld() && Ship->GetWorld()->GetFirstPlayerController() ? Ship->GetWorld()->GetFirstPlayerController()->GetPawn() : nullptr;
	const double Now = FPlatformTime::Seconds();
	bool bMoved = false;
	for (int32 Door = 0; Door < DoorOpen.Num(); ++Door)
	{
		// SC's doors shut again by themselves once nobody stands in them
		if (DoorTarget[Door] > 0.5f && Now - DoorOpenedAt[Door] > ShipDoors::AutoCloseSeconds
			&& !(Walker && Walker != Ship && FVector::Dist(Walker->GetActorLocation(), GetDoorLocation(Door)) < ShipDoors::KeepOpenNearCm))
		{
			DoorTarget[Door] = 0.f;
		}
		if (!DoorSoundTarget.IsValidIndex(Door))
		{
			DoorSoundTarget.SetNum(DoorOpen.Num());
			for (int32 Each = 0; Each < DoorOpen.Num(); ++Each)
			{
				DoorSoundTarget[Each] = DoorTarget[Each];
			}
		}
		if (DoorSoundTarget[Door] != DoorTarget[Door])
		{
			DoorSoundTarget[Door] = DoorTarget[Door];
			PlayDoorSound(Door, DoorTarget[Door] > 0.5f);
		}
		const float Before = DoorOpen[Door];
		DoorOpen[Door] = FMath::FInterpConstantTo(DoorOpen[Door], DoorTarget[Door], DeltaSeconds, 1.f / ShipDoors::DoorSeconds);
		bMoved |= DoorOpen[Door] != Before;
	}
	UpdateDoorPanels();
	if (!bMoved)
	{
		return;
	}
	for (const FDoorLeaf& Leaf : DoorLeaves)
	{
		if (UStaticMeshComponent* Mesh = Leaf.Mesh.Get())
		{
			// a heavy leaf: slow start, quick middle, soft stop
			const float A = FMath::SmoothStep(0.f, 1.f, DoorOpen[Leaf.Door]);
			Mesh->SetRelativeLocation(FMath::Lerp(Leaf.ClosedRel, Leaf.OpenRel, A));
		}
	}
	ApplyDoorCollision();
}

void UShipBoardingComponent::PlayDoorSound(int32 Door, bool bOpen)
{
	if (!DoorOpenSound)
	{
		DoorOpenSound = LoadObject<USoundBase>(nullptr, TEXT("/Game/Ships/Audio/SW_DoorOpen.SW_DoorOpen"), nullptr, LOAD_NoWarn | LOAD_Quiet);
		DoorCloseSound = LoadObject<USoundBase>(nullptr, TEXT("/Game/Ships/Audio/SW_DoorClose.SW_DoorClose"), nullptr, LOAD_NoWarn | LOAD_Quiet);
	}
	USoundBase* Sound = bOpen ? DoorOpenSound.Get() : DoorCloseSound.Get();
	if (!Sound)
	{
		return;
	}
	if (!DoorAttenuation)
	{
		// heard in the room, gone two rooms away: full within 3 m, silent at 15 m
		DoorAttenuation = NewObject<USoundAttenuation>(this);
		DoorAttenuation->Attenuation.bAttenuate = true;
		DoorAttenuation->Attenuation.bSpatialize = true;
		DoorAttenuation->Attenuation.AttenuationShape = EAttenuationShape::Sphere;
		DoorAttenuation->Attenuation.AttenuationShapeExtents = FVector(300.f, 0.f, 0.f);
		DoorAttenuation->Attenuation.FalloffDistance = 1200.f;
	}
	UGameplayStatics::PlaySoundAtLocation(this, Sound, GetDoorLocation(Door), FRotator::ZeroRotator, USpaceUserSettings::GetEffectsVolume() * 0.8f,
		FMath::FRandRange(0.97f, 1.03f), 0.f, DoorAttenuation);
}

void UShipBoardingComponent::ApplyDoorCollision()
{
	for (const FDoorLeaf& Leaf : DoorLeaves)
	{
		UStaticMeshComponent* Mesh = Leaf.Mesh.Get();
		if (!Mesh)
		{
			continue;
		}
		// a shut leaf stops the walker (the rooms' rule while the interior is walked), an opening one lets him pass
		const bool bBlocks = bInteriorWalked && DoorOpen[Leaf.Door] < 0.6f;
		if (bBlocks)
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
	}
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
	ApplyDoorCollision();
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
	const FMinimalViewInfo Seated = PlayerController->PlayerCameraManager ? PlayerController->PlayerCameraManager->GetCameraCacheView() : FMinimalViewInfo();
	PlayerController->Possess(Pilot);
	if (APlayerCharacter* Character = Cast<APlayerCharacter>(Pilot))
	{
		Character->BoardInterior(Ship, Seat.GetRotation().GetForwardVector());
		// getting up: the view rises out of the seat and back over the backrest to the standing eye (author 5. 10. 2026)
		if (ASpacePlayerController* SpaceController = Cast<ASpacePlayerController>(PlayerController))
		{
			SpaceController->PlaySeatTransition(Seated, Character, Character->GetSeatBlendSeconds() * 0.85f, 18.f, 10.f);
		}
	}
	UE_LOG(LogSpaceship, Log, TEXT("%s: pilot up from the seat at %s"), *Ship->GetName(), *Start.GetLocation().ToString());
	return Pilot;
}

// -------------------------------------------------------------------------------------------
// Rear ramp (variant A, author 10. 10. 2026; Tools/Blender/hs_ramp.py)
// -------------------------------------------------------------------------------------------

namespace ShipRamp
{
	constexpr float RampSeconds = 3.0f;
	constexpr double ControlReachCm = 220.0;
	const TCHAR* const OpenSoundPath = TEXT("/Game/Ships/Audio/SW_GearDeploy.SW_GearDeploy");
	const TCHAR* const CloseSoundPath = TEXT("/Game/Ships/Audio/SW_GearRetract.SW_GearRetract");
}

void UShipBoardingComponent::FindRamp()
{
	bRampFound = true;
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	if (!Ship->Hull)
	{
		return;
	}
	FVector HingeWorld, TipWorld;
	if (!Ship->GetHullSocketLocation(TEXT("Ramp_hinge"), HingeWorld) || !Ship->GetHullSocketLocation(TEXT("Ramp_tip"), TipWorld))
	{
		return;
	}
	TArray<UStaticMeshComponent*> Meshes;
	Ship->GetComponents<UStaticMeshComponent>(Meshes);
	USceneComponent* Parent = nullptr;
	for (UStaticMeshComponent* Mesh : Meshes)
	{
		const FString Name = Mesh->GetName();
		if ((Name == TEXT("RampLeaf") || Name == TEXT("RampDecals")) && Mesh->GetStaticMesh())
		{
			RampParts.Add({ Mesh, Mesh->GetRelativeTransform() });
			Parent = Mesh->GetAttachParent();
			// the walk surface is the box below (per polygon the leaf blocked from one side only: a walker coming
			// downhill to its foot slipped under it)
			Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			if (Name == TEXT("RampLeaf"))
			{
				RampLeafMesh = Mesh;
			}
		}
	}
	if (RampParts.IsEmpty())
	{
		return;
	}
	const FTransform ParentTransform = Parent ? Parent->GetComponentTransform() : Ship->GetActorTransform();
	RampHingeRel = ParentTransform.InverseTransformPosition(HingeWorld);
	// the walked collision: a box over the leaf's slab (hinge, outer and inner top corner), riding on the leaf
	FVector TopWorld;
	if (RampLeafMesh.IsValid() && Ship->GetHullSocketLocation(TEXT("Ramp_top"), TopWorld))
	{
		UStaticMeshComponent* Leaf = RampLeafMesh.Get();
		const FTransform LeafT = Leaf->GetComponentTransform();
		const FVector H = LeafT.InverseTransformPosition(HingeWorld);
		const FVector Top = LeafT.InverseTransformPosition(TopWorld);
		const FVector Tip = LeafT.InverseTransformPosition(TipWorld);
		const FVector U = (Top - H).GetSafeNormal();
		const FVector N = (Tip - Top).GetSafeNormal();
		const double Length = FVector::Dist(Top, H);
		const double Thick = FVector::Dist(Tip, Top);
		const FVector Across = FVector::CrossProduct(N, U).GetSafeNormal();
		UBoxComponent* Box = NewObject<UBoxComponent>(Ship, TEXT("RampCollision"));
		Box->SetupAttachment(Leaf);
		Box->SetRelativeTransform(FTransform(FMatrix(U, Across, N, FVector::ZeroVector).ToQuat(), H + U * (Length * 0.5) + N * (Thick * 0.5)));
		Box->SetBoxExtent(FVector(Length * 0.5, 108.0, Thick * 0.5 + 1.0));
		Box->SetCollisionObjectType(ECC_WorldStatic);
		Box->SetCollisionResponseToAllChannels(ECR_Ignore);
		Box->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
		Box->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
		Box->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
		Box->SetHiddenInGame(true);
		Box->RegisterComponent();
		RampCollision = Box;
	}
	RampAxisRel = ParentTransform.InverseTransformVectorNoScale(Ship->GetActorRightVector()).GetSafeNormal();
	// the way that takes the free edge out aft (the FBX import mirrors y, so the sign is found, not assumed; "the
	// lower edge" picked the wrong way - turned forward the edge goes lower still, through the floor)
	const FVector TipRel = ParentTransform.InverseTransformPosition(TipWorld);
	const FVector ForwardRel = ParentTransform.InverseTransformVectorNoScale(Ship->GetActorForwardVector());
	auto TipAfter = [&](float Degrees)
	{
		return RampHingeRel + FQuat(RampAxisRel, FMath::DegreesToRadians(Degrees)).RotateVector(TipRel - RampHingeRel);
	};
	const float Angle = FMath::Abs(RampAngleDeg);
	RampAngleDeg = FVector::DotProduct(TipAfter(Angle) - RampHingeRel, ForwardRel) < FVector::DotProduct(TipAfter(-Angle) - RampHingeRel, ForwardRel) ? Angle : -Angle;
	// the walk zone: the open leaf, its passage and the switch, in the ship's frame
	const FTransform ToActor = ParentTransform.GetRelativeTransform(Ship->GetActorTransform());
	RampZoneLocal = FBox(ForceInit);
	RampZoneLocal += ToActor.TransformPosition(RampHingeRel);
	RampZoneLocal += ToActor.TransformPosition(TipAfter(RampAngleDeg));
	RampZoneLocal += ToActor.TransformPosition(TipRel);
	FVector Control;
	if (Ship->GetHullSocketLocation(TEXT("Control_ramp"), Control))
	{
		RampZoneLocal += Ship->GetActorTransform().InverseTransformPosition(Control);
	}
	RampZoneLocal = RampZoneLocal.ExpandBy(FVector(40.0, 130.0, 120.0));
	RoomsLocal = FBox(ForceInit);
	for (UStaticMeshComponent* Mesh : Meshes)
	{
		const FString Name = Mesh->GetName();
		if ((Name == TEXT("Interior") || Name == TEXT("InteriorKit")) && Mesh->GetStaticMesh())
		{
			RoomsLocal += Mesh->GetStaticMesh()->GetBoundingBox().TransformBy(Mesh->GetComponentTransform().GetRelativeTransform(Ship->GetActorTransform()));
		}
	}
	UE_LOG(LogSpaceship, Display, TEXT("%s: ramp of %d parts, opens %.0f deg; hinge %s, tip open %s (ship cm); walk zone %s .. %s, rooms %s .. %s"),
		*Ship->GetName(), RampParts.Num(), RampAngleDeg, *ToActor.TransformPosition(RampHingeRel).ToString(),
		*ToActor.TransformPosition(TipAfter(RampAngleDeg)).ToString(), *RampZoneLocal.Min.ToString(), *RampZoneLocal.Max.ToString(),
		*RoomsLocal.Min.ToString(), *RoomsLocal.Max.ToString());
}

bool UShipBoardingComponent::HasRamp() const
{
	if (!bRampFound)
	{
		const_cast<UShipBoardingComponent*>(this)->FindRamp();
	}
	return !RampParts.IsEmpty();
}

void UShipBoardingComponent::SetRampOpen(bool bOpen)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	if (!HasRamp())
	{
		return;
	}
	if (bOpen && !Ship->IsLanded())
	{
		UE_LOG(LogSpaceship, Log, TEXT("%s: the ramp stays shut in flight"), *Ship->GetName());
		return;
	}
	RampTarget = bOpen ? 1.f : 0.f;
}

void UShipBoardingComponent::TickRamp(float DeltaSeconds)
{
	if (!HasRamp())
	{
		return;
	}
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	// shut on take-off: after 2 s off the ground (a landed ship hops a little when it settles or is set down)
	RampAirborneSeconds = Ship->IsLanded() ? 0.f : RampAirborneSeconds + DeltaSeconds;
	if (RampTarget > 0.f && RampAirborneSeconds > 2.f)
	{
		RampTarget = 0.f;
	}
	if (RampSoundTarget != RampTarget)
	{
		RampSoundTarget = RampTarget;
		PlayRampSound(RampTarget > 0.5f);
	}
	const float Before = RampOpen;
	RampOpen = FMath::FInterpConstantTo(RampOpen, RampTarget, DeltaSeconds, 1.f / ShipRamp::RampSeconds);
	if (RampOpen != Before)
	{
		ApplyRamp();
		if (RampOpen >= 1.f && RampLeafMesh.IsValid())
		{
			UE_LOG(LogSpaceship, Display, TEXT("%s: ramp down, leaf centre %s, collision box centre %s (ship cm)"), *Ship->GetName(),
				*Ship->GetActorTransform().InverseTransformPosition(RampLeafMesh->Bounds.Origin).ToString(),
				RampCollision ? *Ship->GetActorTransform().InverseTransformPosition(RampCollision->GetComponentLocation()).ToString() : TEXT("-"));
		}
	}
}

void UShipBoardingComponent::ApplyRamp()
{
	// a hydraulic leaf: slow start, slow landing
	const float A = FMath::SmoothStep(0.f, 1.f, RampOpen);
	const FQuat Turn(RampAxisRel, FMath::DegreesToRadians(RampAngleDeg * A));
	const FTransform Pivot = FTransform(FQuat::Identity, -RampHingeRel) * FTransform(Turn) * FTransform(FQuat::Identity, RampHingeRel);
	for (const FRampPart& Part : RampParts)
	{
		if (UStaticMeshComponent* Mesh = Part.Mesh.Get())
		{
			Mesh->SetRelativeTransform(Part.ClosedRel * Pivot);
		}
	}
}

bool UShipBoardingComponent::IsInRampZone(const FVector& Location) const
{
	if (!HasRamp())
	{
		return false;
	}
	const ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	return RampZoneLocal.IsInside(Ship->GetActorTransform().InverseTransformPosition(Location));
}

bool UShipBoardingComponent::IsInsideRooms(const FVector& Location) const
{
	if (!HasRamp() || !RoomsLocal.IsValid)
	{
		return false;
	}
	const ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	return RoomsLocal.IsInside(Ship->GetActorTransform().InverseTransformPosition(Location));
}

bool UShipBoardingComponent::IsNearRampControl(const FVector& Location) const
{
	if (!HasRamp())
	{
		return false;
	}
	return FVector::Dist(GetRampPromptLocation(true), Location) < ShipRamp::ControlReachCm || IsInRampZone(Location);
}

FVector UShipBoardingComponent::GetRampPromptLocation(bool bInside) const
{
	const ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	FVector At;
	if (bInside && Ship->GetHullSocketLocation(TEXT("Control_ramp"), At))
	{
		return At;
	}
	FVector Hinge, Tip;
	if (Ship->GetHullSocketLocation(TEXT("Ramp_hinge"), Hinge) && Ship->GetHullSocketLocation(TEXT("Ramp_tip"), Tip))
	{
		// shut: half way up the leaf, outside; open: over its middle
		const FVector Mid = (Hinge + Tip) * 0.5;
		return RampOpen > 0.5f ? Hinge - Ship->GetActorForwardVector() * 120.0 + Ship->GetActorUpVector() * 60.0
			: Mid - Ship->GetActorForwardVector() * 40.0;
	}
	return Ship->GetActorLocation();
}

void UShipBoardingComponent::PlayRampSound(bool bOpen)
{
	if (!RampOpenSound)
	{
		RampOpenSound = LoadObject<USoundBase>(nullptr, ShipRamp::OpenSoundPath, nullptr, LOAD_NoWarn | LOAD_Quiet);
		RampCloseSound = LoadObject<USoundBase>(nullptr, ShipRamp::CloseSoundPath, nullptr, LOAD_NoWarn | LOAD_Quiet);
	}
	USoundBase* Sound = bOpen ? RampOpenSound.Get() : RampCloseSound.Get();
	if (!Sound)
	{
		return;
	}
	const ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	FVector Hinge = Ship->GetActorLocation();
	Ship->GetHullSocketLocation(TEXT("Ramp_hinge"), Hinge);
	UGameplayStatics::PlaySoundAtLocation(this, Sound, Hinge, FRotator::ZeroRotator, USpaceUserSettings::GetEffectsVolume());
}
