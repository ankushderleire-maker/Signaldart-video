# SignalDart promo: voiceover

`../SignalDart_Promo_VO.mp4` is `Promo-1.m4v` with an energetic voiceover synced to the on-screen text. The original music is kept and dips under the voice. The video stream is copied as-is.

- **Voice:** ElevenLabs "Christina – Energetic Commercial American Female Voice" (`BuaKXS4Sv1Mccaw3flfU`), model `eleven_multilingual_v2`
- **Mix:** -14.5 LUFS integrated, peak -1.2 dBFS, stereo 48 kHz AAC 192k, 60.03 s (same length as the video)
- **Fit:** every line starts when its text appears and ends before the scene changes. The last line ends at 59.44 s. One line is sped up 2.8%; all others play at natural speed.

## Script and timing

| On screen at | Voice ends | Scene ends | Line |
|---:|---:|---:|---|
| 0.25 | 1.07 | 1.95 | You have an idea. |
| 2.05 | 3.41 | 3.95 | And forty tabs open. |
| 3.95 | 4.70 | 4.98 | One spreadsheet. |
| 5.00 | 5.70 | 6.00 | Still a hunch. |
| 6.35 | 7.20 | 8.00 | Meet SignalDart. |
| 8.15 | 10.35 | 10.35 | Validate the idea. Then watch the market. *(×1.028)* |
| 10.40 | 13.39 | 14.40 | One sentence in. That's all it takes to research your market. |
| 14.50 | 15.44 | 16.15 | Your market, mapped. |
| 16.25 | 19.26 | 22.05 | Your real competitors, with live data on every one of them. |
| 22.25 | 24.92 | 28.05 | Every feature, verified, right from their own websites. |
| 28.25 | 31.76 | 32.10 | Find the demand they missed. Real searches, from real buyers. |
| 32.25 | 33.86 | 36.10 | Spot the gap. Price it right. |
| 36.30 | 40.99 | 42.10 | Research it once. Then watch it. Price cuts, launches, funding. You hear it first. |
| 42.30 | 45.57 | 46.10 | Nothing here is invented. Every figure links to its source. |
| 46.30 | 46.91 | 47.70 | Six engines. |
| 47.75 | 48.31 | 49.80 | One answer. |
| 50.40 | 52.37 | 53.85 | Validate the idea. Then watch the market. |
| 54.60 | 55.15 | 55.30 | SignalDart. |
| 55.30 | 57.20 | 57.55 | Know your market. Beat the competition. |
| 57.45 | 59.44 | 59.60 | Start free at signaldart.com. |

## Files

- `vo_stem_synced_60s.mp3`: voice only, already placed on the 60 s timeline. Drop it at 0:00 in any editor to remix with different music.
- `elevenlabs_raw_take.mp3`: the unedited ElevenLabs take, with all lines in order and break pauses between them.
- `cues.json`: the target window for each line.
- `segment.py` / `build.py`: split the take at its breaks, place each line on its cue, lower the music under the voice, then set loudness and limit peaks.

## Rebuild

```sh
python3 segment.py elevenlabs_raw_take.mp3
python3 build.py elevenlabs_raw_take.mp3 out.mp4 /path/to/Promo-1.m4v
```

To change a line, edit `cues.json` and the ElevenLabs prompt, generate a new take, and run the two commands again. `build.py` refuses to build if any line would need more than an 8% speed-up, overlap the next line, or run past the end of the video.
