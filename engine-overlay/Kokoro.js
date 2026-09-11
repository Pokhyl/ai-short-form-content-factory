"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Kokoro = void 0;
const config_1 = require("../../config");
const EDGE_VOICES = [
  "en-US-AndrewNeural",
  "pl-PL-MarekNeural",
  "ru-RU-DmitryNeural",
  "uk-UA-OstapNeural",
];
class Kokoro {
  baseUrl;
  constructor(baseUrl) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }
  async generate(text, voice) {
    const selectedVoice = voice || "en-US-AndrewNeural";
    const response = await fetch(`${this.baseUrl}/synthesize`, {
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
    const audio = audioBuffer.buffer.slice(
      audioBuffer.byteOffset,
      audioBuffer.byteOffset + audioBuffer.byteLength,
    );
    const audioLength = Number(payload.audio_length);
    if (!Number.isFinite(audioLength) || audioLength <= 0) {
      throw new Error("Edge TTS returned invalid audio length");
    }
    config_1.logger.debug({ text, voice: selectedVoice, audioLength }, "Audio generated with Edge TTS");
    return { audio, audioLength };
  }
  static async init(_dtype) {
    return new Kokoro(process.env.EDGE_TTS_URL || "http://edge-tts:3002");
  }
  listAvailableVoices() {
    return EDGE_VOICES;
  }
}
exports.Kokoro = Kokoro;
