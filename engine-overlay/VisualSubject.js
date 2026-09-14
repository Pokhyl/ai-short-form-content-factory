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

// Explicit examples describe a composite only in an existential clause. Other
// example lists remain subordinate to their current subject (e.g. X eats Y).
const EXAMPLES = /,\s*(?:such as|як-от|такі як|такие как|takie jak)\s+/iu;
const EXISTENTIAL = /(?:^there\s+are\s+|(?:^|\s)(?:there\s+are|є|есть|są)\s+)(?:other|інші|другие|inne)\s+/iu;
const CONJUNCTION = /^(?:and|та|і|и|oraz|i)$/iu;
async function exampleSubject(text, lang, lexicon, dictionary) {
  const marker = EXAMPLES.exec(text);
  if (!marker) return null;
  const head = text.slice(0, marker.index);
  const existential = EXISTENTIAL.exec(head);
  if (!existential) return {head};
  const currentHead = head.slice(existential.index + existential[0].length);
  const headMatches = await subjectCandidates(currentHead, lang, lexicon, dictionary);
  if (headMatches.length) return {head: currentHead};
  const start = marker.index + marker[0].length;
  const tail = text.slice(start);
  const boundary = RELATIVE.exec(tail);
  const listText = (boundary ? tail.slice(0, boundary.index) : tail).replace(/[.!?]\s*$/u, '').trim();
  const members = await subjectCandidates(listText, lang, lexicon, dictionary);
  const unmatched = words(listText).filter(w => !members.some(c => c.start <= w.start && c.end >= w.end));
  if (unmatched.some(w => !CONJUNCTION.test(w.text)) || members.length < 2) fail('unresolved_group_member', listText);
  return {mode: 'current_enumeration', listText, surface: listText};
}

const QUANTIFIER = /^(?:[0-9]+|one|two|three|four|five|six|seven|eight|nine|ten|each|every|all|some|of|the|один|два|дві|три|чотири|п'ять|шість|сім|вісім|восьми|дев'ять|десять|кожна|кожен|кожне|усі|всі|з|із|одна|две|четыре|пять|шесть|семь|восемь|восьми|девять|десять|каждая|каждый|каждое|все|из|jeden|dwa|dwie|trzy|cztery|pięć|sześć|siedem|osiem|dziewięć|dziesięć|każda|każdy|każde|wszystkie)$/iu;
function quantifiedHead(text, candidates) {
  const ordered = [...candidates].sort((a,b) => a.start-b.start || b.end-a.end);
  if (!ordered.length) return null;
  const prefix = words(text.slice(0, ordered[0].start));
  if (!prefix.length || !prefix.every(w => QUANTIFIER.test(w.text))) return null;
  const members = [ordered[0]];
  for (const candidate of ordered.slice(1)) {
    const last = members.at(-1);
    if (candidate.start < last.end) return null; // ambiguous aliases still fail below
    const gap = words(text.slice(last.end, candidate.start));
    if (!gap.some(w => CONJUNCTION.test(w.text)) || !gap.every(w => CONJUNCTION.test(w.text) || QUANTIFIER.test(w.text))) break;
    members.push(candidate);
  }
  const remainder = words(text.slice(members.at(-1).end));
  if (remainder.length && CONJUNCTION.test(remainder[0].text)) fail('unresolved_group_member', text);
  if (members.length > 1) return {mode:'current_enumeration', listText:members.map(c=>c.surface).join(', ')};
  return {...members[0], mode:'current_quantified_subject'};
}

async function resolveSubject(text, lang, lexicon, dictionary, previous = null, identify = null) {
  if (!['uk', 'ru', 'pl', 'en'].includes(lang)) fail('unsupported_language', lang);
  if (!String(text || '').trim()) fail('empty_scene', 'Narration is required');
  const examples = await exampleSubject(text, lang, lexicon, dictionary);
  if (examples?.mode) return examples;
  if (examples?.head) text = examples.head;
  let candidates = await subjectCandidates(text, lang, lexicon, dictionary);
  const alias = ALIAS.exec(text), comparison = COMPARISON.exec(text);
  if (!alias) {
    const quantified = quantifiedHead(text, candidates);
    if (quantified) return quantified;
  }
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
    const secondComma = firstComma < 0 ? -1 : text.indexOf(',', firstComma + 1);
    // A paired descriptive apposition starts with an unlinked description,
    // rather than a second coordinated entity. The following clause must also
    // have material before its first linked entity, not continue a noun list.
    const middleStart = secondComma < 0 ? -1 : words(text.slice(firstComma + 1, secondComma))[0]?.start + firstComma + 1;
    const tailStart = secondComma < 0 ? -1 : words(text.slice(secondComma + 1))[0]?.start + secondComma + 1;
    if (leading.length === 1 && HEAD_PREFIX.test(normalize(text.slice(0, leading[0].start))) &&
        secondComma > firstComma && candidates.some(c => c.start > middleStart && c.end <= secondComma) &&
        !candidates.some(c => c.start === middleStart || c.start === tailStart) &&
        !/^\s*(?:and|та|і|и|oraz|i)\s/iu.test(text.slice(secondComma + 1))) candidates = leading;
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
