// Copyright Epic Games, Inc. All Rights Reserved.

/**
 * The look of the scene, tuned in the running game instead of through the editor and a repackage.
 * Post process settings and the two lights are reachable by name through the reflection data, so
 * there is nothing to keep in sync here when Epic adds a setting:
 *
 *   space.PostList bloom             what the level has, and whether it overrides it
 *   space.Post BloomIntensity 0.4    override one setting (colours too: space.Post ColorGain 1 .98 .95)
 *   space.Sun ContactShadowLength .05    a property of the directional light
 *   space.Sky Intensity 0.6              a property of the sky light
 *   space.LightList sun shadow       what those two take
 *   space.PostDump                   every override, as lines for Tools/Assets/build_space_scene.py
 *
 * Nothing here is saved. What looks right goes into Tools/Assets/build_space_scene.py, which writes
 * it into the level (Docs/WORKFLOW.md, the look loop).
 */

#include "CoreMinimal.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/Scene.h"
#include "Engine/SkyLight.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"
#include "UObject/UnrealType.h"

namespace
{
	/** The volume that covers the whole level: PP_SpaceExposure, built by Tools/Assets/build_space_scene.py. */
	APostProcessVolume* FindUnboundVolume(UWorld* World)
	{
		APostProcessVolume* Any = nullptr;
		for (TActorIterator<APostProcessVolume> It(World); It; ++It)
		{
			if (It->bUnbound)
			{
				return *It;
			}
			Any = *It;
		}
		return Any;
	}

	FProperty* FindByName(UStruct* Struct, const FString& Name)
	{
		for (TFieldIterator<FProperty> It(Struct); It; ++It)
		{
			if (It->GetName().Equals(Name, ESearchCase::IgnoreCase))
			{
				return *It;
			}
		}
		return nullptr;
	}

	/** The bOverride_ flag that turns a post process setting on. Only FPostProcessSettings has these. */
	FBoolProperty* FindOverride(UStruct* Struct, const FString& Name)
	{
		return FindFProperty<FBoolProperty>(Struct, *(FString(TEXT("bOverride_")) + Name));
	}

	FString ValueToText(const FProperty* Property, const void* Container)
	{
		FString Text;
		Property->ExportTextItem_Direct(Text, Property->ContainerPtrToValuePtr<void>(Container), nullptr, nullptr, PPF_None);
		return Text;
	}

	/**
	 * The words after the name, as text the property can import. Several bare numbers are a colour or
	 * a vector written the short way (1 0.98 0.95); colours are named R, G, B on purpose, because
	 * FColor declares its bytes in the order B, G, R and the generic path would read them that way.
	 */
	FString ArgsToText(const FProperty* Property, const TArray<FString>& Args, int32 First)
	{
		const FStructProperty* Struct = CastField<FStructProperty>(Property);
		const int32 Count = Args.Num() - First;
		if (Struct && Count > 1 && !Args[First].StartsWith(TEXT("(")))
		{
			const bool bColour = Struct->Struct == TBaseStructure<FLinearColor>::Get() || Struct->Struct == TBaseStructure<FColor>::Get();
			FString Text = TEXT("(");
			int32 Index = First;
			if (bColour)
			{
				const TCHAR* Names[] = { TEXT("R"), TEXT("G"), TEXT("B"), TEXT("A") };
				for (int32 i = 0; i < 4 && Index < Args.Num(); ++i, ++Index)
				{
					Text += FString::Printf(TEXT("%s%s=%s"), i > 0 ? TEXT(",") : TEXT(""), Names[i], *Args[Index]);
				}
			}
			else
			{
				int32 i = 0;
				for (TFieldIterator<FProperty> It(Struct->Struct); It && Index < Args.Num(); ++It, ++i, ++Index)
				{
					Text += FString::Printf(TEXT("%s%s=%s"), i > 0 ? TEXT(",") : TEXT(""), *It->GetName(), *Args[Index]);
				}
			}
			return Text + TEXT(")");
		}
		return FString::Join(TArrayView<const FString>(Args.GetData() + First, Count), TEXT(" "));
	}

	/** Writes one property by name. Returns what it now reads as, or an empty string if it did not take. */
	FString SetByName(UStruct* Struct, void* Container, const TArray<FString>& Args, int32 First)
	{
		FProperty* Property = FindByName(Struct, Args[First - 1]);
		if (!Property)
		{
			return FString();
		}
		const FString Text = ArgsToText(Property, Args, First);
		if (!Property->ImportText_Direct(*Text, Property->ContainerPtrToValuePtr<void>(Container), nullptr, PPF_None))
		{
			UE_LOG(LogTemp, Warning, TEXT("%s does not take %s"), *Property->GetName(), *Text);
			return FString();
		}
		if (FBoolProperty* Override = FindOverride(Struct, Property->GetName()))
		{
			Override->SetPropertyValue_InContainer(Container, true);
		}
		return FString::Printf(TEXT("%s = %s"), *Property->GetName(), *ValueToText(Property, Container));
	}

	void ListProperties(UStruct* Struct, const void* Container, const FString& Filter)
	{
		int32 Shown = 0;
		for (TFieldIterator<FProperty> It(Struct); It; ++It)
		{
			const FString Name = It->GetName();
			if (Name.StartsWith(TEXT("bOverride_")) || (!Filter.IsEmpty() && !Name.Contains(Filter)))
			{
				continue;
			}
			FBoolProperty* Override = FindOverride(Struct, Name);
			const bool bOn = Override && Override->GetPropertyValue_InContainer(Container);
			UE_LOG(LogTemp, Display, TEXT("  %s %s = %s"), bOn ? TEXT("[x]") : TEXT("[ ]"), *Name, *ValueToText(*It, Container));
			++Shown;
		}
		UE_LOG(LogTemp, Display, TEXT("%d properties matching \"%s\" ([x] = overridden here)"), Shown, *Filter);
	}

	/** BloomIntensity -> bloom_intensity: the same setting as Tools/Assets/build_space_scene.py names it. */
	FString ToPythonName(const FString& Name)
	{
		FString Out;
		for (int32 i = 0; i < Name.Len(); ++i)
		{
			if (i > 0 && FChar::IsUpper(Name[i]) && !FChar::IsUpper(Name[i - 1]))
			{
				Out += TEXT('_');
			}
			Out += FChar::ToLower(Name[i]);
		}
		return Out;
	}

	/** Every light component of that class in the level, so a change reaches all of them. */
	template <typename TComponent, typename TActor>
	int32 ForEachLight(UWorld* World, TFunctionRef<void(TComponent*)> Work)
	{
		int32 Count = 0;
		for (TActorIterator<TActor> It(World); It; ++It)
		{
			if (TComponent* Component = It->template GetComponentByClass<TComponent>())
			{
				Work(Component);
				Component->MarkRenderStateDirty();
				++Count;
			}
		}
		return Count;
	}

	FAutoConsoleCommandWithWorldAndArgs PostCommand(
		TEXT("space.Post"),
		TEXT("space.Post <Setting> <Value...>: override one post process setting of the level's unbound volume (BloomIntensity 0.4, ColorGain 1 0.98 0.95). Not saved."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			APostProcessVolume* Volume = FindUnboundVolume(World);
			if (!Volume || Args.Num() < 2)
			{
				UE_LOG(LogTemp, Display, TEXT("space.Post <Setting> <Value...>%s"),
					Volume ? TEXT("") : TEXT(" (no post process volume in this level)"));
				return;
			}
			const FString Result = SetByName(FPostProcessSettings::StaticStruct(), &Volume->Settings, Args, 1);
			UE_LOG(LogTemp, Display, TEXT("space.Post %s"), Result.IsEmpty() ? *FString::Printf(TEXT("%s: no such setting (space.PostList %s)"), *Args[0], *Args[0]) : *Result);
		}));

	FAutoConsoleCommandWithWorldAndArgs PostListCommand(
		TEXT("space.PostList"),
		TEXT("space.PostList <part of a name>: post process settings whose name contains it, with their value in this level."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (APostProcessVolume* Volume = FindUnboundVolume(World))
			{
				ListProperties(FPostProcessSettings::StaticStruct(), &Volume->Settings, Args.Num() > 0 ? Args[0] : FString());
			}
		}));

	FAutoConsoleCommandWithWorldAndArgs PostDumpCommand(
		TEXT("space.PostDump"),
		TEXT("space.PostDump: every overridden post process setting, as lines to paste into POST_SETTINGS in Tools/Assets/build_space_scene.py."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			APostProcessVolume* Volume = FindUnboundVolume(World);
			if (!Volume)
			{
				return;
			}
			const FPostProcessSettings& Settings = Volume->Settings;
			UE_LOG(LogTemp, Display, TEXT("POST_SETTINGS = ["));
			for (TFieldIterator<FProperty> It(FPostProcessSettings::StaticStruct()); It; ++It)
			{
				const FString Name = It->GetName();
				FBoolProperty* Override = FindOverride(FPostProcessSettings::StaticStruct(), Name);
				if (Name.StartsWith(TEXT("bOverride_")) || !Override || !Override->GetPropertyValue_InContainer(&Settings))
				{
					continue;
				}
				UE_LOG(LogTemp, Display, TEXT("    (\"%s\", %s),"), *ToPythonName(Name), *ValueToText(*It, &Settings));
			}
			UE_LOG(LogTemp, Display, TEXT("]"));
		}));

	FAutoConsoleCommandWithWorldAndArgs SunCommand(
		TEXT("space.Sun"),
		TEXT("space.Sun <Property> <Value...>: a property of the level's directional light (Intensity, ContactShadowLength, SpecularScale, LightSourceAngle). Not saved."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (Args.Num() < 2)
			{
				UE_LOG(LogTemp, Display, TEXT("space.Sun <Property> <Value...> (space.LightList sun <part of a name>)"));
				return;
			}
			FString Result;
			const int32 Count = ForEachLight<UDirectionalLightComponent, ADirectionalLight>(World, [&Args, &Result](UDirectionalLightComponent* Light)
			{
				Result = SetByName(Light->GetClass(), Light, Args, 1);
			});
			UE_LOG(LogTemp, Display, TEXT("space.Sun %s on %d lights"),
				Result.IsEmpty() ? *FString::Printf(TEXT("%s: no such property"), *Args[0]) : *Result, Count);
		}));

	FAutoConsoleCommandWithWorldAndArgs SunDirCommand(
		TEXT("space.SunDir"),
		TEXT("space.SunDir <Pitch> <Yaw>: where the sun stands, degrees (the level is built with -39 45). Not saved."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (Args.Num() < 2)
			{
				UE_LOG(LogTemp, Display, TEXT("space.SunDir <Pitch> <Yaw>"));
				return;
			}
			// Named arguments on purpose: FRotator's positional order is pitch, yaw, roll, and the
			// Python side of the project writes it the other way round (Docs/WORKFLOW.md, 9.4).
			const FRotator Rotation(FCString::Atof(*Args[0]), FCString::Atof(*Args[1]), 0.f);
			int32 Count = 0;
			for (TActorIterator<ADirectionalLight> It(World); It; ++It)
			{
				It->SetActorRotation(Rotation);
				++Count;
			}
			UE_LOG(LogTemp, Display, TEXT("space.SunDir pitch %.1f yaw %.1f on %d lights"), Rotation.Pitch, Rotation.Yaw, Count);
		}));

	FAutoConsoleCommandWithWorldAndArgs SkyCommand(
		TEXT("space.Sky"),
		TEXT("space.Sky <Property> <Value...>: a property of the level's sky light (Intensity, CubemapResolution, OcclusionMaxDistance). Not saved."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (Args.Num() < 2)
			{
				UE_LOG(LogTemp, Display, TEXT("space.Sky <Property> <Value...> (space.LightList sky <part of a name>)"));
				return;
			}
			FString Result;
			const int32 Count = ForEachLight<USkyLightComponent, ASkyLight>(World, [&Args, &Result](USkyLightComponent* Light)
			{
				Result = SetByName(Light->GetClass(), Light, Args, 1);
				Light->RecaptureSky();
			});
			UE_LOG(LogTemp, Display, TEXT("space.Sky %s on %d lights"),
				Result.IsEmpty() ? *FString::Printf(TEXT("%s: no such property"), *Args[0]) : *Result, Count);
		}));

	FAutoConsoleCommandWithWorldAndArgs LightListCommand(
		TEXT("space.LightList"),
		TEXT("space.LightList sun|sky <part of a name>: what space.Sun and space.Sky take, with their value in this level."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			const FString Which = Args.Num() > 0 ? Args[0] : TEXT("sun");
			const FString Filter = Args.Num() > 1 ? Args[1] : FString();
			if (Which.Equals(TEXT("sky"), ESearchCase::IgnoreCase))
			{
				ForEachLight<USkyLightComponent, ASkyLight>(World, [&Filter](USkyLightComponent* Light)
				{
					ListProperties(Light->GetClass(), Light, Filter);
				});
			}
			else
			{
				ForEachLight<UDirectionalLightComponent, ADirectionalLight>(World, [&Filter](UDirectionalLightComponent* Light)
				{
					ListProperties(Light->GetClass(), Light, Filter);
				});
			}
		}));
}
