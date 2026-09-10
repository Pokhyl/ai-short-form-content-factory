import {execFile} from "node:child_process";
import {promisify} from "node:util";

const execFileAsync = promisify(execFile);

export const PIPER_MODEL_VERSION = "piper-tts-1.2.0";
export const PIPER_ALIGNMENT_PROVIDER = "self_hosted_piper_faster_whisper";
export const WHISPER_MODEL_IDENTITY = "Systran/faster-whisper-small@536b0662742c02347bc0e980a01041f333bce120";
export const WHISPER_RUNTIME_IDENTITY = "faster-whisper-1.2.1-cpu-int8";

const voices = Object.freeze({
  en: "en_US-norman-medium",
  pl: "pl_PL-darkman-medium",
  ru: "ru_RU-dmitri-medium",
  uk: "uk_UA-mykyta-high",
});

export function piperVoiceForLanguage(languageCode) {
  return voices[String(languageCode ?? "").trim().toLowerCase()] ?? null;
}

export function localTtsBudgetMilliseconds(targetDurationSeconds) {
  const target = Number(targetDurationSeconds);
  if (!Number.isFinite(target) || target <= 0) throw new Error("invalid local TTS target duration");
  return Math.min(180000, 60000 + Math.round(target * 2000));
}

export async function synthesizePiperWhisper({languageCode, narration, outputWavPath, targetDurationSeconds}) {
  const python = process.env.TTS_PYTHON || "/opt/tts-venv/bin/python";
  const helper = "/app/python/piper_whisper_fallback.py";
  const voiceDir = process.env.PIPER_VOICE_DIR || "/opt/piper-voices";
  const whisperDir = process.env.FASTER_WHISPER_MODEL_DIR || "/opt/faster-whisper-small";
  const voice = piperVoiceForLanguage(languageCode);
  if (!voice) throw new Error(`unsupported self-hosted Piper language: ${languageCode}`);
  const budget = localTtsBudgetMilliseconds(targetDurationSeconds);
  const {stdout} = await execFileAsync(python, [
    helper,
    "--language", String(languageCode),
    "--text", String(narration),
    "--output-wav", outputWavPath,
    "--voice-dir", voiceDir,
    "--whisper-dir", whisperDir,
  ], {
    timeout: budget,
    maxBuffer: 16 * 1024 * 1024,
    encoding: "utf8",
  });
  let result;
  try { result = JSON.parse(String(stdout ?? "").trim()); }
  catch { throw new Error("self-hosted Piper/Whisper helper returned invalid JSON"); }
  if (
    result?.provider !== "self_hosted_piper" ||
    result?.model !== PIPER_MODEL_VERSION ||
    result?.voice !== voice ||
    result?.alignment_provider !== "faster_whisper" ||
    result?.alignment_model !== WHISPER_MODEL_IDENTITY ||
    result?.alignment_runtime !== WHISPER_RUNTIME_IDENTITY ||
    !Array.isArray(result?.words) || result.words.length === 0
  ) {
    throw new Error("self-hosted Piper/Whisper helper returned an invalid contract");
  }
  return {...result, budget_ms: budget};
}
