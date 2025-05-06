import os
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import urllib.parse

# Crear carpeta de capturas si no existe (solo HTML)
def ensure_capturas():
    if not os.path.exists("capturas"):
        os.makedirs("capturas")

ensure_capturas()

# Guardar HTML para debugging
def guardar_html(texto, nombre_base):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"capturas/{nombre_base}_{ts}.html"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(texto)
    print(f"📄 HTML guardado: {path}")
    return path

# Función genérica de scraping con requests + BeautifulSoup
def scrape_site(url, container_sel, name_sel, price_sel, link_sel=None, tienda_name=""):
    print(f"[{tienda_name}] Solicitando URL: {url}")
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    html = resp.text
    guardar_html(html, f"{tienda_name.lower()}_raw")
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.select(container_sel)
    print(f"[{tienda_name}] Encontrados {len(items)} contenedores")
    productos = []
    for item in items[:5]:
        try:
            nombre_tag = item.select_one(name_sel)
            precio_tag = item.select_one(price_sel)
            enlace = None
            if link_sel:
                link_tag = item.select_one(link_sel)
                enlace = urllib.parse.urljoin(url, link_tag['href']) if link_tag else None
            nombre = nombre_tag.get_text(strip=True) if nombre_tag else ''
            precio = precio_tag.get_text(strip=True) if precio_tag else ''
            productos.append({
                "nombre": nombre,
                "precio": precio,
                "tienda": tienda_name,
                "enlace": enlace
            })
        except Exception as e:
            print(f"[{tienda_name}] Error extrayendo item: {e}")
    return productos

# Funciones específicas por tienda

def buscar_jumbo(termino):
    url = f"https://jumbo.com.do/catalogsearch/result/?q={urllib.parse.quote(termino)}"
    return scrape_site(
        url,
        container_sel="div.product-item-info",
        name_sel=".product-item-tile__name a",
        price_sel=".product-item-tile__price-current",
        link_sel="a.product-item-tile__link",
        tienda_name="Jumbo"
    )

def buscar_sirena(termino):
    url = f"https://www.sirena.do/products/search/{urllib.parse.quote(termino)}"
    return scrape_site(
        url,
        container_sel="div.item-product",
        name_sel=".item-product-title a",
        price_sel=".item-product-price strong",
        tienda_name="La Sirena"
    )

def buscar_nacional(termino):
    url = f"https://supermercadosnacional.com/catalogsearch/result/?q={urllib.parse.quote(termino)}"
    return scrape_site(
        url,
        container_sel="div.product-item-info",
        name_sel="a.product-item-link",
        price_sel="[data-price-type='finalPrice'] span.price",
        link_sel="a.product-item-link",
        tienda_name="Nacional"
    )

def buscar_plaza_lama(termino):
    url = f"https://plazalama.com.do/search?name={urllib.parse.quote(termino)}"
    return scrape_site(
        url,
        container_sel="div.card-product-vertical.product-card-default",
        name_sel=".prod__name",
        price_sel=".base__price",
        tienda_name="Plaza Lama"
    )

def buscar_pricesmart(termino):
    url = f"https://www.pricesmart.com/es-do/busqueda?q={urllib.parse.quote(termino)}"
    return scrape_site(
        url,
        container_sel="div.product-card-vertical",
        name_sel="span.product-card__title",
        price_sel="span.sf-price__regular",
        tienda_name="PriceSmart"
    )

# Función que agrupa todas las búsquedas
def buscar_en_todas(termino):
    fuentes = [
        buscar_jumbo,
        buscar_sirena,
        buscar_nacional,
        buscar_plaza_lama,
        buscar_pricesmart
    ]
    resultados = []
    for fuente in fuentes:
        resultados.extend(fuente(termino))
    # Ordenar por precio numérico
    def parse_precio(p):
        try:
            return float(p['precio'].replace('RD$', '').replace('$', '').replace(',', '').strip())
        except:
            return float('inf')
    return sorted(resultados, key=parse_precio)
