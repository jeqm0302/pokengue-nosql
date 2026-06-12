from flask import Flask, render_template,url_for, session, redirect, request, jsonify
from pokeapi import get_pokemon, get_lista_pokemons
from services.Neo4jService import Neo4jService

app = Flask(__name__)
neo4j_service = Neo4jService()
from sheets import get_entrenadores, get_pokemons_domesticados
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017/")
db     = client["pokengue"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/pokemon/<nombre_o_id>")
def pokemon(nombre_o_id):
    """Devuelve los datos de un Pokémon en JSON."""
    data = get_pokemon(nombre_o_id.lower())
    if data is None:
        return jsonify({"error": f"Pokémon '{nombre_o_id}' no encontrado"}), 404
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


# ----------------------------------------------------------------------
# Rutas Neo4j (Red social Pokémon)
# Todas devuelven el mismo formato: {"ok": bool, "data": ..., "mensaje": str}
# ----------------------------------------------------------------------
@app.route("/neo4j")
def neo4j_home():
    """Renderiza la página de la demo de Neo4j."""
    return render_template("neo4j.html")


@app.route("/neo4j/entrenador", methods=["POST"])
def neo4j_cargar_entrenador():
    resultado = neo4j_service.cargar_entrenador(dict(request.form))
    return jsonify(resultado)


@app.route("/neo4j/pokemon", methods=["POST"])
def neo4j_cargar_pokemon():
    resultado = neo4j_service.cargar_pokemon(dict(request.form))
    return jsonify(resultado)


@app.route("/neo4j/tiene", methods=["POST"])
def neo4j_crear_tiene():
    resultado = neo4j_service.crear_tiene(dict(request.form))
    return jsonify(resultado)


@app.route("/neo4j/amistad", methods=["POST"])
def neo4j_crear_amistad():
    resultado = neo4j_service.crear_amistad(dict(request.form))
    return jsonify(resultado)


@app.route("/neo4j/info/<id>")
def neo4j_info(id):
    resultado = neo4j_service.obtener_info(id)
    return jsonify(resultado)


@app.route("/neo4j/recomendar/<id>")
def neo4j_recomendar(id):
    resultado = neo4j_service.recomendar(id)
    return jsonify(resultado)


@app.route("/neo4j/estado")
def neo4j_estado():
    resultado = neo4j_service.obtener_estado()
    return jsonify(resultado)

@app.route("/pokedex")
def cargar_pokedex():
    """Vacía la colección pokedex y la recarga con todos los pokémons de la PokeAPI."""
    data = get_lista_pokemons()
    if data is None:
        return jsonify({"error": "No se pudo obtener la lista de pokémons"}), 500

    pokedex = db["pokedex"]
    pokedex.drop()

    pokemons = data["pokemons"]
    if pokemons:
        pokedex.insert_many(pokemons)

    return redirect("/entrenadores")

@app.route("/entrenadores")
def cargar_entrenadores():
    """Vacía la colección entrenador y la recarga desde Google Sheets."""
    try:
        entrenadores = get_entrenadores()
    except Exception as e:
        return jsonify({"error": f"Error al leer el Sheet: {str(e)}"}), 500

    if not entrenadores:
        return jsonify({"error": "No se encontraron entrenadores en el Sheet"}), 404

    coleccion = db["entrenador"]
    coleccion.drop()
    coleccion.insert_many(entrenadores)

    return redirect("/pokemons")

@app.route("/pokemons")
def cargar_pokemons_domesticados():
    """Vacía la colección pokemons y la recarga desde Google Sheets."""
    try:
        pokemons = get_pokemons_domesticados()
    except Exception as e:
        return jsonify({"error": f"Error al leer el Sheet: {str(e)}"}), 500

    if not pokemons:
        return jsonify({"error": "No se encontraron pokémons en el Sheet"}), 404

    coleccion = db["pokemons"]
    coleccion.drop()
    coleccion.insert_many(pokemons)

    return jsonify({
        "mensaje": "Datos cargados correctamente."
    })

if __name__ == "__main__":
    app.run(debug=True)
