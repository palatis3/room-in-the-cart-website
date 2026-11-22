"""Verify deployed public pages, alternates, real assets and noindex directives."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit, unquote
from urllib.request import Request, urlopen
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

class Markup(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elements = defaultdict(list)
        self.title = ''
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        self.elements[tag].append(dict(attrs))
        if tag == 'title':
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data

def fetch(url):
    request = Request(url, headers={'User-Agent': 'RITC-Site-Verification/1.0'})
    try:
        response = urlopen(request, timeout=20)
    except HTTPError as error:
        response = error
    with response:
        return response.status, response.url, response.headers, response.read()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', default='https://roominthecart.com')
    parser.add_argument('--preview-origin', help='Request staging while checking production canonical URLs')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    origin = args.origin.rstrip('/')
    host = (args.preview_origin or origin).rstrip('/')
    def get(url):
        wire = host + url[len(origin):] if url == origin or url.startswith(origin + '/') else url
        status, final, headers, body = fetch(wire)
        if host != origin and (final == host or final.startswith(host + '/')):
            final = origin + final[len(host):]
        return status, final, headers, body
    checks, failures = {}, []
    def check(ok, label):
        if not ok:
            failures.append(label)
    status, _, headers, xml = get(origin + '/sitemap.xml')
    check(status == 200, 'sitemap status')
    pages = [e.text for e in ET.fromstring(xml).findall('.//{*}loc')]
    check(len(set(pages)) >= 8, 'bilingual page count')
    entries, assets, titles, descriptions = {}, set(), [], []
    def route(url):
        return urlsplit(url).path or '/'
    for url in pages:
        status, final, head, body = get(url)
        html = body.decode('utf8')
        dom = Markup()
        dom.feed(html)
        tags = dom.elements
        metas = {t.get('name',t.get('property','')):t.get('content','') for t in tags['meta']}
        alternates = {t.get('hreflang'):t.get('href') for t in tags['link'] if t.get('hreflang')}
        canonical = [t.get('href') for t in tags['link'] if t.get('rel')=='canonical']
        check(status == 200 and final == url, url+' canonical returns 200 directly')
        check(canonical == [url], url+' canonical tag')
        check('noindex' in metas.get('robots','').lower(), url+' noindex meta')
        check('noindex' in head.get('X-Robots-Tag','').lower(), url+' noindex response')
        check(len(tags['h1']) == 1 and len(dom.title.strip()) > 0, url+' h1/title')
        check(bool(metas.get('description')), url+' description')
        check(bool(metas.get('og:image')), url+' open graph image')
        check(metas.get('og:url') == url, url+' open graph URL')
        check(any(k.startswith('en') for k in alternates) and any(k.startswith('es') for k in alternates), url+' alternates')
        ids = {a['id'] for elements in tags.values() for a in elements if 'id' in a}
        hrefs = [urljoin(url,t['href']) for t in tags['a'] if t.get('href')]
        for tag, attr in [('img','src'),('source','src'),('script','src'),('link','href')]:
            for t in tags[tag]:
                if tag=='link' and t.get('rel') not in ('stylesheet','icon','preload','apple-touch-icon','manifest'):
                    continue
                if t.get(attr):
                    assets.add(urljoin(url,t[attr]))
        for t in tags['img']+tags['source']:
            check(t not in tags['img'] or 'alt' in t, url+' image alternative')
            for s in (t.get('srcset') or '').split(','):
                if s.strip():
                    assets.add(urljoin(url,s.strip().split()[0]))
        if metas.get('og:image'):
            assets.add(urljoin(url,metas['og:image']))
        for t in tags['script']:
            if t.get('src'):
                linked = urlsplit(urljoin(url,t['src'])).hostname
                check(linked == urlsplit(origin).hostname, url+' unexpected external script '+str(linked))
        entries[url]=(ids,hrefs,alternates)
        lang=tags['html'][0].get('lang','')
        check(lang.startswith('es' if route(url).startswith('/es/') else 'en'),url+' html language')
        checks[url] = {'status':status,'lang':lang,'title':dom.title,'canonical':canonical,'alternate':alternates,'robots':head.get('X-Robots-Tag')}
        titles.append(dom.title);descriptions.append(metas.get('description'))
    check(len(set(titles))==len(pages),'unique page titles')
    check(len(set(descriptions))==len(pages),'unique descriptions')
    for url,(_,hrefs,alternates) in entries.items():
        for target in alternates.values():
            check(target in entries and url in entries[target][2].values(),url+' reciprocal alternate '+str(target))
        for href in hrefs:
            part=urlsplit(href)
            if part.hostname != urlsplit(origin).hostname:
                continue
            target=origin+(part.path or '/')
            check(target in entries or href in assets,url+' internal link '+href)
            if part.fragment and target in entries:
                check(unquote(part.fragment) in entries[target][0],url+' fragment '+href)
    local_assets=sorted(a for a in assets if urlsplit(a).hostname==urlsplit(origin).hostname)
    def verify_asset(url):
        status,_,head,body=get(url)
        return url,status,head.get('X-Robots-Tag',''),len(body)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for url,status,robots,size in pool.map(verify_asset,local_assets):
            check(status==200 and size>0,url+' asset response')
            check('noindex' in robots.lower(),url+' asset noindex')
    robots=get(origin+'/robots.txt')[3].decode('utf8')
    check(not any(line.split('#')[0].strip().lower().replace(' ','')=='disallow:/' for line in robots.splitlines()),'robots.txt must permit noindex discovery')
    check(get(origin+'/this-page-does-not-exist-ritc-qa')[0]==404, 'custom 404 status')
    result={'checkedAt':datetime.now(timezone.utc).isoformat(),'pages':checks,'checkedAssets':len(local_assets),'issues':failures}
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(len(pages),'pages;',len(local_assets),'assets;',len(failures),'issues')
    for failure in failures:
        print(failure)
    return bool(failures)
if __name__=='__main__':
    raise SystemExit(main())
