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

const wavDurationSeconds = (buffer) => {
  if (buffer.length < 44 || buffer.toString("ascii", 0, 4) !== "RIFF") {
    throw new Error("Piper TTS returned invalid WAV data");
  }

  let byteRate = 0;
  let dataSize = 0;
  let offset = 12;
  while (offset + 8 <= buffer.length) {
    const chunkId = buffer.toString("ascii", offset, offset + 4);
    const chunkSize = buffer.readUInt32LE(offset + 4);
    if (chunkId === "fmt " && chunkSize >= 16 && offset + 24 <= buffer.length) {
      byteRate = buffer.readUInt32LE(offset + 16);
    }
    if (chunkId === "data") {
      dataSize = Math.min(chunkSize, Math.max(0, buffer.length - (offset + 8)));
      break;
    }
    offset += 8 + chunkSize + (chunkSize % 2);
  }

  if (!byteRate || !dataSize) {
    throw new Error("Piper TTS WAV is missing timing metadata");
  }
  return dataSize / byteRate;
};

class Kokoro {
  baseUrl;
  piperBaseUrl;

  constructor(baseUrl, piperBaseUrl) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.piperBaseUrl = piperBaseUrl.replace(/\/$/, "");
  }

  async generate(text, voice) {
    const selectedVoice = voice || "en-US-AndrewNeural";

    if (selectedVoice === "uk-UA-OstapNeural") {
      const response = await fetch(`${this.piperBaseUrl}/synthesize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(`Piper TTS failed: ${response.status} ${detail}`);
      }

      const audioBuffer = Buffer.from(await response.arrayBuffer());
      const audioLength = wavDurationSeconds(audioBuffer);
      const audio = audioBuffer.buffer.slice(
        audioBuffer.byteOffset,
        audioBuffer.byteOffset + audioBuffer.byteLength,
      );
      config_1.logger.debug(
        { text, voice: "uk_UA-mykyta-high", audioLength },
        "Audio generated with Piper TTS",
      );
      return { audio, audioLength };
    }

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
    config_1.logger.debug(
      { text, voice: selectedVoice, audioLength },
      "Audio generated with Edge TTS",
    );
    return { audio, audioLength };
  }

  static async init(_dtype) {
    return new Kokoro(
      process.env.EDGE_TTS_URL || "http://edge-tts:3002",
      process.env.PIPER_TTS_URL || "http://piper-tts:5000",
    );
  }

  listAvailableVoices() {
    return EDGE_VOICES;
  }
}

exports.Kokoro = Kokoro;
