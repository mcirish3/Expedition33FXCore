"""Draw the mod page images for Expedition33FXCore (1920x1080 gallery images and a 1300x372 header)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
F = "C:/Windows/Fonts/"


def font(bold, size):
    return ImageFont.truetype(F + ("segoeuib.ttf" if bold else "segoeui.ttf"), size)


BG, PANEL, LINE = (16, 22, 30), (26, 35, 47), (52, 66, 84)
TEXT, MUTED, GOLD = (232, 236, 241), (150, 163, 179), (231, 176, 74)
TEAL, RED, BLUE = (72, 186, 168), (214, 96, 86), (96, 150, 222)


def centered(d, x0, w, y, s, f, fill):
    d.text((x0 + (w - d.textlength(s, font=f)) / 2, y), s, font=f, fill=fill)


def base(title, sub):
    im = Image.new("RGB", (1920, 1080), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1920, 8), fill=GOLD)
    d.text((110, 60), title, font=font(True, 80), fill=TEXT)
    d.text((114, 170), sub, font=font(False, 32), fill=MUTED)
    return im, d


def main_image():
    im = Image.new("RGB", (1920, 1080), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1920, 8), fill=GOLD)
    d.text((110, 60), "Expedition33FXCore", font=font(True, 96), fill=TEXT)
    d.text((114, 190), "CPU scheduling + audio fix for Clair Obscur: Expedition 33 on older CPUs", font=font(False, 42), fill=GOLD)
    d.text((114, 256), "No graphics settings changed  \u00b7  No game files touched  \u00b7  Open source (MIT)",
           font=font(False, 28), fill=MUTED)
    stats = [("+11\u201316%", "average FPS", TEAL), ("137 \u2192 40", "stutters > 50 ms / min", BLUE),
             ("~90%", "fewer audio dropouts", GOLD)]
    for i, (big, small, col) in enumerate(stats):
        x = 110 + i * 580
        d.rounded_rectangle((x, 350, x + 540, 610), 18, fill=PANEL, outline=col, width=4)
        centered(d, x, 540, 380, big, font(True, 96), col)
        centered(d, x, 540, 520, small, font(False, 34), TEXT)
    d.text((110, 670), "Measured on an AMD FX-8350 + Radeon RX 6600, 1080p, Epic, XeSS native (PresentMon)",
           font=font(False, 30), fill=MUTED)
    d.text((110, 760), "What it does", font=font(True, 36), fill=TEXT)
    items = ["Game, render and RHI threads each get their own CPU module or core",
             "Background loading work is kept off those cores",
             "The audio mixer gets time-critical priority and its own core",
             "Bigger engine audio buffer (2048 x 4) against crackle and static",
             "0.5 ms timer  \u00b7  no Windows power throttling  \u00b7  priority floors"]
    for i, s in enumerate(items):
        d.text((130, 820 + i * 46), "\u2022  " + s, font=font(False, 30), fill=TEXT)
    im.save(OUT / "e33-1-main.png", optimize=True)


def results_image():
    im, d = base("Measured on the test PC",
                 "FX-8350  \u00b7  RX 6600  \u00b7  1080p Epic  \u00b7  XeSS native  \u00b7  stock and mod alternated in one session")
    rows = [("Light area", 22.2, 25.8), ("Heavy area", 20.7, 23.0)]
    y = 260
    for name, a, b in rows:
        d.text((110, y), name + "  (average FPS)", font=font(True, 36), fill=TEXT)
        for j, (lab, v, col) in enumerate((("Stock", a, LINE), ("With the mod", b, TEAL))):
            yy = y + 60 + j * 70
            d.rounded_rectangle((110, yy, 110 + int(1300 * v / 30), yy + 56), 10, fill=col)
            d.text((130, yy + 8), f"{lab}: {v:.1f}", font=font(True, 30), fill=TEXT if col == LINE else BG)
        y += 230
    d.rounded_rectangle((110, 740, 930, 1000), 16, fill=PANEL, outline=BLUE, width=3)
    d.text((140, 760), "Stutters over 50 ms", font=font(True, 34), fill=BLUE)
    d.text((140, 820), "137 \u2192 40 a minute", font=font(True, 60), fill=TEXT)
    d.text((140, 920), "GPU was the limit 25% \u2192 84% of the time", font=font(False, 28), fill=MUTED)
    d.rounded_rectangle((990, 740, 1810, 1000), 16, fill=PANEL, outline=GOLD, width=3)
    d.text((1020, 760), "Audio dropouts (crackle)", font=font(True, 34), fill=GOLD)
    d.text((1020, 820), "~25 \u2192 ~3 a minute", font=font(True, 60), fill=TEXT)
    d.text((1020, 920), "Counted in the audio itself; areas not matched", font=font(False, 28), fill=MUTED)
    im.save(OUT / "e33-2-results.png", optimize=True)


def log_image():
    im, d = base("Check it's working", r"Sandfall\Binaries\Win64\Expedition33FXCore.log, written at every launch")
    lines = [
        r"Expedition33FXCore 1.0.0 loaded into ...\SandFall-Win64-Shipping.exe",
        "Audio buffer: set 2048 frames x 4 buffers in Engine.ini",
        "CPU: AMD FX(tm)-8350 Eight-Core Processor",
        "Topology: 8 logical processors, 4 execution groups, 1 L3 domain(s)",
        "Timer resolution: 0.500 ms",
        "Power throttling opt-out: ok (execution speed only)",
        "Process priority: raised",
        "Critical LPs: game 0, render 2, rhi 4, audio 6 | background mask 0xaa",
        "  GameThread       tid 34812  prio 1 (game's own: 0)",
        "  RHIThread        tid 34808  prio 1 (game's own: 0)",
        "  RenderThread     tid 34292  prio 1 (game's own: 0)",
        "  AudioMixer       tid 35276  prio 15 (game's own: 2)",
    ]
    d.rounded_rectangle((110, 240, 1810, 940), 16, fill=PANEL, outline=LINE, width=3)
    mono = ImageFont.truetype(F + "consola.ttf", 34)
    for i, s in enumerate(lines):
        d.text((150, 272 + i * 54), s, font=mono, fill=GOLD if "Audio" in s else TEXT)
    d.text((110, 990), "No log file means the DLL did not load.", font=font(False, 28), fill=MUTED)
    im.save(OUT / "e33-3-log.png", optimize=True)


def header():
    im = Image.new("RGB", (1300, 372), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1300, 6), fill=GOLD)
    d.text((70, 70), "Expedition33FXCore", font=font(True, 80), fill=TEXT)
    d.text((74, 186), "CPU scheduling + audio fix for older CPUs", font=font(False, 38), fill=GOLD)
    d.text((74, 254), "+11\u201316% FPS  \u00b7  fewer stutters  \u00b7  ~90% less crackle (FX-8350)", font=font(False, 26), fill=MUTED)
    im.save(OUT / "e33-header-1300x372.png", optimize=True)


main_image()
results_image()
log_image()
header()
print("ok")
