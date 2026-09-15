const job = $('Load Job').item.json;
const source = $json;

const wordsPerSecond = {
  en: 2.34,
  pl: 1.80,
  ru: 1.88,
  uk: 1.55,
};

// Empirical pre-synthesis timing model for Gemini 3.1 Flash TTS + Enceladus (UK).
// It is intentionally voice/language-specific and is based on measured production/test audio,
// not on a generic words-per-second assumption.
const geminiUkTimingProfile = {
  lexicalWordSeconds: 0.59870959,
  punctuationSeconds: 0.36178222,
  interceptSeconds: -0.6178946,
};

// 60-second UK calibration from four immutable normal jobs synthesized with
// the same Gemini model, Enceladus voice, seed and natural documentary prompt.
// This model intentionally stays scoped to the calibrated 60s operating point;
// other target durations retain the generic UK model until they have real data.
const geminiUk60TimingProfile = {
  // Immutable production measurements now cover both sides of the renderer gate:
  // 571 chars -> 53.56/54.32s, 585 chars -> 58.64s, 587 chars -> 55.80/56.16s,
  // 626 chars -> 60.48s.  A single point estimate cannot safely separate those cases.
  // Use an empirical uncertainty band instead: 10.70 chars/s is slightly faster than
  // the fastest observed sample (~10.66), while 9.90 chars/s is slightly slower than
  // the slowest observed sample (~9.98).  Candidates must fit the renderer gate under
  // both bounds before the one allowed Gemini synthesis request is spent.
  fastCharsPerSecond: 10.70,
  slowCharsPerSecond: 9.90,
  centerCharsPerSecond: 10.35,
  numericSelectionUncertaintySeconds: 0.10,
  rendererMinNarrationSeconds: 54.0,
};

const speechLexicon = {
  en: { approx: 'approximately ', percent: ' percent', billion: 'billion', million: 'million' },
  pl: { approx: 'okoÅ‚o ', percent: ' procent', billion: 'miliarda', million: 'miliona' },
  ru: { approx: 'Ð¿Ñ€Ð¸Ð¼ÐµÑ€Ð½Ð¾ ', percent: ' Ð¿Ñ€Ð¾Ñ†ÐµÐ½Ñ‚Ð¾Ð²', billion: 'Ð¼Ð¸Ð»Ð»Ð¸Ð°Ñ€Ð´Ð°', million: 'Ð¼Ð¸Ð»Ð»Ð¸Ð¾Ð½Ð°' },
  uk: { approx: 'Ð¿Ñ€Ð¸Ð±Ð»Ð¸Ð·Ð½Ð¾ ', percent: ' Ð²Ñ–Ð´ÑÐ¾Ñ‚ÐºÑ–Ð²', billion: 'Ð¼Ñ–Ð»ÑŒÑÑ€Ð´Ð°', million: 'Ð¼Ñ–Ð»ÑŒÐ¹Ð¾Ð½Ð°' },
};

const normalizeForSpeech = (input, language) => {
  const lexicon = speechLexicon[language] ?? speechLexicon.en;
  return String(input ?? '')
    .normalize('NFC')
    .replace(/[\u0301\u0341]/g, '')
    .replace(/â‰ˆ/g, lexicon.approx)
    .replace(/(\d(?:[\d\s.,]*\d|\d)?)\s*%/g, `$1${lexicon.percent}`)
    .replace(/Ð¼Ð»Ñ€Ð´\.?/giu, lexicon.billion)
    .replace(/Ð¼Ð»Ð½\.?/giu, lexicon.million)
    .replace(/\(([^()]+)\)/g, ', $1,')
    .replace(/\s+[â€”â€“]\s+/g, language === 'uk' ? ' â€” ' : ', ')
    .replace(/[Â«Â»â€œâ€â€ž"]/g, '')
    .replace(/\s*;\s*/g, '. ')
    .replace(/\s*:\s*/g, language === 'uk' ? ' : ' : ', ')
    .replace(/\s*,\s*,+/g, ', ')
    .replace(/\s+/g, ' ')
    .replace(/\s+([,.!?])/g, '$1')
    .trim();
};

const normalizeUkrainianSpeech = (input) => {
  let text = String(input ?? '');
  text = text.replace(
    /(^|(?<=[.!?])\s+)([^,.!?]{2,80})\s+[â€”â€“]\s+/gu,
    '$1$2 â€” Ñ†Ðµ ',
  );
  text = text.replace(/,\s*[â€”â€“]\s+/g, ', Ñ†Ðµ ');
  text = text.replace(
    /(^|(?<=[.!?])\s+)([^,.!?]{2,60}),\s+([^,.!?]{2,60}),\s+(Ñ‰Ð¾|ÑÐºÐ°|ÑÐºÐ¸Ð¹|ÑÐºÐµ|ÑÐºÑ–)\s+/giu,
    '$1$2 â€” Ñ†Ðµ $3, $4 ',
  );
  text = text.replace(/\b(\d{1,3})[,.](\d{2,})\b/g, (match, whole, fraction) => {
    const value = Number(`${whole}.${fraction}`);
    if (!Number.isFinite(value)) return match;
    const rounded = Math.round(value * 10) / 10;
    return String(rounded).replace('.', ',');
  });
  return text
    .replace(/\s*:\s*/g, ', ')
    .replace(/\b(\d+),0\b/g, '$1')
    .replace(/\s+([,.!?])/g, '$1')
    .replace(/\s+/g, ' ')
    .trim();
};

const speechRate = wordsPerSecond[job.language];
if (!speechRate) throw new Error(`missing speech timing profile for ${job.language}`);

const targetDurationSeconds = Number(job.target_duration_seconds);
const minAcceptedNarrationSeconds = Math.max(1, targetDurationSeconds - 1.5);
const maxAcceptedNarrationSeconds = targetDurationSeconds + 0.35;
const isGeminiUk60 = job.language === 'uk' && targetDurationSeconds === 60;
const rendererMinNarrationSeconds = isGeminiUk60
  ? geminiUk60TimingProfile.rendererMinNarrationSeconds
  : minAcceptedNarrationSeconds;
const selectionMaxNarrationSeconds = maxAcceptedNarrationSeconds;
const uk60MinNonSpaceChars = isGeminiUk60
  ? rendererMinNarrationSeconds * geminiUk60TimingProfile.fastCharsPerSecond
  : null;
const uk60MaxNonSpaceChars = isGeminiUk60
  ? maxAcceptedNarrationSeconds * geminiUk60TimingProfile.slowCharsPerSecond
  : null;
const uk60TargetNonSpaceChars = isGeminiUk60
  ? (uk60MinNonSpaceChars + uk60MaxNonSpaceChars) / 2
  : null;
const targetNarrationSeconds = isGeminiUk60
  ? uk60TargetNonSpaceChars / geminiUk60TimingProfile.centerCharsPerSecond
  : (minAcceptedNarrationSeconds + selectionMaxNarrationSeconds) / 2;
const targetWords = Math.max(8, Math.round(targetNarrationSeconds * speechRate));
const minWords = Math.max(6, Math.floor(targetWords * 0.82));
const maxWords = Math.ceil(targetWords * 1.18);
const wordCount = (text) => String(text ?? '').split(/\s+/).filter(Boolean).length;

const estimateIntegerWordCount = (rawDigits) => {
  const digits = String(rawDigits ?? '').replace(/^0+(?=\d)/, '');
  const value = Number(digits || '0');
  if (!Number"æ—4f–æ—FR‡fÇVR’’&WGW&â°¢6öç7BâÒÖF‚æ'2„ÖF‚çG'Væ2‡fÇVR’“°¢–b†âÂ#’&WGW&â°¢–b†âÂ’&WGW&ââRÓÓÒò¢#°¢–b†âÂ’°¢6öç7B&W7BÒâR°¢&WGW&â²‡&W7BòW7F–ÖFT–çFVvW%v÷&D6÷VçB…7G&–ær‡&W7B’’¢“°¢Ð¢–b†âÂóó’°¢6öç7BF†÷W6æG2ÒÖF‚çG'Væ2†âò“°¢6öç7B&W7BÒâR°¢&WGW&âW7F–ÖFT–çFVvW%v÷&D6÷VçB…7G&–ær‡F†÷W6æG2’’²²‡&W7BòW7F–ÖFT–çFVvW%v÷&D6÷VçB…7G&–ær‡&W7B’’¢“°¢Ð¢–b†âÂóóó’°¢6öç7BÖ–ÆÆ–öç2ÒÖF‚çG'Væ2†âòóó“°¢6öç7B&W7BÒâRóó°¢&WGW&âW7F–ÖFT–çFVvW%v÷&D6÷VçB…7G&–ær†Ö–ÆÆ–öç2’’²²‡&W7BòW7F–ÖFT–çFVvW%v÷&D6÷VçB…7G&–ær‡&W7B’’¢“°¢Ð¢&WGW&âÖF‚æÖ‚ƒ"ÂÖF‚æ6V–Â…7G&–ær†â’æÆVæwF‚ò2’¢"“°§Ó° ¦6öç7B7ö¶Våv÷&D6÷VçBÒ‡FW‡B’Óâ7G&–ær‡FW‡Bóòrr¢ç7Æ—B‚õÇ2²ò¢æf–ÇFW"„&ööÆVâ¢ç&VGV6R‚‡7VÒÂ&uFö¶Vâ’Óâ°¢6öç7BFö¶VâÒ&uFö¶Vâç&WÆ6R‚õåµåÇ´ÇÕÇ´çÕÒ·ÅµåÇ´ÇÕÇ´çÒâÂ~(	œ«ÂÕÒ²BöwRÂrr“°¢6öç7BÖF6‚Òõâ…ÆB²’ƒó¢ÇÂåÒ…ÆB²’“òGÂòæW†V2‡Fö¶Vâ“°¢–b‚ÖF6‚’&WGW&â7VÒ²°¢ÆWB6÷VçBÒW7F–ÖFT–çFVvW%v÷&D6÷VçB†ÖF6…³Ò“°¢–b†ÖF6…³%Ò’6÷VçB³Ò²ÖF6…³%ÒæÆVæwFƒ°¢&WGW&â7VÒ²6÷VçC°¢ÒÂ“° ¦6öç7BVæ7GVF–öä6÷VçBÒ‡FW‡B’Óâ…7G&–ær‡FW‡Bóòrr’æÖF6‚‚õ²âòÃ³¥Òör’ÇÂµÒ’æÆVæwFƒ°¦6öç7Bæöå76T6†$6÷VçBÒ‡FW‡B’Óâ7G&–ær‡FW‡Bóòrr’ç&WÆ6R‚õÇ2²örÂrr’æÆVæwFƒ°¦6öç7BçVÖW&–46ö×ÆW†—G’Ò‡FW‡B’Óâ…7G&–ær‡FW‡Bóòrr’æÖF6‚‚õÆB·Å²\++5×ÅÆ"ƒó­­ÇÍÇÍ7Í-Í•Æ"öv—R’ÇÂµÒ’æÆVæwFƒ°¦6öç7BW7F–ÖFUV³cæ'&F–öä&æBÒ‡FW‡B’Óâ°¢6öç7B6†'2Òæöå76T6†$6÷VçB‡FW‡B“°¢&WGW&â°¢f7FW7E6V6öæG3¢6†'2òvVÖ–æ•V³cF–Ö–æu&öf–ÆRæf7D6†'5W%6V6öæBÀ¢6Æ÷vW7E6V6öæG3¢6†'2òvVÖ–æ•V³cF–Ö–æu&öf–ÆRç6Æ÷t6†'5W%6V6öæBÀ¢6VçFW%6V6öæG3¢6†'2òvVÖ–æ•V³cF–Ö–æu&öf–ÆRæ6VçFW$6†'5W%6V6öæBÀ¢Ó°§Ó°¦6öç7BW7F–ÖFTæ'&F–öå6V6öæG2Ò‡FW‡B’Óâ°¢–b†—4vVÖ–æ•V³c’°¢&WGW&âÖF‚æÖ‚ƒãÂW7F–ÖFUV³cæ'&F–öä&æB‡FW‡B’æ6VçFW%6V6öæG2“°¢Ð¢–b†¦ö"æÆæwVvRÓÓÒwV²r’°¢6öç7BÆW†–6Åv÷&G2Òv÷&D6÷VçB‡FW‡B“°¢6öç7BVæ7GVF–öäÖ&·2ÒVæ7GVF–öä6÷VçB‡FW‡B“°¢&WGW&âÖF‚æÖ‚€¢ãÀ¢ÆW†–6Åv÷&G2¢vVÖ–æ•VµF–Ö–æu&öf–ÆRæÆW†–6Åv÷&E6V6öæG2°¢Væ7GVF–öäÖ&·2¢vVÖ–æ•VµF–Ö–æu&öf–ÆRçVæ7GVF–öå6V6öæG2°¢vVÖ–æ•VµF–Ö–æu&öf–ÆRæ–çFW&6WE6V6öæG2À¢“°¢Ð¢&WGW&â7ö¶Våv÷&D6÷VçB‡FW‡B’ò7VV6…&FS°§Ó° ¦6öç7Bæ÷&ÖÆ—¦VE7VV6…6÷W&6RÒæ÷&ÖÆ—¦Tf÷%7VV6‚‡6÷W&6Rç6÷W&6UFW‡BÂ¦ö"æÆæwVvR“°¦6öç7B7VV6…6÷W&6UFW‡BÒ¦ö"æÆæwVvRÓÓÒwV²p¢òæ÷&ÖÆ—¦UV·&–æ–å7VV6‚†æ÷&ÖÆ—¦VE7VV6…6÷W&6R¢¢æ÷&ÖÆ—¦VE7VV6…6÷W&6S° ¦6öç7B6÷W&6U6VçFVæ6T–æFW†W2ÒµÓ°¦6öç7B6VçFVæ6W2Ò7VV6…6÷W&6UFW‡@¢ç7Æ—B‚õÆâ·ÂƒóÃÕ²âõÒ•Ç2²ò¢æÖ‚‡6VçFVæ6R’Óâ6VçFVæ6P¢ç&WÆ6R‚õãÒµÇ2¥µãÕ×³ÃƒÕÇ2£ÒµÇ2¢÷RÂrr¢ç&WÆ6R‚õåµââõ×³ÃƒÕÇ2³ÓÒµÇ2²ƒóÕÇ´ÇWÒ’÷RÂrr¢ç&WÆ6R‚õãÒ·ÃÒ²BörÂrr¢ç&WÆ6R‚õÇ2²örÂrr¢çG&–Ò‚’¢æf–ÇFW"‚‡6VçFVæ6RÂ6÷W&6T–æFW‚’Óâ°¢6öç7B6÷VçBÒv÷&D6÷VçB‡6VçFVæ6R“°¢6öç7BVÆ–v–&ÆRÒ6÷VçBãÒBbb6÷VçBÃÒCbbõãÒòçFW7B‡6VçFVæ6R“°¢–b†VÆ–v–&ÆR’6÷W&6U6VçFVæ6T–æFW†W2çW6‚‡6÷W&6T–æFW‚“°¢&WGW&âVÆ–v–&ÆS°¢Ò¢æÖ‚‡6VçFVæ6R’Óâõ²âõÒBòçFW7B‡6VçFVæ6R’ò6VçFVæ6R¢6VçFVæ6Rç&WÆ6R‚õ²Ã³¥ÒBòÂrr’²râr“° ¢òòW†6W'G2×W7Bæ÷B–çfVçB6öçFW‡B'’G&÷–ærF†R–ÖÖVF–FVÇ’&V6VF–ær6÷W&6P¢òò6VçFVæ6RâF†—2—26VÆV7F–öâ6öç7G&–çBÂæ÷BW&Ö—76–öâFòw&÷VæB&öæ÷Vã°¢òòF†R&VæFW&W"7F–ÆÂfÆ–FFW2F†R7GVÂçFV6VFVçBæBW†7Bf—7VÂ–FVçF—G’à¦6öç7B6öçFW‡D÷Væ–ærÒ°¢V³¢õâƒó¢ƒó­íMÝ§Íýí-WÍýí-mÇÍ}=íMíÇÍ-­íb•Ç2¢ÃõÇ2²“òƒó­-m×Í-íÝÍ-íÝçÍ-íÝ‡Íí=çÍ}wÍ}WÍm]—Ím÷ÍmWÍmgÍ-­—Í-­Í-­WÍ-­b’ƒòÇ´ÇÒ’ö—RÀ¢'S¢õâƒó¢ƒó­íMÝ­çÍ}-]ÇÍýí-íÇÍýí}mWÍ-­mR•Ç2¢ÃõÇ2²“òƒó­í×ÍíÝÍíÝçÍíÝ‡Í]=çÍ]Í]WÍWÍÝ-í'ÍÝ-ÍÝ-çÍÝ-‡Í-­í—Í-­÷Í-­R’ƒòÇ´ÇÒ’ö—RÀ¢Ã¢õâƒó¢ƒó¦¦VFæ·Ç÷FV×Ææ7LI—æ–WÇ;<[¦æ–V§Ç,;7væ–\[Â•Ç2¢ÃõÇ2²“òƒó¦öçÆöæÆöæ÷Æöæ—ÆöæWÆ¦Vv÷Æ¦V§Æ–6‡ÇFVçÇFÇF÷ÇFWÆ6’’ƒòÇ´ÇÒ’ö—RÀ¢Vã¢õâƒó¢ƒó¦†÷vWfW'ÇF†VçÆÆFW'ÆæWfW'F†VÆW77ÆÇ6ò•Ç2¢ÃõÇ2²“òƒó¦†WÇ6†WÆ—GÇF†W—Æ†—7Æ†W'Æ—G7ÇF†V—'ÇF†—7ÇF†GÇF†W6WÇF†÷6R’ƒòÇ´ÇÒ’ö—RÀ§Ó°¦6öç7B†46ö†W&VçD6öçFW‡BÒ†–æFW†W2’Óâ–æFW†W2æWfW'’‚†–æFW‚Â÷6—F–öâ’Óà¢6öçFW‡D÷Væ–æu¶¦ö"æÆæwVvUÒçFW7B‡6VçFVæ6W5¶–æFW…Ò’ÇÀ¢‡÷6—F–öââbb6÷W&6U6VçFVæ6T–æFW†W5¶–æFW†W5·÷6—F–öâÒÕÒÓÓÒ6÷W&6U6VçFVæ6T–æFW†W5¶–æFW…ÒÒ’“° ¦6öç7B'V–ÆD6æF–FFRÒ†–æFW†W2’Óâ°¢6öç7BFW‡BÒ–æFW†W2æÖ‚†–æFW‚’Óâ6VçFVæ6W5¶–æFW…Ò’æ¦ö–â‚rr’çG&–Ò‚“°¢&WGW&â°¢–æFW†W2À¢FW‡BÀ¢ÆW†–6Åv÷&G3¢v÷&D6÷VçB‡FW‡B’À¢7ö¶Våv÷&G3¢7ö¶Våv÷&D6÷VçB‡FW‡B’À¢æöå76T6†'3¢æöå76T6†$6÷VçB‡FW‡B’À¢çVÖW&–46ö×ÆW†—G“¢çVÖW&–46ö×ÆW†—G’‡FW‡B’À¢Væ7GVF–öäÖ&·3¢Væ7GVF–öä6÷VçB‡FW‡B’À¢W7F–ÖFVE6V6öæG3¢W7F–ÖFTæ'&F–öå6V6öæG2‡FW‡B’À¢âââ†—4vVÖ–æ•V³còW7F–ÖFUV³cæ'&F–öä&æB‡FW‡B’¢·Ò’À¢Ó°§Ó° ¦6öç7B6æF–FFTf—G5F–Ö–æuv–æF÷rÒ†6æF–FFR’Óâ—4vVÖ–æ•V³c ¢ò6æF–FFRæf7FW7E6V6öæG2ãÒ&VæFW&W$Ö–äæ'&F–öå6V6öæG2b`¢6æF–FFRç6Æ÷vW7E6V6öæG2ÃÒÖ„66WFVDæ'&F–öå6V6öæG0¢¢6æF–FFRæW7F–ÖFVE6V6öæG2ãÒÖ–ä66WFVDæ'&F–öå6V6öæG2b`¢6æF–FFRæW7F–ÖFVE6V6öæG2ÃÒ6VÆV7F–öäÖ„æ'&F–öå6V6öæG3° ¦6öç7B6æF–FFU66÷&RÒ†6æF–FFRÂv2Ò’Óâ°¢†—4vVÖ–æ•V³c ¢òÖF‚æ'2†6æF–FFRææöå76T6†'2ÒV³cF&vWDæöå76T6†'2’òV³cF&vWDæöå76T6†'0¢¢ÖF‚æ'2†6æF–FFRæW7F–ÖFVE6V6öæG2ÒF&vWDæ'&F–öå6V6öæG2’’°¢†—4vVÖ–æ•V³c ¢ò6æF–FFRæçVÖW&–46ö×ÆW†—G’¢vVÖ–æ•V³cF–Ö–æu&öf–ÆRæçVÖW&–56VÆV7F–öåVæ6W'F–çG•6V6öæG0¢¢’À¢v2À¢6æF–FFRæ–æFW†W5³Òóò““’À¢Ö6æF–FFRæ–æFW†W2æÆVæwF‚À¥Ó° ¦6öç7B66÷&TÆW72Ò†Â"’Óà¢"ÇÀ¢³ÒÂ%³ÒÇÀ¢†³ÒÓÓÒ%³Òbb³ÒÂ%³Ò’ÇÀ¢†³ÒÓÓÒ%³Òbb³ÒÓÓÒ%³Òbb³%ÒÂ%³%Ò’ÇÀ¢†³ÒÓÓÒ%³Òbb³ÒÓÓÒ%³Òbb³%ÒÓÓÒ%³%Òbb³5ÒÂ%³5Ò“° ¦ÆWB&W7BÒçVÆÃ°¦f÷"†ÆWB7F'BÒ²7F'BÂ6VçFVæ6W2æÆVæwFƒ²7F'B²²’°¢f÷"†ÆWBVæBÒ7F'C²VæBÂ6VçFVæ6W2æÆVæwFƒ²VæB²²’°¢6öç7B–æFW†W2Ò'&’æg&öÒ‡²ÆVæwFƒ¢VæBÒ7F'B²ÒÂ…òÂöfg6WB’Óâ7F'B²öfg6WB“°¢–b‚†46ö†W&VçD6öçFW‡B†–æFW†W2’’6öçF–çVS°¢6öç7B6æF–FFRÒ'V–ÆD6æF–FFR†–æFW†W2“°¢–b†6æF–FFRç7ö¶Våv÷&G2ÂÖ–åv÷&G2’6öçF–çVS°¢–b†6æF–FFRç7ö¶Våv÷&G2âÖ…v÷&G2bb6æF–FFRæW7F–ÖFVE6V6öæG2â6VÆV7F–öäÖ„æ'&F–öå6V6öæG2²2’'&V³°¢–b‚6æF–FFTf—G5F–Ö–æuv–æF÷r†6æF–FFR’’6öçF–çVS°¢6öç7B66÷&RÒ6æF–FFU66÷&R†6æF–FFRÂ“°¢–b‡66÷&TÆW72‡66÷&RÂ&W7Còç66÷&R’’&W7BÒ²ââæ6æF–FFRÂ66÷&RÓ°¢Ð§Ð ¦–b‚&W7B’°¢ÆWB7FFW2ÒæWrÖ…µ³ÂµÕÕÒ“°¢f÷"†ÆWB–æFW‚Ò²–æFW‚Â6VçFVæ6W2æÆVæwFƒ²–æFW‚²²’°¢6öç7B6VçFVæ6Uv÷&G2Ò7ö¶Våv÷&D6÷VçB‡6VçFVæ6W5¶–æFW…Ò“°¢–b‡6VçFVæ6Uv÷&G2âÖ…v÷&G2’6öçF–çVS°¢f÷"†6öç7B·7VÒÂ6VÆV7FVEÒöb²ââç7FFW2æVçG&–W2‚•Ò’°¢6öç7BæW‡BÒ7VÒ²6VçFVæ6Uv÷&G3°¢–b†æW‡BâÖ…v÷&G2’6öçF–çVS°¢6öç7B–æFW†W2Ò²ââç6VÆV7FVBÂ–æFW…Ó°¢–b‚†46ö†W&VçD6öçFW‡B†–æFW†W2’’6öçF–çVS°¢6öç7BW†—7F–ærÒ7FFW2ævWB†æW‡B“°¢–b‚W†—7F–ærÇÂ–æFW†W2æÆVæwF‚âW†—7F–æræÆVæwF‚’7FFW2ç6WB†æW‡BÂ–æFW†W2“°¢Ð¢Ð¢f÷"†6öç7B·7VÒÂ–æFW†W5Òöb7FFW2æVçG&–W2‚’’°¢–b‡7VÒÂÖ–åv÷&G2ÇÂ7VÒâÖ…v÷&G2ÇÂ–æFW†W2æÆVæwF‚Â"’6öçF–çVS°¢–b‚†46ö†W&VçD6öçFW‡B†–æFW†W2’’6öçF–çVS°¢6öç7B6æF–FFRÒ'V–ÆD6æF–FFR†–æFW†W2“°¢–b‚6æF–FFTf—G5F–Ö–æuv–æF÷r†6æF–FFR’’6öçF–çVS°¢ÆWBv2Ò°¢f÷"†ÆWB’Ò²’Â–æFW†W2æÆVæwFƒ²’²²’°¢–b†–æFW†W5¶•ÒÓÒ–æFW†W5¶’ÒÒ²’v2²³°¢Ð¢6öç7B66÷&RÒ6æF–FFU66÷&R†6æF–FFRÂv2“°¢–b‡66÷&TÆW72‡66÷&RÂ&W7Còç66÷&R’’&W7BÒ²ââæ6æF–FFRÂ66÷&RÓ°¢Ð§Ð ¦–b‚&W7B’°¢F‡&÷ræWrW'&÷"€¢Æö6Æ—¦VB6÷W&6R6ææ÷B&R×ÆâG¶¦ö"çF&vWEöGW&F–öå÷6V6öæG7×2æ'&F–öâ–ç6–FR°¢G¶Ö–ä66WFVDæ'&F–öå6V6öæG2çFôf—†VBƒ"—ÒÒG·6VÆV7F–öäÖ„æ'&F–öå6V6öæG2çFôf—†VBƒ"—×2&RÕEE26VÆV7F–öâv–æF÷vÀ¢“°§Ð ¦6öç7B6VÆV7FVBÒ&W7Bæ–æFW†W0¢ò&W7Bæ–æFW†W2æÖ‚†–æFW‚’Óâ6VçFVæ6W5¶–æFW…Ò¢¢6VçFVæ6W2ç6Æ–6R†&W7Bç7F'BÂ&W7BæVæB²“° ¦6öç7B6—FÆ—¦U6VçFVæ6U7F'BÒ‡FW‡B’Óâ7G&–ær‡FW‡Bóòrr’ç&WÆ6R‚õâ…Ç2¢’…Ç´ÆÇÒ’÷RÂ…öÖF6‚Â76RÂÆWGFW"’ÓâG·76WÒG¶ÆWGFW"çFôÆö6ÆUWW$66R‚—Ö“°¦6öç7B6†÷6VåVæ—G2Ò6VÆV7FVBæÖ†6—FÆ—¦U6VçFVæ6U7F'B“°¦ÆWB67&—BÒ6†÷6VåVæ—G2æ¦ö–â‚rr’çG&–Ò‚“°§67&—BÒ67&—Bç&WÆ6R‚õ²Ã³¥ÒBòÂrâr“°¦6öç7Bv÷&G2Ò67&—Bç7Æ—B‚õÇ2²ò’æf–ÇFW"„&ööÆVâ“° ¦ÆWB66VæUFW‡G2Ò²ââæ6†÷6VåVæ—G5Ó°¦6öç7BÖ…66VæW2Ò²S¢BÂ3¢bÂCS¢‚Âc¢Õ¶¦ö"çF&vWEöGW&F–öå÷6V6öæG5Òóòc°§v†–ÆR‡66VæUFW‡G2æÆVæwF‚âÖ…66VæW2’°¢ÆWBÖW&vTBÒ°¢ÆWB&W7E6—¦RÒçVÖ&W"åõ4•D•dUô”äd”ä•E“°¢f÷"†ÆWB’Ò²’Â66VæUFW‡G2æÆVæwF‚Ò²’²²’°¢6öç7B6—¦RÒv÷&D6÷VçB‡66VæUFW‡G5¶•Ò’²v÷&D6÷VçB‡66VæUFW‡G5¶’²Ò“°¢–b‡6—¦RÂ&W7E6—¦R’°¢&W7E6—¦RÒ6—¦S°¢ÖW&vTBÒ“°¢Ð¢Ð¢66VæUFW‡G2ç7Æ–6R†ÖW&vTBÂ"ÂG·66VæUFW‡G5¶ÖW&vTE×ÒG·66VæUFW‡G5¶ÖW&vTB²×Ö“°§Ð ¦–b‡66VæUFW‡G2æÆVæwF‚Â"’66VæUFW‡G2Ò6†÷6VåVæ—G3° ¦6öç7B'F–6ÆTÆærÒ6÷W&6Rç6÷W&6TÆærÇÂ¦ö"æÆæwVvS°¦6öç7B'F–6ÆUF—FÆRÒ6÷W&6Rç6÷W&6UF—FÆS°¦6öç7BVævÆ—6…F—FÆRÒ6÷W&6RæVævÆ—6…F—FÆRÇÂ'F–6ÆUF—FÆS°¦6öç7Bf—7VÅ6÷W&6UFW&ÒÒf—7VÇ6÷W&6S£¢G¶'F–6ÆTÆæwÓ£¢G¶Væ6öFUU$”6ö×öæVçB†'F–6ÆUF—FÆR—Ó£¢G¶Væ6öFUU$”6ö×öæVçB†VævÆ—6…F—FÆR—Ö°¦6öç7B66VæW2Ò66VæUFW‡G2æÖ‚‡FW‡BÂ–æFW‚’Óâ‡°¢FW‡BÀ¢ÖVF–6öçFW‡C¢FW‡BÀ¢ÖVF–†—7F÷'“¢–æFW‚âò66VæUFW‡G5¶–æFW‚ÒÒ¢rrÀ¢6V&6…FW&×3¢·f—7VÅ6÷W&6UFW&ÕÒÀ§Ò’“° §&WGW&â·°¢§6öã¢°¢¦ö$–C¢¦ö"æ¦ö%ö–BÀ¢67&—BÀ¢v÷&D6÷VçC¢v÷&G2æÆVæwF‚À¢w&÷VæFVD6æF–FFT6÷VçC¢À¢66VæW2À¢6÷W&6TFF¢°¢F—FÆS¢6÷W&6Rç6÷W&6UF—FÆRÀ¢W&Ã¢6÷W&6Rç6÷W&6UW&ÂÀ¢VævÆ—6…÷F—FÆS¢6÷W&6RæVævÆ—6…F—FÆRÀ¢6÷W&6UöÆæs¢'F–6ÆTÆærÀ¢æ'&F–öåöÖöFS¢vÆö6Æ—¦VE÷6÷W&6UöW‡G&7E÷7VV6…öæ÷&ÖÆ—¦VBrÀ¢ÖVF–öÖöFS¢vVævÆ—6…öw&÷VæFVE÷f—7VÅ÷6V&6…÷crÀ¢F–Ö–æu÷&öf–ÆS¢°¢v÷&G5÷W%÷6V6öæC¢7VV6…&FRÀ¢F&vWE÷v÷&G3¢F&vWEv÷&G2À¢Ö–å÷v÷&G3¢Ö–åv÷&G2À¢Ö…÷v÷&G3¢Ö…v÷&G2À¢ÆW†–6Å÷v÷&G3¢&W7BæÆW†–6Åv÷&G2À¢7ö¶Vå÷v÷&Eö6÷VçC¢&W7Bç7ö¶Våv÷&G2À¢æöå÷76Uö6†'3¢&W7Bææöå76T6†'2À¢çVÖW&–5ö6ö×ÆW†—G“¢&W7BæçVÖW&–46ö×ÆW†—G’À¢Væ7GVF–öåöÖ&·3¢&W7BçVæ7GVF–öäÖ&·2À¢W7F–ÖFVEöæ'&F–öå÷6V6öæG3¢çVÖ&W"†&W7BæW7F–ÖFVE6V6öæG2çFôf—†VBƒ2’’À¢F&vWEöæ'&F–öå÷6V6öæG3¢çVÖ&W"‡F&vWDæ'&F–öå6V6öæG2çFôf—†VBƒ2’’À¢6VÆV7F–öåöÖ…öæ'&F–öå÷6V6öæG3¢çVÖ&W"‡6VÆV7F–öäÖ„æ'&F–öå6V6öæG2çFôf—†VBƒ2’’À¢âââ†—4vVÖ–æ•V³cò°¢W7F–ÖFVEöf7FW7Eöæ'&F–öå÷6V6öæG3¢çVÖ&W"†&W7Bæf7FW7E6V6öæG2çFôf—†VBƒ2’’À¢W7F–ÖFVE÷6Æ÷vW7Eöæ'&F–öå÷6V6öæG3¢çVÖ&W"†&W7Bç6Æ÷vW7E6V6öæG2çFôf—†VBƒ2’’À¢f7Eö6†'5÷W%÷6V6öæC¢vVÖ–æ•V³cF–Ö–æu&öf–ÆRæf7D6†'5W%6V6öæBÀ¢6Æ÷uö6†'5÷W%÷6V6öæC¢vVÖ–æ•V³cF–Ö–æu&öf–ÆRç6Æ÷t6†'5W%6V6öæBÀ¢F&vWEöæöå÷76Uö6†'3¢çVÖ&W"‡V³cF&vWDæöå76T6†'2çFôf—†VBƒ’’À¢&VæFW&W%öÖ–åöæ'&F–öå÷6V6öæG3¢&VæFW&W$Ö–äæ'&F–öå6V6öæG2À¢Ò¢·Ò’À¢66WFVEöæ'&F–öå÷6V6öæG3¢°¢çVÖ&W"‚†—4vVÖ–æ•V³cò&VæFW&W$Ö–äæ'&F–öå6V6öæG2¢Ö–ä66WFVDæ'&F–öå6V6öæG2’çFôf—†VBƒ2’’À¢çVÖ&W"†Ö„66WFVDæ'&F–öå6V6öæG2çFôf—†VBƒ2’’À¢ÒÀ¢ÖöFVÃ¢—4vVÖ–æ•V³c ¢òvvVÖ–æ•öVæ6VÆGW5÷Vµóc5ö6†%ö&æE÷c"p¢¢¦ö"æÆæwVvRÓÓÒwV²p¢òvvVÖ–æ•öVæ6VÆGW5÷Vµ÷v÷&G5÷Væ7GVF–öå÷c"p¢¢wv÷&G5÷W%÷6V6öæE÷crÀ¢ÒÀ¢ÒÀ¢ÒÀ§ÕÓ°