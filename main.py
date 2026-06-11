from flask import Flask, render_template,url_for, session, redirect, request, jsonify
from pokeapi import get_pokemon, get_lista_pokemons
from DAO.Neo4jDAO import Neo4jDAO

app = Flask(__name__)
neo4j_dao = Neo4jDAO()
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
    """Crea/actualiza un Entrenador en el grafo."""
    try:
        idEntrenador = request.form.get("idEntrenador", "").strip()
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        medallas_raw = request.form.get("medallas", "")

        if not idEntrenador:
            return jsonify({"ok": False, "data": None,
                            "mensaje": "Falta el ID del entrenador"})

        # Las medallas vienen como string con comas -> lista limpia
        medallas = [m.strip() for m in medallas_raw.split(",") if m.strip()]

        entrenador = neo4j_dao.cargar_entrenador(idEntrenador, nombre, apellido, medallas)
        return jsonify({
            "ok": True,
            "data": entrenador,
            "mensaje": f"Entrenador {idEntrenador} creado",
        })
    except Exception as e:
        return jsonify({"ok": False, "data": None,
                        "mensaje": f"Error al cargar entrenador: {e}"})


@app.route("/neo4j/pokemon", methods=["POST"])
def neo4j_cargar_pokemon():
    """Crea/actualiza un Pokémon en el grafo."""
    try:
        idPokemon = request.form.get("idPokemon", "").strip()
        especie = request.form.get("especie", "").strip()
        nombre = request.form.get("nombre", "").strip()
        tipo_raw = request.form.get("tipo", "")
        peso_raw = request.form.get("peso", "").strip()
        altura_raw = request.form.get("altura", "").strip()

        if not idPokemon:
            return jsonify({"ok": False, "data": None,
                            "mensaje": "Falta el ID del pokémon"})

        # tipo: string con comas -> lista
        tipo = [t.strip() for t in tipo_raw.split(",") if t.strip()]
        # peso y altura -> float (0.0 si vienen vacíos)
        peso = float(peso_raw) if peso_raw else 0.0
        altura = float(altura_raw) if altura_raw else 0.0

        pokemon = neo4j_dao.cargar_pokemon(idPokemon, especie, nombre, tipo, peso, altura)
        return jsonify({
            "ok": True,
            "data": pokemon,
            "mensaje": f"Pokémon {idPokemon} creado",
        })
    except ValueError:
        return jsonify({"ok": False, "data": None,
                        "mensaje": "Peso y altura deben ser números"})
    except Exception as e:
        return jsonify({"ok": False, "data": None,
                        "mensaje": f"Error al cargar pokémon: {e}"})


@app.route("/neo4j/tiene", methods=["POST"])
def neo4j_crear_tiene():
    """Crea la relación TIENE (entrenador posee pokémon)."""
    try:
        idEntrenador = request.form.get("idEntrenador", "").strip()
        idPokemon = request.form.get("idPokemon", "").strip()
        # Checkbox: viene 'on' si está marcado, None si no
        en_equipo = request.form.get("en_equipo") == "on"

        if not idEntrenador or not idPokemon:
            return jsonify({"ok": False, "data": None,
                            "mensaje": "Faltan IDs de entrenador o pokémon"})

        creada = neo4j_dao.crear_relacion_tiene(idEntrenador, idPokemon, en_equipo)
        if not creada:
            return jsonify({"ok": False, "data": None,
                            "mensaje": f"No existe el entrenador {idEntrenador} o el pokémon {idPokemon}"})

        return jsonify({
            "ok": True,
            "data": {"idEntrenador": idEntrenador, "idPokemon": idPokemon, "en_equipo": en_equipo},
            "mensaje": f"{idEntrenador} ahora TIENE a {idPokemon}",
        })
    except Exception as e:
        return jsonify({"ok": False, "data": None,
                        "mensaje": f"Error al crear relación TIENE: {e}"})


@app.route("/neo4j/amistad", methods=["POST"])
def neo4j_crear_amistad():
    """Crea una amistad bidireccional entre dos entrenadores."""
    try:
        id1 = request.form.get("id1", "").strip()
        id2 = request.form.get("id2", "").strip()

        if not id1 or not id2:
            return jsonify({"ok": False, "data": None,
                            "mensaje": "Faltan los dos IDs de entrenador"})
        if id1 == id2:
            return jsonify({"ok": False, "data": None,
                            "mensaje": "Un entrenador no puede ser amigo de sí mismo"})

        creada = neo4j_dao.crear_amistad(id1, id2)
        if not creada:
            return jsonify({"ok": False, "data": None,
                            "mensaje": f"No existe el entrenador {id1} o {id2}"})

        return jsonify({
            "ok": True,
            "data": {"id1": id1, "id2": id2},
            "mensaje": f"{id1} y {id2} ahora son amigos",
        })
    except Exception as e:
        return jsonify({"ok": False, "data": None,
                        "mensaje": f"Error al crear amistad: {e}"})


@app.route("/neo4j/info/<id>")
def neo4j_info(id):
    """Info completa de un entrenador: datos + pokémons + amigos."""
    try:
        entrenador = neo4j_dao.obtener_entrenador(id)
        if entrenador is None:
            return jsonify({"ok": False, "data": None,
                            "mensaje": f"No se encontró el entrenador con ID {id}"})

        pokemons = neo4j_dao.obtener_pokemons_de(id)
        amigos = neo4j_dao.obtener_amigos(id)

        return jsonify({
            "ok": True,
            "data": {
                "entrenador": entrenador,
                "pokemons": pokemons,
                "amigos": amigos,
            },
            "mensaje": f"Info de {id}",
        })
    except Exception as e:
        return jsonify({"ok": False, "data": None,
                        "mensaje": f"Error al obtener info: {e}"})


@app.route("/neo4j/recomendar/<id>")
def neo4j_recomendar(id):
    """Recomienda amigos (amigos de amigos) para un entrenador."""
    try:
        entrenador = neo4j_dao.obtener_entrenador(id)
        if entrenador is None:
            return jsonify({"ok": False, "data": None,
                            "mensaje": f"No se encontró el entrenador con ID {id}"})

        recomendaciones = neo4j_dao.recomendar_amigos(id)
        return jsonify({
            "ok": True,
            "data": {
                "entrenador": entrenador,
                "recomendaciones": recomendaciones,
            },
            "mensaje": f"Recomendaciones para {id}",
        })
    except Exception as e:
        return jsonify({"ok": False, "data": None,
                        "mensaje": f"Error al recomendar amigos: {e}"})


@app.route("/neo4j/estado")
def neo4j_estado():
    """Conteos generales de nodos y relaciones del grafo."""
    try:
        estado = neo4j_dao.contar_estado_general()
        return jsonify({
            "ok": True,
            "data": estado,
            "mensaje": "Estado del grafo Pokengue",
        })
    except Exception as e:
        return jsonify({"ok": False, "data": None,
                        "mensaje": f"Error al obtener estado del grafo: {e}"})

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
