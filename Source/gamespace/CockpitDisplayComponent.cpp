// Copyright Epic Games, Inc. All Rights Reserved.

#include "CockpitDisplayComponent.h"

#include "Blueprint/UserWidget.h"
#include "Camera/CameraComponent.h"
#include "Components/MeshComponent.h"
#include "Components/RectLightComponent.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/World.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/App.h"
#include "RenderDeferredCleanup.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Slate/WidgetRenderer.h"
#include "SpaceFlightHud.h"
#include "SpaceshipPawn.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"
#include "Stats/Stats.h"

// "stat SpaceCockpit": what the dashboard displays cost the game thread.
DECLARE_STATS_GROUP(TEXT("SpaceCockpit"), STATGROUP_SpaceCockpit, STATCAT_Advanced);
DECLARE_CYCLE_STAT(TEXT("Display state (radar, figures)"), STAT_CockpitDisplayState, STATGROUP_SpaceCockpit);
DECLARE_CYCLE_STAT(TEXT("Display draw"), STAT_CockpitDisplayDraw, STATGROUP_SpaceCockpit);

namespace
{
	TAutoConsoleVariable<int32> CVarCockpitCentre(
		TEXT("space.CockpitCentre"),
		1,
		TEXT("The dashboard's centre column (radar over self status): 1 on, 0 off - its screens go dark and the radar stops looking."),
		ECVF_Default);

	/** space.MfdPage <left> <right>: the MFDs' pages of the ship flown here (shots, testing). */
	FAutoConsoleCommandWithWorldAndArgs MfdPageCommand(
		TEXT("space.MfdPage"),
		TEXT("space.MfdPage <left 0-2> <right 0-2>: FLIGHT / THRUSTERS / NAVIGATION on the left, STATUS / CONTACTS / SELF STATUS on the right."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			for (TActorIterator<ASpaceshipPawn> It(World); It; ++It)
			{
				if (UCockpitDisplayComponent* Displays = It->FindComponentByClass<UCockpitDisplayComponent>())
				{
					for (int32 Display = 0; Display < 2 && Display < Args.Num(); ++Display)
					{
						Displays->SetPage(Display, FCString::Atoi(*Args[Display]));
					}
				}
			}
		}));
}

UCockpitDisplayComponent::UCockpitDisplayComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	// After the ship has moved, so the displays show this frame's state.
	PrimaryComponentTick.TickGroup = TG_PostPhysics;
}

UMeshComponent* UCockpitDisplayComponent::FindDisplaySlot(const AActor* Ship, const FString& Suffix, int32& OutSlot)
{
	OutSlot = INDEX_NONE;
	if (!Ship)
	{
		return nullptr;
	}
	TArray<UMeshComponent*> Meshes;
	Ship->GetComponents(Meshes);
	for (UMeshComponent* Mesh : Meshes)
	{
		const TArray<FName> Names = Mesh->GetMaterialSlotNames();
		for (int32 Index = 0; Index < Names.Num(); ++Index)
		{
			if (Names[Index].ToString().EndsWith(Suffix))
			{
				OutSlot = Mesh->GetMaterialIndex(Names[Index]);
				return Mesh;
			}
		}
	}
	return nullptr;
}

void UCockpitDisplayComponent::BeginPlay()
{
	Super::BeginPlay();
	if (!FApp::CanEverRender() || GetNetMode() == NM_DedicatedServer)
	{
		SetComponentTickEnabled(false);
		return;
	}
	int32 Slot = INDEX_NONE;
	UMeshComponent* Mesh = FindDisplaySlot(GetOwner(), ScreenSlotSuffix, Slot);
	if (!Mesh || Slot == INDEX_NONE)
	{
		SetComponentTickEnabled(false);
		return;
	}

	Widget = CreateWidget<USpaceCockpitDisplays>(GetWorld(), USpaceCockpitDisplays::StaticClass());
	if (!Widget)
	{
		SetComponentTickEnabled(false);
		return;
	}
	SlateWidget = Widget->TakeWidget();
	Widget->SetShip(GetOwner());

	// Like UWidgetComponent: Slate draws in linear space into an sRGB target, the material samples it as
	// colour. Sized to how large the displays are on screen (see PixelScale), not to their layout.
	CurrentScale = PixelScale();
	RenderTarget = FWidgetRenderer::CreateTargetFor(TargetSize(CurrentScale), TF_Bilinear, false);
	RenderTarget->ClearColor = FLinearColor::Black;
	Renderer = new FWidgetRenderer(false);

	Material = UMaterialInstanceDynamic::Create(Mesh->GetMaterial(Slot), this);
	Material->SetTextureParameterValue(TextureParameter, RenderTarget);
	Mesh->SetMaterial(Slot, Material);
	// Draw on the first tick.
	SinceDraw = 1.f / UpdateRateHz;
	SinceState = 1.f / StateRateHz;
	CreateDisplayLights();
}

void UCockpitDisplayComponent::CreateDisplayLights()
{
	const ASpaceshipPawn* Ship = Cast<ASpaceshipPawn>(GetOwner());
	const UCameraComponent* Eye = Ship ? Ship->FindComponentByClass<UCameraComponent>() : nullptr;
	for (const UCameraComponent* Camera : TInlineComponentArray<UCameraComponent*>(GetOwner()))
	{
		if (Camera->GetName() == TEXT("CockpitCamera"))
		{
			Eye = Camera;
		}
	}
	TArray<UMeshComponent*> Meshes;
	GetOwner()->GetComponents(Meshes);
	for (UMeshComponent* Mesh : Meshes)
	{
		for (const FName& Socket : Mesh->GetAllSocketNames())
		{
			if (!Socket.ToString().StartsWith(TEXT("Display_")))
			{
				continue;
			}
			// As large and as bright as its screen: the centre column's small ones light less than the MFDs.
			const FBox2D Rect = USpaceCockpitDisplays::ScreenRect(Socket.ToString().RightChop(8));
			const FVector2D Share = Rect.bIsValid ? Rect.GetSize() / FVector2D(USpaceCockpitDisplays::DisplayWidth, USpaceCockpitDisplays::DisplayHeight)
				: FVector2D(1.0, 1.0);
			URectLightComponent* Light = NewObject<URectLightComponent>(GetOwner(), NAME_None, RF_Transient);
			Light->SetupAttachment(Mesh, Socket);
			Light->SetCastShadows(false);
			Light->SetIntensityUnits(ELightUnits::Candelas);
			Light->SetSourceWidth(DisplayLightSizeCm.X * Share.X);
			Light->SetSourceHeight(DisplayLightSizeCm.Y * Share.Y);
			Light->SetBarnDoorAngle(80.f);
			Light->SetAttenuationRadius(DisplayLightRadiusCm);
			Light->SetLightColor(DisplayLightColor);
			Light->RegisterComponent();
			// Facing the pilot: the screens are turned towards the eye, and so is their light.
			const FVector At = Mesh->GetSocketLocation(Socket);
			const FVector To = Eye ? Eye->GetComponentLocation() : At - Mesh->GetForwardVector() * 100.f;
			Light->SetWorldRotation((To - At).Rotation());
			Lights.Add(Light);
			LightShares.Add(float(Share.X * Share.Y));
		}
	}
	SetDisplayLightIntensity(DisplayLightIntensityCd);
}

void UCockpitDisplayComponent::SetDisplayLightIntensity(float Candela)
{
	DisplayLightIntensityCd = FMath::Max(Candela, 0.f);
	for (int32 Index = 0; Index < Lights.Num(); ++Index)
	{
		Lights[Index]->SetIntensity(DisplayLightIntensityCd * LightShares[Index]);
		Lights[Index]->SetVisibility(DisplayLightIntensityCd > 0.f);
	}
}

void UCockpitDisplayComponent::CyclePage(int32 Display, int32 Direction)
{
	SetPage(Display, GetPage(Display) + (Direction < 0 ? -1 : 1));
}

void UCockpitDisplayComponent::SetPage(int32 Display, int32 Page)
{
	if (Display < 0 || Display > 1)
	{
		return;
	}
	const int32 Count = USpaceCockpitDisplays::PageCount;
	Pages[Display] = ((Page % Count) + Count) % Count;
	// Fill the new page's figures on the next draw rather than up to 200 ms later.
	SinceState = 1.f / FMath::Max(StateRateHz, 1.f);
}

int32 UCockpitDisplayComponent::GetPage(int32 Display) const
{
	return Display >= 0 && Display <= 1 ? Pages[Display] : 0;
}

float UCockpitDisplayComponent::GetDisplayLightIntensity(int32 Index) const
{
	return Lights.IsValidIndex(Index) ? Lights[Index]->Intensity : -1.f;
}

void UCockpitDisplayComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (Renderer)
	{
		BeginCleanup(Renderer);
		Renderer = nullptr;
	}
	SlateWidget.Reset();
	Super::EndPlay(EndPlayReason);
}

void UCockpitDisplayComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	const ASpaceshipPawn* Ship = Cast<ASpaceshipPawn>(GetOwner());
	if (!Renderer || !Widget || !SlateWidget.IsValid() || !Ship)
	{
		return;
	}
	if (bOnlyInCockpitView && (!Ship->IsCockpitView() || !Ship->IsLocallyControlled()))
	{
		return;
	}
	// The lamps and gauges ease every frame; the picture is taken UpdateRateHz times a second.
	Widget->DebugAdvance(DeltaTime);
	SinceDraw += DeltaTime;
	SinceState += DeltaTime;
	if (SinceDraw < 1.f / UpdateRateHz)
	{
		return;
	}
	// The displays are part of the ship: H hides the HUD overlay, not the dashboard. The figures change
	// StateRateHz times a second (see there); the drawing goes on at UpdateRateHz.
	Widget->SetPages(Pages[0], Pages[1]);
	if (SinceState >= 1.f / StateRateHz)
	{
		SCOPE_CYCLE_COUNTER(STAT_CockpitDisplayState);
		const bool bCentre = CVarCockpitCentre.GetValueOnGameThread() != 0;
		Widget->SetCentreColumn(bCentre);
		Widget->ApplyState(bCentre ? USpaceCockpitDisplays::MakeDisplayState(Ship, RadarRangeM) : USpaceFlightHud::MakeState(Ship, 1));
		SinceState = 0.f;
	}
	// Follow the window size: the type is laid out for 560 x 490 per MFD and drawn at the scale the screen shows
	// it, so the font rasteriser draws every letter at its real size. Re-made only on a real change.
	const float Scale = PixelScale();
	if (FMath::Abs(Scale - CurrentScale) > 0.099f)
	{
		CurrentScale = Scale;
		const FVector2D NewSize = TargetSize(Scale);
		RenderTarget->ResizeTarget(uint32(NewSize.X), uint32(NewSize.Y));
	}
	SCOPE_CYCLE_COUNTER(STAT_CockpitDisplayDraw);
	Renderer->DrawWidget(RenderTarget, SlateWidget.ToSharedRef(), CurrentScale, FVector2D(RenderTarget->SizeX, RenderTarget->SizeY), SinceDraw);
	SinceDraw = 0.f;
}

float UCockpitDisplayComponent::PixelScale() const
{
	FVector2D Viewport(1920.0, 1080.0);
	if (GEngine && GEngine->GameViewport)
	{
		GEngine->GameViewport->GetViewportSize(Viewport);
	}
	// From the window's width only, not the live field of view: the afterburner and cruise widen the
	// view a little every frame, the scale flipped between two steps and the target was re-made (and
	// drawn half-made) every frame, which broke the type up in flight.
	const float OnScreen = float(Viewport.X) * ScreenShareAt88;
	const float Scale = OnScreen * Oversample / USpaceCockpitDisplays::DisplayWidth;
	return FMath::Clamp(FMath::RoundToFloat(Scale * 20.f) / 20.f, 0.3f, 2.f);
}

FVector2D UCockpitDisplayComponent::TargetSize(float Scale)
{
	return FVector2D(FMath::RoundToDouble(USpaceCockpitDisplays::CanvasWidth * Scale), FMath::RoundToDouble(USpaceCockpitDisplays::CanvasHeight * Scale));
}
