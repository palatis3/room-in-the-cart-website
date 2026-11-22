"""Build the localized field guides along with their canonical URL inventory."""
from html import escape
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

from build import BRAND, ORIGIN, footer, header, home_path, local, page_head
from guide_copy import GUIDES

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'


def emphasis(value):
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', escape(value))


def structured_data(page, lang, social):
    url = ORIGIN + page['path']
    home = local(lang, 'Home', 'Inicio')
    return {
        '@context': 'https://schema.org',
        '@graph': [
            {'@type': 'WebPage', '@id': url, 'url': url, 'name': page['h1'],
             'inLanguage': lang, 'description': page['description'], 'image': ORIGIN + social,
             'breadcrumb': {'@id': url + '#breadcrumb'}, 'isPartOf': {'@type': 'WebSite', '@id': ORIGIN + '/#website', 'name': BRAND, 'url': ORIGIN + '/'}},
            {'@type': 'BreadcrumbList', '@id': url + '#breadcrumb', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': home, 'item': ORIGIN + home_path(lang)},
                {'@type': 'ListItem', 'position': 2, 'name': page['crumb'], 'item': url},
            ]},
        ],
    }


def guide_case(key, page, lang):
    if key == 'budget':
        return subprocess.run(['node', str(ROOT / 'src/pack-calculator.mjs'), lang],
                              check=True, capture_output=True, text=True).stdout
    headings = ''.join(f'<th scope="col">{escape(h)}</th>' for h in page['headings'])
    rows = []
    for item, amount, decision in page['rows']:
        rows.append(f'<tr><th scope="row">{escape(item)}</th><td>{escape(amount)}</td><td>{escape(decision)}</td></tr>')
    return f'''<section id="example" class="journal-example" aria-labelledby="case-heading">
<h2 id="case-heading">{escape(page['example_title'])}</h2><p>{escape(page['example_intro'])}</p>
<table aria-labelledby="case-heading"><thead><tr>{headings}</tr></thead><tbody>{''.join(rows)}</tbody></table>
<p>{escape(page['example_note'])}</p></section>'''


def related_cards(key, lang):
    cards = []
    for other_key, translations in GUIDES.items():
        if other_key == key:
            continue
        page = translations[lang]
        cards.append(f'''<a class="journal-related-link" href="{page['path']}">
<img src="/assets/guide-{other_key}-480.webp" width="480" height="300" loading="lazy" decoding="async" alt="">
<span>{escape(page['h1'])}</span></a>''')
    return f'''<section class="journal-related" aria-labelledby="more-guides">
<h2 id="more-guides">{local(lang, 'More grocery guides', 'Más guías para tus compras')}</h2>
<div class="journal-related-grid">{''.join(cards)}</div></section>'''


def render(key, lang):
    page = GUIDES[key][lang]
    other = 'en-US' if lang == 'es-MX' else 'es-MX'
    alternate = GUIDES[key][other]['path']
    path = page['path']
    social = f'/assets/share-{key}-{lang}.jpg'
    head = page_head(lang, path, alternate, page['title'], page['description'],
                     structured_data(page, lang, social), social_image=social, social_alt=page['h1'])
    styles = '<link rel="stylesheet" href="/assets/guides.css">'
    if key == 'budget':
        styles += '\n<link rel="stylesheet" href="/assets/pack-calculator.css">'
    head = head.replace('</head>', styles + '\n</head>')
    home = local(lang, 'Home', 'Inicio')
    crumb_label = local(lang, 'Breadcrumb', 'Ruta de navegación')
    steps = ''.join(f'<li><h3>{escape(title)}</h3><p>{emphasis(content)}</p></li>' for title, content in page['steps'])
    screen = f"/assets/screens/{lang}/{page['screen']}"
    return f'''{head}
<body>{header(lang, path, alternate)}
<main id="main" tabindex="-1" class="journal-main journal-{key}"><article>
<div class="wrap journal-wrap">
<nav class="journal-crumb" aria-label="{crumb_label}"><ol><li><a href="{home_path(lang)}">{home}</a></li>
<li><span class="journal-slash" aria-hidden="true">/</span><span aria-current="page">{escape(page['crumb'])}</span></li></ol></nav>
<div class="journal-opening"><div class="journal-intro"><h1>{escape(page['h1'])}</h1>
<p>{escape(page['intro'])}</p><a class="journal-jump" href="#{page['jump_id']}">{escape(page['jump'])}</a></div>
<picture class="journal-cover-picture"><source media="(max-width:620px)" srcset="/assets/guide-{key}-480.webp 480w, /assets/guide-{key}-720.webp 720w" sizes="90vw"><img class="journal-cover" src="/assets/guide-{key}.webp" srcset="/assets/guide-{key}-480.webp 480w, /assets/guide-{key}.webp 960w" sizes="(max-width: 740px) 95vw, 50vw" width="960" height="600" fetchpriority="high" alt="{escape(page['photo_alt'], quote=True)}"></picture></div>
<section class="journal-workflow" aria-labelledby="workflow-title"><div><h2 id="workflow-title">{escape(page['steps_title'])}</h2>
<ol class="journal-steps">{steps}</ol></div>
<figure class="journal-screen"><div class="journal-device"><img src="{screen}-400.webp" srcset="{screen}-400.webp 400w, {screen}-760.webp 760w" sizes="(max-width: 740px) 210px, 230px" width="400" height="869" loading="lazy" decoding="async" alt="{escape(page['screen_alt'], quote=True)}"></div>
<figcaption>{escape(page['screen_caption'])}</figcaption></figure></section>
{guide_case(key, page, lang)}
{related_cards(key, lang)}
</div></article></main>{footer(lang)}</body></html>'''


def build_guides():
    (DIST / 'assets').mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / 'src/assets/guides.css', DIST / 'assets/guides.css')
    urls = ['/', '/es/']
    for key, translations in GUIDES.items():
        for lang, page in translations.items():
            route = page['path']
            dest = DIST / route.strip('/') / 'index.html'
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(render(key, lang), encoding='utf-8')
            urls.append(route)
    # Keep pages crawlable so crawlers can read the explicit noindex directives.
    (DIST / 'robots.txt').write_text('User-agent: *\nAllow: /\n', encoding='utf-8')
    urlset = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for path in urls:
        ET.SubElement(ET.SubElement(urlset, 'url'), 'loc').text = ORIGIN + path
    ET.indent(urlset, space='  ')
    ET.ElementTree(urlset).write(DIST / 'sitemap.xml', encoding='utf-8', xml_declaration=True)


if __name__ == '__main__':
    build_guides()
