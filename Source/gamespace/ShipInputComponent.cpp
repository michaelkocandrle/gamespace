// Copyright Epic Games, Inc. All Rights Reserved.

#include "ShipInputComponent.h"

#include "CockpitDisplayComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "GameFramework/PlayerController.h"
#include "SpacePlayerController.h"
#include "InputAction.h"
#include "InputActionValue.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "InputTriggers.h"
#include "SpaceshipLog.h"
#include "SpaceshipPawn.h"

namespace ShipInputDefaults
{
	/** Authored Enhanced Input assets are looked for here before anything is generated. */
	const TCHAR* const MappingContextPath = TEXT("/Game/Input/IMC_Spaceship.IMC_Spaceship");
	const TCHAR* const ThrustActionPath = TEXT("/Game/Input/IA_Thrust.IA_Thrust");
	const TCHAR* const StrafeActionPath = TEXT("/Game/Input/IA_Strafe.IA_Strafe");
	const TCHAR* const LiftActionPath = TEXT("/Game/Input/IA_Lift.IA_Lift");
	const TCHAR* const RollActionPath = TEXT("/Game/Input/IA_Roll.IA_Roll");
	const TCHAR* const LookActionPath = TEXT("/Game/Input/IA_Look.IA_Look");
	const TCHAR* const ToggleCameraActionPath = TEXT("/Game/Input/IA_ToggleCamera.IA_ToggleCamera");
	const TCHAR* const BoostActionPath = TEXT("/Game/Input/IA_Boost.IA_Boost");
	const TCHAR* const InteractActionPath = TEXT("/Game/Input/IA_Interact.IA_Interact");
	const TCHAR* const FreeLookActionPath = TEXT("/Game/Input/IA_FreeLook.IA_FreeLook");
	const TCHAR* const MouseLookActionPath = TEXT("/Game/Input/IA_LookMouse.IA_LookMouse");
	const TCHAR* const MouseMappingContextPath = TEXT("/Game/Input/IMC_SpaceshipMouse.IMC_SpaceshipMouse");
	const TCHAR* const FlightAssistActionPath = TEXT("/Game/Input/IA_FlightAssist.IA_FlightAssist");
	const TCHAR* const QuantumEngageActionPath = TEXT("/Game/Input/IA_QuantumEngage.IA_QuantumEngage");
	const TCHAR* const AllStopActionPath = TEXT("/Game/Input/IA_AllStop.IA_AllStop");
	const TCHAR* const CameraZoomActionPath = TEXT("/Game/Input/IA_CameraZoom.IA_CameraZoom");
	const TCHAR* const MasterModeActionPath = TEXT("/Game/Input/IA_MasterMode.IA_MasterMode");
	const TCHAR* const SpeedLimiterActionPath = TEXT("/Game/Input/IA_SpeedLimiter.IA_SpeedLimiter");
	const TCHAR* const GSafeActionPath = TEXT("/Game/Input/IA_GSafe.IA_GSafe");
	const TCHAR* const ComStabActionPath = TEXT("/Game/Input/IA_ComStab.IA_ComStab");
	const TCHAR* const AfterburnerActionPath = TEXT("/Game/Input/IA_Afterburner.IA_Afterburner");
	const TCHAR* const LandingGearActionPath = TEXT("/Game/Input/IA_LandingGear.IA_LandingGear");
	const TCHAR* const PrecisionActionPath = TEXT("/Game/Input/IA_Precision.IA_Precision");
	const TCHAR* const VtolActionPath = TEXT("/Game/Input/IA_Vtol.IA_Vtol");
	const TCHAR* const MfdLeftActionPath = TEXT("/Game/Input/IA_MfdLeft.IA_MfdLeft");
	const TCHAR* const DashboardFocusActionPath = TEXT("/Game/Input/IA_DashboardFocus.IA_DashboardFocus");
	const TCHAR* const MfdRightActionPath = TEXT("/Game/Input/IA_MfdRight.IA_MfdRight");

	/** Quiet load: a missing asset is the normal case until the designer authors one. */
	template <typename T>
	T* LoadOptional(const TCHAR* Path)
	{
		return Cast<T>(StaticLoadObject(T::StaticClass(), nullptr, Path, nullptr, LOAD_NoWarn | LOAD_Quiet));
	}
}

UShipInputComponent::UShipInputComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UShipInputComponent::BindInput(UInputComponent* PlayerInputComponent)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	ResolveInputAssets();

	UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(PlayerInputComponent);
	if (!Input)
	{
		UE_LOG(LogSpaceship, Error,
			TEXT("%s expects an UEnhancedInputComponent. Check DefaultInputComponentClass in DefaultInput.ini."),
			*Ship->GetName());
		return;
	}

	auto BindAxis = [this, Input](UInputAction* Action, ESpaceshipAxis Axis)
	{
		if (!Action)
		{
			return;
		}
		Input->BindAction(Action, ETriggerEvent::Triggered, this, &UShipInputComponent::HandleAxisTriggered, Axis);
		// Without these the axis would stay latched at its last value after the key comes up.
		Input->BindAction(Action, ETriggerEvent::Completed, this, &UShipInputComponent::HandleAxisCompleted, Axis);
		Input->BindAction(Action, ETriggerEvent::Canceled, this, &UShipInputComponent::HandleAxisCompleted, Axis);
	};

	BindAxis(Ship->ThrustAction, ESpaceshipAxis::Thrust);
	BindAxis(Ship->StrafeAction, ESpaceshipAxis::Strafe);
	BindAxis(Ship->LiftAction, ESpaceshipAxis::Lift);
	BindAxis(Ship->RollAction, ESpaceshipAxis::Roll);

	if (Ship->LookAction)
	{
		// No Completed binding: LookInput is cleared every tick, see UpdateAngularMotion.
		Input->BindAction(Ship->LookAction, ETriggerEvent::Triggered, this, &UShipInputComponent::HandleLook);
	}

	if (Ship->MouseLookAction)
	{
		Input->BindAction(Ship->MouseLookAction, ETriggerEvent::Triggered, this, &UShipInputComponent::HandleMouseLook);
	}

	if (Ship->ToggleCameraAction)
	{
		// The action carries a Pressed trigger, so Triggered fires once per key press.
		Input->BindAction(Ship->ToggleCameraAction, ETriggerEvent::Triggered, this, &UShipInputComponent::HandleToggleCamera);
	}

	if (Ship->BoostAction)
	{
		Input->BindAction(Ship->BoostAction, ETriggerEvent::Triggered, this, &UShipInputComponent::HandleBoost);
		Input->BindAction(Ship->BoostAction, ETriggerEvent::Completed, this, &UShipInputComponent::HandleBoostCompleted);
		Input->BindAction(Ship->BoostAction, ETriggerEvent::Canceled, this, &UShipInputComponent::HandleBoostCompleted);
	}

	// F (InteractAction) is read by ASpacePlayerController: a tap does Ship->Interact(), holding it is interact mode.

	// H (HUD) and Escape (menu) are bound by ASpacePlayerController, the same in the ship and on foot.

	if (Ship->FlightAssistAction)
	{
		Input->BindAction(Ship->FlightAssistAction, ETriggerEvent::Started, this, &UShipInputComponent::HandleFlightAssist);
	}
	if (Ship->QuantumEngageAction)
	{
		Input->BindAction(Ship->QuantumEngageAction, ETriggerEvent::Started, this, &UShipInputComponent::HandleQuantumEngageStarted);
		Input->BindAction(Ship->QuantumEngageAction, ETriggerEvent::Completed, this, &UShipInputComponent::HandleQuantumEngageCompleted);
		Input->BindAction(Ship->QuantumEngageAction, ETriggerEvent::Canceled, this, &UShipInputComponent::HandleQuantumEngageCompleted);
	}
	if (Ship->AllStopAction)
	{
		Input->BindAction(Ship->AllStopAction, ETriggerEvent::Started, this, &UShipInputComponent::HandleAllStop);
		Input->BindAction(Ship->AllStopAction, ETriggerEvent::Completed, this, &UShipInputComponent::HandleAllStopCompleted);
		Input->BindAction(Ship->AllStopAction, ETriggerEvent::Canceled, this, &UShipInputComponent::HandleAllStopCompleted);
	}
	if (Ship->CameraZoomAction)
	{
		Input->BindAction(Ship->CameraZoomAction, ETriggerEvent::Triggered, this, &UShipInputComponent::HandleCameraZoom);
	}
	if (Ship->MasterModeAction)
	{
		Input->BindAction(Ship->MasterModeAction, ETriggerEvent::Started, this, &UShipInputComponent::HandleMasterMode);
	}
	if (Ship->SpeedLimiterAction)
	{
		Input->BindAction(Ship->SpeedLimiterAction, ETriggerEvent::Triggered, this, &UShipInputComponent::HandleSpeedLimiter);
	}
	if (Ship->GSafeAction)
	{
		Input->BindAction(Ship->GSafeAction, ETriggerEvent::Started, this, &UShipInputComponent::HandleGSafe);
	}
	if (Ship->ComStabAction)
	{
		Input->BindAction(Ship->ComStabAction, ETriggerEvent::Started, this, &UShipInputComponent::HandleComStab);
	}
	if (Ship->AfterburnerAction)
	{
		Input->BindAction(Ship->AfterburnerAction, ETriggerEvent::Triggered, this, &UShipInputComponent::HandleAfterburner);
		Input->BindAction(Ship->AfterburnerAction, ETriggerEvent::Completed, this, &UShipInputComponent::HandleAfterburnerCompleted);
		Input->BindAction(Ship->AfterburnerAction, ETriggerEvent::Canceled, this, &UShipInputComponent::HandleAfterburnerCompleted);
	}

	if (Ship->LandingGearAction)
	{
		Input->BindAction(Ship->LandingGearAction, ETriggerEvent::Started, this, &UShipInputComponent::HandleLandingGear);
	}
	if (Ship->PrecisionAction)
	{
		Input->BindAction(Ship->PrecisionAction, ETriggerEvent::Started, this, &UShipInputComponent::HandlePrecision);
	}
	if (Ship->VtolAction)
	{
		Input->BindAction(Ship->VtolAction, ETriggerEvent::Started, this, &UShipInputComponent::HandleVtol);
	}
	if (Ship->DashboardFocusAction)
	{
		Input->BindAction(Ship->DashboardFocusAction, ETriggerEvent::Started, this, &UShipInputComponent::HandleDashboardFocusStarted);
		Input->BindAction(Ship->DashboardFocusAction, ETriggerEvent::Completed, this, &UShipInputComponent::HandleDashboardFocusCompleted);
		Input->BindAction(Ship->DashboardFocusAction, ETriggerEvent::Canceled, this, &UShipInputComponent::HandleDashboardFocusCompleted);
	}
	if (Ship->MfdLeftAction)
	{
		Input->BindAction(Ship->MfdLeftAction, ETriggerEvent::Started, this, &UShipInputComponent::HandleMfdLeft);
	}
	if (Ship->MfdRightAction)
	{
		Input->BindAction(Ship->MfdRightAction, ETriggerEvent::Started, this, &UShipInputComponent::HandleMfdRight);
	}

	if (Ship->FreeLookAction)
	{
		Input->BindAction(Ship->FreeLookAction, ETriggerEvent::Started, this, &UShipInputComponent::HandleFreeLookStarted);
		Input->BindAction(Ship->FreeLookAction, ETriggerEvent::Completed, this, &UShipInputComponent::HandleFreeLookCompleted);
		Input->BindAction(Ship->FreeLookAction, ETriggerEvent::Canceled, this, &UShipInputComponent::HandleFreeLookCompleted);
	}

	const APlayerController* PlayerController = Cast<APlayerController>(Ship->GetController());
	if (!PlayerController)
	{
		return;
	}

	if (UEnhancedInputLocalPlayerSubsystem* Subsystem =
		ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PlayerController->GetLocalPlayer()))
	{
		if (Ship->FlightMappingContext)
		{
			Subsystem->AddMappingContext(Ship->FlightMappingContext, Ship->MappingContextPriority);
		}
		if (Ship->MouseMappingContext)
		{
			// One above the flight context: its mouse mapping consumes the mouse there.
			Subsystem->AddMappingContext(Ship->MouseMappingContext, Ship->MappingContextPriority + 1);
		}
		// The hand-authored IMC_Spaceship may predate F / right mouse button (their add_*.py
		// scripts not run yet): map whatever is missing in a small runtime context.
		auto IsMapped = [Ship](const UInputAction* Action)
		{
			return Ship->FlightMappingContext->GetMappings().ContainsByPredicate(
				[Action](const FEnhancedActionKeyMapping& Mapping) { return Mapping.Action == Action; });
		};
		if (Ship->FlightMappingContext && !InteractMappingContext)
		{
			InteractMappingContext = NewObject<UInputMappingContext>(Ship, FName(TEXT("IMC_SpaceshipExtras_Runtime")));
			if (Ship->InteractAction && !IsMapped(Ship->InteractAction))
			{
				InteractMappingContext->MapKey(Ship->InteractAction, EKeys::F);
			}
			if (Ship->FreeLookAction && !IsMapped(Ship->FreeLookAction))
			{
				InteractMappingContext->MapKey(Ship->FreeLookAction, EKeys::RightMouseButton);
			}
			if (Ship->FlightAssistAction && !IsMapped(Ship->FlightAssistAction))
			{
				InteractMappingContext->MapKey(Ship->FlightAssistAction, EKeys::V);
			}
			if (Ship->QuantumEngageAction && !IsMapped(Ship->QuantumEngageAction))
			{
				InteractMappingContext->MapKey(Ship->QuantumEngageAction, EKeys::LeftMouseButton);
			}
			if (Ship->AllStopAction && !IsMapped(Ship->AllStopAction))
			{
				InteractMappingContext->MapKey(Ship->AllStopAction, EKeys::X);
			}
			if (Ship->CameraZoomAction && !IsMapped(Ship->CameraZoomAction))
			{
				InteractMappingContext->MapKey(Ship->CameraZoomAction, EKeys::MouseWheelAxis);
			}
			if (Ship->MasterModeAction && !IsMapped(Ship->MasterModeAction))
			{
				InteractMappingContext->MapKey(Ship->MasterModeAction, EKeys::B);
			}
			if (Ship->SpeedLimiterAction && !IsMapped(Ship->SpeedLimiterAction))
			{
				InteractMappingContext->MapKey(Ship->SpeedLimiterAction, EKeys::MouseWheelAxis);
			}
			if (Ship->GSafeAction && !IsMapped(Ship->GSafeAction))
			{
				InteractMappingContext->MapKey(Ship->GSafeAction, EKeys::K);
			}
			if (Ship->ComStabAction && !IsMapped(Ship->ComStabAction))
			{
				InteractMappingContext->MapKey(Ship->ComStabAction, EKeys::L);
			}
			if (Ship->AfterburnerAction && !IsMapped(Ship->AfterburnerAction))
			{
				InteractMappingContext->MapKey(Ship->AfterburnerAction, EKeys::Tab);
			}
			if (Ship->LandingGearAction && !IsMapped(Ship->LandingGearAction))
			{
				InteractMappingContext->MapKey(Ship->LandingGearAction, EKeys::N);
			}
			if (Ship->PrecisionAction && !IsMapped(Ship->PrecisionAction))
			{
				InteractMappingContext->MapKey(Ship->PrecisionAction, EKeys::P);
			}
			if (Ship->VtolAction && !IsMapped(Ship->VtolAction))
			{
				InteractMappingContext->MapKey(Ship->VtolAction, EKeys::G);
			}
			if (Ship->DashboardFocusAction && !IsMapped(Ship->DashboardFocusAction))
			{
				InteractMappingContext->MapKey(Ship->DashboardFocusAction, EKeys::Z);
				InteractMappingContext->MapKey(Ship->DashboardFocusAction, EKeys::MiddleMouseButton);
			}
			if (Ship->MfdLeftAction && !IsMapped(Ship->MfdLeftAction))
			{
				InteractMappingContext->MapKey(Ship->MfdLeftAction, EKeys::F1);
			}
			if (Ship->MfdRightAction && !IsMapped(Ship->MfdRightAction))
			{
				InteractMappingContext->MapKey(Ship->MfdRightAction, EKeys::F2);
			}
		}
		if (InteractMappingContext && InteractMappingContext->GetMappings().Num() > 0)
		{
			Subsystem->AddMappingContext(InteractMappingContext, Ship->MappingContextPriority);
		}
	}
}

void UShipInputComponent::RemoveMappingContexts()
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	// Remove this ship's contexts while the controller is still known: the mouse context would
	// otherwise keep consuming the mouse after the pilot got out.
	if (const APlayerController* PlayerController = Cast<APlayerController>(Ship->GetController()))
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem =
			ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PlayerController->GetLocalPlayer()))
		{
			for (UInputMappingContext* Context : { Ship->FlightMappingContext.Get(), Ship->MouseMappingContext.Get(), InteractMappingContext.Get() })
			{
				if (Context)
				{
					Subsystem->RemoveMappingContext(Context);
				}
			}
		}
	}
}

void UShipInputComponent::ResolveInputAssets()
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	using namespace ShipInputDefaults;

	// Anything the designer assigned on the Blueprint wins; then authored assets in /Game/Input.
	if (!Ship->FlightMappingContext)
	{
		Ship->FlightMappingContext = LoadOptional<UInputMappingContext>(MappingContextPath);
	}
	if (!Ship->ThrustAction)
	{
		Ship->ThrustAction = LoadOptional<UInputAction>(ThrustActionPath);
	}
	if (!Ship->StrafeAction)
	{
		Ship->StrafeAction = LoadOptional<UInputAction>(StrafeActionPath);
	}
	if (!Ship->LiftAction)
	{
		Ship->LiftAction = LoadOptional<UInputAction>(LiftActionPath);
	}
	if (!Ship->RollAction)
	{
		Ship->RollAction = LoadOptional<UInputAction>(RollActionPath);
	}
	if (!Ship->LookAction)
	{
		Ship->LookAction = LoadOptional<UInputAction>(LookActionPath);
	}
	if (!Ship->ToggleCameraAction)
	{
		Ship->ToggleCameraAction = LoadOptional<UInputAction>(ToggleCameraActionPath);
	}
	if (!Ship->BoostAction)
	{
		Ship->BoostAction = LoadOptional<UInputAction>(BoostActionPath);
	}
	if (!Ship->InteractAction)
	{
		Ship->InteractAction = LoadOptional<UInputAction>(InteractActionPath);
	}
	if (!Ship->FreeLookAction)
	{
		Ship->FreeLookAction = LoadOptional<UInputAction>(FreeLookActionPath);
	}
	if (!Ship->MouseLookAction)
	{
		Ship->MouseLookAction = LoadOptional<UInputAction>(MouseLookActionPath);
	}
	if (!Ship->MouseMappingContext)
	{
		Ship->MouseMappingContext = LoadOptional<UInputMappingContext>(MouseMappingContextPath);
	}

	// Newer actions: authored assets once Tools/Assets/add_flight_modes_input.py has run, otherwise
	// runtime stand-ins, mapped through the extras context in BindInput.
	auto LoadOrMake = [Ship](TObjectPtr<UInputAction>& Action, const TCHAR* Path, const TCHAR* RuntimeName, EInputActionValueType ValueType)
	{
		if (!Action)
		{
			Action = LoadOptional<UInputAction>(Path);
		}
		if (!Action)
		{
			Action = NewObject<UInputAction>(Ship, FName(RuntimeName));
			Action->ValueType = ValueType;
		}
	};
	LoadOrMake(Ship->FlightAssistAction, FlightAssistActionPath, TEXT("IA_FlightAssist_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(Ship->QuantumEngageAction, QuantumEngageActionPath, TEXT("IA_QuantumEngage_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(Ship->AllStopAction, AllStopActionPath, TEXT("IA_AllStop_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(Ship->CameraZoomAction, CameraZoomActionPath, TEXT("IA_CameraZoom_Runtime"), EInputActionValueType::Axis1D);
	LoadOrMake(Ship->MasterModeAction, MasterModeActionPath, TEXT("IA_MasterMode_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(Ship->SpeedLimiterAction, SpeedLimiterActionPath, TEXT("IA_SpeedLimiter_Runtime"), EInputActionValueType::Axis1D);
	LoadOrMake(Ship->GSafeAction, GSafeActionPath, TEXT("IA_GSafe_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(Ship->ComStabAction, ComStabActionPath, TEXT("IA_ComStab_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(Ship->AfterburnerAction, AfterburnerActionPath, TEXT("IA_Afterburner_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(Ship->LandingGearAction, LandingGearActionPath, TEXT("IA_LandingGear_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(Ship->PrecisionAction, PrecisionActionPath, TEXT("IA_Precision_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(Ship->VtolAction, VtolActionPath, TEXT("IA_Vtol_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(Ship->DashboardFocusAction, DashboardFocusActionPath, TEXT("IA_DashboardFocus_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(Ship->MfdLeftAction, MfdLeftActionPath, TEXT("IA_MfdLeft_Runtime"), EInputActionValueType::Boolean);
	LoadOrMake(Ship->MfdRightAction, MfdRightActionPath, TEXT("IA_MfdRight_Runtime"), EInputActionValueType::Boolean);

	BuildProceduralInputAssets();
}

void UShipInputComponent::BuildProceduralInputAssets()
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	const bool bNeedsAnything = !Ship->FlightMappingContext || !Ship->ThrustAction || !Ship->StrafeAction || !Ship->LiftAction
		|| !Ship->RollAction || !Ship->LookAction || !Ship->ToggleCameraAction || !Ship->BoostAction || !Ship->MouseLookAction
		|| !Ship->MouseMappingContext || !Ship->InteractAction || !Ship->FreeLookAction;
	if (!bNeedsAnything)
	{
		return;
	}

	UE_LOG(LogSpaceship, Warning,
		TEXT("%s is falling back to procedurally built Enhanced Input objects. Author IMC_Spaceship and the ")
		TEXT("IA_* actions in /Game/Input (or assign them on a Blueprint child) to make the bindings editable."),
		*Ship->GetName());

	auto MakeAction = [Ship](const TCHAR* Name, EInputActionValueType ValueType,
		EInputActionAccumulationBehavior Accumulation) -> UInputAction*
	{
		UInputAction* Action = NewObject<UInputAction>(Ship, FName(Name));
		Action->ValueType = ValueType;
		Action->AccumulationBehavior = Accumulation;
		return Action;
	};

	// Opposing keys on one axis (W and S) have to cancel, which is what Cumulative does.
	// The default, TakeHighestAbsoluteValue, would pick one of +1 and -1 arbitrarily.
	const EInputActionAccumulationBehavior Opposed = EInputActionAccumulationBehavior::Cumulative;

	if (!Ship->ThrustAction)
	{
		Ship->ThrustAction = MakeAction(TEXT("IA_Thrust_Runtime"), EInputActionValueType::Axis1D, Opposed);
	}
	if (!Ship->StrafeAction)
	{
		Ship->StrafeAction = MakeAction(TEXT("IA_Strafe_Runtime"), EInputActionValueType::Axis1D, Opposed);
	}
	if (!Ship->LiftAction)
	{
		Ship->LiftAction = MakeAction(TEXT("IA_Lift_Runtime"), EInputActionValueType::Axis1D, Opposed);
	}
	if (!Ship->RollAction)
	{
		Ship->RollAction = MakeAction(TEXT("IA_Roll_Runtime"), EInputActionValueType::Axis1D, Opposed);
	}
	if (!Ship->LookAction)
	{
		// Mouse and stick feed the same action, so here the larger of the two should win.
		Ship->LookAction = MakeAction(TEXT("IA_Look_Runtime"), EInputActionValueType::Axis2D,
			EInputActionAccumulationBehavior::TakeHighestAbsoluteValue);
	}
	if (!Ship->ToggleCameraAction)
	{
		Ship->ToggleCameraAction = MakeAction(TEXT("IA_ToggleCamera_Runtime"), EInputActionValueType::Boolean,
			EInputActionAccumulationBehavior::TakeHighestAbsoluteValue);
		Ship->ToggleCameraAction->Triggers.Add(NewObject<UInputTriggerPressed>(Ship->ToggleCameraAction));
	}
	if (!Ship->BoostAction)
	{
		Ship->BoostAction = MakeAction(TEXT("IA_Boost_Runtime"), EInputActionValueType::Boolean,
			EInputActionAccumulationBehavior::TakeHighestAbsoluteValue);
	}
	if (!Ship->InteractAction)
	{
		Ship->InteractAction = MakeAction(TEXT("IA_Interact_Runtime"), EInputActionValueType::Boolean,
			EInputActionAccumulationBehavior::TakeHighestAbsoluteValue);
		Ship->InteractAction->Triggers.Add(NewObject<UInputTriggerPressed>(Ship->InteractAction));
	}
	if (!Ship->FreeLookAction)
	{
		Ship->FreeLookAction = MakeAction(TEXT("IA_FreeLook_Runtime"), EInputActionValueType::Boolean,
			EInputActionAccumulationBehavior::TakeHighestAbsoluteValue);
	}
	if (!Ship->MouseLookAction)
	{
		Ship->MouseLookAction = MakeAction(TEXT("IA_LookMouse_Runtime"), EInputActionValueType::Axis2D,
			EInputActionAccumulationBehavior::TakeHighestAbsoluteValue);
	}
	if (!Ship->MouseMappingContext)
	{
		Ship->MouseMappingContext = NewObject<UInputMappingContext>(Ship, FName(TEXT("IMC_SpaceshipMouse_Runtime")));
		Ship->MouseMappingContext->MapKey(Ship->MouseLookAction, EKeys::Mouse2D);
	}

	// A context the designer supplied is left alone even if it is missing mappings: silently
	// bolting extra keys onto an authored asset would be worse than a context that does nothing.
	if (Ship->FlightMappingContext)
	{
		return;
	}

	Ship->FlightMappingContext = NewObject<UInputMappingContext>(Ship, FName(TEXT("IMC_Spaceship_Runtime")));

	struct FDefaultMapping
	{
		const UInputAction* Action;
		FKey Key;
		bool bNegate;
	};

	const FDefaultMapping DefaultMappings[] = {
		{ Ship->ThrustAction, EKeys::W,                     false },
		{ Ship->ThrustAction, EKeys::S,                     true  },
		{ Ship->ThrustAction, EKeys::Gamepad_LeftY,         false },
		{ Ship->StrafeAction, EKeys::D,                     false },
		{ Ship->StrafeAction, EKeys::A,                     true  },
		{ Ship->StrafeAction, EKeys::Gamepad_LeftX,         false },
		{ Ship->LiftAction,   EKeys::SpaceBar,              false },
		{ Ship->LiftAction,   EKeys::LeftControl,           true  },
		{ Ship->RollAction,   EKeys::E,                     false },
		{ Ship->RollAction,   EKeys::Q,                     true  },
		{ Ship->RollAction,   EKeys::Gamepad_RightShoulder, false },
		{ Ship->RollAction,   EKeys::Gamepad_LeftShoulder,  true  },
		// The mouse is mapped in MouseMappingContext, not here.
		{ Ship->LookAction,   EKeys::Gamepad_Right2D,       false },
		{ Ship->ToggleCameraAction, EKeys::C,               false },
		{ Ship->BoostAction,  EKeys::LeftShift,             false },
		{ Ship->InteractAction, EKeys::F,                   false },
		{ Ship->FreeLookAction, EKeys::RightMouseButton,    false },
	};

	for (const FDefaultMapping& Mapping : DefaultMappings)
	{
		FEnhancedActionKeyMapping& KeyMapping = Ship->FlightMappingContext->MapKey(Mapping.Action, Mapping.Key);
		if (Mapping.bNegate)
		{
			KeyMapping.Modifiers.Add(NewObject<UInputModifierNegate>(Ship->FlightMappingContext));
		}
	}
}

void UShipInputComponent::HandleAxisTriggered(const FInputActionValue& Value, ESpaceshipAxis Axis)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->AxisInput(Axis) = Value.Get<float>();
}

void UShipInputComponent::HandleAxisCompleted(const FInputActionValue& /*Value*/, ESpaceshipAxis Axis)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->AxisInput(Axis) = 0.f;
}

void UShipInputComponent::HandleLook(const FInputActionValue& Value)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->LookInput = Value.Get<FVector2D>();
}

void UShipInputComponent::HandleMouseLook(const FInputActionValue& Value)
{
	// (in interact mode the ship holds free look: the mouse turns the head - SpacePlayerController::SetInteractMode)
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	// Accumulated: every pixel moved between two ticks counts, however events are batched.
	Ship->MouseLookDelta += Value.Get<FVector2D>();
}

void UShipInputComponent::HandleToggleCamera(const FInputActionValue& /*Value*/)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->SetCockpitView(!Ship->bCockpitView);
}

void UShipInputComponent::HandleBoost(const FInputActionValue& /*Value*/)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->Systems->SetBoostHeld(true);
}

void UShipInputComponent::HandleInteract(const FInputActionValue& /*Value*/)
{
	CastChecked<ASpaceshipPawn>(GetOwner())->Interact();
}

void UShipInputComponent::HandleFlightAssist(const FInputActionValue& /*Value*/)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->SetFlightAssist(!Ship->bFlightAssist);
}

void UShipInputComponent::HandleQuantumEngageStarted(const FInputActionValue& /*Value*/)
{
	if (ASpacePlayerController::IsInteractModeFor(CastChecked<APawn>(GetOwner())))
	{
		return;  // the left button clicks hotspots in interact mode
	}
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->SetQuantumEngageHeld(true);
}

void UShipInputComponent::HandleQuantumEngageCompleted(const FInputActionValue& /*Value*/)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->SetQuantumEngageHeld(false);
}

void UShipInputComponent::HandleAllStop(const FInputActionValue& /*Value*/)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->SetSpaceBrake(true);
}

void UShipInputComponent::HandleAllStopCompleted(const FInputActionValue& /*Value*/)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->SetSpaceBrake(false);
}

void UShipInputComponent::HandleMasterMode(const FInputActionValue& /*Value*/)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->ToggleMasterMode();
}

void UShipInputComponent::HandleSpeedLimiter(const FInputActionValue& Value)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	// The wheel is mapped to both the limiter and the zoom; Alt picks the zoom.
	if (!IsAltHeld())
	{
		Ship->AdjustSpeedLimiter(Value.Get<float>());
	}
}

void UShipInputComponent::HandleGSafe(const FInputActionValue& /*Value*/)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->SetGSafe(!Ship->bGSafe);
}

void UShipInputComponent::HandleAfterburner(const FInputActionValue& /*Value*/)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->Systems->SetAfterburnerHeld(true);
}

void UShipInputComponent::HandleAfterburnerCompleted(const FInputActionValue& /*Value*/)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->Systems->SetAfterburnerHeld(false);
}

void UShipInputComponent::HandleComStab(const FInputActionValue& /*Value*/)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->SetComStab(!Ship->bComStab);
}

void UShipInputComponent::HandleLandingGear(const FInputActionValue& /*Value*/)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->ToggleGear();
}

void UShipInputComponent::HandleMfdLeft(const FInputActionValue& /*Value*/)
{
	CycleMfdPage(0);
}

void UShipInputComponent::HandleMfdRight(const FInputActionValue& /*Value*/)
{
	CycleMfdPage(1);
}

void UShipInputComponent::HandlePrecision(const FInputActionValue& /*Value*/)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->TogglePrecisionMode();
}

void UShipInputComponent::HandleCameraZoom(const FInputActionValue& Value)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	if (!IsAltHeld())
	{
		return;  // the plain wheel is the speed limiter
	}
	// One wheel notch is +-1. Up (positive) brings the camera closer / zooms the cockpit in.
	const float Notches = Value.Get<float>();
	if (Ship->bCockpitView)
	{
		Ship->CockpitZoomTarget = FMath::Clamp(Ship->CockpitZoomTarget + 0.2f * Notches, 0.f, 1.f);
	}
	else
	{
		Ship->CameraZoomTarget = FMath::Clamp(Ship->CameraZoomTarget * FMath::Pow(1.f - Ship->CameraZoomStep, Notches), Ship->CameraZoomMin, Ship->CameraZoomMax);
	}
}

void UShipInputComponent::HandleFreeLookStarted(const FInputActionValue& /*Value*/)
{
	if (ASpacePlayerController::IsInteractModeFor(CastChecked<APawn>(GetOwner())))
	{
		return;  // the right button goes back on a display in interact mode
	}
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->SetFreeLookHeld(true);
}

void UShipInputComponent::HandleFreeLookCompleted(const FInputActionValue& /*Value*/)
{
	if (ASpacePlayerController::IsInteractModeFor(CastChecked<APawn>(GetOwner())))
	{
		return;  // the right button was a click on a display; interact mode keeps the free look
	}
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->SetFreeLookHeld(false);
}

void UShipInputComponent::HandleDashboardFocusStarted(const FInputActionValue& /*Value*/)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->SetDashboardFocus(true);
}

void UShipInputComponent::HandleDashboardFocusCompleted(const FInputActionValue& /*Value*/)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->SetDashboardFocus(false);
}

void UShipInputComponent::HandleBoostCompleted(const FInputActionValue& /*Value*/)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->Systems->SetBoostHeld(false);
}

void UShipInputComponent::HandleVtol(const FInputActionValue& Value)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	Ship->ToggleVtol();
}

void UShipInputComponent::CycleMfdPage(int32 Display)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	// Alt goes back: Shift would be the boost as well.
	const APlayerController* PlayerController = Cast<APlayerController>(Ship->GetController());
	const bool bBack = PlayerController && (PlayerController->IsInputKeyDown(EKeys::LeftAlt) || PlayerController->IsInputKeyDown(EKeys::RightAlt));
	if (Ship->CockpitDisplays)
	{
		Ship->CockpitDisplays->CyclePage(Display, bBack ? -1 : 1);
	}
}

bool UShipInputComponent::IsAltHeld() const
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	const APlayerController* PlayerController = Cast<APlayerController>(Ship->GetController());
	return PlayerController && (PlayerController->IsInputKeyDown(EKeys::LeftAlt) || PlayerController->IsInputKeyDown(EKeys::RightAlt));
}
