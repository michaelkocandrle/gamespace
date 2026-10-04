// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceControls.h"

#define LOCTEXT_NAMESPACE "SpaceControls"

const TArray<FSpaceControl>& FSpaceControls::Get()
{
	using M = ESpaceControlMode;
	using C = ESpaceControlCategory;
	static const TArray<FSpaceControl> Controls = []()
	{
		TArray<FSpaceControl> T;
		auto Add = [&T](M Mode, const TCHAR* Key, bool bAlt, const FText& Label, C Category, const TCHAR* Action)
		{
			FSpaceControl Control;
			Control.Mode = Mode;
			Control.Key = FName(Key);
			Control.bAlt = bAlt;
			Control.Label = Label;
			Control.Category = Category;
			Control.Action = Action ? FName(Action) : NAME_None;
			T.Add(Control);
		};
		// Flight (IMC_Spaceship, IMC_SpaceshipMouse).
		Add(M::Flight, TEXT("W"), false, LOCTEXT("ThrustFwd", "Tah\nvpřed"), C::Movement, TEXT("IA_Thrust"));
		Add(M::Flight, TEXT("S"), false, LOCTEXT("ThrustBack", "Tah\nvzad"), C::Movement, TEXT("IA_Thrust"));
		Add(M::Flight, TEXT("A"), false, LOCTEXT("StrafeLeft", "Úkrok\nvlevo"), C::Movement, TEXT("IA_Strafe"));
		Add(M::Flight, TEXT("D"), false, LOCTEXT("StrafeRight", "Úkrok\nvpravo"), C::Movement, TEXT("IA_Strafe"));
		Add(M::Flight, TEXT("SpaceBar"), false, LOCTEXT("LiftUp", "Stoupání"), C::Movement, TEXT("IA_Lift"));
		Add(M::Flight, TEXT("LeftControl"), false, LOCTEXT("LiftDown", "Klesání"), C::Movement, TEXT("IA_Lift"));
		Add(M::Flight, TEXT("Q"), false, LOCTEXT("RollLeft", "Náklon\nvlevo"), C::Movement, TEXT("IA_Roll"));
		Add(M::Flight, TEXT("E"), false, LOCTEXT("RollRight", "Náklon\nvpravo"), C::Movement, TEXT("IA_Roll"));
		Add(M::Flight, TEXT("Mouse2D"), false, LOCTEXT("Steer", "Klopení a zatáčení (VJoy)"), C::Movement, TEXT("IA_Look"));
		Add(M::Flight, TEXT("LeftShift"), false, LOCTEXT("Boost", "Boost"), C::Systems, TEXT("IA_Boost"));
		Add(M::Flight, TEXT("Tab"), false, LOCTEXT("Afterburner", "Přídavný\ntah (AB)"), C::Systems, TEXT("IA_Afterburner"));
		Add(M::Flight, TEXT("V"), false, LOCTEXT("Coupled", "Coupled /\nDecoupled"), C::Systems, TEXT("IA_FlightAssist"));
		Add(M::Flight, TEXT("X"), false, LOCTEXT("SpaceBrake", "Vesmírná\nbrzda"), C::Systems, TEXT("IA_AllStop"));
		Add(M::Flight, TEXT("B"), false, LOCTEXT("MasterMode", "SCM /\nNAV"), C::Systems, TEXT("IA_MasterMode"));
		Add(M::Flight, TEXT("K"), false, LOCTEXT("GSafe", "G-Safe"), C::Systems, TEXT("IA_GSafe"));
		Add(M::Flight, TEXT("L"), false, LOCTEXT("ComStab", "ComStab"), C::Systems, TEXT("IA_ComStab"));
		Add(M::Flight, TEXT("MouseWheelAxis"), false, LOCTEXT("Limiter", "Omezovač rychlosti"), C::Systems, TEXT("IA_SpeedLimiter"));
		Add(M::Flight, TEXT("N"), false, LOCTEXT("Gear", "Podvozek"), C::Landing, TEXT("IA_LandingGear"));
		Add(M::Flight, TEXT("P"), false, LOCTEXT("Precision", "Přesný\nrežim"), C::Landing, TEXT("IA_Precision"));
		Add(M::Flight, TEXT("G"), false, LOCTEXT("Vtol", "VTOL"), C::Landing, TEXT("IA_Vtol"));
		Add(M::Flight, TEXT("LeftMouseButton"), false, LOCTEXT("Quantum", "Quantum skok (podržet, NAV)"), C::Navigation, TEXT("IA_QuantumEngage"));
		Add(M::Flight, TEXT("C"), false, LOCTEXT("Camera", "Kamera\n1. / 3. os."), C::Camera, TEXT("IA_ToggleCamera"));
		Add(M::Flight, TEXT("RightMouseButton"), false, LOCTEXT("FreeLook", "Volné rozhlížení (podržet)"), C::Camera, TEXT("IA_FreeLook"));
		Add(M::Flight, TEXT("Z"), false, LOCTEXT("Focus", "Pohled\nna desku"), C::Camera, TEXT("IA_DashboardFocus"));
		Add(M::Flight, TEXT("MiddleMouseButton"), false, LOCTEXT("FocusMouse", "Pohled na desku (podržet)"), C::Camera, TEXT("IA_DashboardFocus"));
		Add(M::Flight, TEXT("MouseWheelAxis"), true, LOCTEXT("Zoom", "Zoom kamery"), C::Camera, TEXT("IA_CameraZoom"));
		Add(M::Flight, TEXT("F1"), false, LOCTEXT("MfdLeft", "Levé\nMFD"), C::Interface, TEXT("IA_MfdLeft"));
		Add(M::Flight, TEXT("F2"), false, LOCTEXT("MfdRight", "Pravé\nMFD"), C::Interface, TEXT("IA_MfdRight"));
		Add(M::Flight, TEXT("LeftBracket"), false, LOCTEXT("MfdLeftUs", "Levé\nMFD"), C::Interface, TEXT("IA_MfdLeft"));
		Add(M::Flight, TEXT("RightBracket"), false, LOCTEXT("MfdRightUs", "Pravé\nMFD"), C::Interface, TEXT("IA_MfdRight"));
		Add(M::Flight, TEXT("F1"), true, LOCTEXT("MfdLeftBack", "Alt: zpět"), C::Interface, nullptr);
		Add(M::Flight, TEXT("F2"), true, LOCTEXT("MfdRightBack", "Alt: zpět"), C::Interface, nullptr);
		Add(M::Flight, TEXT("F"), false, LOCTEXT("GetUp", "Vstát /\nvystoupit"), C::Interaction, TEXT("IA_Interact"));
		// On foot (IMC_Character, and the view switch the character adds itself).
		Add(M::OnFoot, TEXT("W"), false, LOCTEXT("WalkFwd", "Chůze\nvpřed"), C::Movement, TEXT("IA_CharMove"));
		Add(M::OnFoot, TEXT("S"), false, LOCTEXT("WalkBack", "Chůze\nvzad"), C::Movement, TEXT("IA_CharMove"));
		Add(M::OnFoot, TEXT("A"), false, LOCTEXT("WalkLeft", "Úkrok\nvlevo"), C::Movement, TEXT("IA_CharMove"));
		Add(M::OnFoot, TEXT("D"), false, LOCTEXT("WalkRight", "Úkrok\nvpravo"), C::Movement, TEXT("IA_CharMove"));
		Add(M::OnFoot, TEXT("SpaceBar"), false, LOCTEXT("Jump", "Skok"), C::Movement, TEXT("IA_CharJump"));
		Add(M::OnFoot, TEXT("LeftShift"), false, LOCTEXT("Sprint", "Běh"), C::Movement, TEXT("IA_CharSprint"));
		Add(M::OnFoot, TEXT("Mouse2D"), false, LOCTEXT("LookAround", "Rozhlížení"), C::Camera, TEXT("IA_CharLook"));
		Add(M::OnFoot, TEXT("F"), false, LOCTEXT("Interact", "Interakce"), C::Interaction, TEXT("IA_Interact"));
		// Everywhere (the controller's own context).
		Add(M::Global, TEXT("Escape"), false, LOCTEXT("Menu", "Menu"), C::Interface, nullptr);
		Add(M::Global, TEXT("F10"), false, LOCTEXT("MenuF10", "Menu"), C::Interface, nullptr);
		Add(M::Global, TEXT("H"), false, LOCTEXT("Hud", "HUD"), C::Interface, TEXT("IA_ToggleHud"));
		Add(M::Global, TEXT("I"), false, LOCTEXT("Interior", "Prohlídka\ninteriéru"), C::Interface, nullptr);
		return T;
	}();
	return Controls;
}

FLinearColor FSpaceControls::CategoryColor(ESpaceControlCategory Category)
{
	switch (Category)
	{
	case ESpaceControlCategory::Movement: return FLinearColor(0.30f, 0.75f, 1.00f);
	case ESpaceControlCategory::Systems: return FLinearColor(1.00f, 0.55f, 0.15f);
	case ESpaceControlCategory::Landing: return FLinearColor(1.00f, 0.85f, 0.00f);
	case ESpaceControlCategory::Camera: return FLinearColor(0.00f, 0.55f, 1.00f);
	case ESpaceControlCategory::Navigation: return FLinearColor(1.00f, 0.08f, 0.75f);
	case ESpaceControlCategory::Interaction: return FLinearColor(0.10f, 1.00f, 0.25f);
	default: return FLinearColor(0.75f, 0.80f, 0.78f);
	}
}

FText FSpaceControls::CategoryName(ESpaceControlCategory Category)
{
	switch (Category)
	{
	case ESpaceControlCategory::Movement: return LOCTEXT("CatMovement", "Pohyb");
	case ESpaceControlCategory::Systems: return LOCTEXT("CatSystems", "Systémy lodi");
	case ESpaceControlCategory::Landing: return LOCTEXT("CatLanding", "Přistání");
	case ESpaceControlCategory::Camera: return LOCTEXT("CatCamera", "Kamera a pohled");
	case ESpaceControlCategory::Navigation: return LOCTEXT("CatNavigation", "Navigace a quantum");
	case ESpaceControlCategory::Interaction: return LOCTEXT("CatInteraction", "Interakce");
	default: return LOCTEXT("CatInterface", "Rozhraní");
	}
}

TArray<FString> USpaceControlsLibrary::DescribeControls()
{
	TArray<FString> Lines;
	for (const FSpaceControl& Control : FSpaceControls::Get())
	{
		const TCHAR* Mode = Control.Mode == ESpaceControlMode::Flight ? TEXT("flight") : Control.Mode == ESpaceControlMode::OnFoot ? TEXT("onfoot") : TEXT("global");
		Lines.Add(FString::Printf(TEXT("%s|%s|%d|%s|%s"), Mode, *Control.Key.ToString(), Control.bAlt ? 1 : 0,
			Control.Action.IsNone() ? TEXT("") : *Control.Action.ToString(), *Control.Label.ToString().Replace(TEXT("\n"), TEXT(" "))));
	}
	return Lines;
}

#undef LOCTEXT_NAMESPACE
