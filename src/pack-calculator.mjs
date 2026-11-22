import { copyFile, mkdir } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { comparePacks, copy, example, formatComparison, units } from './assets/pack-calculator.mjs';

export function packCalculator(locale) {
  const content = copy[locale];
  if (!content) throw new Error('Unsupported calculator locale: ' + locale);
  const output = formatComparison(comparePacks(example), locale, 'piece');
  const field = (key, label) => `<div class="pack-field">
    <label for="pack-${key}">${label}</label>
    <input type="text" inputmode="decimal" id="pack-${key}" value="${example[key]}" required aria-describedby="pack-${key}-error">
    <span id="pack-${key}-error" class="pack-error"></span>
  </div>`;
  const options = units.map((unit, index) => `<option value="${unit}">${content.units[index]}</option>`).join('');
  const offers = ['A', 'B'];
  return `<section class="pack-calculator" data-locale="${locale}" id="pack-calculator" aria-labelledby="pack-heading">
    <h2 id="pack-heading">${content.heading}</h2>
    <p data-example>${content.example}</p>
    <form autocomplete="off" novalidate hidden>
      <p>${content.instruction}</p>
      <div class="pack-need">
        ${field('need', content.need)}
        <div class="pack-field"><label for="pack-unit">${content.unit}</label><select id="pack-unit">${options}</select></div>
      </div>
      <div class="pack-options">
        ${offers.map(id => `<fieldset><legend>${content.pack} ${id}</legend>
          ${field('size' + id, content.size)}
          ${field('price' + id, content.price)}
        </fieldset>`).join('')}
      </div>
      <button type="submit">${content.compare}</button>
    </form>
    <p data-status role="status" aria-atomic="true">${output.summary}</p>
    <table>
      <caption>${content.caption}</caption>
      <thead><tr><th scope="col">${content.pack}</th><th scope="col">${content.packs}</th><th scope="col">${content.cost}</th><th scope="col">${content.left}</th></tr></thead>
      <tbody>${offers.map(id => `<tr data-offer="${id}"><th scope="row">${id}</th>${output[id].map(value => `<td>${value}</td>`).join('')}</tr>`).join('')}</tbody>
    </table>
    <script type="module" src="/assets/pack-calculator.mjs"></script>
  </section>`;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const html = packCalculator(process.argv[2]);
  const destination = new URL('../dist/assets/', import.meta.url);
  await mkdir(destination, { recursive: true });
  for (const file of ['pack-calculator.mjs', 'pack-calculator.css']) {
    await copyFile(new URL('./assets/' + file, import.meta.url), new URL(file, destination));
  }
  process.stdout.write(html);
}
