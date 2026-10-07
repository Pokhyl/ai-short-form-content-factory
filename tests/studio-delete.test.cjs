const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../factory_v3/web/app.js'), 'utf8');
const id = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
async function fixture({confirm = true, reject = false, detail = {}, detailFor = null, extraRows = []} = {}) {
  const elements = new Map(), storage = new Map();
  function element() { return {children: [], dataset: {}, hidden: false, disabled: false,
    append(...items) {this.children.push(...items);}, replaceChildren(...items) {this.children = items;},
    setAttribute(key, value) {this[key] = value;}, getAttribute(key) {return this[key];},
    removeAttribute(key) {delete this[key];}, pause() {}, load() {}}; }
  const get = key => {if (!elements.has(key)) elements.set(key, element()); return elements.get(key);};
  const calls = [], replacements = [];
  let deleted = false;
  const history = {replaceState(...args) {replacements.push(args);context.location.href = args[2].href; context.location.search = args[2].search;}};
  const context = {document: {getElementById: get, createElement: element, createTextNode: text => ({textContent: text})},
    location: {href: `https://example.test/factory-v3/?request=${id}`, search: `?request=${id}`},
    history, URL, URLSearchParams, confirm: () => confirm, clearTimeout() {}, setTimeout() {},
    localStorage: {getItem: key => storage.get(key), setItem: (key, value) => storage.set(key, value), removeItem: key => storage.delete(key)},
    fetch: async (url, options) => {
      calls.push([url, options.method]);
      let body, status = 200;
      if (url.endsWith('/delete')) {if (reject) {status = 409; body = {error: 'deletion_refused'};} else {deleted = true; body = {state: 'deleted'};}}
      else if (url.endsWith('/session')) body = {};
      else if (url.endsWith('/requests')) body = deleted ? [] : [{id, status: 'qa_pass', request: {topic: 'Test', language: 'en', seconds: 30}}, ...extraRows];
      else body = detailFor ? await detailFor(url) : {request: {topic: 'Test'}, status: 'qa_pass', machine_pass: true, ...detail};
      return {ok: status === 200, status, json: async () => body};
    }};
  context.window = context;
  vm.runInNewContext(source, context);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(get('result').hidden, false);
  return {get, calls, replacements, context, history, storage};
}
test('classic script preserves native history; successful delete clears selection and refreshes cards', async () => {
  const f = await fixture();
  assert.equal(f.context.history, f.history);
  await f.get('delete-video').onclick();
  assert.equal(f.calls.filter(([url]) => url.endsWith('/delete')).length, 1);
  assert.equal(f.calls.filter(([url]) => url.endsWith('/requests')).length, 2);
  assert.equal(f.get('history').children.some(item => item.dataset.requestId === id), false);
  assert.equal(f.get('result').hidden, true);
  assert.equal(f.storage.has('factoryV3Last'), false);
  assert.equal(f.get('video').getAttribute('src'), undefined);
  assert.equal(f.replacements[0][2].searchParams.has('request'), false);
  assert.equal(f.get('message').textContent, 'Видео и связанные файлы удалены с сервера.');
});
test('cancel leaves video and card intact without a server deletion', async () => {
  const f = await fixture({confirm: false}); await f.get('delete-video').onclick();
  assert.equal(f.calls.some(([url]) => url.endsWith('/delete')), false);
  assert.equal(f.get('result').hidden, false);
  assert.equal(f.get('history').children[0].dataset.requestId, id);
});
test('server refusal retains card and reports failure without claiming deletion', async () => {
  const f = await fixture({reject: true}); await f.get('delete-video').onclick();
  assert.equal(f.get('result').hidden, false);
  assert.equal(f.get('history').children[0].dataset.requestId, id);
  assert.equal(f.get('message').textContent, 'deletion_refused');
  assert.equal(f.get('delete-video').disabled, false);
  assert.equal(f.replacements.length, 0);
});

test('terminal failure shows a saved failure notice instead of promising an upcoming video', async () => {
  const f = await fixture({detail: {status: 'failed', machine_pass: false, error_code: 'ModelSchemaError', source_revision: 'old-version'}});
  assert.equal(f.get('result-content').hidden, true);
  assert.equal(f.get('failure-notice').hidden, false);
  assert.match(f.get('failure-notice').textContent, /Готового MP4 нет/);
  assert.match(f.get('failure-notice').textContent, /не изменяют/);
  assert.equal(f.get('script').textContent, 'Текст не подготовлен.');
  assert.match(f.get('identity').textContent, /old-version.*ModelSchemaError/);
  assert.equal(f.get('download').hidden, true);
});
test('active preparation keeps upcoming result visible and clears terminal notice', async () => {
  const f = await fixture({detail: {status: 'preparing', machine_pass: false}});
  assert.equal(f.get('result-content').hidden, false);
  assert.equal(f.get('failure-notice').hidden, true);
  assert.equal(f.get('failure-notice').textContent, '');
  assert.match(f.get('script').textContent, /появится/);
});

test('switching to a failed duplicate title updates the share URL and never leaves old video controls active', async () => {
  const failed = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
  let finish;
  const f = await fixture({extraRows: [{id: failed, status: 'failed', request: {topic: 'Test', language: 'en', seconds: 30}}],
    detailFor: url => url.endsWith(failed) ? new Promise(resolve => {finish = resolve;}) : {request: {topic: 'Test'}, status: 'qa_pass', machine_pass: true}});
  const loading = f.get('history').children[1].onclick();
  assert.equal(new URL(f.context.location.href).searchParams.get('request'), failed);
  assert.equal(f.get('result').hidden, true);
  assert.equal(f.get('delete-video').disabled, true);
  finish({request: {topic: 'Test'}, status: 'failed', machine_pass: false, error_code: 'MaterialUnavailable'});
  await loading;
  assert.equal(f.get('failure-notice').hidden, false);
  assert.equal(f.get('download').hidden, true);
  assert.match(f.get('identity').textContent, new RegExp(failed));
  await f.get('history').children[0].onclick();
  assert.equal(new URL(f.context.location.href).searchParams.get('request'), id);
  assert.equal(f.get('download').hidden, false);
  assert.equal(f.get('download').href, '/factory-v3/video/' + id + '?download=1');
});
