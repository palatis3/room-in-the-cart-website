import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { chromium } from '@playwright/test';

const live = process.argv.includes('--live');
const helpHosts = ['help.roominthecart.com', 'room-in-the-cart-help.vercel.app'];
const website = 'https://roominthecart.com';
const topics = ['privacy', 'support'];
const locales = {
  en: { home: '/', contact: '/contact/', privacy: 'Privacy policy', support: 'Support', website: 'Room in the Cart website', contactLabel: 'Contact us' },
  es: { home: '/es/', contact: '/es/contacto/', privacy: 'Política de privacidad', support: 'Soporte', website: 'Sitio web de Room in the Cart', contactLabel: 'Contacto' }
};

const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_BINARY });
try {
  const page = await browser.newPage({ viewport: { width: 375, height: 812 } });
  for (const topic of topics) {
    const source = new URL('./public/' + topic + '/index.html', import.meta.url);
    const otherTopic = topic === 'privacy' ? 'support' : 'privacy';
    for (const lang of Object.keys(locales)) {
      const locale = locales[lang];
      await page.goto(source.href + '?lang=' + lang);
      assert.equal(await page.locator('html').getAttribute('lang'), lang);
      const article = page.locator('article:visible');
      assert.equal(await article.count(), 1);
      assert.equal(await article.getAttribute('id'), lang);
      assert.equal(await article.locator('h1').textContent(), locale[topic]);
      assert.equal(await page.title(), locale[topic] + ' | Room in the Cart');
      assert.equal(await article.locator('a[href^="mailto:"]').first().getAttribute('href'), 'mailto:hello@roominthecart.com');
      const footer = await article.locator('footer a').evaluateAll(links => links.map(link => [link.textContent, link.getAttribute('href')]));
      assert.deepEqual(footer, [
        [locale[otherTopic], '../' + otherTopic + '/?lang=' + lang + '#' + lang],
        [locale.website, website + locale.home],
        [locale.contactLabel, website + locale.contact]
      ]);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth));
      const alternate = lang === 'es' ? 'en' : 'es';
      await page.locator('nav a[hreflang="' + alternate + '"]').click();
      assert.equal(await page.locator('article:visible').getAttribute('id'), alternate);
    }
    if (!live) continue;

    const bytes = await readFile(source);
    for (const host of helpHosts) {
      for (const suffix of ['', '/', '?lang=en', '?lang=es', '/?lang=es']) {
        const url = 'https://' + host + '/' + topic + suffix;
        const response = await fetch(url, { redirect: 'manual' });
        assert.equal(response.status, 200, url);
        assert.match(response.headers.get('content-type') ?? '', /text\/html/, url);
        assert.match(response.headers.get('cache-control') ?? '', /must-revalidate/, url);
        assert.match(response.headers.get('x-robots-tag') ?? '', /\bnoindex\b/i, url);
        assert.deepEqual(Buffer.from(await response.arrayBuffer()), bytes, url);
      }
    }
  }

  if (live) {
    const help = 'https://help.roominthecart.com';
    for (const [path, destination] of [
      ['/privacy', '/privacy'],
      ['/support', '/support'],
      ['/privacy?lang=es', '/privacy?lang=es#es'],
      ['/support?lang=es', '/support?lang=es#es'],
      ['/es/privacidad/', '/privacy?lang=es#es'],
      ['/es/soporte/', '/support?lang=es#es']
    ]) {
      const url = website + path;
      const response = await fetch(url, { redirect: 'manual' });
      assert.equal(response.status, 308, url);
      assert.equal(response.headers.get('location'), help + destination, url);
      assert.match(response.headers.get('x-robots-tag') ?? '', /\bnoindex\b/i, url);
      await response.body?.cancel();
    }
    for (const host of helpHosts) {
      for (const path of ['/', '/terms', '/terms/', '/unknown-page']) {
        const url = 'https://' + host + path;
        const response = await fetch(url, { redirect: 'manual' });
        assert.equal(response.status, 404, url);
        await response.body.cancel();
      }
    }
    for (const [lang, locale] of Object.entries(locales)) {
      for (const path of [locale.home, locale.contact]) {
        const response = await page.goto(website + path);
        assert.equal(response.status(), 200, path);
        assert.equal(page.url(), website + path);
        assert.equal((await page.locator('html').getAttribute('lang')).split('-')[0], lang);
      }
    }
  }
} finally {
  await browser.close();
}
console.log(live ? 'Help pages, both public hosts and website destinations verified.' : 'Bilingual help pages and navigation verified.');
