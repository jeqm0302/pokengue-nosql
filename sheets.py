import gspread
from google.oauth2.service_account import Credentials
from datetime import date, time

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

SPREADSHEET_ID = "1Ai_sSEz9aoqN0kYZHo-Q--BD49XW30uZVAJD90B80ro"
CREDENTIALS_FILE = "pokengueCredentials.json"


def get_sheet_as_dicts(nombre_hoja):
    """Lee la hoja como strings puros y devuelve lista de dicts"""
    creds  = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet  = client.open_by_key(SPREADSHEET_ID).worksheet(nombre_hoja)

    valores = sheet.get_all_values()
    if not valores:
        return []

    headers = valores[0]
    return [dict(zip(headers, fila)) for fila in valores[1:]]


def _a_float(valor):
    """Convierte un valor a float manejando coma como separador decimal."""
    try:
        return float(str(valor).replace(",", "."))
    except (ValueError, TypeError):
        return None


def get_entrenadores():
    """Lee la hoja Entrenadores y devuelve los datos listos para Mongo."""
    registros = get_sheet_as_dicts("Entrenadores")
    entrenadores = []
    for row in registros:
        entrenadores.append({
            "idEntrenador": row["idEntrenador"],
            "nombre":       row["Nombre"],
            "apellido":     row["Apellido"],
            "medallas":     [m.strip() for m in row["Medallas"].split(",") if m.strip()],
        })
    return entrenadores


def get_combates():
    """Lee datos/combates.csv y devuelve los datos listos para Cassandra."""
    import csv
    combates = []
    with open("datos/combates.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            combates.append({
                "id":          row["idCombate"],
                "fecha":       date.fromisoformat(row["Fecha"]),
                "hora":        time.fromisoformat(row["Hora"].zfill(8)),
                "entrenador1": row["idEntrenador1"],
                "pokemon1":    row["idPokemon1"],
                "resultado":   row["Resultado"],
                "entrenador2": row["idEntrenador2"],
                "pokemon2":    row["idPokemon2"],
            })
    return combates


def get_pokemons_domesticados():
    """Lee la hoja Pokemons y devuelve los datos listos para Mongo."""
    registros = get_sheet_as_dicts("Pokemons")
    pokemons = []
    for row in registros:
        pokemons.append({
            "idPokemon": row["idPokemon"],
            "especie":   row["Especie"],
            "nombre":    row["Nombre"],
            "peso":      _a_float(row["Peso (kg)"]),
            "altura":    _a_float(row["Altura (m)"]),
            "foto":      row["Foto"],
            "tipo":      [t.strip() for t in row["Tipo"].split(",") if t.strip()],
        })
    return pokemons