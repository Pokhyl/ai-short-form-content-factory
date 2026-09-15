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
  cleanWordsPerSecond: 1.78,
  numericComplexitySeconds: -0.35,
  numericSelectionUncertaintySeconds: 0.10,
};

const speechLexicon = {
  en: { approx: 'approximately ', percent: ' percent', billion: 'billion', million: 'million' },
  pl: { approx: 'około ', percent: ' procent', billion: 'miliarda', million: 'miliona' },
  ru: { approx: 'примерно ', percent: ' процентов', billion: 'миллиарда', million: 'миллиона' },
  uk: { approx: 'приблизно ', percent: ' відсотків', billion: 'мільярда', million: 'мільйона' },
};

const normalizeForSpeech = (input, language) => {
  const lexicon = speechLexicon[language] ?? speechLexicon.en;
  return String(input ?? '')
    .normalize('NFC')
    .replace(/[\u0301\u0341]/g, '')
    .replace(/≈/g, lexicon.approx)
    .replace(/(\d(?:[\d\s.,]*\d|\d)?)\s*%/g, `$1${lexicon.percent}`)
    .replace(/млрд\.?/giu, lexicon.billion)
    .replace(/млн\.?/giu, lexicon.million)
    .replace(/\(([^()]+)\)/g, ', $1,')
    .replace(/\s+[—–]\s+/g, ', ')
    .replace(/[«»“”„"]/g, '')
    .replace(/\s*;\s*/g, '. ')
    .replace(/\s*:\s*/g, '. ')
    .replace(/\s*,\s*,+/g, ', ')
    .replace(/\s+/g, ' ')
    .replace(/\s+([,.!?])/g, '$1')
    .trim();
};

const normalizeUkrainianSpeech = (input) => {
  let text = String(input ?? '');
  text = text.replace(
    /^([^,.!?]{2,60}),\s+([^,.!?]{2,60}),\s+(що|яка|який|яке|які)\s+/iu,
    '$1 — це $2, $3 ',
  );
  text = text.replace(/\b(\d{1,3})[,.](\d{2,})\b/g, (match, whole, fraction) => {
    const value = Number(`${whole}.${fraction}`);
    if (!Number.isFinite(value)) return match;
    const rounded = Math.round(value * 10) / 10;
    return String(rounded).replace('.', ',');
  });
  return text
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
const targetNarrationSeconds = (minAcceptedNarrationSeconds + maxAcceptedNarrationSeconds) / 2;
const targetWords = Math.max(8, Math.round(targetNarrationSeconds * speechRate));
const minWords = Math.max(6, Math.floor(targetWords * 0.82));
const maxWords = Math.ceil(targetWords * 1.18);
const wordCount = (text) => String(text ?? '').split(/\s+/).filter(Boolean).length;

const estimateIntegerWordCount = (rawDigits) => {
  const digits = String(rawDigits ?? '').replace(/^0+(?=\d)/, '');
  const value = Number(digits || '0');
  if (!Number.isFinite(value)) return 1;
  const n = Math.abs(Math.trunc(value));
  if (n < 20) return 1;
  if (n < 100) return n % 10 === 0 ? 1 : 2;
  if (n < 1000) {
    const rest = n % 100;
    return 1 + (rest ? estimateIntegerWordCount(String(rest)) : 0);
  }
  if (n < 1_000_000) {
    const thousands = Math.trunc(n / 1000);
    const rest = n % 1000;
    return estimateIntegerWordCount(String(thousands)) + 1 + (rest ? estimateIntegerWordCount(String(rest)) : 0);
  }
  if (n < 1_000_000_000) {
    const millions = Math.trunc(n / 1_000_000);
    const rest = n % 1_000_000;
    return estimateIntegerWordCount(String(millions)) + 1 + (rest ? estimateIntegerWordCount(String(rest)) : 0);
  }
  return Math.max(2, Math.ceil(String(n).length / 3) * 2);
};

const spokenWordCount = (text) => String(text ?? '')
  .split(/\s+/)
  .filter(Boolean)
  .reduce((sum, rawToken) => {
    const token = rawToken.replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}.,'’ʼ-]+$/gu, '');
    const match = /^(\d+)(?:[,.](\d+))?$/.exec(token);
    if (!match) return sum + 1;
    let count = estimateIntegerWordCount(match[1]);
    if (match[2]) count += 1 + match[2].length;
    return sum + count;
  }, 0);

const punctuationCount = (text) => (String(text ?? '').match(/[.!?,;:]/g) || []).length;
const nonSpaceCharCount = (text) => String(text ?? '').replace(/\s+/g, '').length;
const numericComplexity = (text) => (String(text ?? '').match(/\d+|[%°³]|\b(?:км|см|г|тис|рр)\b/giu) || []).length;
const estimateNarrationSeconds = (text) => {
  if (job.language === 'uk' && targetDurationSeconds === 60) {
    const spokenWords = spokenWordCount(text);
    const complexity = numericComplexity(text);
    return Math.max(
      0.1,
      spokenWords / geminiUk60TimingProfile.cleanWordsPerSecond +
        complexity * geminiUk60TimingProfile.numericComplexitySeconds,
    );
  }
  if (job.language === 'uk') {
    const lexicalWords = wordCount(text);
    const punctuationMarks = punctuationCount(text);
    return Math.max(
      0.1,
      lexicalWords * geminiUkTimingProfile.lexicalWordSeconds +
        punctuationMarks * geminiUkTimingProfile.punctuationSeconds +
        geminiUkTimingProfile.interceptSeconds,
    );
  }
  return spokenWordCount(text) / speechRate;
};

const normalizedSpeechSource = normalizeForSpeech(source.sourceText, job.language);
const speechSourceText = job.language === 'uk'
  ? normalizeUkrainianSpeech(normalizedSpeechSource)
  : normalizedSpeechSource;

const sourceSentenceIndexes = [];
const sentences = speechSourceText
  .split(/\n+|(?<=[.!?])\s+/)
  .map((sentence) => sentence
    .replace(/^=+\s*[^=]{1,80}\s*=+\s*/u, '')
    .replace(/^[^.!?]{1,80}\s+==+\s+(?=\p{Lu})/u, '')
    .replace(/^=+|=+$/g, '')
    .replace(/\s+/g, ' ')
    .trim())
  .filter((sentence, sourceIndex) => {
    const count = wordCount(sentence);
    const eligible = count >= 4 && count <= 40 && !/^=/.test(sentence);
    if (eligible) sourceSentenceIndexes.push(sourceIndex);
    return eligible;
  })
  .map((sentence) => /[.!?]$/.test(sentence) ? sentence : sentence.replace(/[,;:]$/, '') + '.');

// Excerpts must not invent context by dropping the immediately preceding source
// sentence. This is a selection constraint, not permission to ground a pronoun;
// the renderer still validates the actual antecedent and exact visual identity.
const contextOpening = {
  uk: /^(?:(?:однак|проте|потім|згодом|також)\s*,?\s+)?(?:він|вона|воно|вони|його|її|їх|цей|ця|це|ці|такий|така|таке|такі)(?!\p{L})/iu,
  ru: /^(?:(?:однако|затем|потом|позже|также)\s*,?\s+)?(?:он|она|оно|они|его|её|ее|их|этот|эта|это|эти|такой|такая|такие)(?!\p{L})/iu,
  pl: /^(?:(?:jednak|potem|następnie|później|również)\s*,?\s+)?(?:on|ona|ono|oni|one|jego|jej|ich|ten|ta|to|te|ci)(?!\p{L})/iu,
  en: /^(?:(?:however|then|later|nevertheless|also)\s*,?\s+)?(?:he|she|it|they|his|her|its|their|this|that|these|those)(?!\p{L})/iu,
};
const hasCoherentContext = (indexes) => indexes.every((index, position) =>
  !contextOpening[job.language].test(sentences[index]) ||
  (position > 0 && sourceSentenceIndexes[indexes[position - 1]] === sourceSentenceIndexes[index] - 1));

const buildCandidate = (indexes) => {
  const text = indexes.map((index) => sentences[index]).join(' ').trim();
  return {
    indexes,
    text,
    lexicalWords: wordCount(text),
    spokenWords: spokenWordCount(text),
    nonSpaceChars: nonSpaceCharCount(text),
    numericComplexity: numericComplexity(text),
    punctuationMarks: punctuationCount(text),
    estimatedSeconds: estimateNarrationSeconds(text),
  };
};

const candidateScore = (candidate, gaps = 0) => [
  Math.abs(candidate.estimatedSeconds - targetNarrationSeconds) +
    (job.language === 'uk' && targetDurationSeconds === 60
      ? candidate.numericComplexity * geminiUk60TimingProfile.numericSelectionUncertaintySeconds
      : 0),
  gaps,
  candidate.indexes[0] ?? 999,
  -candidate.indexes.length,
];

const scoreLess = (a, b) =>
  !b ||
  a[0] < b[0] ||
  (a[0] === b[0] && a[1] < b[1]) ||
  (a[0] === b[0] && a[1] === b[1] && a[2] < b[2]) ||
  (a[0] === b[0] && a[1] === b[1] && a[2] === b[2] && a[3] < b[3]);

let best = null;
for (let start = 0; start < sentences.length; start++) {
  for (let end = start; end < sentences.length; end++) {
    const indexes = Array.from({ length: end - start + 1 }, (_, offset) => start + offset);
    if (!hasCoherentContext(indexes)) continue;
    const candidate = buildCandidate(indexes);
    if (candidate.spokenWords < minWords) continue;
    if (candidate.spokenWords > maxWords && candidate.estimatedSeconds > maxAcceptedNarrationSeconds + 3) break;
    if (candidate.estimatedSeconds < minAcceptedNarrationSeconds || candidate.estimatedSeconds > maxAcceptedNarrationSeconds) continue;
    const score = candidateScore(candidate, 0);
    if (scoreLess(score, best?.score)) best = { ...candidate, score };
  }
}

if (!best) {
  let states = new Map([[0, []]]);
  for (let index = 0; index < sentences.length; index++) {
    const sentenceWords = spokenWordCount(sentences[index]);
    if (sentenceWords > maxWords) continue;
    for (const [sum, selected] of [...states.entries()]) {
      const next = sum + sentenceWords;
      if (next > maxWords) continue;
      const indexes = [...selected, index];
      if (!hasCoherentContext(indexes)) continue;
      const existing = states.get(next);
      if (!existing || indexes.length > existing.length) states.set(next, indexes);
    }
  }
  for (const [sum, indexes] of states.entries()) {
    if (sum < minWords || sum > maxWords || indexes.length < 2) continue;
    if (!hasCoherentContext(indexes)) continue;
    const candidate = buildCandidate(indexes);
    if (candidate.estimatedSeconds < minAcceptedNarrationSeconds || candidate.estimatedSeconds > maxAcceptedNarrationSeconds) continue;
    let gaps = 0;
    for (let i = 1; i < indexes.length; i++) {
      if (indexes[i] !== indexes[i - 1] + 1) gaps++;
    }
    const score = candidateScore(candidate, gaps);
    if (scoreLess(score, best?.score)) best = { ...candidate, score };
  }
}

if (!best) {
  throw new Error(
    `localized source cannot pre-plan ${job.target_duration_seconds}s narration inside ` +
      `${minAcceptedNarrationSeconds.toFixed(2)}-${maxAcceptedNarrationSeconds.toFixed(2)}s`,
  );
}

const selected = best.indexes
  ? best.indexes.map((index) => sentences[index])
  : sentences.slice(best.start, best.end + 1);

const capitalizeSentenceStart = (text) => String(text ?? '').replace(/^(\s*)(\p{Ll})/u, (_match, space, letter) => `${space}${letter.toLocaleUpperCase()}`);
const chosenUnits = selected.map(capitalizeSentenceStart);
let script = chosenUnits.join(' ').trim();
script = script.replace(/[,;:]$/, '.');
const words = script.split(/\s+/).filter(Boolean);

let sceneTexts = [...chosenUnits];
const maxScenes = { 15: 4, 30: 6, 45: 8, 60: 10 }[job.target_duration_seconds] ?? 6;
while (sceneTexts.length > maxScenes) {
  let mergeAt = 0;
  let bestSize = Number.POSITIVE_INFINITY;
  for (let i = 0; i < sceneTexts.length - 1; i++) {
    const size = wordCount(sceneTexts[i]) + wordCount(sceneTexts[i + 1]);
    if (size < bestSize) {
      bestSize = size;
      mergeAt = i;
    }
  }
  sceneTexts.splice(mergeAt, 2, `${sceneTexts[mergeAt]} ${sceneTexts[mergeAt + 1]}`);
}

if (sceneTexts.length < 2) sceneTexts = chosenUnits;

const articleLang = source.sourceLang || job.language;
const articleTitle = source.sourceTitle;
const englishTitle = source.englishTitle || articleTitle;
const visualSourceTerm = `visualsource::${articleLang}::${encodeURIComponent(articleTitle)}::${encodeURIComponent(englishTitle)}`;
const scenes = sceneTexts.map((text, index) => ({
  text,
  mediaContext: text,
  mediaHistory: index > 0 ? sceneTexts[index - 1] : '',
  searchTerms: [visualSourceTerm],
}));

return [{
  json: {
    jobId: job.job_id,
    script,
    wordCount: words.length,
    groundedCandidateCount: 0,
    scenes,
    sourceData: {
      title: source.sourceTitle,
      url: source.sourceUrl,
      english_title: source.englishTitle,
      source_lang: articleLang,
      narration_mode: 'localized_source_extract_speech_normalized',
      media_mode: 'english_grounded_visual_search_v1',
      timing_profile: {
        words_per_second: speechRate,
        target_words: targetWords,
        min_words: minWords,
        max_words: maxWords,
        lexical_words: best.lexicalWords,
        spoken_word_count: best.spokenWords,
        non_space_chars: best.nonSpaceChars,
        numeric_complexity: best.numericComplexity,
        punctuation_marks: best.punctuationMarks,
        estimated_narration_seconds: Number(best.estimatedSeconds.toFixed(3)),
        target_narration_seconds: Number(targetNarrationSeconds.toFixed(3)),
        accepted_narration_seconds: [
          Number(minAcceptedNarrationSeconds.toFixed(3)),
          Number(maxAcceptedNarrationSeconds.toFixed(3)),
        ],
        model: job.language === 'uk' && targetDurationSeconds === 60
          ? 'gemini_enceladus_uk_60s_clean_speech_v1'
          : job.language === 'uk'
            ? 'gemini_enceladus_uk_words_punctuation_v2'
            : 'words_per_second_v1',
      },
    },
  },
}];
