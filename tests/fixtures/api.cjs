const {PexelsAPI} = require('../../engine-overlay/Pexels.js');
const fixture = require('./scenes.cjs');
function api() {
  return new PexelsAPI('', {fetchJson: async input => {
    const url = new URL(input), p = url.searchParams;
    const lang = url.hostname.split('.')[0], index = fixture.langs.indexOf(lang);
    if (p.get('action') === 'parse') return {parse: {revid: 123, wikitext: {'*': fixture.source(lang)}}};
    if (p.get('generator') === 'search') return {query: {pages: {}}};
    const title = p.get('titles');
    const entity = fixture.entities.find(e => [lang === 'en' ? e[0] : e[2][index], e[2][index]].some(t => t.toLowerCase() === String(title).toLowerCase()));
    if (!entity) return {query: {pages: {'-1': {missing: ''}}}};
    return {query: {pages: {1: {pageid: Number(entity[1].slice(1)), title: lang === 'en' ? entity[0] : entity[2][index], pageprops: {wikibase_item: entity[1]}, langlinks: [{lang: 'en', '*': entity[0]}], pageimage: `${entity[0]}.jpg`, thumbnail: {source: `https://upload.wikimedia.org/wikipedia/commons/a/ab/${encodeURIComponent(entity[0])}.jpg`, width: 1080, height: 800}}}}};
  }});
}
module.exports = {api};
