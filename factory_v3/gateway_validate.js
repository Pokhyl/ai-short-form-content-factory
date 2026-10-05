'use strict';
function validateProviderRequest(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw new Error('invalid gateway request');
  const provider = input.provider;
  const request = input.request || {};
  const query = request.query || {};
  const body = request.body;
  const model = 'gemini-3.5-flash-lite';
  const boundedQuery = (q) => {
    if (typeof q !== 'string' || !q.trim() || q.length > 100) throw new Error('photo query exceeds bounds');
  };
  let url, method = 'GET';
  if (provider === 'pixabay') {
    boundedQuery(query.q);
    if (query.per_page !== 8 || query.image_type !== 'photo' || query.safesearch !== 'true' ||
        query.lang !== 'en' || !['all','horizontal','vertical'].includes(query.orientation) ||
        Object.keys(query).some(k => !['q','per_page','image_type','safesearch','lang','orientation'].includes(k))) {
      throw new Error('unsupported Pixabay settings');
    }
    url = 'https://pixabay.com/api/';
  } else if (provider === 'pexels') {
    boundedQuery(query.query);
    if (query.per_page !== 8 || (query.orientation && !['portrait','landscape'].includes(query.orientation)) ||
        Object.keys(query).some(k => !['query','per_page','orientation'].includes(k))) {
      throw new Error('unsupported Pexels settings');
    }
    url = 'https://api.pexels.com/v1/search';
  } else if (provider === 'gemini') {
    method = 'POST';
    url = 'https://generativelanguage.googleapis.com/v1beta/models/' + model + ':generateContent';
    if (!body || Object.keys(body).some(k => !['systemInstruction','contents','generationConfig'].includes(k)) ||
        !Array.isArray(body.contents) || body.contents.length !== 1 ||
        body.generationConfig?.candidateCount !== 1 ||
        body.generationConfig?.responseMimeType !== 'application/json' ||
        Object.keys(body.generationConfig || {}).some(k => !['candidateCount','maxOutputTokens','responseMimeType','responseJsonSchema'].includes(k)) ||
        !Number.isInteger(body.generationConfig?.maxOutputTokens) ||
        body.generationConfig.maxOutputTokens < 1 || body.generationConfig.maxOutputTokens > 16384 ||
        JSON.stringify(body).length > 14 * 1024 * 1024) throw new Error('unsupported Gemini request');
  } else if (provider === 'google_tts') {
    method = 'POST';
    url = 'https://texttospeech.googleapis.com/v1/text:synthesize';
    const voices = {
      'en-US':'en-US-Chirp3-HD-Algenib','pl-PL':'pl-PL-Chirp3-HD-Enceladus',
      'ru-RU':'ru-RU-Wavenet-D','uk-UA':'uk-UA-Chirp3-HD-Enceladus'
    };
    if (!body || Object.keys(body).some(k => !['input','voice','audioConfig'].includes(k)) ||
        typeof body.input?.text !== 'string' || !body.input.text.trim() || body.input.text.length > 8000 ||
        Object.keys(body.input).length !== 1 ||
        voices[body.voice?.languageCode] !== body.voice?.name || Object.keys(body.voice).length !== 2 ||
        body.audioConfig?.audioEncoding !== 'MP3' || Object.keys(body.audioConfig).length !== 1) {
      throw new Error('unsupported final TTS request');
    }
  } else if (provider === 'gemini_info') {
    if (Object.keys(request).length) throw new Error('model metadata request must be fixed');
    url = 'https://generativelanguage.googleapis.com/v1beta/models/' + model;
  } else if (provider === 'google_metadata') {
    if (request.operation === 'key_owner') {
      if (typeof body?.key_string !== 'string' || !body.key_string || body.key_string.length > 1024) {
        throw new Error('invalid selected credential metadata request');
      }
      url = 'https://apikeys.googleapis.com/v2/keys:lookupKey';
      return {provider, method, url, query: {keyString: body.key_string}};
    }
    if (request.operation === 'project') {
      if (!/^[0-9]{4,30}$/.test(String(body?.project_number || ''))) throw new Error('invalid project number');
      url = 'https://cloudresourcemanager.googleapis.com/v3/projects/' + body.project_number;
    } else if (request.operation === 'billing') {
      if (!/^[a-z][a-z0-9-]{4,62}$/.test(body?.project_id || '')) throw new Error('invalid project identifier');
      url = 'https://cloudbilling.googleapis.com/v1/projects/' + body.project_id + '/billingInfo';
      // Use the verified Gemini project, rather than the OAuth client's project.
      // Caller headers are never forwarded to the authenticated upstream node.
      return {provider, method, url, query, body,
        headers: {'x-goog-user-project': body.project_id}};
    } else throw new Error('unsupported metadata operation');
  } else throw new Error('provider not allowed');
  return {provider, method, url, query, body};
}
if (typeof module !== 'undefined') module.exports = {validateProviderRequest};
