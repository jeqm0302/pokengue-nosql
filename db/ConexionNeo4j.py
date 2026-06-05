import os
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable


class ConexionNeo4j:
    _instancia = None
    _driver = None
    _database = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia

    def conectar(self):
        if self._driver is None:
            uri = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
            usuario = os.getenv("NEO4J_USER", "neo4j")
            contrasena = os.getenv("NEO4J_PASSWORD", "pokengue")
            self._database = os.getenv("NEO4J_DATABASE", "neo4j")
            try:
                self._driver = GraphDatabase.driver(uri, auth=(usuario, contrasena))
                self._driver.verify_connectivity()  # verifica conexión
            except (Neo4jError, ServiceUnavailable) as e:
                self._driver = None
                self._database = None
                raise Exception(f"No se pudo conectar a Neo4j: {e}")
        return self._driver

    def obtener_driver(self):
        if self._driver is None:
            self.conectar()
        return self._driver

    def obtener_session(self):
        driver = self.obtener_driver()
        return driver.session(database=self._database)

    def cerrar(self):
        if self._driver:
            self._driver.close()
            self._driver = None
            self._database = None
