// Copyright Epic Games, Inc. All Rights Reserved.

#include "PlayerCharacterAnimInstance.h"

#include "Animation/AnimNodeBase.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimationPoseData.h"
#include "Animation/BlendSpace.h"
#include "AnimationRuntime.h"
#include "BonePose.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "QuadSpherePlanet.h"
#include "TwoBoneIK.h"
#include "UObject/ConstructorHelpers.h"

namespace PlayerAnimDefaults
{
	const TCHAR* const Idle = TEXT("/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle.MM_Idle");
	const TCHAR* const Walk = TEXT("/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd.MF_Unarmed_Walk_Fwd");
	const TCHAR* const Jog = TEXT("/Game/Characters/Mannequins/Anims/Unarmed/Jog/MF_Unarmed_Jog_Fwd.MF_Unarmed_Jog_Fwd");
	const TCHAR* const Jump = TEXT("/Game/Characters/Mannequins/Anims/Unarmed/Jump/MM_Jump.MM_Jump");
	const TCHAR* const Fall = TEXT("/Game/Characters/Mannequins/Anims/Unarmed/Jump/MM_Fall_Loop.MM_Fall_Loop");
	const TCHAR* const Land = TEXT("/Game/Characters/Mannequins/Anims/Unarmed/Jump/MM_Land.MM_Land");
	const TCHAR* const SpeedBlendSpace = TEXT("/Game/Characters/Mannequins/Anims/Unarmed/BS_Idle_Walk_Run.BS_Idle_Walk_Run");

	/** Seconds a landing animation blends over the locomotion. */
	constexpr double LandBlendSeconds = 0.35;
	/** Air time below which a touchdown is a step, not a landing. */
	constexpr double MinAirTimeForLanding = 0.3;


	/** Speed of Sequence on the blend space's "Speed" axis, or 0. Prefers the forward sample. */
	float SpeedFromBlendSpace(const UBlendSpace* BlendSpace, const UAnimSequence* Sequence)
	{
		if (!BlendSpace || !Sequence)
		{
			return 0.f;
		}
		int32 SpeedAxis = 0;
		for (int32 Axis = 0; Axis < 2; ++Axis)
		{
			if (BlendSpace->GetBlendParameter(Axis).DisplayName.Contains(TEXT("Speed")))
			{
				SpeedAxis = Axis;
			}
		}
		const int32 OtherAxis = 1 - SpeedAxis;
		float Best = 0.f;
		double BestOther = TNumericLimits<double>::Max();
		for (const FBlendSample& Sample : BlendSpace->GetBlendSamples())
		{
			if (Sample.Animation == Sequence && FMath::Abs(Sample.SampleValue[OtherAxis]) < BestOther)
			{
				BestOther = FMath::Abs(Sample.SampleValue[OtherAxis]);
				Best = float(FMath::Abs(Sample.SampleValue[SpeedAxis]));
			}
		}
		return Best;
	}

	void SamplePose(const UAnimSequence* Sequence, double Time, bool bLoop, FPoseContext& Into)
	{
		const double Length = FMath::Max(double(Sequence->GetPlayLength()), 1e-3);
		const double SampleTime = bLoop ? FMath::Fmod(FMath::Max(Time, 0.0), Length) : FMath::Clamp(Time, 0.0, Length);
		FAnimationPoseData PoseData(Into);
		Sequence->GetAnimationPose(PoseData, FAnimExtractContext(SampleTime, false, {}, bLoop));
	}

	/** Blends Other into InOut: InOut keeps (1 - OtherWeight). */
	void BlendInto(FPoseContext& InOut, FPoseContext& Other, float OtherWeight)
	{
		FAnimationPoseData Base(InOut);
		const FAnimationPoseData Blend(Other);
		FAnimationRuntime::BlendTwoPosesTogetherInPlace(Base, Blend, 1.f - OtherWeight);
	}
}

// -------------------------------------------------------------------------------------------
// Instance
// -------------------------------------------------------------------------------------------

UPlayerCharacterAnimInstance::UPlayerCharacterAnimInstance()
{
	// Every instance must set these: a native class does not copy its properties from the class
	// default object, it relies on the constructor. Static finders load each asset only once.
	static ConstructorHelpers::FObjectFinderOptional<UAnimSequence> IdleFinder(PlayerAnimDefaults::Idle);
	static ConstructorHelpers::FObjectFinderOptional<UAnimSequence> WalkFinder(PlayerAnimDefaults::Walk);
	static ConstructorHelpers::FObjectFinderOptional<UAnimSequence> JogFinder(PlayerAnimDefaults::Jog);
	static ConstructorHelpers::FObjectFinderOptional<UAnimSequence> JumpFinder(PlayerAnimDefaults::Jump);
	static ConstructorHelpers::FObjectFinderOptional<UAnimSequence> FallFinder(PlayerAnimDefaults::Fall);
	static ConstructorHelpers::FObjectFinderOptional<UAnimSequence> LandFinder(PlayerAnimDefaults::Land);
	static ConstructorHelpers::FObjectFinderOptional<UBlendSpace> SpeedFinder(PlayerAnimDefaults::SpeedBlendSpace);
	IdleAnimation = IdleFinder.Get();
	WalkAnimation = WalkFinder.Get();
	JogAnimation = JogFinder.Get();
	JumpAnimation = JumpFinder.Get();
	FallLoopAnimation = FallFinder.Get();
	LandAnimation = LandFinder.Get();
	SpeedReferenceBlendSpace = SpeedFinder.Get();
}

FVector2D UPlayerCharacterAnimInstance::GetLocomotionReferenceSpeeds() const
{
	const float Walk = PlayerAnimDefaults::SpeedFromBlendSpace(SpeedReferenceBlendSpace, WalkAnimation);
	const float Jog = PlayerAnimDefaults::SpeedFromBlendSpace(SpeedReferenceBlendSpace, JogAnimation);
	return FVector2D(Walk > 1.f ? Walk : FallbackWalkSpeed, Jog > 1.f ? Jog : FallbackJogSpeed);
}

void UPlayerCharacterAnimInstance::SetDebugOverride(bool bEnable, float GroundSpeed, bool bFalling, bool bOverrideGround, float LeftGroundCm, float RightGroundCm)
{
	bDebugOverride = bEnable;
	DebugGroundSpeed = GroundSpeed;
	bDebugFalling = bFalling;
	bDebugOverrideGround = bOverrideGround;
	DebugLeftGroundCm = LeftGroundCm;
	DebugRightGroundCm = RightGroundCm;
}

FAnimInstanceProxy* UPlayerCharacterAnimInstance::CreateAnimInstanceProxy()
{
	return new FPlayerCharacterAnimProxy(this);
}

void UPlayerCharacterAnimInstance::DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy)
{
	delete static_cast<FPlayerCharacterAnimProxy*>(InProxy);
}

// -------------------------------------------------------------------------------------------
// Proxy: game thread
// -------------------------------------------------------------------------------------------

void FPlayerCharacterAnimProxy::Initialize(UAnimInstance* InAnimInstance)
{
	FAnimInstanceProxy::Initialize(InAnimInstance);
	const UPlayerCharacterAnimInstance* Instance = CastChecked<UPlayerCharacterAnimInstance>(InAnimInstance);
	const FVector2D Speeds = Instance->GetLocomotionReferenceSpeeds();
	WalkSpeed = float(Speeds.X);
	JogSpeed = FMath::Max(float(Speeds.Y), WalkSpeed + 1.f);
}

void FPlayerCharacterAnimProxy::PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds)
{
	FAnimInstanceProxy::PreUpdate(InAnimInstance, DeltaSeconds);
	UPlayerCharacterAnimInstance* Instance = CastChecked<UPlayerCharacterAnimInstance>(InAnimInstance);

	// The anim thread is idle while PreUpdate runs, so this is the safe moment to hand results back.
	Instance->FootIKReadout = LastFootIK;
	Instance->ProxyCounters = FIntVector(++PreUpdateCount, UpdateCount, EvaluateCount);

	Idle = Instance->IdleAnimation;
	Walk = Instance->WalkAnimation;
	Jog = Instance->JogAnimation;
	Jump = Instance->JumpAnimation;
	Fall = Instance->FallLoopAnimation;
	Land = Instance->LandAnimation;
	bFootIK = Instance->bEnableFootIK;
	MaxPelvisDrop = Instance->MaxPelvisDropCm;
	MaxPelvisRaise = Instance->MaxPelvisRaiseCm;
	MaxFootOffset = Instance->MaxFootOffsetCm;
	MaxFootTilt = Instance->MaxFootTiltDeg;
	IKInterpSpeed = Instance->FootIKInterpSpeed;

	GroundSpeed = 0.f;
	VerticalSpeed = 0.f;
	bFalling = false;
	bTerrainValid = false;
	bGroundOverride = false;

	if (const USkeletalMeshComponent* Mesh = GetSkelMeshComponent())
	{
		ComponentToWorld = Mesh->GetComponentTransform();
	}

	const ACharacter* Character = Cast<ACharacter>(Instance->TryGetPawnOwner());
	if (const UCharacterMovementComponent* Movement = Character ? Character->GetCharacterMovement() : nullptr)
	{
		// Speeds in the character's own frame: world XY is meaningless on a round planet.
		const FVector Up = -Movement->GetGravityDirection();
		const FVector Velocity = Movement->Velocity;
		GroundSpeed = float(FVector::VectorPlaneProject(Velocity, Up).Size());
		VerticalSpeed = float(Velocity | Up);
		bFalling = Movement->IsFalling();

		const FFindFloorResult& Floor = Movement->CurrentFloor;
		if (Movement->IsMovingOnGround() && Floor.bBlockingHit)
		{
			if (const AQuadSpherePlanet* Planet = Cast<AQuadSpherePlanet>(Floor.HitResult.GetActor()))
			{
				Terrain = Planet->GetTerrainSettings();
				PlanetToWorld = Planet->GetActorTransform();
				bTerrainValid = true;
			}
		}
	}

	if (Instance->bDebugOverride)
	{
		GroundSpeed = Instance->DebugGroundSpeed;
		bFalling = Instance->bDebugFalling;
		VerticalSpeed = bFalling ? 200.f : 0.f;
		bGroundOverride = Instance->bDebugOverrideGround && !bFalling;
		OverrideLeftGround = Instance->DebugLeftGroundCm;
		OverrideRightGround = Instance->DebugRightGroundCm;
	}
}

// -------------------------------------------------------------------------------------------
// Proxy: anim thread
// -------------------------------------------------------------------------------------------

void FPlayerCharacterAnimProxy::Update(float DeltaSeconds)
{
	FAnimInstanceProxy::Update(DeltaSeconds);
	++UpdateCount;
	DeltaTime = DeltaSeconds;
	IdleTime += DeltaSeconds;

	// Idle -> walk below walking speed, walk -> jog above it, jog sped up beyond.
	const float TargetMove = FMath::Clamp(GroundSpeed / FMath::Max(WalkSpeed, 1.f), 0.f, 1.f);
	const float TargetJog = FMath::Clamp((GroundSpeed - WalkSpeed) / FMath::Max(JogSpeed - WalkSpeed, 1.f), 0.f, 1.f);
	const float Smooth = 1.f - FMath::Exp(-10.f * DeltaSeconds);
	MoveBlend += (TargetMove - MoveBlend) * Smooth;
	JogAlpha += (TargetJog - JogAlpha) * Smooth;

	if (Walk && Jog)
	{
		// One phase for both cycles keeps the feet in step while blending; the rate makes the
		// feet travel at the ground speed, so they do not slide.
		const double CycleLength = FMath::Lerp(double(Walk->GetPlayLength()), double(Jog->GetPlayLength()), double(JogAlpha));
		const double ReferenceSpeed = FMath::Lerp(double(WalkSpeed), double(JogSpeed), double(JogAlpha));
		const double PlayRate = FMath::Max(double(GroundSpeed), 0.4 * WalkSpeed) / FMath::Max(ReferenceSpeed, 1.0);
		Phase = FMath::Frac(Phase + DeltaSeconds * PlayRate / FMath::Max(CycleLength, 1e-3));
	}

	if (bFalling)
	{
		if (!bWasFalling)
		{
			AirTime = 0.0;
			bJumpStart = VerticalSpeed > 50.f;
		}
		AirTime += DeltaSeconds;
	}
	else
	{
		if (bWasFalling)
		{
			LandTime = 0.0;
			bLanding = AirTime > PlayerAnimDefaults::MinAirTimeForLanding;
		}
		LandTime += DeltaSeconds;
	}
	bWasFalling = bFalling;
	AirBlend += ((bFalling ? 1.f : 0.f) - AirBlend) * (1.f - FMath::Exp(-14.f * DeltaSeconds));
}

bool FPlayerCharacterAnimProxy::Evaluate(FPoseContext& Output)
{
	using namespace PlayerAnimDefaults;
	++EvaluateCount;
	if (!Idle)
	{
		return false;  // reference pose; the Mannequin pack is missing
	}

	SamplePose(Idle, IdleTime, true, Output);

	if (MoveBlend > 0.001f && Walk && Jog)
	{
		FPoseContext Move(this);
		SamplePose(Walk, Phase * Walk->GetPlayLength(), true, Move);
		if (JogAlpha > 0.001f)
		{
			FPoseContext JogPose(this);
			SamplePose(Jog, Phase * Jog->GetPlayLength(), true, JogPose);
			BlendInto(Move, JogPose, JogAlpha);
		}
		BlendInto(Output, Move, MoveBlend);
	}

	if (AirBlend > 0.001f && Fall)
	{
		FPoseContext Air(this);
		if (bJumpStart && Jump && AirTime < Jump->GetPlayLength())
		{
			SamplePose(Jump, AirTime, false, Air);
		}
		else
		{
			SamplePose(Fall, AirTime, true, Air);
		}
		BlendInto(Output, Air, AirBlend);
	}

	if (bLanding && Land && !bFalling && LandTime < LandBlendSeconds)
	{
		FPoseContext Landing(this);
		SamplePose(Land, LandTime, false, Landing);
		BlendInto(Output, Landing, 0.8f * float(1.0 - LandTime / LandBlendSeconds));
	}

	Output.Pose.NormalizeRotations();
	ApplyFootIK(Output);
	return true;
}

bool FPlayerCharacterAnimProxy::GroundUnderFoot(const FVector& FootComponent, float& OutGroundZ, FVector& OutNormalComponent) const
{
	if (!bTerrainValid)
	{
		return false;
	}
	// Straight from the height field, like the visible terrain mesh.
	const FVector FootWorld = ComponentToWorld.TransformPosition(FootComponent);
	const FVector Direction = PlanetToWorld.InverseTransformPositionNoScale(FootWorld).GetSafeNormal();
	const FVector SurfaceWorld = PlanetToWorld.TransformPositionNoScale(PlanetTerrain::SurfacePoint(Terrain, Direction));
	const FVector NormalWorld = PlanetToWorld.TransformVectorNoScale(PlanetTerrain::SurfaceNormal(Terrain, Direction));
	OutGroundZ = float(ComponentToWorld.InverseTransformPosition(SurfaceWorld).Z);
	OutNormalComponent = ComponentToWorld.InverseTransformVector(NormalWorld).GetSafeNormal();
	return true;
}

void FPlayerCharacterAnimProxy::ApplyFootIK(FPoseContext& Output)
{
	FFootIKState State;
	const FBoneContainer& Bones = Output.Pose.GetBoneContainer();
	auto Index = [&Bones](const TCHAR* Name)
	{
		const int32 MeshIndex = Bones.GetPoseBoneIndexForBoneName(FName(Name));
		return MeshIndex == INDEX_NONE ? FCompactPoseBoneIndex(INDEX_NONE) : Bones.MakeCompactPoseIndex(FMeshPoseBoneIndex(MeshIndex));
	};
	const FCompactPoseBoneIndex Pelvis = Index(TEXT("pelvis"));
	const FCompactPoseBoneIndex Legs[2][3] = {
		{ Index(TEXT("thigh_l")), Index(TEXT("calf_l")), Index(TEXT("foot_l")) },
		{ Index(TEXT("thigh_r")), Index(TEXT("calf_r")), Index(TEXT("foot_r")) },
	};
	if (!Pelvis.IsValid() || !Legs[0][2].IsValid() || !Legs[1][2].IsValid() || !Legs[0][0].IsValid() || !Legs[1][0].IsValid())
	{
		LastFootIK = State;
		return;
	}

	FCSPose<FCompactPose> Pose;
	Pose.InitPose(Output.Pose);

	// Targets: ground height under each foot relative to the capsule floor (component Z = 0),
	// clamped. No ground (in the air, on a ship, IK off): ease back to the animation.
	const bool bGround = bFootIK && AirBlend < 0.5f && (bGroundOverride || bTerrainValid);
	float Target[2] = { 0.f, 0.f };
	FVector Normal[2] = { FVector::UpVector, FVector::UpVector };
	FVector AnimatedFoot[2];
	for (int32 Side = 0; Side < 2; ++Side)
	{
		AnimatedFoot[Side] = Pose.GetComponentSpaceTransform(Legs[Side][2]).GetLocation();
		if (!bGround)
		{
			continue;
		}
		float GroundZ = 0.f;
		if (bGroundOverride)
		{
			GroundZ = Side == 0 ? OverrideLeftGround : OverrideRightGround;
		}
		else if (!GroundUnderFoot(AnimatedFoot[Side], GroundZ, Normal[Side]))
		{
			continue;
		}
		State.bClamped |= FMath::Abs(GroundZ) > MaxFootOffset;
		Target[Side] = FMath::Clamp(GroundZ, -MaxFootOffset, MaxFootOffset);
	}
	float PelvisTarget = bGround ? FMath::Clamp(FMath::Min(Target[0], Target[1]), -MaxPelvisDrop, MaxPelvisRaise) : 0.f;
	State.bClamped |= bGround && FMath::Min(Target[0], Target[1]) < -MaxPelvisDrop;

	const float Alpha = 1.f - FMath::Exp(-IKInterpSpeed * FMath::Max(DeltaTime, 0.f));
	PelvisOffset += (PelvisTarget - PelvisOffset) * Alpha;
	LeftOffset += (Target[0] - LeftOffset) * Alpha;
	RightOffset += (Target[1] - RightOffset) * Alpha;
	const float TiltWeight = bGround ? 1.f - AirBlend : 0.f;

	State.bActive = bGround;
	State.PelvisOffsetCm = PelvisOffset;
	State.LeftFootOffsetCm = LeftOffset;
	State.RightFootOffsetCm = RightOffset;
	LastFootIK = State;

	if (FMath::Abs(PelvisOffset) < 0.05f && FMath::Abs(LeftOffset) < 0.05f && FMath::Abs(RightOffset) < 0.05f && TiltWeight <= 0.f)
	{
		return;
	}

	// Pelvis first; everything below follows it.
	{
		FTransform PelvisTransform = Pose.GetComponentSpaceTransform(Pelvis);
		PelvisTransform.AddToTranslation(FVector(0.0, 0.0, PelvisOffset));
		TArray<FBoneTransform, TInlineAllocator<1>> Changed;
		Changed.Add(FBoneTransform(Pelvis, PelvisTransform));
		Pose.SafeSetCSBoneTransforms(Changed);
	}

	const float Offsets[2] = { LeftOffset, RightOffset };
	for (int32 Side = 0; Side < 2; ++Side)
	{
		if (!Legs[Side][1].IsValid())
		{
			continue;
		}
		FTransform Thigh = Pose.GetComponentSpaceTransform(Legs[Side][0]);
		FTransform Calf = Pose.GetComponentSpaceTransform(Legs[Side][1]);
		FTransform Foot = Pose.GetComponentSpaceTransform(Legs[Side][2]);

		// Keep the knee in its animated bend plane: aim the pole away from the hip-ankle line.
		const FVector HipToAnkleMid = (Thigh.GetLocation() + Foot.GetLocation()) * 0.5;
		FVector Bend = (Calf.GetLocation() - HipToAnkleMid).GetSafeNormal();
		if (Bend.IsNearlyZero())
		{
			Bend = FVector(0.0, 1.0, 0.0);  // Mannequin faces +Y in component space
		}
		const FVector Effector = AnimatedFoot[Side] + FVector(0.0, 0.0, Offsets[Side]);
		AnimationCore::SolveTwoBoneIK(Thigh, Calf, Foot, Calf.GetLocation() + Bend * 100.0, Effector, false, 1.0, 1.0);

		// Tilt the foot with the slope, limited.
		if (TiltWeight > 0.f)
		{
			FQuat Tilt = FQuat::FindBetweenNormals(FVector::UpVector, Normal[Side]);
			const double Angle = FMath::RadiansToDegrees(Tilt.GetAngle());
			if (Angle > 1e-3)
			{
				const double Weight = TiltWeight * FMath::Min(1.0, MaxFootTilt / Angle);
				Tilt = FQuat::Slerp(FQuat::Identity, Tilt, Weight);
				Foot.SetRotation((Tilt * Foot.GetRotation()).GetNormalized());
			}
		}

		TArray<FBoneTransform, TInlineAllocator<3>> Changed;
		Changed.Add(FBoneTransform(Legs[Side][0], Thigh));
		Changed.Add(FBoneTransform(Legs[Side][1], Calf));
		Changed.Add(FBoneTransform(Legs[Side][2], Foot));
		Changed.Sort(FCompareBoneTransformIndex());
		Pose.SafeSetCSBoneTransforms(Changed);
	}

	FCSPose<FCompactPose>::ConvertComponentPosesToLocalPoses(MoveTemp(Pose), Output.Pose);
}
