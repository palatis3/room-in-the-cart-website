import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import worker from '../hosting/_worker.js';

const origin = 'https://roominthecart.com';
const robots = 'noindex, follow';

test('public help shortcuts reach the official localized documents', async () => {
  const help = 'https://help.roominthecart.com';
  for (const [path, destination] of [
    ['/privacy', '/privacy'],
    ['/support/', '/support'],
    ['/privacy?lang=es', '/privacy?lang=es#es'],
    ['/support?lang=es-MX', '/support?lang=es#es'],
    ['/privacy/?lang=en-US', '/privacy?lang=en'],
    ['/es/privacidad/', '/privacy?lang=es#es'],
    ['/es/soporte', '/support?lang=es#es'],
    ['/support?email=private&lang=es&next=https://example.org', '/support?lang=es#es'],
  ]) {
    const response = await worker.fetch(new Request(origin + path), {});
    assert.equal(response.status, 308, path);
    assert.equal(response.headers.get('Location'), help + destination, path);
    assert.equal(response.headers.get('X-Robots-Tag'), robots, path);
  }
});

test('static fallback headers cover every path while indexing is paused', async () => {
  const rules = await readFile(new URL('../hosting/_headers', import.meta.url), 'utf8');
  assert.match(rules, /^\/\*\r?\n[ \t]+X-Robots-Tag: noindex, follow\s*$/im);
});

for (const [path, status] of [['/es/', 200], ['/assets/site.css', 200], ['/missing', 404]]) {
  test(`asset binding preserves ${status} and sends noindex for ${path}`, async () => {
    const request = new Request(origin + path);
    const ASSETS = { fetch: async (received) => {
      assert.equal(received, request);
      return new Response('asset', { status, headers: { 'X-Test': 'preserved' } });
    } };
    const response = await worker.fetch(request, { ASSETS });
    assert.equal(response.status, status);
    assert.equal(response.headers.get('X-Robots-Tag'), robots);
    assert.equal(response.headers.get('X-Test'), 'preserved');
    assert.equal(await response.text(), 'asset');
  });
}

for (const host of ['http://roominthecart.com', 'https://www.roominthecart.com']) {
  test(`${host} redirects to the canonical host with the path and query`, async () => {
    const path = '/es/guias/presupuesto-del-super/?lang=es';
    const response = await worker.fetch(new Request(host + path), {});
    assert.equal(response.status, 308);
    assert.equal(response.headers.get('Location'), origin + path);
    assert.equal(response.headers.get('X-Robots-Tag'), robots);
  });
}
