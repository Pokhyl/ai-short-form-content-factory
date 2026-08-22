# Voiceover Decision — Source of Truth

Last updated: 2026-08-22

This file locks the initial voiceover method and voice presets for the clean rebuild.
Do not re-run voice selection unless a real quality or provider-availability problem appears.

## Method

Provider: **Google Cloud Text-to-Speech**

Request method:

```text
POST https://texttospeech.googleapis.com/v1/text:synthesize
```

Authentication:

```text
Google OAuth2
```

Output:

```text
MP3
```

The n8n workflow sends the narration text and the selected language/voice pair to Google TTS, receives `audioContent` as base64, decodes it to MP3, and passes the audio file to media-worker for storage/measurement.

## Locked voice profile

Profile name:

```text
google-selected-v1
```

| Language | Locale | Voice | Model family |
| --- | --- | --- | --- |
| English | `en-US` | `en-US-Chirp3-HD-Algenib` | Chirp 3 HD |
| Polish | `pl-PL` | `pl-PL-Chirp3-HD-Enceladus` | Chirp 3 HD |
| Russian | `ru-RU` | `ru-RU-Wavenet-D` | WaveNet |
| Ukrainian | `uk-UA` | `uk-UA-Chirp3-HD-Enceladus` | Chirp 3 HD |

These are the exact presets recovered from the previous working WF03 configuration. They are not newly guessed replacements.

## Runtime JSON body

The new n8n implementation should use the same simple request shape:

```json
{
  "input": {
    "text": "<scene narration>"
  },
  "voice": {
    "languageCode": "<locale>",
    "name": "<voice name>"
  },
  "audioConfig": {
    "audioEncoding": "MP3"
  }
}
```

## Rules

1. Do not use speaking-rate manipulation to force the requested video duration.
2. Measure the real MP3 duration with ffprobe after synthesis.
3. Scene timing follows the real narration duration.
4. Do not silently switch voice names or providers.
5. If Google removes or materially changes one of these voices, stop that language and make an explicit replacement decision.
6. Voice credentials and OAuth tokens are runtime secrets and must never be committed to Git.
