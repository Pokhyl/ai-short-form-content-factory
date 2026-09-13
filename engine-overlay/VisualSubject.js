"use strict";
const {execFile} = require('node:child_process');
const path = require('node:path');

const normalize = text => String(text || '').normalize('NFKC').toLowerCase().replace(/[’ʼ]/gu, "'").replace(/_/g, ' ');
const words = text => [...normalize(text).matchAll(/[\p{L}\p{N}]+(?:['-][\p{L}\p{N}]+)*/gu)].map(m => ({text: m[0], start: m.index, end: m.index + m[0].length}));

class VisualPreflightError extends Error {
  constructor(code, detail) { super(`Visual preflight FAIL [${code}]: ${detail}`); this.code = code; }
}
const fail = (code, detail) => { throw new VisualPreflightError(code, detail); };

class DictionaryLemmas {
  constructor() { this.cache = new Map(); }
  async get(lang, vocabulary) {
    const cache = this.cache.get(lang) || new Map();
    this.cache.set(lang, cache);
    const missing = [...new Set(vocabulary)].filter(w => !cache.has(w));
    if (missing.length) {
      const result = await new Promise((resolve, reject) => {
        const child = execFile(process.env.VISUAL_PYTHON || 'python3', [path.join(__dirname, 'visual-lemmas.py')],
          {timeout: 30000, maxBuffer: 4 * 1024 * 1024}, (error, stdout, stderr) => {
            if (error) return reject(new VisualPreflightError('dictionary_unavailable', stderr || error.message));
            try { resolve(JSON.parse(stdout)); } catch (e) { reject(e); }
          });
        child.stdin.end(JSON.stringify({lang, words: missing}));
      });
      if (!Array.isArray(result) || result.length !== missing.length) fail('dictionary_invalid', lang);
      missing.forEach((w, i) => cache.set(w, result[i].map(normalize)));
    }
    return cache;
  }
}

function sourceLexicon(wikitext, sourceTitle) {
  const entries = new Map();
  const add = (title, surface) => {
    title = title.replace(/#.*/, '').replace(/_/g, ' ').trim();
    if (!title || title.includes(':') || !surface || /[{}<>\[\]]/.test(surface)) return;
    const key = normalize(title);
    if (!entries.has(key)) entries.set(key, {title, aliases: new Set([title])});
    entries.get(key).aliases.add(surface.trim());
  };
  add(sourceTitle, sourceTitle);
  // Link display text is evidence for a local alias, including inflected forms.
  for (const m of wikitext.matchAll(/\[\[([^\[\]|]+)(?:\|([^\[\]]+))?\]\]([\p{L}]*)/gu)) {
    add(m[1], `${m[2] || m[1].replace(/#.*/, '')}${m[3]}`);
  }
  return [...entries.values()].map(e => ({...e, aliases: [...e.aliases]}));
}

// Language grammar, never topic vocabulary. Restrict alias promotion to explicit
// renaming of the leading subject; a later object's "called ..." is not an alias.
const ALIAS = /(?:звані\s+також|також\s+називаються|называемые\s+также|также\s+называются|zwane\s+(?:także|również)|nazywane\s+(?:także|również)|also\s+known\s+as|also\s+called)\s+/iu;
const COMPARISON = /(?<!\p{L})(?:than|unlike|compared\s+to|whereas|niż|w\s+porównaniu\s+z|ніж|на\s+відміну\s+від|порівняно\s+з|чем|в\s+отличие\s+от|по\s+сравнению\s+с)(?!\p{L})/iu;
const ANAPHORA = /(?<!\p{L})(?:з\s+них|із\s+них|ці|цей|ця|вони|из\s+них|эти|этот|эта|они|z\s+nich|te|ci|one|of\s+them|these|those|they|it)(?!\p{L})/iu;
const LOCATIVE_START = /^(?:у|в|за|поза|між|серед|между|среди|w|we|za|poza|między|in|within|beyond|between|among|outside)\s/iu;
const PREDICATE = /(?<!\p{L})(?:є|існують|розташовано|розташовані|розташовуються|есть|имеются|расположены|находятся|są|jest|znajdują\s+się|are|is|lie|lies|exist|there\s+are)(?!\p{L})/iu;
const RELATIVE = /,\s*(?:which|who|that|що|який|яка|яке|які|который|которая|которые|которое|który|która|które)(?!\p{L})/iu;
const HEAD_PREFIX = /^(?:(?:the|a|an|each|every|some|all)\s+)*$/iu;
const PARTITIVE_PREFIX = /^(?:(?:the\s+)?(?:largest|smallest|biggest|main|major)\s+(?:objects|members|parts|examples)\s+(?:of\s+(?:the\s+)?)?|(?:найбільшими|найменшими|головними)\s+(?:об'єктами|членами|частинами)|(?:крупнейшими|наибольшими|наименьшими|главными)\s+(?:объектами|членами|частями)|(?:największymi|najmniejszymi|głównymi)\s+(?:obiektami|członkami|częściami))\s*$/iu;

async function subjectCandidates(text, lang, lexicon, dictionary) {
  const normalized = normalize(text), sceneWords = words(text);
  const forms = lexicon.flatMap(e => e.aliases.map(alias => ({title: e.title, alias, tokens: words(alias)})));
  const lemma = await dictionary.get(lang, [...sceneWords.map(w => w.text), ...forms.flatMap(f => f.tokens.map(w => w.text))]);
  const found = [];
  for (const form of forms) {
    const n = form.tokens.length;
    if (!n) continue;
    for (let i = 0; i + n <= sceneWords.length; i++) {
      const slice = sceneWords.slice(i, i + n);
      // Every token in order must match. No stopword deletion, prefix or partial match.
      if (!slice.every((w, j) => lemma.get(w.text).some(l => lemma.get(form.tokens[j].text).includes(l)))) continue;
      const start = slice[0].start, end = slice[n - 1].end;
      if (/[,;.!?]/u.test(normalized.slice(start, end))) continue;
      found.push({title: form.title, alias: form.alias, start, end, size: n, surface: text.slice(start, end), rawExact: slice.every((w,j) => w.text === form.tokens[j].text)});
    }
  }
  const bySpan = new Map();
  for (const f of found) {
    const key = `${normalize(f.title)}:${f.start}:${f.end}`;
    if (!bySpan.has(key) || f.rawExact) bySpan.set(key, f);
  }
  const unique = [...bySpan.values()].filter(f => f.rawExact || !found.some(g => g.start === f.start && g.end === f.end && g.rawExact));
  // A whole linked noun phrase wins over names embedded in that phrase.
  return unique.filter(f => !unique.some(g => g.start <= f.start && g.end >= f.end && g.size > f.size));
}

async function resolveSubject(text, lang, lexicon, dictionary, previous = null, identify = null) {
  if (!['uk', 'ru', 'pl', 'en'].includes(lang)) fail('unsupported_language', lang);
  if (!String(text || '').trim()) fail('empty_scene', 'Narration is required');
  let candidates = await subjectCandidates(text, lang, lexicon, dictionary);
  const alias = ALIAS.exec(text), comparison = COMPARISON.exec(text);
  let mode = 'current_subject';
  let locative = false;
  if (comparison) candidates = candidates.filter(c => c.start < comparison.index);
  if (alias && (!comparison || alias.index < comparison.index)) {
    const start = alias.index + alias[0].length;
    const stop = text.slice(start).search(/[,;.!?]/u);
    candidates = candidates.filter(c => c.start >= start && (stop < 0 || c.end <= start + stop));
    if (!candidates.length) fail('unresolved_alias', text);
    mode = 'current_explicit_alias';
  } else {
    // Leading locative adjuncts provide context, not the narrated entity.
    const predicate = LOCATIVE_START.test(text.trim()) ? PREDICATE.exec(text) : null;
    if (predicate) { candidates = candidates.filter(c => c.start >= predicate.index + predicate[0].length); locative = true; }
    const firstComma = text.indexOf(',');
    const leading = candidates.filter(c => firstComma < 0 || c.end <= firstComma);
    const relative = RELATIVE.exec(text);
    if (relative && leading.length) candidates = candidates.filter(c => c.end <= relative.index);
    else if (leading.some(c => c.size > 1) && /^,\s*(?:a|an)\s/iu.test(text.slice(firstComma))) candidates = leading;
    const anaphora = ANAPHORA.exec(text);
    const explicitPhrase = candidates.some(c => c.size > 1);
    if (anaphora && (firstComma < 0 || anaphora.index < firstComma) && !explicitPhrase) {
      if (!previous) fail('missing_antecedent', text);
      return {title: previous.localTitle, mode: 'previous_scene_anaphora', surface: anaphora[0], antecedentScene: previous.sceneIndex};
    }
  }
  const multi = candidates.filter(c => c.size > 1);
  if (multi.length) candidates = multi;
  const titles = [...new Set(candidates.map(c => normalize(c.title)))];
  // Multiple independent subjects need scene segmentation, not an arbitrary winner.
  if (!titles.length) fail('unresolved_subject', text);
  if (titles.length > 1) {
    const identities = identify ? await Promise.all(titles.map(t => identify(candidates.find(c => normalize(c.title) === t).title))) : titles;
    if (new Set(identities).size !== 1) fail('ambiguous_subject', `${text} -> ${candidates.map(c => c.title).join(' | ')}`);
  }
  const chosen = candidates.sort((a, b) => a.start - b.start || b.size - a.size)[0];
  if (mode === 'current_subject' && !locative) {
    const prefix = normalize(text.slice(0, chosen.start)).trimStart();
    if (!HEAD_PREFIX.test(prefix) && !PARTITIVE_PREFIX.test(prefix)) fail('unresolved_subject_role', text);
  }
  return {...chosen, mode, ...(mode === 'current_explicit_alias' ? {listText: text.slice(0, alias.index).replace(/,\s*$/, '').split(':').at(-1).trim()} : {})};
}

module.exports = {DictionaryLemmas, VisualPreflightError, fail, normalize, words, sourceLexicon, subjectCandidates, resolveSubject};
