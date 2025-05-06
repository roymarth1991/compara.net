import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.parse

# Crear carpeta de capturas si no existe
def ensure_capturas():
    if not os.path.exists("capturas"):
        os.makedirs("capturas")

ensure_capturas()

# Funciones de utilidades
def guardar_captura(driver, nombre_base):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"capturas/{nombre_base}_{ts}.png"
    driver.save_screenshot(path)
    print(f"🖼️ Captura: {path}")
    return path


def guardar_html(driver, nombre_base):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"capturas/{nombre_base}_{ts}.html"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print(f"📄 HTML: {path}")
    return path

# Configuración del navegador
def configurar_driver():
    opts = Options()
    # opts.add_argument("--headless")  # Descomenta para modo invisible
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--start-maximized")
    opts.add_argument("--log-level=3")
    opts.add_argument("--disable-software-rasterizer")
    return webdriver.Chrome(options=opts)

# Función genérica de scraping
def scrape_site(url, cont_selector, name_sel, price_sel, link_sel=None, tienda_name=""):
    driver = configurar_driver()
    driver.get(url)
    guardar_html(driver, f"{tienda_name.lower()}_raw")
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, cont_selector))
        )
    except Exception as e:
        print(f"[{tienda_name}] Timeout esperando productos: {e}")
    items = driver.find_elements(By.CSS_SELECTOR, cont_selector)
    print(f"[{tienda_name}] Contenedores: {len(items)}")
    if not items:
        guardar_captura(driver, f"{tienda_name.lower()}_vacio")
        guardar_html(driver, f"{tienda_name.lower()}_source_empty")
    productos = []
    for item in items[:5]:
        try:
            nombre = item.find_element(By.CSS_SELECTOR, name_sel).text.strip()
            precio = item.find_element(By.CSS_SELECTOR, price_sel).text.strip()
            enlace = item.find_element(By.CSS_SELECTOR, link_sel).get_attribute('href') if link_sel else None
            productos.append({
                "nombre": nombre,
                "precio": precio,
                "tienda": tienda_name,
                "enlace": enlace
            })
        except Exception as e:
            print(f"[{tienda_name}] Error al extraer: {e}")
    driver.quit()
    return productos

# Funciones específicas por tienda
def buscar_jumbo(termino):
    return scrape_site(
        f"https://jumbo.com.do/catalogsearch/result/?q={urllib.parse.quote(termino)}",
        cont_selector="div.product-item-info",
        name_sel=".product-item-tile__name a",
        price_sel=".product-item-tile__price-current",
        link_sel="a.product-item-tile__link",
        tienda_name="Jumbo"
    )

def buscar_sirena(termino):
    return scrape_site(
        f"https://www.sirena.do/products/search/{urllib.parse.quote(termino)}",
        cont_selector="div.item-product",
        name_sel=".item-product-title a",
        price_sel=".item-product-price strong",
        link_sel=None,
        tienda_name="La Sirena"
    )

def buscar_nacional(termino):
    return scrape_site(
        f"https://supermercadosnacional.com/catalogsearch/result/?q={urllib.parse.quote(termino)}",
        cont_selector="div.product-item-info",
        name_sel="a.product-item-link",
        price_sel="[data-price-type='finalPrice'] span.price",
        link_sel="a.product-item-link",
        tienda_name="Nacional"
    )

def buscar_plaza_lama(termino):
    return scrape_site(
        f"https://plazalama.com.do/search?name={urllib.parse.quote(termino)}",
        cont_selector="div.card-product-vertical.product-card-default",
        name_sel=".prod__name",
        price_sel=".base__price",
        link_sel=None,
        tienda_name="Plaza Lama"
    )

def buscar_pricesmart(termino):
    return scrape_site(
        f"https://www.pricesmart.com/es-do/busqueda?q={urllib.parse.quote(termino)}",
        cont_selector="div.product-card-vertical",
        name_sel="span.product-card__title",
        price_sel="span.sf-price__regular",
        link_sel=None,
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
        resultados += fuente(termino)
    def extraer(p):
        try:
            return float(
                p["precio"].replace("RD$", "").replace("$", "").replace(",", "").strip()
            )
        except:
            return float("inf")
    return sorted(resultados, key=extraer)