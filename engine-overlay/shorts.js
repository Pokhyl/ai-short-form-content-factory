"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.createShortInput = exports.renderConfig = exports.MusicVolumeEnum = exports.OrientationEnum = exports.VoiceEnum = exports.sceneInput = exports.CaptionPositionEnum = exports.MusicMoodEnum = void 0;
const zod_1 = __importDefault(require("zod"));
var MusicMoodEnum;
(function (MusicMoodEnum) {
    MusicMoodEnum["sad"] = "sad";
    MusicMoodEnum["melancholic"] = "melancholic";
    MusicMoodEnum["happy"] = "happy";
    MusicMoodEnum["euphoric"] = "euphoric/high";
    MusicMoodEnum["excited"] = "excited";
    MusicMoodEnum["chill"] = "chill";
    MusicMoodEnum["uneasy"] = "uneasy";
    MusicMoodEnum["angry"] = "angry";
    MusicMoodEnum["dark"] = "dark";
    MusicMoodEnum["hopeful"] = "hopeful";
    MusicMoodEnum["contemplative"] = "contemplative";
    MusicMoodEnum["funny"] = "funny/quirky";
})(MusicMoodEnum || (exports.MusicMoodEnum = MusicMoodEnum = {}));
var CaptionPositionEnum;
(function (CaptionPositionEnum) {
    CaptionPositionEnum["top"] = "top";
    CaptionPositionEnum["center"] = "center";
    CaptionPositionEnum["bottom"] = "bottom";
})(CaptionPositionEnum || (exports.CaptionPositionEnum = CaptionPositionEnum = {}));
exports.sceneInput = zod_1.default.object({
    text: zod_1.default.string().describe("Text to be spoken in the video"),
    searchTerms: zod_1.default
        .array(zod_1.default.string())
        .describe("Search term for video, 1 word, and at least 2-3 search terms should be provided for each scene. Make sure to match the overall context with the word - regardless what the video search result would be."),
});
var VoiceEnum;
(function (VoiceEnum) {
    VoiceEnum["af_heart"] = "af_heart";
    VoiceEnum["af_alloy"] = "af_alloy";
    VoiceEnum["af_aoede"] = "af_aoede";
    VoiceEnum["af_bella"] = "af_bella";
    VoiceEnum["af_jessica"] = "af_jessica";
    VoiceEnum["af_kore"] = "af_kore";
    VoiceEnum["af_nicole"] = "af_nicole";
    VoiceEnum["af_nova"] = "af_nova";
    VoiceEnum["af_river"] = "af_river";
    VoiceEnum["af_sarah"] = "af_sarah";
    VoiceEnum["af_sky"] = "af_sky";
    VoiceEnum["am_adam"] = "am_adam";
    VoiceEnum["am_echo"] = "am_echo";
    VoiceEnum["am_eric"] = "am_eric";
    VoiceEnum["am_fenrir"] = "am_fenrir";
    VoiceEnum["am_liam"] = "am_liam";
    VoiceEnum["am_michael"] = "am_michael";
    VoiceEnum["am_onyx"] = "am_onyx";
    VoiceEnum["am_puck"] = "am_puck";
    VoiceEnum["am_santa"] = "am_santa";
    VoiceEnum["bf_emma"] = "bf_emma";
    VoiceEnum["bf_isabella"] = "bf_isabella";
    VoiceEnum["bm_george"] = "bm_george";
    VoiceEnum["bm_lewis"] = "bm_lewis";
    VoiceEnum["bf_alice"] = "bf_alice";
    VoiceEnum["bf_lily"] = "bf_lily";
    VoiceEnum["bm_daniel"] = "bm_daniel";
    VoiceEnum["bm_fable"] = "bm_fable";
})(VoiceEnum || (exports.VoiceEnum = VoiceEnum = {}));
var OrientationEnum;
(function (OrientationEnum) {
    OrientationEnum["landscape"] = "landscape";
    OrientationEnum["portrait"] = "portrait";
})(OrientationEnum || (exports.OrientationEnum = OrientationEnum = {}));
var MusicVolumeEnum;
(function (MusicVolumeEnum) {
    MusicVolumeEnum["muted"] = "muted";
    MusicVolumeEnum["low"] = "low";
    MusicVolumeEnum["medium"] = "medium";
    MusicVolumeEnum["high"] = "high";
})(MusicVolumeEnum || (exports.MusicVolumeEnum = MusicVolumeEnum = {}));
exports.renderConfig = zod_1.default.object({
    paddingBack: zod_1.default
        .number()
        .optional()
        .describe("For how long the video should be playing after the speech is done, in milliseconds. 1500 is a good value."),
    music: zod_1.default
        .nativeEnum(MusicMoodEnum)
        .optional()
        .describe("Music tag to be used to find the right music for the video"),
    captionPosition: zod_1.default
        .nativeEnum(CaptionPositionEnum)
        .optional()
        .describe("Position of the caption in the video"),
    captionBackgroundColor: zod_1.default
        .string()
        .optional()
        .describe("Background color of the caption, a valid css color, default is blue"),
    voice: zod_1.default
        .string()
        .min(1)
        .optional()
        .describe("Voice identifier used by the configured text-to-speech adapter"),
    orientation: zod_1.default
        .nativeEnum(OrientationEnum)
        .optional()
        .describe("Orientation of the video, default is portrait"),
    musicVolume: zod_1.default
        .nativeEnum(MusicVolumeEnum)
        .optional()
        .describe("Volume of the music, default is high"),
});
exports.createShortInput = zod_1.default.object({
    scenes: zod_1.default.array(exports.sceneInput).describe("Each scene to be created"),
    config: exports.renderConfig.describe("Configuration for rendering the video"),
});
