#include "PartMapData.h"

namespace
{
	FPartBoneRule MakeRule(const FGameplayTag& Tag,
	                       const TArray<FName>& Prefixes,
	                       float MaxHealth, int32 Salvage, bool bKills,
	                       float Front = 1.0f, float Side = 1.0f,
	                       float Back = 1.0f)
	{
		FPartBoneRule R;
		R.PartTag = Tag;
		R.BonePrefixes = Prefixes;
		R.MaxHealth = MaxHealth;
		R.SalvageValue = Salvage;
		R.bDestructionKills = bKills;
		R.FrontMultiplier = Front;
		R.SideMultiplier = Side;
		R.BackMultiplier = Back;
		return R;
	}
}

void UPartMapData::BuildDefaultRules(bool bForPlayer)
{
	Rules.Empty();

	if (bForPlayer)
	{
		// 玩家骨架来自 Blender 的 build_rig：
		//   root / pelvis / torso / head / shoulder_L,R / upperarm_L,R
		//   / forearm_L,R / leg_L,R / foot_L,R
		// 注意：没有独立的 core 骨骼 —— 核心包含在 torso 里，所以 torso 兼任核心。
		//
		// 倍率：核心/躯干正面硬（1.0），侧面 1.15，背面 1.3；
		// 四肢没有装甲，侧面 1.3、背面 1.6。
		//
		// 玩家的倍率刻意比敌人低一档：这是 PvE，敌人会主动绕后，
		// 而玩家在混战里很难同时盯住五个方向 —— 背面 2.0 会让"站着不动"
		// 变成必死，惩罚过重。敌人身上的 1.6/2.0 保持不变：
		// 玩家绕后仍然值得，只是挨打时不至于被瞬间拆光。
		Rules.Add(MakeRule(RobotTags::Part_Core(), { TEXT("torso") }, 90.f, 0, true,
			1.0f, 1.15f, 1.3f));
		Rules.Add(MakeRule(RobotTags::Part_Torso(), { TEXT("head") }, 40.f, 0, false,
			1.0f, 1.15f, 1.3f));
		Rules.Add(MakeRule(RobotTags::Part_Arm_L(),
			{ TEXT("upperarm_L"), TEXT("forearm_L"), TEXT("shoulder_L") },
			34.f, 5, false, 1.0f, 1.3f, 1.6f));
		Rules.Add(MakeRule(RobotTags::Part_Arm_R(),
			{ TEXT("upperarm_R"), TEXT("forearm_R"), TEXT("shoulder_R") },
			34.f, 5, false, 1.0f, 1.3f, 1.6f));
		Rules.Add(MakeRule(RobotTags::Part_Leg_L(),
			{ TEXT("leg_L"), TEXT("foot_L") }, 30.f, 6, false,
			1.0f, 1.3f, 1.6f));
		Rules.Add(MakeRule(RobotTags::Part_Leg_R(),
			{ TEXT("leg_R"), TEXT("foot_R") }, 30.f, 6, false,
			1.0f, 1.3f, 1.6f));
	}
	else
	{
		// 敌人骨架由 build_enemies.py 的 infer_bone_name 生成：
		//   core / arm_L,R / leg_L,R / torso / head
		// 核心是独立的小目标（26 血），正面打得动但慢；背面拆核心是"速杀"路线，
		// 拆四肢则是"回收"路线 —— 两条路的收益差由倍率拉开。
		Rules.Add(MakeRule(RobotTags::Part_Core(), { TEXT("core") }, 26.f, 9, true,
			1.0f, 1.3f, 1.6f));
		Rules.Add(MakeRule(RobotTags::Part_Torso(),
			{ TEXT("torso"), TEXT("head") }, 70.f, 0, false,
			1.0f, 1.3f, 1.6f));
		Rules.Add(MakeRule(RobotTags::Part_Arm_L(), { TEXT("arm_L") }, 20.f, 5, false,
			1.0f, 1.6f, 2.0f));
		Rules.Add(MakeRule(RobotTags::Part_Arm_R(), { TEXT("arm_R") }, 20.f, 5, false,
			1.0f, 1.6f, 2.0f));
		Rules.Add(MakeRule(RobotTags::Part_Leg_L(), { TEXT("leg_L") }, 18.f, 6, false,
			1.0f, 1.6f, 2.0f));
		Rules.Add(MakeRule(RobotTags::Part_Leg_R(), { TEXT("leg_R") }, 18.f, 6, false,
			1.0f, 1.6f, 2.0f));
	}
}

FGameplayTag UPartMapData::ResolvePartTag(FName BoneName) const
{
	const FString BoneStr = BoneName.ToString();
	for (const FPartBoneRule& Rule : Rules)
	{
		for (const FName& Prefix : Rule.BonePrefixes)
		{
			if (BoneStr.StartsWith(Prefix.ToString(), ESearchCase::IgnoreCase))
			{
				return Rule.PartTag;
			}
		}
	}
	return FGameplayTag();
}

bool UPartMapData::FindRule(const FGameplayTag& PartTag, FPartBoneRule& OutRule) const
{
	for (const FPartBoneRule& Rule : Rules)
	{
		if (Rule.PartTag == PartTag)
		{
			OutRule = Rule;
			return true;
		}
	}
	return false;
}
