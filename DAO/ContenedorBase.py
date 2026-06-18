from bson import ObjectId
from pymongo import ReturnDocument
from db.ConexionMongo import ConexionMongo

class ContenedorBase:
    def __init__(self, nombreColeccion:str):
        db = ConexionMongo().obtener_db()
        self.coleccion = db[nombreColeccion]
        self._db = db

    def siguiente_id(self, prefijo: str, campo_id: str) -> str:
        nombre = self.coleccion.name

        max_num = 0
        for doc in self.coleccion.find({}, {campo_id: 1, "_id": 0}):
            partes = str(doc.get(campo_id, "")).split("-")
            if len(partes) == 2 and partes[1].isdigit():
                max_num = max(max_num, int(partes[1]))

        # Si el counter no existe o quedó atrás del máximo real, lo sincroniza
        self._db["counters"].update_one(
            {"_id": nombre, "seq": {"$lt": max_num}},
            {"$set": {"seq": max_num}},
        )

        resultado = self._db["counters"].find_one_and_update(
            {"_id": nombre},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return f"{prefijo}-{resultado['seq']:03d}"
    
    def insertar(self, documento:dict):
        resultado = self.coleccion.insert_one(documento)
        return str(resultado.inserted_id)
    
    def buscar_por_id(self, id):
        return self.coleccion.find_one({"_id": ObjectId(id)})
    
    def buscar_uno(self, filtro:dict):
        return self.coleccion.find_one(filtro)
    
    def buscar_varios(self, filtro={}):
        return list(self.coleccion.find(filtro))
    
    def actualizar(self, id, datos):
        resultado = self.coleccion.update_one(
            {"_id": ObjectId(id)},
            {"$set": datos}
        )
    
    def eliminar(self, id):
        resultado = self.coleccion.delete_one({"_id": ObjectId(id)})
        return resultado.deleted_count > 0
    
    