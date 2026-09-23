// Copyright Epic Games, Inc. All Rights Reserved.

/**
 * Ship interiors tuned in the running game, the same way SpacePostTuning.cpp does the scene: the
 * materials and lights of the placed interior, found by actor tag (labels do not survive cooking).
 * Tools/Assets/import_interior.py puts the tags on.
 *
 *   space.Kit Lift 0.8                      a scalar on every interior material (Lift, MetallicScale,
 *   space.Kit Lift 0.8 Trim                 RoughnessScale, RoughnessFloor, AccentStrength); an optional
 *                                           last word keeps it to materials whose name contains it
 *   space.KitColor Gunmetal .45 .52 .62 Trim   the same for a colour
 *   space.KitLight Work Temperature 7000    a property of the interior lights (Work, Accent or All);
 *   space.KitLight All UseTemperature 1     Intensity (lm), LightColor, AttenuationRadius...
 *   space.KitReset                          everything above, and the sun and sky light, back to what
 *                                           the level has
 *
 * Shot runs keep console settings for the rest of the run (Docs/WORKFLOW.md 9.2), so every variant
 * in a tuning preset starts with space.KitReset. Nothing is saved: what looks right goes into
 * Tools/Assets/import_interior.py.
 */

#include "CoreMinimal.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/SkyLight.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/UnrealType.h"

namespace
{
	const FName InteriorTag(TEXT("SpaceInterior"));
	const FName WorkLightTag(TEXT("SpaceInteriorLight_Work"));
	const FName AccentLightTag(TEXT("SpaceInteriorLight_Accent"));

	/** What the level had before any of these commands touched it, for space.KitReset. */
	struct FLightDefaults
	{
		float Intensity = 0.f;
		FLinearColor Colour = FLinearColor::White;
		float Temperature = 6500.f;
		bool bUseTemperature = false;
		float AttenuationRadius = 0.f;
	};
	TMap<TWeakObjectPtr<ULightComponentBase>, FLightDefaults> SavedLights;

	/** Base class on purpose: the sky light is a light, but not a ULightComponent. */
	void Remember(ULightComponentBase* Light)
	{
		if (!Light || SavedLights.Contains(Light))
		{
			return;
		}
		FLightDefaults Defaults;
		Defaults.Intensity = Light->Intensity;
		Defaults.Colour = Light->LightColor.ReinterpretAsLinear();
		if (const ULightComponent* Full = Cast<ULightComponent>(Light))
		{
			Defaults.Temperature = Full->Temperature;
			Defaults.bUseTemperature = Full->bUseTemperature;
		}
		if (const UPointLightComponent* Point = Cast<UPointLightComponent>(Light))
		{
			Defaults.AttenuationRadius = Point->AttenuationRadius;
		}
		SavedLights.Add(Light, Defaults);
	}

	void Restore(ULightComponentBase* Light, const FLightDefaults& Defaults)
	{
		// Straight to the fields and a render state refresh, not SetIntensity(): the interior lights
		// are Static, and the setters refuse to touch a static light in a running game.
		Light->Intensity = Defaults.Intensity;
		Light->LightColor = Defaults.Colour.ToFColor(false);
		if (ULightComponent* Full = Cast<ULightComponent>(Light))
		{
			Full->Temperature = Defaults.Temperature;
			Full->bUseTemperature = Defaults.bUseTemperature;
		}
		if (UPointLightComponent* Point = Cast<UPointLightComponent>(Light))
		{
			Point->AttenuationRadius = Defaults.AttenuationRadius;
		}
		Light->MarkRenderStateDirty();
	}

	/** The interior lights of one group ("Work", "Accent", "All"). */
	TArray<UPointLightComponent*> InteriorLights(UWorld* World, const FString& Group)
	{
		const bool bAll = Group.Equals(TEXT("All"), ESearchCase::IgnoreCase);
		const bool bWork = Group.Equals(TEXT("Work"), ESearchCase::IgnoreCase);
		TArray<UPointLightComponent*> Lights;
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			const bool bIsWork = It->ActorHasTag(WorkLightTag);
			const bool bIsAccent = It->ActorHasTag(AccentLightTag);
			if ((bAll && (bIsWork || bIsAccent)) || (bWork && bIsWork) || (!bAll && !bWork && bIsAccent))
			{
				if (UPointLightComponent* Light = It->FindComponentByClass<UPointLightComponent>())
				{
					Lights.Add(Light);
				}
			}
		}
		return Lights;
	}

	/**
	 * Every material slot of the interior as a dynamic instance, made on first use. The filter
	 * matches the name of the asset the slot came with (MI_T_Trim_01, MI_KitDark...), so that a
	 * colour meant for the trim sheets does not repaint the black plastic.
	 */
	TArray<UMaterialInstanceDynamic*> InteriorMaterials(UWorld* World, const FString& Filter)
	{
		TArray<UMaterialInstanceDynamic*> Materials;
		for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
		{
			if (!It->ActorHasTag(InteriorTag))
			{
				continue;
			}
			UStaticMeshComponent* Mesh = It->GetStaticMeshComponent();
			for (int32 Index = 0; Mesh && Index < Mesh->GetNumMaterials(); ++Index)
			{
				UMaterialInterface* Current = Mesh->GetMaterial(Index);
				UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Current);
				const UMaterialInterface* Source = Dynamic ? Dynamic->Parent.Get() : Current;
				if (!Source || (!Filter.IsEmpty() && !Source->GetName().Contains(Filter)))
				{
					continue;
				}
				if (!Dynamic)
				{
					Dynamic = Mesh->CreateAndSetMaterialInstanceDynamic(Index);
				}
				if (Dynamic)
				{
					Materials.Add(Dynamic);
				}
			}
		}
		return Materials;
	}

	FAutoConsoleCommandWithWorldAndArgs KitCommand(
		TEXT("space.Kit"),
		TEXT("space.Kit <Parameter> <Value> [part of a material name]: a scalar on the interior's materials (Lift, MetallicScale, RoughnessScale, RoughnessFloor, AccentStrength). Not saved."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (Args.Num() < 2)
			{
				UE_LOG(LogTemp, Display, TEXT("space.Kit <Parameter> <Value> [part of a material name]"));
				return;
			}
			const TArray<UMaterialInstanceDynamic*> Materials = InteriorMaterials(World, Args.Num() > 2 ? Args[2] : FString());
			for (UMaterialInstanceDynamic* Material : Materials)
			{
				Material->SetScalarParameterValue(FName(*Args[0]), FCString::Atof(*Args[1]));
			}
			UE_LOG(LogTemp, Display, TEXT("space.Kit %s = %s on %d materials"), *Args[0], *Args[1], Materials.Num());
		}));

	FAutoConsoleCommandWithWorldAndArgs KitColorCommand(
		TEXT("space.KitColor"),
		TEXT("space.KitColor <Parameter> <R> <G> <B> [part of a material name]: a colour on the interior's materials (Gunmetal, Accent). Not saved."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (Args.Num() < 4)
			{
				UE_LOG(LogTemp, Display, TEXT("space.KitColor <Parameter> <R> <G> <B> [part of a material name]"));
				return;
			}
			const FLinearColor Colour(FCString::Atof(*Args[1]), FCString::Atof(*Args[2]), FCString::Atof(*Args[3]), 1.f);
			const TArray<UMaterialInstanceDynamic*> Materials = InteriorMaterials(World, Args.Num() > 4 ? Args[4] : FString());
			for (UMaterialInstanceDynamic* Material : Materials)
			{
				Material->SetVectorParameterValue(FName(*Args[0]), Colour);
			}
			UE_LOG(LogTemp, Display, TEXT("space.KitColor %s on %d materials"), *Args[0], Materials.Num());
		}));

	FAutoConsoleCommandWithWorldAndArgs KitLightCommand(
		TEXT("space.KitLight"),
		TEXT("space.KitLight Work|Accent|All <Property> <Value...>: a property of the interior's lights (Intensity, Temperature, UseTemperature, LightColor R G B, AttenuationRadius). Not saved."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (Args.Num() < 3)
			{
				UE_LOG(LogTemp, Display, TEXT("space.KitLight Work|Accent|All <Property> <Value...>"));
				return;
			}
			FProperty* Property = nullptr;
			for (TFieldIterator<FProperty> It(UPointLightComponent::StaticClass()); It; ++It)
			{
				if (It->GetName().Equals(Args[1], ESearchCase::IgnoreCase)
					|| It->GetName().Equals(TEXT("b") + Args[1], ESearchCase::IgnoreCase))
				{
					Property = *It;
					break;
				}
			}
			if (!Property)
			{
				UE_LOG(LogTemp, Display, TEXT("space.KitLight %s: no such property"), *Args[1]);
				return;
			}
			// Colours by name, R G B: FColor declares its bytes B, G, R (Docs/WORKFLOW.md 9.5 e).
			FString Text = FString::Join(TArrayView<const FString>(Args.GetData() + 2, Args.Num() - 2), TEXT(" "));
			if (CastField<FStructProperty>(Property) && Args.Num() >= 5)
			{
				Text = FString::Printf(TEXT("(R=%s,G=%s,B=%s,A=255)"), *Args[2], *Args[3], *Args[4]);
			}
			int32 Count = 0;
			for (UPointLightComponent* Light : InteriorLights(World, Args[0]))
			{
				Remember(Light);
				if (Property->ImportText_Direct(*Text, Property->ContainerPtrToValuePtr<void>(Light), Light, PPF_None))
				{
					Light->MarkRenderStateDirty();
					++Count;
				}
			}
			UE_LOG(LogTemp, Display, TEXT("space.KitLight %s %s = %s on %d lights"), *Args[0], *Property->GetName(), *Text, Count);
		}));

	FAutoConsoleCommandWithWorldAndArgs KitResetCommand(
		TEXT("space.KitReset"),
		TEXT("space.KitReset: the interior's materials and lights, the sun and the sky light back to what the level has."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			int32 Materials = 0;
			for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
			{
				UStaticMeshComponent* Mesh = It->ActorHasTag(InteriorTag) ? It->GetStaticMeshComponent() : nullptr;
				for (int32 Index = 0; Mesh && Index < Mesh->GetNumMaterials(); ++Index)
				{
					if (UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Mesh->GetMaterial(Index)))
					{
						Mesh->SetMaterial(Index, Dynamic->Parent);
						++Materials;
					}
				}
			}
			// The sun and the sky light are remembered the first time round, so that a variant with
			// them off (space.Sun Intensity 0) does not leak into the next one.
			for (TActorIterator<ADirectionalLight> It(World); It; ++It)
			{
				Remember(It->GetComponentByClass<UDirectionalLightComponent>());
			}
			for (TActorIterator<ASkyLight> It(World); It; ++It)
			{
				Remember(It->GetComponentByClass<USkyLightComponent>());
			}
			for (UPointLightComponent* Light : InteriorLights(World, TEXT("All")))
			{
				Remember(Light);
			}
			int32 Lights = 0;
			for (const TPair<TWeakObjectPtr<ULightComponentBase>, FLightDefaults>& Saved : SavedLights)
			{
				if (ULightComponentBase* Light = Saved.Key.Get())
				{
					Restore(Light, Saved.Value);
					++Lights;
				}
			}
			for (TActorIterator<ASkyLight> It(World); It; ++It)
			{
				if (USkyLightComponent* Sky = It->GetComponentByClass<USkyLightComponent>())
				{
					Sky->RecaptureSky();
				}
			}
			UE_LOG(LogTemp, Display, TEXT("space.KitReset: %d materials, %d lights"), Materials, Lights);
		}));
}
