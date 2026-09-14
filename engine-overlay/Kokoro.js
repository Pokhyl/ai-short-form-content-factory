"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Kokoro = void 0;
const config_1 = require("../../config");

const AVAILABLE_VOICES = [
  "en-US-AndrewNeural",
  "pl-PL-MarekNeural",
  "ru-RU-DmitryNeural",
  "gemini:Enceladus",
];

const toArrayBuffer = (buffer) => buffer.buffer.slice(
  buffer.byteOffset,
  buffer.byteOffset + buffer.byteLength,
);

const pcm16ToWav = (pcm, sampleRate, channels) => {
  const bitsPerSample = 16;
  const blockAlign = channels * 2;
  const byteRate = sampleRate * blockAlign;
  const wav = Buffer.alloc(44 + pcm.length);
  wav.write("RIFF", 0, 4, "ascii");
  wav.writeUInt32LE(36 + pcm.length, 4);
  wav.write("WAVE", 8, 4, "ascii");
  wav.write("fmt ", 12, 4, "ascii");
  wav.writeUInt32LE(16, 16);
  wav.writeUInt16LE(1, 20);
  wav.writeUInt16LE(channels, 22);
  wav.writeUInt32LE(sampleRate, 24);
  wav.writeUInt32LE(byteRate, 28);
  wav.writeUInt16LE(blockAlign, 32);
  wav.writeUInt16LE(bitsPerSample, 34);
  wav.write("data", 36, 4, "ascii");
  wav.writeUInt32LE(pcm.length, 40);
  pcm.copy(wav, 44);
  return wav;
};

const deterministicCaptions = (text, audioLength) => {
  const words = String(text || "").trim().split(/\s+/).filter(Boolean);
  if (words.length === 0 || !Number.isFinite(audioLength) || audioLength <= 0) return [];
  const totalWeight = words.reduce((sum, word) => sum + Math.max(1, word.length), 0);
  let elapsedWeight = 0;
  return words.map((word, index) => {
    const weight = Math.max(1, word.length);
    const startMs = Math.round((elapsedWeight / totalWeight) * audioLength * 1000);
    elapsedWeight += weight;
    const endMs = index === words.length - 1
      ? Math.round(audioLength * 1000)
      : Math.round((elapsedWeight / totalWeight) * audioLength * 1000);
    return { text: word, startMs, endMs };
  });
};

class Kokoro {
  edgeBaseUrl;
  geminiTtsUrl;

  constructor(edgeBaseUrl, geminiTtsUrl) {
    this.edgeBaseUrl = edgeBaseUrl.replace(/\/$/, "");
    this.geminiTtsUrl = geminiTtsUrl;
  }

  async generate(text, voice, targetDurationSeconds = null) {
    const selectedVoice = voice || "en-US-AndrewNeural";
    if (selectedVoice.startsWith("gemini:")) {
      return this.generateGemini(text, selectedVoice.slice("gemini:".length), targetDurationSeconds);
    }
    return this.generateEdge(text, selectedVoice);
  }

  async generateGemini(text, voice, targetDurationSeconds = null) {
    const selectedVoice = voice || "Enceladus";
    const requestedTarget = Number(targetDurationSeconds);
    const hasTarget = Number.isFinite(requestedTarget) && requestedTarget > 0;

    const synthesize = async () => {
      const requestBody = JSON.stringify({
        text,
        voice: selectedVoice,
        target_duration_seconds: hasTarget ? requestedTarget : null,
        previous_duration_seconds: null,
      });
      const response = await fetch(this.geminiTtsUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: requestBody,
      });
      const raw = await response.text();
      if (!response.ok || !raw) {
        throw new Error(`Gemini TTS gateway failed: HTTP ${response.status} ${raw.slice(0, 300)}`);
      }
      let payload;
      try {
        payload = JSON.parse(raw);
      } catch (error) {
        throw new Error(`Gemini TTS gateway returned invalid JSON: ${String(error)}`);
      }
      if (typeof payload.audio_base64 !== "string" || payload.audio_base64.length === 0) {
        throw new Error("Gemini TTS gateway response contained no audio");
      }
      const sampleRate = Number(payload.sample_rate || 24000);
      const channels = Number(payload.channels || 1);
      if (!Number.isFinite(sampleRate) || sampleRate <= 0) throw new Error("Gemini TTS returned invalid sample rate");
      if (!Number.isFinite(channels) || channels <= 0) throw new Error("Gemini TTS returned invalid channel count");
      const pcm = Buffer.from(payload.audio_base64, "base64");
      if (pcm.length === 0 || pcm.length % (channels * 2) !== 0) {
        throw new Error("Gemini TTS returned invalid PCM length");
      }
      const audioLength = pcm.length / (sampleRate * channels * 2);
      const wav = pcm16ToWav(pcm, sampleRate, channels);
      // Gemini does not return trustworthy word timestamps in this gateway response.
      // Do not fabricate them from character lengths: ShortCreator will run the
      // single synthesized waveform through local Whisper timing extraction.
      const captions = [];
      return {
        audio: toArrayBuffer(wav),
        audioLength,
        captions,
        model: payload.model || null,
        sampleRate,
        channels,
      };
    };

    const result = await synthesize();

    config_1.logger.debug(
      {
        text,
        voice: selectedVoice,
        model: result.model,
        audioLength: result.audioLength,
        sampleRate: result.sampleRate,
        channels: result.channels,
        captionCount: result.captions.length,
        requestedTarget: hasTarget ? requestedTarget : null,
      },
      "Audio generated with Gemini TTS",
    );
    return {
      audio: result.audio,
      audioLength: result.audioLength,
      captions: result.captions,
      voice: selectedVoice,
      model: result.model,
      sampleRate: result.sampleRate,
      channels: result.channels,
      ttsRequestCount: 1,
    };
  }

  async generateEdge(text, selectedVoice) {
    const response = await fetch(`${this.edgeBaseUrl}/synthesize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, voice: selectedVoice }),
    });
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(`Edge TTS failed: ${response.status} ${detail}`);
    }
    const payload = await response.json();
    const audioBuffer = Buffer.from(payload.audio_base64, "base64");
    const audioLength = Number(payload.audio_length);
    if (!Number.isFinite(audioLength) || audioLength <= 0) {
      throw new Error("Edge TTS returned invalid audio length");
    }
    const captions = Array.isArray(payload.word_boundaries)
      ? payload.word_boundaries
          .map((item) => ({
            text: String(item.text || "").trim(),
            startMs: Number(item.start_ms),
            endMs: Number(item.end_ms),
          }))
          .filter((item) => item.text && Number.isFinite(item.startMs) && Number.isFinite(item.endMs) && item.endMs > item.startMs)
      : [];
    config_1.logger.debug(
      { text, voice: selectedVoice, audioLength, captionCount: captions.length },
      "Audio generated with Edge TTS",
    );
    return { audio: toArrayBuffer(audioBuffer), audioLength, captions };
  }

  static async init(_dtype) {
    return new Kokoro(
      process.env.EDGE_TTS_URL || "http://edge-tts:3002",
      process.env.GEMINI_TTS_URL || "http://n8n-n8n-1:5678/webhook/internal-gemini-tts",
    );
  }

  listAvailableVoices() {
    return AVAILABLE_VOICES;
  }
}

exports.Kokoro = Kokoro;
