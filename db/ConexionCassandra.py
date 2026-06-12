from cassandra.cluster import Cluster;
from cassandra import DriverException;

class ConexionCassandra:

    _cluster = None;
    _sesion = None;
    _instancia = None;

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls);
        return cls._instancia;

    def conectar(self):
        if self._cluster is None:
            try:
                self._cluster = Cluster();
                self._sesion = self._cluster.connect("pokengue");
            except DriverException as e:
                raise Exception(f"Falló la conexión con Cassandra: {e}");
        return self._sesion;

    def inicializarConexion(self):
        if self._cluster is None:
            return self.conectar();
        return self._sesion;

    def cerrar(self):
        if self._cluster:
            self._cluster.shutdown();
            self._sesion = None;
            self._cluster = None;