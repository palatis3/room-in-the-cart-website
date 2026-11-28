import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
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
      // A source edit must also update the shipped CSP hash or browsers discard it.
      const csp = await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute('content');
      for (const tag of ['style', 'script']) {
        const code = await page.locator(tag).textContent();
        const hash = createHash('sha256').update(code).digest('base64');
        assert.ok(csp.includes(tag + "-src 'sha256-" + hash + "'"), topic + ' ' + tag + ' hash');
      }
      const article = page.locator('article:visible');
      assert.equal(await article.count(), 1);
      assert.equal(await article.getAttribute('id'), lang);
      assert.equal(await article.locator('h1').textContent(), locale[topic]);
      assert.equal(await page.title(), locale[topic] + ' | Room in the Cart');
      if (topic === 'privacy') {
        const date = article.locator('time');
        const isoDate = await date.getAttribute('datetime');
        assert.match(isoDate, /^\d{4}-\d{2}-\d{2}$/);
        const formatter = new Intl.DateTimeFormat(lang === 'es' ? 'es-MX' : 'en-US', {
          dateStyle: 'long', timeZone: 'UTC'
        });
        assert.equal(await date.textContent(), formatter.format(new Date(isoDate + 'T00:00:00Z')));
        const policyDates = await page.locator('article time').evaluateAll(dates => dates.map(d => d.dateTime));
        assert.deepEqual(policyDates, [isoDate, isoDate]);
      }
      assert.equal(await article.locator('a[href^="mailto:"]').first().getAttribute('href'), 'mailto:hello@roominthecart.com');
      const footer = await article.locator('footer a').evaluateAll(links => links.map(link => [link.textContent, link.getAttribute('href')]));
      assert.deepEqual(footer, [
        [locale[otherTopic], '../' + otherTopic + '/?lang=' + lang + '#' + lang],
        [locale.website, website + locale.home],
        [locale.contactLabel, website + locale.contact]
      ]);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth));
      await page.setViewportSize({ width: 320, height: 812 });
      const narrow = await page.evaluate(() => {
        const root = document.documentElement;
        root.style.fontSize = '200%';
        return { font: getComputedStyle(root).fontSize, viewport: root.clientWidth, content: root.scrollWidth };
      });
      assert.deepEqual(narrow, { font: '32px', viewport: 320, content: 320 }, topic + ' ' + lang + ' at 200%');
      await page.setViewportSize({ width: 375, height: 812 });
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

  // Epic accepts one privacy URL for all guardians. Test that same URL without
  // an app-supplied language parameter, then follow the family's language choice.
  const privacy = new URL('./public/privacy/index.html', import.meta.url);
  for (const [locale, language] of [['en-US', 'en'], ['es-MX', 'es'], ['fr-FR', 'en']]) {
    const context = await browser.newContext({ locale, viewport: { width: 320, height: 812 } });
    try {
      const guardianPage = await context.newPage();
      await guardianPage.goto(privacy.href);
      assert.equal(await guardianPage.locator('html').getAttribute('lang'), language);
      await guardianPage.locator('article:visible a[href="#guardian-' + language + '"]').click();
      const methods = guardianPage.locator('#guardian-' + language);
      assert.equal(await methods.isVisible(), true);
      assert.equal(new URL(guardianPage.url()).hash, '#guardian-' + language);
      const methodText = await methods.innerText();
      for (const processor of ['Stripe', 'Veratad', 'Nubarium']) assert.ok(methodText.includes(processor));
      const other = language === 'es' ? 'en' : 'es';
      await guardianPage.locator('nav a[hreflang="' + other + '"]').click();
      assert.equal(await guardianPage.locator('html').getAttribute('lang'), other);
      await guardianPage.goto(privacy.href + '#guardian-' + other);
      assert.equal(await guardianPage.locator('article:visible').getAttribute('id'), other);
    } finally {
      await context.close();
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
