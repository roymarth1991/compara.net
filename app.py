from flask import Flask, render_template, request, redirect, url_for
from comparador import buscar_en_todas, obtener_top5  # Importar también obtener_top5
from db import init_db, guardar_en_db

app = Flask(__name__)

# Solo inicializar la base de datos una vez
if not os.path.exists('productos_db.db'):
    init_db()  # Inicia la base de datos al arrancar, solo si es necesario

TIENDAS = ["Jumbo", "La Sirena", "Nacional", "Plaza Lama", "PriceSmart"]

@app.route("/", methods=["GET", "POST"])
def index():
    resultados = []
    termino = ""
    top5 = obtener_top5()  # Obtener top 5 búsquedas siempre, fuera del POST

    if request.method == "POST" and "termino" in request.form:
        termino = request.form["termino"]
        if termino.strip():  # Verifica si se ingresa un término válido
            resultados = buscar_en_todas(termino)
            guardar_en_db(resultados)
            top5 = obtener_top5()  # Actualizar top5 después de guardar

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
    if not productos:
        return render_template("index.html", error="No se seleccionaron productos")  # Validación de formulario vacío
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
