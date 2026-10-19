#!/usr/bin/env python3
"""Generador de la web de Downtown Life VIP.

Uso:
    python3 build.py            -> genera la web lista para subir en ./dist
    python3 build.py --preview  -> genera una versión con enlaces relativos en ./preview
                                   (para abrir los archivos en el ordenador sin servidor)

Para publicar un artículo nuevo, crea un archivo .md en content/posts/
(copia content/posts/_plantilla.md) y vuelve a ejecutar el generador.
"""
import html
import json
import math
import re
import shutil
import sys
from datetime import date, datetime, timezone
from email.utils import format_datetime
from pathlib import Path

import markdown

# ---------------------------------------------------------------- configuración
SITE = {
    "url": "https://downtownlifevipmargarita.com",
    "name": "Downtown Life VIP",
    "tagline": "Apartamento frente al mar en Pampatar",
    "airbnb": "https://www.airbnb.es/rooms/1113809198959554052",
    "airbnb_short": "airbnb.es/h/downtownlifemargarita",
    "host": "Dayana",
    "whatsapp_link": "https://wa.me/qr/YEER4SHRSWEZF1",  # enlace corto de WhatsApp Business (no muestra tu número), ej. "https://wa.me/message/ABCDEF123456"
    "instagram": "",     # ej. "downtownlifevip"
    "email": "",         # ej. "hola@downtownlifemargarita.com"
    "address": "Pampatar, Isla de Margarita, Venezuela",   # zona aproximada: la dirección exacta se envía tras reservar
    "maps": "https://www.google.com/maps/search/?api=1&query=Pampatar,+Nueva+Esparta,+Venezuela",
    "rating": "5,0", "rating_num": 5.0, "reviews": 75, "years": 3,
}
ROOT = Path(__file__).parent
PREVIEW = "--preview" in sys.argv
if "--demo-wa" in sys.argv and not SITE["whatsapp_link"]:
    SITE["whatsapp_link"] = "https://wa.me/message/PENDIENTE"  # solo para la vista previa
OUT = ROOT / ("preview" if PREVIEW else "dist")
CATEGORIES = {
    "playas": "Playas",
    "pampatar": "Pampatar",
    "excursiones": "Excursiones",
    "gastronomia": "Gastronomía",
    "consejos": "Consejos de viaje",
}
CATEGORIES_EN = {
    "playas": "Beaches",
    "pampatar": "Pampatar",
    "excursiones": "Day trips",
    "gastronomia": "Food",
    "consejos": "Travel tips",
}
MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def cat_label(c, lang="es"):
    return CATEGORIES_EN[c] if lang == "en" else CATEGORIES[c]

# ---------------------------------------------------------------- iconos (SVG de línea)
ICONS = {
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "bed": '<path d="M2 4v16"/><path d="M2 8h18a2 2 0 0 1 2 2v10"/><path d="M2 17h20"/><path d="M6 8v9"/>',
    "bath": '<path d="M4 12h16v3a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z"/><path d="M6 12V5a2 2 0 0 1 3.5-1.3"/><path d="M7 20l-1 2M17 20l1 2"/>',
    "sofa": '<path d="M20 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v3"/><path d="M2 11v5a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-5a2 2 0 0 0-4 0v2H6v-2a2 2 0 0 0-4 0z"/><path d="M4 18v2M20 18v2"/>',
    "waves": '<path d="M2 7c1.5 1.2 3 1.2 4.5 0s3-1.2 4.5 0 3 1.2 4.5 0 3-1.2 4.5 0"/><path d="M2 12c1.5 1.2 3 1.2 4.5 0s3-1.2 4.5 0 3 1.2 4.5 0 3-1.2 4.5 0"/><path d="M2 17c1.5 1.2 3 1.2 4.5 0s3-1.2 4.5 0 3 1.2 4.5 0 3-1.2 4.5 0"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "snow": '<path d="M12 2v20M3.3 7l17.4 10M3.3 17L20.7 7"/><path d="M9 4l3 2 3-2M9 20l3-2 3 2"/>',
    "wifi": '<path d="M2 9a15 15 0 0 1 20 0"/><path d="M5 12.5a10 10 0 0 1 14 0"/><path d="M8.5 16a5 5 0 0 1 7 0"/><circle cx="12" cy="19.5" r="1"/>',
    "car": '<path d="M3 13l2-5.5A2 2 0 0 1 6.9 6h10.2a2 2 0 0 1 1.9 1.5L21 13v5h-3v-2H6v2H3z"/><circle cx="7.5" cy="13" r="1"/><circle cx="16.5" cy="13" r="1"/>',
    "kitchen": '<path d="M3 11h18v3a6 6 0 0 1-6 6H9a6 6 0 0 1-6-6z"/><path d="M8 7c0-1.5 1-2 1-3M12 7c0-1.5 1-2 1-3M16 7c0-1.5 1-2 1-3"/>',
    "laptop": '<rect x="4" y="5" width="16" height="11" rx="1.5"/><path d="M2 19h20"/>',
    "washer": '<rect x="4" y="2" width="16" height="20" rx="2"/><circle cx="12" cy="13" r="5"/><path d="M8 6h.01M11 6h.01"/>',
    "check": '<path d="M20 6L9 17l-5-5"/>',
    "star": '<path d="M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z"/>',
    "pin": '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "message": '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 21l1.9-5.4A8 8 0 1 1 21 12z"/>',
    "instagram": '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r=".6"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "menu": '<path d="M4 6h16M4 12h16M4 18h16"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
    "key": '<circle cx="7.5" cy="15.5" r="4.5"/><path d="M10.7 12.3L21 2M17 6l3 3"/>',
    "pool": '<path d="M2 18c1.5 1.2 3 1.2 4.5 0s3-1.2 4.5 0 3 1.2 4.5 0 3-1.2 4.5 0"/><path d="M8 15V5a2 2 0 0 1 4 0M16 15V5a2 2 0 0 0-4 0M8 9h8M8 13h8"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
}
def icon(name, cls="icon"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'

LOGO = ('<svg viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="19" fill="#1F3A55"/>'
        '<circle cx="20" cy="16" r="5.5" fill="#F7E695"/>'
        '<path d="M8 25c2 1.4 4 1.4 6 0s4-1.4 6 0 4 1.4 6 0 4-1.4 6 0" stroke="#F6F1E7" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
        '<path d="M11 30c1.5 1 3 1 4.5 0s3-1 4.5 0 3 1 4.5 0 3-1 4.5 0" stroke="#F6F1E7" stroke-width="1.6" fill="none" stroke-linecap="round" opacity=".7"/></svg>')

# ---------------------------------------------------------------- utilidades
def esc(s):
    return html.escape(s, quote=True)

def fdate(iso, lang="es"):
    y, m, d = [int(x) for x in iso.split("-")]
    if lang == "en":
        return f"{MONTHS_EN[m-1]} {d}, {y}"
    return f"{d} de {MONTHS[m-1]} de {y}"

class Page:
    """Contexto de una página: su ruta (p. ej. 'blog/playas-margarita/') y cómo enlazar desde ella."""
    def __init__(self, path):
        self.path = path
        self.depth = path.count("/")
        self.images = []
    def u(self, target):
        if PREVIEW:
            rel = "../" * self.depth
            if target.endswith("/") or target == "":
                return rel + target + "index.html"
            return rel + target
        return "/" + target
    def abs(self, target=None):
        return SITE["url"] + "/" + (self.path if target is None else target)

from PIL import Image as _PIL
CATALOG = json.loads((ROOT / "content" / "fotos.json").read_text(encoding="utf-8"))
_DIMS = {}
def dims(name):
    if name not in _DIMS:
        with _PIL.open(ROOT / "fotos" / (name + ".webp")) as im:
            _DIMS[name] = im.size
    return _DIMS[name]

def cat_entry(name):
    v = CATALOG.get(name)
    return v if isinstance(v, dict) else ({"alt": v} if v else {})

def alt_for(name, alt=None, lang="es"):
    if alt:
        return alt
    e = cat_entry(name)
    return (e.get("alt_en") if lang == "en" else None) or e.get("alt") or name.replace("-", " ")

def credit_html(name, lang="es"):
    """Crédito para fotos con licencia libre (Wikimedia Commons)."""
    e = cat_entry(name)
    if "credit" not in e:
        return ""
    c = e.get("credit_en") if lang == "en" else e["credit"]
    author = re.sub(r"\s*\(.*\)\s*$", "", c)
    lic = e.get("license", "")
    lic_html = f' · <a href="{e["license_url"]}" target="_blank" rel="noopener license">{esc(lic)}</a>' if lic and e.get("license_url") else ""
    changed = (" · Recortada y redimensionada" if lang != "en" else " · Cropped and resized") if "SA" in lic else ""
    return f' <span class="credit"><a href="{e["source"]}" target="_blank" rel="noopener">{esc(author)}</a>{lic_html}{changed}</span>'

def img(p, name, alt=None, cls="", sizes="(max-width: 700px) 100vw, 50vw", lazy=True, lang="es"):
    """Imagen responsive con medidas reales, texto alternativo del catálogo y registro para el mapa de imágenes."""
    w, h = dims(name)
    if name not in p.images:
        p.images.append(name)
    a = 'loading="lazy" decoding="async"' if lazy else 'fetchpriority="high" decoding="async"'
    c = f' class="{cls}"' if cls else ""
    return (f'<img{c} src="{p.u("fotos/" + name + ".webp")}" '
            f'srcset="{p.u("fotos/" + name + "-640.webp")} 640w, {p.u("fotos/" + name + ".webp")} {w}w" '
            f'sizes="{sizes}" width="{w}" height="{h}" alt="{esc(alt_for(name, alt, lang))}" {a}>')

WA_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true" width="22" height="22"><path fill="currentColor" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.7.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.2-.4.7-1.4a.5.5 0 0 0 0-.5l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.7 11.8 11.8 0 0 0 4.5 4c1.7.7 2.3.8 3.2.6a2.7 2.7 0 0 0 1.8-1.2 2.2 2.2 0 0 0 .1-1.2c0-.1-.2-.2-.4-.3z"/></svg>'

def wa_link():
    return SITE.get("whatsapp_link", "")

def wa_modal(p, lang="es"):
    if not wa_link():
        return ""
    if lang == "en":
        t = ("Close", "Message us on WhatsApp", "Scan this code with your phone camera and WhatsApp will open so you can message us.",
             "We reply as soon as we can.", "QR code to message Downtown Life VIP on WhatsApp")
    else:
        t = ("Cerrar", "Escríbenos por WhatsApp", "Escanea este código con la cámara de tu móvil y se abrirá WhatsApp para escribirnos.",
             "Te respondemos lo antes posible.", "Código QR para escribir por WhatsApp a Downtown Life VIP")
    return (f'<div class="wa-modal" id="wa-modal" hidden role="dialog" aria-modal="true" aria-labelledby="wa-modal-t">'
            f'<div class="wa-modal-box"><button type="button" class="wa-modal-x" aria-label="{t[0]}">✕</button>'
            f'<h3 id="wa-modal-t">{t[1]}</h3>'
            f'<p>{t[2]}</p>'
            f'<p class="wa-modal-note">{t[3]}</p>'
            f'<img src="{p.u("assets/img/whatsapp-qr.svg")}" width="220" height="220" alt="{t[4]}">'
            f'</div></div>')

def wa_card(title="¿Tienes alguna pregunta?", text="Escríbenos por WhatsApp y te respondemos lo antes posible.", button="Escribir por WhatsApp"):
    if not wa_link():
        return ""
    return (f'<div class="wa-card"><h3>{title}</h3><p>{text}</p>'
            f'<a class="btn btn-wa" href="{wa_link()}" target="_blank" rel="noopener">{WA_SVG} {button}</a></div>')

def book_url():
    return SITE["airbnb"]

# ---------------------------------------------------------------- plantilla base
def layout(p, title, description, body, active="", schema=None, og_image="fotos/og/portada.jpg", og_type="website", noindex=False, og_alt="", extra_head="", lang="es", alternates=None):
    """alternates: lista de (idioma, ruta) con las versiones de esta página en cada idioma (para hreflang)."""
    en = lang == "en"
    # Botón "Volver" en todas las páginas menos la portada
    if p.path not in ("", "en/blog/"):
        parts = [x for x in p.path.strip("/").split("/") if x]
        parent = "/".join(parts[:-1])
        if parent in ("blog/categoria", "en"):
            parent = parent.split("/")[0] if parent != "en" else ""
        parent = (parent + "/") if parent else ""
        back = (f'<a class="back-link" href="{p.u(parent)}" data-back>'
                f'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5M11 6l-6 6 6 6"/></svg>{"Back" if en else "Volver"}</a>')
        body = body.replace('<section class="page-hero"><div class="container">', '<section class="page-hero"><div class="container">' + back, 1)
    full_title = title if (title.endswith(SITE["name"]) or len(title) > 44) else f"{title} | {SITE['name']}"
    if en:
        nav_items = [("en/blog/", "Margarita guide"), ("apartamento/", "The apartment"), ("contacto/", "Contact")]
    else:
        nav_items = [("", "Inicio"), ("apartamento/", "El apartamento"), ("blog/", "Guía de Margarita"), ("sobre-dayana/", "Sobre mí"), ("contacto/", "Contacto")]
    nav = "".join(
        f'<li><a href="{p.u(t)}"{" aria-current=\"page\"" if active == t else ""}>{l}</a></li>' for t, l in nav_items)
    alternates = alternates or []
    hreflang = ""
    switch = ""
    if len(alternates) > 1:
        hreflang = "".join(f'<link rel="alternate" hreflang="{l}" href="{SITE["url"]}/{path}">' for l, path in alternates)
        es_path = dict(alternates).get("es")
        hreflang += f'<link rel="alternate" hreflang="x-default" href="{SITE["url"]}/{es_path}">'
        other = [(l, path) for l, path in alternates if l != lang][0]
        label = "Español" if other[0] == "es" else "English"
        switch = f'<li class="lang-switch"><a href="{p.u(other[1])}" hreflang="{other[0]}" lang="{other[0]}">{label}</a></li>'
    schema_tags = "".join(f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>' for s in (schema or []))
    social = ""
    if SITE["instagram"]:
        social += f'<li><a href="https://instagram.com/{SITE["instagram"]}" rel="noopener" target="_blank">Instagram</a></li>'
    if wa_link():
        social += f'<li><a href="{wa_link()}" rel="noopener" target="_blank">WhatsApp</a></li>'
    year = date.today().year
    home = "en/blog/" if en else ""
    T = {
        "skip": "Skip to content" if en else "Saltar al contenido",
        "home_label": "home" if en else "inicio",
        "menu": "Open menu" if en else "Abrir menú",
        "nav": "Main" if en else "Principal",
        "book_long": "Book on Airbnb" if en else "Reservar en Airbnb",
        "book": "Book" if en else "Reservar",
        "small": "Pampatar · Margarita",
        "wa_float": "Questions? Message us" if en else "¿Dudas? Escríbenos",
        "wa_aria": "Message us on WhatsApp" if en else "Escríbenos por WhatsApp",
        "mobile_reviews": "reviews" if en else "evaluaciones",
    }
    if en:
        footer_cols = f"""<div>
      <a class="brand" href="{p.u(home)}">{LOGO}<span class="brand-name">Downtown Life VIP<small>Pampatar · Margarita</small></span></a>
      <p>Beachfront apartment on the Caribbean Sea in Pampatar, Margarita Island, Venezuela. Your host: {SITE['host']}, Airbnb Superhost.</p>
    </div>
    <div><h2 class="footer-h">The apartment</h2><ul>
      <li><a href="{p.u('apartamento/')}">Photos and details (Spanish)</a></li>
      <li><a href="{book_url()}" target="_blank" rel="noopener">Book on Airbnb</a></li>
    </ul></div>
    <div><h2 class="footer-h">Margarita guide</h2><ul>
      <li><a href="{p.u('en/blog/')}">All articles</a></li>
      <li><a href="{p.u('blog/')}" hreflang="es">Guía en español</a></li>
    </ul></div>
    <div><h2 class="footer-h">Contact</h2><ul>
      <li><a href="{p.u('contacto/')}">Get in touch</a></li>{social}
      <li><a href="{p.u('aviso-legal/')}">Legal notice</a></li>
      <li><a href="{p.u('privacidad/')}">Privacy and cookies</a></li>
    </ul></div>"""
        rss = ""
    else:
        cat_links = "".join(f'<li><a href="{p.u("blog/categoria/" + k + "/")}">{v}</a></li>' for k, v in CATEGORIES.items())
        footer_cols = f"""<div>
      <a class="brand" href="{p.u('')}">{LOGO}<span class="brand-name">Downtown Life VIP<small>Pampatar · Margarita</small></span></a>
      <p>Apartamento frente al mar Caribe en Pampatar, Isla de Margarita. Anfitriona: {SITE['host']}, Superanfitriona en Airbnb.</p>
    </div>
    <div><h2 class="footer-h">El apartamento</h2><ul>
      <li><a href="{p.u('apartamento/')}">Fotos y detalles</a></li>
      <li><a href="{p.u('apartamento/')}#comodidades">Comodidades</a></li>
      <li><a href="{p.u('apartamento/')}#preguntas">Preguntas frecuentes</a></li>
      <li><a href="{book_url()}" target="_blank" rel="noopener">Reservar en Airbnb</a></li>
    </ul></div>
    <div><h2 class="footer-h">Guía de Margarita</h2><ul>{cat_links}<li><a href="{p.u('en/blog/')}" hreflang="en">Guide in English</a></li></ul></div>
    <div><h2 class="footer-h">Contacto</h2><ul>
      <li><a href="{p.u('contacto/')}">Escríbenos</a></li>{social}
      <li><a href="{p.u('sobre-dayana/')}">Sobre la anfitriona</a></li>
      <li><a href="{p.u('aviso-legal/')}">Aviso legal</a></li>
      <li><a href="{p.u('privacidad/')}">Privacidad y cookies</a></li>
    </ul></div>"""
        rss = f'<link rel="alternate" type="application/rss+xml" title="Guía de Margarita" href="{p.u("feed.xml")}">'
    wa_float = (f'<a class="wa-float" href="{wa_link()}" target="_blank" rel="noopener" aria-label="{T["wa_aria"]}">{WA_SVG}<span>{T["wa_float"]}</span></a>') if wa_link() else ''
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{p.abs()}">
{hreflang}
{'<meta name="robots" content="noindex">' if noindex else ''}
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{SITE['name']}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{p.abs()}">
<meta property="og:image" content="{SITE['url']}/{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(og_alt or title)}">
{extra_head}
<meta property="og:locale" content="{'en_US' if en else 'es_ES'}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#FFFFFF">
<link rel="icon" href="{p.u('favicon.svg')}" type="image/svg+xml">
<link rel="icon" href="{p.u('favicon-32.png')}" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="{p.u('apple-touch-icon.png')}">
{rss}
<link rel="preload" href="{p.u('assets/fonts/jost-latin-400-normal.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{p.u('assets/css/style.css')}">
{schema_tags}
</head>
<body>
<a class="skip" href="#contenido">{T['skip']}</a>
<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="{p.u(home)}" aria-label="{SITE['name']}, {T['home_label']}">{LOGO}<span class="brand-name">Downtown Life VIP<small>{T['small']}</small></span></a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="main-nav" aria-label="{T['menu']}">{icon('menu')}</button>
    <nav class="main-nav" id="main-nav" aria-label="{T['nav']}">
      <ul>{nav}{switch}</ul>
      <a class="btn btn-primary nav-book" href="{book_url()}" target="_blank" rel="noopener">{T['book_long']}</a>
    </nav>
    <a class="btn btn-primary btn-sm header-cta" href="{book_url()}" target="_blank" rel="noopener">{T['book']}</a>
  </div>
</header>
<main id="contenido">
{body}
</main>
<footer class="site-footer">
  <div class="container footer-grid">
    {footer_cols}
  </div>
  <div class="container footer-bottom"><span>© {year} Downtown Life VIP</span><span>{SITE['address']}</span></div>
</footer>
{wa_float}
<div class="mobile-book"><div><strong>Downtown Life VIP</strong><span>★ {SITE['rating'].replace(',', '.') if en else SITE['rating']} · {SITE['reviews']} {T['mobile_reviews']}</span></div><a class="btn btn-primary btn-sm" href="{book_url()}" target="_blank" rel="noopener">{T['book']}</a></div>
{wa_modal(p, lang)}
<script src="{p.u('assets/js/main.js')}" defer></script>
</body>
</html>
"""

def breadcrumbs(p, items, lang="es"):
    """items: lista de (ruta|None, etiqueta)."""
    li = []
    for t, label in items:
        li.append(f'<li><a href="{p.u(t)}">{esc(label)}</a></li>' if t is not None else f'<li aria-current="page">{esc(label)}</li>')
    schema = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": label, "item": SITE["url"] + "/" + (t if t is not None else p.path)}
        for i, (t, label) in enumerate(items)]}
    return f'<nav class="breadcrumbs" aria-label="{"Breadcrumb" if lang == "en" else "Migas de pan"}"><ol>{"".join(li)}</ol></nav>', schema

# ---------------------------------------------------------------- datos del apartamento
REVIEWS = [
    ("Faine", "septiembre de 2026", "Dayana es una excelente anfitriona, muy atenta a nuestras necesidades. Llegamos tarde y tenía todo previsto para recibirnos. Segunda vez que me hospedo y repetiría sin dudarlo."),
    ("Carlos Guillermo", "julio de 2026", "El lugar está como nuevo y la decoración le da su toque hogareño. Queda en Pampatar, con muchos restaurantes y cosas por hacer en la zona. 100 % recomendable."),
    ("Héctor", "agosto de 2026", "Un apartamento impecable, con unas vistas espectaculares e increíble ubicación. Todo excelente y la atención muy buena."),
    ("María", "septiembre de 2026", "Pensamos que tal vez las fotos fueran generadas por IA, pero no: el apartamento es exactamente así de bonito. La ubicación es genial, a poca distancia a pie de la playa."),
    ("Jesús", "junio de 2026", "Excelente ubicación, apartamento cómodo y seguro. Ideal para toda la familia, tranquilo y con restaurantes y club de playa cerca."),
    ("Rosdey", "junio de 2026", "Todo excelente, el apartamento impecable y las fotos tal cual lo describe. Dayana, increíble trato."),
]
AMENITIES = [
    ("Cocina y comedor", ["Cocina completa", "Nevera Whirlpool y congelador", "Fogones eléctricos Whirlpool de 4 hornillas", "Horno y microondas", "Cafetera de filtro y café", "Batidora y tostadora", "Bandeja de repostería", "Copas de vino", "Platos, boles, tazas y cubiertos", "Cazuelas, sartenes, aceite, sal y pimienta", "Comedor al aire libre", "Barbacoa"]),
    ("Dormitorios y lavandería", ["Ropa de cama de algodón egipcio", "Almohadas y mantas adicionales", "Cortinas o persianas opacas", "Vestidor y perchas", "Plancha", "Lavadora en el apartamento", "Secadora en el apartamento", "Tendedero para ropa", "Lavandería cercana"]),
    ("Baño", ["Agua caliente", "Champú y acondicionador", "Gel de ducha", "Secador de pelo", "Toallas, sábanas, jabón y papel higiénico", "Productos de limpieza", "Ducha exterior"]),
    ("Ocio, trabajo y clima", ["Wifi", "TV HD con Netflix, Prime Video y Disney+", "Zona de trabajo privada con silla ergonómica", "Soporte para portátil y protector de sobretensiones", "Libros y material de lectura", "Juegos de mesa", "Aire acondicionado tipo split"]),
    ("Playa y exteriores", ["Junto al agua", "Acceso a la playa", "Básicos de playa: toallas, sillas y sombrilla", "Balcón privado", "Mobiliario exterior", "Tumbonas", "Piscina compartida (6:00–22:00)", "Jacuzzi compartido (6:00–22:00)", "Acceso al resort (con importe adicional)", "Gimnasio en la zona"]),
    ("Familias", ["Parque infantil al aire libre", "Libros y juguetes para niños", "Trona", "Platos y cubiertos para niños", "Bañera para bebés (bajo petición)", "Protecciones en las ventanas", "Recomendaciones de canguros"]),
    ("Llegada y edificio", ["Entrada privada", "Ascensor", "Alojamiento de una sola planta", "Aparcamiento gratis en cochera (1 plaza)", "Aparcamiento gratuito en la calle", "Se permite dejar el equipaje", "Disponible para estancias largas (28 días o más)"]),
    ("Seguridad", ["Detector de humo", "Detector de monóxido de carbono", "Extintor de incendios", "Botiquín", "Cámara de seguridad en los exteriores"]),
]
GALLERY = [
    ("apartamento-pampatar-salon-con-vista-al-mar", "Salón con sofá azul y ventanal al mar"), ("apartamento-pampatar-cocina-equipada", "Cocina con isla de acabado marmolado"),
    ("apartamento-pampatar-dormitorio-principal", "Dormitorio principal con cama de matrimonio grande"), ("apartamento-pampatar-balcon-vista-al-mar", "Balcón con desayuno y vista al mar"),
    ("piscina-residencial-pampatar-isla-margarita", "Piscina del residencial"), ("apartamento-pampatar-salon-y-balcon", "Salón con salida al balcón"),
    ("apartamento-margarita-sofa-cama-salon", "Sofá cama del salón"), ("apartamento-pampatar-cocina-isla-marmol", "Cocina vista desde la entrada"), ("apartamento-margarita-electrodomesticos-cocina", "Pequeños electrodomésticos de la cocina"),
    ("apartamento-margarita-cafetera-desayuno", "Rincón del café"), ("apartamento-pampatar-dormitorio-salida-balcon-mar", "Salida al balcón desde el dormitorio"), ("apartamento-pampatar-dormitorio-principal-ventana-mar", "Dormitorio principal con vista"),
    ("apartamento-pampatar-segundo-dormitorio-dos-camas", "Segundo dormitorio con dos camas individuales"), ("apartamento-margarita-habitacion-camas-individuales", "Camas individuales del segundo dormitorio"),
    ("apartamento-pampatar-bano-completo", "Baño con lavabo de piedra y espejo iluminado"), ("apartamento-pampatar-segundo-bano", "Segundo baño completo"), ("apartamento-margarita-zona-de-trabajo-teletrabajo", "Zona de trabajo con silla ergonómica"),
    ("apartamento-margarita-lavadora-secadora", "Lavadora y secadora"), ("desayuno-balcon-vista-mar-caribe-pampatar", "Desayuno en el balcón"), ("vista-al-mar-desde-balcon-pampatar", "Vista del mar desde el balcón"),
    ("balcon-de-noche-pampatar-margarita", "Balcón de noche"), ("jacuzzi-residencial-pampatar", "Jacuzzi del residencial"), ("parque-infantil-residencial-pampatar", "Parque infantil y comedor exterior"),
    ("zona-barbacoa-residencial-pampatar", "Zona de barbacoa"), ("residencial-frente-al-mar-pampatar", "Edificio del residencial"), ("vista-aerea-playa-pampatar-isla-margarita", "Vista aérea de la playa frente al edificio"),
    ("club-de-playa-downtownbeach-margarita", "Club de playa Downtownbeach"), ("cancha-de-padel-pampatar", "Cancha de pádel"), ("atardecer-mar-caribe-isla-margarita", "Atardecer sobre el mar Caribe"),
]

def schema_rental():
    return {
        "@context": "https://schema.org", "@type": "VacationRental",
        "name": "Downtown Life VIP frente al mar Caribe",
        "description": "Apartamento de 2 dormitorios y 2 baños frente al mar en Pampatar, Isla de Margarita, para hasta 5 viajeros.",
        "url": SITE["url"] + "/apartamento/",
        "image": [f"{SITE['url']}/fotos/{n}.webp" for n, _ in GALLERY[:6]],
        "address": {"@type": "PostalAddress", "addressLocality": "Pampatar",
                    "addressRegion": "Nueva Esparta", "addressCountry": "VE"},
        "aggregateRating": {"@type": "AggregateRating", "ratingValue": SITE["rating_num"], "reviewCount": SITE["reviews"], "bestRating": 5},
        "containsPlace": {"@type": "Accommodation", "additionalType": "EntirePlace", "numberOfBedrooms": 2,
                          "numberOfBathroomsTotal": 2, "occupancy": {"@type": "QuantitativeValue", "value": 5},
                          "amenityFeature": [{"@type": "LocationFeatureSpecification", "name": n, "value": True}
                                             for n in ["Wifi", "Aire acondicionado", "Piscina", "Acceso a la playa", "Aparcamiento gratis", "Lavadora", "Cocina"]]},
        "checkinTime": "16:00", "checkoutTime": "10:00",
    }

FAQ = [
    ("¿Cómo reservo el apartamento?", "Las reservas se hacen a través de nuestro anuncio en Airbnb. Ahí ves las fechas libres y el precio final, y pagas de forma segura."),
    ("¿A qué hora es la llegada y la salida?", "La llegada es a partir de las 16:00 y la salida antes de las 10:00. Si llegas antes o te vas más tarde, puedes dejar tu equipaje."),
    ("¿Cuántas personas pueden alojarse?", "Hasta 5 viajeros: una cama de matrimonio grande en el dormitorio principal, dos camas individuales en el segundo dormitorio y un sofá cama en el salón."),
    ("¿Está cerca de la playa?", "Sí. El apartamento está frente al mar, justo enfrente del club de playa Downtownbeach Margarita, y tiene acceso a la playa."),
    ("¿Hay aparcamiento?", "Sí, una plaza gratis en la cochera del edificio y aparcamiento gratuito en la calle."),
    ("¿Se puede teletrabajar?", "Sí. Hay wifi y una zona de trabajo privada con silla ergonómica, soporte para portátil y protector de sobretensiones."),
    ("¿Hay descuentos por estancias largas?", "Sí: 10 % de descuento semanal y 10 % mensual. Aceptamos estancias de 3 a 60 noches."),
    ("¿Se puede fumar?", "No. El apartamento es un espacio libre de humo, también en los balcones."),
    ("¿Cuál es la política de cancelación?", "Semiestricta: reembolso completo si cancelas hasta 30 días antes de la llegada, del 50 % entre 30 y 7 días antes, y sin reembolso en los últimos 7 días. Si reservas con al menos 7 días de antelación, tienes además 24 horas desde la confirmación para cancelar gratis."),
    ("¿Es seguro pagar?", "Sí. El pago se hace a través de Airbnb, que lo protege con AirCover para huéspedes."),
]

CANCEL_SHORT = [
    ("Hasta 30 días antes de la llegada", "Reembolso completo."),
    ("Entre 30 y 7 días antes", "Reembolso del 50 %."),
    ("Menos de 7 días antes", "Sin reembolso de las noches."),
]
def cancel_block():
    rows = "".join(f"<tr><th>{a}</th><td>{b}</td></tr>" for a, b in CANCEL_SHORT)
    return f"""<h3>Política de cancelación: semiestricta</h3>
<p>Para estancias de menos de 28 noches, si cancelas:</p>
<table class="info-table">{rows}</table>
<p class="small-note">Además, si reservas con al menos 7 días de antelación, Airbnb te da 24 horas desde la confirmación para cancelar con reembolso completo. En estancias de 28 noches o más, el reembolso es completo hasta 30 días antes de la llegada; después, se cobran las noches ya disfrutadas más 30 noches. Al reservar, Airbnb también te ofrece una tarifa no reembolsable un 10 % más barata. Las condiciones exactas de tu reserva aparecen siempre en Airbnb antes de pagar.</p>"""

# ---------------------------------------------------------------- artículos
def parse_post(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    md = markdown.Markdown(extensions=["toc", "tables", "attr_list"], extension_configs={"toc": {"toc_depth": "2"}})
    body = md.convert(m.group(2))
    words = len(re.sub(r"<[^>]+>", " ", body).split())
    faq = []
    fm = re.search(r"^## (?:Preguntas frecuentes|Frequently asked questions)\s*$(.*?)(?=^## |\Z)", m.group(2), re.S | re.M)
    if fm:
        for q, a in re.findall(r"^### (.+?)\n+(.+?)(?=^### |\Z)", fm.group(1), re.S | re.M):
            a = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", a).replace("**", "").strip()
            faq.append((q.strip(), " ".join(a.split())))
    meta.update(html=body, toc=md.toc_tokens, minutes=max(2, math.ceil(words / 200)), words=words, faq=faq)
    return meta

def load_posts(lang="es"):
    posts = []
    folder = ROOT / "content" / "posts" / ("en" if lang == "en" else "")
    for f in sorted(folder.glob("*.md")):
        if f.name.startswith("_"):
            continue
        p = parse_post(f)
        if p.get("draft", "no") == "si":
            continue
        p["lang"] = lang
        posts.append(p)
    posts.sort(key=lambda x: (x["date"], x.get("order", "0")), reverse=True)
    return posts

def post_card(p, post):
    en = post.get("lang") == "en"
    prefix = "en/blog/" if en else "blog/"
    return f"""<a class="post-card" href="{p.u(prefix + post['slug'] + '/')}"{' lang="en"' if en and p.path[:3] != 'en/' else ''}>
  {img(p, post['cover'], post.get('cover_alt'), sizes="(max-width: 600px) 100vw, 33vw", lang=post.get('lang', 'es'))}
  <div class="body">
    <div class="meta"><span class="cat">{cat_label(post['category'], post.get('lang', 'es'))}</span><span>{post['minutes']} {'min read' if en else 'min de lectura'}</span></div>
    <h3>{esc(post['title'])}</h3>
    <p>{esc(post['description'])}</p>
    <span class="more">{'Read article' if en else 'Leer artículo'} →</span>
  </div>
</a>"""

# ---------------------------------------------------------------- páginas
HERO_SLIDES = [
    ("apartamento-pampatar-salon-con-vista-al-mar", "Salón del apartamento con ventanal al mar"),
    ("vista-al-mar-desde-balcon-pampatar", "Vista del mar, la playa y las palmeras desde el balcón"),
    ("piscina-residencial-pampatar-isla-margarita", "Piscina del residencial en Pampatar"),
    ("atardecer-desde-balcon-pampatar", "Atardecer sobre el mar Caribe desde el balcón"),
    ("club-de-playa-downtownbeach-margarita", "Club de playa Downtownbeach frente al apartamento"),
    ("apartamento-pampatar-dormitorio-principal-ventana-mar", "Dormitorio principal con vista al mar"),
]
def hero_slides(p):
    """Fotos extra de la portada: se cargan después con JavaScript para no frenar la página."""
    out = []
    for n, alt in HERO_SLIDES:
        w, h = dims(n)
        if n not in p.images:
            p.images.append(n)
        out.append(f'<img data-src="{p.u("fotos/" + n + ".webp")}" data-srcset="{p.u("fotos/" + n + "-640.webp")} 640w, {p.u("fotos/" + n + ".webp")} {w}w" sizes="100vw" width="{w}" height="{h}" alt="{esc(alt)}" decoding="async">')
    return "".join(out)

def page_home(posts):
    p = Page("")
    facts = "".join(f'<li>{icon(i)}<div><strong>{a}</strong><span>{b}</span></div></li>' for i, a, b in [
        ("users", "5 viajeros", "Ideal para familias"), ("bed", "2 dormitorios", "4 camas"), ("bath", "2 baños", "Completos"), ("waves", "Frente al mar", "Acceso a la playa")])
    features = "".join(f'<div class="feature">{icon(i)}<h3>{a}</h3><p>{b}</p></div>' for i, a, b in [
        ("sun", "Balcón con vista al mar", "Desayuna frente al Caribe"), ("pool", "Piscina y jacuzzi", "Abiertos todo el año, de 6:00 a 22:00"),
        ("snow", "Aire acondicionado", "Sistema split en el apartamento"), ("wifi", "Wifi y zona de trabajo", "Silla ergonómica y soporte para portátil"),
        ("kitchen", "Cocina completa", "Electrodomésticos Whirlpool"), ("washer", "Lavadora y secadora", "Dentro del apartamento"),
        ("car", "Aparcamiento gratis", "Una plaza en la cochera"), ("shield", "Edificio seguro", "Ascensor y entrada privada")])
    reviews = "".join(f"""<article class="review"><div class="stars" aria-label="5 de 5 estrellas">{icon('star')*5}</div>
<blockquote>“{esc(t)}”</blockquote><footer><span class="avatar" aria-hidden="true">{n[0]}</span><div><strong>{esc(n)}</strong>{d}</div></footer></article>""" for n, d, t in REVIEWS[:3])
    latest = "".join(post_card(p, x) for x in posts[:3])
    body = f"""
<section class="hero">
  <div class="hero-media" data-slideshow>{img(p, 'apartamento-pampatar-balcon-vista-al-mar', 'Balcón del apartamento con desayuno frente al mar Caribe', cls='is-active', sizes='100vw', lazy=False)}{hero_slides(p)}</div>
  <div class="container"><div class="hero-content">
    <span class="rating">{icon('star')} {SITE['rating']} · {SITE['reviews']} evaluaciones en Airbnb</span>
    <h1>Tu apartamento frente al mar en Pampatar</h1>
    <p class="lead"><span class="lead-main">Moderno, totalmente equipado y con balcón al Caribe.</span><span class="lead-sub">Justo enfrente del club de playa Downtownbeach, para hasta 5 viajeros.</span></p>
    <div class="hero-actions">
      <a class="btn btn-primary" href="{book_url()}" target="_blank" rel="noopener">Ver disponibilidad</a>
      <a class="btn btn-outline" href="{p.u('apartamento/')}">Ver el apartamento</a>
    </div>
  </div></div>
</section>
<div class="container"><ul class="facts">{facts}</ul></div>

<section class="section intro">
  <div class="container">
    <div class="intro-head">
      <h2>Frente al mar, en Pampatar</h2>
      <p>Un apartamento luminoso con balcón al Caribe, frente al Tibisay Hotel Boutique y al club de playa Downtownbeach. Cerca de los mejores restaurantes y centros comerciales de la isla.</p>
    </div>
    <div class="intro-photos">
      <figure>{img(p, 'apartamento-pampatar-salon-con-vista-al-mar', 'Salón del apartamento con sofá azul y ventanal al mar', sizes='(max-width: 760px) 100vw, 33vw')}<figcaption>Salón con vista al mar y sofá cama</figcaption></figure>
      <figure>{img(p, 'apartamento-pampatar-dormitorio-principal', 'Dormitorio principal con cama de matrimonio grande', sizes='(max-width: 760px) 100vw, 33vw')}<figcaption>Dormitorio principal con ropa de algodón egipcio</figcaption></figure>
      <figure>{img(p, 'desayuno-balcon-vista-mar-caribe-pampatar', 'Desayuno en el balcón frente al mar Caribe', sizes='(max-width: 760px) 100vw, 33vw')}<figcaption>Balcón privado para desayunar frente al Caribe</figcaption></figure>
    </div>
    <p class="intro-link"><a class="btn btn-outline" href="{p.u('apartamento/')}">Ver todas las fotos</a></p>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head"><div><span class="eyebrow">Opiniones</span><h2>Lo que dicen nuestros huéspedes</h2></div>
      <div class="score"><span class="big">{SITE['rating']}</span><span>Superanfitriona · {SITE['reviews']} evaluaciones<br>Entre el 1 % de alojamientos mejor valorados</span></div></div>
    <div class="reviews">{reviews}</div>
    <p style="margin-top:20px"><a href="{book_url()}" target="_blank" rel="noopener">Leer todas las opiniones en Airbnb →</a></p>
  </div>
</section>

<section class="section alt">
  <div class="container">
    <div class="section-head"><div><span class="eyebrow">Guía de Margarita</span><h2>Qué hacer en la isla</h2><p>Playas, historia, excursiones y consejos prácticos para aprovechar tu viaje.</p></div><a class="btn btn-outline btn-sm" href="{p.u('blog/')}">Ver todos los artículos</a></div>
    <div class="posts">{latest}</div>
  </div>
</section>

<section class="cta-band"><div class="container"><div><h2>¿Te vienes a Margarita?</h2><p>Consulta las fechas disponibles y reserva en un minuto.</p></div><a class="btn btn-sun" href="{book_url()}" target="_blank" rel="noopener">Reservar en Airbnb</a></div></section>
"""
    site_schema = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE["name"], "url": SITE["url"] + "/", "inLanguage": "es"}
    return p, layout(p, "Apartamento frente al mar en Pampatar | Downtown Life VIP",
                     "Apartamento de 2 dormitorios frente al mar en Pampatar, Isla de Margarita. Balcón al Caribe, piscina, wifi y aparcamiento. Superanfitriona con 5,0 en Airbnb.",
                     body, active="", schema=[site_schema, schema_rental()])

def review_cards(items):
    return "".join(f"""<article class="review"><div class="stars" aria-label="5 de 5 estrellas">{icon('star')*5}</div>
<blockquote>“{esc(t)}”</blockquote><footer><span class="avatar" aria-hidden="true">{n[0]}</span><div><strong>{esc(n)}</strong>{d}</div></footer></article>""" for n, d, t in items)

def page_apartment():
    p = Page("apartamento/")
    bc, bc_schema = breadcrumbs(p, [("", "Inicio"), (None, "El apartamento")])
    gal = []
    for i, (n, alt) in enumerate(GALLERY):
        cls = ' class="wide"' if i == 0 else ""
        gal.append(f'<a{cls} href="{p.u("fotos/" + n + ".webp")}" data-lightbox>{img(p, n, None, sizes="(max-width: 760px) 50vw, 25vw")}</a>')
    amen = "".join(f'<section><h3>{g}</h3><ul>{"".join(f"<li>{icon("check")}<span>{esc(x)}</span></li>" for x in items)}</ul></section>' for g, items in AMENITIES)
    faq = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in FAQ)
    faq_schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}
    maps = SITE["maps"]
    wa_btn = ('<a class="btn btn-wa" style="width:100%;margin-top:10px" href="' + wa_link() + '" target="_blank" rel="noopener">' + WA_SVG + ' Pregúntanos por WhatsApp</a>') if wa_link() else ''
    body = f"""
<section class="page-hero"><div class="container">{bc}
  <h1>Downtown Life VIP frente al mar Caribe</h1>
  <p>Apartamento entero en un complejo residencial de Pampatar, Isla de Margarita. 2 dormitorios, 4 camas, 2 baños y balcón con vista al mar para hasta 5 viajeros.</p>
</div></section>

<!-- 1. Fotos -->
<section class="section" style="padding-top:36px;padding-bottom:40px">
  <div class="container">
    <div class="gallery">{''.join(gal[:9])}</div>
    <div hidden>{''.join(gal[9:])}</div>
    <div class="after-gallery">
      <a href="{p.u('fotos/' + GALLERY[0][0] + '.webp')}" onclick="this.closest('.container').querySelector('.gallery a').click();return false;">Ver las {len(GALLERY)} fotos</a>
      <a class="btn btn-primary" href="{book_url()}" target="_blank" rel="noopener">Ver disponibilidad y precio</a>
    </div>
  </div>
</section>

<!-- 2. Disponibilidad y precio -->
<section class="section" style="padding-top:0">
  <div class="container split" style="align-items:start">
    <div>
      <h2>Sobre el apartamento</h2>
      <p>Disfruta de una estadía inolvidable en este apartamento moderno y totalmente equipado, ubicado en la mejor y más exclusiva zona de la isla, frente al mar y al Tibisay Hotel Boutique, cerca de los principales atractivos turísticos. A pocos kilómetros tienes los mejores centros comerciales y restaurantes.</p>
      <p>Justo enfrente está el club de playa Downtownbeach Margarita, donde podrás bañarte en el mar y disfrutar de sus actividades recreativas y deportivas, entre ellas pádel, beach tennis y kayak.</p>
      <h3 style="margin-top:28px">Distribución</h3>
      <table class="info-table">
        <tr><th>Dormitorio 1</th><td>Cama de matrimonio grande y vestidor</td></tr>
        <tr><th>Dormitorio 2</th><td>Dos camas individuales</td></tr>
        <tr><th>Salón</th><td>Sofá cama, Smart TV y salida al balcón</td></tr>
        <tr><th>Baños</th><td>Dos baños completos</td></tr>
        <tr><th>Balcón</th><td>Privado, con comedor exterior y vista al mar</td></tr>
      </table>
    </div>
    <aside class="book-card" id="reservar">
      <div class="in">
        <h3>Disponibilidad y precio</h3>
        <p>Las fechas libres y el precio final, con todos los gastos incluidos, se ven en Airbnb antes de pagar. Reserva con confirmación inmediata.</p>
        <table class="info-table" style="margin-bottom:16px">
          <tr><th>Llegada</th><td>A partir de las 16:00</td></tr>
          <tr><th>Salida</th><td>Antes de las 10:00</td></tr>
          <tr><th>Estancia</th><td>De 3 a 60 noches</td></tr>
          <tr><th>Descuentos</th><td>10 % semanal y 10 % mensual</td></tr>
          <tr><th>Cancelación</th><td>Semiestricta: reembolso completo hasta 30 días antes. <a href="#normas">Ver detalles</a></td></tr>
        </table>
        <a class="btn btn-primary" href="{book_url()}" target="_blank" rel="noopener" style="width:100%">Ver fechas libres en Airbnb</a>
        {wa_btn}
        <p class="small-note" style="margin-top:12px">Pago seguro a través de Airbnb, protegido por AirCover para huéspedes.</p>
      </div>
    </aside>
  </div>
</section>

<!-- 3. Opiniones, junto al botón de reservar -->
<section class="section alt">
  <div class="container">
    <div class="section-head"><div><span class="eyebrow">Opiniones</span><h2>{SITE['rating']} de 5 en {SITE['reviews']} evaluaciones</h2><p>Superanfitriona en Airbnb y entre el 1 % de alojamientos mejor valorados.</p></div>
      <a class="btn btn-primary" href="{book_url()}" target="_blank" rel="noopener">Reservar en Airbnb</a></div>
    <div class="reviews">{review_cards(REVIEWS)}</div>
    <p style="margin-top:20px"><a href="{book_url()}" target="_blank" rel="noopener">Leer todas las opiniones en Airbnb</a></p>
  </div>
</section>

<section class="section" id="comodidades">
  <div class="container">
    <div class="section-head"><div><span class="eyebrow">Comodidades</span><h2>68 comodidades incluidas</h2></div></div>
    <div class="amenities-wrap is-collapsed" data-collapse><div class="amenities">{amen}</div>
    <button type="button" class="btn btn-outline btn-sm amenities-toggle" data-collapse-btn aria-expanded="false">Ver las 68 comodidades</button></div>
  </div>
</section>

<!-- 4. Normas y cancelación -->
<section class="section alt" id="normas">
  <div class="container split" style="align-items:start">
    <div>
      <span class="eyebrow">Normas de la casa</span>
      <h2>Antes de llegar</h2>
      <table class="info-table">
        <tr><th>Viajeros</th><td>Máximo 5</td></tr>
        <tr><th>Fumar</th><td>No está permitido, tampoco en los balcones</td></tr>
        <tr><th>Huéspedes</th><td>Solo pueden alojarse las personas registradas en la reserva</td></tr>
        <tr><th>Cuidado de la casa</th><td>Te pedimos no sentarte con ropa mojada en el sofá ni en las sillas</td></tr>
        <tr><th>Seguridad</th><td>Detectores de humo y de monóxido de carbono, extintor, botiquín y cámara en los exteriores</td></tr>
      </table>
    </div>
    <div>{cancel_block()}</div>
  </div>
</section>

<section class="section">
  <div class="container split" style="align-items:start">
    <div>
      <span class="eyebrow">Ubicación</span>
      <h2>Pampatar, Isla de Margarita</h2>
      <p>En Pampatar, frente al mar y a pocos minutos del casco histórico, de las playas y de los mejores restaurantes de la isla.</p>
      <p class="small-note">Por tu seguridad y la de nuestros huéspedes, igual que en Airbnb, la dirección exacta te la enviamos una vez confirmada la reserva.</p>
      <p style="margin-top:16px"><a class="btn btn-outline" href="{maps}" target="_blank" rel="noopener">{icon('pin')} Ver la zona en el mapa</a></p>
      <p style="margin-top:16px">¿Qué hacer en la zona? Lee <a href="{p.u('blog/que-ver-en-pampatar/')}">qué ver en Pampatar</a> y <a href="{p.u('blog/mejores-playas-isla-margarita/')}">las mejores playas de Margarita</a>.</p>
    </div>
    <div>{img(p, 'vista-aerea-playa-pampatar-isla-margarita', 'Vista aérea de la playa y el edificio en Pampatar')}</div>
  </div>
</section>

<section class="section alt" id="preguntas">
  <div class="container">
    <div class="section-head"><div><span class="eyebrow">Preguntas frecuentes</span><h2>Resolvemos tus dudas</h2></div></div>
    <div class="faq">{faq}</div>
  </div>
</section>

<section class="cta-band"><div class="container"><div><h2>Reserva tu estancia en Pampatar</h2><p>Consulta las fechas libres y el precio final en Airbnb.</p></div><a class="btn btn-sun" href="{book_url()}" target="_blank" rel="noopener">Reservar en Airbnb</a></div></section>
"""
    return p, layout(p, "Fotos, comodidades y normas del apartamento",
                     "Apartamento entero frente al mar en Pampatar: 2 dormitorios, 4 camas, 2 baños, balcón con vista al Caribe, piscina, jacuzzi, wifi y aparcamiento gratis.",
                     body, active="apartamento/", schema=[schema_rental(), faq_schema, bc_schema])

def page_about():
    p = Page("sobre-dayana/")
    bc, bc_schema = breadcrumbs(p, [("", "Inicio"), (None, "Sobre mí")])
    wa = f'<a class="btn btn-wa" href="{wa_link()}" target="_blank" rel="noopener">{WA_SVG} Escribir por WhatsApp</a>' if wa_link() else ""
    body = f"""
<section class="page-hero"><div class="container">{bc}
  <div class="about-hero">
    <div class="profile-ring">{img(p, 'dayana-anfitriona-pampatar', 'Dayana, anfitriona de Downtown Life VIP en Pampatar', cls='profile-photo', sizes='(max-width: 600px) 104px, 152px', lazy=False)}</div>
    <div><h1>¡Hola, soy Dayana!</h1>
    <p>Tu anfitriona de confianza en Airbnb ;)</p></div>
  </div>
</div></section>

<section class="section">
  <div class="container split" style="align-items:start">
    <div>
      <h2>Te voy a contar sobre este proyecto tan especial</h2>
      <p>Downtown Life VIP empezó como un sueño compartido con mi mamá. Lo imaginamos juntas, elegimos cada detalle con cariño y lo convertimos en un lugar al que daba gusto llegar. Hoy ella ya no está, pero este apartamento sigue teniendo mucho de ella. Por eso, para mí no es solo un alojamiento: es un proyecto muy especial que cuido con todo mi corazón.</p>
      <p>Lo que más deseo es que, al abrir la puerta, te sientas en tu propia casa en Margarita. Que descanses de verdad, que encuentres todo lo que necesitas y que tu estancia sea cómoda, tranquila y muy agradable.</p>
      <p>Y ojalá, al irte, te lleves contigo lo mejor de Margarita.</p>
      <p>Gracias por elegirnos. Será un placer recibirte.</p>
      <p class="signature">Dayana</p>
      <ul class="trust-stats">
        <li><strong>{SITE['rating']}</strong><span>valoración media</span></li>
        <li><strong>{SITE['reviews']}</strong><span>evaluaciones</span></li>
        <li><strong>{SITE['years']} años</strong><span>como anfitriona</span></li>
      </ul>
    </div>
    <div class="memorial-col"><figure class="memorial">{img(p, 'dayana-con-su-mama-margarita', 'Dayana con su mamá en Isla de Margarita', sizes='(max-width: 860px) 80vw, 380px')}<figcaption>En memoria de mi mamá.<br>Este proyecto también es suyo.</figcaption></figure></div>
  </div>
</section>

<section class="section alt">
  <div class="container trust-grid">
    <div>
      <h2>Cómo se reserva y se paga</h2>
      <p>Todas las reservas se hacen a través de nuestro anuncio en Airbnb. Ahí ves las fechas libres y el precio final antes de pagar, y recibes la confirmación al momento.</p>
      <p>El pago lo gestiona Airbnb, que lo protege con <strong>AirCover para huéspedes</strong>: si hubiera un problema grave con la reserva, Airbnb te ayuda a encontrar otro alojamiento o te devuelve el dinero.</p>
    </div>
    <div>
      <h2>Si algo no sale bien</h2>
      <p>Escríbeme por los mensajes de Airbnb o por WhatsApp y lo resolvemos lo antes posible. Si lo necesitas, el servicio de ayuda de Airbnb está disponible las 24 horas.</p>
      <p>{wa}</p>
    </div>
  </div>
</section>

<section class="section">
  <div class="container split" style="align-items:start">
    <div>{cancel_block()}</div>
    <div>
      <h3>Lo que dicen los huéspedes</h3>
      <div class="reviews one-col">{review_cards(REVIEWS[:2])}</div>
    </div>
  </div>
</section>

<section class="cta-band"><div class="container"><div><h2>¿Te vienes a Margarita?</h2><p>Consulta las fechas libres y el precio final en Airbnb.</p></div><a class="btn btn-sun" href="{book_url()}" target="_blank" rel="noopener">Ver disponibilidad</a></div></section>
"""
    person = {"@context": "https://schema.org", "@type": "AboutPage", "name": "Sobre Dayana, anfitriona de Downtown Life VIP", "url": SITE["url"] + "/sobre-dayana/",
              "mainEntity": {"@type": "Person", "name": SITE["host"], "jobTitle": "Anfitriona de Downtown Life VIP"}}
    return p, layout(p, "Sobre Dayana, tu anfitriona en Pampatar",
                     "La historia de Downtown Life VIP, un proyecto creado por Dayana y su mamá en Pampatar. Cómo se reserva, cómo se paga y la política de cancelación.",
                     body, active="sobre-dayana/", schema=[person, bc_schema])

def page_blog(posts, cat=None):
    path = "blog/" if not cat else f"blog/categoria/{cat}/"
    p = Page(path)
    items = [("", "Inicio"), ("blog/", "Guía de Margarita")] if not cat else [("", "Inicio"), ("blog/", "Guía de Margarita"), (None, CATEGORIES[cat])]
    if not cat:
        items[-1] = (None, "Guía de Margarita")
    bc, bc_schema = breadcrumbs(p, items)
    chosen = [x for x in posts if not cat or x["category"] == cat]
    catnav = f'<a href="{p.u("blog/")}"{" aria-current=\"page\"" if not cat else ""}>Todos</a>' + "".join(
        f'<a href="{p.u("blog/categoria/" + k + "/")}"{" aria-current=\"page\"" if cat == k else ""}>{v}</a>'
        for k, v in CATEGORIES.items() if any(x["category"] == k for x in posts))
    title = "Guía de Margarita: qué hacer en la isla" if not cat else f"{CATEGORIES[cat]} en Isla de Margarita"
    intro = ("Playas, historia, excursiones, gastronomía y consejos prácticos para tu viaje a Isla de Margarita, escritos por la anfitriona de Downtown Life VIP en Pampatar."
             if not cat else f"Artículos sobre {CATEGORIES[cat].lower()} en Isla de Margarita: recomendaciones y consejos para tu viaje.")
    cards = "".join(post_card(p, x) for x in chosen) or "<p>Pronto publicaremos artículos en esta categoría.</p>"
    body = f"""
<section class="page-hero"><div class="container">{bc}<h1>{esc(title)}</h1><p>{esc(intro)}</p>{'' if cat else '<a class="lang-pill" href="' + p.u('en/blog/') + '" hreflang="en" lang="en">Read the guide in English →</a>'}</div></section>
<section class="section"><div class="container"><nav class="cat-nav" aria-label="Categorías">{catnav}</nav><h2 class="sr-only">Artículos</h2><div class="posts">{cards}</div></div></section>
<section class="cta-band"><div class="container"><div><h2>Tu base en Margarita</h2><p>Un apartamento frente al mar en Pampatar para descansar entre excursión y excursión.</p></div><a class="btn btn-sun" href="{book_url()}" target="_blank" rel="noopener">Ver disponibilidad</a></div></section>
"""
    blog_schema = {"@context": "https://schema.org", "@type": "Blog", "name": "Guía de Margarita", "url": SITE["url"] + "/blog/", "inLanguage": "es"}
    alts = [("es", "blog/"), ("en", "en/blog/")] if not cat else None
    return p, layout(p, title, intro, body, active="blog/", schema=[blog_schema, bc_schema], alternates=alts)

def page_post(post, posts, pair=None):
    """pair: el artículo equivalente en el otro idioma (o None)."""
    en = post.get("lang") == "en"
    lang = "en" if en else "es"
    base = "en/blog/" if en else "blog/"
    p = Page(f"{base}{post['slug']}/")
    cat = post["category"]
    if en:
        bc, bc_schema = breadcrumbs(p, [("en/blog/", "Margarita guide"), (None, post["title"])], lang)
    else:
        bc, bc_schema = breadcrumbs(p, [("", "Inicio"), ("blog/", "Guía de Margarita"), (f"blog/categoria/{cat}/", CATEGORIES[cat]), (None, post["title"])])
    T = {
        "toc": "In this article" if en else "En este artículo",
        "pub": "Published" if en else "Publicado el",
        "upd": "Updated" if en else "Actualizado el",
        "min": "min read" if en else "min de lectura",
        "by": f"By {SITE['host']}, your host in Pampatar" if en else f"Por {SITE['host']}, anfitriona en Pampatar",
        "cta_t": "Looking for a place to stay in Pampatar?" if en else "¿Buscas dónde quedarte en Pampatar?",
        "cta_p": f"Beachfront apartment with pool and free parking. ★ {SITE['rating'].replace(',', '.')} on Airbnb." if en else f"Apartamento frente al mar, con piscina y aparcamiento. ★ {SITE['rating']} en Airbnb.",
        "cta_b": "Check availability" if en else "Ver disponibilidad",
        "author": (f"<strong>{SITE['host']}</strong> is the host of Downtown Life VIP in Pampatar and an Airbnb Superhost with {SITE['reviews']} five-star reviews. In this guide she shares what she recommends to her guests."
                   if en else f"<strong>{SITE['host']}</strong> es la anfitriona de Downtown Life VIP en Pampatar y Superanfitriona en Airbnb con {SITE['reviews']} evaluaciones de 5 estrellas. En esta guía comparte lo que recomienda a sus huéspedes."),
        "side_t": "Stay by the sea" if en else "Quédate frente al mar",
        "side_p": "2 bedrooms, a balcony over the Caribbean and a pool in Pampatar. Up to 5 guests." if en else "2 dormitorios, balcón al Caribe y piscina en Pampatar. Hasta 5 viajeros.",
        "side_b": "Book" if en else "Reservar",
        "wa": (("Questions about your trip?", "Message us on WhatsApp and we will help you plan your days in Margarita.", "Message us on WhatsApp") if en
               else ("¿Preguntas sobre tu viaje?", "Escríbenos por WhatsApp y te ayudamos a organizar tus días en Margarita.", "Escribir por WhatsApp")),
        "more_e": "Keep reading" if en else "Sigue leyendo",
        "more_h": "More ideas for your trip" if en else "Más ideas para tu viaje",
        "pair": "Lee este artículo en español" if en else "Read this article in English",
    }
    toc = ""
    if len(post["toc"]) >= 3:
        toc = f'<nav class="toc" aria-label="{T["toc"]}"><strong>{T["toc"]}</strong><ol>' + "".join(
            f'<li><a href="#{t["id"]}">{re.sub(r"^[0-9]+[.] *", "", t["name"])}</a></li>' for t in post["toc"]) + "</ol></nav>"
    related = [x for x in posts if x["slug"] != post["slug"] and x["category"] == cat][:3]
    related += [x for x in posts if x["slug"] != post["slug"] and x not in related][: 3 - len(related)]
    rel_html = "".join(post_card(p, x) for x in related)
    def _fig(m):
        return f'<figure>{img(p, m.group(2), m.group(1) or None, sizes="(max-width: 980px) 100vw, 70vw", lang=lang)}<figcaption class="caption">{m.group(1)}{credit_html(m.group(2), lang)}</figcaption></figure>'
    body_html = re.sub(r'<p><img alt="([^"]*)" src="fotos/([a-z0-9-]+)\.webp" ?/?></p>', _fig, post["html"])
    if PREVIEW:
        body_html = re.sub(r'href="(\.\./[^"#]*?/)"', r'href="\1index.html"', body_html)
    body_html = body_html.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    upd = post.get("updated", post["date"])
    alternates = None
    pair_link = ""
    if pair:
        other_path = ("blog/" if en else "en/blog/") + pair["slug"] + "/"
        alternates = [(lang, p.path), ("es" if en else "en", other_path)]
        pair_link = f'<a class="lang-pill" href="{p.u(other_path)}" hreflang="{"es" if en else "en"}" lang="{"es" if en else "en"}">{T["pair"]} →</a>'
    body = f"""
<article>
<section class="page-hero"><div class="container">{bc}
  <div class="article-head"><span class="eyebrow">{cat_label(cat, lang)}</span><h1>{esc(post['title'])}</h1>
  <div class="meta"><span>{icon('calendar')} {T['pub']} <time datetime="{post['date']}">{fdate(post['date'], lang)}</time></span>{('<span>' + T['upd'] + ' <time datetime="' + upd + '">' + fdate(upd, lang) + '</time></span>') if upd != post['date'] else ''}<span>{icon('clock')} {post['minutes']} {T['min']}</span><span>{T['by']}</span></div>{pair_link}</div>
</div></section>
<div class="container section" style="padding-top:8px">
  <div class="article-layout">
    <div>
      <figure class="article-cover" style="margin-left:0;margin-right:0">{img(p, post['cover'], post.get('cover_alt'), sizes='(max-width: 980px) 100vw, 70vw', lazy=False, lang=lang)}</figure>
      <p class="caption">{esc(post['cover_alt'])}{credit_html(post['cover'], lang)}</p>
      {toc}
      <div class="prose">{body_html}</div>
      {share_block(p, post, lang)}
      <div class="cta-inline"><div><strong>{T['cta_t']}</strong><p>{T['cta_p']}</p></div><a class="btn btn-sun" href="{book_url()}" target="_blank" rel="noopener">{T['cta_b']}</a></div>
      <div class="author"><span class="avatar" aria-hidden="true">D</span><p>{T['author']}</p></div>
    </div>
    <aside class="sidebar">
      <div class="book-card">{img(p, 'apartamento-pampatar-balcon-vista-al-mar', 'Balcony with breakfast and Caribbean Sea view at the apartment in Pampatar' if en else None, sizes='300px')}
        <div class="in"><h3>{T['side_t']}</h3><p>{T['side_p']}</p><a class="btn btn-primary" href="{book_url()}" target="_blank" rel="noopener">{T['side_b']}</a></div></div>
      {wa_card(*T['wa'])}
    </aside>
  </div>
</div>
</article>
<section class="section alt"><div class="container"><div class="section-head"><div><span class="eyebrow">{T['more_e']}</span><h2>{T['more_h']}</h2></div></div><div class="posts">{rel_html}</div></div></section>
"""
    cw, ch = dims(post["cover"])
    art_schema = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": post["title"], "description": post["description"],
                  "image": {"@type": "ImageObject", "url": f"{SITE['url']}/fotos/{post['cover']}.webp", "width": cw, "height": ch, "caption": post.get("cover_alt") or alt_for(post["cover"])},
                  "datePublished": post["date"], "dateModified": upd, "wordCount": post["words"], "articleSection": cat_label(cat, lang),
                  "keywords": post.get("keywords", ""), "about": {"@type": "Place", "name": "Margarita Island, Venezuela" if en else "Isla de Margarita, Venezuela"},
                  "inLanguage": lang, "author": {"@type": "Person", "name": SITE["host"], "url": SITE["url"] + "/"},
                  "publisher": {"@type": "Organization", "name": SITE["name"], "logo": {"@type": "ImageObject", "url": SITE["url"] + "/favicon.svg"}},
                  "mainEntityOfPage": p.abs()}
    schemas = [art_schema, bc_schema]
    if post["faq"]:
        schemas.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in post["faq"]]})
    extra = (f'<meta property="article:published_time" content="{post["date"]}">'
             f'<meta property="article:modified_time" content="{upd}">'
             f'<meta property="article:section" content="{cat_label(cat, lang)}">')
    return p, layout(p, post.get("seo_title", post["title"]), post["description"], body, active=base,
                     schema=schemas, og_image=f"fotos/og/{post['cover']}.jpg", og_type="article",
                     og_alt=post.get("cover_alt") or alt_for(post["cover"]), extra_head=extra, lang=lang, alternates=alternates)

SHARE_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12"/><path d="M7 8l5-5 5 5"/><path d="M5 13v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6"/></svg>'

def share_block(p, post, lang):
    en = lang == "en"
    T = (("Did you find it useful? Share it", "Share", "Copy link", "Link copied", "Close")
         if en else ("¿Te ha servido? Compártelo", "Compartir", "Copiar enlace", "Enlace copiado", "Cerrar"))
    from urllib.parse import quote
    u, t = quote(p.abs(), safe=""), quote(post["title"], safe="")
    opts = [
        ("WhatsApp", f"https://wa.me/?text={t}%20{u}", "wa"),
        ("Facebook", f"https://www.facebook.com/sharer/sharer.php?u={u}", "fb"),
        ("Telegram", f"https://t.me/share/url?url={u}&text={t}", "tg"),
        ("X", f"https://x.com/intent/post?url={u}&text={t}", "x"),
    ]
    items = "".join(f'<a class="share-opt share-{k}" href="{h}" target="_blank" rel="noopener">{n}</a>' for n, h, k in opts)
    return (f'<div class="share" data-share data-title="{esc(post["title"])}" data-url="{p.abs()}" data-copied="{T[3]}">'
            f'<span class="share-title">{T[0]}</span>'
            f'<button type="button" class="btn btn-primary" data-share-btn aria-expanded="false">{SHARE_SVG}{T[1]}</button>'
            f'<div class="share-menu" hidden>{items}<button type="button" class="share-opt share-copy" data-share-copy><span>{T[2]}</span></button></div>'
            f'</div>')

def page_blog_en(posts_en):
    p = Page("en/blog/")
    bc, bc_schema = breadcrumbs(p, [(None, "Margarita guide")], "en")
    title = "Margarita Island travel guide: things to do"
    intro = "Beaches, history, day trips and practical tips for your trip to Margarita Island, Venezuela, written by the host of Downtown Life VIP in Pampatar."
    cards = "".join(post_card(p, x) for x in posts_en)
    body = f"""
<section class="page-hero"><div class="container">{bc}<h1>{esc(title)}</h1><p>{esc(intro)}</p><a class="lang-pill" href="{p.u('blog/')}" hreflang="es" lang="es">Guía en español →</a></div></section>
<section class="section"><div class="container"><h2 class="sr-only">Articles</h2><div class="posts">{cards}</div></div></section>
<section class="cta-band"><div class="container"><div><h2>Your base in Margarita</h2><p>A beachfront apartment in Pampatar to rest between beaches and day trips.</p></div><a class="btn btn-sun" href="{book_url()}" target="_blank" rel="noopener">Check availability</a></div></section>
"""
    blog_schema = {"@context": "https://schema.org", "@type": "Blog", "name": "Margarita Island travel guide", "url": SITE["url"] + "/en/blog/", "inLanguage": "en"}
    return p, layout(p, title, intro, body, active="en/blog/", schema=[blog_schema, bc_schema], lang="en",
                     alternates=[("en", "en/blog/"), ("es", "blog/")])

def page_contact():
    p = Page("contacto/")
    bc, bc_schema = breadcrumbs(p, [("", "Inicio"), (None, "Contacto")])
    cards = [f"""<div class="contact-card">{icon('message')}<h3>Mensaje por Airbnb</h3><p>La forma más rápida de consultar fechas, precios o cualquier duda sobre tu estancia.</p><a class="btn btn-primary" href="{book_url()}" target="_blank" rel="noopener">Escribir en Airbnb</a></div>"""]
    if wa_link():
        cards.insert(0, f"""<div class="contact-card wa">{WA_SVG}<h3>WhatsApp</h3><p>¿Tienes preguntas antes de reservar? Escríbenos directamente y te respondemos lo antes posible.</p><a class="btn btn-wa" href="{wa_link()}" target="_blank" rel="noopener">{WA_SVG} Escribir por WhatsApp</a></div>""")
    if SITE["email"]:
        cards.append(f"""<div class="contact-card">{icon('mail')}<h3>Correo</h3><p>Para colaboraciones o estancias largas.</p><p><strong>{SITE['email']}</strong></p></div>""")
    if SITE["instagram"]:
        cards.append(f"""<div class="contact-card">{icon('instagram')}<h3>Instagram</h3><p>Fotos del apartamento y de la isla.</p><a class="btn btn-outline" href="https://instagram.com/{SITE['instagram']}" target="_blank" rel="noopener">@{SITE['instagram']}</a></div>""")
    cards.append(f"""<div class="contact-card">{icon('pin')}<h3>Ubicación</h3><p>{SITE['address']}. La dirección exacta te la enviamos al confirmar la reserva.</p><a class="btn btn-outline" href="{SITE['maps']}" target="_blank" rel="noopener">Ver en el mapa</a></div>""")
    body = f"""
<section class="page-hero"><div class="container">{bc}<h1>Contacto</h1><p>¿Tienes dudas sobre el apartamento o quieres organizar tu viaje a Margarita? Escríbenos.</p></div></section>
<section class="section"><div class="container"><h2 class="sr-only">Formas de contacto</h2><div class="contact-grid">{''.join(cards)}</div></div></section>
"""
    return p, layout(p, "Contacto", "Contacta con la anfitriona de Downtown Life VIP, apartamento frente al mar en Pampatar, Isla de Margarita.", body, active="contacto/", schema=[bc_schema])

def page_legal(kind):
    p = Page(f"{kind}/")
    if kind == "aviso-legal":
        title = "Aviso legal"
        content = f"""<p>Este sitio web presenta el apartamento turístico Downtown Life VIP, situado en {SITE['address']}, gestionado por su anfitriona, {SITE['host']}.</p>
<h2>Objeto</h2><p>La web tiene carácter informativo. Las reservas no se realizan en este sitio, sino a través de la plataforma Airbnb, que gestiona el pago y las condiciones de la reserva conforme a sus propios términos.</p>
<h2>Contenidos</h2><p>Los textos y fotografías de esta web pertenecen a Downtown Life VIP, salvo que se indique lo contrario. La información de la guía de Margarita se ofrece como recomendación y puede variar; te aconsejamos confirmar horarios y precios antes de cada visita.</p>
<h2>Enlaces externos</h2><p>Esta web contiene enlaces a sitios de terceros, como Airbnb o Google Maps, sobre cuyos contenidos y políticas no tenemos control.</p>
<h2>Contacto</h2><p>Puedes contactar con la titular a través de la página de <a href="{p.u('contacto/')}">contacto</a>.</p>"""
    else:
        title = "Privacidad y cookies"
        content = f"""<p>En Downtown Life VIP respetamos tu privacidad. Esta web no tiene formularios ni registro de usuarios, y no recoge datos personales.</p>
<h2>Cookies</h2><p>Esta web no utiliza cookies propias ni de terceros con fines de análisis o publicidad. Las fuentes tipográficas se sirven desde nuestro propio servidor.</p>
<h2>Servicios externos</h2><p>Cuando pulsas un enlace a Airbnb, Google Maps, WhatsApp o Instagram, sales de esta web y se aplican las políticas de privacidad de esos servicios.</p>
<h2>Reservas</h2><p>Los datos que facilitas al reservar los gestiona Airbnb conforme a su política de privacidad.</p>
<h2>Contacto</h2><p>Para cualquier consulta sobre privacidad, escríbenos desde la página de <a href="{p.u('contacto/')}">contacto</a>.</p>"""
    body = f"""<section class="page-hero"><div class="container"><h1>{title}</h1><p>Última actualización: {fdate(date.today().isoformat())}</p></div></section>
<section class="section"><div class="container"><div class="prose">{content}</div></div></section>"""
    desc = ("Aviso legal de Downtown Life VIP: quién gestiona la web del apartamento frente al mar en Pampatar y cómo funcionan las reservas a través de Airbnb."
            if kind == "aviso-legal" else
            "Privacidad y cookies en la web de Downtown Life VIP: no recogemos datos personales ni usamos cookies de análisis o publicidad. Las reservas las gestiona Airbnb.")
    return p, layout(p, title, desc, body)

def page_404():
    p = Page("")
    body = f"""<section class="notfound container"><span class="eyebrow">Error 404</span><h1>Esta página no existe</h1><p>Puede que el enlace haya cambiado. Vuelve al inicio o explora la guía de Margarita.</p>
<p style="margin-top:24px;display:flex;gap:12px;justify-content:center;flex-wrap:wrap"><a class="btn btn-primary" href="{p.u('')}">Ir al inicio</a><a class="btn btn-outline" href="{p.u('blog/')}">Guía de Margarita</a></p></section>"""
    return layout(p, "Página no encontrada", "La página que buscas no existe o ha cambiado de dirección. Vuelve al inicio de Downtown Life VIP o explora la guía de Isla de Margarita.", body, noindex=True)

# ---------------------------------------------------------------- generación
def write(path, content):
    if wa_link():
        content = content.replace(f'href="{wa_link()}" target', f'href="{wa_link()}" data-wa target')
    f = OUT / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(content, encoding="utf-8")

def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets")
    shutil.copytree(ROOT / "fotos", OUT / "fotos")
    if wa_link():
        import qrcode, qrcode.image.svg
        (OUT / "assets" / "img").mkdir(parents=True, exist_ok=True)
        qrcode.make(wa_link(), image_factory=qrcode.image.svg.SvgPathFillImage, border=2).save(str(OUT / "assets" / "img" / "whatsapp-qr.svg"))
    write("favicon.svg", LOGO.replace('aria-hidden="true"', 'xmlns="http://www.w3.org/2000/svg"'))
    shutil.copy(ROOT / "assets" / "apple-touch-icon.png", OUT / "apple-touch-icon.png")
    shutil.copy(ROOT / "assets" / "favicon-32.png", OUT / "favicon-32.png")
    posts = load_posts()
    posts_en = load_posts("en")
    by_slug = {x["slug"]: x for x in posts}
    pairs = {}
    for e in posts_en:
        es = by_slug.get(e.get("translation", ""))
        if es:
            pairs[e["slug"]] = es; pairs[es["slug"]] = e
    # imágenes para redes sociales (1200x630, JPG)
    (OUT / "fotos" / "og").mkdir(exist_ok=True)
    def og(src, dst):
        with _PIL.open(ROOT / "fotos" / (src + ".webp")) as im:
            im = im.convert("RGB"); W, H = im.size; tw = W; th = round(W * 630 / 1200)
            if th > H: th = H; tw = round(H * 1200 / 630)
            l = (W - tw) // 2; t = (H - th) // 2
            im.crop((l, t, l + tw, t + th)).resize((1200, 630), _PIL.LANCZOS).save(OUT / "fotos" / "og" / (dst + ".jpg"), quality=84)
    og("apartamento-pampatar-balcon-vista-al-mar", "portada")
    for x in posts + posts_en:
        og(x["cover"], x["cover"])
    pages = []
    for fn in (lambda: page_home(posts), page_apartment, page_about, page_contact, lambda: page_blog(posts)):
        pg, out = fn(); pages.append(pg); write(pg.path + "index.html", out)
    for c in CATEGORIES:
        pg, out = page_blog(posts, c); write(pg.path + "index.html", out)
        if any(x["category"] == c for x in posts):
            pages.append(pg)
    for post in posts:
        pg, out = page_post(post, posts, pairs.get(post["slug"]) if post["slug"] in by_slug else None); pages.append(pg); write(pg.path + "index.html", out)
    if posts_en:
        pg, out = page_blog_en(posts_en); pages.append(pg); write(pg.path + "index.html", out)
        for post in posts_en:
            pg, out = page_post(post, posts_en, pairs.get(post["slug"])); pages.append(pg); write(pg.path + "index.html", out)
    for k in ("aviso-legal", "privacidad"):
        pg, out = page_legal(k); write(pg.path + "index.html", out)
    write("404.html", page_404())
    today = date.today().isoformat()
    def img_tags(pg):
        return "".join(f"<image:image><image:loc>{SITE['url']}/fotos/{n}.webp</image:loc></image:image>" for n in pg.images)
    urls = "".join(f"<url><loc>{SITE['url']}/{pg.path}</loc><lastmod>{today}</lastmod>{img_tags(pg)}</url>" for pg in pages)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">{urls}</urlset>\n')
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE['url']}/sitemap.xml\n")
    items = "".join(f"""<item><title>{esc(x['title'])}</title><link>{SITE['url']}/blog/{x['slug']}/</link><guid>{SITE['url']}/blog/{x['slug']}/</guid><pubDate>{format_datetime(datetime.fromisoformat(x['date']).replace(tzinfo=timezone.utc))}</pubDate><description>{esc(x['description'])}</description></item>""" for x in posts)
    write("feed.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Guía de Margarita | Downtown Life VIP</title><link>{SITE["url"]}/blog/</link><description>Qué hacer en Isla de Margarita</description><language>es</language>{items}</channel></rss>\n')
    print(f"Listo: {len(pages)} páginas indexables, {len(posts)} artículos en español y {len(posts_en)} en inglés en {OUT}")

if __name__ == "__main__":
    main()
