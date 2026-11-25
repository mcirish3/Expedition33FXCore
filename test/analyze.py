r"""Per-mode results from one recorded session: python -I analyze.py captures\<stamp>"""
import csv, re, sys
from collections import defaultdict
base = sys.argv[1]; SETTLE = 5.0; QPF = 10_000_000
log = open(base + ".mod.log", encoding="utf-8", errors="replace").read().splitlines()
marks = [(int(m[2]), m[1]) for l in log if (m := re.search(r"AB: mode=(\w+) qpc=(\d+)", l))]
F = lambda r, k: float(r[k]) if r.get(k) not in (None, "", "NA") else None
rows = defaultdict(list)
with open(base + ".frames.csv", encoding="utf-8", errors="replace") as fh:
    for r in csv.DictReader(fh):
        if F(r, "MsBetweenPresents") is not None: rows[r["SwapChainAddress"]].append(r)
if not rows: sys.exit("no frames")
chain = max(rows, key=lambda k: len(rows[k])); fr = rows[chain]
print(f"swapchains {[(k, len(v)) for k, v in rows.items()]}; using the busiest")
def stats(fs):
    ft = sorted(F(r, "MsBetweenPresents") for r in fs); n = len(ft); tot = sum(ft)
    worst = ft[-max(1, n // 100):]
    cb = [x for r in fs if (x := F(r, "MsCPUBusy")) is not None]; gb = [x for r in fs if (x := F(r, "MsGPUBusy")) is not None]
    gl = sum(1 for r in fs if (F(r, "MsGPUBusy") or 0) >= 0.9 * F(r, "MsBetweenPresents"))
    mins = tot / 60000
    return dict(sec=tot / 1000, fps=1000 * n / tot, low1=1000 * len(worst) / sum(worst), p99=ft[int(n * .99)], h50=sum(x > 50 for x in ft) / mins,
                h100=sum(x > 100 for x in ft) / mins, worst=ft[-1], cpu=sum(cb) / max(1, len(cb)), gpu=sum(gb) / max(1, len(gb)), gbound=100 * gl / n)
hdr = f"{'':22}{'sec':>6}{'fps':>7}{'1%low':>7}{'p99ms':>7}{'>50/m':>7}{'>100/m':>7}{'worst':>7}{'cpuMs':>7}{'gpuMs':>7}{'gpuLim%':>8}"
def line(n, s): print(f"{n:22}{s['sec']:6.0f}{s['fps']:7.1f}{s['low1']:7.1f}{s['p99']:7.1f}{s['h50']:7.1f}{s['h100']:7.1f}{s['worst']:7.0f}{s['cpu']:7.1f}{s['gpu']:7.1f}{s['gbound']:8.0f}")
print(hdr); line("whole session", stats(fr))
per = defaultdict(list)
for i, (q, m) in enumerate(marks):
    end = marks[i + 1][0] if i + 1 < len(marks) else 1 << 62
    b = [r for r in fr if q + SETTLE * QPF <= int(float(r["TimeInQPC"])) < end]
    if len(b) < 200: continue
    s = stats(b); line(f"  block {i + 1:2d} {m}", s); per[m].append((b, s))
for m, v in per.items(): line("ALL " + m, stats([r for b, _ in v for r in b]))
au = defaultdict(lambda: [0, 0, 0.0, 0])
for l in log:
    if (m := re.search(r"Audio (\w+): buffers (\d+)\s+dropouts (\d+)\s+\(([\d.]+) ms cut\)\s+queue-empty (\d+) \| (.*)", l)):
        a = au[m[1]]; a[0] += int(m[2]); a[1] += int(m[3]); a[2] += float(m[4]); a[3] += int(m[5]); tail = m[6]
for m, a in au.items(): print(f"AUDIO {m:10} buffers {a[0]}  dropouts {a[1]}  cut {a[2]:.0f} ms  queue-empty {a[3]}")
if au: print("AUDIO format:", tail)