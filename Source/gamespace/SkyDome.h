// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SkyDome.generated.h"

class UMaterialInstanceDynamic;
class UStaticMeshComponent;

/**
 * Sky sphere that stays centred on the player camera.
 *
 * The sky material looks its stars up by view direction, so the dome's position never changes
 * how the sky looks; it only has to surround the camera. Following the camera means the ship
 * can fly any distance - including across origin rebases - without leaving it.
 *
 * Anything farther away than DomeRadiusKm is hidden behind the dome, so the radius must exceed
 * the distance of the farthest body that should be visible.
 *
 * Inside a planet's atmosphere the dome blends from stars to a sky gradient: every frame it
 * samples the environment of the body nearest to the camera and passes AtmosphereAmount,
 * PlanetUp and the sky colours to the material.
 *
 * It also points the material's sun disc at the level's first directional light, and scales
 * star twinkle and nebula brightness (stronger twinkle in air, where real stars scintillate).
 */
UCLASS()
class GAMESPACE_API ASkyDome : public AActor
{
	GENERATED_BODY()

public:
	/** The dome's own material instance (tuning: space.SkyParam). Null before BeginPlay. */
	UMaterialInstanceDynamic* GetSkyMaterial() const { return SkyMaterial; }

	ASkyDome();

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

protected:
	/** Engine sphere; its material is set on the placed actor (M_Starfield_Sky). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Sky Dome")
	TObjectPtr<UStaticMeshComponent> Dome;

	/** Radius of the dome in km. Must exceed the distance to the farthest visible body. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Sky Dome", meta = (ClampMin = "1.0", Units = "km"))
	float DomeRadiusKm = 1000.f;

	/** Star twinkle in empty space, 0..1 of a star's brightness... */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Sky Dome", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float SpaceTwinkle = 0.12f;

	/** ...and in full atmosphere. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Sky Dome", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float AtmosphereTwinkle = 0.6f;

	/** Multiplies the nebula brightness baked into the material. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Sky Dome", meta = (ClampMin = "0.0"))
	float NebulaScale = 1.f;

	/** Multiplies the sun disc and glow brightness baked into the material. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Sky Dome", meta = (ClampMin = "0.0"))
	float SunScale = 1.f;

private:
	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> SkyMaterial;

	TWeakObjectPtr<class ADirectionalLight> Sun;
	float NebulaBase = -1.f;
	float SunDiscBase = -1.f;
	float SunGlowBase = -1.f;
};
