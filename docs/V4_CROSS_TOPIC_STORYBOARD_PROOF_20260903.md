# V4 Cross-Topic Storyboard + Actual-Audio Proof — 2026-09-03

This stage intentionally stops tuning the induction fixture and builds three materially different non-induction cases before another renderer decision.

## Cases

- `eiffel-pl` — exact place/history, Polish, target 30 s.
- `zipper-ru` — object/mechanism, Russian, target 30 s.
- `oled-en` — technical comparison, English, target 30 s.

Combined machine-readable fixture:

`prototype/v4/fixtures/cross_topic_storyboards_20260903.json`

Runtime working set:

`/opt/ai-short-form-v4-runs/cross-topic-20260903/`

## Evidence sources

Eiffel:
- official Eiffel Tower history and construction pages (`toureiffel.paris`);
- exact historic construction media is retrieved separately from Wikimedia Commons, preferring public-domain originals.

Zipper:
- YKK product education states that the slider bends the elements so that they engage; reversing the slider separates them;
- exact macro zipper photography may support the hook/close, but generic fashion footage is not accepted.

OLED vs LCD:
- LG official OLED technical material states that conventional LCD uses a backlight and liquid crystal layer, while OLED does not require a backlight and is self-emissive;
- the mechanism is therefore represented primarily by constructed side-by-side motion graphics rather than random TV/phone stock.

## Speech / actual-audio timing

No rate or pitch fitting was used.

Isolated V4 tooling environment was recreated at `/opt/ai-short-form-v4-tools` using:
- `edge-tts 7.2.7`;
- `faster-whisper 1.1.0`;
- `requests` (required because the pinned faster-whisper package did not import without it in the fresh environment);
- `mutagen` for exact MP3 duration measurement.

The existing local `Systran/faster-whisper-small` cache was reused; the model was not downloaded again.

Measured audio durations:
- Eiffel PL: first draft 24.816 s -> script expanded with one source-backed rivet fact -> final 28.584 s;
- zipper RU: 28.128 s;
- OLED EN: 30.312 s.

Whisper detected the requested language with probability 1.0 for all three runs.

The director text remains the canonical caption text; Whisper timings are the timing source. Ordinary recognition substitutions (including written digits in transcription) are not sent back to TTS.

## Timeline contract result

All three actual-duration timelines passed the same `prototype/v4/timeline_contract.py` structural contract:

- Eiffel: 7 beats; 6 exact, 1 constructed, 0 contextual;
- zipper: 6 beats; 2 exact, 4 constructed, 0 contextual;
- OLED: 6 beats; 0 exact, 6 constructed, 0 contextual.

Full V4 contract suite remains `12/12 PASS`.

No timeline uses:
- text-only primary visuals;
- generic factual fallback stock;
- fullscreen landscape photos;
- contextual media without explicit justification.

## Renderer finding before implementation

The currently checked-out OpenMontage renderer was searched for a generic diagram/flow/process primitive. It has presentation components such as `ComparisonCard`, but no general mechanism/flow primitive suitable for zipper engagement, OLED light paths and Eiffel prefabrication alignment.

Because standalone title/card presentation was already a verified HUMAN FAIL mode, the next implementation must not substitute those components for actual mechanism visuals.

Any new constructed-visual primitive must be exercised on multiple matrix cases, not written only for zipper or OLED.
