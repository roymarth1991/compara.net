# comparador.py

import os
import json
import time
import urllib.parse
import cloudscraper
import requests
from bs4 import BeautifulSoup
import asyncio
from playwright.async_api import async_playwright

from db import init_db, guardar_en_db  # Inicializa y guarda en BD

# Archivos de configuración
top_file = "top_searches.json"
CACHE_FILE = "cache.json"
CACHE_TTL = None  # Cache sin expiración

# Directorio de capturas
def ensure_capturas():
    os.makedirs("capturas", exist_ok=True)

# Archivo de top búsquedas
def ensure_top_file():
    if not os.path.exists(top_file):
        with open(top_file, 'w', encoding='utf-8') as f:
            json.dump({}, f)

ensure_capturas()
ensure_top_file()

# --- Tracking de búsquedas ---

def cargar_topes():
    try:
        with open(top_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def guardar_topes(counts):
    with open(top_file, 'w', encoding='utf-8') as f:
        json.dump(counts, f, ensure_ascii=False, indent=2)


def incrementar_busqueda(termino: str):
    counts = cargar_topes()
    counts[termino] = counts.get(termino, 0) + 1
    guardar_topes(counts)


def obtener_top5() -> list:
    counts = cargar_topes()
    top5 = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
    return [item for item, _ in top5]

# --- Caching de páginas ---

def cargar_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def guardar_cache(cache: dict):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

CACHE = cargar_cache()

def cache_valido(entry: dict) -> bool:
    # Validación básica
    if not isinstance(entry, dict) or 'timestamp' not in entry or 'data' not in entry:
        return False
    if not isinstance(entry['data'], list) or not entry['data']:
        return False
    # Si CACHE_TTL es None, nunca expira
    if CACHE_TTL is None:
        return True
    # Si tiene TTL, comprueba tiempo
    return (time.time() - entry['timestamp']) < CACHE_TTL

# --- Scraping con Playwright para JS ---

async def fetch_js_content(url: str, wait_selector: str, tienda_name: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        try:
            await page.wait_for_selector(wait_selector, timeout=30000)
            await page.wait_for_timeout(2000)
        except Exception:
            print(f"[{tienda_name}] Timeout JS selector: {wait_selector}")
        content = await page.content()
        await browser.close()
        return content


def get_js_html(url: str, wait_selector: str, tienda_name: str) -> str:
    return asyncio.run(fetch_js_content(url, wait_selector, tienda_name))

# --- Función genérica de scraping ---

def scrape_site(
    url: str,
    cont_sel: str,
    name_sel: str,
    price_sel: str,
    link_sel: str = None,
    tienda_name: str = "",
    js_render: bool = False
) -> list:
    cache_key = f"{tienda_name}|{url}"
    if cache_key in CACHE and cache_valido(CACHE[cache_key]):
        print(f"[{tienda_name}] Usando cache")
        return CACHE[cache_key]['data']

    print(f"[{tienda_name}] Solicitando: {url}")
    try:
        if js_render:
            html = get_js_html(url, cont_sel, tienda_name)
        else:
            headers = {'User-Agent': 'Mozilla/5.0'}
            if 'jumbo.com.do' in url:
                scraper = cloudscraper.create_scraper()
                scraper.get(url, headers=headers, timeout=10)
                resp = scraper.get(url, headers=headers, timeout=15)
            else:
                time.sleep(2)
                resp = requests.get(url, headers=headers, timeout=20)
            resp.raise_for_status()
            html = resp.text
    except Exception as e:
        print(f"[{tienda_name}] HTTP Error: {e}")
        return []

    # Guardar snapshot
    ts = int(time.time())
    with open(f"capturas/{tienda_name.lower()}_{ts}.html", 'w', encoding='utf-8') as f:
        f.write(html)

    soup = BeautifulSoup(html, 'html.parser')
    items = soup.select(cont_sel)
    print(f"[{tienda_name}] Encontrados: {len(items)} items")

    productos = []
    for item in items[:10]:
        try:
            nombre_el = item.select_one(name_sel)
            precio_el = item.select_one(price_sel)
            if not nombre_el or not precio_el:
                continue
            nombre = nombre_el.get_text(strip=True)
            precio = precio_el.get_text(strip=True)
            enlace = None
            if link_sel:
                link_el = item.select_one(link_sel)
                if link_el and link_el.has_attr('href'):
                    enlace = urllib.parse.urljoin(url, link_el['href'])
            productos.append({
                'nombre': nombre,
                'precio': precio,
                'tienda': tienda_name,
                'enlace': enlace
            })
        except Exception as e:
            print(f"[{tienda_name}] Error parseo item: {e}")

    CACHE[cache_key] = {'timestamp': time.time(), 'data': productos}
    guardar_cache(CACHE)
    return productos

# --- Funciones específicas por tienda ---

def buscar_jumbo(termino: str) -> list:
    return scrape_site(
        f"https://jumbo.com.do/catalogsearch/result/?q={urllib.parse.quote(termino)}",
        cont_sel="div.product-item-info",
        name_sel=".product-item-tile__name a",
        price_sel=".product-item-tile__price-current",
        link_sel="a.product-item-tile__link",
        tienda_name="Jumbo",
        js_render=False
    )

# TODO: definir buscar_sirena, buscar_nacional, buscar_plaza_lama, buscar_pricesmart con mismos parámetros

def buscar_sirena(termino: str) -> list:
    return scrape_site(
        f"https://www.sirena.do/products/search/{urllib.parse.quote(termino)}",
        cont_sel="div.item-product",
        name_sel=".item-product-title a",
        price_sel=".item-product-price strong",
        tienda_name="La Sirena",
        js_render=True
    )

def buscar_nacional(termino: str) -> list:
    return scrape_site(
        f"https://supermercadosnacional.com/catalogsearch/result/?q={urllib.parse.quote(termino)}",
        cont_sel="div.product-item-info",
        name_sel="a.product-item-link",
        price_sel="[data-price-type='finalPrice'] span.price",
        link_sel="a.product-item-link",
        tienda_name="Nacional",
        js_render=False
    )

def buscar_plaza_lama(termino: str) -> list:
    return scrape_site(
        f"https://plazalama.com.do/search?name={urllib.parse.quote(termino)}",
        cont_sel="div.card-product-vertical.product-card-default",
        name_sel=".prod__name",
        price_sel=".base__price",
        tienda_name="Plaza Lama",
        js_render=True
    )

def buscar_pricesmart(termino: str) -> list:
    return scrape_site(
        f"https://www.pricesmart.com/es-do/busqueda?q={urllib.parse.quote(termino)}",
        cont_sel="div.product-card-vertical",
        name_sel="span.product-card__title",
        price_sel="span.sf-price__regular",
        tienda_name="PriceSmart",
        js_render=True
    )

# --- Búsqueda en todas las tiendas ---

def buscar_en_todas(termino: str) -> list:
    incrementar_busqueda(termino)
    init_db()
    fuentes = [buscar_jumbo, buscar_sirena, buscar_nacional, buscar_plaza_lama, buscar_pricesmart]
    resultados = []
    for fuente in fuentes:
        resultados += fuente(termino)
    resultados.sort(key=lambda p: float(
        p['precio']
        .replace('RD$', '')
        .replace('DOP', '')
        .replace('$', '')
        .replace(',', '')
        .strip()
    ) if p['precio'] else float('inf'))
    guardar_en_db(resultados)
    return resultados

# Exportar funciones
__all__ = ['buscar_en_todas', 'obtener_top5']

# --- Ejecución directa ---
if __name__ == '__main__':
    termino = input('Término a buscar: ')
    resultados = buscar_en_todas(termino)
    for prod in resultados:
        print(prod)
    print("\nTop 5 búsquedas:", obtener_top5())
