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

class PexelsAPI {
  constructor(_apiKey) {
    this.articleMediaCache = new Map();
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
        iiprop: "url|mime|size",
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
        mediaByKey.set(fileKey, {
          id: `wikiarticle:${lang}:${fileKey}`,
          url,
          width: width || 1080,
          height: height || 1920,
          kind: "image",
          extension: mime.includes("png") ? ".png" : mime.includes("webp") ? ".webp" : ".jpg",
          source: "wikipedia_article",
          title: page.title,
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

  async _findArticleImage(spec, excludeIds) {
    const media = await this._loadArticleMedia(spec.lang, spec.title);
    let selected = media.find((item) => !excludeIds.includes(item.id));
    if (!selected) {
      selected = media[excludeIds.length % media.length];
      logger_1.logger.warn({ lang: spec.lang, title: spec.title, media: selected.title }, "Reusing source article image");
    }
    logger_1.logger.debug({ lang: spec.lang, title: spec.title, media: selected }, "Selected source article image");
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

  async findVideo(searchTerms, _minDurationSeconds, excludeIds = []) {
    const direct = (searchTerms || []).map(parseDirectMediaTerm).find(Boolean);
    if (direct) {
      logger_1.logger.debug({ media: direct }, 'Using preselected Wikimedia media');
      return direct;
    }
    const sceneSpec = (searchTerms || []).map(parseSceneTerm).find(Boolean);
    if (sceneSpec) {
      return await this._findSceneImage(sceneSpec, excludeIds);
    }

    const articleSpec = (searchTerms || []).map(parseArticleTerm).find(Boolean);
    if (articleSpec) {
      return await this._findArticleImage(articleSpec, excludeIds);
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
