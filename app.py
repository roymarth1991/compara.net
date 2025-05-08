from flask import Flask, render_template, request, flash
from comparador import buscar_en_todas  # tu módulo scraper

app = Flask(__name__)
app.secret_key = "CAMBIA_ESTA_CLAVE_POR_ALGO_SECRETO"  # necesario para flash

@app.route("/", methods=["GET", "POST"])
def index():
    resultados = []
    termino = ""
    if request.method == "POST":
        termino = request.form.get("termino", "").strip()
        if not termino:
            flash("Por favor ingresa un término de búsqueda.", "warning")
        else:
            try:
                resultados = buscar_en_todas(termino)
                if not resultados:
                    flash(f"No se encontraron resultados para «{termino}».", "info")
            except Exception as e:
                # capturamos cualquier error del scraper
                app.logger.error(f"Error al buscar «{termino}»: {e}")
                flash("Ocurrió un error al procesar tu búsqueda. Intenta de nuevo más tarde.", "danger")
    return render_template("index.html", resultados=resultados, termino=termino)

if __name__ == "__main__":
    # debug=True solo en desarrollo; en producción debería ser False
    app.run(host="0.0.0.0", port=5000, debug=True)
