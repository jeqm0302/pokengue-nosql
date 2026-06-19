from db.ConexionNeo4j import ConexionNeo4j


class Neo4jDAO:

    def __init__(self):
        self.conn = ConexionNeo4j()

    def crear_constraints(self):
        with self.conn.obtener_session() as sesion:
            sesion.run(
                "CREATE CONSTRAINT entrenador_id_unico IF NOT EXISTS "
                "FOR (e:Entrenador) REQUIRE e.idEntrenador IS UNIQUE"
            )
            sesion.run(
                "CREATE CONSTRAINT pokemon_id_unico IF NOT EXISTS "
                "FOR (p:Pokemon) REQUIRE p.idPokemon IS UNIQUE"
            )

    def cargar_entrenador(self, idEntrenador, nombre, apellido, medallas):
        consulta = """
        MERGE (e:Entrenador {idEntrenador: $idEntrenador})
        SET e.nombre = $nombre,
            e.apellido = $apellido,
            e.medallas = $medallas
        RETURN e
        """
        with self.conn.obtener_session() as sesion:
            resultado = sesion.run(
                consulta,
                idEntrenador=idEntrenador,
                nombre=nombre,
                apellido=apellido,
                medallas=medallas,
            )
            registro = resultado.single()
            return dict(registro["e"]) if registro else None

    def cargar_pokemon(self, idPokemon, especie, nombre, tipo, peso, altura):
        consulta = """
        MERGE (p:Pokemon {idPokemon: $idPokemon})
        SET p.especie = $especie,
            p.nombre = $nombre,
            p.tipo = $tipo,
            p.peso = $peso,
            p.altura = $altura
        RETURN p
        """
        with self.conn.obtener_session() as sesion:
            resultado = sesion.run(
                consulta,
                idPokemon=idPokemon,
                especie=especie,
                nombre=nombre,
                tipo=tipo,
                peso=peso,
                altura=altura,
            )
            registro = resultado.single()
            return dict(registro["p"]) if registro else None

    def crear_relacion_tiene(self, idEntrenador, idPokemon, en_equipo):
        consulta = """
        MATCH (e:Entrenador {idEntrenador: $idEntrenador})
        MATCH (p:Pokemon {idPokemon: $idPokemon})
        MERGE (e)-[r:TIENE]->(p)
        SET r.en_equipo = $en_equipo
        RETURN r
        """
        with self.conn.obtener_session() as sesion:
            resultado = sesion.run(
                consulta,
                idEntrenador=idEntrenador,
                idPokemon=idPokemon,
                en_equipo=en_equipo,
            )
            return resultado.single() is not None

    def crear_amistad(self, id1, id2):
        consulta = """
        MATCH (a:Entrenador {idEntrenador: $id_menor})
        MATCH (b:Entrenador {idEntrenador: $id_mayor})
        MERGE (a)-[r:ES_AMIGO_DE]->(b)
        RETURN r
        """
        id_menor, id_mayor = sorted([id1, id2])
        with self.conn.obtener_session() as sesion:
            resultado = sesion.run(consulta, id_menor=id_menor, id_mayor=id_mayor)
            return resultado.single() is not None

    def obtener_entrenador(self, idEntrenador):
        consulta = """
        MATCH (e:Entrenador {idEntrenador: $idEntrenador})
        RETURN e
        """
        with self.conn.obtener_session() as sesion:
            resultado = sesion.run(consulta, idEntrenador=idEntrenador)
            registro = resultado.single()
            return dict(registro["e"]) if registro else None

    def recomendar_amigos(self, idEntrenador):
        consulta = """
        MATCH (yo:Entrenador {idEntrenador: $idEntrenador})-[:ES_AMIGO_DE]-(amigo:Entrenador)
              -[:ES_AMIGO_DE]-(candidato:Entrenador)
        WHERE candidato.idEntrenador <> $idEntrenador
          AND NOT (yo)-[:ES_AMIGO_DE]-(candidato)
        RETURN candidato, count(DISTINCT amigo) AS amigos_en_comun
        ORDER BY amigos_en_comun DESC, candidato.idEntrenador
        """
        with self.conn.obtener_session() as sesion:
            resultado = sesion.run(consulta, idEntrenador=idEntrenador)
            recomendaciones = []
            for registro in resultado:
                candidato = dict(registro["candidato"])
                candidato["amigos_en_comun"] = registro["amigos_en_comun"]
                recomendaciones.append(candidato)
            return recomendaciones

    def detectar_rivales_potenciales(self, idEntrenador, limite=10):
        consulta = """
        MATCH (yo:Entrenador {idEntrenador: $idEntrenador})-[:TIENE]->(p:Pokemon)
        MATCH (otro:Entrenador)-[:TIENE]->(p)
        WHERE otro.idEntrenador <> $idEntrenador
          AND NOT (yo)-[:ES_AMIGO_DE]-(otro)
        RETURN DISTINCT otro.idEntrenador AS idEntrenador,
               otro.nombre AS nombre,
               otro.apellido AS apellido,
               count(DISTINCT p) AS pokemons_en_comun,
               collect(DISTINCT p.nombre) AS nombres_pokemons
        ORDER BY pokemons_en_comun DESC
        LIMIT $limite
        """
        with self.conn.obtener_session() as sesion:
            resultado = sesion.run(consulta, idEntrenador=idEntrenador, limite=limite)
            rivales = []
            for record in resultado:
                rivales.append({
                    "idEntrenador": record["idEntrenador"],
                    "nombre": record["nombre"],
                    "apellido": record["apellido"],
                    "pokemons_en_comun": record["pokemons_en_comun"],
                    "nombres_pokemons": record["nombres_pokemons"]
                })
            return rivales

    def contar_estado_general(self):
        consulta = """
        CALL () { MATCH (e:Entrenador) RETURN count(e) AS entrenadores }
        CALL () { MATCH (p:Pokemon) RETURN count(p) AS pokemons }
        CALL () { MATCH ()-[r:TIENE]->() RETURN count(r) AS tiene }
        CALL () { MATCH ()-[r:ES_AMIGO_DE]->() RETURN count(r) AS amistades }
        RETURN entrenadores, pokemons, tiene, amistades
        """
        with self.conn.obtener_session() as sesion:
            resultado = sesion.run(consulta)
            return resultado.single().data()

    def limpiar_base(self):
        with self.conn.obtener_session() as sesion:
            sesion.run("MATCH (n) DETACH DELETE n")
