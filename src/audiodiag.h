#pragma once
#include <windows.h>

typedef struct {
    volatile LONG engines, voices, submits, starved, gaps, gapFrames;
    volatile LONG depth[4];           /* buffers still queued at each submit: 0, 1, 2, 3+ */
    volatile LONG lastFrames, channels, rate;
} AudioDiag;

extern AudioDiag g_ad;

int    AudioDiag_Install(void);
void **AudioDiag_FindSlot(HMODULE mod);
void   AudioDiag_OnEngine(void *engine);
