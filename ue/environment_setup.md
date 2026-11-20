> Language: **English** | [简体中文](./环境搭建.md)
# UE5 Environment Testing and Setup

Tested: 2026-10-08 ｜ Conclusion: **the engine works, but the C++ compiler is missing, so the project can't be compiled yet**

---

## I. Test Results

| Check | Status | Details |
|---|---|---|
| Unreal Engine | ✅ Installed | `C:\Program Files\Epic Games\UE_5.8` |
| Engine version | ✅ | **5.8.3**, Changelist 58210709, Promoted Build |
| `UnrealEditor.exe` | ✅ | Present, editor itself works |
| `UnrealEditor-Cmd.exe` | ✅ | Present, can run headless |
| `UnrealBuildTool.exe` | ✅ | Present |
| Engine-bundled .NET | ✅ | 10.0 win-x64 (`Build.bat` uses it automatically) |
| winget | ✅ | v1.29.380, can be used to install the toolchain |
| **Visual Studio** | ❌ **Not installed** | No VS installation of any kind |
| **MSVC compiler** | ❌ **Not installed** | `cl.exe` not found |
| **Windows SDK** | ❌ **Not installed** | No `Windows Kits/10/Include` |

## II. Decisive Test: Actually Compile Once

I ran a real build command directly instead of guessing:

```bat
Engine\Build\BatchFiles\Build.bat RobotGameEditor Win64 Development ^
  -Project="...\ue\RobotGame.uproject" -WaitMutex
```

**Result:**

```
Using bundled DotNet SDK version: 10.0 win-x64
Determining max actions to execute in parallel (14 physical cores, 20 logical cores)
Creating makefile for RobotGameEditor (no existing makefile)

Platform Win64 is not a valid platform to build. SDK validation failed:
  Sdk: not found. Required version 10.0.19041.0.

Result: Failed (OtherCompilationError)
```

**This result tells us three things:**

1. **The engine itself is healthy** — UBT started normally, read the .uproject correctly, and generated the makefile successfully.
2. **The blocker is the Windows SDK**, the error is at the SDK validation stage, **the MSVC compiler hasn't even been checked yet**.
3. **`Result: Failed` is not a code problem**, it's an environment problem. Not a single line of my C++ has been compiled.

> The `UbaStorageServer ... Access is denied` in the log was caused by running in a sandbox;
> running it yourself in a normal terminal won't have this issue (UBA is a build accelerator, even if unavailable it doesn't affect compilation).

## III. Solution

Need to install the **Visual Studio C++ build tools** (including the MSVC compiler + Windows SDK).

### Option A: VS 2022 Build Tools (recommended, smaller)

Only the minimal set needed for compiling, about **7–12 GB**, no GUI.

```powershell
winget install --id Microsoft.VisualStudio.2022.BuildTools --source winget ^
  --override "--quiet --wait --norestart --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

`Microsoft.VisualStudio.Workload.VCTools` is the "Desktop development with C++" workload,
`--includeRecommended` automatically brings in the MSVC compiler and the matching Windows SDK.

### Option B: VS 2022 Community (full IDE)

Adds a GUI and debugger, about **15–25 GB**. If you plan to do C++ development long-term,
the debugging experience is noticeably better; if you just want "something that compiles", Option A is enough.

```powershell
winget install --id Microsoft.VisualStudio.2022.Community --source winget ^
  --override "--quiet --wait --norestart --add Microsoft.VisualStudio.Workload.NativeGame --includeRecommended"
```

`NativeGame` is the "Game development with C++" workload, officially recommended by Epic.

> Both commands require **administrator privileges** and will download several GB.

### If UBT Still Reports a Wrong SDK Version

Manually install the specified Windows SDK version:

```powershell
# Install Windows 11 SDK (covers the 10.0.19041.0+ required by UE 5.8)
winget install --id Microsoft.VisualStudio.2022.BuildTools --source winget ^
  --override "--quiet --wait --add Microsoft.VisualStudio.Component.Windows11SDK.26100"
```

---

## IV. What to Do After Installation

### 1. Verify the Compiler Is in Place

```bash
# Should list MSVC and the Windows SDK
"/c/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe" -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64
ls "/c/Program Files (x86)/Windows Kits/10/Include"
```

### 2. Generate Project Files

```bash
"/c/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat" ^
  -projectfiles -project="C:/Users/25227/Documents/robot_game/ue/RobotGame.uproject" -game -rocket -progress
```

### 3. Compile

```bash
"/c/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat" ^
  RobotGameEditor Win64 Development ^
  -Project="C:/Users/25227/Documents/robot_game/ue/RobotGame.uproject" -WaitMutex
```

### 4. Open the Editor

Double-click `ue/RobotGame.uproject`, or after a successful build:
```bash
"/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe" ^
  "C:/Users/25227/Documents/robot_game/ue/RobotGame.uproject"
```

---

## V. What to Expect When Compiling

This is my first time validating this code with a real compiler, **there will most likely be errors**. Anticipated high-risk points:

| Location | Risk | Notes |
|---|---|---|
| `URobotChassisData::IsDataValid` | Signature | Changed from `TArray<FText>&` to `FDataValidationContext&` around UE 5.4 |
| `USkeletalMeshComponent::GetSkeletalMeshAsset()` | API name | Only replaced the `SkeletalMesh` member after 5.1 |
| `ASC->SetReplicationMode` | Necessity | May not be needed in a single-player project |
| `FGameplayTag::RequestGameplayTag(FName, bool)` | Parameters | The two-argument version exists, but confirm it isn't deprecated in 5.8 |
| `GameplayTasks` in `RobotCombat.Build.cs` | Dependency | GAS needs it, but some versions require explicitly declaring the `GameplayTasks` module |

**Paste the compile errors to me verbatim and I'll fix them one by one.** A dozen to a few dozen errors on the first build is normal,
it doesn't mean the architecture is wrong — it means "nobody has run it through a real compiler yet".

---

## VI. What You Can Do Right Now (Without Waiting for the Compiler)

Even without VS, these can proceed:

| What you can do | How |
|---|---|
| Open the engine and look at resources | Launch `UnrealEditor.exe` directly and browse the engine's built-in sample content |
| Create a blueprint-only test project | Create a Blueprint project, no C++ needed, verify the engine runs on your machine |
| Import and view models | Create a project, import `assets/out/chassis_medium.fbx`, **verify orientation and size** |
| Run the core loop prototype | `prototype/core_loop_prototype.html`, open directly in a browser |

**Among these, "import a model and verify orientation and size" is the most worth doing first** — it doesn't depend on C++,
but its result affects all later assets: if the FBX `global_scale=100` conversion is wrong,
all 54 assets will need to be re-exported.
