// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceInterior.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "PlayerCharacter.h"
#include "SpacePlayerController.h"

DEFINE_LOG_CATEGORY_STATIC(LogSpaceInterior, Log, All);

// -------------------------------------------------------------------------------------------
// Gravity volume
// -------------------------------------------------------------------------------------------

ASpaceGravityVolume::ASpaceGravityVolume()
{
	PrimaryActorTick.bCanEverTick = false;
	Volume = CreateDefaultSubobject<UBoxComponent>(TEXT("Volume"));
	Volume->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Volume->SetBoxExtent(FVector(500.f));
	Volume->SetMobility(EComponentMobility::Movable);
	RootComponent = Volume;
}

bool ASpaceGravityVolume::ContainsPoint(const FVector& Location) const
{
	const FVector Local = Volume->GetComponentTransform().InverseTransformPositionNoScale(Location);
	const FVector Extent = Volume->GetScaledBoxExtent();
	return FMath::Abs(Local.X) <= Extent.X && FMath::Abs(Local.Y) <= Extent.Y && FMath::Abs(Local.Z) <= Extent.Z;
}

const ASpaceGravityVolume* ASpaceGravityVolume::FindAt(const UWorld* World, const FVector& Location)
{
	if (!World)
	{
		return nullptr;
	}
	for (TActorIterator<ASpaceGravityVolume> It(const_cast<UWorld*>(World)); It; ++It)
	{
		if (It->ContainsPoint(Location))
		{
			return *It;
		}
	}
	return nullptr;
}

// -------------------------------------------------------------------------------------------
// Sliding door
// -------------------------------------------------------------------------------------------

ASpaceSlidingDoor::ASpaceSlidingDoor()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.f;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Threshold"));
	RootComponent->SetMobility(EComponentMobility::Static);
	for (TObjectPtr<UStaticMeshComponent>* Leaf : { &LeafA, &LeafB })
	{
		*Leaf = CreateDefaultSubobject<UStaticMeshComponent>(Leaf == &LeafA ? TEXT("LeafA") : TEXT("LeafB"));
		(*Leaf)->SetupAttachment(RootComponent);
		(*Leaf)->SetMobility(EComponentMobility::Movable);
		(*Leaf)->SetCollisionProfileName(UCollisionProfile::BlockAll_ProfileName);
	}
}

FVector ASpaceSlidingDoor::ComputeLeafLocation(float LeafWidthCm, float LeafHeightCm, float Side, float InOpenness)
{
	// Closed: the two leaves meet at the middle (each centred half a leaf out). Open: each has slid
	// a whole leaf further out, behind the jamb.
	const float Eased = InOpenness * InOpenness * (3.f - 2.f * InOpenness);
	return FVector(0.f, Side * LeafWidthCm * (0.5f + Eased * 0.98f), LeafHeightCm * 0.5f);
}

void ASpaceSlidingDoor::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	LayoutLeaves();
}

void ASpaceSlidingDoor::BeginPlay()
{
	Super::BeginPlay();
	LayoutLeaves();
}

void ASpaceSlidingDoor::LayoutLeaves()
{
	LeafSize = FVector::ZeroVector;
	if (const UStaticMesh* Mesh = LeafA ? LeafA->GetStaticMesh() : nullptr)
	{
		LeafSize = Mesh->GetBoundingBox().GetSize();
	}
	if (LeafB && LeafA && !LeafB->GetStaticMesh())
	{
		LeafB->SetStaticMesh(LeafA->GetStaticMesh());
	}
	PlaceLeaves();
}

void ASpaceSlidingDoor::PlaceLeaves()
{
	if (LeafSize.IsNearlyZero())
	{
		return;
	}
	// The second leaf turned round, so the same mesh reads mirrored.
	LeafA->SetRelativeLocationAndRotation(ComputeLeafLocation(LeafSize.Y, LeafSize.Z, -1.f, Openness), FRotator::ZeroRotator);
	LeafB->SetRelativeLocationAndRotation(ComputeLeafLocation(LeafSize.Y, LeafSize.Z, 1.f, Openness), FRotator(0.f, 180.f, 0.f));
}

void ASpaceSlidingDoor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	bool bOpen = Forced == 1;
	if (Forced < 0)
	{
		const FVector Here = GetActorLocation();
		for (FConstPlayerControllerIterator It = GetWorld()->GetPlayerControllerIterator(); It; ++It)
		{
			const APawn* Pawn = It->Get() ? It->Get()->GetPawn() : nullptr;
			if (Pawn && FVector::DistSquared(Pawn->GetActorLocation(), Here) < FMath::Square(TriggerRadiusCm))
			{
				bOpen = true;
			}
		}
	}
	const float Target = bOpen ? 1.f : 0.f;
	if (!FMath::IsNearlyEqual(Openness, Target))
	{
		Openness = FMath::FInterpConstantTo(Openness, Target, DeltaSeconds, 1.f / OpenSeconds);
		PlaceLeaves();
	}
}

// -------------------------------------------------------------------------------------------
// Console
// -------------------------------------------------------------------------------------------

namespace
{
	FAutoConsoleCommandWithWorldAndArgs InteriorCommand(
		TEXT("space.Interior"),
		TEXT("space.Interior: walk the Steadfast interior (from the ship, or back into it). The same as I in the game."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			ASpacePlayerController* Controller = World ? Cast<ASpacePlayerController>(World->GetFirstPlayerController()) : nullptr;
			const bool bDone = Controller && Controller->ToggleInterior();
			UE_LOG(LogSpaceInterior, Display, TEXT("space.Interior: %s"), bDone
				? (Controller->IsWalkingInterior() ? TEXT("walking the interior") : TEXT("back in the ship"))
				: TEXT("nothing to do (no interior in this level, or no ship to go back to)"));
		}));

	/**
	 * space.Walk <forward> <right> <seconds> [yaw]: the character walks as if the keys were held
	 * (forward/right -1..1), optionally facing yaw degrees first (relative to the gravity frame).
	 * For shots and for checking collision in the packaged game: it logs where it ended up.
	 */
	FAutoConsoleCommandWithWorldAndArgs WalkCommand(
		TEXT("space.Walk"),
		TEXT("space.Walk <forward> <right> <seconds> [yaw]: walk the player's character as if keys were held; logs where it stops."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			APlayerController* Controller = World ? World->GetFirstPlayerController() : nullptr;
			APlayerCharacter* Character = Controller ? Cast<APlayerCharacter>(Controller->GetPawn()) : nullptr;
			if (!Character || Args.Num() < 3)
			{
				UE_LOG(LogSpaceInterior, Display, TEXT("space.Walk <forward> <right> <seconds> [yaw] (on foot only)"));
				return;
			}
			if (Args.Num() > 3)
			{
				Character->SetLookYaw(FCString::Atof(*Args[3]));
			}
			Character->DebugWalk(FVector2D(FCString::Atof(*Args[1]), FCString::Atof(*Args[0])), FCString::Atof(*Args[2]));
		}));

	FAutoConsoleCommandWithWorldAndArgs DoorCommand(
		TEXT("space.Door"),
		TEXT("space.Door 1|0|-1: every sliding door open, closed, or automatic again."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			const int32 State = Args.Num() > 0 ? FCString::Atoi(*Args[0]) : -1;
			int32 Count = 0;
			for (TActorIterator<ASpaceSlidingDoor> It(World); It; ++It)
			{
				It->ForceOpen(State);
				++Count;
			}
			UE_LOG(LogSpaceInterior, Display, TEXT("space.Door %d on %d doors"), State, Count);
		}));
}
