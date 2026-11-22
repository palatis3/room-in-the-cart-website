"""Generate the public website from hand-authored local copy and approved assets."""
from html import escape
from hero_previews import SCREENS as HERO_PREVIEWS
import json
from pathlib import Path
from shutil import copyfile, copytree

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
ORIGIN = "https://roominthecart.com"
BRAND = "Room in the Cart"

ICONS = {
    "book": '<path d="M3 4.5q5-2 9 1.5 4-3.5 9-1.5v14q-5-2-9 1.5-4-3.5-9-1.5z"/><path d="M12 6v14"/>',
    "list": '<rect x="4.5" y="3" width="15" height="18" rx="2.5"/><path d="m7.5 9 1.2 1.2 2-2.4M13 9h3m-8.5 6 1.2 1.2 2-2.4M13 15h3"/>',
    "compare": '<path d="M12 4v16m-3 0h6M4 6h16M6 6l-3 7h6L6 6Zm12 0-3 7h6l-3-7Z"/><path d="M3.2 13q2.8 4 5.6 0m6.4 0q2.8 4 5.6 0"/>',
    "jar": '<rect x="6" y="3" width="12" height="3" rx="1"/><path d="M7.5 6v2C6 9 5.5 10 5.5 12v6.5q0 2.5 2.5 2.5h8q2.5 0 2.5-2.5V12c0-2-.5-3-2-4V6"/><path d="M6 12h12m-12 5h12"/>',
    "dinner": '<path d="M3 13.5h18a9.6 9.6 0 0 1-18 0Zm4 7h10M8 10c-1.2-2 .9-3 0-5m4 5c-1.2-2 .9-3 0-5m4 5c-1.2-2 .9-3 0-5"/>',
    "receipt": '<path d="M5 3l2 1.5L9 3l3 1.5L15 3l2 1.5L19 3v18l-2-1.5-2 1.5-3-1.5L9 21l-2-1.5L5 21z"/><path d="M8.5 8h7m-7 4h7m-7 4h4"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="3.5" ry="9"/><path d="M3.5 12h17"/>',
    "menu": '<path d="M3 7h18M3 12h18M3 17h18"/>',
    "expand": '<path d="M14 4h6v6m0-6-6.5 6.5M10 20H4v-6m0 6 6.5-6.5"/>',
    "close": '<path d="m5 5 14 14M19 5 5 19"/>',
    "plus": '<path d="M5 12h14m-7-7v14"/>',
    "phone": '<rect x="6.5" y="2" width="11" height="20" rx="2.5"/><path d="M11 18.5h2"/>',
}

def icon(name):
    return f'<svg class="icon" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>'

def local(lang, en, es):
    return es if lang == "es-MX" else en

def home_path(lang):
    return local(lang, "/", "/es/")

def page_head(lang, path, alt_path, title, description, structured=None, social_image=None, social_alt=None):
    e = escape
    en, es = (alt_path, path) if lang == "es-MX" else (path, alt_path)
    og_locale = lang.replace("-", "_")
    other_locale = local(lang, "es_MX", "en_US")
    graph = ""
    if structured:
        graph = '<script type="application/ld+json">' + json.dumps(structured, ensure_ascii=False).replace("<", "\\u003c") + '</script>'
    assets = "/assets"
    social_image = social_image or f"{assets}/share-{lang}.jpg"
    social_alt = social_alt or local(lang, "Room in the Cart grocery planner for iPhone", "Room in the Cart para planear las compras en iPhone")
    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#fcf8ef">
<meta name="robots" content="noindex,follow">
<title>{e(title)}</title>
<meta name="description" content="{e(description,quote=True)}">
<link rel="canonical" href="{ORIGIN}{path}">
<link rel="alternate" hreflang="en-US" href="{ORIGIN}{en}">
<link rel="alternate" hreflang="es-MX" href="{ORIGIN}{es}">
<link rel="alternate" hreflang="x-default" href="{ORIGIN}{en}">
<meta property="og:type" content="{'website' if path in ('/','/es/','/404.html') else 'article'}">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:locale" content="{og_locale}">
<meta property="og:locale:alternate" content="{other_locale}">
<meta property="og:title" content="{e(title,quote=True)}">
<meta property="og:description" content="{e(description,quote=True)}">
<meta property="og:url" content="{ORIGIN}{path}">
<meta property="og:image" content="{ORIGIN}{social_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{e(social_alt,quote=True)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title,quote=True)}">
<meta name="twitter:description" content="{e(description,quote=True)}">
<meta name="twitter:image" content="{ORIGIN}{social_image}">
<link rel="icon" type="image/png" href="{assets}/favicon.png">
<link rel="apple-touch-icon" href="{assets}/app-icon.png">
<link rel="preload" as="font" type="font/woff2" crossorigin href="{assets}/fonts/InstrumentSerif-Regular.woff2">
<link rel="stylesheet" href="{assets}/site.css">
{graph}
</head>'''

def brand_link(lang):
    return f'<a class="brand" href="{home_path(lang)}" aria-label="{local(lang, "Room in the Cart home", "Room in the Cart, inicio")}"><img src="/assets/app-icon.png" width="40" height="40" alt=""><span>Room in the Cart</span></a>'

def header(lang, path, alt_path):
    t = lambda en, es: local(lang, en, es)
    home = home_path(lang)
    items = (("tour",t("App tour","La app")),("guides",t("Guides","Guías")),("faq",t("FAQ","Preguntas")))
    nav = "".join(f'<a href="{home}#{key}">{label}</a>' for key,label in items)
    alt_lang, alt_label = t("es-MX","en-US"),t("Español","English")
    return f'''<a class="skip" href="#main">{t("Skip to content","Saltar al contenido")}</a>
<header class="masthead"><div class="wrap mast-inner">
{brand_link(lang)}
<nav class="primary-nav" aria-label="{t("Main navigation","Navegación principal")}">{nav}</nav>
<div class="mast-tools"><a class="language" href="{alt_path}" hreflang="{alt_lang}" lang="{alt_lang}" aria-label="{alt_label}">{icon("globe")}<span>{alt_label}</span></a>
<details class="mobile-menu"><summary aria-label="{t("Navigation menu","Menú de navegación")}">{icon("menu")}</summary><nav aria-label="{t("Mobile navigation","Navegación móvil")}">{nav}</nav></details></div>
</div></header>'''

def footer(lang):
    t = lambda en, es: local(lang, en, es)
    query = t("", "?lang=es")
    home = home_path(lang)
    return f'''<footer class="site-footer"><div class="wrap footer-inner">
{brand_link(lang)}<nav aria-label="{t("Footer navigation","Navegación del pie de página")}"><a href="{home}#guides">{t("Guides","Guías")}</a><a href="https://help.roominthecart.com/support{query}">{t("Support","Soporte")}</a><a href="https://help.roominthecart.com/privacy{query}">{t("Privacy","Privacidad")}</a></nav>
</div></footer><script src="/assets/site.js" defer></script>'''

SCENES = (
    ("01-grocery-list","list","list",
     ("Grocery list","Make a list. <em>Check it off.</em>","Group groceries by department and check them off as you shop. If there are only two cans on the shelf, record the two you picked up and keep the third on your list.","The shopping list shows one picked item at $3.49 USD."),
     ("Lista del súper","Haz tu lista. <em>Marca lo que llevas.</em>","Agrupa tus productos por sección y márcalos mientras compras. Si solo quedan dos latas, anota las que llevas y deja la tercera pendiente en tu lista.","La lista del súper muestra un producto de 3.49 USD que ya está en el carrito.")),
    ("02-pack-comparison","compare","packs",
     ("Pack comparison","Which bag <em>costs less?</em>","Enter the price and size of two packs of the same food. Compare how many whole packs you need, what you’d pay and what you’d have left over.","The app compares the whole-bag costs of two packs of rolled oats."),
     ("Comparar paquetes","¿Qué bolsa <em>cuesta menos?</em>","Anota el precio y el tamaño de dos presentaciones del mismo alimento. Compara cuántos paquetes necesitas, cuánto pagarías y cuánto te sobraría.","La app compara el costo de comprar bolsas completas de avena en dos presentaciones.")),
    ("03-pantry","jar","pantry",
     ("Pantry","How much rice <em>is left?</em>","Check what’s in your pantry, fridge and freezer before you shop. Choose how much to use for dinner and see what you still need to buy.","The pantry shows three cups of brown rice."),
     ("Despensa","¿Cuánto arroz <em>te queda?</em>","Revisa la despensa, el refri y el congelador antes de ir al súper. Elige cuánto vas a usar para la cena y ve qué te falta comprar.","La despensa muestra tres tazas de arroz integral.")),
    ("04-dinner","dinner","dinner",
     ("Dinner plan","Taco night <em>for four.</em>","Save your recipes, put dinner on the calendar and adjust the servings. Set aside tomorrow’s lunch while you’re planning tonight’s meal.","The dinner plan shows black bean tacos for four."),
     ("Plan de cenas","Noche de tacos <em>para cuatro.</em>","Guarda tus recetas, anota la cena en el calendario y ajusta las porciones. Aparta comida para mañana mientras planeas lo que vas a preparar hoy.","El plan de cenas muestra tacos de frijoles negros para cuatro personas.")),
    ("05-receipt-review","receipt","receipt",
     ("Receipt review","Your receipt, <em>line by line.</em>","Open a receipt photo or PDF and check each line against what came home. Save the usable amount to the pantry, fridge or freezer.","Receipt review shows the selected grocery lines before preview."),
     ("Revisar el recibo","Tu recibo, <em>renglón por renglón.</em>","Abre una foto o un PDF de tu recibo y compara cada renglón con lo que recibiste. Guarda la cantidad que puedes usar en la despensa, el refri o el congelador.","La revisión del recibo muestra la cantidad de lentejas y el lugar donde se van a guardar.")),
)
GUIDES = (
    ("budget", ("At the store","Compare the cost of two packs","Work out how many packs you’ll need and what you’ll pay at checkout.","/guides/grocery-budget/"), ("En el súper","Compara el costo de dos paquetes","Calcula cuántos paquetes necesitas y cuánto pagarías en la caja.","/es/guias/presupuesto-del-super/")),
    ("pantry", ("In the kitchen","Plan dinner from your pantry","Start with what’s on the shelf and put only the missing ingredients on your list.","/guides/pantry-to-dinner/"), ("En la cocina","Planea la cena con tu despensa","Empieza con lo que ya tienes y agrega a la lista solo lo que te falta.","/es/guias/de-la-despensa-a-la-cena/")),
    ("receipt", ("Back at home","From receipt to pantry shelf","Check what came home, then record the amount you can actually use.","/guides/receipt-to-pantry/"), ("De vuelta en casa","Del recibo a la despensa","Revisa qué llegó a casa y anota cuánto puedes usar.","/es/guias/del-ticket-a-la-despensa/")),
)
FAQ = (
    (("When can I download Room in the Cart?","The iPhone app is planned for the United States and Mexico. The release date hasn’t been announced."),("¿Cuándo podré descargar Room in the Cart?","El lanzamiento para iPhone está previsto en México y Estados Unidos. Aún no se ha anunciado la fecha.")),
    (("Can I use the app offline?","Yes. You can make a grocery list and compare pack sizes offline, without creating an account. Optional features such as looking up a barcode or importing a recipe link need an internet connection."),("¿Puedo usar la app sin conexión?","Sí. Puedes hacer tu lista y comparar paquetes sin conexión y sin crear una cuenta. Algunas funciones opcionales, como buscar un código de barras o importar una receta desde un enlace, requieren internet.")),
    (("Which currency does the app use?","Grocery prices, budgets and estimates use US dollars (USD) in both languages, including in Mexico. Enter the prices you want to compare in USD."),("¿En qué moneda se muestran los precios?","Los precios, presupuestos y cálculos se expresan en dólares estadounidenses (USD), también en México. Anota en USD los precios que quieras comparar.")),
    (("Can I use the app in Spanish?","Yes. Room in the Cart is available in English and Mexican Spanish. You can select the app’s language in Settings."),("¿Puedo usar la app en español?","Sí. Room in the Cart está en español de México y en inglés. Puedes elegir el idioma de la app en Configuración.")),
)

def screen_image(lang, name, alt, eager=False, sizes="(max-width: 620px) 126px, (max-width: 940px) 142px, (max-width: 1450px) 13vw, 192px"):
    path = f"/assets/screens/{lang}/{name}"
    load = 'loading="eager" decoding="sync" fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    return f'<img src="{path}-400.webp" srcset="{path}-400.webp 400w, {path}-760.webp 760w" sizes="{sizes}" width="400" height="869" {load} alt="{escape(alt)}">'

def render_tour(lang):
    is_es = lang == "es-MX"
    t = lambda en, es: local(lang,en,es)
    tabs, panels = [], []
    home = home_path(lang)
    for i,(name,glyph,key,en,es) in enumerate(SCENES):
        label,title,summary,alt = es if is_es else en
        tabs.append(f'<a class="tour-tab" id="tab-{key}" href="#scene-{key}">{icon(glyph)}<span>{label}</span></a>')
        image = screen_image(lang,name,alt)
        guide = 0 if i < 2 else 1 if i < 4 else 2
        _,gen,ges = GUIDES[guide]
        _,gtitle,_,url = ges if is_es else gen
        panels.append(f'''<section class="tour-slide scene-{key}" id="scene-{key}" aria-labelledby="title-{key}">
<div class="stage"><div class="stage-orbit" aria-hidden="true"></div>
<picture class="stage-illustration"><source media="(max-width:760px), (max-width:960px) and (max-height:500px)" srcset="/assets/market-illustration-360.webp"><img src="/assets/market-illustration.webp" alt="" loading="lazy" width="576" height="230"></picture>
<a class="screen-link" href="/assets/screens/{lang}/{name}-760.webp" data-screen-title="{escape(label)}" aria-label="{t("Enlarge screenshot","Ampliar captura")} — {escape(label)}"><span class="device tour-device">{image}</span><span class="zoom">{icon("expand")}<span>{t("Enlarge","Ampliar")}</span></span></a>
</div><div class="scene-copy"><span class="scene-symbol">{icon(glyph)}</span><h3 id="title-{key}">{title}</h3><p>{summary}</p><a class="text-link" href="{url}">{gtitle}</a></div></section>''')
    return f'''<section class="tour-section wrap" id="tour" aria-labelledby="tour-heading">
<div class="section-intro"><div><p class="eyebrow">{t("Inside the app","Dentro de la app")}</p><h2 id="tour-heading">{t("A grocery run, <em>start to finish.</em>","Una vuelta al súper, <em>de principio a fin.</em>")}</h2></div></div>
<nav class="tour-tabs" aria-label="{t("App tour chapters","Secciones del recorrido")}">{''.join(tabs)}</nav>
<div class="tour-panels">{''.join(panels)}</div></section>
<dialog class="screen-dialog" aria-labelledby="screen-dialog-title"><div class="dialog-top"><strong id="screen-dialog-title"></strong><form method="dialog"><button aria-label="{t("Close screenshot","Cerrar captura")}">{icon("close")}</button></form></div><div class="dialog-image"><img alt=""></div></dialog>'''

def render_guides(lang):
    t = lambda en, es: local(lang,en,es)
    cards = []
    for key,en,es in GUIDES:
        label,title,desc,url = local(lang,en,es)
        cards.append(f'''<article class="guide-card"><a href="{url}"><div class="guide-photo"><picture><source media="(max-width:620px), (max-width:960px) and (max-height:500px)" srcset="/assets/guide-{key}-480.webp 480w, /assets/guide-{key}-720.webp 720w" sizes="(min-width:621px) 28vw, 90vw"><img alt="" src="/assets/guide-{key}-480.webp" srcset="/assets/guide-{key}-480.webp 480w, /assets/guide-{key}.webp 960w" sizes="(max-width: 639px) 92vw, (max-width: 1200px) 33vw, 400px" width="960" height="600" loading="lazy" decoding="async"></picture></div>
<div class="guide-card-copy"><p class="eyebrow">{label}</p><h3>{title}</h3><p>{desc}</p></div></a></article>''')
    return f'''<section class="guides-section" id="guides" aria-labelledby="guides-heading"><div class="wrap">
<div class="section-intro"><div><p class="eyebrow">{t("Kitchen guides","Guías de cocina")}</p><h2 id="guides-heading">{t("Notes for <em>the next shop.</em>","Ideas para <em>la próxima compra.</em>")}</h2></div></div>
<div class="guide-cards">{''.join(cards)}</div></div></section>'''

def render_faq(lang):
    t = lambda en, es: local(lang,en,es)
    items = []
    for en,es in FAQ:
        q,a = local(lang,en,es)
        items.append(f'<details><summary><span>{q}</span>{icon("plus")}</summary><p>{a}</p></details>')
    return f'''<section class="faq-section wrap" id="faq" aria-labelledby="faq-heading"><div class="faq-title"><p class="eyebrow">{t("Before launch","Antes del lanzamiento")}</p><h2 id="faq-heading">{t("A few <em>questions.</em>","Algunas <em>preguntas.</em>")}</h2><a class="text-link" href="https://help.roominthecart.com/support{t("", "?lang=es")}">{t("Visit support","Ir a soporte")}</a></div><div class="faqs">{''.join(items)}</div></section>'''

def home_page(lang):
    t = lambda en, es: local(lang,en,es)
    path, alternate = home_path(lang), t("/es/","/")
    title = t("Room in the Cart | Grocery List, Pantry & Meal Planner","Room in the Cart | Lista del súper, despensa y comidas")
    desc = t("Plan dinners, make a grocery list and compare whole-pack prices on iPhone. See what’s in your pantry and review receipts when you get home.","Planea cenas, haz tu lista del súper y compara precios por paquete en iPhone. Revisa tu despensa y registra lo que compraste al llegar a casa.")
    data = {"@context":"https://schema.org","@type":"WebPage","name":title,"description":desc,"inLanguage":lang,"url":ORIGIN+path,"about":{"@type":"MobileApplication","name":BRAND,"operatingSystem":"iOS","applicationCategory":"LifestyleApplication"}}
    head = page_head(lang,path,alternate,title,desc,data)
    image = screen_image(lang,"01-grocery-list", t("Room in the Cart showing a grocery trip on iPhone.","Room in the Cart muestra una vuelta al súper en iPhone."),True,"(orientation: landscape) and (max-height: 500px) and (max-width: 960px) 127px, (max-width: 430px) 123px, (max-width: 760px) 160px, (max-width: 940px) 185px, (max-width: 1500px) 16.5vw, 246px")
    hero = f'''<section class="hero" aria-labelledby="hero-heading">
<picture class="hero-art" aria-hidden="true"><source media="(orientation:landscape) and (max-width:960px) and (max-height:500px)" srcset="/assets/market-mobile-640.webp 640w, /assets/market-mobile-900.webp 900w" sizes="55vw"><source media="(max-width:760px) and (orientation:portrait)" srcset="/assets/market-mobile-640.webp 640w, /assets/market-mobile-900.webp 900w" sizes="100vw"><img src="/assets/market-still-life-1200.webp" srcset="/assets/market-still-life-640.webp 640w, /assets/market-still-life-1200.webp 1200w" sizes="(max-width: 679px) 100vw, 62vw" width="1200" height="1200" alt="" fetchpriority="high"></picture>
<div class="wrap hero-inner"><div class="hero-copy"><p class="hero-kicker">{icon("phone")}{t("Coming to iPhone","Próximamente en iPhone")}</p>
<h1 id="hero-heading">{t("From grocery list <em>to taco night.</em>","De la lista del súper <em>a la noche de tacos.</em>")}</h1>
<p class="hero-desc">{t("Plan dinner with what’s in your pantry, compare prices in the aisle, and bring home the groceries you need.","Planea la cena con lo que tienes en la despensa, compara precios en el súper y lleva a casa lo que necesitas.")}</p>
<div class="hero-actions"><a class="button" href="#tour">{icon("book")}{t("Explore the app","Explora la app")}</a><a class="hero-link" href="#guides">{t("Read the guides","Lee las guías")}</a></div>
</div><div class="hero-product"><div class="device hero-device" style="--preview:url(data:image/webp;base64,{HERO_PREVIEWS[lang]})">{image}</div></div></div>
</section>'''
    return head + '<body>' + header(lang,path,alternate) + '<main id="main" tabindex="-1">' + hero + render_tour(lang) + render_guides(lang) + render_faq(lang) + '</main>' + footer(lang) + '</body></html>'

def not_found():
    return '''<!doctype html><html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex,follow"><title>Page not found | Room in the Cart</title><link rel="icon" href="/assets/favicon.png"><link rel="stylesheet" href="/assets/site.css"></head><body>''' + header("en-US","/404.html","/es/") + '''<main id="main" tabindex="-1" class="wrap error-page"><p class="eyebrow">404</p><h1>Page <em>not found.</em></h1><p>This address doesn’t lead to a page on Room in the Cart.</p><p lang="es-MX">Esta dirección no lleva a una página de Room in the Cart.</p><div class="error-links"><a class="button" href="/">English home</a><a class="text-link" lang="es-MX" href="/es/">Inicio en español</a></div></main>''' + footer("en-US") + '</body></html>'

def build_site():
    (DIST / "es").mkdir(parents=True,exist_ok=True)
    (DIST / "assets").mkdir(exist_ok=True)
    copytree(ROOT / "src/media", DIST / "assets", dirs_exist_ok=True)
    for name in ("site.css","site.js"):
        copyfile(ROOT / "src/assets" / name,DIST / "assets" / name)
    for lang,path in (("en-US","index.html"),("es-MX","es/index.html")):
        (DIST / path).write_text(home_page(lang),encoding="utf-8")
    (DIST / "404.html").write_text(not_found(),encoding="utf-8")

if __name__ == "__main__":
    build_site()
    from guides import build_guides
    build_guides()
