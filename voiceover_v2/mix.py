"""Mix voice stem over the (extended) music with ducking; -14 LUFS; mux with the re-timed video.
usage: mix.py <video_retimed.mp4> <vox.wav> <music.wav> <out.mp4>"""
import re, subprocess, sys
VID, VOX, MUS, OUT = sys.argv[1:5]
ST = "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo"
def ff(a): subprocess.run(["ffmpeg", "-v", "error", "-y"] + a, check=True)
def lufs(f):
    e = subprocess.run(["ffmpeg", "-i", f, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+([-\d.]+) LUFS", e)[-1])
dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", VID], capture_output=True, text=True).stdout.strip()
vn, mix = OUT + ".vox.wav", OUT + ".mix.wav"
ff(["-i", VOX, "-af", f"volume={-16 - lufs(VOX):.2f}dB,{ST}", "-c:a", "pcm_s16le", vn])
fc = (f"[0:a]{ST},asplit=2[v1][vsc];[1:a]{ST},volume=0.30[mus];"
      f"[mus][vsc]sidechaincompress=threshold=0.02:ratio=6:attack=15:release=400[duck];"
      f"[v1][duck]amix=inputs=2:normalize=0:duration=longest[m]")
ff(["-i", vn, "-i", MUS, "-filter_complex", fc, "-map", "[m]", "-t", dur, "-c:a", "pcm_s16le", mix])
g = -14 - lufs(mix)
ff(["-i", VID, "-i", mix, "-filter_complex", f"[1:a]volume={g:.2f}dB,alimiter=limit=0.84:level=false,{ST}[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", dur, "-movflags", "+faststart", OUT])
for f in (vn, mix): subprocess.run(["rm", "-f", f])
