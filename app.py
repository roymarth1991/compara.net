# app.py
import os
from flask import Flask, render_template, request
from comparador import buscar_en_todas, obtener_top5, cargar_topes
from db import init_db, guardar_en_db
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "CAMBIAR_ESTO")

# Inicializar base de datos al arrancar
init_db()

TIENDAS = ["Jumbo", "La Sirena", "Nacional", "Plaza Lama", "PriceSmart"]

@app.route("/health")
def health_check():
    return "OK", 200

@app.route("/", methods=["GET", "POST"])
def index():
    resultados = []
    termino = ""

    # Preparar top5 con contadores
    counts = cargar_topes()
    top5 = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top5_counts = top5  # lista de tuplas (item, count)

    if request.method == "POST" and request.form.get("termino", "").strip():
        termino = request.form["termino"].strip()
        resultados = buscar_en_todas(termino)
        guardar_en_db(resultados)
        # Actualizar top5 después de la búsqueda
        counts = cargar_topes()
        top5_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return render_template(
        "index.html",
        resultados=resultados,
        termino=termino,
        tiendas=TIENDAS,
        top5_counts=top5_counts
    )

@app.route("/lista", methods=["POST"])
def lista():
    productos = request.form.getlist("producto")
    totales = {t: 0.0 for t in TIENDAS}
    detalle = {t: [] for t in TIENDAS}

    for prod in productos:
        res = buscar_en_todas(prod)
        precios_por_tienda = {t: float('inf') for t in TIENDAS}
        for r in res:
            try:
                precio = float(r['precio'].replace('RD$', '').replace('$', '').replace(',', ''))
            except:
                precio = float('inf')
            if precio < precios_por_tienda[r['tienda']]:
                precios_por_tienda[r['tienda']] = precio
        for t in TIENDAS:
            precio = precios_por_tienda[t]
            if precio == float('inf'):
                detalle[t].append(f"{prod}: —")
            else:
                detalle[t].append(f"{prod}: {precio:.2f}")
                totales[t] += precio

    mejor = min(totales, key=totales.get) if productos else None
    # Preparar top5 para plantilla
    counts = cargar_topes()
    top5_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return render_template(
        "index.html",
        resultados=[],
        termino="",
        tiendas=TIENDAS,
        lista=productos,
        totales=totales,
        detalle=detalle,
        mejor=mejor,
        top5_counts=top5_counts
    )

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
