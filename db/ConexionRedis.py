import os
import redis
from redis.exceptions import ConnectionError as RedisConnectionError


class ConexionRedis:
    """Singleton de conexión a Redis (mismo patrón que ConexionMongo y ConexionNeo4j)."""

    _instancia = None
    _cliente = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia

    def conectar(self):
        if self._cliente is None:
            host = os.getenv("REDIS_HOST", "localhost")
            puerto = int(os.getenv("REDIS_PORT", "6379"))
            db = int(os.getenv("REDIS_DB", "0"))
            try:
                # decode_responses=True -> devuelve str en vez de bytes
                self._cliente = redis.Redis(
                    host=host, port=puerto, db=db, decode_responses=True
                )
                self._cliente.ping()  # verifica conexión
                print("Conexión a Redis exitosa")
            except RedisConnectionError as e:
                self._cliente = None
                raise Exception(f"No se pudo conectar a Redis: {e}")
        return self._cliente

    def obtener_cliente(self):
        if self._cliente is None:
            return self.conectar()
        return self._cliente

    def cerrar(self):
        if self._cliente:
            self._cliente.close()
            self._cliente = None
