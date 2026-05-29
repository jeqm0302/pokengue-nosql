class Pokemon:
    def __init__(self, idPokemon:str, especie:str, nombre:str, peso:float, altura:float, foto:str, tipo:list[str]):
        self.idPokemon:str = idPokemon
        self.especie:str = especie
        self.nombre:str = nombre
        self.peso:float = peso
        self.altura:float = altura
        self.foto:str = foto
        self.tipo:list[str] = tipo
