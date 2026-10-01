# SignalDart promo v2: full narration

`../SignalDart_Promo_VO_v2.mp4` is a 1:34 cut of `Promo-1.m4v`. Each feature gets 2–3 sentences of energetic narration, and the video is slowed only where a line needs more time.

- **Voice:** ElevenLabs "Christina – Energetic Commercial American Female Voice" (`BuaKXS4Sv1Mccaw3flfU`), `eleven_multilingual_v2`
- **Length:** 93.73 s (original 60.03 s). Picture and audio are both exactly 2,812 frames long, so they never drift apart.
- **Mix:** -14.3 LUFS integrated, peak -1.1 dBFS, stereo 48 kHz AAC 192k. The voice sits about 11 dB above the music while she speaks.

## How it was re-timed

Each narration line is anchored to the moment its text or feature appears in the original video (`chunks.json`). Where a line needs more time than the footage gives, only that stretch is slowed, with frame blending to keep motion smooth. Text intros and scene transitions stay at normal speed, so headlines still snap in. The slowest stretch is 0.19x, on the "Six engines" card hold. Every line ends at least 0.4 s before the next one starts.

The original **120 BPM music** is extended by repeating whole bars, so its four hits still land on the visuals:

| Hit | Original | New | How |
|---|---:|---:|---|
| Logo reveal | 6.0 s | 7.3 s | music starts 1.3 s in |
| Breakdown ("Nothing here is invented") | 42.0 s | 63.0 s | +10 bars of main groove, tempo x1.004 |
| Return hit ("Six engines") | 46.0 s | 68.3 s | +2 beats, tempo x0.95 |
| End-card hit | 54.0 s | 86.4 s | +5 bars before the fill, tempo x0.994 |

## Script and timing

| Voice in (s) | Voice out (s) | Line |
|---:|---:|---|
| 0.2 | 1.0 | You have an idea. |
| 2.1 | 3.0 | And forty tabs open. |
| 4.0 | 4.8 | One messy spreadsheet. |
| 5.4 | 6.7 | And it's still just a hunch. |
| 7.3 | 7.9 | Meet Signal Dart. |
| 9.6 | 12.0 | Validate the idea. Then watch the market. All in one place. |
| 12.6 | 14.0 | Just describe your idea in one sentence. |
| 14.6 | 19.4 | Signal Dart finds your competitors, reads their pricing pages, and measures real search demand, all on its own. |
| 20.0 | 25.2 | In minutes, your market is mapped. Competitors, features, search demand, and a clear opportunity score. |
| 25.8 | 28.9 | These are your real competitors, with live data on every single one. |
| 29.5 | 33.5 | Funding, pricing, reviews, even who they're hiring. All in one view. |
| 34.1 | 38.3 | Every feature, verified. Signal Dart checks each one against the competitor's own website. |
| 38.9 | 42.0 | So you can spot the features buyers want, that almost nobody offers. |
| 42.6 | 47.5 | Find the demand they missed. See what real buyers search for every month, and the keywords nobody ranks for yet. |
| 48.1 | 54.7 | Spot the gap, and price it right. Uncover the pain points customers complain about, and see exactly where your price lands against every rival. |
| 55.3 | 56.8 | Research it once. Then watch it. |
| 57.9 | 62.8 | When a rival cuts prices, ships a new feature, raises money, or starts hiring, you hear about it first. |
| 63.4 | 64.5 | And nothing here is invented. |
| 65.1 | 68.1 | Every single figure links straight back to the page it came from. |
| 68.7 | 77.2 | Six powerful engines. Competitor research, SEO intelligence, market gap analysis, an AI strategy advisor, autonomous monitoring, and executive reports. |
| 77.8 | 81.4 | One clear answer. Export it to PDF, PowerPoint, or Notion. |
| 82.0 | 83.9 | Validate the idea. Then watch the market. |
| 84.5 | 86.0 | Get started free. No credit card needed. |
| 87.1 | 87.6 | Signal Dart. |
| 88.2 | 89.8 | Know your market. Beat the competition. |
| 90.4 | 92.4 | Start free today, at signal dart dot com. |

## Files

- `vo_stem_synced.mp3`: voice only, on the 1:34 timeline
- `music_extended.mp3`: the extended original music, on the same timeline
- `elevenlabs_raw_take.mp3`: the unedited ElevenLabs take, with 1.5 s breaks between lines
- `chunks.json`: script lines and their anchor times in the original video
- `timeline.json`: the computed speed map and line placements
- `retime.py`, `music.py`, `mix.py`: the pipeline below

## Rebuild

```sh
python3 retime.py elevenlabs_raw_take.mp3 /path/to/Promo-1.m4v out     # slowed video + voice stem
python3 music.py /path/to/Promo-1.m4v out/timeline.json out/music.wav  # extended music
python3 mix.py out/video_retimed.mp4 out/vox.wav out/music.wav out/final.mp4
```

To change a line, edit `chunks.json`, generate a new take with the same text joined by `<break time="1.5s" />`, and rerun the three commands. Running `CHECK=1 python3 retime.py <take> x y` first prints each line's length so you can confirm the take split correctly. `retime.py` refuses to build if the line splits are ambiguous, if lines overlap, or if the last line runs into the end of the video.
