# Expedition33FXCore

**A CPU scheduling and audio mod for Clair Obscur: Expedition 33 on older CPUs.**

Expedition33FXCore is a small native DLL that loads with the game and changes **how Windows schedules the game's
threads on your CPU**. It also gives the engine a bigger audio buffer, which cuts down on the crackling and static
the game has on slower CPUs. It doesn't change graphics settings, game files or saves.

It was built and tested on an AMD FX-8350 with a Radeon RX 6600 and adapts to whatever CPU it finds. It is a port of
[WindroseFXCore](https://github.com/mcirish3/WindroseFXCore) and
[EverwindFXCore](https://github.com/mcirish3/EverwindFXCore) to Expedition 33 (Unreal Engine 5.4).

## Measured results

Test PC: AMD FX-8350, Radeon RX 6600 8 GB, 32 GB DDR3, Windows 10, 1080p, all settings Epic, XeSS at native
resolution, VSync on, 60 FPS limit. Frame times were recorded with PresentMon.

**Frame rate.** The mod switched between stock and modded scheduling every minute *within one session*, so both were
measured in the same places, five times over:

| | Stock | With the mod |
|---|---|---|
| Average FPS (light area) | 22.2 | **25.8** (+16%) |
| Average FPS (heavy area) | 20.7 | **23.0** (+11%) |
| Stutters over 50 ms, per minute | 137 | **40** |
| Time the graphics card was the limit | 25% | **84%** |

The last row is the important one: with the mod, the CPU stops holding the graphics card back most of the time.
On this PC the game is now mostly limited by the graphics card, so a faster card would gain more.

**Audio.** The mod counted dropouts (the moments that sound like crackle or static) directly in the audio the game
sends to Windows:

| | Dropouts | Audio lost |
|---|---|---|
| Stock audio buffer, 25 minutes | 619 (about 25 a minute) | 5.6 s |
| With the bigger buffer, 36 minutes | 94 (about 3 a minute) | 4.7 s |

That's roughly 90% fewer dropouts. The two sessions weren't in exactly the same areas, so take the exact number
loosely. The player on the test PC heard far less static, and the build-up that the game is known for didn't happen.
It doesn't remove every glitch: short ones can still happen during heavy scenes.

**Your results will differ.** Newer CPUs have less to gain. Please share yours (see [Reporting results](#reporting-results)).

## What the mod does

| Fix | What it does |
|---|---|
| **Topology-aware thread placement** | GameThread, RenderThread and RHIThread each prefer their own module (AMD FX) or core (SMT CPUs), read from your CPU's real cache layout at launch. |
| **Background worker isolation** | Unreal's background pool (asset streaming, decompression, shader work) is kept off the cores the frame threads prefer. |
| **Audio protection** | The audio mixer runs at time-critical priority on its own preferred core. |
| **Audio buffer fix** (on by default) | Raises the engine's audio buffer to 2048 frames x 4. See [Audio buffer fix](#audio-buffer-fix). |
| **Priority floors** | Frame threads run at least at Above Normal priority. |
| **0.5 ms timer resolution** | Lets the frame limiter and thread waits wake on time. |
| **Power-throttling opt-out** | Stops Windows from applying EcoQoS or timer coalescing to the game. |

| CPU family | What applies |
|---|---|
| **AMD FX** (FX-8xxx/9xxx) | Everything. |
| **Intel Core i7 with Hyper-Threading, Ryzen** | Everything. Critical threads stay inside one L3 domain on multi-CCX Ryzen chips. |
| **Intel 12th gen and newer** | Critical threads are placed on P-cores. |
| **Dual cores, or quad cores without SMT** | Thread placement switches itself off. The timer, priority, power and audio fixes still apply. |

## In-game settings tested on the same PC

- **Frame generation is not worth it at this frame rate.** With only 22–25 real frames per second, the
  generated frames smeared badly in testing. Frame generation needs a higher base frame rate to look right.
- **XeSS at native resolution** ran better here than FSR 4 at native resolution (through OptiScaler), which cost
  about 4 ms more per frame on an RX 6600 and got slower over a long session.

## Install

1. Download the latest zip from [Nexus Mods](https://www.nexusmods.com/clairobscurexpedition33), GameBanana or
   [Releases](../../releases).
2. In Steam, right-click **Clair Obscur: Expedition 33 → Manage → Browse local files**.
3. Extract the zip into that folder. The files land in `Sandfall\Binaries\Win64\`, next to
   `SandFall-Win64-Shipping.exe`:
   - `version.dll`
   - `Expedition33FXCore.ini`
4. Launch the game through Steam as usual.

Tested with the Steam version only. The Game Pass / Microsoft Store version uses different folders and is not
supported.

## Check that it's working

After launching, open `Sandfall\Binaries\Win64\Expedition33FXCore.log`. On an FX-8350 it looks like this:

```
Expedition33FXCore 1.0.0 loaded into ...\SandFall-Win64-Shipping.exe
Audio buffer: set 2048 frames x 4 buffers in Engine.ini
CPU: AMD FX(tm)-8350 Eight-Core Processor
Topology: 8 logical processors, 4 execution groups, 1 L3 domain(s)
Timer resolution: 0.500 ms
Power throttling opt-out: ok (execution speed only)
Process priority: raised
Critical LPs: game 0, render 2, rhi 4, audio 6 | background mask 0xaa
  GameThread       tid ...  prio 1 (game's own: 0)
  RHIThread        tid ...  prio 1 (game's own: 0)
  RenderThread     tid ...  prio 1 (game's own: 0)
  AudioMixer       tid ...  prio 15 (game's own: 2)
```

If there's no log file at all, the DLL isn't loading. Please open an issue.

## Configure

Every fix can be turned off on its own in `Expedition33FXCore.ini`. Changes take effect at the next launch.

| Setting | Default | Notes |
|---|---|---|
| `Enabled` | 1 | Master switch |
| `TimerResolution100ns` | 5000 | 0.5 ms. `10000` = 1 ms, `0` = leave alone |
| `DisablePowerThrottling` | 1 | |
| `ProcessPriority` | 1 | 0 Normal, 1 Above Normal, 2 High (not recommended) |
| `PlaceCriticalThreads` | 1 | |
| `IsolateBackgroundWorkers` | 1 | |
| `ExclusiveGameModule` | 0 | Gives the GameThread a whole module or core to itself. Measured the same as the normal placement here |
| `BoostCriticalPriority` | 1 | |
| `BoostAudioPriority` | 1 | |
| `AudioMixerPriority` | 15 | 15 = time-critical, 2 = highest |
| `PlaceAudioThread` | 1 | |
| `AudioBufferFix` | 1 | Writes the audio buffer size to `Engine.ini`. See below |
| `AudioBufferFrames` | 2048 | Frames per buffer (256–8192) |
| `AudioBuffersToEnqueue` | 4 | Buffers queued ahead (2–8) |
| `AudioSourceWorkers` | -1 | Experimental, untested. `-1` leaves the game's value |
| `VerboseLog` | 0 | Logs every worker thread too |
| `PerfLogSeconds` | 0 | Diagnostics: every N seconds, logs CPU use of the frame threads and workers (100% = one full core) |
| `AudioDiag` | 0 | Diagnostics: counts audio dropouts and logs them once a minute. Never changes the audio |
| `ABSeconds` | 0 | Test mode: switches between stock and modded scheduling every N seconds and logs each switch |

## Audio buffer fix

Expedition 33 has no menu option for its audio buffer, and its default (256 frames, about 5 ms) is too small for a
busy older CPU. When the mixer misses that deadline you hear a crackle.

- At every launch the mod writes these lines to `%LOCALAPPDATA%\Sandfall\Saved\Config\Windows\Engine.ini`:
  ```
  [/Script/WindowsTargetPlatform.WindowsTargetSettings]
  AudioCallbackBufferFrameSize=2048
  AudioNumBuffersToEnqueue=4
  ```
  The game deletes `Engine.ini` when it exits, which is why the mod writes it every time.
- The first time, an existing `Engine.ini` is copied to `Engine.ini.Expedition33FXCore.bak`, and the original values
  are recorded in `Expedition33FXCore.state` next to the DLL.
- A bigger buffer adds a little audio delay, up to about 0.17 s with 2048 x 4. On the test PC parry timing still felt
  normal. If it doesn't for you, try `AudioBufferFrames=1024`.
- **To undo:** set `AudioBufferFix=0` (or `Enabled=0`) and launch once. The original values are put back.

## Uninstall

1. Set `AudioBufferFix=0` in `Expedition33FXCore.ini` and launch the game once, so your `Engine.ini` is restored.
2. Delete `version.dll`, `Expedition33FXCore.ini`, `Expedition33FXCore.log` and `Expedition33FXCore.state` from
   `Sandfall\Binaries\Win64`.

## FAQ

**Is it safe?** Expedition 33 is single-player and has no anti-cheat. The DLL makes no network connections and
never touches saves or game files.

**Does it work with other mods?** Yes, unless another mod also uses `version.dll` as its loader. Then only one can be
installed at a time. It works alongside OptiScaler (`dxgi.dll`).

**The game won't start after an update.** Delete `version.dll` to rule it out, then open an issue with the game version.

## Reporting results

Open an [issue](../../issues) or comment on the mod page with:
- your CPU, GPU and RAM
- your `Expedition33FXCore.log`
- what changed for you: frame rate, stutters, audio

To measure it yourself, set `ABSeconds=60` and `PerfLogSeconds=5`, play for 20 minutes or more, and record frame
times with PresentMon. The log marks each switch between stock and modded scheduling.

## Building from source

The mod is plain C with no dependencies.

```
pip install ziglang
python -m ziglang cc -target x86_64-windows-gnu -O2 -shared -o version.dll src/version_proxy.c src/fxcore.c src/audiodiag.c src/version.def -ladvapi32 -s
```
Or run `build.bat`. `python package.py <version>` makes the release zip.

**How it loads:** Unreal Engine links `version.dll`, so the game loads it from its own folder first.
`src/version_proxy.c` forwards all 17 real exports to `System32\version.dll`, and `src/fxcore.c` starts one
background thread that does the work. It only activates inside an executable whose name contains `Shipping`,
so the crash reporter and other tools are never affected. `src/audiodiag.c` is the optional dropout counter
(`AudioDiag=1`); it is not installed unless you turn it on.

## License

MIT. See [LICENSE](LICENSE).

Created by Patrick McCoy, with Claude (Anthropic).
