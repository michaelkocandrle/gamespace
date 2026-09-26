// Ship interior lighting variants at runtime, for measuring what a dense interior light set costs
// (author 26. 9. 2026: density close to the C2 at <= ~2 ms). Nothing is saved.
//
//   space.FixLights -1|0|1            fixture lights (Light_fix_*, hs_fixture_lights.py): automatic (on only
//                                     with the camera inside the ship), forced off, forced on
//   space.ShipLightShadows 0|1 [fix|int|all]   cast shadows on the ship's interior lights (default all)
//   space.ShipLightRadius <scale> [fix|int|all] attenuation radius x scale of the imported value
//   space.IntEmissive <scale>         emissive strength x scale on the interior's lamp, glow strip and
//                                     accent line materials (Lumen then lights the room from them)
//   space.ShipLightList               counts of the ship's interior lights (visible, shadowed)
// MegaLights is switched with the engine's own r.MegaLights.EnableForProject 0|1 (read every frame).

#include "SpaceshipPawn.h"

#include "Components/LocalLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"
#include "Materials/MaterialInstanceDynamic.h"

DEFINE_LOG_CATEGORY_STATIC(LogSpaceShipLights, Log, All);

namespace
{
	/** "fix" = Light_fix_* (fixture lights), "int" = Light_int_* (room and cockpit lights), "all" = both. */
	bool Matches(const ULocalLightComponent* Light, const FString& Which)
	{
		const FString Name = Light->GetName();
		const bool bFix = Name.StartsWith(TEXT("Light_fix_"));
		const bool bInt = Name.StartsWith(TEXT("Light_int_"));
		return Which == TEXT("fix") ? bFix : Which == TEXT("int") ? bInt : (bFix || bInt);
	}

	template <typename Fn>
	int32 ForEachShipLight(UWorld* World, const FString& Which, Fn&& Do)
	{
		int32 Count = 0;
		for (TActorIterator<ASpaceshipPawn> It(World); It; ++It)
		{
			TArray<ULocalLightComponent*> Lights;
			It->GetComponents<ULocalLightComponent>(Lights);
			for (ULocalLightComponent* Light : Lights)
			{
				if (Matches(Light, Which))
				{
					Do(*It, Light);
					++Count;
				}
			}
		}
		return Count;
	}

	FAutoConsoleCommandWithWorldAndArgs FixLightsCommand(
		TEXT("space.FixLights"),
		TEXT("space.FixLights -1|0|1: fixture lights automatic (camera inside), forced off, forced on."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			const int32 Mode = Args.Num() > 0 ? FCString::Atoi(*Args[0]) : -1;
			for (TActorIterator<ASpaceshipPawn> It(World); It; ++It)
			{
				It->DebugSetFixtureLightMode(Mode);
			}
			UE_LOG(LogSpaceShipLights, Display, TEXT("space.FixLights %d"), Mode);
		}));

	FAutoConsoleCommandWithWorldAndArgs ShadowsCommand(
		TEXT("space.ShipLightShadows"),
		TEXT("space.ShipLightShadows 0|1 [fix|int|all]: cast shadows on the ship's interior lights."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			const bool bOn = Args.Num() > 0 && FCString::Atoi(*Args[0]) != 0;
			const FString Which = Args.Num() > 1 ? Args[1] : FString(TEXT("all"));
			const int32 Count = ForEachShipLight(World, Which, [bOn](ASpaceshipPawn*, ULocalLightComponent* Light)
			{
				Light->SetCastShadows(bOn);
			});
			UE_LOG(LogSpaceShipLights, Display, TEXT("space.ShipLightShadows %d on %d %s lights"), bOn ? 1 : 0, Count, *Which);
		}));

	FAutoConsoleCommandWithWorldAndArgs RadiusCommand(
		TEXT("space.ShipLightRadius"),
		TEXT("space.ShipLightRadius <scale> [fix|int|all]: attenuation radius x scale of the imported value."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			const float Scale = Args.Num() > 0 ? FCString::Atof(*Args[0]) : 1.f;
			const FString Which = Args.Num() > 1 ? Args[1] : FString(TEXT("all"));
			const int32 Count = ForEachShipLight(World, Which, [Scale](ASpaceshipPawn*, ULocalLightComponent* Light)
			{
				const ULocalLightComponent* Default = Cast<ULocalLightComponent>(Light->GetArchetype());
				const float Base = Default ? Default->AttenuationRadius : Light->AttenuationRadius;
				Light->SetAttenuationRadius(Base * Scale);
			});
			UE_LOG(LogSpaceShipLights, Display, TEXT("space.ShipLightRadius %.2f on %d %s lights"), Scale, Count, *Which);
		}));

	FAutoConsoleCommandWithWorldAndArgs EmissiveCommand(
		TEXT("space.IntEmissive"),
		TEXT("space.IntEmissive <scale>: emissive strength x scale on the interior's lamp, glow strip and accent materials."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			const float Scale = Args.Num() > 0 ? FCString::Atof(*Args[0]) : 1.f;
			int32 Count = 0;
			for (TActorIterator<ASpaceshipPawn> It(World); It; ++It)
			{
				TArray<UStaticMeshComponent*> Meshes;
				It->GetComponents<UStaticMeshComponent>(Meshes);
				for (UStaticMeshComponent* Mesh : Meshes)
				{
					if (!Mesh->GetName().StartsWith(TEXT("Interior")))
					{
						continue;
					}
					for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
					{
						UMaterialInterface* Material = Mesh->GetMaterial(Slot);
						UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Material);
						UMaterialInterface* Source = Dynamic ? Dynamic->Parent.Get() : Material;
						const FString Name = Source ? Source->GetName() : FString();
						if (!(Name.Contains(TEXT("IntLight")) || Name.Contains(TEXT("IntGlow")) || Name.Contains(TEXT("IntAccentGlow"))))
						{
							continue;
						}
						float Base = 0.f;
						if (!Source->GetScalarParameterValue(TEXT("EmissiveStrength"), Base))
						{
							continue;
						}
						if (!Dynamic)
						{
							Dynamic = Mesh->CreateDynamicMaterialInstance(Slot, Source);
						}
						Dynamic->SetScalarParameterValue(TEXT("EmissiveStrength"), Base * Scale);
						++Count;
					}
				}
			}
			UE_LOG(LogSpaceShipLights, Display, TEXT("space.IntEmissive %.2f on %d material slots"), Scale, Count);
		}));

	FAutoConsoleCommandWithWorldAndArgs ListCommand(
		TEXT("space.ShipLightList"),
		TEXT("space.ShipLightList: the ship's interior lights (fix / int, visible, shadowed)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			int32 Counts[2][3] = {};
			for (int32 k = 0; k < 2; ++k)
			{
				ForEachShipLight(World, k == 0 ? FString(TEXT("fix")) : FString(TEXT("int")), [&Counts, k](ASpaceshipPawn*, ULocalLightComponent* Light)
				{
					++Counts[k][0];
					Counts[k][1] += Light->IsVisible() ? 1 : 0;
					Counts[k][2] += Light->CastShadows ? 1 : 0;
				});
			}
			UE_LOG(LogSpaceShipLights, Display, TEXT("SHIPLIGHTS fix %d (visible %d, shadows %d), int %d (visible %d, shadows %d)"),
				Counts[0][0], Counts[0][1], Counts[0][2], Counts[1][0], Counts[1][1], Counts[1][2]);
		}));
}
