export const example = { need: '12', sizeA: '8', priceA: '3.20', sizeB: '6', priceB: '2.70' };

export const copy = {
  'en-US': {
    heading: 'Compare your pack sizes',
    example: 'You need 12 tortillas. In this example, a pack of 8 costs $3.20 and a pack of 6 costs $2.70. All prices are in US dollars.',
    instruction: 'Start with 12 tortillas or enter your own amounts. Use the same unit for the amount you need and both pack sizes.',
    need: 'Amount you still need', unit: 'Unit', units: ['Pieces', 'Grams', 'Kilograms', 'Ounces by weight', 'Pounds', 'Milliliters', 'Liters'],
    size: 'Usable amount per pack', price: 'Price per pack (USD)', compare: 'Compare packs', pack: 'Pack',
    packs: 'Packs to buy', cost: 'Cost (USD)', left: 'Left over', caption: 'Whole packs for this item',
    pending: 'Compare again to see your updated totals.', invalid: 'Check the marked fields to compare the packs.',
    needError: 'Enter 0 or more, with up to 6 decimal places. Use a period for decimals.',
    sizeError: 'Enter more than 0, with up to 6 decimal places. Use a period for decimals.',
    priceError: 'Enter a price of 0 or more, with up to 2 decimal places, such as 2.70.',
    lengthError: 'Enter a number with at most 24 characters.',
    piece: ['piece', 'pieces'],
    cheaper: (pack, saving) => `Pack ${pack} costs ${saving} less.`,
    tie: (cost) => `Both options cost ${cost}.`
  },
  'es-MX': {
    heading: 'Compara dos tamaños de paquete',
    example: 'Necesitas 12 tortillas. En este ejemplo, el paquete de 8 cuesta 3.20 dólares y el de 6 cuesta 2.70 dólares. Los precios están en dólares estadounidenses.',
    instruction: 'Empieza con 12 tortillas o ingresa tus propias cantidades. Usa la misma unidad para la cantidad que necesitas y el contenido de ambos paquetes.',
    need: 'Cantidad que te falta', unit: 'Unidad', units: ['Piezas', 'Gramos', 'Kilogramos', 'Onzas de peso', 'Libras', 'Mililitros', 'Litros'],
    size: 'Cantidad aprovechable por paquete', price: 'Precio por paquete (USD)', compare: 'Comparar paquetes', pack: 'Paquete',
    packs: 'Paquetes a comprar', cost: 'Costo (USD)', left: 'Sobrante', caption: 'Paquetes completos para este producto',
    pending: 'Vuelve a comparar para ver los nuevos totales.', invalid: 'Revisa los campos señalados para comparar los paquetes.',
    needError: 'Ingresa 0 o más, con hasta 6 decimales. Usa un punto para los decimales.',
    sizeError: 'Ingresa una cantidad mayor que 0, con hasta 6 decimales. Usa un punto para los decimales.',
    priceError: 'Ingresa un precio de 0 o más, con hasta 2 decimales, por ejemplo 2.70.',
    lengthError: 'Ingresa un número de hasta 24 caracteres.',
    piece: ['pieza', 'piezas'],
    cheaper: (pack, saving) => `El paquete ${pack} cuesta ${saving} menos.`,
    tie: (cost) => `Ambas opciones cuestan ${cost}.`
  }
};

export const units = ['piece', 'g', 'kg', 'oz', 'lb', 'mL', 'L'];
const quantityScale = 1_000_000n;

function fixedDecimal(text, places) {
  const value = text.trim();
  if (!/^(?:\d+(?:\.\d*)?|\.\d+)$/.test(value)) return null;
  const [whole, decimal = ''] = value.split('.');
  if (decimal.length > places) return null;
  return BigInt(whole + decimal.padEnd(places, '0'));
}

export function comparePacks(values) {
  const errors = {};
  const amounts = {};
  for (const key of Object.keys(example)) {
    const text = String(values[key] ?? '').trim();
    if (text.length > 24) {
      errors[key] = 'lengthError';
      continue;
    }
    const price = key.startsWith('price');
    const amount = fixedDecimal(text, price ? 2 : 6);
    if (amount === null || (key.startsWith('size') && amount === 0n)) {
      errors[key] = price ? 'priceError' : key === 'need' ? 'needError' : 'sizeError';
    } else {
      amounts[key] = amount;
    }
  }
  if (Object.keys(errors).length) return { errors };

  function offer(size, price) {
    const packs = (amounts.need + size - 1n) / size;
    return { packs, cents: packs * price, leftover: packs * size - amounts.need };
  }
  return { A: offer(amounts.sizeA, amounts.priceA), B: offer(amounts.sizeB, amounts.priceB) };
}

export function formatComparison(result, locale, unit) {
  const content = copy[locale];
  const number = new Intl.NumberFormat(locale);
  const currency = new Intl.NumberFormat(locale, { style: 'currency', currency: 'USD' });
  const money = (cents) => currency.formatToParts(cents / 100n).map(({ type, value }) =>
    type === 'fraction' ? (cents % 100n).toString().padStart(2, '0') : value).join('');
  const offer = ({ packs, cents, leftover }) => {
    const fraction = (leftover % quantityScale).toString().padStart(6, '0').replace(/0+$/, '');
    const amount = number.format(leftover / quantityScale) + (fraction ? '.' + fraction : '');
    const label = unit === 'piece' ? content.piece[leftover === quantityScale ? 0 : 1] : unit;
    return [number.format(packs), money(cents), amount + ' ' + label];
  };
  const difference = result.A.cents - result.B.cents;
  const summary = difference === 0n ? content.tie(money(result.A.cents))
    : difference < 0n ? content.cheaper('A', money(-difference)) : content.cheaper('B', money(difference));
  return { summary, A: offer(result.A), B: offer(result.B) };
}

export function enhanceCalculator(section) {
  const locale = section.dataset.locale;
  const content = copy[locale];
  const form = section.querySelector('form');
  const status = section.querySelector('[data-status]');
  const table = section.querySelector('table');
  const fields = Object.fromEntries(Object.keys(example).map(key => [key, form.querySelector('#pack-' + key)]));
  const unit = form.querySelector('select');

  function edit({ target }) {
    if (target.hasAttribute('aria-invalid')) {
      target.removeAttribute('aria-invalid');
      section.querySelector('#' + target.id + '-error').textContent = '';
    }
    table.hidden = true;
    if (status.textContent !== content.pending) status.textContent = content.pending;
  }
  function render(focusError) {
    const entries = Object.fromEntries(Object.entries(fields).map(([key, input]) => [key, input.value]));
    const result = comparePacks(entries);
    for (const [key, input] of Object.entries(fields)) {
      const message = result.errors?.[key];
      if (message) input.setAttribute('aria-invalid', 'true');
      else input.removeAttribute('aria-invalid');
      section.querySelector('#' + input.id + '-error').textContent = message ? content[message] : '';
    }
    table.hidden = Boolean(result.errors);
    if (result.errors) {
      status.textContent = content.invalid;
      if (focusError) fields[Object.keys(result.errors)[0]].focus();
      return;
    }
    const output = formatComparison(result, locale, unit.value);
    for (const id of ['A', 'B']) {
      section.querySelectorAll('[data-offer="' + id + '"] td').forEach((cell, index) => { cell.textContent = output[id][index]; });
    }
    status.textContent = output.summary;
  }
  form.addEventListener('input', edit);
  form.addEventListener('submit', event => {
    event.preventDefault();
    render(true);
  });
  render(false);
  section.querySelector('[data-example]').hidden = true;
  form.hidden = false;
}

if (typeof document !== 'undefined') {
  document.querySelectorAll('.pack-calculator').forEach(enhanceCalculator);
}
