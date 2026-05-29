from bson import ObjectId

from db.ConexionMongo import ConexionMongo

class ContenedorBase:
    def __init__(self, nombreColeccion:str):
        db = ConexionMongo().obtener_db()
        self.coleccion = db[nombreColeccion]    
    
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
    
    