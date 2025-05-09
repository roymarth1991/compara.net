import os
from flask import Flask, render_template, request, redirect, url_for
from comparador import buscar_en_todas, obtener_top5  # Importar también obtener_top5
from db import init_db, guardar_en_db

app = Flask(__name__)
init_db()  # inicia la base de datos al arrancar

TIENDAS = ["Jumbo", "La Sirena", "Nacional", "Plaza Lama", "PriceSmart"]

@app.route("/", methods=["GET", "POST"])
def index():
    resultados = []
    termino = ""
    # Obtener top 5 búsquedas siempre
    top5 = obtener_top5()

    if request.method == "POST" and "termino" in request.form:
        termino = request.form["termino"]
        resultados = buscar_en_todas(termino)
        guardar_en_db(resultados)
        # Actualizar top5 luego de registrar búsqueda
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
            precio = float(r["precio"].replace('RD$', '').replace('$', '').replace(',', ''))
            if precio < precios_por_tienda[r["tienda"]]:
                precios_por_tienda[r["tienda"]] = precio
        for t in TIENDAS:
            precio = precios_por_tienda[t]
            if precio == float('inf'):
                detalle[t].append(f"{prod}: —")
            else:
                detalle[t].append(f"{prod}: {precio:.2f}")
                totales[t] += precio

    mejor = min(totales, key=totales.get)
    # Obtener top5 para mostrar en plantilla lista también
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
    app.run(debug=True)
