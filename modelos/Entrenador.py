
class Entrenador:
    def __init__(self,idEntrenador:str, nombre:str, apellido:str, medallas:list[str]):
        self.idEntrenador:str = idEntrenador
        self.nombre:str = nombre
        self.apellido:str = apellido
        self.medallas:list[str] = medallas