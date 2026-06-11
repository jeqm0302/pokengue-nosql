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
            "habilidades": [a["ability"]["name"] for a in data["abilities"]],
            "stats": {s["stat"]["name"]: s["base_stat"] for s in data["stats"]},
            "sprite": data["sprites"]["other"]["official-artwork"]["front_default"]
                      or data["sprites"]["front_default"],
        }
    except requests.exceptions.HTTPError:
        return None
    except Exception as e:
        print(f"Error al obtener Pokémon: {e}")
        return None


def _fetch_detalle_pokemon(url):
    """Obtiene los datos específicos de un pokémon dado su URL de detalle."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        return {
            "nroPokedex": data["id"],
            "especie":    data["name"].capitalize(),
            "nombre":     data["name"].capitalize(),
            "peso":       round(data["weight"] / 10, 2),    # hectogramos → kg
            "altura":     round(data["height"] / 10, 2),    # decímetros  → m
            "foto":       (data["sprites"]["other"]["official-artwork"]["front_default"]
                           or data["sprites"]["front_default"]),
            "tipo":       [t["type"]["name"].capitalize() for t in data["types"]],
        }
    except Exception as e:
        print(f"Error al obtener detalle: {e}")
        return None


def get_lista_pokemons(limite=1350, offset=0):
    """Obtiene todos los pokémons con sus datos completos para cargar en la pokedex."""
    try:
        response = requests.get(f"{BASE_URL}/pokemon", params={"limit": limite, "offset": offset})
        response.raise_for_status()
        data = response.json()

        pokemons = []
        total = len(data["results"])

        for i, entry in enumerate(data["results"], 1):
            print(f"Obteniendo {i}/{total}: {entry['name']}...")
            detalle = _fetch_detalle_pokemon(entry["url"])
            if detalle:
                pokemons.append(detalle)

        return {
            "total":    data["count"],
            "pokemons": pokemons,
        }
    except Exception as e:
        print(f"Error al obtener lista: {e}")
        return None