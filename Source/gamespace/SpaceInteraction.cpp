// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceInteraction.h"

#include "PlayerCharacter.h"
#include "ShipQuantumComponent.h"
#include "SpaceshipPawn.h"
#include "SpaceFlightHud.h"

#define LOCTEXT_NAMESPACE "SpaceInteraction"

namespace SpaceInteractionLocal
{
	/** Interact mode reaches hotspots this far from the eye on foot (SC: within arm's reach of a panel, a little more). */
	constexpr double ReachOnFootCm = 600.0;

	/** The left MFD's CONFIGURATION page, while it is up: each row's switch. */
	void AddConfig(ASpaceshipPawn* Ship, TArray<FSpaceHotspot>& Out)
	{
		if (Ship->GetPowerState() != ESpacePowerState::On || Ship->GetMfdPage(0) != USpaceCockpitDisplays::ConfigPage)
		{
			return;
		}
		const TWeakObjectPtr<ASpaceshipPawn> Weak(Ship);
		const bool bOn[] = { Ship->IsFlightAssistOn(), Ship->IsGSafeOn(), Ship->IsComStabOn(), Ship->IsPrecisionModeOn(), Ship->IsVtolOn() };
		for (int32 Row = 0; Row < USpaceCockpitDisplays::ConfigRowNames().Num() && Row < UE_ARRAY_COUNT(bOn); ++Row)
		{
			FVector At;
			if (!Ship->GetDisplayPoint(0, USpaceCockpitDisplays::ConfigSwitchUV(Row), At))
			{
				return;
			}
			FSpaceHotspot Spot;
			Spot.Label = FText::Format(bOn[Row] ? LOCTEXT("CfgOff", "{0}: VYPNOUT") : LOCTEXT("CfgOn", "{0}: ZAPNOUT"),
				FText::FromString(USpaceCockpitDisplays::ConfigRowNames()[Row]));
			Spot.WorldLocation = At;
			Spot.SizeCm = 6.f;
			Spot.Aspect = 2.3f;      // the ON / OFF pill
			// The label over the display's top frame, above this switch: never over the page (critic 4. 10.).
			Spot.bLabelAnchor = Ship->GetDisplayPoint(0, FVector2D(USpaceCockpitDisplays::ConfigSwitchUV(Row).X - 0.25, -0.07), Spot.LabelWorldLocation);
			Spot.Use = [Weak, Row](bool bPrimary)
			{
				ASpaceshipPawn* Live = Weak.Get();
				if (!Live || !bPrimary)
				{
					return;
				}
				switch (Row)
				{
				case 0: Live->SetFlightAssist(!Live->IsFlightAssistOn()); break;
				case 1: Live->SetGSafe(!Live->IsGSafeOn()); break;
				case 2: Live->SetComStab(!Live->IsComStabOn()); break;
				case 3: Live->TogglePrecisionMode(); break;
				default: Live->ToggleVtol(); break;
				}
			};
			Out.Add(MoveTemp(Spot));
		}
	}

	/** The dashboard's PWR selector (SC: the lit POWER key you click in interact mode). */
	void AddPower(ASpaceshipPawn* Ship, TArray<FSpaceHotspot>& Out)
	{
		FVector At;
		if (!Ship->GetPowerControlLocation(At))
		{
			return;
		}
		const TWeakObjectPtr<ASpaceshipPawn> Weak(Ship);
		FSpaceHotspot Spot;
		Spot.Label = Ship->GetPowerState() == ESpacePowerState::Off ? LOCTEXT("PowerOn", "ZAPNOUT NAPÁJENÍ") : LOCTEXT("PowerOff", "VYPNOUT NAPÁJENÍ");
		Spot.WorldLocation = At;
		Spot.SizeCm = 4.f;
		Spot.Use = [Weak](bool bPrimary)
		{
			if (ASpaceshipPawn* Live = Weak.Get(); Live && bPrimary)
			{
				Live->TogglePower();
			}
		};
		Out.Add(MoveTemp(Spot));
	}

	void AddMfds(ASpaceshipPawn* Ship, TArray<FSpaceHotspot>& Out)
	{
		// Dark glass has no pages to click through.
		if (Ship->GetPowerState() != ESpacePowerState::On)
		{
			return;
		}
		const TWeakObjectPtr<ASpaceshipPawn> Weak(Ship);
		for (int32 Display = 0; Display < 2; ++Display)
		{
			// The page tab's arrows at the bottom of the page (SC): < the page before, > the next one. Each is its own
			// small control the cursor has to be on (author 5. 10. 2026: "click right on the arrow, not the middle").
			for (const int32 Step : { -1, 1 })
			{
				FVector At;
				if (!Ship->GetDisplayPoint(Display, FVector2D(Step < 0 ? 0.035 : 0.965, 0.94), At))
				{
					continue;
				}
				FSpaceHotspot Spot;
				Spot.Label = Step < 0 ? LOCTEXT("MfdPrev", "PŘEDCHOZÍ STRÁNKA") : LOCTEXT("MfdNext", "DALŠÍ STRÁNKA");
				Spot.WorldLocation = At;
				Spot.SizeCm = 3.f;
				Spot.Aspect = 0.8f;      // the arrow glyph, a little taller than wide
				Spot.Use = [Weak, Display, Step](bool bPrimary)
				{
					if (ASpaceshipPawn* Live = Weak.Get())
					{
						Live->CycleMfdPage(Display, bPrimary ? Step : -Step);
					}
				};
				Out.Add(MoveTemp(Spot));
			}
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
		AddPower(Ship, OutHotspots);
		AddConfig(Ship, OutHotspots);
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
		else if (const int32 Door = Inside->FindDoorAhead(At + Inside->GetActorUpVector() * 40.0, Pawn->GetViewRotation().Vector(), 160.f); Door != INDEX_NONE)
		{
			OutTarget.bValid = true;
			OutTarget.bVertical = true;
			OutTarget.Label = Inside->IsDoorOpen(Door) ? LOCTEXT("DoorClose", "ZAVŘÍT") : LOCTEXT("DoorOpen", "OTEVŘÍT");
			// a little under the eye on the door (SC's prompt sits on the panel, not at the walker's feet)
			OutTarget.WorldLocation = Inside->GetDoorPromptLocation(Door) + Inside->GetActorUpVector() * 25.0;
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
			Spot.SizeCm = 30.f;
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
			AddPower(Inside, OutHotspots);
			AddConfig(Inside, OutHotspots);
		}
		if (bRamp && FVector::Dist(Ramp, At) < ReachOnFootCm && Inside->IsLanded())
		{
			FSpaceHotspot Spot;
			Spot.Label = LOCTEXT("RampSpot", "VYSTOUPIT");
			Spot.WorldLocation = Ramp;
			Spot.SizeCm = 50.f;
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
		if (Cast<ASpaceshipPawn>(Pawn))
		{
			Add(LOCTEXT("HintPowerInteract", "NAPÁJENÍ (ZAP/VYP)"), TEXT("U"));
		}
		Add(LOCTEXT("HintUse", "POUŽÍT"), TEXT("LMB"));
		Add(LOCTEXT("HintBack", "ZPĚT (MFD)"), TEXT("RMB"));
		Add(LOCTEXT("HintLeave", "ZAVŘÍT INTERAKCI (PUSTIT)"), TEXT("F"));
		return;
	}
	if (const ASpaceshipPawn* Ship = Cast<ASpaceshipPawn>(Pawn))
	{
		// SC's list starts with POWER (TOGGLE) [U]; without power only the seat, interact mode and the camera.
		Add(LOCTEXT("HintPower", "NAPÁJENÍ (ZAP/VYP)"), TEXT("U"));
		if (Ship->IsLeaveSeatPending())
		{
			Add(LOCTEXT("HintGetUpCancel", "ZŮSTAT SEDĚT (LOĎ BRZDÍ)"), TEXT("F"));
		}
		else if (Ship->CanLeaveSeat())
		{
			Add(LOCTEXT("HintGetUp", "VSTÁT"), TEXT("F"));
		}
		else if (Ship->CanLeaveSeatInFlight())
		{
			Add(LOCTEXT("HintGetUpFlight", "VSTÁT (LOĎ ZASTAVÍ)"), TEXT("F"));
		}
		else if (Ship->CanExit())
		{
			Add(LOCTEXT("HintGetOut", "VYSTOUPIT"), TEXT("F"));
		}
		Add(LOCTEXT("HintInteractMode", "INTERAKCE (DRŽET)"), TEXT("F"));
		if (!Ship->IsPowered())
		{
			// nothing to fly yet
		}
		else if (Ship->IsLanded())
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
