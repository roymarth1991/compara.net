from flask import Flask, render_template, request
from comparador import buscar_en_todas  # tu módulo scraper

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    resultados = None
    termino = ""
    if request.method == "POST":
        termino = request.form["termino"]
        resultados = buscar_en_todas(termino)
    return render_template("index.html", resultados=resultados, termino=termino)

if __name__ == "__main__":
    app.run(debug=True)
