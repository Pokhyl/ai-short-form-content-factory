"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PexelsAPI = void 0;
const logger_1 = require("../../logger");

const COMMONS_API = "https://commons.wikimedia.org/w/api.php";
const USER_AGENT =
  "ai-short-form-content-factory/1.0 (https://github.com/Pokhyl/ai-short-form-content-factory)";

function normalizeSearchTerm(value) {
  return String(value || "")
    .replace(/\s+(documentary|detail)$/i, "")
    .replace(/\s+/g, " ")
    .trim();
}


function parseDirectMediaTerm(value) {
  const match = /^directmedia::(.+)$/i.exec(String(value || "").trim());
  if (!match) return null;
  try {
    const media = JSON.parse(decodeURIComponent(match[1]));
    if (!media || !/^https:\/\//i.test(String(media.url || ''))) return null;
    return {
      id: `direct:${String(media.id || media.url)}`,
      url: String(media.url),
      width: Number(media.width || 1080),
      height: Number(media.height || 1920),
      kind: 'image',
      extension: String(media.extension || '.jpg'),
      source: 'preselected_wikimedia',
      title: String(media.title || ''),
    };
  } catch (_error) {
    return null;
  }
}

function parseArticleTerm(value) {
  const match = /^wikiarticle::([a-z-]+)::(.+)$/i.exec(String(value || "").trim());
  if (!match) return null;
  try {
    return {
      lang: match[1].toLowerCase(),
      title: decodeURIComponent(match[2]),
    };
  } catch (_error) {
    return null;
  }
}

function parseVisualSourceTerm(value) {
  const match = /^visualsource::([a-z-]+)::([^:]+)::(.+)$/i.exec(String(value || "").trim());
  if (!match) return null;
  try {
    return {
      sourceLang: match[1].toLowerCase(),
      sourceTitle: decodeURIComponent(match[2]),
      englishTitle: decodeURIComponent(match[3]),
    };
  } catch (_error) {
    return null;
  }
}

function parseMediaPreference(value) {
  const match = /^mediapreference::(image|video)$/i.exec(String(value || "").trim());
  return match ? match[1].toLowerCase() : null;
}

function parseSceneTerm(value) {
  const match = /^wikiscene::([a-z-]+)::(.+)$/i.exec(String(value || "").trim());
  if (!match) return null;
  try {
    return {
      lang: match[1].toLowerCase(),
      text: decodeURIComponent(match[2]),
    };
  } catch (_error) {
    return null;
  }
}

function normalizeFileKey(value) {
  return String(value || "")
    .replace(/^[^:]+:/, "")
    .replace(/_/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

function usefulArticleImage(filename) {
  const value = String(filename || "");
  if (!/\.(?:jpe?g|png|webp)$/i.test(value)) return false;
  if (/(?:logo|icon|emoji|symbol|quotation|wikidata|commons)/i.test(value)) return false;
  return true;
}

const STOPWORDS = new Set([
  "the","and","for","with","from","this","that","into","over","under",
  "це","що","який","яка","яке","які","його","її","їх","для","при","над","під","між","також","частина","частиною",
  "и","что","который","которая","которые","его","ее","их","для","при","над","под","между",
  "oraz","który","która","które","jego","jej","ich","dla","przy","nad","pod","między",
  "приблизно","близько","років","роки","року","рік","тому","мільярд","мільярда","мільярдів","мільйон","мільйона","мільйонів","відсотків","відсоток",
  "примерно","около","лет","года","год","назад","миллиард","миллиарда","миллиардов","миллион","миллиона","миллионов","процентов","процент",
  "około","lat","roku","rok","miliard","miliarda","miliardów","milion","miliona","milionów","procent","procentów",
  "approximately","about","years","year","ago","billion","billions","million","millions","percent","percentage",
  "нуль","один","одна","одне","два","дві","три","чотири","п'ять","п’ять","шість","сім","вісім","дев'ять","дев’ять","десять","одинадцять","дванадцять",
  "ноль","одна","одно","два","две","три","четыре","пять","шесть","семь","восемь","девять","десять","одиннадцать","двенадцать",
  "zero","one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve",
  "zero","jeden","jedna","jedno","dwa","dwie","trzy","cztery","pięć","sześć","siedem","osiem","dziewięć","dziesięć","jedenaście","dwanaście",
  "восьми","шести","семи","чотирьох","трьох","двох","одного","однієї"
]);

function plainText(value) {
  return String(value || "")
    .replace(/<[^>]+>/g, " ")
    .replace(/\{\{[^{}]*\}\}/g, " ")
    .replace(/\[\[(?:File|Image|Файл):[^\]]+\]\]/gi, " ")
    .replace(/\[\[([^|\]]+\|)?([^\]]+)\]\]/g, "$2")
    .replace(/[=*_#{}<>]/g, " ")
    .replace(/&[a-z]+;/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokens(value) {
  return [...new Set(plainText(value)
    .toLocaleLowerCase()
    .replace(/[’ʼ]/g, "'")
    .split(/[^\p{L}\p{N}']+/u)
    .map((token) => token.replace(/^'+|'+$/g, ""))
    .filter((token) => token.length >= 3 && !STOPWORDS.has(token)))];
}

function namedTokens(value) {
  const found = String(value || "").match(/\p{Lu}[\p{L}’ʼ'’-]{2,}/gu) || [];
  return new Set(found.map((token) => token.toLocaleLowerCase().replace(/[’ʼ]/g, "'")));
}

function relevanceScore(sceneText, media) {
  const sceneTokens = tokens(sceneText);
  if (!sceneTokens.length) return 0;
  const haystack = `${media.title || ""} ${media.searchText || ""}`;
  const candidateTokens = new Set(tokens(haystack));
  const named = namedTokens(sceneText);
  let score = 0;
  for (const token of sceneTokens) {
    if (!candidateTokens.has(token)) continue;
    score += named.has(token) ? 7 : token.length >= 7 ? 4 : 2;
  }
  const normalizedHaystack = plainText(haystack).toLocaleLowerCase();
  for (let i = 0; i < sceneTokens.length - 1; i++) {
    const phrase = `${sceneTokens[i]} ${sceneTokens[i + 1]}`;
    if (normalizedHaystack.includes(phrase)) score += 5;
  }
  return score;
}

function parseSceneContext(value) {
  const match = /^scenecontext::(.+)$/i.exec(String(value || "").trim());
  if (!match) return null;
  try { return decodeURIComponent(match[1]); } catch (_error) { return null; }
}

function parseSemanticContext(value) {
  const match = /^semanticcontext::(.+)$/i.exec(String(value || "").trim());
  if (!match) return null;
  try { return decodeURIComponent(match[1]); } catch (_error) { return null; }
}

function parseHistoryContext(value) {
  const match = /^historycontext::(.*)$/i.exec(String(value || "").trim());
  if (!match) return null;
  try { return decodeURIComponent(match[1]); } catch (_error) { return null; }
}

function entityAnchors(value) {
  const matches = String(value || "").match(/\p{Lu}[\p{L}’ʼ'’-]{2,}(?:\s+\p{Lu}[\p{L}’ʼ'’-]{2,})*/gu) || [];
  const anchors = [];
  for (const match of matches) {
    const words = match.split(/\s+/).filter(Boolean);
    while (words.length && STOPWORDS.has(words[0].toLocaleLowerCase())) words.shift();
    if (!words.length) continue;
    const anchor = words.join(" ").trim();
    if (anchor.length >= 4 && !anchors.includes(anchor)) anchors.push(anchor);
  }
  return anchors.slice(0, 8);
}

function stemLikeToken(value) {
  const normalized = String(value || "").toLocaleLowerCase().replace(/[’ʼ']/g, "");
  return normalized.slice(0, Math.min(3, normalized.length));
}

function morphTokenMatch(left, right) {
  const a = String(left || "").toLocaleLowerCase().replace(/[^\p{L}\p{N}]/gu, "");
  const b = String(right || "").toLocaleLowerCase().replace(/[^\p{L}\p{N}]/gu, "");
  if (!a || !b) return false;
  if (a === b) return true;
  const minLen = Math.min(a.length, b.length);
  const maxLen = Math.max(a.length, b.length);
  if (minLen < 4) return false;
  let common = 0;
  while (common < minLen && a[common] === b[common]) common++;
  const required = minLen <= 4 ? 3 : (a.length === b.length && minLen === 5 ? 4 : Math.min(5, minLen));
  return common >= required && (maxLen - minLen) <= 2;
}

function fuzzyEntityTitleMatch(anchor, title) {
  const anchorTokens = tokens(anchor);
  const titleTokens = tokens(title);
  if (!anchorTokens.length || !titleTokens.length) return false;
  return anchorTokens.every((anchorToken) => {
    const stem = stemLikeToken(anchorToken);
    return titleTokens.some((titleToken) => stem && stemLikeToken(titleToken) === stem);
  });
}

function semanticOverlapScore(context, title) {
  const contextStems = new Set(tokens(context).map(stemLikeToken).filter(Boolean));
  let score = 0;
  for (const token of tokens(title)) {
    const stem = stemLikeToken(token);
    if (stem && contextStems.has(stem)) score += 1;
  }
  return score;
}

class PexelsAPI {
  constructor(_apiKey) {
    this.articleMediaCache = new Map();
    this.articleLinksCache = new Map();
    this.englishTitleCache = new Map();
  }

  async _fetchJson(url) {
    const response = await fetch(url, {
      headers: { "User-Agent": USER_AGENT },
      signal: AbortSignal.timeout(10000),
    });
    if (!response.ok) {
      throw new Error(`Wikimedia API error: ${response.status} ${response.statusText}`);
    }
    return await response.json();
  }

  async _loadArticleMedia(lang, title) {
    if (!/^[a-z-]{2,12}$/i.test(lang)) throw new Error(`Invalid Wikipedia language: ${lang}`);
    const key = `${lang}:${title}`;
    if (this.articleMediaCache.has(key)) return this.articleMediaCache.get(key);

    const api = `https://${lang}.wikipedia.org/w/api.php`;
    const parseParams = new URLSearchParams({
      action: "parse",
      page: title,
      prop: "images",
      format: "json",
      origin: "*",
    });
    logger_1.logger.debug({ lang, title }, "Loading source article images");
    const parsed = await this._fetchJson(`${api}?${parseParams.toString()}`);
    const filenames = (parsed.parse?.images || [])
      .filter(usefulArticleImage)
      .slice(0, 60);
    if (!filenames.length) throw new Error(`No usable images in source article: ${title}`);

    const mediaByKey = new Map();
    for (let offset = 0; offset < filenames.length; offset += 20) {
      const chunk = filenames.slice(offset, offset + 20);
      const infoParams = new URLSearchParams({
        action: "query",
        titles: chunk.map((name) => `File:${name}`).join("|"),
        prop: "imageinfo",
        iiprop: "url|mime|size|extmetadata",
        iiurlwidth: "1080",
        format: "json",
        origin: "*",
      });
      const payload = await this._fetchJson(`${api}?${infoParams.toString()}`);
      for (const page of Object.values(payload.query?.pages || {})) {
        const info = Array.isArray(page.imageinfo) ? page.imageinfo[0] : null;
        if (!info) continue;
        const mime = String(info.mime || "");
        if (!/^image\/(jpeg|png|webp)$/i.test(mime)) continue;
        const width = Number(info.thumbwidth || info.width || 0);
        const height = Number(info.thumbheight || info.height || 0);
        if (!width || !height) continue;
        if (Math.max(width, height) < 500) continue;
        const aspectRatio = width / height;
        if (aspectRatio > 3 || aspectRatio < (1 / 3)) continue;
        const url = info.thumburl || info.url;
        if (!url || !/^https:\/\//i.test(url)) continue;
        const fileKey = normalizeFileKey(page.title);
        const metadata = info.extmetadata || {};
        const searchText = [
          page.title,
          metadata.ObjectName?.value,
          metadata.ImageDescription?.value,
          metadata.Categories?.value,
        ].filter(Boolean).map(plainText).join(" ");
        mediaByKey.set(fileKey, {
          id: `wikiarticle:${lang}:${fileKey}`,
          url,
          width: width || 1080,
          height: height || 1920,
          kind: "image",
          extension: mime.includes("png") ? ".png" : mime.includes("webp") ? ".webp" : ".jpg",
          source: "wikipedia_article",
          title: page.title,
          searchText,
        });
      }
    }

    const ordered = filenames
      .map((filename) => mediaByKey.get(normalizeFileKey(filename)))
      .filter(Boolean);
    if (!ordered.length) throw new Error(`No downloadable images in source article: ${title}`);
    this.articleMediaCache.set(key, ordered);
    logger_1.logger.debug({ lang, title, imageCount: ordered.length }, "Loaded source article media pool");
    return ordered;
  }

  async _loadArticleLinks(lang, title) {
    if (!/^[a-z-]{2,12}$/i.test(lang)) throw new Error(`Invalid Wikipedia language: ${lang}`);
    const key = `${lang}:${title}`;
    if (this.articleLinksCache.has(key)) return this.articleLinksCache.get(key);
    const api = `https://${lang}.wikipedia.org/w/api.php`;
    const links = [];
    let continuation = null;
    do {
      const params = new URLSearchParams({
        action: "query",
        titles: title,
        prop: "links",
        plnamespace: "0",
        pllimit: "max",
        redirects: "1",
        format: "json",
        origin: "*",
      });
      if (continuation) params.set("plcontinue", continuation);
      const payload = await this._fetchJson(`${api}?${params.toString()}`);
      const page = Object.values(payload.query?.pages || {})[0];
      for (const link of Array.isArray(page?.links) ? page.links : []) {
        const linkTitle = String(link.title || "").trim();
        if (linkTitle && !links.includes(linkTitle)) links.push(linkTitle);
      }
      continuation = payload.continue?.plcontinue || null;
    } while (continuation && links.length < 500);
    this.articleLinksCache.set(key, links);
    logger_1.logger.debug({ lang, title, linkCount: links.length }, "Loaded grounded source-article links");
    return links;
  }

  _rankSourceArticleLinks(sourceTitle, links, sceneText, semanticContext, historyContext = "") {
    const currentText = String(sceneText || "").trim();
    const semanticText = String(semanticContext || sceneText || "").trim();
    const historyText = String(historyContext || "").trim();
    const currentTokens = tokens(currentText);
    const semanticTokens = tokens(semanticText);
    const historyTokens = tokens(historyText);
    if (!currentTokens.length && !semanticTokens.length && !historyTokens.length) return [];

    const normalizedSource = plainText(sourceTitle).toLocaleLowerCase();
    const currentNamed = [...namedTokens(currentText)];
    const aliasMatch = /(?:зван(?:і|ий|а|е)\s+також|також\s+назива(?:ють|ються)|назива(?:ють|ються)|называем(?:ые|ый|ая|ое)\s+также|также\s+называ(?:ют|ются)|zwane\s+(?:również|także)|nazywane\s+(?:również|także)|also\s+known\s+as|also\s+called|called)\s+([^,.!?]{2,80})/iu.exec(currentText);
    const aliasTokens = tokens(aliasMatch?.[1] || "");
    const anaphoraTokens = new Set([
      "цих","цього","цьому","них","нього","неї","вони","вона","він","воно","цей","ця",
      "этих","этого","него","неё","они","она","это","этот","эта",
      "tych","tego","nich","jego","jej","oni","one","ten",
      "these","those","this","that","them",
    ]);
    const currentUsesAnaphora = currentTokens.some((token) => anaphoraTokens.has(token));
    const ranked = [];

    for (const linkTitle of links) {
      const coreTitle = String(linkTitle || "").replace(/\s*\([^)]*\)\s*$/u, "").trim();
      const normalizedTitle = plainText(coreTitle).toLocaleLowerCase();
      if (!normalizedTitle || normalizedTitle === normalizedSource) continue;
      const titleTokens = tokens(coreTitle);
      if (!titleTokens.length) continue;

      const currentMatches = titleTokens.filter((token) => currentTokens.some((candidate) => morphTokenMatch(token, candidate)));
      const semanticMatches = titleTokens.filter((token) => semanticTokens.some((candidate) => morphTokenMatch(token, candidate)));
      const historyMatches = titleTokens.filter((token) => historyTokens.some((candidate) => morphTokenMatch(token, candidate)));
      const aliasMatches = titleTokens.filter((token) => aliasTokens.some((candidate) => morphTokenMatch(token, candidate)));
      const namedCurrentMatch = titleTokens.some((token) => currentNamed.some((candidate) => morphTokenMatch(token, candidate)));
      const currentPosition = currentTokens.findIndex((candidate) => titleTokens.some((token) => morphTokenMatch(token, candidate)));

      const fullCurrent = currentMatches.length === titleTokens.length;
      const fullSemantic = semanticMatches.length === titleTokens.length;
      const fullAlias = aliasTokens.length > 0 && aliasMatches.length === titleTokens.length && titleTokens.length >= 2;
      const fullHistory = currentUsesAnaphora && historyMatches.length === titleTokens.length && titleTokens.length >= 2;
      const singleNamedCurrent = titleTokens.length === 1 && fullCurrent && namedCurrentMatch;

      // Deterministic resolver: only entities fully grounded in the current
      // semantic scene are eligible. History is allowed solely for explicit
      // anaphora. No partial/fuzzy subject substitution.
      if (!fullAlias && !fullCurrent && !fullSemantic && !fullHistory && !singleNamedCurrent) continue;
      if (titleTokens.length === 1 && !singleNamedCurrent) continue;

      let resolutionMode = "current_exact";
      const positionBoost = Math.max(0, 100 - Math.min(100, currentPosition < 0 ? 100 : currentPosition));
      let priority = 0;
      if (fullAlias) {
        resolutionMode = "current_alias_exact";
        priority = 700 + titleTokens.length * 10 + positionBoost;
      } else if (fullCurrent && titleTokens.length >= 2) {
        resolutionMode = "current_exact_multi";
        priority = 600 + positionBoost + titleTokens.length;
      } else if (fullSemantic && titleTokens.length >= 2) {
        resolutionMode = "semantic_exact_multi";
        priority = 500 + positionBoost + titleTokens.length;
      } else if (singleNamedCurrent) {
        resolutionMode = "current_exact_named";
        priority = 400 + positionBoost;
      } else if (fullHistory) {
        resolutionMode = "history_anaphora_exact";
        priority = 300 + titleTokens.length * 10;
      } else {
        continue;
      }

      ranked.push({
        title: linkTitle,
        score: priority,
        coverage: 1,
        namedPrefix: singleNamedCurrent,
        currentMatched: currentMatches.length,
        semanticMatched: semanticMatches.length,
        historyMatched: historyMatches.length,
        tokenCount: titleTokens.length,
        currentPosition: currentPosition < 0 ? 999 : currentPosition,
        resolutionMode,
      });
    }

    ranked.sort((a, b) =>
      b.score - a.score ||
      b.tokenCount - a.tokenCount ||
      a.currentPosition - b.currentPosition ||
      a.title.length - b.title.length
    );

    const selected = ranked.slice(0, 4);
    logger_1.logger.debug({ sceneText, semanticContext, historyContext, candidates: selected }, "Exact grounded source-link resolution");
    return selected;
  }

  async _englishTitleForLocalPage(lang, title) {
    if (!title) return null;
    if (lang === "en") return title;
    const key = `${lang}:${title}`;
    if (this.englishTitleCache.has(key)) return this.englishTitleCache.get(key);
    const api = `https://${lang}.wikipedia.org/w/api.php`;
    const params = new URLSearchParams({
      action: "query",
      titles: title,
      redirects: "1",
      prop: "langlinks",
      lllang: "en",
      lllimit: "1",
      format: "json",
      origin: "*",
    });
    const payload = await this._fetchJson(`${api}?${params.toString()}`);
    const page = Object.values(payload.query?.pages || {})[0];
    const englishTitle = Array.isArray(page?.langlinks) ? page.langlinks[0]?.["*"] || null : null;
    this.englishTitleCache.set(key, englishTitle);
    return englishTitle;
  }

  async _findExactEnglishPageImage(title) {
    if (!title) return null;
    const params = new URLSearchParams({
      action: "query",
      titles: title,
      redirects: "1",
      prop: "pageimages",
      piprop: "thumbnail",
      pithumbsize: "1080",
      format: "json",
      origin: "*",
    });
    const payload = await this._fetchJson(`https://en.wikipedia.org/w/api.php?${params.toString()}`);
    const page = Object.values(payload.query?.pages || {})[0];
    const thumb = page?.thumbnail;
    if (!thumb?.source || !/^https:\/\//i.test(thumb.source)) return null;
    const path = new URL(thumb.source).pathname.toLowerCase();
    let extension = null;
    if (/\.png(?:\/|$)/.test(path)) extension = ".png";
    else if (/\.webp(?:\/|$)/.test(path)) extension = ".webp";
    else if (/\.jpe?g(?:\/|$)/.test(path)) extension = ".jpg";
    if (!extension) return null;
    return {
      id: `enwiki:${page.pageid}`,
      url: thumb.source,
      width: Number(thumb.width || 1080),
      height: Number(thumb.height || 1920),
      kind: "image",
      extension,
      source: "english_wikipedia_page",
      title: String(page.title || title),
      searchText: String(page.title || title),
    };
  }

  async _findEnglishCommonsMedia(query, excludeIds, targetAspect, preferVideo = false) {
    const search = preferVideo ? `${query} filetype:video` : query;
    const params = new URLSearchParams({
      action: "query",
      generator: "search",
      gsrsearch: search,
      gsrnamespace: "6",
      gsrlimit: "24",
      prop: "imageinfo",
      iiprop: "url|mime|size|extmetadata",
      iiurlwidth: "1080",
      format: "json",
      origin: "*",
    });
    const payload = await this._fetchJson(`${COMMONS_API}?${params.toString()}`);
    const candidates = [];
    for (const page of Object.values(payload.query?.pages || {})) {
      const info = Array.isArray(page.imageinfo) ? page.imageinfo[0] : null;
      if (!info) continue;
      const mime = String(info.mime || "").toLowerCase();
      const isImage = /^image\/(jpeg|png|webp)$/.test(mime);
      const isVideo = /^video\/(webm|mp4)$/.test(mime);
      if (!isImage && !isVideo) continue;
      if (preferVideo && !isVideo) continue;
      const width = Number(info.thumbwidth || info.width || 0);
      const height = Number(info.thumbheight || info.height || 0);
      if (!width || !height || Math.max(width, height) < 700) continue;
      const aspect = width / height;
      if (aspect > 3 || aspect < 1 / 3) continue;
      const url = isVideo ? info.url : (info.thumburl || info.url);
      if (!url || !/^https:\/\//i.test(url)) continue;
      const extension = isVideo ? (mime.includes("mp4") ? ".mp4" : ".webm") : mime.includes("png") ? ".png" : mime.includes("webp") ? ".webp" : ".jpg";
      const metadata = info.extmetadata || {};
      const searchText = [page.title, metadata.ObjectName?.value, metadata.ImageDescription?.value, metadata.Categories?.value]
        .filter(Boolean).map(plainText).join(" ");
      const item = {
        id: `commons:${page.pageid}`,
        url,
        width,
        height,
        kind: isVideo ? "video" : "image",
        extension,
        source: "english_commons_search",
        title: String(page.title || ""),
        searchText,
      };
      if (isVideo && /\b(song|music|lyrics?|karaoke|youtube)\b/i.test(searchText)) continue;
      if (excludeIds.includes(item.id)) continue;
      const normalizedQueryKey = normalizeFileKey(query);
      const normalizedTitleKey = normalizeFileKey(page.title);
      const safeQueryPrefix = Boolean(normalizedQueryKey) && (
        normalizedTitleKey === normalizedQueryKey ||
        normalizedTitleKey.startsWith(`${normalizedQueryKey} `) ||
        normalizedTitleKey.startsWith(`${normalizedQueryKey}-`)
      );
      if (!preferVideo && !safeQueryPrefix) continue;
      const relevance = relevanceScore(query, item);
      const aspectPenalty = Number.isFinite(targetAspect) && targetAspect > 0
        ? Math.abs(Math.log(Math.max(0.01, aspect) / targetAspect))
        : 0;
      candidates.push({ item, relevance, aspectPenalty });
    }
    candidates.sort((a, b) => b.relevance - a.relevance || a.aspectPenalty - b.aspectPenalty);
    const selected = candidates[0]?.item || null;
    if (selected) logger_1.logger.debug({ query, preferVideo, media: selected }, "Selected English Commons media");
    return selected;
  }

  async _findEnglishVisual(spec, sceneText, semanticContext, historyContext, excludeIds, targetAspect, preferVideo) {
    const links = await this._loadArticleLinks(spec.sourceLang, spec.sourceTitle);
    const rankedConcepts = this._rankSourceArticleLinks(spec.sourceTitle, links, sceneText, semanticContext, historyContext);
    const primary = rankedConcepts[0] || null;
    if (!primary) {
      throw new Error(`No exact grounded entity for scene: ${sceneText}`);
    }

    const primaryEnglish = await this._englishTitleForLocalPage(spec.sourceLang, primary.title);
    if (!primaryEnglish) {
      throw new Error(`No English entity mapping for grounded scene entity: ${primary.title}`);
    }

    logger_1.logger.debug({
      sourceLang: spec.sourceLang,
      sourceTitle: spec.sourceTitle,
      sceneText,
      semanticContext,
      historyContext,
      primary,
      primaryEnglish,
      preferVideo,
    }, "Resolved exact English visual entity");

    const withResolution = (media, resolutionType, confidence) => media ? ({
      ...media,
      visualQuery: primaryEnglish,
      groundedEntity: primaryEnglish,
      resolutionType,
      confidence,
    }) : null;

    const exactImage = await this._findExactEnglishPageImage(primaryEnglish);
    if (exactImage && !excludeIds.includes(exactImage.id)) {
      return withResolution(exactImage, "exact_english_wikipedia", "high");
    }

    if (preferVideo) {
      const video = await this._findEnglishCommonsMedia(primaryEnglish, excludeIds, targetAspect, true);
      if (video?.kind === "video") {
        return withResolution(video, "exact_entity_commons_video", "high");
      }
    }

    const commons = await this._findEnglishCommonsMedia(primaryEnglish, excludeIds, targetAspect, false);
    if (commons) {
      return withResolution(commons, "exact_entity_commons_image", "high");
    }

    throw new Error(`No exact visual media for grounded entity: ${primaryEnglish}`);
  }

  async _findNamedEntityImage(lang, sceneText, excludeIds, sourceTitle = "", semanticContext = "") {
    if (!/^[a-z-]{2,12}$/i.test(lang)) return null;
    const sourceStems = new Set(tokens(sourceTitle).map(stemLikeToken));
    const anchors = entityAnchors(sceneText)
      .map((anchor, index) => ({
        anchor,
        index,
        sourceOverlap: tokens(anchor).filter((token) => sourceStems.has(stemLikeToken(token))).length,
      }))
      .sort((a, b) => a.sourceOverlap - b.sourceOverlap || a.index - b.index)
      .map((item) => item.anchor);
    if (!anchors.length) return null;
    const api = `https://${lang}.wikipedia.org/w/api.php`;
    for (const anchor of anchors) {
      const params = new URLSearchParams({
        action: "query",
        titles: anchor,
        redirects: "1",
        prop: "pageimages|pageprops",
        piprop: "thumbnail",
        ppprop: "wikibase_item",
        pithumbsize: "1080",
        format: "json",
        origin: "*",
      });
      const payload = await this._fetchJson(`${api}?${params.toString()}`);
      const pages = Object.values(payload.query?.pages || {});
      let exactPageExists = false;
      for (const page of pages) {
        if (page.missing !== undefined) continue;
        exactPageExists = true;
        const id = `wikientity:${lang}:${page.pageid}`;

        let mediaUrl = page.thumbnail?.source || null;
        let mediaWidth = Number(page.thumbnail?.width || 0);
        let mediaHeight = Number(page.thumbnail?.height || 0);
        let mediaMime = "";
        let mediaSource = "wikipedia_named_entity";

        if (!mediaUrl || !/^https:\/\//i.test(mediaUrl)) {
          const qid = page.pageprops?.wikibase_item;
          if (qid) {
            const claimParams = new URLSearchParams({
              action: "wbgetclaims",
              entity: qid,
              property: "P18",
              format: "json",
              origin: "*",
            });
            const claims = await this._fetchJson(`https://www.wikidata.org/w/api.php?${claimParams.toString()}`);
            const filename = claims.claims?.P18?.[0]?.mainsnak?.datavalue?.value;
            if (filename) {
              const fileParams = new URLSearchParams({
                action: "query",
                titles: `File:${filename}`,
                prop: "imageinfo",
                iiprop: "url|mime|size",
                iiurlwidth: "1080",
                format: "json",
                origin: "*",
              });
              const filePayload = await this._fetchJson(`${COMMONS_API}?${fileParams.toString()}`);
              const filePage = Object.values(filePayload.query?.pages || {})[0];
              const info = Array.isArray(filePage?.imageinfo) ? filePage.imageinfo[0] : null;
              if (info) {
                mediaUrl = info.thumburl || info.url || null;
                mediaWidth = Number(info.thumbwidth || info.width || 0);
                mediaHeight = Number(info.thumbheight || info.height || 0);
                mediaMime = String(info.mime || "");
                mediaSource = "wikidata_p18";
              }
            }
          }
        }

        if (!mediaUrl || !/^https:\/\//i.test(mediaUrl)) continue;
        let extension = null;
        if (/png/i.test(mediaMime)) extension = ".png";
        else if (/webp/i.test(mediaMime)) extension = ".webp";
        else if (/jpe?g/i.test(mediaMime)) extension = ".jpg";
        if (!extension) {
          const urlPath = new URL(mediaUrl).pathname.toLowerCase();
          if (/\.png(?:\/|$)/.test(urlPath)) extension = ".png";
          else if (/\.webp(?:\/|$)/.test(urlPath)) extension = ".webp";
          else if (/\.jpe?g(?:\/|$)/.test(urlPath)) extension = ".jpg";
        }
        if (!extension) continue;
        const anchorTokens = tokens(anchor);
        const titleTokens = tokens(page.title);
        const normalizedAnchor = plainText(anchor).toLocaleLowerCase();
        const normalizedTitle = plainText(page.title).toLocaleLowerCase();
        const directPrefixMatch = normalizedTitle.startsWith(normalizedAnchor);
        const singleTokenInflectionMatch = anchorTokens.length === 1 &&
          titleTokens.length === 1 &&
          stemLikeToken(anchorTokens[0]) === stemLikeToken(titleTokens[0]);
        const multiwordInflectionMatch = anchorTokens.length > 1 && fuzzyEntityTitleMatch(anchor, page.title);
        if (!directPrefixMatch && !singleTokenInflectionMatch && !multiwordInflectionMatch) {
          logger_1.logger.debug(
            { lang, sceneText, anchor, matchedPage: page.title },
            "Rejected ambiguous named-entity redirect",
          );
          continue;
        }
        const media = {
          id,
          url: mediaUrl,
          width: mediaWidth || 1080,
          height: mediaHeight || 1920,
          kind: "image",
          extension,
          source: mediaSource,
          title: page.title,
          searchText: `${anchor} ${page.title}`,
        };
        logger_1.logger.debug({ lang, sceneText, anchor, matchedPage: page.title, media }, "Selected exact named-entity image");
        return media;
      }

      if (!exactPageExists && !anchor.includes(" ")) continue;

      const searchParams = new URLSearchParams({
        action: "query",
        generator: "search",
        gsrsearch: anchor,
        gsrnamespace: "0",
        gsrlimit: "5",
        prop: "pageimages",
        piprop: "thumbnail",
        pithumbsize: "1080",
        format: "json",
        origin: "*",
      });
      const searchPayload = await this._fetchJson(`${api}?${searchParams.toString()}`);
      const anchorTokenCount = Math.max(1, tokens(anchor).length);
      const disambiguationContext = semanticContext || sceneText;
      const candidates = Object.values(searchPayload.query?.pages || {})
        .sort((a, b) => {
          const aTitle = String(a.title || "");
          const bTitle = String(b.title || "");
          const aExact = aTitle.toLocaleLowerCase().startsWith(anchor.toLocaleLowerCase()) ? 0 : 1;
          const bExact = bTitle.toLocaleLowerCase().startsWith(anchor.toLocaleLowerCase()) ? 0 : 1;
          if (aExact !== bExact) return aExact - bExact;
          const aSemantic = semanticOverlapScore(disambiguationContext, aTitle);
          const bSemantic = semanticOverlapScore(disambiguationContext, bTitle);
          if (aSemantic !== bSemantic) return bSemantic - aSemantic;
          const aExtra = Math.abs(tokens(aTitle).length - anchorTokenCount);
          const bExtra = Math.abs(tokens(bTitle).length - anchorTokenCount);
          if (aExtra !== bExtra) return aExtra - bExtra;
          return Number(a.index || 9999) - Number(b.index || 9999);
        });
      logger_1.logger.debug({
        lang,
        sceneText,
        anchor,
        candidates: candidates.map((page) => ({
          index: Number(page.index || 9999),
          title: page.title,
          tokenCount: tokens(page.title).length,
          exactPrefix: String(page.title || "").toLocaleLowerCase().startsWith(anchor.toLocaleLowerCase()),
          fuzzyMatch: anchor.includes(" ") && fuzzyEntityTitleMatch(anchor, page.title),
          semanticScore: semanticOverlapScore(semanticContext || sceneText, page.title),
          hasThumbnail: Boolean(page.thumbnail?.source),
        })),
      }, "Named-entity candidate ranking");
      for (const page of candidates) {
        const normalizedTitle = String(page.title || "").toLocaleLowerCase();
        const exactTitlePrefix = normalizedTitle.startsWith(anchor.toLocaleLowerCase());
        const inflectedMultiwordMatch = anchor.includes(" ") && fuzzyEntityTitleMatch(anchor, page.title);
        if (!exactTitlePrefix && !inflectedMultiwordMatch) continue;
        const thumb = page.thumbnail;
        if (!thumb?.source || !/^https:\/\//i.test(thumb.source)) continue;
        const id = `wikientity:${lang}:${page.pageid}`;
        const urlPath = new URL(thumb.source).pathname.toLowerCase();
        let extension = null;
        if (/\.png(?:\/|$)/.test(urlPath)) extension = ".png";
        else if (/\.webp(?:\/|$)/.test(urlPath)) extension = ".webp";
        else if (/\.jpe?g(?:\/|$)/.test(urlPath)) extension = ".jpg";
        if (!extension) continue;
        const media = {
          id,
          url: thumb.source,
          width: Number(thumb.width || 1080),
          height: Number(thumb.height || 1920),
          kind: "image",
          extension,
          source: "wikipedia_named_entity_search",
          title: page.title,
          searchText: `${anchor} ${page.title}`,
        };
        logger_1.logger.debug({ lang, sceneText, anchor, matchedPage: page.title, media }, "Resolved named entity through localized search");
        return media;
      }
    }
    return null;
  }

  async _findArticleImage(spec, excludeIds, targetAspect = null, sceneText = "", semanticContext = "") {
    if (sceneText) {
      const entityMedia = await this._findNamedEntityImage(spec.lang, sceneText, excludeIds, spec.title, semanticContext);
      if (entityMedia) return entityMedia;

      logger_1.logger.debug(
        { lang: spec.lang, title: spec.title, sceneText, semanticContext },
        "No confident named entity; using source-article media",
      );
    }
    const media = await this._loadArticleMedia(spec.lang, spec.title);
    const available = media.filter((item) => !excludeIds.includes(item.id));
    const context = [sceneText, semanticContext].filter(Boolean).join(" ");
    const rankedAll = [...media].map((item) => {
      const relevance = relevanceScore(context, item);
      const aspect = Math.max(0.01, Number(item.width || 1) / Number(item.height || 1));
      const aspectPenalty = Number.isFinite(targetAspect) && targetAspect > 0
        ? Math.abs(Math.log(aspect / targetAspect))
        : 0;
      return { item, relevance, aspectPenalty };
    }).sort((a, b) => {
      if (b.relevance !== a.relevance) return b.relevance - a.relevance;
      return a.aspectPenalty - b.aspectPenalty;
    });

    const bestRelevant = rankedAll.find((entry) => entry.relevance > 0);
    let selected = null;
    let selectedRelevance = 0;
    if (bestRelevant) {
      selected = bestRelevant.item;
      selectedRelevance = bestRelevant.relevance;
    } else {
      const aspectPool = available.length ? available : media;
      selected = [...aspectPool].sort((a, b) => {
        const ar = Math.max(0.01, Number(a.width || 1) / Number(a.height || 1));
        const br = Math.max(0.01, Number(b.width || 1) / Number(b.height || 1));
        const ap = Number.isFinite(targetAspect) && targetAspect > 0 ? Math.abs(Math.log(ar / targetAspect)) : 0;
        const bp = Number.isFinite(targetAspect) && targetAspect > 0 ? Math.abs(Math.log(br / targetAspect)) : 0;
        return ap - bp;
      })[0] || media[0];
    }
    if (excludeIds.includes(selected.id)) {
      logger_1.logger.debug({ lang: spec.lang, title: spec.title, sceneText, semanticContext, media: selected.title }, "Reusing relevant source image instead of selecting unrelated media");
    }
    logger_1.logger.debug({ lang: spec.lang, title: spec.title, sceneText, semanticContext, targetAspect, relevance: selectedRelevance, media: selected }, "Selected scene-relevant source image");
    return selected;
  }

  async _findSceneImage(spec, excludeIds) {
    if (!/^[a-z-]{2,12}$/i.test(spec.lang)) throw new Error(`Invalid Wikipedia language: ${spec.lang}`);
    const query = String(spec.text || '').replace(/\s+/g, ' ').trim();
    if (!query) throw new Error('Empty scene media query');

    const api = `https://${spec.lang}.wikipedia.org/w/api.php`;
    const params = new URLSearchParams({
      action: 'query',
      generator: 'search',
      gsrsearch: query,
      gsrnamespace: '0',
      gsrlimit: '5',
      prop: 'pageimages',
      piprop: 'thumbnail',
      pithumbsize: '1080',
      format: 'json',
      origin: '*',
    });
    logger_1.logger.debug({ lang: spec.lang, sceneText: query }, 'Searching localized Wikipedia page for scene');
    const payload = await this._fetchJson(`${api}?${params.toString()}`);
    const pages = Object.values(payload.query?.pages || {})
      .sort((a, b) => Number(a.index || 9999) - Number(b.index || 9999));

    const candidates = [];
    for (const page of pages) {
      const thumb = page.thumbnail;
      if (!thumb?.source || !/^https:\/\//i.test(thumb.source)) continue;
      if (Math.max(Number(thumb.width || 0), Number(thumb.height || 0)) < 700) continue;
      const urlPath = new URL(thumb.source).pathname.toLowerCase();
      let extension = null;
      if (urlPath.endsWith('.png')) extension = '.png';
      else if (urlPath.endsWith('.webp')) extension = '.webp';
      else if (urlPath.endsWith('.jpg') || urlPath.endsWith('.jpeg')) extension = '.jpg';
      if (!extension) continue;
      candidates.push({
        id: `wikiscene:${spec.lang}:${page.pageid}`,
        url: thumb.source,
        width: Number(thumb.width || 1080),
        height: Number(thumb.height || 1920),
        kind: 'image',
        extension,
        source: 'wikipedia_scene_page',
        title: page.title,
      });
    }
    if (!candidates.length) throw new Error(`No localized Wikipedia page image found for scene: ${query}`);

    const selected = candidates.find((item) => !excludeIds.includes(item.id)) || candidates[0];
    logger_1.logger.debug(
      { lang: spec.lang, sceneText: query, matchedPage: selected.title, media: selected },
      'Selected localized scene image',
    );
    return selected;
  }

  async _findImage(searchTerm, excludeIds) {
    const query = normalizeSearchTerm(searchTerm);
    if (!query) throw new Error("Empty media search term");

    const params = new URLSearchParams({
      action: "query",
      generator: "search",
      gsrsearch: query,
      gsrnamespace: "6",
      gsrlimit: "24",
      prop: "imageinfo",
      iiprop: "url|mime|size",
      iiurlwidth: "1080",
      format: "json",
      origin: "*",
    });

    logger_1.logger.debug({ searchTerm: query }, "Searching Wikimedia Commons media");
    const payload = await this._fetchJson(`${COMMONS_API}?${params.toString()}`);
    const pages = Object.values(payload.query?.pages || {})
      .sort((a, b) => Number(a.index || 9999) - Number(b.index || 9999));

    for (const page of pages) {
      const id = Number(page.pageid);
      if (!Number.isFinite(id) || excludeIds.includes(id)) continue;
      const info = Array.isArray(page.imageinfo) ? page.imageinfo[0] : null;
      if (!info) continue;
      const mime = String(info.mime || "");
      if (!mime.startsWith("image/")) continue;
      const url = info.thumburl || info.url;
      if (!url || !/^https:\/\//i.test(url)) continue;
      const extension = mime.includes("png") ? ".png" : mime.includes("webp") ? ".webp" : ".jpg";
      const media = {
        id,
        url,
        width: Number(info.thumbwidth || info.width || 1080),
        height: Number(info.thumbheight || info.height || 1920),
        kind: "image",
        extension,
        source: "wikimedia_commons",
        title: page.title,
      };
      logger_1.logger.debug({ searchTerm: query, media }, "Found Wikimedia Commons image");
      return media;
    }
    throw new Error(`No Wikimedia Commons image found for: ${query}`);
  }

  async findVideo(searchTerms, _minDurationSeconds, excludeIds = [], _orientation = null, targetAspect = null) {
    const direct = (searchTerms || []).map(parseDirectMediaTerm).find(Boolean);
    if (direct) {
      logger_1.logger.debug({ media: direct }, 'Using preselected Wikimedia media');
      return direct;
    }
    const visualSource = (searchTerms || []).map(parseVisualSourceTerm).find(Boolean);
    if (visualSource) {
      const sceneText = (searchTerms || []).map(parseSceneContext).find(Boolean) || "";
      const semanticContext = (searchTerms || []).map(parseSemanticContext).find(Boolean) || sceneText;
      const historyContext = (searchTerms || []).map(parseHistoryContext).find((value) => value !== null) || "";
      const preference = (searchTerms || []).map(parseMediaPreference).find(Boolean) || "image";
      return await this._findEnglishVisual(
        visualSource,
        sceneText,
        semanticContext,
        historyContext,
        excludeIds,
        targetAspect,
        preference === "video",
      );
    }

    const sceneSpec = (searchTerms || []).map(parseSceneTerm).find(Boolean);
    if (sceneSpec) {
      return await this._findSceneImage(sceneSpec, excludeIds);
    }

    const articleSpec = (searchTerms || []).map(parseArticleTerm).find(Boolean);
    if (articleSpec) {
      const sceneText = (searchTerms || []).map(parseSceneContext).find(Boolean) || "";
      const semanticContext = (searchTerms || []).map(parseSemanticContext).find(Boolean) || sceneText;
      return await this._findArticleImage(articleSpec, excludeIds, targetAspect, sceneText, semanticContext);
    }

    const normalized = [...new Set((searchTerms || []).map(normalizeSearchTerm).filter(Boolean))];
    let lastError = null;
    for (const term of normalized) {
      try {
        return await this._findImage(term, excludeIds);
      } catch (error) {
        lastError = error;
        logger_1.logger.warn({ searchTerm: term, error: String(error) }, "Commons media search term failed");
      }
    }
    throw lastError || new Error("No Wikimedia Commons media found");
  }
}
exports.PexelsAPI = PexelsAPI;