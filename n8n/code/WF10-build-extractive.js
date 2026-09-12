const job = $('Load Job').item.json;
const source = $json;

const wordsPerSecond = {
  en: 2.34,
  pl: 1.80,
  ru: 1.88,
  uk: 1.48,
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
    .replace(/\s*;\s*/g, '. ')
    .replace(/\s*:\s*/g, '. ')
    .replace(/\s*,\s*,+/g, ', ')
    .replace(/\s+/g, ' ')
    .replace(/\s+([,.!?])/g, '$1')
    .trim();
};

const speechRate = wordsPerSecond[job.language];
if (!speechRate) throw new Error(`missing speech timing profile for ${job.language}`);

const audioTargetSeconds = Math.max(1, job.target_duration_seconds - 0.75);
const targetWords = Math.max(8, Math.round(audioTargetSeconds * speechRate));
const minWords = Math.max(6, Math.floor(targetWords * 0.9));
const maxWords = Math.ceil(targetWords * 1.1);
const wordCount = (text) => text.split(/\s+/).filter(Boolean).length;

const speechSourceText = normalizeForSpeech(source.sourceText, job.language);

const sentences = speechSourceText
  .split(/\n+|(?<=[.!?])\s+/)
  .map((sentence) => sentence.replace(/^=+|=+$/g, '').replace(/\s+/g, ' ').trim())
  .filter((sentence) => {
    const count = wordCount(sentence);
    return count >= 4 && count <= 40 && !/^=/.test(sentence);
  })
  .map((sentence) => /[.!?]$/.test(sentence) ? sentence : sentence.replace(/[,;:]$/, '') + '.');

let best = null;
for (let start = 0; start < sentences.length; start++) {
  let words = 0;
  for (let end = start; end < sentences.length; end++) {
    words += wordCount(sentences[end]);
    if (words >= minWords && words <= maxWords) {
      const score = [start, Math.abs(words - targetWords), -(end - start + 1)];
      if (!best || score[0] < best.score[0] ||
          (score[0] === best.score[0] && score[1] < best.score[1]) ||
          (score[0] === best.score[0] && score[1] === best.score[1] && score[2] < best.score[2])) {
        best = { score, start, end, words };
      }
    }
    if (words > maxWords) break;
  }
}

if (!best) {
  let states = new Map([[0, []]]);
  for (let index = 0; index < sentences.length; index++) {
    const sentenceWords = wordCount(sentences[index]);
    if (sentenceWords > maxWords) continue;
    for (const [sum, selected] of [...states.entries()]) {
      const next = sum + sentenceWords;
      if (next > maxWords) continue;
      const indexes = [...selected, index];
      if (!states.has(next) || indexes.length > states.get(next).length) states.set(next, indexes);
    }
  }
  for (const [sum, selected] of states.entries()) {
    if (sum < minWords || sum > maxWords) continue;
    let gaps = 0;
    for (let i = 1; i < selected.length; i++) {
      if (selected[i] !== selected[i - 1] + 1) gaps++;
    }
    const score = [Math.abs(sum - targetWords), gaps, selected[0] ?? 999, -selected.length];
    if (!best || score[0] < best.score[0] ||
        (score[0] === best.score[0] && score[1] < best.score[1]) ||
        (score[0] === best.score[0] && score[1] === best.score[1] && score[2] < best.score[2])) {
      best = { score, indexes: selected, words: sum };
    }
  }
}

if (!best) throw new Error(`localized source cannot fill ${job.target_duration_seconds}s narration`);

const selected = best.indexes
  ? best.indexes.map((index) => sentences[index])
  : sentences.slice(best.start, best.end + 1);

const splitSemantic = (sentence) => {
  const maxChunkWords = 16;
  const marked = sentence
    .replace(/([,;:])\s+/g, '$1|||')
    .replace(/\s+[—–]\s+/g, '|||— ');
  const parts = marked.split('|||').map((part) => part.trim()).filter(Boolean);
  if (parts.length < 2) return [sentence];

  const chunks = [];
  let current = '';
  for (const part of parts) {
    if (!current) {
      current = part;
      continue;
    }
    const combined = `${current} ${part}`;
    const currentWords = wordCount(current);
    const partWords = wordCount(part);
    const shouldSplit =
      (wordCount(combined) > maxChunkWords && currentWords >= 6) ||
      (currentWords >= 3 && partWords >= 5 && wordCount(combined) >= 9);
    if (shouldSplit) {
      chunks.push(current);
      current = part;
    } else {
      current = combined;
    }
  }
  if (current) chunks.push(current);

  if (chunks.length > 1 && wordCount(chunks[chunks.length - 1]) < 3) {
    chunks[chunks.length - 2] = `${chunks[chunks.length - 2]} ${chunks[chunks.length - 1]}`;
    chunks.pop();
  }
  return chunks;
};

const narrationUnits = selected.flatMap(splitSemantic);
let bestPrefix = null;
let prefixWords = 0;
for (let index = 0; index < narrationUnits.length; index++) {
  prefixWords += wordCount(narrationUnits[index]);
  if (prefixWords >= minWords && prefixWords <= maxWords) {
    const distance = Math.abs(prefixWords - targetWords);
    if (!bestPrefix || distance < bestPrefix.distance ||
        (distance === bestPrefix.distance && prefixWords < bestPrefix.words)) {
      bestPrefix = { end: index, words: prefixWords, distance };
    }
  }
  if (prefixWords > maxWords) break;
}

const chosenUnits = bestPrefix
  ? narrationUnits.slice(0, bestPrefix.end + 1)
  : narrationUnits;
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
const scenes = sceneTexts.map((text) => ({
  text,
  searchTerms: [`wikiarticle::${articleLang}::${encodeURIComponent(articleTitle)}`],
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
      media_mode: 'localized_article_images_only',
      timing_profile: {
        words_per_second: speechRate,
        target_words: targetWords,
        min_words: minWords,
        max_words: maxWords,
      },
    },
  },
}];
