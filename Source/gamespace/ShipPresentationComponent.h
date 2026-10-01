// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ShipPresentationComponent.generated.h"

class UAudioComponent;
class UDirectionalLightComponent;
class ULocalLightComponent;
class UMaterialInstanceDynamic;
class UMaterialParameterCollection;
class USkyLightComponent;
class UStaticMeshComponent;

/** A hull material slot whose EmissiveStrength the ship animates (thrusters, strobes). */
struct FShipGlowMaterial
{
	TWeakObjectPtr<UMaterialInstanceDynamic> Material;
	float BaseStrength = 0.f;
	float Applied = -1.f;
};

/**
 * What the ship looks and sounds like from moment to moment, split out of ASpaceshipPawn
 * (Docs/Reviews/2026-09-30_spaceshippawn_split_plan.md): camera kick, shake, field of view, exposure and lag; the
 * engine sound layers; the thruster glow and nav strobes; space dust, speed tunnel and hull sparks with the quantum
 * jump's own light; and what the camera being inside the ship switches (MPC_ShipView, fixture lights, interior
 * shadows).
 *
 * The look reads nearly everything the ship does and all of its look tuning, so unlike the other components it reads
 * the pawn directly (a friend of ASpaceshipPawn) instead of taking arguments: the tuning, the cameras and the effect
 * components stay on the pawn, and the function bodies are the pawn's as they were. What lives here is the state -
 * the eased blends that drive the look, the kick, the sound layers, the glow materials, the inside view. No tick of
 * its own: the pawn's Tick calls the Update* functions after the flight step, in the same order as before.
 */
UCLASS(ClassGroup = (Spaceship), meta = (BlueprintSpawnableComponent = "false"))
class GAMESPACE_API UShipPresentationComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UShipPresentationComponent();

	// --- BeginPlay ---------------------------------------------------------------------------------------------

	void LoadViewCollection();
	/** The level's sun and sky light, dimmed in a quantum jump. */
	void FindLevelLights();
	void SetupAudioLayers();
	void SetupShipLights();

	// --- Every frame, after the flight step, in this order -----------------------------------------------------

	void UpdateCameraEffects(float DeltaSeconds);
	void UpdateEngineAudio(float DeltaSeconds);
	void UpdateShipLights(float DeltaSeconds);
	void UpdateSpaceDust(float DeltaSeconds);
	/**
	 * Glass reflection by where the camera is (author 26. 9. 2026): MPC_ShipView.InsideView = 1 while the
	 * player's camera is inside this ship's interior (the "Interior*" parts' bounds, or the cockpit camera
	 * of a ship without one): the canopy reflects weakly; 0 in the chase camera and outside: strongly.
	 */
	void UpdateViewCollection();

	// --- For the pawn --------------------------------------------------------------------------------------------

	/** A jolt felt in the camera: at least Strength now, dying away. */
	void Kick(float Strength) { CameraKick = FMath::Max(CameraKick, Strength); }
	/** The kick set outright (a quantum jump's start and end). */
	void SetKick(float Strength) { CameraKick = Strength; }

	/** 0..1: how much of the quantum look is showing. */
	float GetQuantumBlend() const { return QuantumBlend; }
	/** Shots: the jump's look at once. */
	void SetQuantumBlend(float Blend) { QuantumBlend = Blend; }

	/** MPC_ShipView.InsideView as this ship last set it: 1 = the player's camera is inside its interior. */
	float GetInsideView() const { return InsideView; }
	/** Fixture lights (Light_fix_*): -1 automatic (on only with the camera inside), 0 forced off, 1 forced on. */
	void SetFixtureLightMode(int32 Mode) { FixtureLightMode = Mode; bFixtureLightsDirty = true; }

private:
	/** Eased 0..1 blends driving camera, lights and sound. */
	float BoostBlend = 0.f;
	float AfterburnerFeel = 0.f;
	float QuantumBlend = 0.f;
	float CameraKick = 0.f;

	/** Smoothed engine load and boost blend, each in [0, 1], driving the engine sound. */
	float EngineLoad = 0.f;
	float EngineBoostBlend = 0.f;
	float HumBlend = 0.f;
	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> EngineHumAudio;
	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> BoostAudio;
	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> QuantumAudio;

	TArray<FShipGlowMaterial> ThrusterMaterials;
	TArray<FShipGlowMaterial> StrobeMaterials;

	/** The level's sun and its own intensity, for QuantumSunScale. */
	TWeakObjectPtr<UDirectionalLightComponent> QuantumSun;
	float QuantumSunBaseIntensity = -1.f;
	TWeakObjectPtr<USkyLightComponent> QuantumSky;
	float QuantumSkyBaseIntensity = -1.f;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialParameterCollection> ViewCollection;
	/** The interior parts' bounds in actor space (cm); invalid when the ship has none. */
	FBox InteriorBoundsLocal = FBox(ForceInit);
	bool bInteriorBoundsReady = false;
	float InsideView = 0.f;
	/** The Light_fix_* components (hs_fixture_lights.py), on only while the camera is inside the ship. */
	UPROPERTY(Transient)
	TArray<TObjectPtr<ULocalLightComponent>> FixtureLights;
	bool bFixtureLightsOn = true;
	int32 FixtureLightMode = -1;
	bool bFixtureLightsDirty = false;
	/** The interior meshes (Interior, InteriorKit, InteriorDecals): out of the sun's shadows while the interior
	 * lighting is on. The hull still shadows the rooms; non-Nanite, they cost ~2 ms of the sun's virtual shadow maps
	 * in a corridor view (28. 9. 2026). The kit rooms' parts (InteriorMod_*) are off the sun's lighting channel. */
	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> InteriorShadowMeshes;
	/** The fixture lights imported with shadows (a kit room's main lights, kit_rooms.py): shadowed only under the
	 * interior lighting (MegaLights traces them); flown, their shadow maps cost ~4-5 ms (28. 9. 2026). */
	UPROPERTY(Transient)
	TArray<TObjectPtr<ULocalLightComponent>> ShadowedFixtureLights;
	/** Fixture lights tagged InteriorOnly (kit_rooms.py: the component bays' lights): on only under the interior
	 * lighting; flown, every unshadowed light costs its full screen area (~0.6 ms for a corridor's bays, 29. 9. 2026). */
	UPROPERTY(Transient)
	TArray<TObjectPtr<ULocalLightComponent>> InteriorOnlyLights;
	int32 InteriorShadowState = -1;
};
