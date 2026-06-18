import re
from DAO.ContenedorBase import ContenedorBase
 
class EntrenadorDAO(ContenedorBase):
    def __init__(self):
        super().__init__("entrenador")
 
    def buscar_por_id(self, idEntrenador: str):
        return self.buscar_uno({"idEntrenador": idEntrenador})
 
    def buscar_por_nombre(self, nombre: str = "", apellido: str = ""):
        filtro = {}
        if nombre:
            filtro["nombre"] = {"$regex": nombre, "$options": "i"}
        if apellido:
            filtro["apellido"] = {"$regex": apellido, "$options": "i"}
        return self.buscar_varios(filtro)
 
    def buscar_por_medalla(self, medalla: str):
        return self.buscar_varios({"medallas": {"$regex": medalla, "$options": "i"}})
 
    def listar_todos(self):
        return self.buscar_varios()
 
 
class PokemonDAO(ContenedorBase):
    def __init__(self):
        super().__init__("pokemons")
 
    def buscar_por_id(self, idPokemon: str):
        return self.buscar_uno({"idPokemon": idPokemon})
 
    def buscar_por_nombre(self, nombre: str):
        return self.buscar_varios({
            "$or": [
                {"nombre":  {"$regex": nombre, "$options": "i"}},
                {"especie": {"$regex": nombre, "$options": "i"}},
            ]
        })
 
    def buscar_por_tipo(self, tipo: str):
        return self.buscar_varios({"tipo": {"$regex": tipo, "$options": "i"}})
 
    def buscar_por_peso(self, min_peso: float = None, max_peso: float = None):
        filtro = {}
        if min_peso is not None:
            filtro.setdefault("peso", {})["$gte"] = min_peso
        if max_peso is not None:
            filtro.setdefault("peso", {})["$lte"] = max_peso
        return self.buscar_varios(filtro)
 
    def buscar_por_altura(self, min_altura: float = None, max_altura: float = None):
        filtro = {}
        if min_altura is not None:
            filtro.setdefault("altura", {})["$gte"] = min_altura
        if max_altura is not None:
            filtro.setdefault("altura", {})["$lte"] = max_altura
        return self.buscar_varios(filtro)
 
    def listar_todos(self):
        return self.buscar_varios()