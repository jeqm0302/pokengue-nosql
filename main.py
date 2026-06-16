from flask import Flask, render_template,url_for, session, redirect, request, jsonify
from pokeapi import get_pokemon, get_lista_pokemons
from services.Neo4jService import Neo4jService
from DAO.CassandraDAO import CassandraDAO
from DAO.RedisDAO import RedisDAO

app = Flask(__name__)
neo4j_service = Neo4jService()
redis_dao = RedisDAO()
from sheets import get_entrenadores, get_pokemons_domesticados
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017/")
db     = client["pokengue"]

cassandra_dao = CassandraDAO()

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


@app.route("/neo4j/recomendar/<id>")
def neo4j_recomendar(id):
    resultado = neo4j_service.recomendar(id)
    return jsonify(resultado)


@app.route("/neo4j/estado")
def neo4j_estado():
    resultado = neo4j_service.obtener_estado()
    return jsonify(resultado)

"""
@app.route("/cassandra/combate", methods=["POST"])
def cassandra_registrar_combate():
    try:
        combate_id = cassandra_dao.prueba1()
        return jsonify({"ok": True, "data": {"combate_id": combate_id}, "mensaje": "Combate registrado en Cassandra"})
    except Exception as e:
        return jsonify({"ok": False, "data": None, "mensaje": str(e)}), 500
"""

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


# ----------------------------------------------------------------------
# Rutas Redis (Configuración y preferencias de entrenadores)
# ----------------------------------------------------------------------
@app.route("/redis/config", methods=["POST"])
@app.route("/redis")
def redis_home():
    """Renderiza la página de la demo de Redis."""
    return render_template("redis.html")

@app.route("/redis/config", methods=["POST"])
def redis_guardar_config():
    """Crea/actualiza la configuración de un entrenador en Redis."""
    try:
        idEntrenador = request.form.get("idEntrenador", "").strip()
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        medallas_raw = request.form.get("medallas", "")
        idioma = request.form.get("idioma", "").strip()
        tema = request.form.get("tema", "").strip()
        notificaciones = request.form.get("notificaciones") == "on"

        if not idEntrenador:
            return jsonify({"ok": False, "data": None,
                            "mensaje": "Falta el ID del entrenador"})

        medallas = [m.strip() for m in medallas_raw.split(",") if m.strip()]
        config = redis_dao.guardar_config(
            idEntrenador, nombre, apellido, medallas, idioma, tema, notificaciones
        )
        return jsonify({
            "ok": True,
            "data": config,
            "mensaje": f"Configuración de {idEntrenador} guardada",
        })
    except Exception as e:
        return jsonify({"ok": False, "data": None,
                        "mensaje": f"Error al guardar configuración: {e}"})


@app.route("/redis/config/<idEntrenador>")
def redis_obtener_config(idEntrenador):
    """Devuelve la configuración de un entrenador."""
    try:
        config = redis_dao.obtener_config(idEntrenador)
        if config is None:
            return jsonify({"ok": False, "data": None,
                            "mensaje": f"No hay configuración para {idEntrenador}"})
        return jsonify({"ok": True, "data": config,
                        "mensaje": f"Configuración de {idEntrenador}"})
    except Exception as e:
        return jsonify({"ok": False, "data": None,
                        "mensaje": f"Error al obtener configuración: {e}"})


@app.route("/redis/config/<idEntrenador>", methods=["DELETE"])
def redis_eliminar_config(idEntrenador):
    """Elimina la configuración de un entrenador y sus índices."""
    try:
        eliminada = redis_dao.eliminar_config(idEntrenador)
        if not eliminada:
            return jsonify({"ok": False, "data": None,
                            "mensaje": f"No existe configuración para {idEntrenador}"})
        return jsonify({"ok": True, "data": {"idEntrenador": idEntrenador},
                        "mensaje": f"Configuración de {idEntrenador} eliminada"})
    except Exception as e:
        return jsonify({"ok": False, "data": None,
                        "mensaje": f"Error al eliminar configuración: {e}"})


@app.route("/redis/buscar")
def redis_buscar():
    """
    Busca entrenadores por uno o más atributos usando los índices invertidos.
    """
    try:
        idioma = request.args.get("idioma", "").strip() or None
        tema = request.args.get("tema", "").strip() or None
        medalla = request.args.get("medalla", "").strip() or None
        notif_raw = request.args.get("notificaciones", "").strip().lower()

        if notif_raw in ("true", "false"):
            resultados = redis_dao.buscar_por_notificaciones(notif_raw == "true")
        elif sum(x is not None for x in (idioma, tema, medalla)) > 1:
            resultados = redis_dao.buscar_combinado(idioma, tema, medalla)
        elif idioma:
            resultados = redis_dao.buscar_por_idioma(idioma)
        elif tema:
            resultados = redis_dao.buscar_por_tema(tema)
        elif medalla:
            resultados = redis_dao.buscar_por_medalla(medalla)
        else:
            return jsonify({"ok": False, "data": None,
                            "mensaje": "Indicá al menos un filtro: idioma, tema, medalla o notificaciones"})

        return jsonify({
            "ok": True,
            "data": {"cantidad": len(resultados), "entrenadores": resultados},
            "mensaje": f"Se encontraron {len(resultados)} entrenadores",
        })
    except Exception as e:
        return jsonify({"ok": False, "data": None,
                        "mensaje": f"Error en la búsqueda: {e}"})


@app.route("/redis/estado")
def redis_estado():
    """Conteos generales de la base Redis (para la demo)."""
    try:
        estado = redis_dao.contar_estado_general()
        return jsonify({"ok": True, "data": estado,
                        "mensaje": "Estado de Redis en Pokengue"})
    except Exception as e:
        return jsonify({"ok": False, "data": None,
                        "mensaje": f"Error al obtener estado: {e}"})
    
if __name__ == "__main__":
    app.run(debug=True)
