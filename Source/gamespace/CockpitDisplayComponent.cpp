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
#include "Slate/WidgetRenderer.h"
#include "SpaceFlightHud.h"
#include "SpaceshipPawn.h"

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

	// Like UWidgetComponent: Slate draws in linear space into an sRGB target, the material samples it as colour.
	const FVector2D Size(USpaceCockpitDisplays::DisplayWidth * 2.f, USpaceCockpitDisplays::DisplayHeight);
	RenderTarget = FWidgetRenderer::CreateTargetFor(Size, TF_Bilinear, false);
	RenderTarget->ClearColor = FLinearColor::Black;
	Renderer = new FWidgetRenderer(false);

	Material = UMaterialInstanceDynamic::Create(Mesh->GetMaterial(Slot), this);
	Material->SetTextureParameterValue(TextureParameter, RenderTarget);
	Mesh->SetMaterial(Slot, Material);
	// Draw on the first tick.
	SinceDraw = 1.f / UpdateRateHz;
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
			URectLightComponent* Light = NewObject<URectLightComponent>(GetOwner(), NAME_None, RF_Transient);
			Light->SetupAttachment(Mesh, Socket);
			Light->SetCastShadows(false);
			Light->SetIntensityUnits(ELightUnits::Candelas);
			Light->SetSourceWidth(DisplayLightSizeCm.X);
			Light->SetSourceHeight(DisplayLightSizeCm.Y);
			Light->SetBarnDoorAngle(80.f);
			Light->SetAttenuationRadius(DisplayLightRadiusCm);
			Light->SetLightColor(DisplayLightColor);
			Light->RegisterComponent();
			// Facing the pilot: the screens are turned towards the eye, and so is their light.
			const FVector At = Mesh->GetSocketLocation(Socket);
			const FVector To = Eye ? Eye->GetComponentLocation() : At - Mesh->GetForwardVector() * 100.f;
			Light->SetWorldRotation((To - At).Rotation());
			Lights.Add(Light);
		}
	}
	SetDisplayLightIntensity(DisplayLightIntensityCd);
}

void UCockpitDisplayComponent::SetDisplayLightIntensity(float Candela)
{
	DisplayLightIntensityCd = FMath::Max(Candela, 0.f);
	for (URectLightComponent* Light : Lights)
	{
		Light->SetIntensity(DisplayLightIntensityCd);
		Light->SetVisibility(DisplayLightIntensityCd > 0.f);
	}
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
	if (SinceDraw < 1.f / UpdateRateHz)
	{
		return;
	}
	// The displays are part of the ship: H hides the HUD overlay, not the dashboard.
	Widget->ApplyState(USpaceFlightHud::MakeState(Ship, 1));
	const FVector2D Size(RenderTarget->SizeX, RenderTarget->SizeY);
	Renderer->DrawWidget(RenderTarget, SlateWidget.ToSharedRef(), Size, SinceDraw);
	SinceDraw = 0.f;
}
