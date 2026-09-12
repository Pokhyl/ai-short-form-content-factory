"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ShortCreator = void 0;
const shorts_1 = require("./../types/shorts");
/* eslint-disable @remotion/deterministic-randomness */
const fs_extra_1 = __importDefault(require("fs-extra"));
const cuid_1 = __importDefault(require("cuid"));
const path_1 = __importDefault(require("path"));
const https_1 = __importDefault(require("https"));
const logger_1 = require("../logger");
class ShortCreator {
    config;
    remotion;
    kokoro;
    whisper;
    ffmpeg;
    pexelsApi;
    musicManager;
    queue = [];
    constructor(config, remotion, kokoro, whisper, ffmpeg, pexelsApi, musicManager) {
        this.config = config;
        this.remotion = remotion;
        this.kokoro = kokoro;
        this.whisper = whisper;
        this.ffmpeg = ffmpeg;
        this.pexelsApi = pexelsApi;
        this.musicManager = musicManager;
    }
    status(id) {
        const videoPath = this.getVideoPath(id);
        if (this.queue.find((item) => item.id === id)) {
            return "processing";
        }
        if (fs_extra_1.default.existsSync(videoPath)) {
            return "ready";
        }
        return "failed";
    }
    addToQueue(sceneInput, config) {
        const id = (0, cuid_1.default)();
        this.queue.push({ sceneInput, config, id });
        if (this.queue.length === 1) this.processQueue();
        return id;
    }
    async processQueue() {
        if (this.queue.length === 0) return;
        const { sceneInput, config, id } = this.queue[0];
        logger_1.logger.debug({ sceneInput, config, id }, "Processing video item in the queue");
        try {
            await this.createShort(id, sceneInput, config);
            logger_1.logger.debug({ id }, "Video created successfully");
        }
        catch (error) {
            logger_1.logger.error(error, "Error creating video");
        }
        finally {
            this.queue.shift();
            this.processQueue();
        }
    }
    async createShort(videoId, inputScenes, config) {
        logger_1.logger.debug({ inputScenes, config }, "Creating short video with continuous narration");
        if (!Array.isArray(inputScenes) || inputScenes.length === 0) throw new Error("At least one scene is required");
        const orientation = config.orientation || shorts_1.OrientationEnum.portrait;
        const narrationText = inputScenes.map((scene) => String(scene.text || "").trim()).filter(Boolean).join(" ").replace(/\s+/g, " ").trim();
        if (!narrationText) throw new Error("Narration text is empty");
        const narration = await this.kokoro.generate(narrationText, config.voice ?? "en-US-AndrewNeural");
        const audioLength = narration.audioLength;
        const audioStream = narration.audio;
        const tempFiles = [];
        const excludeVideoIds = [];
        const scenes = [];
        const narrationId = (0, cuid_1.default)();
        const tempWavFileName = `${narrationId}.wav`;
        const tempMp3FileName = `${narrationId}.mp3`;
        const tempWavPath = path_1.default.join(this.config.tempDirPath, tempWavFileName);
        const tempMp3Path = path_1.default.join(this.config.tempDirPath, tempMp3FileName);
        tempFiles.push(tempWavPath, tempMp3Path);
        let fullCaptions = Array.isArray(narration.captions) ? narration.captions : [];
        if (fullCaptions.length === 0) {
            await this.ffmpeg.saveNormalizedAudio(audioStream, tempWavPath);
            fullCaptions = await this.whisper.CreateCaption(tempWavPath);
            logger_1.logger.debug({ captionCount: fullCaptions.length }, "Using Whisper fallback captions");
        }
        else {
            logger_1.logger.debug({ captionCount: fullCaptions.length }, "Using Edge TTS word-boundary captions");
        }
        await this.ffmpeg.saveToMp3(audioStream, tempMp3Path);
        const narrationUrl = `http://localhost:${this.config.port}/api/tmp/${tempMp3FileName}`;
        const wordCounts = inputScenes.map((scene) => Math.max(1, String(scene.text || "").trim().split(/\s+/).filter(Boolean).length));
        const totalWords = wordCounts.reduce((sum, count) => sum + count, 0);
        let cumulativeWords = 0;
        let sceneStartSeconds = 0;
        for (let index = 0; index < inputScenes.length; index++) {
            const scene = inputScenes[index];
            cumulativeWords += wordCounts[index];
            const sceneEndSeconds = index === inputScenes.length - 1 ? audioLength : audioLength * (cumulativeWords / totalWords);
            const sceneDuration = Math.max(0.25, sceneEndSeconds - sceneStartSeconds);
            const sceneStartMs = sceneStartSeconds * 1000;
            const sceneEndMs = sceneEndSeconds * 1000;
            const captions = fullCaptions
                .filter((caption) => {
                    const midpoint = (caption.startMs + caption.endMs) / 2;
                    return midpoint >= sceneStartMs && (index === inputScenes.length - 1 ? midpoint <= sceneEndMs : midpoint < sceneEndMs);
                })
                .map((caption) => ({ ...caption, startMs: Math.max(0, caption.startMs - sceneStartMs), endMs: Math.min(sceneDuration * 1000, Math.max(0, caption.endMs - sceneStartMs)) }))
                .filter((caption) => caption.endMs > caption.startMs);
            const requiredVideoDuration = sceneDuration + (index === inputScenes.length - 1 && config.paddingBack ? config.paddingBack / 1000 : 0);
            const video = await this.pexelsApi.findVideo(scene.searchTerms, requiredVideoDuration, excludeVideoIds, orientation);
            const mediaType = video.kind === "image" ? "image" : "video";
            const mediaExtension = video.extension || (mediaType === "image" ? ".jpg" : ".mp4");
            const tempVideoFileName = `${(0, cuid_1.default)()}${mediaExtension}`;
            const tempVideoPath = path_1.default.join(this.config.tempDirPath, tempVideoFileName);
            tempFiles.push(tempVideoPath);
            logger_1.logger.debug({ mediaType, source: video.source, url: video.url }, `Downloading media to ${tempVideoPath}`);
            const downloadMedia = () => new Promise((resolve, reject) => {
                const fileStream = fs_extra_1.default.createWriteStream(tempVideoPath);
                const request = https_1.default.get(video.url, { headers: { "User-Agent": "ai-short-form-content-factory/1.0 (https://github.com/Pokhyl/ai-short-form-content-factory)" } }, (response) => {
                    if (response.statusCode !== 200) {
                        response.resume();
                        fileStream.destroy();
                        fs_extra_1.default.unlink(tempVideoPath, () => { });
                        const error = new Error(`Failed to download media: ${response.statusCode}`);
                        error.statusCode = response.statusCode;
                        error.retryAfter = Number(response.headers["retry-after"] || 0);
                        reject(error);
                        return;
                    }
                    response.pipe(fileStream);
                    fileStream.on("finish", () => fileStream.close(resolve));
                    fileStream.on("error", reject);
                });
                request.on("error", (err) => {
                    fileStream.destroy();
                    fs_extra_1.default.unlink(tempVideoPath, () => { });
                    reject(err);
                });
            });
            for (let attempt = 1; attempt <= 5; attempt++) {
                try {
                    await downloadMedia();
                    break;
                }
                catch (error) {
                    const retryable = error?.statusCode === 429 || error?.statusCode >= 500;
                    if (!retryable || attempt === 5) throw error;
                    const waitMs = Math.max(1200, (error.retryAfter || 0) * 1000, attempt * 1500);
                    logger_1.logger.warn({ attempt, waitMs, statusCode: error.statusCode, url: video.url }, "Media download throttled; retrying");
                    await new Promise((resolve) => setTimeout(resolve, waitMs));
                }
            }
            if (String(video.source || "").startsWith("wikipedia_")) await new Promise((resolve) => setTimeout(resolve, 800));
            excludeVideoIds.push(video.id);
            scenes.push({ captions, video: `http://localhost:${this.config.port}/api/tmp/${tempVideoFileName}`, mediaType, audio: { url: narrationUrl, duration: sceneDuration } });
            sceneStartSeconds = sceneEndSeconds;
        }
        const paddingSeconds = config.paddingBack ? config.paddingBack / 1000 : 0;
        const totalDuration = audioLength + paddingSeconds;
        const selectedMusic = this.findMusic(totalDuration, config.music);
        logger_1.logger.debug({ selectedMusic, audioLength, sceneCount: scenes.length }, "Rendering continuous narration video");
        await this.remotion.render({ music: selectedMusic, scenes, config: { durationMs: totalDuration * 1000, paddingBack: config.paddingBack, captionBackgroundColor: config.captionBackgroundColor, captionPosition: config.captionPosition, musicVolume: config.musicVolume } }, videoId, orientation);
        for (const file of tempFiles) fs_extra_1.default.removeSync(file);
        return videoId;
    }
    getVideoPath(videoId) { return path_1.default.join(this.config.videosDirPath, `${videoId}.mp4`); }
    deleteVideo(videoId) { fs_extra_1.default.removeSync(this.getVideoPath(videoId)); logger_1.logger.debug({ videoId }, "Deleted video file"); }
    getVideo(videoId) {
        const videoPath = this.getVideoPath(videoId);
        if (!fs_extra_1.default.existsSync(videoPath)) throw new Error(`Video ${videoId} not found`);
        return fs_extra_1.default.readFileSync(videoPath);
    }
    findMusic(videoDuration, tag) {
        const musicFiles = this.musicManager.musicList().filter((music) => tag ? music.mood === tag : true);
        return musicFiles[Math.floor(Math.random() * musicFiles.length)];
    }
    ListAvailableMusicTags() {
        const tags = new Set();
        this.musicManager.musicList().forEach((music) => tags.add(music.mood));
        return Array.from(tags.values());
    }
    listAllVideos() {
        const videos = [];
        if (!fs_extra_1.default.existsSync(this.config.videosDirPath)) return videos;
        const files = fs_extra_1.default.readdirSync(this.config.videosDirPath);
        for (const file of files) {
            if (file.endsWith(".mp4")) {
                const videoId = file.replace(".mp4", "");
                videos.push({ id: videoId, status: this.queue.find((item) => item.id === videoId) ? "processing" : "ready" });
            }
        }
        for (const queueItem of this.queue) {
            if (!videos.find((v) => v.id === queueItem.id)) videos.push({ id: queueItem.id, status: "processing" });
        }
        return videos;
    }
    ListAvailableVoices() { return this.kokoro.listAvailableVoices(); }
}
exports.ShortCreator = ShortCreator;
