"""Extend the promo's original 120 BPM music to the re-timed length by repeating
whole bars/beats, keeping its four structural hits on the matching visuals.
usage: music.py <source_video> <timeline.json> <out.wav>"""
import json, subprocess, sys
VIDEO, TL, OUT = sys.argv[1:4]
BEAT, PHASE, SRC_END = 0.4996, 0.012, 60.01
tl = json.load(open(TL)); segs = tl["segments"]; TOTAL = tl["total"]
def warp(t):
    out = 0.0
    for s, e, k in segs:
        if t >= e: out += (e - s) / k
        else:
            if t > s: out += (t - s) / k
            break
    return out
def G(x):  # snap to the beat grid, cut 10 ms ahead of the beat
    return 0.0 if x == 0 else PHASE + round((x - PHASE) / BEAT) * BEAT - 0.010
T = {h: warp(G(h) + 0.010) for h in (6, 42, 46, 54)}
sections = [  # (pieces in original-music seconds, target end on new timeline)
    ([(0, 6)], T[6]),
    ([(6, 30), (14, 30), (26, 42)], T[42]),
    ([(42, 44), (43, 44), (44, 46)], T[46]),
    ([(46, 52), (48, 52), (48, 52), (50, 52), (52, 54)], T[54]),
]
parts, labels, t = [], [], None
delay = T[6] - (G(6) - G(0))
for si, (pcs, tend) in enumerate(sections):
    tstart = delay if si == 0 else sections[si - 1][1]
    srclen = sum(G(b) - G(a) for a, b in pcs)
    tempo = srclen / (tend - tstart)
    assert 0.94 < tempo < 1.06 or si == 0, f"section {si} tempo {tempo:.3f}"
    ins = []
    for pi, (a, b) in enumerate(pcs):
        f = f"[0:a]atrim={G(a):.4f}:{G(b):.4f},asetpts=PTS-STARTPTS"
        if pi > 0: f += ",afade=t=in:d=0.004"
        if pi < len(pcs) - 1: f += f",afade=t=out:st={G(b) - G(a) - 0.004:.4f}:d=0.004"
        parts.append(f + f"[m{si}_{pi}]"); ins.append(f"[m{si}_{pi}]")
    f = "".join(ins) + f"concat=n={len(ins)}:v=0:a=1"
    if abs(tempo - 1) > 1e-4: f += f",atempo={tempo:.5f}"
    parts.append(f + f"[sec{si}]"); labels.append(f"[sec{si}]")
    print(f"section {si}: {srclen:6.2f}s of source -> {tend - tstart:6.2f}s (tempo x{tempo:.4f}), ends at {tend:6.2f}")
parts.append(f"[0:a]atrim={G(54):.4f}:{SRC_END},asetpts=PTS-STARTPTS[sec4]"); labels.append("[sec4]")
print(f"outro: starts {T[54]:.2f}, ends {T[54] + SRC_END - G(54):.2f} (video ends {TOTAL:.2f})")
fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=0:a=1,adelay={int(round(delay * 1000))}:all=1,apad=whole_dur={TOTAL:.3f}[mus]"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO, "-filter_complex", fc, "-map", "[mus]", "-t", f"{TOTAL:.3f}", "-ar", "48000", "-c:a", "pcm_s16le", OUT], check=True)
print("hits on new timeline:", {k: round(v, 2) for k, v in T.items()}, f"music delay {delay:.2f}s")
