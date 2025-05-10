# app.py
import os
from flask import Flask, render_template, request, redirect, url_for
from comparador import buscar_en_todas, obtener_top5
from db import init_db, guardar_en_db

# Cargar .env si existe
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "CAMBIAR_ESTO")

# Inicializar BD al arrancar
init_db()

TIENDAS = ["Jumbo", "La Sirena", "Nacional", "Plaza Lama", "PriceSmart"]

@app.route("/health")
def health_check():
    return "OK", 200

@app.route("/", methods=["GET", "POST"])
def index():
    resultados = []
    termino = ""
    top5 = obtener_top5()

    if request.method == "POST" and "termino" in request.form:
        termino = request.form.get("termino", "").strip()
        if termino:
            resultados = buscar_en_todas(termino)
            guardar_en_db(resultados)
            top5 = obtener_top5()

    return render_template(
        "index.html",
        resultados=resultados,
        termino=termino,
        tiendas=TIENDAS,
        top5=top5
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
            precio = float(r['precio'].replace('RD$', '').replace('$', '').replace(',', ''))
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
    top5 = obtener_top5()
    return render_template(
        "index.html",
        resultados=[],
        termino="",
        tiendas=TIENDAS,
        lista=productos,
        totales=totales,
        detalle=detalle,
        mejor=mejor,
        top5=top5
    )

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
