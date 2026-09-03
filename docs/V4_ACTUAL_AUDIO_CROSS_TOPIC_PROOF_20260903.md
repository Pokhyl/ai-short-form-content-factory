# V4 Actual-Audio Cross-Topic Proof — 2026-09-03

## Purpose

Continue V4 as an automation project, not as manual production of one polished fixture. Three non-induction matrix cases were advanced through the same speech/timing/timeline contracts:

- `Jak zbudowano Wieżę Eiffla` — Polish, exact place/history;
- `Как работает молния на одежде` — Russian, object/mechanism;
- `OLED vs LCD: what actually changes` — English, comparison/mechanism.

Production semantic-v3 remained frozen.

## Tooling recovery

The earlier disk cleanup had removed the old MoneyPrinterTurbo Python environment. The Whisper model cache survived under `/root/.cache/huggingface`.

A separate V4-only tooling environment was restored at `/opt/ai-short-form-v4-tools` with:

- `edge-tts 7.2.7`;
- `faster-whisper`;
- `requests`.

This did not modify production containers.

## Speech guard

All three final scripts passed the existing general speech-ready guard before synthesis.

An initial English comparison script was rejected because it contained the ambiguous abbreviations `OLED` and `LCD`. The spoken script was corrected generically by expanding the names to `organic light emitting diode display` and `liquid crystal display`. The abbreviations remain suitable only as visual labels.

No acronym-specific TTS bypass was added.

## Real audio + Whisper results

One continuous Edge voice track was synthesized per matrix case at natural rate, without speed fitting.

### Eiffel / Polish

- voice: `pl-PL-MarekNeural`;
- speech-ready script words: `63`;
- actual Whisper duration: `27.34 s`;
- Whisper language probability: `1.0`;
- Whisper segments: `5`;
- audio SHA256: `711d0e23b02fcd536df83da524e756f61674523403815a6b6039bc6629169ec9`;
- script SHA256: `3ed155f6496f912fe1b1e4e85434722746cd37662388bafb1433608d9dd960db`.

### Zipper / Russian

- voice: `ru-RU-DmitryNeural`;
- speech-ready script words: `59`;
- actual Whisper duration: `27.14 s`;
- Whisper language probability: `1.0`;
- Whisper segments: `8`;
- audio SHA256: `0cf7c311ca6affac26ae39eab19308ce7d6c4482dd87e0eb010593f0502d668c`;
- script SHA256: `6710dcb57cdb6c1f0ee2f6df3def6518e904bec0d49a5eb474b84c7a6a177b38`.

### OLED/LCD / English

- voice: `en-US-AndrewNeural`;
- speech-ready script words: `87`;
- actual Whisper duration: `32.34 s`;
- Whisper language probability: `1.0`;
- Whisper segments: `6`;
- audio SHA256: `bd1f5b6d3401e8972134dacc7c505a692fbf65dc6737a78cc2398345d104e22b`;
- script SHA256: `08b25e10b36cdbfc5d585d79642d3f7e818cc8f0d783bcf1e481de9a9252a15a`.

## Stale-artifact failure discovered

The cross-topic run directories already contained older `director.json` and `timeline.json` files whose narration and durations no longer matched the current scripts/audio.

This is a general automation defect: a later stage could accidentally render an old storyboard/timeline against new narration while still producing technically valid files.

Do not fix this by manually deleting selected files per fixture.

## General fix

New module:

`prototype/v4/timeline_builder.py`

New CLI commands:

- `compile-timeline`;
- `validate-timeline`.

The compiler receives:

- current script file;
- exact current audio file;
- Whisper output from that audio;
- semantic visual obligations with no invented timestamps.

It then:

1. derives beat timing from actual Whisper segment starts;
2. keeps silence gaps covered by the preceding meaningful visual beat;
3. records `script_sha256` and `audio_sha256` provenance in the timeline;
4. runs the shared structural timeline contract before writing a candidate timeline.

Remote commits:

- actual-audio timeline builder: `9c6216638639ad9b2a196cc96df978a2a382b053`;
- builder tests: `af4cde4c147bc4271e46d78d588dce4ae42fa86f`;
- CLI integration: `d9b0e342926160b152ad40336865c3a7c23fd4f3`.

Local VPS commit:

`f73d7cab98148e4c5c842ae03722c0f9d187d554`

Full V4 focused suite after the change: `15/15 PASS`.

The CLI was run independently for Eiffel, zipper and OLED. Its outputs byte-matched the reference compiler output in all three cases.

## Cross-topic timelines now passing the same contract

### Eiffel

- `5` actual-audio beats;
- `2` exact-media beats;
- `3` constructed motion/diagram beats;
- duration `27.34 s`.

### Zipper

- `8` actual-audio beats;
- `1` exact portrait macro-media beat;
- `7` constructed mechanism beats;
- duration `27.14 s`.

### OLED/LCD

- `6` actual-audio beats;
- `6` constructed comparison/mechanism beats;
- duration `32.34 s`.

All three reject text-only primary visuals and generic factual fallback stock through the same `timeline_contract.py`.

## Evidence basis used for the three reference directors

- Eiffel Tower official history/construction material: `https://www.toureiffel.paris/en/the-monument/history`;
- YKK zipper structure / Y-shaped slider tunnel: `https://www.ykk.com/english/ykk/tech/01.html`;
- slider two-channel convergence detail: `https://patents.google.com/patent/US20230380550A1/en`;
- LG OLED panel structure: `https://www.lg.com/uk/business/commercial-display/resources-guides/technology-solution/oled-technology/`;
- Samsung OLED architecture description: `https://www.samsung.com/us/computing/monitors/oled-monitor/`.

These reference directors are matrix fixtures for proving downstream automation. They are not evidence that the automatic semantic-director provider is solved yet.

## Immediate next action

Do not render hand-picked fixture assets manually.

Build the next reusable automation layer:

1. exact-media acquisition with source/license/provenance metadata for declared `exact_media` obligations;
2. constructed motion-graphic payloads for declared `motion_graphic/diagram` obligations;
3. deterministic render input generated from the compiled timeline;
4. render multiple matrix cases through the same general renderer contract;
5. review complete exact videos and record failures before changing the architecture.

No n8n/DB production rebuild yet. M8 remains `2/10` until human-approved direct prototypes exist across materially different cases.
