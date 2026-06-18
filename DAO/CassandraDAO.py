from uuid import uuid4
from db.ConexionCassandra import ConexionCassandra
from cassandra.query import BatchStatement
from modelos.RegistroCombate import RegistroCombate

class CassandraDAO:
    CREAR_TABLA_REGISTRO_COMBATES = """
        CREATE TABLE IF NOT EXISTS registro_combates (
            combate_id  text,
            fecha       date, 
            hora        time, 
            entrenador1 text, 
            pokemon1    text, 
            resultado   text, 
            entrenador2 text, 
            pokemon2    text,
            PRIMARY KEY (combate_id, fecha, hora))
            WITH CLUSTERING ORDER BY (fecha DESC, hora DESC);
    """
    CREAR_TABLA_REGISTRO_COMBATE_POR_FECHA = """
        CREATE TABLE IF NOT EXISTS registro_combates_por_fecha (
            combate_id  text,
            fecha       date, 
            hora        time, 
            entrenador1 text, 
            resultado   text, 
            entrenador2 text, 
            PRIMARY KEY (fecha, hora, combate_id))
            WITH CLUSTERING ORDER BY (hora DESC, combate_id ASC);
    """
    CREAR_TABLA_REGISTRO_COMBATE_POR_JUGADOR_1 = """
        CREATE TABLE IF NOT EXISTS registro_combates_por_jugador_1 (
            combate_id  text,
            fecha       date, 
            hora        time, 
            entrenador1 text, 
            pokemon1    text, 
            resultado   text, 
            PRIMARY KEY (entrenador1, fecha, combate_id)) 
            WITH CLUSTERING ORDER BY (fecha DESC, combate_id ASC);
    """
    CREAR_TABLA_REGISTRO_COMBATE_POR_JUGADOR_2 = """
        CREATE TABLE IF NOT EXISTS registro_combates_por_jugador_2 (
            combate_id  text,
            fecha       date, 
            hora        time, 
            entrenador2 text, 
            pokemon2    text, 
            resultado   text, 
            PRIMARY KEY (entrenador2, fecha, combate_id)) 
            WITH CLUSTERING ORDER BY (fecha DESC, combate_id ASC);
    """

    def __init__(self):
        self._sesion = ConexionCassandra().conectar()
        self._sesion.execute(self.CREAR_TABLA_REGISTRO_COMBATES)
        self._sesion.execute(self.CREAR_TABLA_REGISTRO_COMBATE_POR_JUGADOR_1)
        self._sesion.execute(self.CREAR_TABLA_REGISTRO_COMBATE_POR_JUGADOR_2)
        self._sesion.execute(self.CREAR_TABLA_REGISTRO_COMBATE_POR_FECHA)

    def agregar(self, combate):
        batch = BatchStatement()

        query1 = """
        INSERT INTO registro_combates
        (
            combate_id,
            entrenador1,
            entrenador2,
            pokemon1,
            pokemon2,
            resultado,
            fecha,
            hora
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """
        batch.add(
            query1,
            (
                combate.combate_id,
                combate.entrenador1,
                combate.entrenador2,
                combate.pokemon1,
                combate.pokemon2,
                combate.resultado,
                combate.fecha,
                combate.hora,
            )
        )

        query2 = """
        INSERT INTO registro_combates_por_fecha
        (
            fecha,
            hora,
            combate_id,
            entrenador1,
            resultado,
            entrenador2
        )
        VALUES (%s,%s,%s,%s,%s,%s)
        """
        batch.add(
            query2,
            (
                combate.fecha,
                combate.hora,
                combate.combate_id,
                combate.entrenador1,
                combate.resultado,
                combate.entrenador2,
            )
        )

        query3 = """
        INSERT INTO registro_combates_por_jugador_1
        (
            entrenador1,
            fecha,
            combate_id,
            pokemon1,
            resultado,
            hora
        )
        VALUES (%s,%s,%s,%s,%s,%s)
        """
        batch.add(
            query3,
            (
                combate.entrenador1,
                combate.fecha,
                combate.combate_id,
                combate.pokemon1,
                combate.resultado,
                combate.hora,
            )
        )

        query4 = """
        INSERT INTO registro_combates_por_jugador_2
        (
            entrenador2,
            fecha,
            combate_id,
            pokemon2,
            resultado,
            hora
        )
        VALUES (%s,%s,%s,%s,%s,%s)
        """
        batch.add(
            query4,
            (
                combate.entrenador2,
                combate.fecha,
                combate.combate_id,
                combate.pokemon2,
                combate.resultado,
                combate.hora,
            )
        )

        self._sesion.execute(batch)

    def limpiar_todo(self):
        self._sesion.execute("TRUNCATE registro_combates")
        self._sesion.execute("TRUNCATE registro_combates_por_fecha")
        self._sesion.execute("TRUNCATE registro_combates_por_jugador_1")
        self._sesion.execute("TRUNCATE registro_combates_por_jugador_2")

    def cargar_masivo(self, lista_dicts):
        """
        Recibe lista de dicts con claves: fecha, hora, entrenador1, pokemon1,
        resultado, entrenador2, pokemon2. Genera un UUID por cada combate.
        """
        procesados = 0
        for d in lista_dicts:
            combate = RegistroCombate(
                d.get("id", str(uuid4())), d["fecha"], d["hora"],
                d["entrenador1"], d["pokemon1"], d["resultado"],
                d["entrenador2"], d["pokemon2"],
            )
            self.agregar(combate)
            procesados += 1
        return procesados

    def listar_todos(self):
        return self._sesion.execute("SELECT * FROM registro_combates")

    def buscar_por_id(self, combate_id):
        query = """
        SELECT *
        FROM registro_combates
        WHERE combate_id = %s
        """
        return self._sesion.execute(query, (combate_id,))

    def buscar_por_fecha(self, fecha):
        query = """
        SELECT *
        FROM registro_combates_por_fecha
        WHERE fecha = %s
        """
        return self._sesion.execute(query, (fecha,))

    def buscar_por_jugador1(self, jugador):
        query = """
        SELECT *
        FROM registro_combates_por_jugador_1
        WHERE entrenador1 = %s
        """
        return self._sesion.execute(query, (jugador,))

    def buscar_por_jugador2(self, jugador):
        query = """
        SELECT *
        FROM registro_combates_por_jugador_2
        WHERE entrenador2 = %s
        """
        return self._sesion.execute(query, (jugador,))

    def eliminar(self, combate):
        batch = BatchStatement()
        batch.add(
            """
            DELETE FROM registro_combates
            WHERE combate_id=%s
            """,
            (combate.combate_id,)
        )
        batch.add(
            """
            DELETE FROM registro_combates_por_fecha
            WHERE fecha=%s AND hora=%s AND combate_id=%s
            """,
            (
                combate.fecha,
                combate.hora,
                combate.combate_id,
            )
        )
        batch.add(
            """
            DELETE FROM registro_combates_por_jugador_1
            WHERE entrenador1=%s AND fecha=%s AND combate_id=%s
            """,
            (
                combate.entrenador1,
                combate.fecha,
                combate.combate_id,
            )
        )
        batch.add(
            """
            DELETE FROM registro_combates_por_jugador_2
            WHERE entrenador2=%s AND fecha=%s AND combate_id=%s
            """,
            (
                combate.entrenador2,
                combate.fecha,
                combate.combate_id,
            )
        )
        self._sesion.execute(batch)
