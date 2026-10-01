import json, subprocess, sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from segment import speech_regions
S = os.path.dirname(os.path.abspath(__file__))
TAKE, OUT, VIDEO = sys.argv[1], sys.argv[2], sys.argv[3]   # voice take, output mp4, source promo video
VDUR = 60.033
cues = json.load(open(f"{S}/cues.json"))
groups = json.load(open(TAKE + ".groups.json"))
regions, _ = speech_regions(TAKE)
PRE, POST = 0.03, 0.07
MAXGAP, KEEPGAP = 0.45, 0.35        # tighten long mid-line pauses for punchier sync

def pieces(a, b):
    """Speech intervals for one line, with long inner pauses shortened to KEEPGAP."""
    rs = [r for r in regions if r[0] >= a - 1e-6 and r[1] <= b + 1e-6]
    out = [[rs[0][0] - PRE, rs[0][1]]]
    for r in rs[1:]:
        gap = r[0] - out[-1][1]
        if gap > MAXGAP:
            out[-1][1] += KEEPGAP / 2
            out.append([r[0] - KEEPGAP / 2, r[1]])
        else:
            out[-1][1] = r[1]
    out[-1][1] += POST
    out[0][0] = max(0, out[0][0])
    return out

parts, labels, report = [], [], []
for i, (c, (a, b)) in enumerate(zip(cues, groups)):
    pcs = pieces(a, b)
    L = sum(e - s_ for s_, e in pcs)
    win = c["end"] - c["start"] + PRE + POST
    tempo = max(1.0, L / win)
    assert tempo <= 1.08, f"line {i} needs tempo {tempo:.3f} - too much"
    placed_len = L / tempo
    start = c["start"] - PRE
    end = start + placed_len
    report.append((c["start"], end - POST, c["end"], tempo, c["text"]))
    segs = [f"[1:a]atrim={s_:.3f}:{e:.3f},asetpts=PTS-STARTPTS[p{i}_{k}]" for k, (s_, e) in enumerate(pcs)]
    if len(pcs) > 1:
        chain = ";".join(segs) + ";" + "".join(f"[p{i}_{k}]" for k in range(len(pcs))) + f"concat=n={len(pcs)}:v=0:a=1"
    else:
        chain = segs[0].rsplit("[", 1)[0]
    if tempo > 1.0: chain += f",atempo={tempo:.4f}"
    chain += f",afade=t=in:d=0.01,afade=t=out:st={max(0, placed_len-0.04):.3f}:d=0.04"
    chain += f",adelay={int(round(start*1000))}:all=1[v{i}]"
    parts.append(chain); labels.append(f"[v{i}]")

# check no overlaps and nothing past the video end
for (s1, e1, _, _, _), (s2, _, _, _, _) in zip(report, report[1:]):
    assert e1 <= s2, f"overlap at {s1}"
assert report[-1][1] < VDUR - 0.3

import re
def run(args): subprocess.run(["ffmpeg", "-v", "error", "-y"] + args, check=True)
def dur(f): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout)
def lufs(f):
    e = subprocess.run(["ffmpeg", "-i", f, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+([-\d.]+) LUFS", e)[-1])

ST = "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo"
VOX, MIX = OUT + ".vox.wav", OUT + ".mix.wav"

# Stage 1: voice stem, full video length, stereo 48k
fc = ";".join(parts)
fc += f";{''.join(labels)}amix=inputs={len(labels)}:normalize=0:dropout_transition=0,{ST},highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=2,apad=whole_dur={VDUR}[vox]"
run(["-i", VIDEO, "-i", TAKE, "-filter_complex", fc, "-map", "[vox]", "-t", str(VDUR), "-c:a", "pcm_s16le", VOX])
run(["-i", VOX, "-af", f"volume={-16 - lufs(VOX):.2f}dB", "-c:a", "pcm_s16le", VOX + ".n.wav"]); subprocess.run(["mv", VOX + ".n.wav", VOX])

# Stage 2: music bed lowered and ducked under the voice, then mixed
fc2 = (f"[1:a]{ST},asplit=2[v1][vsc];[0:a]{ST},volume=0.32[mus];"
       f"[mus][vsc]sidechaincompress=threshold=0.02:ratio=6:attack=15:release=400[duck];"
       f"[v1][duck]amix=inputs=2:normalize=0:duration=longest[mix]")
run(["-i", VIDEO, "-i", VOX, "-filter_complex", fc2, "-map", "[mix]", "-t", str(VDUR), "-c:a", "pcm_s16le", MIX])

# Stage 3: fixed gain to -14 LUFS, limiter for peaks, mux with the untouched video stream
g = -14 - lufs(MIX)
run(["-i", VIDEO, "-i", MIX, "-filter_complex", f"[1:a]volume={g:.2f}dB,alimiter=limit=0.84:level=false,{ST}[a]",
     "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(VDUR), "-movflags", "+faststart", OUT])
for f in (VOX, MIX, OUT): print(f"duration {f.rsplit('/',1)[-1]}: {dur(f):.3f}s")
print(f"{'on-screen':>9} {'voice end':>9} {'scene end':>9} tempo  line")
for s, e, w, t, txt in report:
    print(f"{s:9.2f} {e:9.2f} {w:9.2f} {t:5.3f}  {txt}")
