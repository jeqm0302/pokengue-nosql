from modelos.Entrenador import Entrenador
from modelos.Pokemon import Pokemon
from DAO.Neo4jDAO import Neo4jDAO


class Neo4jService:

    def __init__(self):
        self.dao = Neo4jDAO()

    def cargar_entrenador(self, datos):
        try:
            idEntrenador = datos.get("idEntrenador", "").strip()
            nombre = datos.get("nombre", "").strip()
            apellido = datos.get("apellido", "").strip()
            medallas_raw = datos.get("medallas", "")

            if not idEntrenador:
                return {"ok": False, "data": None, "mensaje": "Falta el ID del entrenador"}

            medallas = [m.strip() for m in medallas_raw.split(",") if m.strip()]
            entrenador = Entrenador(idEntrenador, nombre, apellido, medallas)
            self.dao.cargar_entrenador(
                entrenador.idEntrenador,
                entrenador.nombre,
                entrenador.apellido,
                entrenador.medallas,
            )
            return {
                "ok": True,
                "data": entrenador.__dict__,
                "mensaje": f"Entrenador {entrenador.idEntrenador} creado",
            }
        except Exception as e:
            return {"ok": False, "data": None,
                    "mensaje": f"Error al cargar entrenador: {e}"}

    def cargar_pokemon(self, datos):
        try:
            idPokemon = datos.get("idPokemon", "").strip()
            especie = datos.get("especie", "").strip()
            nombre = datos.get("nombre", "").strip()
            tipo_raw = datos.get("tipo", "")
            peso_raw = datos.get("peso", "").strip()
            altura_raw = datos.get("altura", "").strip()

            if not idPokemon:
                return {"ok": False, "data": None, "mensaje": "Falta el ID del pokémon"}

            tipo = [t.strip() for t in tipo_raw.split(",") if t.strip()]
            peso = float(peso_raw) if peso_raw else 0.0
            altura = float(altura_raw) if altura_raw else 0.0

            pokemon = Pokemon(idPokemon, especie, nombre, peso, altura, "", tipo)
            self.dao.cargar_pokemon(
                pokemon.idPokemon,
                pokemon.especie,
                pokemon.nombre,
                pokemon.tipo,
                pokemon.peso,
                pokemon.altura,
            )
            return {
                "ok": True,
                "data": pokemon.__dict__,
                "mensaje": f"Pokémon {pokemon.idPokemon} creado",
            }
        except ValueError:
            return {"ok": False, "data": None,
                    "mensaje": "Peso y altura deben ser números"}
        except Exception as e:
            return {"ok": False, "data": None,
                    "mensaje": f"Error al cargar pokémon: {e}"}

    def crear_tiene(self, datos):
        try:
            idEntrenador = datos.get("idEntrenador", "").strip()
            idPokemon = datos.get("idPokemon", "").strip()
            en_equipo = datos.get("en_equipo") == "on"

            if not idEntrenador or not idPokemon:
                return {"ok": False, "data": None,
                        "mensaje": "Faltan IDs de entrenador o pokémon"}

            creada = self.dao.crear_relacion_tiene(idEntrenador, idPokemon, en_equipo)
            if not creada:
                return {"ok": False, "data": None,
                        "mensaje": f"No existe el entrenador {idEntrenador} o el pokémon {idPokemon}"}

            return {
                "ok": True,
                "data": {"idEntrenador": idEntrenador, "idPokemon": idPokemon, "en_equipo": en_equipo},
                "mensaje": f"{idEntrenador} ahora TIENE a {idPokemon}",
            }
        except Exception as e:
            return {"ok": False, "data": None,
                    "mensaje": f"Error al crear relación TIENE: {e}"}

    def crear_amistad(self, datos):
        try:
            id1 = datos.get("id1", "").strip()
            id2 = datos.get("id2", "").strip()

            if not id1 or not id2:
                return {"ok": False, "data": None,
                        "mensaje": "Faltan los dos IDs de entrenador"}
            if id1 == id2:
                return {"ok": False, "data": None,
                        "mensaje": "Un entrenador no puede ser amigo de sí mismo"}

            creada = self.dao.crear_amistad(id1, id2)
            if not creada:
                return {"ok": False, "data": None,
                        "mensaje": f"No existe el entrenador {id1} o {id2}"}

            return {
                "ok": True,
                "data": {"id1": id1, "id2": id2},
                "mensaje": f"{id1} y {id2} ahora son amigos",
            }
        except Exception as e:
            return {"ok": False, "data": None,
                    "mensaje": f"Error al crear amistad: {e}"}

    def obtener_info(self, id):
        try:
            entrenador_dict = self.dao.obtener_entrenador(id)
            if entrenador_dict is None:
                return {"ok": False, "data": None,
                        "mensaje": f"No se encontró el entrenador con ID {id}"}

            entrenador = Entrenador(**entrenador_dict)
            pokemons_dicts = self.dao.obtener_pokemons_de(id)
            amigos_dicts = self.dao.obtener_amigos(id)
            amigos = [Entrenador(**d).__dict__ for d in amigos_dicts]

            return {
                "ok": True,
                "data": {
                    "entrenador": entrenador.__dict__,
                    "pokemons": pokemons_dicts,
                    "amigos": amigos,
                },
                "mensaje": f"Info de {id}",
            }
        except Exception as e:
            return {"ok": False, "data": None,
                    "mensaje": f"Error al obtener info: {e}"}

    def recomendar(self, id):
        try:
            entrenador_dict = self.dao.obtener_entrenador(id)
            if entrenador_dict is None:
                return {"ok": False, "data": None,
                        "mensaje": f"No se encontró el entrenador con ID {id}"}

            entrenador = Entrenador(**entrenador_dict)
            recomendaciones = self.dao.recomendar_amigos(id)

            return {
                "ok": True,
                "data": {
                    "entrenador": entrenador.__dict__,
                    "recomendaciones": recomendaciones,
                },
                "mensaje": f"Recomendaciones para {id}",
            }
        except Exception as e:
            return {"ok": False, "data": None,
                    "mensaje": f"Error al recomendar amigos: {e}"}

    def obtener_estado(self):
        try:
            estado = self.dao.contar_estado_general()
            return {"ok": True, "data": estado, "mensaje": "Estado del grafo Pokengue"}
        except Exception as e:
            return {"ok": False, "data": None,
                    "mensaje": f"Error al obtener estado del grafo: {e}"}
