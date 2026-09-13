"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.Whisper = exports.ErrorWhisper = void 0;
const install_whisper_cpp_1 = require("@remotion/install-whisper-cpp");
const path_1 = __importDefault(require("path"));
const logger_1 = require("../../logger");
exports.ErrorWhisper = new Error("There was an error with WhisperCpp");
class Whisper {
    config;
    constructor(config) {
        this.config = config;
    }
    static async init(config) {
        if (!config.runningInDocker) {
            logger_1.logger.debug("Installing WhisperCpp");
            await (0, install_whisper_cpp_1.installWhisperCpp)({
                to: config.whisperInstallPath,
                version: config.whisperVersion,
                printOutput: true,
            });
            logger_1.logger.debug("WhisperCpp installed");
            logger_1.logger.debug("Downloading Whisper model");
            await (0, install_whisper_cpp_1.downloadWhisperModel)({
                model: config.whisperModel,
                folder: path_1.default.join(config.whisperInstallPath, "models"),
                printOutput: config.whisperVerbose,
                onProgress: (downloadedBytes, totalBytes) => {
                    const progress = `${Math.round((downloadedBytes / totalBytes) * 100)}%`;
                    logger_1.logger.debug({ progress, model: config.whisperModel }, "Downloading Whisper model");
                },
            });
        }
        return new Whisper(config);
    }
    async CreateCaption(audioPath) {
        logger_1.logger.debug({ audioPath }, "Starting word-aligned audio timing extraction");
        const { transcription, result } = await (0, install_whisper_cpp_1.transcribe)({
            model: this.config.whisperModel,
            whisperPath: this.config.whisperInstallPath,
            modelFolder: path_1.default.join(this.config.whisperInstallPath, "models"),
            whisperCppVersion: this.config.whisperVersion,
            inputPath: audioPath,
            tokenLevelTimestamps: false,
            tokensPerItem: 1,
            splitOnWord: true,
            language: "auto",
            printOutput: this.config.whisperVerbose,
            onProgress: (progress) => {
                logger_1.logger.debug({ audioPath, progress }, "Word timing extraction progress");
            },
        });
        const captions = (Array.isArray(transcription) ? transcription : [])
            .map((record) => ({
                text: String(record.text || "").trim(),
                startMs: Number(record.offsets?.from),
                endMs: Number(record.offsets?.to),
            }))
            .filter((item) => item.text && Number.isFinite(item.startMs) && Number.isFinite(item.endMs) && item.endMs > item.startMs);
        logger_1.logger.debug({ audioPath, language: result?.language || null, captionCount: captions.length }, "Extracted real audio word timings");
        return captions;
    }
}
exports.Whisper = Whisper;
