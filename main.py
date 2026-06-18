import random
from flask import Flask, render_template,url_for, session, redirect, request, jsonify
from pokeapi import get_pokemon, get_lista_pokemons
from services.Neo4jService import Neo4jService
from DAO.CassandraDAO import CassandraDAO
from DAO.RedisDAO import RedisDAO
<<<<<<< Updated upstream
from modelos.RegistroCombate import RegistroCombate
from uuid import uuid4
from datetime import date, time

=======
from flask import request, jsonify, render_template
from DAO.MongoDAO import EntrenadorDAO, PokemonDAO
from bson import ObjectId
>>>>>>> Stashed changes
app = Flask(__name__)
neo4j_service = Neo4jService()
redis_dao = RedisDAO()
from sheets import get_entrenadores, get_pokemons_domesticados, get_combates
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db     = client["pokengue"]

cassandra_dao = CassandraDAO()

@app.route("/")
def index():
    return render_template("index.html")

# ---------------------------------------------------------------
# Importar arriba en main.py junto al resto de imports:
# from DAO.MongoDAO import EntrenadorDAO, PokemonDAO
# ---------------------------------------------------------------

from flask import request, jsonify, render_template
from DAO.MongoDAO import EntrenadorDAO, PokemonDAO
from bson import ObjectId

entrenador_dao = EntrenadorDAO()
pokemon_dao    = PokemonDAO()

# Helper para limpiar _id de Mongo antes de serializar
def _limpiar(docs):
    if docs is None:
        return None
    if isinstance(docs, list):
        for d in docs:
            d.pop("_id", None)
        return docs
    docs.pop("_id", None)
    return docs


# ---------------------------------------------------------------
# Rutas MongoDB
# ---------------------------------------------------------------

@app.route("/mongo")
def mongo_home():
    return render_template("mongo.html")


# ── Entrenadores ──────────────────────────────────────────────

@app.route("/mongo/entrenadores")
def mongo_entrenadores():
    try:
        id_ent  = request.args.get("id", "").strip()
        nombre  = request.args.get("nombre", "").strip()
        apellido = request.args.get("apellido", "").strip()
        medalla = request.args.get("medalla", "").strip()

        if id_ent:
            resultado = entrenador_dao.buscar_por_id(id_ent)
            data = _limpiar([resultado]) if resultado else []
        elif nombre or apellido:
            data = _limpiar(entrenador_dao.buscar_por_nombre(nombre, apellido))
        elif medalla:
            data = _limpiar(entrenador_dao.buscar_por_medalla(medalla))
        else:
            data = _limpiar(entrenador_dao.listar_todos())

        return jsonify({"ok": True, "data": data, "mensaje": f"{len(data)} resultado(s)"})
    except Exception as e:
        return jsonify({"ok": False, "data": None, "mensaje": str(e)}), 500


# ── Pokémons ──────────────────────────────────────────────────

@app.route("/mongo/pokemons")
def mongo_pokemons():
    try:
        id_pok     = request.args.get("id", "").strip()
        nombre     = request.args.get("nombre", "").strip()
        tipo       = request.args.get("tipo", "").strip()
        peso_min   = request.args.get("peso_min", "").strip()
        peso_max   = request.args.get("peso_max", "").strip()
        altura_min = request.args.get("altura_min", "").strip()
        altura_max = request.args.get("altura_max", "").strip()

        if id_pok:
            resultado = pokemon_dao.buscar_por_id(id_pok)
            data = _limpiar([resultado]) if resultado else []
        elif nombre:
            data = _limpiar(pokemon_dao.buscar_por_nombre(nombre))
        elif tipo:
            data = _limpiar(pokemon_dao.buscar_por_tipo(tipo))
        elif peso_min or peso_max:
            mn = float(peso_min) if peso_min else None
            mx = float(peso_max) if peso_max else None
            data = _limpiar(pokemon_dao.buscar_por_peso(mn, mx))
        elif altura_min or altura_max:
            mn = float(altura_min) if altura_min else None
            mx = float(altura_max) if altura_max else None
            data = _limpiar(pokemon_dao.buscar_por_altura(mn, mx))
        else:
            data = _limpiar(pokemon_dao.listar_todos())

        return jsonify({"ok": True, "data": data, "mensaje": f"{len(data)} resultado(s)"})
    except Exception as e:
        return jsonify({"ok": False, "data": None, "mensaje": str(e)}), 500

@app.route("/pokemon/<nombre_o_id>")
def pokemon(nombre_o_id):
    """Devuelve los datos de un Pokémon en JSON."""
    data = get_pokemon(nombre_o_id.lower())
    if data is None:
        return jsonify({"error": f"Pokémon '{nombre_o_id}' no encontrado"}), 404
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


@app.route("/neo4j/rivales/<idEntrenador>")
def neo4j_rivales(idEntrenador):
    resultado = neo4j_service.detectar_rivales(idEntrenador)
    return jsonify(resultado)


@app.route("/neo4j/estado")
def neo4j_estado():
    resultado = neo4j_service.obtener_estado()
    return jsonify(resultado)

@app.route("/cassandra")
def cassandra_home():
    """Renderiza la página de demo de Cassandra."""
    return render_template("cassandra.html")

@app.route("/cassandra/estado")
def cassandra_estado():
    try:
        cassandra_dao._sesion.execute("SELECT release_version FROM system.local")
        return jsonify({"ok": True, "data": {"conectado": True}, "mensaje": "Cassandra conectada"})
    except Exception as e:
        return jsonify({"ok": False, "data": None,
                        "mensaje": f"Error al conectar con Cassandra: {e}"})


def _row_value(fila, nombre):
    if fila is None:
        return None

    try:
        return fila[nombre]
    except Exception:
        pass

    try:
        return fila.get(nombre)
    except Exception:
        pass

    try:
        return getattr(fila, nombre)
    except Exception:
        return None


def _combate_a_dict(fila):
    if fila is None:
        return None

    combate_id = _row_value(fila, "combate_id")
    result = {
        "combate_id": str(combate_id) if combate_id is not None else None,
        "fecha": str(_row_value(fila, "fecha")) if _row_value(fila, "fecha") is not None else None,
        "hora": str(_row_value(fila, "hora")) if _row_value(fila, "hora") is not None else None,
        "entrenador1": _row_value(fila, "entrenador1"),
        "pokemon1": _row_value(fila, "pokemon1"),
        "resultado": _row_value(fila, "resultado"),
        "entrenador2": _row_value(fila, "entrenador2"),
        "pokemon2": _row_value(fila, "pokemon2"),
    }

    if result["combate_id"] is not None and (
        result["entrenador2"] is None or result["pokemon2"] is None or
        result["entrenador1"] is None or result["pokemon1"] is None
    ):
        try:
            registro_completo = next(iter(cassandra_dao.buscar_por_id(result["combate_id"])), None)
            if registro_completo is not None:
                return {
                    "combate_id": str(_row_value(registro_completo, "combate_id")) if _row_value(registro_completo, "combate_id") is not None else None,
                    "fecha": str(_row_value(registro_completo, "fecha")) if _row_value(registro_completo, "fecha") is not None else None,
                    "hora": str(_row_value(registro_completo, "hora")) if _row_value(registro_completo, "hora") is not None else None,
                    "entrenador1": _row_value(registro_completo, "entrenador1"),
                    "pokemon1": _row_value(registro_completo, "pokemon1"),
                    "resultado": _row_value(registro_completo, "resultado"),
                    "entrenador2": _row_value(registro_completo, "entrenador2"),
                    "pokemon2": _row_value(registro_completo, "pokemon2"),
                }
        except Exception:
            pass

    return result

@app.route("/cassandra/cargar")
def cassandra_cargar():
    try:
        combates = get_combates()
        cassandra_dao.limpiar_todo()
        procesados = cassandra_dao.cargar_masivo(combates)
        return jsonify({"ok": True,
                        "data": {"procesados": procesados},
                        "mensaje": f"Se cargaron {procesados} combates desde Google Sheets."})
    except Exception as e:
        return jsonify({"ok": False, "data": None, "mensaje": str(e)}), 500

@app.route("/cassandra/combates")
def cassandra_listar_todos():
    try:
        filas = list(cassandra_dao.listar_todos())
        return jsonify({"ok": True,
                        "data": [_combate_a_dict(f) for f in filas],
                        "mensaje": f"Se encontraron {len(filas)} combates."})
    except Exception as e:
        return jsonify({"ok": False, "data": None, "mensaje": str(e)}), 500

@app.route("/cassandra/combate", methods=["POST"])
def cassandra_registrar_combate():
    try:
        entrenador1 = request.form.get("entrenador1", "").strip()
        pokemon1 = request.form.get("pokemon1", "").strip()
        entrenador2 = request.form.get("entrenador2", "").strip()
        pokemon2 = request.form.get("pokemon2", "").strip()
        resultado = request.form.get("resultado", "").strip()
        fecha_texto = request.form.get("fecha", "").strip()
        hora_texto = request.form.get("hora", "").strip()

        if not all([entrenador1, pokemon1, entrenador2, pokemon2, resultado, fecha_texto, hora_texto]):
            return jsonify({"ok": False, "data": None,
                            "mensaje": "Faltan datos para registrar el combate."}), 400

        try:
            fecha_combate = date.fromisoformat(fecha_texto)
            hora_combate = time.fromisoformat(hora_texto)
        except ValueError:
            return jsonify({"ok": False, "data": None,
                            "mensaje": "Formato de fecha u hora inválido. Usa YYYY-MM-DD y HH:MM."}), 400

        combate_id = uuid4()
        combate = RegistroCombate(
            combate_id, fecha_combate, hora_combate,
            entrenador1, pokemon1, resultado,
            entrenador2, pokemon2,
        )
        cassandra_dao.agregar(combate)
        return jsonify({"ok": True, "data": _combate_a_dict(combate),
                        "mensaje": "Combate registrado en Cassandra"})
    except Exception as e:
        return jsonify({"ok": False, "data": None,
                        "mensaje": str(e)}), 500

@app.route("/cassandra/combate/<combate_id>")
def cassandra_buscar_por_id(combate_id):
    try:
        rows = cassandra_dao.buscar_por_id(combate_id)
        fila = next(iter(rows), None)
        if fila is None:
            return jsonify({"ok": False, "data": None,
                            "mensaje": f"No se encontró combate con id {combate_id}."}), 404
        return jsonify({"ok": True, "data": _combate_a_dict(fila),
                        "mensaje": "Combate encontrado."})
    except Exception as e:
        return jsonify({"ok": False, "data": None,
                        "mensaje": str(e)}), 500

@app.route("/cassandra/fecha")
def cassandra_buscar_por_fecha():
    try:
        fecha_texto = request.args.get("fecha", "").strip()
        if not fecha_texto:
            return jsonify({"ok": False, "data": None,
                            "mensaje": "Debés indicar una fecha como YYYY-MM-DD."}), 400
        fecha_combate = date.fromisoformat(fecha_texto)
        filas = list(cassandra_dao.buscar_por_fecha(fecha_combate))
        return jsonify({"ok": True,
                        "data": [_combate_a_dict(f) for f in filas],
                        "mensaje": f"Se encontraron {len(filas)} combates en {fecha_texto}."})
    except ValueError:
        return jsonify({"ok": False, "data": None,
                        "mensaje": "Formato de fecha inválido. Usa YYYY-MM-DD."}), 400
    except Exception as e:
        return jsonify({"ok": False, "data": None,
                        "mensaje": str(e)}), 500

@app.route("/cassandra/jugador1/<jugador>")
def cassandra_buscar_por_jugador1(jugador):
    try:
        filas = list(cassandra_dao.buscar_por_jugador1(jugador))
        return jsonify({"ok": True,
                        "data": [_combate_a_dict(f) for f in filas],
                        "mensaje": f"Se encontraron {len(filas)} combates para {jugador}."})
    except Exception as e:
        return jsonify({"ok": False, "data": None,
                        "mensaje": str(e)}), 500

@app.route("/cassandra/jugador2/<jugador>")
def cassandra_buscar_por_jugador2(jugador):
    try:
        filas = list(cassandra_dao.buscar_por_jugador2(jugador))
        return jsonify({"ok": True,
                        "data": [_combate_a_dict(f) for f in filas],
                        "mensaje": f"Se encontraron {len(filas)} combates para {jugador}."})
    except Exception as e:
        return jsonify({"ok": False, "data": None,
                        "mensaje": str(e)}), 500

@app.route("/cassandra/combate/<combate_id>", methods=["DELETE"])
def cassandra_eliminar_combate(combate_id):
    try:
        rows = cassandra_dao.buscar_por_id(combate_id)
        fila = next(iter(rows), None)
        if fila is None:
            return jsonify({"ok": False, "data": None,
                            "mensaje": f"No se encontró combate con id {combate_id}."}), 404
        combate = RegistroCombate(
            combate_id, fila.fecha, fila.hora,
            fila.entrenador1, fila.pokemon1, fila.resultado,
            fila.entrenador2, fila.pokemon2,
        )
        cassandra_dao.eliminar(combate)
        return jsonify({"ok": True, "data": {"combate_id": combate_id},
                        "mensaje": "Combate eliminado de Cassandra."})
    except Exception as e:
        return jsonify({"ok": False, "data": None,
                        "mensaje": str(e)}), 500

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
    
@app.route("/mongo/pokedex/especies")
def mongo_pokedex_especies():
    try:
        especies = list(db["pokedex"].find(
            {}, {"_id": 0, "nroPokedex": 1, "especie": 1, "foto": 1}
        ))
        especies.sort(key=lambda x: x.get("nroPokedex", 0))
        return jsonify({"ok": True, "data": especies})
    except Exception as e:
        return jsonify({"ok": False, "data": None, "mensaje": str(e)}), 500


@app.route("/mongo/entrenadores/nuevo", methods=["POST"])
def mongo_nuevo_entrenador():
    try:
        body     = request.get_json()
        nombre   = body.get("nombre",   "").strip()
        apellido = body.get("apellido", "").strip()
        medallas = [m.strip() for m in body.get("medallas", "").split(",") if m.strip()]

        if not nombre:
            return jsonify({"ok": False, "data": None, "mensaje": "El nombre es obligatorio"})

        idEntrenador = entrenador_dao.siguiente_id("ENT", "idEntrenador")
        doc = {"idEntrenador": idEntrenador, "nombre": nombre,
               "apellido": apellido, "medallas": medallas}
        entrenador_dao.insertar(doc)
        doc.pop("_id", None)
        return jsonify({"ok": True, "data": doc,
                        "mensaje": f"Entrenador {nombre} cargado con ID {idEntrenador}"})
    except Exception as e:
        return jsonify({"ok": False, "data": None, "mensaje": str(e)}), 500


@app.route("/mongo/pokemons/nuevo", methods=["POST"])
def mongo_nuevo_pokemon():
    try:
        body   = request.get_json()
        nombre = body.get("nombre", "").strip()
        nro    = body.get("nroPokedex")

        if not nombre or nro is None:
            return jsonify({"ok": False, "data": None,
                            "mensaje": "nombre y especie son obligatorios"})

        base = db["pokedex"].find_one({"nroPokedex": int(nro)})
        if not base:
            return jsonify({"ok": False, "data": None,
                            "mensaje": "Especie no encontrada en la Pokédex"})

        idPokemon = pokemon_dao.siguiente_id("POK", "idPokemon")
        doc = {
            "idPokemon": idPokemon,
            "especie":   base["especie"],
            "nombre":    nombre,
            "peso":      round(base["peso"]   * random.uniform(0.9, 1.1), 2),
            "altura":    round(base["altura"] * random.uniform(0.9, 1.1), 2),
            "foto":      base.get("foto", ""),
            "tipo":      base.get("tipo", []),
        }
        pokemon_dao.insertar(doc)
        doc.pop("_id", None)
        return jsonify({"ok": True, "data": doc,
                        "mensaje": f"Pokémon {nombre} cargado con ID {idPokemon}"})
    except Exception as e:
        return jsonify({"ok": False, "data": None, "mensaje": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
