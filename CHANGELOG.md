# Changelog

## 1.0.0 - 2026-11-25

First public release. Port of WindroseFXCore / EverwindFXCore to Clair Obscur: Expedition 33 (Unreal Engine 5.4.4).

- Thread placement, background worker isolation, priority floors, 0.5 ms timer resolution and the power-throttling
  opt-out, as in WindroseFXCore.
- Measured on an FX-8350 with an RX 6600 (PresentMon, stock and modded scheduling alternated within one session):
  +16% average FPS in a light area (22.2 to 25.8), +11% in a heavy area (20.7 to 23.0), stutters over 50 ms down
  from 137 to 40 a minute.
- The audio buffer fix (2048 frames x 4) is on by default here. The game's own buffer is 256 frames. Dropouts fell
  from about 25 a minute to about 3 a minute on the test PC. The game deletes Engine.ini on exit, so the mod writes it
  at every launch.
- `ExclusiveGameModule` is off by default: it measured the same as the normal placement.
- New diagnostics, all off by default: `AudioDiag` (counts audio dropouts in the buffers the game sends to XAudio2,
  never changes the audio), `ABSeconds` (switches between stock and modded scheduling for measuring) and
  `AudioSourceWorkers` (experimental, untested).
- `test/` has the PresentMon recorder and the analysis script used for the numbers above.
