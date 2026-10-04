// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceInteraction.h"

#include "PlayerCharacter.h"
#include "ShipQuantumComponent.h"
#include "SpaceshipPawn.h"

#define LOCTEXT_NAMESPACE "SpaceInteraction"

namespace SpaceInteractionLocal
{
	/** Interact mode reaches hotspots this far from the eye on foot (SC: within arm's reach of a panel, a little more). */
	constexpr double ReachOnFootCm = 600.0;

	void AddMfds(ASpaceshipPawn* Ship, TArray<FSpaceHotspot>& Out)
	{
		const TWeakObjectPtr<ASpaceshipPawn> Weak(Ship);
		const TCHAR* Sockets[] = { TEXT("Display_left"), TEXT("Display_right") };
		const FText Labels[] = { LOCTEXT("MfdLeft", "LEVÉ MFD – DALŠÍ STRÁNKA"), LOCTEXT("MfdRight", "PRAVÉ MFD – DALŠÍ STRÁNKA") };
		for (int32 Display = 0; Display < 2; ++Display)
		{
			FVector At;
			if (!Ship->GetHullSocketLocation(Sockets[Display], At))
			{
				continue;
			}
			FSpaceHotspot Spot;
			Spot.Label = Labels[Display];
			Spot.SecondaryLabel = LOCTEXT("MfdBack", "PRAVÉ TLAČÍTKO: ZPĚT");
			Spot.WorldLocation = At;
			Spot.Use = [Weak, Display](bool bPrimary)
			{
				if (ASpaceshipPawn* Live = Weak.Get())
				{
					Live->CycleMfdPage(Display, bPrimary ? 1 : -1);
				}
			};
			Out.Add(MoveTemp(Spot));
		}
	}
}

void SpaceInteraction::Gather(APawn* Pawn, FSpaceInteractTarget& OutTarget, TArray<FSpaceHotspot>& OutHotspots)
{
	using namespace SpaceInteractionLocal;
	OutTarget = FSpaceInteractTarget();
	OutHotspots.Reset();

	// In the pilot seat: the seated actions go to the key list (SC), the screens are the hotspots.
	if (ASpaceshipPawn* Ship = Cast<ASpaceshipPawn>(Pawn))
	{
		AddMfds(Ship, OutHotspots);
		// Getting up is on the key list (SC); the seat itself is under the pilot's view.
		return;
	}

	APlayerCharacter* Character = Cast<APlayerCharacter>(Pawn);
	if (!Character)
	{
		return;
	}
	const FVector At = Character->GetActorLocation();
	if (ASpaceshipPawn* Inside = Character->GetInteriorShip())
	{
		FVector Seat, Ramp;
		// SC puts the seat prompt on the seat: a little under the pilot's eye (the WalkSeat socket is on the floor).
		const bool bSeat = Inside->HasWalkInterior();
		Seat = Inside->GetPilotEyeLocation() - Inside->GetActorUpVector() * 35.0;
		const bool bRamp = Inside->GetHullSocketLocation(TEXT("WalkRamp"), Ramp);
		if (Inside->IsNearSeat(At) && bSeat)
		{
			OutTarget.bValid = true;
			OutTarget.Label = LOCTEXT("Sit", "SEDNOUT");
			OutTarget.WorldLocation = Seat;
		}
		else if (Inside->IsNearRamp(At) && bRamp)
		{
			OutTarget.bValid = true;
			OutTarget.bAvailable = Inside->IsLanded();
			OutTarget.Label = Inside->IsLanded() ? LOCTEXT("StepOut", "VYSTOUPIT") : LOCTEXT("RampShut", "RAMPA ZAVŘENÁ ZA LETU");
			OutTarget.WorldLocation = Ramp;
		}
		const TWeakObjectPtr<APlayerCharacter> WeakCharacter(Character);
		if (bSeat && FVector::Dist(Seat, At) < ReachOnFootCm)
		{
			FSpaceHotspot Spot;
			Spot.Label = LOCTEXT("SitSpot", "SEDNOUT");
			Spot.WorldLocation = Seat;
			Spot.Use = [WeakCharacter](bool bPrimary)
			{
				if (APlayerCharacter* Live = WeakCharacter.Get(); bPrimary && Live && Live->GetInteriorShip()
					&& Live->GetInteriorShip()->IsNearSeat(Live->GetActorLocation()))
				{
					Live->Interact();
				}
			};
			OutHotspots.Add(MoveTemp(Spot));
			AddMfds(Inside, OutHotspots);
		}
		if (bRamp && FVector::Dist(Ramp, At) < ReachOnFootCm && Inside->IsLanded())
		{
			FSpaceHotspot Spot;
			Spot.Label = LOCTEXT("RampSpot", "VYSTOUPIT");
			Spot.WorldLocation = Ramp;
			Spot.Use = [WeakCharacter](bool bPrimary)
			{
				if (APlayerCharacter* Live = WeakCharacter.Get(); bPrimary && Live && Live->GetInteriorShip()
					&& Live->GetInteriorShip()->IsNearRamp(Live->GetActorLocation()))
				{
					Live->Interact();
				}
			};
			OutHotspots.Add(MoveTemp(Spot));
		}
		return;
	}

	double Distance = 0.0;
	if (ASpaceshipPawn* Ship = Character->FindBoardableShip(Distance))
	{
		FVector Ramp;
		OutTarget.bValid = true;
		OutTarget.Label = Ship->HasWalkInterior() ? LOCTEXT("WalkIn", "VSTOUPIT DO LODI") : LOCTEXT("Board", "NASTOUPIT");
		OutTarget.WorldLocation = Ship->GetHullSocketLocation(TEXT("WalkRamp"), Ramp) ? Ramp
			: Ship->GetHullSocketLocation(TEXT("Exit"), Ramp) ? Ramp : Ship->GetActorLocation();
	}
}

void SpaceInteraction::KeyHints(APawn* Pawn, bool bInteractMode, const FSpaceInteractTarget& Target, TArray<FSpaceKeyHint>& Out)
{
	Out.Reset();
	auto Add = [&Out](const FText& Action, const TCHAR* Key) { Out.Add({ Action, Key }); };
	if (bInteractMode)
	{
		Add(LOCTEXT("HintUse", "POUŽÍT"), TEXT("LMB"));
		Add(LOCTEXT("HintBack", "ZPĚT (MFD)"), TEXT("RMB"));
		Add(LOCTEXT("HintLeave", "ZAVŘÍT INTERAKCI (PUSTIT)"), TEXT("F"));
		return;
	}
	if (const ASpaceshipPawn* Ship = Cast<ASpaceshipPawn>(Pawn))
	{
		if (Ship->CanLeaveSeat())
		{
			Add(LOCTEXT("HintGetUp", "VSTÁT"), TEXT("F"));
		}
		else if (Ship->CanExit())
		{
			Add(LOCTEXT("HintGetOut", "VYSTOUPIT"), TEXT("F"));
		}
		Add(LOCTEXT("HintInteractMode", "INTERAKCE (DRŽET)"), TEXT("F"));
		if (Ship->IsLanded())
		{
			Add(LOCTEXT("HintTakeOff", "VZLET"), TEXT("Space"));
		}
		else
		{
			Add(Ship->IsGearDeployed() ? LOCTEXT("HintGearUp", "ZASUNOUT PODVOZEK") : LOCTEXT("HintGearDown", "VYSUNOUT PODVOZEK"), TEXT("N"));
			Add(LOCTEXT("HintMode", "SCM / NAV"), TEXT("B"));
			Add(LOCTEXT("HintCoupled", "COUPLED / DECOUPLED"), TEXT("V"));
			Add(LOCTEXT("HintBrake", "VESMÍRNÁ BRZDA"), TEXT("X"));
			if (Ship->GetQuantumState() == EQuantumState::Ready)
			{
				Add(LOCTEXT("HintQuantum", "QUANTUM SKOK (DRŽET)"), TEXT("LMB"));
			}
		}
		Add(LOCTEXT("HintCamera", "KAMERA"), TEXT("C"));
		return;
	}
	if (Target.bValid && Target.bAvailable)
	{
		Out.Add({ Target.Label, TEXT("F") });
	}
	Add(LOCTEXT("HintInteractModeFoot", "INTERAKCE (DRŽET)"), TEXT("F"));
	Add(LOCTEXT("HintJump", "SKOK"), TEXT("Space"));
	Add(LOCTEXT("HintRun", "BĚH"), TEXT("Shift"));
}

void SpaceInteraction::Interact(APawn* Pawn)
{
	if (ASpaceshipPawn* Ship = Cast<ASpaceshipPawn>(Pawn))
	{
		Ship->Interact();
	}
	else if (APlayerCharacter* Character = Cast<APlayerCharacter>(Pawn))
	{
		Character->Interact();
	}
}

#undef LOCTEXT_NAMESPACE
