import assert from 'node:assert/strict';
import test from 'node:test';
import { comparePacks, example, formatComparison } from '../src/assets/pack-calculator.mjs';
import { packCalculator } from '../src/pack-calculator.mjs';

test('twelve tortillas take two whole packs at each price', () => {
  assert.deepEqual(comparePacks(example), {
    A: { packs: 2n, cents: 640n, leftover: 4_000_000n },
    B: { packs: 2n, cents: 540n, leftover: 0n }
  });
});

test('fractional quantities and prices stay exact at the whole-pack boundary', () => {
  const values = { need: '0.30', sizeA: '.1', priceA: '0.10', sizeB: '.300001', priceB: '0.30' };
  const exact = comparePacks(values);
  assert.deepEqual(exact.A, { packs: 3n, cents: 30n, leftover: 0n });
  assert.deepEqual(exact.B, { packs: 1n, cents: 30n, leftover: 1n });
  assert.deepEqual(comparePacks({ ...values, need: '0.300001' }).A, { packs: 4n, cents: 40n, leftover: 99_999n });
});

test('a free pack and zero remaining need are valid', () => {
  assert.equal(comparePacks({ ...example, priceA: '0' }).A.cents, 0n);
  const zero = comparePacks({ ...example, need: '0' });
  assert.deepEqual(zero.A, { packs: 0n, cents: 0n, leftover: 0n });
  assert.deepEqual(zero.A, zero.B);
});

test('large integer cents are never converted to floating point for display', () => {
  const result = comparePacks({ ...example, need: '1', sizeA: '1', priceA: '9007199254740993.01' });
  assert.equal(formatComparison(result, 'en-US', 'g').A[1], '$9,007,199,254,740,993.01');
});

test('individual field errors replace the entire comparison', () => {
  assert.deepEqual(comparePacks({ ...example, need: '-1', sizeA: '0', priceA: '', sizeB: '0.0000001', priceB: '2.701' }), {
    errors: { need: 'needError', sizeA: 'sizeError', priceA: 'priceError', sizeB: 'sizeError', priceB: 'priceError' }
  });
  for (const invalid of ['Infinity', 'NaN', '0x10', '2e2', '1,200', '$ 2.70', '2/3']) {
    assert.deepEqual(comparePacks({ ...example, need: invalid }), { errors: { need: 'needError' } });
  }
  assert.deepEqual(comparePacks({ ...example, need: '1'.repeat(25) }), { errors: { need: 'lengthError' } });
});

for (const [locale, expected] of [
  ['en-US', { summary: /Pack B costs \$1\.00 less/, tie: /Both options cost \$0\.30/, piece: '4 pieces', heading: 'Compare your pack sizes' }],
  ['es-MX', { summary: /El paquete B cuesta USD\s1\.00 menos/, tie: /Ambas opciones cuestan USD\s0\.30/, piece: '4 piezas', heading: 'Compara dos tamaños de paquete' }]
]) {
  test(locale + ' shows localized winners, ties, exact leftovers and a static worked example', () => {
    const output = formatComparison(comparePacks(example), locale, 'piece');
    assert.match(output.summary, expected.summary);
    assert.equal(output.A[2], expected.piece);
    const tie = comparePacks({ ...example, need: '.3', sizeA: '.1', priceA: '.1', sizeB: '.300001', priceB: '.3' });
    const formatted = formatComparison(tie, locale, 'kg');
    assert.match(formatted.summary, expected.tie);
    assert.equal(formatted.B[2], '0.000001 kg');
    const html = packCalculator(locale);
    assert.ok(html.includes(expected.heading));
    assert.ok(html.includes('12 tortillas'));
    assert.match(html, expected.summary);
    assert.ok(html.includes('<td>' + expected.piece + '</td>'));
    assert.match(html, /<form[^>]*hidden>/);
    assert.ok(html.includes('<table>'));
  });
}
