# -*- coding: utf-8 -*-
"""把 BeginPlay 里的"运行时 SpawnActor 补光"换成"移动关卡里的 HeroFill"。"""
import io

P = r"ue/Source/RobotGame/Private/RobotCharacter.cpp"
d = io.open(P, "r", encoding="utf-8", newline="").read()

start_marker = "\t// \u2500\u2500 \u73a9\u5bb6\u82f1\u96c4\u8865\u5149 \u2500\u2500"
end_marker = "\t// \u5efa\u7acb\u7a0b\u5e8f\u5316\u52a8\u753b\u7528\u7684\u53ef\u89c1\u7f51\u683c"

i = d.find(start_marker)
j = d.find(end_marker, i)
assert i > 0 and j > i, (i, j)

new = (
    "\t// \u2500\u2500 \u73a9\u5bb6\u82f1\u96c4\u8865\u5149 \u2500\u2500\r\n"
    "\t// \u7b2c\u4e09\u4eba\u79f0\u89c6\u89d2\u4e0b\u673a\u4f53\u80cc\u5bf9\u592a\u9633\uff0c"
    "\u955c\u5934\u770b\u5230\u7684\u90a3\u4e00\u9762\u6c38\u8fdc\u5728\u9634\u5f71\u91cc\u3002\r\n"
    "\t//\r\n"
    "\t// \u2605 2026-10-25\uff1a\u8fd9\u76cf\u706f\u539f\u6765\u662f BeginPlay \u91cc "
    "SpawnActor \u51fa\u6765\u7684\u3002\r\n"
    "\t//   \u672c\u5de5\u7a0b\u5b9e\u6d4b\u7ed3\u8bba\u662f**\u8fd0\u884c\u65f6\u751f\u6210\u7684"
    "\u706f\u5b8c\u5168\u4e0d\u53c2\u4e0e\u6e32\u67d3**\uff08\u5f3a\u5ea6/\u53ef\u89c1/\u6ce8\u518c"
    "\u5168\u662f 1\u3001\u4f4d\u7f6e\u4e5f\u5bf9\uff0c\u753b\u9762\u4e00\u4e2a\u50cf\u7d20\u90fd"
    "\u4e0d\u4eae\uff09\u3002\r\n"
    "\t//   \u6240\u4ee5\u5b83\u4ece\u5199\u4e0b\u90a3\u5929\u8d77\u5c31\u6ca1\u4eae\u8fc7 \u2014\u2014 "
    "\u673a\u4f53\u6c38\u8fdc\u662f\u4e00\u56e2\u9ed1\u526a\u5f71\u3002\r\n"
    "\t//   \u73b0\u5728\u6539\u6210\u300c\u5173\u5361\u91cc\u9884\u5148\u5efa\u597d\u7684 HeroFill"
    "\uff08ue/Scripts/arena_herofill.py\uff09+ C++ \u6bcf\u5e27\u6446\u4f4d\u300d\uff0c\r\n"
    "\t//   \u548c\u5149\u6c60\u8d70\u540c\u4e00\u6761\u5df2\u9a8c\u8bc1\u53ef\u884c\u7684\u8def\u5f84"
    "\u3002\r\n"
    "\tfor (TActorIterator<AActor> It(GetWorld()); It; ++It)\r\n"
    "\t{\r\n"
    "\t\tif (!It->ActorHasTag(TEXT(\"HeroFill\")))\r\n"
    "\t\t{\r\n"
    "\t\t\tcontinue;\r\n"
    "\t\t}\r\n"
    "\t\tHeroFillLight = *It;\r\n"
    "\t\tif (UPointLightComponent* KC = Cast<UPointLightComponent>(\r\n"
    "\t\t\tIter->GetComponentByClass(UPointLightComponent::StaticClass())))\r\n"
    "\t\t{\r\n"
    "\t\t\tKC->SetMobility(EComponentMobility::Movable);\r\n"
    "\t\t\t// \u8865\u5149\u7684\u804c\u8d23\u53ea\u662f\u628a\u6697\u90e8\u62ac\u8d77\u6765\u4e00\u70b9\uff1a\r\n"
    "\t\t\t// 9000cd \u5728 3m \u5904\u7ea6 1000 lux\uff0c\u4e0d\u5230\u6708\u5149"
    "(1800 lux) \u7684\u4e00\u534a\u591a\uff0c\r\n"
    "\t\t\t// \u518d\u5f3a\u5c31\u628a\u88c5\u7532\u677f\u7684\u5012\u89d2\u3001\u51f9\u69fd\u3001"
    "\u87ba\u6813\u5168\u90e8\u62b9\u5e73\u6210\u4e00\u5757\u80a5\u7682\u3002\r\n"
    "\t\t\tKC->SetIntensity(9000.f);\r\n"
    "\t\t\tKC->SetAttenuationRadius(1900.f);\r\n"
    "\t\t\tKC->SetLightColor(FLinearColor(0.82f, 0.90f, 1.00f));\r\n"
    "\t\t\tKC->SetCastShadows(false);\r\n"
    "\t\t\tKC->SetVisibility(true);\r\n"
    "\t\t\tKC->SetVolumetricScatteringIntensity(0.f);\r\n"
    "\t\t\tKC->MarkRenderStateDirty();\r\n"
    "\t\t}\r\n"
    "\t\tUpdateHeroFill();\r\n"
    "\t\tUE_LOG(LogTemp, Warning,\r\n"
    "\t\t\tTEXT(\"[\u706f] \u82f1\u96c4\u8865\u5149\u5df2\u63a5\u7ba1\uff08\u5173\u5361 HeroFill\uff09\uff1a"
    "9000cd / 1900cm / \u65e0\u9634\u5f71\"));\r\n"
    "\t\tbreak;\r\n"
    "\t}\r\n"
    "\r\n"
)

d2 = d[:i] + new + d[j:]
io.open(P, "w", encoding="utf-8", newline="").write(d2)
print("patched", len(d) - len(d2))
