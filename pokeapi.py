import requests
 
BASE_URL = "https://pokeapi.co/api/v2"
 
def get_pokemon(nombre_o_id):
    """Obtiene un Pokémon por nombre o ID desde la PokeAPI."""
    try:
        response = requests.get(f"{BASE_URL}/pokemon/{nombre_o_id}")
        response.raise_for_status()
        data = response.json()
 
        return {
            "id": data["id"],
            "nombre": data["name"].capitalize(),
            "altura": data["height"],
            "peso": data["weight"],
            "tipos": [t["type"]["name"] for t in data["types"]],
            "sprite": data["sprites"]["other"]["official-artwork"]["front_default"]
                      or data["sprites"]["front_default"],
        }
    except requests.exceptions.HTTPError:
        return None
    except Exception as e:
        print(f"Error al obtener Pokémon: {e}")
        return None
 
 
def get_lista_pokemons(limite=200, offset=0):
    """Obtiene una lista paginada de Pokémon."""
    try:
        response = requests.get(f"{BASE_URL}/pokemon", params={"limit": limite, "offset": offset})
        response.raise_for_status()
        data = response.json()
        return {
            "total": data["count"],
            "pokemons": [p["name"] for p in data["results"]],
        }
    except Exception as e:
        print(f"Error al obtener lista: {e}")
        return None