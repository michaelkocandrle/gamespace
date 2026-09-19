// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CockpitDisplayComponent.generated.h"

class FWidgetRenderer;
class SWidget;
class UMaterialInstanceDynamic;
class UMeshComponent;
class URectLightComponent;
class USpaceCockpitDisplays;
class UTextureRenderTarget2D;

/**
 * The cockpit's dashboard displays show the flight instruments: USpaceCockpitDisplays (the flight
 * HUD's widgets laid out for two screens) is drawn into a render target, and the render target goes
 * into the ScreenTexture of the interior's display slot - the material slot whose name ends in
 * ScreenSlotSuffix (M_Ship_<Ship>_Screens, made by Tools/Blender/build_ai_ship.py: flat quads over
 * the AI model's painted screens, UV-mapped side by side across one texture).
 *
 * Drawn UpdateRateHz times a second, and only while the owning ship is flown from the cockpit: from
 * the chase camera nobody sees the dashboard. A ship without a display slot simply has no displays.
 */
UCLASS(ClassGroup = (Spaceship), meta = (BlueprintSpawnableComponent))
class GAMESPACE_API UCockpitDisplayComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UCockpitDisplayComponent();

	/** The display slot: the first material slot on the ship whose name ends in this. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cockpit Displays")
	FString ScreenSlotSuffix = TEXT("_Screens");

	/** Texture parameter of the display material (M_Ship_Screen) that gets the render target. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cockpit Displays")
	FName TextureParameter = TEXT("ScreenTexture");

	/**
	 * How wide one display is on screen as a share of the window's width at the cockpit's 88 degree
	 * field of view (measured on the Vanguard: ~295 of 1911 px). The render target follows the window
	 * from this, so the type is drawn at the size it is seen: drawn larger and shrunk by the GPU, its
	 * thin strokes fell between samples and the words broke up.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cockpit Displays", meta = (ClampMin = "0.01"))
	float ScreenShareAt88 = 0.155f;

	/** Render target pixels per screen pixel (a little over 1 keeps edges smooth). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cockpit Displays", meta = (ClampMin = "0.5"))
	float Oversample = 1.25f;

	/** Tests: the layout scale the displays are drawn at. */
	UFUNCTION(BlueprintCallable, Category = "Cockpit Displays|Tests")
	float PixelScale() const;

	/** Render target size for a layout scale (the whole canvas: both MFDs and the centre column). */
	static FVector2D TargetSize(float Scale);

	/**
	 * How often the figures change, per second. Like a real instrument's readout: a number rewritten
	 * every frame (speed while accelerating) was a blur of two values under temporal AA; held for a few
	 * frames it is sharp. Bars and lamps still move smoothly (they ease between these updates).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cockpit Displays", meta = (ClampMin = "1.0"))
	float StateRateHz = 12.f;

	/** Redraws per second: 60, so bars and lamps move smoothly. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cockpit Displays", meta = (ClampMin = "1.0"))
	float UpdateRateHz = 60.f;

	/** Draw only while the ship is flown from the cockpit (off: always, e.g. for a passenger view). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cockpit Displays")
	bool bOnlyInCockpitView = true;

	/**
	 * The displays light the cockpit around them: a shadowless rect light in front of each socket named
	 * Display_* on the ship (build_ai_ship.py puts one in front of every display), facing the pilot.
	 * Candela per display; 0: no light.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cockpit Displays", meta = (ClampMin = "0.0"))
	float DisplayLightIntensityCd = 0.f;

	/** The displays' glow colour: a cool cyan-blue, as the reference's screens light its cockpit. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cockpit Displays")
	FLinearColor DisplayLightColor = FLinearColor(0.4f, 0.75f, 1.f);

	/** Size of one display light, cm (about the screen). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cockpit Displays")
	FVector2D DisplayLightSizeCm = FVector2D(32.0, 28.0);

	/** How far the displays' light reaches, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cockpit Displays", meta = (ClampMin = "1.0"))
	float DisplayLightRadiusCm = 160.f;

	/** The cockpit radar's range, metres (the reference's shows 2 km; asteroids here are kilometres apart). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cockpit Displays", meta = (ClampMin = "100.0"))
	float RadarRangeM = 5000.f;

	/**
	 * MFD pages (F1 and F2 in the ship, [ and ] too; Alt goes back): Display 0 left, 1 right. Kept here, so the page
	 * stays when the displays are rebuilt, and works headless.
	 */
	UFUNCTION(BlueprintCallable, Category = "Cockpit Displays")
	void CyclePage(int32 Display, int32 Direction);

	UFUNCTION(BlueprintCallable, Category = "Cockpit Displays")
	void SetPage(int32 Display, int32 Page);

	UFUNCTION(BlueprintPure, Category = "Cockpit Displays")
	int32 GetPage(int32 Display) const;

	/** Changes the display lights' brightness (tuning, shots). */
	UFUNCTION(BlueprintCallable, Category = "Cockpit Displays")
	void SetDisplayLightIntensity(float Candela);

	/** Tests: the display lights made at BeginPlay. */
	UFUNCTION(BlueprintCallable, Category = "Cockpit Displays|Tests")
	int32 GetDisplayLightCount() const { return Lights.Num(); }

	/** Tests: a display light's candela (smaller screens light less), -1 for a bad index. */
	UFUNCTION(BlueprintCallable, Category = "Cockpit Displays|Tests")
	float GetDisplayLightIntensity(int32 Index) const;

	/** Tests: the display slot was found and the displays are set up. */
	UFUNCTION(BlueprintCallable, Category = "Cockpit Displays|Tests")
	bool HasDisplays() const { return RenderTarget != nullptr; }

	UFUNCTION(BlueprintCallable, Category = "Cockpit Displays|Tests")
	UTextureRenderTarget2D* GetRenderTarget() const { return RenderTarget; }

	UFUNCTION(BlueprintCallable, Category = "Cockpit Displays|Tests")
	USpaceCockpitDisplays* GetDisplaysWidget() const { return Widget; }

	/** The mesh and slot index the displays are on (null / INDEX_NONE: this ship has none). */
	UFUNCTION(BlueprintCallable, Category = "Cockpit Displays")
	static UMeshComponent* FindDisplaySlot(const AActor* Ship, const FString& Suffix, int32& OutSlot);

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	UPROPERTY(Transient)
	TObjectPtr<UTextureRenderTarget2D> RenderTarget;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> Material;

	UPROPERTY(Transient)
	TObjectPtr<USpaceCockpitDisplays> Widget;

	UPROPERTY(Transient)
	TArray<TObjectPtr<URectLightComponent>> Lights;

	/** Each light's share of DisplayLightIntensityCd: its screen's area against a big display's. */
	TArray<float> LightShares;

	/** The MFDs' pages, left and right. */
	int32 Pages[2] = { 0, 0 };

	void CreateDisplayLights();

	TSharedPtr<SWidget> SlateWidget;
	FWidgetRenderer* Renderer = nullptr;
	/**
	 * The one window the displays are drawn in. FWidgetRenderer::DrawWidget makes a new window for every
	 * draw, and Slate keeps an element list, with its vertex arrays, per window: a new window meant arrays
	 * grown from nothing every draw, re-allocated and copied whole for every render batch - ~3.5 ms of
	 * Slate::AddLineElements a draw (19. 9. 2026). With one window the list and its capacity are reused.
	 */
	TSharedPtr<class SVirtualWindow> DrawWindow;
	TSharedPtr<class FHittestGrid> HitTestGrid;
	float SinceDraw = 0.f;
	float SinceState = 0.f;
	float CurrentScale = 1.f;
};
