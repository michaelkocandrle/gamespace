// Copyright Epic Games, Inc. All Rights Reserved.

#include "ShipPresentationComponent.h"

#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/AudioComponent.h"
#include "Components/BoxComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/LocalLightComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/SkyLight.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialParameterCollection.h"
#include "Sound/SoundBase.h"
#include "SpaceDustComponent.h"
#include "SpaceHullSparksComponent.h"
#include "SpacePlayerController.h"
#include "SpaceSpeedTunnelComponent.h"
#include "SpaceUserSettings.h"
#include "SpaceshipPawn.h"

namespace ShipPresentationDefaults
{
	const TCHAR* const EngineHumSoundPath = TEXT("/Game/Ships/Audio/SW_EngineHum.SW_EngineHum");
	const TCHAR* const BoostLoopSoundPath = TEXT("/Game/Ships/Audio/SW_BoostLoop.SW_BoostLoop");
	const TCHAR* const CruiseLoopSoundPath = TEXT("/Game/Ships/Audio/SW_CruiseLoop.SW_CruiseLoop");
	const TCHAR* const BoostStartSoundPath = TEXT("/Game/Ships/Audio/SW_BoostStart.SW_BoostStart");
	const TCHAR* const CruiseChargeSoundPath = TEXT("/Game/Ships/Audio/SW_CruiseCharge.SW_CruiseCharge");
	const TCHAR* const CruiseEngageSoundPath = TEXT("/Game/Ships/Audio/SW_CruiseEngage.SW_CruiseEngage");
	const TCHAR* const CruiseDropSoundPath = TEXT("/Game/Ships/Audio/SW_CruiseDrop.SW_CruiseDrop");
	const TCHAR* const TouchdownSoundPath = TEXT("/Game/Ships/Audio/SW_Touchdown.SW_Touchdown");

	/** The material parameter the ship animates on thruster and strobe slots (M_Ship_Hull). */
	const FName EmissiveStrengthParameter(TEXT("EmissiveStrength"));

	/** Quiet load: a missing asset is the normal case until the designer authors one. */
	template <typename T>
	T* LoadOptional(const TCHAR* Path)
	{
		return Cast<T>(StaticLoadObject(T::StaticClass(), nullptr, Path, nullptr, LOAD_NoWarn | LOAD_Quiet));
	}
}

UShipPresentationComponent::UShipPresentationComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UShipPresentationComponent::LoadViewCollection()
{
	// Cooked with the glass material that reads it (ship_materials.py builds both).
	ViewCollection = LoadObject<UMaterialParameterCollection>(nullptr, TEXT("/Game/Ships/Shared/Materials/MPC_ShipView.MPC_ShipView"));
}

void UShipPresentationComponent::FindLevelLights()
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	for (TActorIterator<ADirectionalLight> It(Ship->GetWorld()); It; ++It)
	{
		if (UDirectionalLightComponent* Light = Cast<UDirectionalLightComponent>(It->GetLightComponent()))
		{
			QuantumSun = Light;
			break;
		}
	}
	for (TActorIterator<ASkyLight> It(Ship->GetWorld()); It; ++It)
	{
		QuantumSky = It->GetLightComponent();
		break;
	}
}

void UShipPresentationComponent::UpdateCameraEffects(float DeltaSeconds)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	BoostBlend = FMath::FInterpTo(BoostBlend, Ship->Systems->IsBoostActive() ? 1.f : 0.f, DeltaSeconds, 4.f);
	// Asymmetric on purpose: the punch arrives at once, the view settles back slowly. Symmetric easing
	// made lighting the afterburner feel soft, which is most of what "no kick" was about.
	AfterburnerFeel = FMath::FInterpTo(AfterburnerFeel, Ship->Systems->IsAfterburnerActive() ? 1.f : 0.f, DeltaSeconds,
		Ship->Systems->IsAfterburnerActive() ? 9.f : 2.5f);
	// The quantum look arrives in about a second and leaves faster; the last 5% of a jump fades it out.
	// The jump's look follows its speed, so it builds up with the acceleration ramp instead of snapping
	// on (the author, 22. 9. 2026); the last 5 % of the jump fades it out again.
	const float SpeedShare = float(Ship->LinearVelocity.Size() / FMath::Max(double(Ship->QuantumMaxSpeedKmS) * 100000.0 * Ship->QuantumLookFullSpeedShare, 1.0));
	const float QuantumTarget01 = Ship->Quantum->GetState() == EQuantumState::Traveling
		? FMath::SmoothStep(0.f, 1.f, FMath::Clamp(SpeedShare, 0.f, 1.f)) * FMath::Clamp((1.f - Ship->GetQuantumTravelProgress()) / 0.05f, 0.f, 1.f) : 0.f;
	QuantumBlend = FMath::FInterpTo(QuantumBlend, QuantumTarget01, DeltaSeconds, QuantumTarget01 > QuantumBlend ? 4.f : 4.f);
	CameraKick *= FMath::Exp(-5.f * DeltaSeconds);
	// No camera lag in a quantum jump: even capped at 15 m it trails along the flight path, and
	// looked at from the side (free look) that pushed the ship out of the frame (21. 9. 2026).
	// The lag is not switched off any more, it is wound up: at the moment it went off, the boom
	// snapped to its exact place and the ship jumped across the screen (the author, 22. 9. 2026).
	// Switched off rather than capped at 0 would not do either: a CameraLagMaxDistance of 0 means no
	// cap at all, and the camera was left kilometres behind.
	if (Ship->CameraSnapTicks == 0)
	{
		const float Catching = FMath::Max(Ship->Quantum->GetState() == EQuantumState::Traveling ? 1.f : 0.f, QuantumBlend);
		Ship->CameraBoom->bEnableCameraLag = true;
		Ship->CameraBoom->CameraLagSpeed = FMath::Lerp(Ship->BaseCameraLagSpeed, Ship->QuantumCameraLagSpeed, FMath::SmoothStep(0.f, 1.f, Catching));
	}

	// Mouse wheel zoom, eased.
	Ship->CameraZoom = FMath::FInterpTo(Ship->CameraZoom, Ship->CameraZoomTarget, DeltaSeconds, 8.f);
	Ship->CockpitZoom = FMath::FInterpTo(Ship->CockpitZoom, Ship->CockpitZoomTarget, DeltaSeconds, 8.f);
	if (Ship->BaseArmLength > 0.f)
	{
		Ship->CameraBoom->TargetArmLength = Ship->BaseArmLength * Ship->CameraZoom;
		// The height above the ship grows slower than the distance, so a far camera does not end
		// up looking steeply down on it.
		Ship->CameraBoom->SocketOffset = Ship->BaseSocketOffset * FMath::Sqrt(Ship->CameraZoom);
	}

	// A jump is dark: the tunnel is nearly black with a bright point ahead, and letting the eye
	// adapt to it washed the whole frame out to a flat navy blue (the author against the reference,
	// 22. 9. 2026). So the exposure is pinned while the jump lasts.
	for (UCameraComponent* Camera : { ToRawPtr(Ship->ChaseCamera), ToRawPtr(Ship->CockpitCamera) })
	{
		FPostProcessSettings& Post = Camera->PostProcessSettings;
		Post.bOverride_AutoExposureMinBrightness = QuantumBlend > 0.001f;
		Post.bOverride_AutoExposureMaxBrightness = QuantumBlend > 0.001f;
		const float OwnBias = Camera == Ship->CockpitCamera ? Ship->CockpitExposureBias : 0.f;
		Post.bOverride_AutoExposureBias = QuantumBlend > 0.001f || OwnBias != 0.f;
		const float Pinned = FMath::Lerp(0.f, Ship->QuantumExposure, QuantumBlend);
		Post.AutoExposureMinBrightness = FMath::Max(Pinned, 0.03f);
		Post.AutoExposureMaxBrightness = FMath::Max(Pinned, 0.03f);
		Post.AutoExposureBias = FMath::Lerp(OwnBias, Ship->QuantumExposureBias, QuantumBlend);
	}

	// Speed you can feel: the view widens with the afterburner and more in a quantum jump.
	const float FovKick = Ship->AfterburnerFovKick * AfterburnerFeel + Ship->QuantumFovKick * QuantumBlend;
	Ship->ChaseCamera->SetFieldOfView(Ship->BaseChaseFov + FovKick);
	const float CockpitFov = FMath::Lerp(Ship->BaseCockpitFov, Ship->CockpitZoomFov, Ship->CockpitZoom) + 0.6f * FovKick * (1.f - Ship->CockpitZoom);
	Ship->CockpitCamera->SetFieldOfView(FMath::Lerp(CockpitFov, Ship->DashboardFocusFov, Ship->DashboardFocusBlend));

	// Smooth noise rather than random jumps: a rumble, not a flicker. Nothing moves when calm.
	static const IConsoleVariable* ShakeScale = IConsoleManager::Get().RegisterConsoleVariable(TEXT("space.CameraShake"), 1.f,
		TEXT("Camera shake multiplier (boost, afterburner, quantum, heat, kicks); 0 = none."), ECVF_Default);
	const float Spool = Ship->Quantum->GetState() == EQuantumState::Ready ? Ship->GetQuantumEngageHold() : 0.f;
	const float Amplitude = ShakeScale->GetFloat() * USpaceUserSettings::GetCameraShakeScale() * (Ship->HeatShakeCm * Ship->Heat * Ship->Heat + Ship->BoostShakeCm * BoostBlend + Ship->AfterburnerShakeCm * AfterburnerFeel
		+ Ship->QuantumShakeCm * (Spool * Spool + 0.25f * QuantumBlend) + Ship->KickShakeCm * CameraKick);
	const double Time = Ship->GetWorld()->GetTimeSeconds();
	const FVector Shake = Amplitude < 0.01f
		? FVector::ZeroVector
		: FVector(
			FMath::PerlinNoise1D(float(Time * 11.0 + 3.7)),
			FMath::PerlinNoise1D(float(Time * 12.4 + 17.1)),
			FMath::PerlinNoise1D(float(Time * 10.0 + 41.9))) * Amplitude;
	Ship->ChaseCamera->SetRelativeLocation(Ship->ChaseCameraBaseLocation + Shake);
	// Dashboard focus leans the head in; the shake stays, a little, on the way.
	Ship->CockpitCamera->SetRelativeLocation(FMath::Lerp(Ship->CockpitCameraBaseLocation, Ship->DashboardFocusEye, Ship->DashboardFocusBlend) + Shake * 0.25 * (1.f - 0.6f * Ship->DashboardFocusBlend));
}

void UShipPresentationComponent::SetupAudioLayers()
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	using namespace ShipPresentationDefaults;
	auto Load = [](TObjectPtr<USoundBase>& Sound, const TCHAR* Path)
	{
		if (!Sound)
		{
			Sound = LoadOptional<USoundBase>(Path);
		}
	};
	Load(Ship->EngineHumSound, EngineHumSoundPath);
	Load(Ship->BoostLoopSound, BoostLoopSoundPath);
	Load(Ship->QuantumLoopSound, CruiseLoopSoundPath);
	Load(Ship->BoostStartSound, BoostStartSoundPath);
	Load(Ship->QuantumChargeSound, CruiseChargeSoundPath);
	Load(Ship->QuantumEngageSound, CruiseEngageSoundPath);
	Load(Ship->QuantumExitSound, CruiseDropSoundPath);
	Load(Ship->TouchdownSound, TouchdownSoundPath);

	// Created at runtime rather than as default subobjects: nothing to configure per ship, and
	// Blueprints made before these layers existed need no changes.
	auto MakeLayer = [Ship](USoundBase* Sound, const TCHAR* Name) -> UAudioComponent*
	{
		if (!Sound)
		{
			return nullptr;
		}
		UAudioComponent* Layer = NewObject<UAudioComponent>(Ship, FName(Name));
		Layer->SetupAttachment(Ship->HullCollision);
		Layer->bAutoActivate = false;
		Layer->bAllowSpatialization = false;
		Layer->SetSound(Sound);
		Layer->RegisterComponent();
		return Layer;
	};
	EngineHumAudio = MakeLayer(Ship->EngineHumSound, TEXT("EngineHumAudio"));
	BoostAudio = MakeLayer(Ship->BoostLoopSound, TEXT("BoostAudio"));
	QuantumAudio = MakeLayer(Ship->QuantumLoopSound, TEXT("QuantumAudio"));
}

void UShipPresentationComponent::UpdateEngineAudio(float DeltaSeconds)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	// Powered off the engines and the cockpit's hum are silent; they spool up with the start-up.
	const bool bPiloted = Ship->IsPlayerControlled() && Ship->GetPowerState() != ESpacePowerState::Off;

	// Eased rather than snapped, so the engines spool up and down instead of clicking. The load is
	// what the thrusters really do: braking and holding altitude are heard too, a steady coast
	// through empty space is quiet.
	// Coupled, the engines also drone with speed (in a quantum jump: a steady drone), so steady flight is
	// never silent.
	const float LeverLoad = Ship->Quantum->GetState() == EQuantumState::Traveling ? 0.35f
		: Ship->bFlightAssist ? 0.35f * FMath::Clamp(float(Ship->LinearVelocity.Size()) / FMath::Max(Ship->GetModeMaxSpeed(), 1.f), 0.f, 1.f) : 0.f;
	// (the engines are their own switch since 5. 10. 2026: their load and roar follow their spool)
	const float Spool = Ship->GetEngineSpoolAlpha();
	EngineLoad = FMath::FInterpTo(EngineLoad, bPiloted ? Spool * FMath::Max(Ship->EngineDemand, FMath::Max(LeverLoad, 0.12f * Spool)) : 0.f, DeltaSeconds, Ship->EngineSpoolRate);
	EngineBoostBlend = FMath::FInterpTo(EngineBoostBlend, bPiloted && Ship->Systems->IsAfterburnerActive() ? 1.f : 0.f, DeltaSeconds, Ship->EngineSpoolRate);
	HumBlend = FMath::FInterpTo(HumBlend, bPiloted ? 1.f : 0.f, DeltaSeconds, 1.5f);

	const float Effects = USpaceUserSettings::GetEffectsVolume();
	auto Drive = [Effects](UAudioComponent* Layer, float Volume, float Pitch)
	{
		Volume *= Effects;
		if (!Layer || !Layer->GetSound())
		{
			return;
		}
		// Below this the layer is inaudible anyway; stopping it frees the voice.
		if (Volume < 0.004f)
		{
			if (Layer->IsPlaying())
			{
				Layer->Stop();
			}
			return;
		}
		if (!Layer->IsPlaying())
		{
			Layer->Play();
		}
		Layer->SetVolumeMultiplier(Volume);
		Layer->SetPitchMultiplier(Pitch);
	};

	Drive(EngineHumAudio, Ship->EngineHumVolume * HumBlend * (0.85f + 0.3f * EngineLoad), 1.f + 0.04f * EngineLoad + 0.06f * QuantumBlend);

	const float Load = FMath::Min(EngineLoad + 0.35f * EngineBoostBlend, 1.f);
	Drive(Ship->EngineAudio, Ship->EngineVolume * Load,
		FMath::Lerp(Ship->EngineMinPitch, Ship->EngineMaxPitch, EngineLoad) + Ship->EngineBoostPitch * EngineBoostBlend);
	// Interpolated in log space, which is how cutoff frequencies are heard.
	Ship->EngineAudio->SetLowPassFilterFrequency(FMath::Exp(FMath::Lerp(
		FMath::Loge(Ship->EngineLowPassIdleHz), FMath::Loge(Ship->EngineLowPassFullHz), Load)));

	Drive(BoostAudio, bPiloted ? Ship->BoostVolume * AfterburnerFeel : 0.f, 1.f + 0.06f * AfterburnerFeel);
	const float QuantumSpeed = FMath::Clamp(float(Ship->LinearVelocity.Size() / (double(Ship->QuantumMaxSpeedKmS) * 100000.0)), 0.f, 1.f);
	Drive(QuantumAudio, bPiloted ? Ship->QuantumVolume * QuantumBlend : 0.f, 0.9f + 0.25f * FMath::Sqrt(QuantumSpeed));
}

void UShipPresentationComponent::SetupShipLights()
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	ThrusterMaterials.Reset();
	StrobeMaterials.Reset();
	if (!Ship->Hull->GetStaticMesh())
	{
		return;
	}
	// By slot name, as named in Blender: M_Ship_<Ship>_Emissive for thrusters, _NavWhite strobes.
	const TArray<FName> Slots = Ship->Hull->GetMaterialSlotNames();
	for (int32 Index = 0; Index < Slots.Num(); ++Index)
	{
		const FString Name = Slots[Index].ToString();
		const bool bThruster = Name.Contains(TEXT("Emissive")) || Name.Contains(TEXT("Thruster"));
		const bool bStrobe = Name.Contains(TEXT("NavWhite")) || Name.Contains(TEXT("Strobe"));
		if (!bThruster && !bStrobe)
		{
			continue;
		}
		UMaterialInstanceDynamic* Material = Ship->Hull->CreateDynamicMaterialInstance(Index);
		const float Base = Material ? Material->K2_GetScalarParameterValue(ShipPresentationDefaults::EmissiveStrengthParameter) : 0.f;
		if (Base <= 0.f)
		{
			continue;  // not an M_Ship_Hull glow material; nothing to animate
		}
		FShipGlowMaterial Glow;
		Glow.Material = Material;
		Glow.BaseStrength = Base;
		(bThruster ? ThrusterMaterials : StrobeMaterials).Add(Glow);
	}
}

void UShipPresentationComponent::ApplyPowerGlow(bool bLit)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	bPowerGlowLit = bLit;
	TArray<UStaticMeshComponent*> Meshes;
	Ship->GetComponents<UStaticMeshComponent>(Meshes);
	if (!bPowerGlowGathered)
	{
		// The materials space.IntEmissive scales: the interior's lamps, glow strips and accents...
		bPowerGlowGathered = true;
		for (UStaticMeshComponent* Mesh : Meshes)
		{
			for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
			{
				UMaterialInterface* Material = Mesh->GetMaterial(Slot);
				UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Material);
				UMaterialInterface* Source = Dynamic ? Dynamic->Parent.Get() : Material;
				const FString Name = Source ? Source->GetName() : FString();
				float Base = 0.f;
				// ...the interior kit's glow materials (MI_Kit_<Maker>_Glow*), and the hull's lamps and light strips (MI_Ship_<Ship>_Light*, _PosWhite; the strobes and thrusters
				// follow the power in UpdateShipLights): their orange strips along the cockpit sill lit a dead ship.
				const bool bHullLamp = Name.Contains(TEXT("_Light")) || Name.Contains(TEXT("_PosWhite"));
				if (!(Name.Contains(TEXT("IntLight")) || Name.Contains(TEXT("IntGlow")) || Name.Contains(TEXT("IntAccentGlow")) || Name.Contains(TEXT("_Glow")) || bHullLamp)
					|| !Source->GetScalarParameterValue(TEXT("EmissiveStrength"), Base))
				{
					continue;
				}
				if (!Dynamic)
				{
					Dynamic = Mesh->CreateDynamicMaterialInstance(Slot, Source);
				}
				PowerGlowMaterials.Add({ Dynamic, Base });
			}
		}
	}
	// Powered off a faint remnant stays (SC's dark cockpit still shows its fittings by the hangar's light).
	for (const TPair<TWeakObjectPtr<UMaterialInstanceDynamic>, float>& Glow : PowerGlowMaterials)
	{
		if (UMaterialInstanceDynamic* Dynamic = Glow.Key.Get())
		{
			Dynamic->SetScalarParameterValue(TEXT("EmissiveStrength"), Glow.Value * (bLit ? 1.f : 0.03f));
		}
	}
	for (UStaticMeshComponent* Mesh : Meshes)
	{
		if (Mesh->GetName().StartsWith(TEXT("Hologram")))
		{
			Mesh->SetVisibility(bLit);
		}
	}
}

void UShipPresentationComponent::UpdateShipLights(float DeltaSeconds)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	auto Apply = [](FShipGlowMaterial& Glow, float Strength)
	{
		UMaterialInstanceDynamic* Material = Glow.Material.Get();
		// Only on a visible change: every parameter set re-uploads the material's uniforms.
		if (Material && FMath::Abs(Strength - Glow.Applied) > 0.01f * FMath::Max(Glow.BaseStrength, 1.f))
		{
			Material->SetScalarParameterValue(ShipPresentationDefaults::EmissiveStrengthParameter, Strength);
			Glow.Applied = Strength;
		}
	};

	// The jump runs on a pinned, dark exposure, and at full glow the engines read as four headlights
	// instead of the soft blue of the reference (the author, 22. 9. 2026).
	const float Thrust = (Ship->ThrusterIdleGlow + (1.f - Ship->ThrusterIdleGlow) * EngineLoad + Ship->ThrusterAfterburnerGlow * AfterburnerFeel
		+ 0.3f * BoostBlend + Ship->ThrusterQuantumGlow * QuantumBlend) * FMath::Lerp(1.f, Ship->QuantumThrusterScale, QuantumBlend);
	const float Power = Ship->GetEngineSpoolAlpha();   // the nozzles glow with the engines, not the power
	for (FShipGlowMaterial& Glow : ThrusterMaterials)
	{
		Apply(Glow, Glow.BaseStrength * Thrust * Power);
	}

	const bool bGlowLit = Ship->GetPowerState() != ESpacePowerState::Off;
	if (bGlowLit != bPowerGlowLit)
	{
		ApplyPowerGlow(bGlowLit);
	}

	// A quick double flash, like aircraft anti-collision strobes.
	const double Phase = FMath::Fmod(Ship->GetWorld()->GetTimeSeconds(), double(Ship->NavStrobePeriodSeconds));
	const bool bFlash = Phase < 0.06 || (Phase > 0.16 && Phase < 0.22);
	for (FShipGlowMaterial& Glow : StrobeMaterials)
	{
		Apply(Glow, Glow.BaseStrength * (bFlash ? 1.f : 0.03f) * Power);
	}
}

void UShipPresentationComponent::UpdateSpaceDust(float DeltaSeconds)
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	const APlayerController* PlayerController = Cast<APlayerController>(Ship->GetController());
	if (!PlayerController || !PlayerController->PlayerCameraManager || Ship->Landing->GetState() == ELandingState::Landed)
	{
		Ship->SpaceDust->HideDust();
		Ship->SpeedTunnel->HideTunnel();
		Ship->HullSparks->UpdateSparks(DeltaSeconds, 0.f, 0.f, Ship->GetActorLocation());
		return;
	}
	// The camera manager still holds last frame's view (it updates after the pawn ticks). At 1.2 km/s
	// that is 20 m behind, which put the dust's "nothing right at the lens" fade 20 m off and let a
	// streak run through the lens as a white wedge (21. 9. 2026). The camera travels with the ship,
	// so this frame's move is added.
	const FVector View = PlayerController->PlayerCameraManager->GetCameraLocation() + Ship->LinearVelocity * DeltaSeconds;
	// The dust only as a hint of motion in normal flight, and none in a jump (the tunnel is the look
	// there); Star Citizen shows almost no speed lines outside quantum (the reference video, 21. 9. 2026).
	Ship->SpaceDust->UpdateDust(View, Ship->LinearVelocity, 1.f - QuantumBlend);
	Ship->SpeedTunnel->UpdateTunnel(View, Ship->LinearVelocity, DeltaSeconds, QuantumBlend);
	Ship->HullSparks->UpdateSparks(DeltaSeconds, float(Ship->LinearVelocity.Size()), QuantumBlend, View);

	// The jump's own light: sun down, blue glow at the nose (only the player's ship touches the sun).
	Ship->QuantumGlow->SetIntensity(Ship->QuantumGlowCandela * QuantumBlend);
	Ship->QuantumGlow->SetVisibility(QuantumBlend > 0.01f);
	// The level's fill light goes down with it: inside the tunnel there is nothing to bounce off, and
	// against the pinned exposure the ship came out white instead of a silhouette (the author, 22. 9. 2026).
	if (USkyLightComponent* Sky = QuantumSky.Get())
	{
		if (QuantumBlend > 0.001f || QuantumSkyBaseIntensity >= 0.f)
		{
			if (QuantumSkyBaseIntensity < 0.f)
			{
				QuantumSkyBaseIntensity = Sky->Intensity;
			}
			Sky->SetIntensity(QuantumSkyBaseIntensity * FMath::Lerp(1.f, Ship->QuantumSkyScale, QuantumBlend));
			if (QuantumBlend <= 0.001f)
			{
				QuantumSkyBaseIntensity = -1.f;
			}
		}
	}
	if (UDirectionalLightComponent* Sun = QuantumSun.Get())
	{
		if (QuantumBlend > 0.001f || QuantumSunBaseIntensity >= 0.f)
		{
			if (QuantumSunBaseIntensity < 0.f)
			{
				QuantumSunBaseIntensity = Sun->Intensity;
			}
			Sun->SetIntensity(QuantumSunBaseIntensity * FMath::Lerp(1.f, Ship->QuantumSunScale, QuantumBlend));
			if (QuantumBlend <= 0.001f)
			{
				// Back to the level's own value; tuning (space.Sun) works again outside jumps.
				QuantumSunBaseIntensity = -1.f;
			}
		}
	}
}

void UShipPresentationComponent::UpdateViewCollection()
{
	ASpaceshipPawn* const Ship = CastChecked<ASpaceshipPawn>(GetOwner());
	if (!ViewCollection)
	{
		return;
	}
	if (!bInteriorBoundsReady)
	{
		bInteriorBoundsReady = true;
		TArray<ULocalLightComponent*> Lights;
		Ship->GetComponents<ULocalLightComponent>(Lights);
		for (ULocalLightComponent* Light : Lights)
		{
			if (Light->GetName().StartsWith(TEXT("Light_fix_")))
			{
				FixtureLights.Add(Light);
				if (Light->CastShadows)
				{
					ShadowedFixtureLights.Add(Light);
				}
				if (Light->ComponentHasTag(TEXT("InteriorOnly")))
				{
					InteriorOnlyLights.Add(Light);
				}
			}
		}
		TArray<UStaticMeshComponent*> Meshes;
		Ship->GetComponents<UStaticMeshComponent>(Meshes);
		for (const UStaticMeshComponent* Mesh : Meshes)
		{
			if (Mesh->GetStaticMesh() && Mesh->GetName().StartsWith(TEXT("Interior")))
			{
				const FTransform ToActor = Mesh->GetComponentTransform().GetRelativeTransform(Ship->GetActorTransform());
				InteriorBoundsLocal += Mesh->GetStaticMesh()->GetBoundingBox().TransformBy(ToActor);
				const FString Name = Mesh->GetName();
				if (Name == TEXT("Interior") || Name == TEXT("InteriorKit") || Name == TEXT("InteriorDecals"))
				{
					InteriorShadowMeshes.Add(const_cast<UStaticMeshComponent*>(Mesh));
				}
			}
		}
	}
	const APlayerCameraManager* Camera = UGameplayStatics::GetPlayerCameraManager(Ship, 0);
	if (!Camera)
	{
		return;
	}
	// Through this pawn's own cameras: inside only in the cockpit view (the chase camera can hang inside the
	// interior's box above the hull). Through anything else (the walking character, a shot's free camera): the
	// camera inside the interior parts' box.
	bool bInside;
	if (Camera->GetViewTarget() == Ship)
	{
		bInside = Ship->bCockpitView;
	}
	else
	{
		bInside = InteriorBoundsLocal.IsValid
			&& InteriorBoundsLocal.IsInside(Ship->GetActorTransform().InverseTransformPosition(Camera->GetCameraLocation()));
	}
	// The fixture lights (a light for every strip and lamp, hs_fixture_lights.py) only while the camera is inside:
	// without shadows they light the hull through its walls, and from outside their volumes cover the whole ship
	// on screen (~3 ms on the target GPU in a close chase view)
	// The fixtures are the ship's lights: dark while it is powered off.
	const bool bWantFixtures = (FixtureLightMode < 0 ? bInside : FixtureLightMode > 0) && Ship->GetPowerState() != ESpacePowerState::Off;
	// The interior lighting (MegaLights, walked interiors): the interior meshes out of the sun's shadows - the hull
	// shadows the rooms anyway, and flown the cockpit keeps its interior's sun shadows
	const int32 ShadowState = ASpacePlayerController::IsInteriorLightingOn() ? 1 : 0;
	if (ShadowState != InteriorShadowState)
	{
		InteriorShadowState = ShadowState;
		bFixtureLightsDirty = true;       // the interior-only lights follow the lighting mode
		for (UStaticMeshComponent* Mesh : InteriorShadowMeshes)
		{
			if (Mesh)
			{
				Mesh->SetCastShadow(ShadowState == 0);
			}
		}
		for (ULocalLightComponent* Light : ShadowedFixtureLights)
		{
			if (Light)
			{
				Light->SetCastShadows(ShadowState == 1);
			}
		}
	}
	if (bWantFixtures != bFixtureLightsOn || bFixtureLightsDirty)
	{
		bFixtureLightsOn = bWantFixtures;
		bFixtureLightsDirty = false;
		for (ULocalLightComponent* Light : FixtureLights)
		{
			if (Light)
			{
				Light->SetVisibility(bWantFixtures && (ShadowState == 1 || !InteriorOnlyLights.Contains(Light)));
			}
		}
	}
	// One collection for the whole world: the ship the camera is in wins the frame, the others only clear
	// it when no ship has claimed it yet this frame.
	static uint64 ClaimedFrame = 0;
	if (bInside)
	{
		ClaimedFrame = GFrameCounter;
	}
	else if (ClaimedFrame == GFrameCounter)
	{
		InsideView = 0.f;
		return;
	}
	InsideView = bInside ? 1.f : 0.f;
	UKismetMaterialLibrary::SetScalarParameterValue(Ship, ViewCollection, TEXT("InsideView"), InsideView);
	// Seen from inside, the canopy fills the whole view: Lumen's sharp front-layer reflections on it cost ~1.9 ms
	// on the target GPU (RTX 2060, 1080p). Inside the cheap radiance-cache reflection is enough (the "weak"
	// reflection); outside the glass covers a small part of the screen and gets the sharp one.
	static int32 LastFrontLayer = -1;
	const int32 FrontLayer = bInside ? 0 : 1;
	if (FrontLayer != LastFrontLayer)
	{
		LastFrontLayer = FrontLayer;
		if (IConsoleVariable* Var = IConsoleManager::Get().FindConsoleVariable(TEXT("r.Lumen.TranslucencyReflections.FrontLayer.Enable")))
		{
			Var->Set(FrontLayer, ECVF_SetByCode);
		}
	}
}
