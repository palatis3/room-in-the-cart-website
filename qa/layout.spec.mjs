import { expect, test } from '@playwright/test';

const pairs = [
  ['/', '/es/'],
  ['/guides/grocery-budget/', '/es/guias/presupuesto-del-super/'],
  ['/guides/pantry-to-dinner/', '/es/guias/de-la-despensa-a-la-cena/'],
  ['/guides/receipt-to-pantry/', '/es/guias/del-ticket-a-la-despensa/'],
  ['/contact/', '/es/contacto/']
];

async function layoutIssues(page) {
  return page.evaluate(viewportWidth => {
    const width = document.documentElement.clientWidth;
    const issues = [];
    if (width !== viewportWidth) issues.push(`Layout viewport ${width} instead of ${viewportWidth}`);
    function checkBounds(element) {
      const rect = element.getBoundingClientRect();
      if (rect.width && (rect.left < -1 || rect.right > width + 1)) {
        issues.push(`${element.tagName}.${element.className} at ${rect.left.toFixed(1)}–${rect.right.toFixed(1)}`);
      }
    }
    if (document.documentElement.scrollWidth > width + 1) {
      issues.push(`Document width ${document.documentElement.scrollWidth} exceeds ${width}`);
    }
    for (const element of document.querySelectorAll(
      '.masthead .brand, .mast-tools a, .mast-tools summary, header nav a, main :is(h1,h2,h3,input,select,button), footer nav'
    )) checkBounds(element);

    for (const heading of document.querySelectorAll('main :is(h1,h2,h3)')) {
      const text = document.createRange();
      text.selectNodeContents(heading);
      for (const rect of text.getClientRects()) {
        if (rect.width && (rect.left < -1 || rect.right > width + 1)) {
          issues.push(`Heading offscreen: ${heading.textContent.trim()}`);
          break;
        }
      }
    }

    // The header can wrap at enlarged sizes. Only simultaneous horizontal and
    // vertical overlap indicates that two groups cover each other's controls.
    const headerGroups = ['.masthead .brand', '.primary-nav', '.mast-tools']
      .map(selector => document.querySelector(selector))
      .filter(element => element?.getClientRects().length);
    for (const [index, first] of headerGroups.entries()) {
      const a = first.getBoundingClientRect();
      for (const second of headerGroups.slice(index + 1)) {
        const b = second.getBoundingClientRect();
        if (Math.min(a.right, b.right) - Math.max(a.left, b.left) > 1 &&
            Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 1) {
          issues.push(`Header groups overlap: ${first.className} and ${second.className}`);
        }
      }
    }
    return issues;
  }, page.viewportSize().width);
}

for (const route of [...pairs.flat(), '/404.html']) {
  test(`page fits at normal and enlarged text sizes: ${route}`, async ({ page }) => {
    for (const [scale, widths] of [
      ['100%', [320, 360, 371, 375, 390, 430, 620, 621, 740, 741, 760, 761, 768, 940, 941, 1024, 1440]],
      ['200%', [320, 375, 390, 430, 768, 1024]]
    ]) {
      for (const width of widths) {
        await page.setViewportSize({ width, height: 900 });
        await page.goto(route);
        await page.evaluate(async value => {
          document.documentElement.style.fontSize = value;
          await document.fonts.ready;
        }, scale);
        expect(await layoutIssues(page), `${route} at ${width}px / ${scale}`).toEqual([]);
      }
    }
  });
}

test('all English and Spanish language controls reach the corresponding page', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  for (const [english, spanish] of pairs) {
    await page.goto(english);
    await page.locator('header a[hreflang="es-MX"]').click();
    await expect(page).toHaveURL(new URL(spanish, page.url()).href);
    await expect(page.locator('html')).toHaveAttribute('lang', 'es-MX');
    await page.locator('header a[hreflang="en-US"]').click();
    await expect(page).toHaveURL(new URL(english, page.url()).href);
    await expect(page.locator('html')).toHaveAttribute('lang', 'en-US');
  }
});

test.describe('touch navigation', () => {
  test.use({ hasTouch: true, isMobile: true });

  async function expectFingerTargets(page, selector) {
    const targets = page.locator(selector).filter({ visible: true });
    expect(await targets.count(), selector).toBeGreaterThan(0);
    for (const target of await targets.all()) {
      const bounds = await target.boundingBox();
      const label = await target.getAttribute('aria-label') || await target.textContent();
      expect(bounds.width, `${label} width`).toBeGreaterThanOrEqual(43.5);
      expect(bounds.height, `${label} height`).toBeGreaterThanOrEqual(43.5);
    }
  }

  for (const [home, budget] of [['/', pairs[1][0]], ['/es/', pairs[1][1]]]) {
    test(`menu, tour, calculator and links remain usable: ${home}`, async ({ page }) => {
      for (const [width, height] of [[320, 568], [667, 375], [844, 390]]) {
        await page.setViewportSize({ width, height });
        await page.goto(home);
        await page.evaluate(() => document.fonts.ready);
        expect(await layoutIssues(page), `${home} at ${width}×${height}`).toEqual([]);
        await expectFingerTargets(page, 'header .brand, header .language, footer a, .hero-actions a, .tour-tab, .faqs summary');
        const menu = page.locator('header .mobile-menu');
        if (await menu.isVisible()) {
          await expectFingerTargets(page, 'header summary');
          await menu.locator('summary').tap();
          await expectFingerTargets(page, 'header details[open] nav a');
          await menu.locator('summary').tap();
        }
        const dinner = page.locator('#tab-dinner');
        await dinner.tap();
        const opener = page.getByRole('tabpanel').locator('.screen-link');
        await opener.tap();
        await expectFingerTargets(page, 'dialog[open] button');
        await page.locator('dialog[open] button').tap();
        await expect(opener).toBeFocused();
        await page.goto(budget);
        await expectFingerTargets(page, '.journal-crumb a, .journal-jump, .pack-calculator input, .pack-calculator select, .pack-calculator button');
      }
    });
  }
});
