"""Re-time the promo so a longer narration fits.

Each narration line is anchored to the moment its text/feature appears in the
original video. Where a line needs more time than the original footage gives,
that stretch of video is slowed (frame-blended), keeping text intros and scene
transitions at normal speed. Voice lines are then placed on the re-timed anchors.

usage: retime.py <take.mp3> <source_video> <out_dir>
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TAKE, VIDEO, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
VDUR = 60.033
chunks = json.load(open(os.path.join(HERE, "chunks.json")))
N = len(chunks)

GAP = 0.40            # breathing room after each line
LEAD = 0.10           # voice starts this long after its anchor
END_MARGIN = 1.20     # end card keeps showing after the last word
INTRO, OUTRO = 0.45, 0.35   # real-time text intro / scene transition
PRE, POST = 0.03, 0.07
MAXGAP, KEEPGAP = 0.45, 0.35  # shorten long mid-line pauses

def ff(args): subprocess.run(["ffmpeg", "-v", "error", "-y"] + args, check=True)
def dur(f): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout)

# ---- 1. split the take into lines -------------------------------------------
def speech_regions(path, noise="-42dB", d=0.10):
    err = subprocess.run(["ffmpeg", "-i", path, "-af", f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"], capture_output=True, text=True).stderr
    total = dur(path)
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    regions, cur = [], 0.0
    for s, e in zip(st, en + [total] * (len(st) - len(en))):
        if s > cur: regions.append([cur, s])
        cur = e
    if cur < total: regions.append([cur, total])
    return [r for r in regions if r[1] - r[0] > 0.05]

regions = speech_regions(TAKE)
gaps = sorted(range(len(regions) - 1), key=lambda i: regions[i + 1][0] - regions[i][1], reverse=True)
cuts = sorted(gaps[: N - 1])
lines, s0 = [], 0
for c in cuts + [len(regions) - 1]:
    lines.append(regions[s0: c + 1]); s0 = c + 1
split_gaps = sorted(lines[i + 1][0][0] - lines[i][-1][1] for i in range(N - 1))
inner_gaps = sorted((r2[0] - r1[1] for ln in lines for r1, r2 in zip(ln, ln[1:])), reverse=True)
print(f"split gaps min {split_gaps[0]:.2f}s | longest in-line pause {inner_gaps[0] if inner_gaps else 0:.2f}s")
assert split_gaps[0] > (inner_gaps[0] if inner_gaps else 0) + 0.15, "line splits are ambiguous"

def pieces(ln):
    out = [[ln[0][0] - PRE, ln[0][1]]]
    for r in ln[1:]:
        if r[0] - out[-1][1] > MAXGAP:
            out[-1][1] += KEEPGAP / 2; out.append([r[0] - KEEPGAP / 2, r[1]])
        else:
            out[-1][1] = r[1]
    out[-1][1] += POST; out[0][0] = max(0, out[0][0])
    return out
P = [pieces(ln) for ln in lines]
L = [sum(e - s for s, e in p) for p in P]
if os.environ.get("CHECK"):
    for c, l, ln in zip(chunks, L, lines):
        print(f"  {l:5.2f}s  {len(c['text'].split()):2d}w  {len(c['text'].split())/l:4.1f}w/s  {c['text'][:70]}")
    sys.exit(0)

# ---- 2. video time map --------------------------------------------------------
segs = []   # (src_start, src_end, speed)  speed<1 = slowed
if chunks[0]["at"] > 0: segs.append((0.0, chunks[0]["at"], 1.0))
for i, c in enumerate(chunks):
    a = c["at"]; last = i == N - 1
    b = VDUR if last else chunks[i + 1]["at"]
    D = b - a
    need = L[i] + LEAD + (END_MARGIN if last else GAP)
    p = min(c.get("intro", INTRO), 0.3 * D) if c["scene"] else 0.0
    q = 0.0 if last or not chunks[i + 1]["scene"] else min(OUTRO, 0.2 * D)
    if D >= need:
        segs.append((a, b, 1.0)); continue
    k = (D - p - q) / (need - p - q)
    if p: segs.append((a, a + p, 1.0))
    segs.append((a + p, b - q, k))
    if q: segs.append((b - q, b, 1.0))

def warp(t):
    out = 0.0
    for s, e, k in segs:
        if t >= e: out += (e - s) / k
        else:
            if t > s: out += (t - s) / k
            break
    return out
TOTAL = warp(VDUR)

# ---- 3. render re-timed video (silent) ---------------------------------------
# Each piece gets an exact frame count taken from the warp, so frame rounding
# never accumulates into drift between picture and voice.
parts, t_out = [], 0.0
for j, (s, e, k) in enumerate(segs):
    n = round((t_out + (e - s) / k) * 30) - round(t_out * 30)
    t_out += (e - s) / k
    f = f"[0:v]trim={s:.4f}:{e + 0.2:.4f},setpts=(PTS-STARTPTS)/{k:.5f}"
    f += ",framerate=fps=30" if k < 0.999 else ",fps=30"
    f += f",trim=end_frame={n},setpts=N/(30*TB)"
    parts.append(f + f"[s{j}]")
fc = ";".join(parts) + ";" + "".join(f"[s{j}]" for j in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=0,format=yuv420p[v]"
VID = os.path.join(OUT, "video_retimed.mp4")
ff(["-i", VIDEO, "-filter_complex", fc, "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-r", "30", "-movflags", "+faststart", VID])

# ---- 4. voice stem on the new timeline ----------------------------------------
ST = "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo"
vparts, labels, report = [], [], []
for i, c in enumerate(chunks):
    start = warp(c["at"]) + LEAD
    segs_a = [f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS[p{i}_{m}]" for m, (s, e) in enumerate(P[i])]
    body = ";".join(segs_a) + ";" + "".join(f"[p{i}_{m}]" for m in range(len(P[i]))) + f"concat=n={len(P[i])}:v=0:a=1"
    body += f",afade=t=in:d=0.01,afade=t=out:st={max(0, L[i] - 0.04):.3f}:d=0.04,adelay={int(round((start - PRE) * 1000))}:all=1[v{i}]"
    vparts.append(body); labels.append(f"[v{i}]")
    nxt = TOTAL if i == N - 1 else warp(chunks[i + 1]["at"])
    report.append((start, start + L[i] - PRE - POST, nxt, c["text"]))
for (s1, e1, n1, _), (s2, *_rest) in zip(report, report[1:]):
    assert e1 < s2, "overlap"
assert report[-1][1] < TOTAL - 0.8
VOX = os.path.join(OUT, "vox.wav")
vfc = ";".join(vparts) + f";{''.join(labels)}amix=inputs={N}:normalize=0:dropout_transition=0,{ST},highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=2,apad=whole_dur={TOTAL:.3f}[vox]"
ff(["-i", TAKE, "-filter_complex", vfc, "-map", "[vox]", "-t", f"{TOTAL:.3f}", "-c:a", "pcm_s16le", VOX])

json.dump({"total": TOTAL, "segments": segs, "lines": [{"start": s, "end": e, "next": n, "text": t} for s, e, n, t in report]},
          open(os.path.join(OUT, "timeline.json"), "w"), indent=1)
print(f"new length {TOTAL:.2f}s (was {VDUR:.2f}s); video {dur(VID):.2f}s, voice stem {dur(VOX):.2f}s")
print(f"{'voice in':>8} {'voice out':>9} {'next':>7}  line")
for s, e, n, t in report: print(f"{s:8.2f} {e:9.2f} {n:7.2f}  {t[:70]}")
slow = [(s, e, k) for s, e, k in segs if k < 1]
print("slowest stretch: %.2fx at source %.2f-%.2f" % min(((k, s, e) for s, e, k in slow), default=(1, 0, 0)))
