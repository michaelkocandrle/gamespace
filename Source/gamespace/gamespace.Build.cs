// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class gamespace : ModuleRules
{
	public gamespace(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
	
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput" });

		PrivateDependencyModuleNames.AddRange(new string[] { "ProceduralMeshComponent", "AnimationCore" });

		// Menus (SSpaceMenu) are plain Slate; the flight HUD (USpaceFlightHud) is UMG.
		PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore", "UMG" });
		
		// Uncomment if you are using online features
		// PrivateDependencyModuleNames.Add("OnlineSubsystem");

		// To include OnlineSubsystemSteam, add it to the plugins section in your uproject file with the Enabled attribute set to true
	}
}
