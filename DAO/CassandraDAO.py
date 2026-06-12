from uuid import uuid4;
from db.ConexionCassandra import ConexionCassandra;

class CassandraDAO:
    CREAR_TABLA_REGISTRO_COMBATES = """
        CREATE TABLE IF NOT EXISTS registro_combates (
            combate_id  uuid, 
            fecha       date, 
            hora        time, 
            entrenador1 text, 
            pokemon1    text, 
            resultado   text, 
            entrenador2 text, 
            pokemon2    text,
            PRIMARY KEY (combate_id, fecha, hora))
            WITH CLUSTERING ORDER BY (fecha DESC, hora DESC);
    """;
    CREAR_TABLA_REGISTRO_COMBATE_POR_FECHA = """ 
        CREATE TABLE IF NOT EXISTS registro_combates_por_fecha (
            combate_id  uuid, 
            fecha       date, 
            hora        time, 
            entrenador1 text, 
            resultado   text, 
            entrenador2 text, 
            PRIMARY KEY (fecha, hora, combate_id))
            WITH CLUSTERING ORDER BY (hora DESC, combate_id ASC);
    """;
    CREAR_TABLA_REGISTRO_COMBATE_POR_JUGADOR_1 = """
        CREATE TABLE IF NOT EXISTS  registro_combates_por_jugador_1 (
            combate_id  uuid, 
            fecha       date, 
            hora        time, 
            entrenador1 text, 
            pokemon1    text, 
            resultado   text, 
            PRIMARY KEY (entrenador1, fecha, combate_id)) 
            WITH CLUSTERING ORDER BY (fecha DESC, combate_id ASC);
    """;
    CREAR_TABLA_REGISTRO_COMBATE_POR_JUGADOR_2 = """
        CREATE TABLE IF NOT EXISTS  registro_combates_por_jugador_2 (
            combate_id  uuid, 
            fecha       date, 
            hora        time, 
            entrenador2 text, 
            pokemon2    text, 
            resultado   text, 
            PRIMARY KEY (entrenador2, fecha, combate_id)) 
            WITH CLUSTERING ORDER BY (fecha DESC, combate_id ASC);
    """;

    def __init__(self):
        self._sesion = ConexionCassandra().conectar();
        self._sesion.execute(self.CREAR_TABLA_REGISTRO_COMBATES);
        self._sesion.execute(self.CREAR_TABLA_REGISTRO_COMBATE_POR_JUGADOR_1);
        self._sesion.execute(self.CREAR_TABLA_REGISTRO_COMBATE_POR_JUGADOR_2);
        self._sesion.execute(self.CREAR_TABLA_REGISTRO_COMBATE_POR_FECHA);

    """
    def prueba1(self):
        combate_id = uuid4();

        query =
        INSERT INTO registro_combates (
            combate_id,
            fecha,
            hora,
            entrenador1,
            pokemon1,
            resultado,
            entrenador2,
            pokemon2
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ;
        self._sesion.execute(query, (
            combate_id,
            "2026-06-12",
            "15:30:00",
            "Ash",
            "Pikachu",
            "Victoria",
            "Gary",
            "Blastoise"
        ));
        return str(combate_id);
        """

