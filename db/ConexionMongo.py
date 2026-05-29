from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson import ObjectId
import os
class ConexionMongo:
    
    _instancia = None
    _cliente = None
    _db = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia

    def conectar(self):
        if self._cliente is None:
            uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
            nombre_db = os.getenv("MONGO_DB", "famedic")
            try:
                self._cliente = MongoClient(uri)
                self._cliente.admin.command("ping")
                self._db = self._cliente[nombre_db]
                print("Conexión a MongoDB exitosa")
            except ConnectionFailure as e:
                raise Exception(f"No se pudo conectar a MongoDB: {e}")
        return self._db

    def obtener_db(self):
        if self._db is None:
            return self.conectar()
        return self._db

    def cerrar(self):
        if self._cliente:
            self._cliente.close()
            self._cliente = None
            self._db = None