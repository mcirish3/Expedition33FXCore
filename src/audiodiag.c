/*
 * Optional diagnostic (AudioDiag=1): counts audio dropouts exactly.
 *
 * Unreal's audio mixer hands finished buffers to XAudio2 through one source
 * voice. When the mixer misses its deadline the game submits a buffer that is
 * cut off with zeros, or XAudio2 runs out of queued buffers. Both are heard as
 * static or crackle. This file watches the buffers as they are submitted and
 * counts those events. It never changes the audio.
 *
 * How: the game's delay-import slot for XAudio2Create (ordinal 1) is replaced.
 * The wrapper calls the original and then patches two vtable slots:
 * IXAudio2::CreateSourceVoice (to learn the format) and
 * IXAudio2SourceVoice::SubmitSourceBuffer (to look at each buffer).
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "audiodiag.h"

#define VT_CREATE_SOURCE_VOICE   5
#define VT_SUBMIT_SOURCE_BUFFER 21
#define VT_GET_STATE            25
#define XAUDIO2_VOICE_NOSAMPLESPLAYED 0x100

#pragma pack(push, 1)
typedef struct { WORD tag, ch; DWORD rate, bps; WORD align, bits, cb; } WFX;
typedef struct { UINT32 flags, bytes; const BYTE *data; } XABUF;   /* leading fields only */
#pragma pack(pop)

typedef HRESULT (WINAPI *PFN_Create)(void **, UINT32, UINT32);
typedef HRESULT (WINAPI *PFN_CreateSourceVoice)(void *, void **, const WFX *, UINT32, float, void *, const void *, const void *);
typedef HRESULT (WINAPI *PFN_Submit)(void *, const XABUF *, const void *);
typedef void    (WINAPI *PFN_GetState)(void *, void *, UINT32);

static PFN_Create            g_origCreate;
static PFN_CreateSourceVoice g_origCSV;
static PFN_Submit            g_origSubmit;

AudioDiag g_ad;

#define MAX_VOICES 32
typedef struct { void *voice; WORD ch, bits; DWORD rate; float lastPeak; LONG submits; BOOL inGap; } Voice;
static Voice g_voice[MAX_VOICES];
static SRWLOCK g_lock = SRWLOCK_INIT;

static void PatchSlot(void **slot, void *fn)
{
    DWORD old;
    if (VirtualProtect(slot, sizeof(void *), PAGE_READWRITE, &old)) {
        InterlockedExchangePointer(slot, fn);
        VirtualProtect(slot, sizeof(void *), old, &old);
    }
}

static Voice *FindVoice(void *v)
{
    for (int i = 0; i < MAX_VOICES; i++) if (g_voice[i].voice == v) return &g_voice[i];
    return NULL;
}

/* A dropout is a run of exact zeros that starts abruptly: the sample frame just
   before it was still audible. Fades and real silence end near zero first. */
#define AUDIBLE  1e-4f
#define MIN_RUN  8

static void ScanFloat(Voice *v, const float *p, UINT32 frames, UINT32 ch)
{
    UINT32 run = 0;
    float prev = v->lastPeak;
    LONG gaps = 0, zero = 0;
    BOOL cut = v->inGap;
    for (UINT32 f = 0; f < frames; f++, p += ch) {
        float pk = 0;
        for (UINT32 c = 0; c < ch; c++) { float a = p[c] < 0 ? -p[c] : p[c]; if (a > pk) pk = a; }
        if (pk == 0.0f) {
            if (run == 0 && !cut) cut = prev > AUDIBLE;
            run++;
            if (cut) { if (run == MIN_RUN && !v->inGap) { gaps++; zero += MIN_RUN; v->inGap = TRUE; } else if (v->inGap) zero++; }
        } else { run = 0; cut = FALSE; v->inGap = FALSE; }
        prev = pk;
    }
    v->lastPeak = prev;
    if (gaps) InterlockedExchangeAdd(&g_ad.gaps, gaps);
    /* Long zero runs are a real stop (pause, loading), so only the first 0.5 s of a gap counts. */
    if (zero > (LONG)(v->rate / 2)) zero = v->rate / 2;
    if (zero) InterlockedExchangeAdd(&g_ad.gapFrames, zero);
}

static HRESULT WINAPI HookSubmit(void *self, const XABUF *b, const void *wma)
{
    AcquireSRWLockExclusive(&g_lock);
    Voice *v = FindVoice(self);
    if (v && b && b->data && b->bytes) {
        BYTE st[64] = { 0 };
        PFN_GetState gs = (PFN_GetState)(*(void ***)self)[VT_GET_STATE];
        gs(self, st, XAUDIO2_VOICE_NOSAMPLESPLAYED);
        UINT32 queued = *(UINT32 *)(st + 8);
        if (v->submits++ > 4 && queued == 0) InterlockedIncrement(&g_ad.starved);
        InterlockedIncrement(&g_ad.depth[queued > 3 ? 3 : queued]);
        InterlockedIncrement(&g_ad.submits);
        UINT32 fr = b->bytes / (v->ch * (v->bits / 8u));
        g_ad.lastFrames = fr; g_ad.channels = v->ch; g_ad.rate = v->rate;
        if (v->bits == 32) ScanFloat(v, (const float *)b->data, fr, v->ch);
    }
    ReleaseSRWLockExclusive(&g_lock);
    return g_origSubmit(self, b, wma);
}

static HRESULT WINAPI HookCSV(void *self, void **pp, const WFX *fmt, UINT32 flags, float ratio,
                              void *cb, const void *sends, const void *fx)
{
    HRESULT hr = g_origCSV(self, pp, fmt, flags, ratio, cb, sends, fx);
    if (SUCCEEDED(hr) && pp && *pp && fmt && fmt->ch && fmt->bits >= 8) {
        AcquireSRWLockExclusive(&g_lock);
        Voice *v = FindVoice(*pp);
        for (int i = 0; !v && i < MAX_VOICES; i++) if (!g_voice[i].voice) v = &g_voice[i];
        if (!v) v = &g_voice[0];
        ZeroMemory(v, sizeof(*v));
        v->voice = *pp; v->ch = fmt->ch; v->bits = fmt->bits; v->rate = fmt->rate;
        void **vt = *(void ***)*pp;
        if (vt[VT_SUBMIT_SOURCE_BUFFER] != (void *)HookSubmit) {
            g_origSubmit = (PFN_Submit)vt[VT_SUBMIT_SOURCE_BUFFER];
            PatchSlot(&vt[VT_SUBMIT_SOURCE_BUFFER], (void *)HookSubmit);
        }
        InterlockedIncrement(&g_ad.voices);
        ReleaseSRWLockExclusive(&g_lock);
    }
    return hr;
}

void AudioDiag_OnEngine(void *engine)
{
    void **vt = *(void ***)engine;
    if (vt[VT_CREATE_SOURCE_VOICE] != (void *)HookCSV) {
        g_origCSV = (PFN_CreateSourceVoice)vt[VT_CREATE_SOURCE_VOICE];
        PatchSlot(&vt[VT_CREATE_SOURCE_VOICE], (void *)HookCSV);
    }
    InterlockedIncrement(&g_ad.engines);
}

static HRESULT WINAPI HookCreate(void **pp, UINT32 flags, UINT32 proc)
{
    HRESULT hr = g_origCreate(pp, flags, proc);
    if (SUCCEEDED(hr) && pp && *pp) AudioDiag_OnEngine(*pp);
    return hr;
}

/* Address of the delay-import slot for ordinal 1 of XAudio2_9Redist.dll, or NULL. */
void **AudioDiag_FindSlot(HMODULE mod)
{
    BYTE *base = (BYTE *)mod;
    IMAGE_NT_HEADERS64 *nt = (IMAGE_NT_HEADERS64 *)(base + ((IMAGE_DOS_HEADER *)base)->e_lfanew);
    IMAGE_DATA_DIRECTORY dir = nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT];
    if (!dir.VirtualAddress) return NULL;
    DWORD *d = (DWORD *)(base + dir.VirtualAddress);        /* attrs, name, hmod, iat, int, bound, unload, time */
    for (; d[1]; d += 8) {
        if (lstrcmpiA((char *)(base + d[1]), "XAudio2_9Redist.dll")) continue;
        ULONGLONG *names = (ULONGLONG *)(base + d[4]);
        void **iat = (void **)(base + d[3]);
        for (int i = 0; names[i]; i++)
            if ((names[i] >> 63) && (names[i] & 0xFFFF) == 1) return &iat[i];
    }
    return NULL;
}

int AudioDiag_Install(void)
{
    void **slot = AudioDiag_FindSlot(GetModuleHandleW(NULL));
    if (!slot || !*slot) return 0;
    g_origCreate = (PFN_Create)*slot;
    PatchSlot(slot, (void *)HookCreate);
    return 1;
}
