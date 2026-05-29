from flask import Flask, render_template, request, jsonify
from pokeapi import get_pokemon, get_lista_pokemons
 
app = Flask(__name__)
@app.route("/")
def index():
    return render_template("index.html")
 
@app.route("/pokemon/<nombre_o_id>")
def pokemon(nombre_o_id):
    """Devuelve los datos de un Pokémon en JSON."""
    data = get_pokemon(nombre_o_id.lower())
    if data is None:
        return jsonify({"error": f"Pokemon '{nombre_o_id}' no encontrado"}), 404
    return jsonify(data)
 
@app.route("/pokemons")
def lista_pokemons():
    """Devuelve una lista paginada de Pokémon."""
    limite = request.args.get("limite", 20, type=int)
    offset = request.args.get("offset", 0, type=int)
    data = get_lista_pokemons(limite, offset)
    if data is None:
        return jsonify({"error": "No se pudo obtener la lista"}), 500
    return jsonify(data)
 
if __name__ == "__main__":
    app.run(debug=True)