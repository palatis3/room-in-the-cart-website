"""Check the canonical page map, crawl directives, page graph and bilingual metadata. No external requests."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
ORIGIN = 'https://roominthecart.com'


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.lang, self.title, self.part = '', '', ''
        self.links, self.anchors, self.images, self.jsonld = [], [], [], []
        self.identifiers, self.h1, self.meta = [], 0, {}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a: self.identifiers.append(a['id'])
        if tag == 'html': self.lang = a['lang']
        if tag == 'link': self.links.append(a)
        if tag == 'a' and 'href' in a: self.anchors.append(a['href'])
        if tag == 'img': self.images.append(a)
        if tag == 'h1': self.h1 += 1
        if tag == 'meta': self.meta[a.get('name', a.get('property'))] = a.get('content')
        if tag == 'title': self.part = 'title'
        if tag == 'script' and a.get('type') == 'application/ld+json': self.part = 'json'

    def handle_endtag(self, tag):
        if tag in ('title', 'script'): self.part = ''

    def handle_data(self, data):
        if self.part == 'title': self.title += data
        if self.part == 'json': self.jsonld.append(json.loads(data))

    def canonical(self):
        return [a.get('href') for a in self.links if a.get('rel') == 'canonical']

    def alternates(self):
        return {a['hreflang']: a['href'] for a in self.links if a.get('rel') == 'alternate'}


def disk_target(path):
    target = DIST / unquote(path.lstrip('/'))
    return target / 'index.html' if path.endswith('/') else target


def run():
    pages = {}
    for file in DIST.rglob('*.html'):
        path = '/' + str(file.relative_to(DIST)).removesuffix('index.html')
        pages[path] = Page(file.read_text())
    urls = [elem.text for elem in ET.parse(DIST / 'sitemap.xml').findall('.//{*}loc')]
    assert len(set(urls)) == len(urls) == 8
    assert set(urls) == {ORIGIN + p for p in pages if p != '/404.html'}
    robots = (DIST / 'robots.txt').read_text().lower()
    assert 'allow: /' in robots and 'sitemap:' not in robots and 'disallow: /' not in robots
    result = []
    for path, p in sorted(pages.items()):
        assert p.h1 == 1 and len(set(p.identifiers)) == len(p.identifiers), path
        assert set(p.meta['robots'].replace(' ', '').lower().split(',')) == {'noindex','follow'}, path
        if path == '/404.html': continue
        canon = ORIGIN + path
        assert p.canonical() == [canon], path
        assert p.meta['og:url'] == canon and p.meta['og:locale'] == p.lang.replace('-','_'), path
        assert p.meta['og:title'] == p.meta['twitter:title'] == p.title, path
        assert p.meta['og:description'] == p.meta['description'] == p.meta['twitter:description'], path
        assert p.meta['twitter:image'] == p.meta['og:image'] and disk_target(urlsplit(p.meta['og:image']).path).is_file(), path
        alts = p.alternates(); assert set(alts) == {'en-US', 'es-MX', 'x-default'} and alts[p.lang] == canon and alts['x-default'] == alts['en-US'], path
        for url in alts.values():
            assert url.startswith(ORIGIN + '/') and pages[urlsplit(url).path].alternates() == alts, (path, url)
        for href in p.anchors:
            u = urlsplit(href)
            if u.scheme or u.netloc: continue
            dest = u.path or path
            assert disk_target(dest).is_file(), (path, href)
            if u.fragment: assert u.fragment in pages[dest].identifiers, (path, href)
        assert p.jsonld and all('alt' in img for img in p.images), path
        for img in p.images:
            if 'src' in img:
                assert disk_target(img['src']).is_file(), (path, img['src'])
        if '/guides/' in path or '/guias/' in path:
            graph = p.jsonld[0]['@graph']
            match = next(node for node in graph if node['@type'] == 'WebPage')
            trail = next(node for node in graph if node['@type'] == 'BreadcrumbList')
            assert match['url'] == canon and match['inLanguage'] == p.lang, path
            assert trail['itemListElement'][-1]['item'] == canon and match['breadcrumb']['@id'] == trail['@id'], path
        result.append({'route': path, 'language': p.lang, 'title': p.title, 'canonical': canon, 'noindex': True, 'alternates': alts})
    assert len({p['title'] for p in result}) == 8
    assert len({p.meta['description'] for path,p in pages.items() if path != '/404.html'}) == 8
    print(json.dumps({'status': 'passed', 'html_documents': len(pages), 'canonical_documents': len(urls), 'guide_pages': 6, '404_noindex': True, 'sitemap_advertised': False, 'pages': result}, ensure_ascii=False, indent=2))


if __name__ == '__main__': run()
