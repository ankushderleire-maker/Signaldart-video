import json, re, subprocess, sys
import os
S = os.path.dirname(os.path.abspath(__file__))
cues = json.load(open(f"{S}/cues.json"))

def speech_regions(path, noise="-42dB", d=0.10):
    out = subprocess.run(["ffmpeg", "-i", path, "-af", f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                               capture_output=True, text=True).stdout)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    sil = list(zip(starts, ends + [dur] * (len(starts) - len(ends))))
    regions, cur = [], 0.0
    for s, e in sil:
        if s > cur: regions.append([cur, s])
        cur = e
    if cur < dur: regions.append([cur, dur])
    return [r for r in regions if r[1] - r[0] > 0.05], dur

def group(path):
    regions, dur = speech_regions(path)
    n = len(cues)
    gaps = sorted(range(len(regions) - 1), key=lambda i: regions[i + 1][0] - regions[i][1], reverse=True)[: n - 1]
    cuts = sorted(gaps)
    groups, start = [], 0
    for c in cuts + [len(regions) - 1]:
        groups.append([regions[start][0], regions[c][1]]); start = c + 1
    gapvals = sorted(regions[i + 1][0] - regions[i][1] for i in range(len(regions) - 1))
    return groups, gapvals, dur

if __name__ == "__main__":
    path = sys.argv[1]
    groups, gapvals, dur = group(path)
    print(f"{path}: {len(groups)} lines; smallest split gap kept={sorted(gapvals, reverse=True)[len(cues)-2]:.2f}s, largest intra gap={sorted(gapvals, reverse=True)[len(cues)-1]:.2f}s")
    tot_over = 0
    for c, (a, b) in zip(cues, groups):
        L = b - a; win = c["end"] - c["start"]; fit = "OK " if L <= win else "OVER"
        if L > win: tot_over += 1
        print(f"  {fit} len={L:4.2f} win={win:4.2f} need_tempo={max(1, L/win):.3f}  {c['text'][:60]}")
    json.dump(groups, open(path + ".groups.json", "w"))
    print("lines over window:", tot_over)
