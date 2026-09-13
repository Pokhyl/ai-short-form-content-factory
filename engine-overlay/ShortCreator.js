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
const child_process_1 = require("child_process");
const logger_1 = require("../logger");

const runFfmpeg = (args) => new Promise((resolve, reject) => {
    const child = (0, child_process_1.spawn)("/usr/bin/ffmpeg", args, { stdio: ["ignore", "ignore", "pipe"] });
    let stderr = "";
    child.stderr.on("data", (chunk) => { stderr += chunk.toString(); });
    child.on("error", reject);
    child.on("close", (code) => {
        if (code === 0) return resolve();
        reject(new Error(`ffmpeg portrait composition failed (${code}): ${stderr.slice(-1200)}`));
    });
});

const downloadMediaFile = (media, targetPath) => new Promise((resolve, reject) => {
    const fileStream = fs_extra_1.default.createWriteStream(targetPath);
    const request = https_1.default.get(media.url, {
        headers: {
            "User-Agent": "ai-short-form-content-factory/1.0 (https://github.com/Pokhyl/ai-short-form-content-factory)",
        },
    }, (response) => {
        if (response.statusCode !== 200) {
            response.resume();
            fileStream.destroy();
            fs_extra_1.default.unlink(targetPath, () => { });
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
        fs_extra_1.default.unlink(targetPath, () => { });
        reject(err);
    });
});

const buildPortraitFrame = async (inputPaths, outputPath) => {
    const tileCount = inputPaths.length;
    const tileHeight = Math.floor(1920 / tileCount);
    const args = ["-hide_banner", "-loglevel", "error", "-y"];
    inputPaths.forEach((file) => args.push("-i", file));
    if (tileCount === 1) {
        args.push(
            "-filter_complex",
            "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,setsar=1[out]",
            "-map", "[out]",
            "-frames:v", "1",
            "-q:v", "2",
            outputPath,
        );
    } else {
        const filters = inputPaths.map((_, index) =>
            `[${index}:v]scale=1080:${tileHeight}:force_original_aspect_ratio=decrease,pad=1080:${tileHeight}:(ow-iw)/2:(oh-ih)/2:black,setsar=1[v${index}]`,
        );
        const stackInputs = inputPaths.map((_, index) => `[v${index}]`).join("");
        filters.push(`${stackInputs}vstack=inputs=${tileCount}[out]`);
        args.push(
            "-filter_complex", filters.join(";"),
            "-map", "[out]",
            "-frames:v", "1",
            "-q:v", "2",
            outputPath,
        );
    }
    await runFfmpeg(args);
};

const normalizeAlignmentToken = (value) => String(value || "")
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[’ʼ']/g, "")
    .replace(/[^\p{L}\p{N}]+/gu, "");

const tokenizeAlignmentText = (text) => (String(text || "").match(/[\p{L}\p{N}]+(?:[’ʼ'’-][\p{L}\p{N}]+)*/gu) || [])
    .map(normalizeAlignmentToken)
    .filter(Boolean);

const alignmentSubstitutionCost = (left, right) => {
    if (left === right) return 0;
    if (!left || !right) return 1;
    const shorter = Math.min(left.length, right.length);
    if (shorter >= 4 && (left.startsWith(right) || right.startsWith(left))) return 0.25;
    if (shorter >= 5 && left.slice(0, 4) === right.slice(0, 4)) return 0.45;
    return 1;
};

const buildSceneCaptionAlignment = (inputScenes, captions) => {
    const transcriptTokens = [];
    const sceneTokenEnds = [];
    for (const scene of inputScenes) {
        transcriptTokens.push(...tokenizeAlignmentText(scene.text));
        sceneTokenEnds.push(transcriptTokens.length - 1);
    }
    const captionEntries = captions
        .map((caption, index) => ({ index, token: normalizeAlignmentToken(caption.text) }))
        .filter((entry) => entry.token);
    const n = transcriptTokens.length;
    const m = captionEntries.length;
    if (!n || !m) {
        return {
            endIndices: sceneTokenEnds.map((_, index) => index === sceneTokenEnds.length - 1
                ? captions.length
                : Math.max(1, Math.min(captions.length - (sceneTokenEnds.length - index - 1), Math.round(captions.length * ((index + 1) / sceneTokenEnds.length))))),
            boundarySources: sceneTokenEnds.map((_, index) => index === sceneTokenEnds.length - 1 ? "final" : "scene_proportional_fallback"),
            matchedTokens: 0,
            transcriptTokens: n,
            captionTokens: m,
            matchRatio: 0,
        };
    }
    const dp = Array.from({ length: n + 1 }, () => new Float64Array(m + 1));
    const dir = Array.from({ length: n + 1 }, () => new Uint8Array(m + 1));
    for (let i = 1; i <= n; i++) { dp[i][0] = i; dir[i][0] = 1; }
    for (let j = 1; j <= m; j++) { dp[0][j] = j; dir[0][j] = 2; }
    for (let i = 1; i <= n; i++) {
        for (let j = 1; j <= m; j++) {
            const substitutionCost = alignmentSubstitutionCost(transcriptTokens[i - 1], captionEntries[j - 1].token);
            const diagonal = dp[i - 1][j - 1] + substitutionCost;
            const deletion = dp[i - 1][j] + 1;
            const insertion = dp[i][j - 1] + 1;
            if (diagonal <= deletion && diagonal <= insertion) {
                dp[i][j] = diagonal;
                dir[i][j] = 3;
            }
            else if (deletion <= insertion) {
                dp[i][j] = deletion;
                dir[i][j] = 1;
            }
            else {
                dp[i][j] = insertion;
                dir[i][j] = 2;
            }
        }
    }
    const inputToCaption = new Map();
    let i = n;
    let j = m;
    while (i > 0 || j > 0) {
        const direction = dir[i][j];
        if (i > 0 && j > 0 && direction === 3) {
            const cost = alignmentSubstitutionCost(transcriptTokens[i - 1], captionEntries[j - 1].token);
            if (cost <= 0.45) inputToCaption.set(i - 1, captionEntries[j - 1].index);
            i--;
            j--;
        }
        else if (i > 0 && (direction === 1 || j === 0)) {
            i--;
        }
        else if (j > 0) {
            j--;
        }
        else {
            break;
        }
    }
    const endIndices = [];
    const boundarySources = [];
    let previousEnd = 0;
    for (let sceneIndex = 0; sceneIndex < sceneTokenEnds.length; sceneIndex++) {
        if (sceneIndex === sceneTokenEnds.length - 1) {
            endIndices.push(captions.length);
            boundarySources.push("final");
            break;
        }
        const tokenBoundary = sceneTokenEnds[sceneIndex];
        let mappedCaption = inputToCaption.get(tokenBoundary);
        let source = "aligned_exact_boundary";
        if (mappedCaption === undefined) {
            for (let offset = 1; offset <= 4 && mappedCaption === undefined; offset++) {
                const left = inputToCaption.get(tokenBoundary - offset);
                if (left !== undefined) {
                    mappedCaption = left;
                    source = "aligned_nearest_left";
                }
            }
        }
        if (mappedCaption === undefined) {
            for (let offset = 1; offset <= 4 && mappedCaption === undefined; offset++) {
                const right = inputToCaption.get(tokenBoundary + offset);
                if (right !== undefined) {
                    mappedCaption = Math.max(0, right - 1);
                    source = "aligned_nearest_right";
                }
            }
        }
        const remainingScenes = sceneTokenEnds.length - sceneIndex - 1;
        const minEnd = Math.min(captions.length, previousEnd + 1);
        const maxEnd = Math.max(previousEnd, captions.length - remainingScenes);
        let endIndex;
        if (mappedCaption !== undefined) {
            endIndex = mappedCaption + 1;
        }
        else {
            const tokenFraction = (tokenBoundary + 1) / Math.max(1, transcriptTokens.length);
            endIndex = Math.round(captions.length * tokenFraction);
            source = "token_proportional_fallback";
        }
        endIndex = Math.max(minEnd, Math.min(maxEnd, endIndex));
        endIndices.push(endIndex);
        boundarySources.push(source);
        previousEnd = endIndex;
    }
    return {
        endIndices,
        boundarySources,
        matchedTokens: inputToCaption.size,
        transcriptTokens: n,
        captionTokens: m,
        matchRatio: Number((inputToCaption.size / n).toFixed(4)),
    };
};

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
        // todo add mutex lock
        const id = (0, cuid_1.default)();
        this.queue.push({
            sceneInput,
            config,
            id,
        });
        if (this.queue.length === 1) {
            this.processQueue();
        }
        return id;
    }
    async processQueue() {
        // todo add a semaphore
        if (this.queue.length === 0) {
            return;
        }
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
        if (!Array.isArray(inputScenes) || inputScenes.length === 0) {
            throw new Error("At least one scene is required");
        }
        inputScenes = this.pexelsApi.prepareScenes(inputScenes);
        const preflightMedia = await this.pexelsApi.preflightScenes(inputScenes);
        const orientation = config.orientation || shorts_1.OrientationEnum.portrait;
        const narrationText = inputScenes.map((scene) => String(scene.text || "").trim()).filter(Boolean).join(" ").replace(/\s+/g, " ").trim();
        if (!narrationText) {
            throw new Error("Narration text is empty");
        }
        const requestedTargetSeconds = Number(config.targetDurationSeconds);
        const hasRequestedTarget = Number.isFinite(requestedTargetSeconds) && requestedTargetSeconds > 0;
        const narration = await this.kokoro.generate(
            narrationText,
            config.voice ?? "en-US-AndrewNeural",
            hasRequestedTarget ? requestedTargetSeconds : null,
        );
        const audioLength = narration.audioLength;
        const audioStream = narration.audio;
        const durationDeltaSeconds = hasRequestedTarget ? requestedTargetSeconds - audioLength : null;
        if (hasRequestedTarget && (durationDeltaSeconds < -0.35 || durationDeltaSeconds > 1.5)) {
            throw new Error(`Narration duration ${audioLength.toFixed(3)}s is outside target ${requestedTargetSeconds.toFixed(3)}s tolerance`);
        }
        const effectivePaddingBack = hasRequestedTarget
            ? Math.max(0, Math.round(durationDeltaSeconds * 1000))
            : (config.paddingBack || 0);
        logger_1.logger.debug({
            audioLength,
            requestedTargetSeconds: hasRequestedTarget ? requestedTargetSeconds : null,
            durationDeltaSeconds,
            effectivePaddingBack,
        }, "Resolved final duration padding");
        const tempFiles = [];
        const excludeVideoIds = [];
        const scenes = [];
        const sceneAudit = [];
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
            logger_1.logger.debug({ captionCount: fullCaptions.length }, "Using TTS caption timings");
        }
        await this.ffmpeg.saveToMp3(audioStream, tempMp3Path);
        const narrationUrl = `http://localhost:${this.config.port}/api/tmp/${tempMp3FileName}`;
        const renderInputScenes = inputScenes.map((scene) => ({
            ...scene,
            mediaContext: String(scene.mediaContext || scene.text || "").trim(),
        }));
        const wordCounts = renderInputScenes.map((scene) => Math.max(1, tokenizeAlignmentText(scene.text).length));
        const totalWords = wordCounts.reduce((sum, count) => sum + count, 0);
        const captionAlignment = buildSceneCaptionAlignment(renderInputScenes, fullCaptions);
        logger_1.logger.debug({
            semanticSceneCount: inputScenes.length,
            renderSceneCount: renderInputScenes.length,
            audioLength,
            captionAlignment,
        }, "Using semantic scenes aligned to real audio word timings");

        let captionCursor = 0;
        let cumulativeWords = 0;
        let sceneStartSeconds = 0;
        for (let index = 0; index < renderInputScenes.length; index++) {
            const scene = renderInputScenes[index];
            const sceneWordCount = wordCounts[index];
            const isLastScene = index === renderInputScenes.length - 1;
            cumulativeWords += sceneWordCount;
            const plannedCaptionEnd = Number(captionAlignment.endIndices[index]);
            const captionEndIndex = isLastScene
                ? fullCaptions.length
                : Math.max(captionCursor + 1, Math.min(fullCaptions.length, Number.isFinite(plannedCaptionEnd) ? plannedCaptionEnd : captionCursor + 1));
            const boundarySource = captionAlignment.boundarySources[index] || (isLastScene ? "final" : "unknown");
            const sceneCaptionSlice = fullCaptions.slice(captionCursor, captionEndIndex);
            const proportionalEndSeconds = audioLength * (cumulativeWords / totalWords);
            const captionTimedEndSeconds = sceneCaptionSlice.length
                ? Number(sceneCaptionSlice[sceneCaptionSlice.length - 1].endMs) / 1000
                : proportionalEndSeconds;
            const sceneEndSeconds = isLastScene
                ? audioLength
                : Math.min(audioLength, Math.max(sceneStartSeconds + 0.25, captionTimedEndSeconds));
            const sceneDuration = Math.max(0.25, sceneEndSeconds - sceneStartSeconds);
            const sceneStartMs = sceneStartSeconds * 1000;
            const captions = sceneCaptionSlice
                .map((caption) => ({
                    ...caption,
                    startMs: Math.max(0, caption.startMs - sceneStartMs),
                    endMs: Math.min(sceneDuration * 1000, Math.max(0, caption.endMs - sceneStartMs)),
                }))
                .filter((caption) => caption.endMs > caption.startMs);
            const requiredVideoDuration = sceneDuration + (isLastScene && effectivePaddingBack ? effectivePaddingBack / 1000 : 0);
            const primary = preflightMedia[index];
            let mediaType = primary.kind === "image" ? "image" : "video";
            let finalMediaFileName = null;

            const downloadWithRetry = async (media, targetPath) => {
                for (let attempt = 1; attempt <= 5; attempt++) {
                    try {
                        await downloadMediaFile(media, targetPath);
                        return;
                    }
                    catch (error) {
                        const retryable = error?.statusCode === 429 || error?.statusCode >= 500;
                        if (!retryable || attempt === 5) throw error;
                        const waitMs = Math.max(1200, (error.retryAfter || 0) * 1000, attempt * 1500);
                        logger_1.logger.warn({ attempt, waitMs, statusCode: error.statusCode, url: media.url }, "Media download throttled; retrying");
                        await new Promise((resolve) => setTimeout(resolve, waitMs));
                    }
                }
            };

            const shots = await this.pexelsApi.planShots(primary, requiredVideoDuration);
            const preparedFiles = new Map();
            const visuals = [];
            for (const shot of shots) {
                const media = shot.media;
                if (!preparedFiles.has(media.mediaKey)) {
                    const inputPaths = [];
                    for (const component of media.components || [media]) {
                        const inputPath = path_1.default.join(this.config.tempDirPath, `${(0, cuid_1.default)()}${component.extension}`);
                        tempFiles.push(inputPath);
                        await downloadWithRetry(component, inputPath);
                        inputPaths.push(inputPath);
                    }
                    if (media.kind === "image") {
                        const frameName = `${(0, cuid_1.default)()}.jpg`;
                        const framePath = path_1.default.join(this.config.tempDirPath, frameName);
                        tempFiles.push(framePath);
                        await buildPortraitFrame(inputPaths, framePath);
                        preparedFiles.set(media.mediaKey, frameName);
                    } else {
                        preparedFiles.set(media.mediaKey, path_1.default.basename(inputPaths[0]));
                    }
                }
                visuals.push({
                    url: `http://localhost:${this.config.port}/api/tmp/${preparedFiles.get(media.mediaKey)}`,
                    mediaType: media.kind,
                    startSeconds: shot.startSeconds,
                    durationSeconds: shot.durationSeconds,
                });
            }
            finalMediaFileName = preparedFiles.get(primary.mediaKey);

            sceneAudit.push({
                sceneIndex: index,
                narrationText: String(scene.text || "").trim(),
                startSeconds: Number(sceneStartSeconds.toFixed(3)),
                endSeconds: Number(sceneEndSeconds.toFixed(3)),
                durationSeconds: Number(sceneDuration.toFixed(3)),
                captionStartIndex: captionCursor,
                captionEndIndex,
                boundarySource,
                groundedEntity: primary.groundedEntity || null,
                groundedEntityId: primary.groundedEntityId,
                subjectEvidence: primary.subject,
                sourceRevision: primary.sourceRevision,
                mediaKey: primary.mediaKey,
                reuseReason: primary.reuseReason || null,
                components: primary.components || null,
                visualShots: shots.map(shot => ({startSeconds: shot.startSeconds, durationSeconds: shot.durationSeconds, mediaKey: shot.media.mediaKey, title: shot.media.title, source: shot.media.source, holdReason: shot.holdReason || null})),
                visualQuery: primary.visualQuery || null,
                selectedMediaTitle: primary.title || null,
                selectedMediaSource: primary.source || null,
                selectedMediaResolution: primary.resolutionType || null,
                selectedMediaConfidence: primary.confidence || null,
                mediaType,
                sourceWidth: primary.width || null,
                sourceHeight: primary.height || null,
                outputWidth: 1080,
                outputHeight: 1920,
            });
            scenes.push({
                captions,
                video: `http://localhost:${this.config.port}/api/tmp/${finalMediaFileName}`,
                visuals,
                mediaType,
                audio: { url: narrationUrl, duration: sceneDuration },
            });
            captionCursor = captionEndIndex;
            sceneStartSeconds = sceneEndSeconds;
        }
        const paddingSeconds = effectivePaddingBack / 1000;
        const totalDuration = audioLength + paddingSeconds;
        const selectedMusic = this.findMusic(totalDuration, config.music);
        logger_1.logger.debug({ selectedMusic, audioLength, sceneCount: scenes.length }, "Rendering continuous narration video");
        await this.remotion.render({
            music: selectedMusic,
            scenes,
            config: {
                durationMs: totalDuration * 1000,
                paddingBack: effectivePaddingBack,
                captionBackgroundColor: config.captionBackgroundColor,
                captionPosition: config.captionPosition,
                musicVolume: config.musicVolume,
            },
        }, videoId, orientation);
        const auditPath = path_1.default.join(this.config.videosDirPath, `${videoId}.audit.json`);
        await fs_extra_1.default.writeJson(auditPath, {
            videoId,
            renderer: "semantic_scene_word_aligned_v2",
            tts: {
                provider: narration.model ? "gemini" : "edge",
                model: narration.model || null,
                voice: narration.voice || config.voice || null,
                synthesisRequests: narration.ttsRequestCount || 1,
                audioLengthSeconds: Number(audioLength.toFixed(3)),
                targetDurationSeconds: hasRequestedTarget ? requestedTargetSeconds : null,
                sampleRate: narration.sampleRate || null,
                channels: narration.channels || null,
            },
            captionTiming: {
                source: Array.isArray(narration.captions) && narration.captions.length > 0 ? "tts" : "whisper",
                captionCount: fullCaptions.length,
                alignment: captionAlignment,
            },
            semanticSceneCount: renderInputScenes.length,
            scenes: sceneAudit,
            paddingSeconds: Number(paddingSeconds.toFixed(3)),
            totalRenderDurationSeconds: Number(totalDuration.toFixed(3)),
            output: { width: 1080, height: 1920 },
        }, { spaces: 2 });
        for (const file of tempFiles) {
            fs_extra_1.default.removeSync(file);
        }
        return videoId;
    }
    getVideoPath(videoId) {
        return path_1.default.join(this.config.videosDirPath, `${videoId}.mp4`);
    }
    deleteVideo(videoId) {
        const videoPath = this.getVideoPath(videoId);
        fs_extra_1.default.removeSync(videoPath);
        logger_1.logger.debug({ videoId }, "Deleted video file");
    }
    getVideo(videoId) {
        const videoPath = this.getVideoPath(videoId);
        if (!fs_extra_1.default.existsSync(videoPath)) {
            throw new Error(`Video ${videoId} not found`);
        }
        return fs_extra_1.default.readFileSync(videoPath);
    }
    findMusic(videoDuration, tag) {
        const musicFiles = this.musicManager.musicList().filter((music) => {
            if (tag) {
                return music.mood === tag;
            }
            return true;
        });
        return musicFiles[Math.floor(Math.random() * musicFiles.length)];
    }
    ListAvailableMusicTags() {
        const tags = new Set();
        this.musicManager.musicList().forEach((music) => {
            tags.add(music.mood);
        });
        return Array.from(tags.values());
    }
    listAllVideos() {
        const videos = [];
        // Check if videos directory exists
        if (!fs_extra_1.default.existsSync(this.config.videosDirPath)) {
            return videos;
        }
        // Read all files in the videos directory
        const files = fs_extra_1.default.readdirSync(this.config.videosDirPath);
        // Filter for MP4 files and extract video IDs
        for (const file of files) {
            if (file.endsWith(".mp4")) {
                const videoId = file.replace(".mp4", "");
                let status = "ready";
                const inQueue = this.queue.find((item) => item.id === videoId);
                if (inQueue) {
                    status = "processing";
                }
                videos.push({ id: videoId, status });
            }
        }
        // Add videos that are in the queue but not yet rendered
        for (const queueItem of this.queue) {
            const existingVideo = videos.find((v) => v.id === queueItem.id);
            if (!existingVideo) {
                videos.push({ id: queueItem.id, status: "processing" });
            }
        }
        return videos;
    }
    ListAvailableVoices() {
        return this.kokoro.listAvailableVoices();
    }
}
exports.ShortCreator = ShortCreator;
