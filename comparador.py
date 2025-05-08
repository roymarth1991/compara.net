import os
import json
import time
import urllib.parse
import cloudscraper
import requests
from bs4 import BeautifulSoup
import asyncio
from playwright.async_api import async_playwright

CACHE_FILE = "cache.json"
CACHE_TTL = 60 * 60 * 3  # 3 horas

def ensure_capturas():
    if not os.path.exists("capturas"):
        os.makedirs("capturas")

ensure_capturas()

def guardar_html(texto, nombre_base):
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = f"capturas/{nombre_base}_{ts}.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(texto)
    print(f"📄 HTML guardado en: {path}")
    return path

def cargar_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

CACHE = cargar_cache()

def cache_valido(entry):
    return (
        isinstance(entry, dict)
        and "timestamp" in entry
        and "data" in entry
        and isinstance(entry["data"], list)
        and entry["data"]
        and (time.time() - entry["timestamp"]) < CACHE_TTL
    )

# Fetch dinámico con Playwright
async def fetch_js_content(url, wait_selector, tienda_name):
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

# Wrapper síncrono
def get_js_html(url, wait_selector, tienda_name):
    return asyncio.run(fetch_js_content(url, wait_selector, tienda_name))

def scrape_site(url, cont_sel, name_sel, price_sel, link_sel=None, tienda_name="", js_render=False):
    cache_key = f"{tienda_name}|{url}"
    if cache_key in CACHE and cache_valido(CACHE[cache_key]):
        print(f"[{tienda_name}] Cache válido")
        return CACHE[cache_key]["data"]

    print(f"[{tienda_name}] Solicitando: {url}")
    html = None
    if js_render:
        html = get_js_html(url, cont_sel, tienda_name)
    else:
        try:
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://jumbo.com.do/'}
            if "jumbo.com.do" in url:
                scraper = cloudscraper.create_scraper()
                scraper.get("https://jumbo.com.do", headers=headers, timeout=10)
                resp = scraper.get(url, headers=headers, timeout=15)
            else:
                time.sleep(2)
                resp = requests.get(url, headers=headers, timeout=20)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            print(f"[{tienda_name}] HTTP Error: {e}")
            return []

    guardar_html(html, tienda_name.lower())
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(cont_sel)
    print(f"[{tienda_name}] Elementos encontrados: {len(items)}")

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
                if link_el and link_el.has_attr("href"):
                    enlace = urllib.parse.urljoin(url, link_el["href"])
            productos.append({"nombre": nombre, "precio": precio, "tienda": tienda_name, "enlace": enlace})
        except Exception as e:
            print(f"[{tienda_name}] Error extraer: {e}")

    CACHE[cache_key] = {"timestamp": time.time(), "data": productos}
    guardar_cache(CACHE)
    return productos

# Funciones específicas por tienda
def buscar_jumbo(termino):
    return scrape_site(
        f"https://jumbo.com.do/catalogsearch/result/?q={urllib.parse.quote(termino)}",
        cont_sel="div.product-item-info",
        name_sel=".product-item-tile__name a",
        price_sel=".product-item-tile__price-current",
        link_sel="a.product-item-tile__link",
        tienda_name="Jumbo",
        js_render=False
    )

def buscar_sirena(termino):
    return scrape_site(
        f"https://www.sirena.do/products/search/{urllib.parse.quote(termino)}",
        cont_sel="div.item-product",
        name_sel=".item-product-title a",
        price_sel=".item-product-price strong",
        link_sel=None,
        tienda_name="La Sirena",
        js_render=True
    )

def buscar_nacional(termino):
    return scrape_site(
        f"https://supermercadosnacional.com/catalogsearch/result/?q={urllib.parse.quote(termino)}",
        cont_sel="div.product-item-info",
        name_sel="a.product-item-link",
        price_sel="[data-price-type='finalPrice'] span.price",
        link_sel="a.product-item-link",
        tienda_name="Nacional",
        js_render=False
    )

def buscar_plaza_lama(termino):
    return scrape_site(
        f"https://plazalama.com.do/search?name={urllib.parse.quote(termino)}",
        cont_sel="div.card-product-vertical.product-card-default",
        name_sel=".prod__name",
        price_sel=".base__price",
        link_sel=None,
        tienda_name="Plaza Lama",
        js_render=True
    )

def buscar_pricesmart(termino):
    return scrape_site(
        f"https://www.pricesmart.com/es-do/busqueda?q={urllib.parse.quote(termino)}",
        cont_sel="div.product-card-vertical",
        name_sel="span.product-card__title",
        price_sel="span.sf-price__regular",
        link_sel=None,
        tienda_name="PriceSmart",
        js_render=True
    )

def buscar_en_todas(termino):
    fuentes = [buscar_jumbo, buscar_sirena, buscar_nacional, buscar_plaza_lama, buscar_pricesmart]
    resultados = []
    for fuente in fuentes:
        resultados += fuente(termino)
    resultados.sort(key=lambda p: float(p['precio']
                      .replace('RD$', '')
                      .replace('DOP', '')
                      .replace('$', '')
                      .replace(',', '')
                      .strip()) if p['precio'] else float('inf'))
    return resultados

# Prueba manual
if __name__ == '__main__':
    termino = input('Término a buscar: ')
    for prod in buscar_en_todas(termino):
        print(prod)
