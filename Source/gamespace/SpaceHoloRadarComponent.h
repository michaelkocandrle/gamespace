// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "SpaceHoloRadarComponent.generated.h"

class ASpaceshipPawn;
class UMaterialInstanceDynamic;
class UMaterialInterface;
class UStaticMesh;
class UStaticMeshComponent;

/**
 * The cockpit's 3D holographic radar (author 8. 10. 2026: instead of the two small centre screens - a radar standing
 * over the centre column's emitter as light, switched on and off from interact mode). A disc of light with range rings,
 * a cross and a rotating sweep (M_Ship_HoloRadar) floats over the emitter; every contact is a point of light at its
 * place around the ship in 3D - ahead along the ship's nose, above or below its wings - on a thin stalk down to the
 * disc (SC's radar). Planets and moons are a bearing on the rim. The ship sits in the middle as a small cone.
 *
 * Placed at the hull socket Control_radar (hs_cockpit.pedestal); a ship without it has no radar. Visible while the
 * ship is powered and the radar is switched on.
 */
UCLASS(ClassGroup = Space)
class GAMESPACE_API USpaceHoloRadarComponent : public USceneComponent
{
	GENERATED_BODY()

public:
	USpaceHoloRadarComponent();

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** Whether this ship has the radar (its socket exists). */
	bool HasRadar() const { return bHasRadar; }

	bool IsRadarOn() const { return bRadarOn; }
	void SetRadarOn(bool bOn);
	void ToggleRadar() { SetRadarOn(!bRadarOn); }

	/** Disc radius, cm. */
	UPROPERTY(EditAnywhere, Category = "Holo Radar")
	float RadiusCm = 13.f;

	/** The disc's height over the emitter, cm. */
	UPROPERTY(EditAnywhere, Category = "Holo Radar")
	float DiscHeightCm = 8.f;

	/** The disc tilted towards the pilot, deg (flat it read as a thin line from the eye just above it). */
	UPROPERTY(EditAnywhere, Category = "Holo Radar")
	float TiltDeg = 28.f;

	/** Range at the rim, m. */
	UPROPERTY(EditAnywhere, Category = "Holo Radar")
	float RangeM = 5000.f;

	/** Contacts are read this often, Hz (the sweep itself runs in the material). */
	UPROPERTY(EditAnywhere, Category = "Holo Radar")
	float UpdateHz = 5.f;

	UPROPERTY(EditAnywhere, Category = "Holo Radar")
	FLinearColor ContactColour = FLinearColor(0.35f, 0.75f, 1.f);

	UPROPERTY(EditAnywhere, Category = "Holo Radar")
	FLinearColor BodyColour = FLinearColor(1.f, 0.6f, 0.2f);

private:
	static constexpr int32 MaxBlips = 24;

	UStaticMeshComponent* MakePiece(UStaticMesh* Mesh, UMaterialInterface* Material, FName Name);
	void UpdateContacts();
	void ApplyVisibility();

	UPROPERTY(Transient)
	TObjectPtr<UStaticMesh> PlaneMesh;
	UPROPERTY(Transient)
	TObjectPtr<UStaticMesh> SphereMesh;
	UPROPERTY(Transient)
	TObjectPtr<UStaticMesh> CylinderMesh;
	UPROPERTY(Transient)
	TObjectPtr<UStaticMesh> ConeMesh;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> Pieces;
	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> Blips;
	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> Stalks;
	UPROPERTY(Transient)
	TArray<TObjectPtr<UMaterialInstanceDynamic>> BlipMaterials;

	TWeakObjectPtr<ASpaceshipPawn> Ship;
	bool bHasRadar = false;
	bool bRadarOn = true;
	bool bShown = false;
	int32 ActiveBlips = 0;
	float SinceUpdate = 0.f;
};
