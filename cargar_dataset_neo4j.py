import csv
import os
from neo4j import GraphDatabase

URI = "neo4j://127.0.0.1:7687"
USER = "neo4j"
PASSWORD = "pokengue"

LIMPIAR_PRIMERO = True

CARPETA_DATOS = "datos"


def a_float(valor):
    try:
        return float(str(valor).replace(",", "."))
    except (ValueError, TypeError):
        return None


def leer_entrenadores(ruta):
    entrenadores = []
    with open(ruta, encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            medallas_texto = fila["Medallas"].strip()
            medallas = [m.strip() for m in medallas_texto.split(",") if m.strip()]
            entrenadores.append({
                "idEntrenador": fila["idEntrenador"].strip(),
                "nombre": fila["Nombre"].strip(),
                "apellido": fila["Apellido"].strip(),
                "medallas": medallas,
            })
    return entrenadores


def leer_pokemons(ruta):
    pokemons = []
    with open(ruta, encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            tipo_texto = fila["Tipo"].strip()
            tipo = [t.strip() for t in tipo_texto.split(",") if t.strip()]
            pokemons.append({
                "idPokemon": fila["idPokemon"].strip(),
                "especie": fila["Especie"].strip(),
                "nombre": fila["Nombre"].strip(),
                "tipo": tipo,
                "peso": a_float(fila["Peso (kg)"]),
                "altura": a_float(fila["Altura (m)"]),
            })
    return pokemons


def leer_relaciones_tiene(ruta):
    relaciones = []
    with open(ruta, encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            relaciones.append({
                "idEntrenador": fila["idEntrenador"].strip(),
                "idPokemon": fila["idPokemon"].strip(),
                "en_equipo": fila["en_equipo"].strip().lower() == "true",
            })
    return relaciones


def leer_amistades(ruta):
    amistades = []
    with open(ruta, encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            amistades.append({
                "id1": fila["id1"].strip(),
                "id2": fila["id2"].strip(),
            })
    return amistades


def crear_constraints(sesion):
    sesion.run(
        "CREATE CONSTRAINT entrenador_id_unico IF NOT EXISTS "
        "FOR (e:Entrenador) REQUIRE e.idEntrenador IS UNIQUE"
    )
    sesion.run(
        "CREATE CONSTRAINT pokemon_id_unico IF NOT EXISTS "
        "FOR (p:Pokemon) REQUIRE p.idPokemon IS UNIQUE"
    )


def cargar_entrenadores(sesion, entrenadores):
    consulta = """
    UNWIND $filas AS fila
    MERGE (e:Entrenador {idEntrenador: fila.idEntrenador})
    SET e.nombre = fila.nombre,
        e.apellido = fila.apellido,
        e.medallas = fila.medallas
    """
    sesion.run(consulta, filas=entrenadores)


def cargar_pokemons(sesion, pokemons):
    consulta = """
    UNWIND $filas AS fila
    MERGE (p:Pokemon {idPokemon: fila.idPokemon})
    SET p.especie = fila.especie,
        p.nombre = fila.nombre,
        p.tipo = fila.tipo,
        p.peso = fila.peso,
        p.altura = fila.altura
    """
    sesion.run(consulta, filas=pokemons)


def cargar_relaciones_tiene(sesion, relaciones):
    consulta = """
    UNWIND $filas AS fila
    MATCH (e:Entrenador {idEntrenador: fila.idEntrenador})
    MATCH (p:Pokemon {idPokemon: fila.idPokemon})
    MERGE (e)-[r:TIENE]->(p)
    SET r.en_equipo = fila.en_equipo
    """
    sesion.run(consulta, filas=relaciones)


def cargar_amistades(sesion, amistades):
    consulta = """
    UNWIND $filas AS fila
    MATCH (a:Entrenador {idEntrenador: fila.id1})
    MATCH (b:Entrenador {idEntrenador: fila.id2})
    MERGE (a)-[r:ES_AMIGO_DE]->(b)
    """
    sesion.run(consulta, filas=amistades)


def contar_estado(sesion):
    consulta = """
    CALL () { MATCH (e:Entrenador) RETURN count(e) AS entrenadores }
    CALL () { MATCH (p:Pokemon) RETURN count(p) AS pokemons }
    CALL () { MATCH ()-[r:TIENE]->() RETURN count(r) AS tiene }
    CALL () { MATCH ()-[r:ES_AMIGO_DE]->() RETURN count(r) AS amistades }
    RETURN entrenadores, pokemons, tiene, amistades
    """
    return sesion.run(consulta).single().data()


def buscar_buenos_ejemplos_demo(sesion):
    consulta = """
    MATCH (yo:Entrenador)
    OPTIONAL MATCH (yo)-[:ES_AMIGO_DE]-(:Entrenador)-[:ES_AMIGO_DE]-(rec:Entrenador)
    WHERE rec <> yo AND NOT (yo)-[:ES_AMIGO_DE]-(rec)
    WITH yo, count(DISTINCT rec) AS recomendaciones
    OPTIONAL MATCH (yo)-[:TIENE]->(:Pokemon)<-[:TIENE]-(riv:Entrenador)
    WHERE riv <> yo AND NOT (yo)-[:ES_AMIGO_DE]-(riv)
    WITH yo, recomendaciones, count(DISTINCT riv) AS rivales
    WHERE recomendaciones > 0 AND rivales > 0
    RETURN yo.idEntrenador AS id, yo.nombre AS nombre, yo.apellido AS apellido,
           recomendaciones, rivales
    ORDER BY recomendaciones DESC, rivales DESC
    LIMIT 5
    """
    return [registro.data() for registro in sesion.run(consulta)]


def main():
    ruta_entrenadores = os.path.join(CARPETA_DATOS, "entrenadores.csv")
    ruta_pokemons = os.path.join(CARPETA_DATOS, "pokemons.csv")
    ruta_tiene = os.path.join(CARPETA_DATOS, "relaciones_tiene.csv")
    ruta_amistades = os.path.join(CARPETA_DATOS, "amistades.csv")

    print("Leyendo archivos CSV...")
    entrenadores = leer_entrenadores(ruta_entrenadores)
    pokemons = leer_pokemons(ruta_pokemons)
    relaciones = leer_relaciones_tiene(ruta_tiene)
    amistades = leer_amistades(ruta_amistades)
    print(f"  {len(entrenadores)} entrenadores leidos (datos reales del equipo)")
    print(f"  {len(pokemons)} pokemons leidos (datos reales del equipo)")
    print(f"  {len(relaciones)} relaciones TIENE leidas")
    print(f"  {len(amistades)} amistades leidas")

    print("\nConectando a Neo4j...")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    with driver.session() as sesion:
        if LIMPIAR_PRIMERO:
            sesion.run("MATCH (n) DETACH DELETE n")
            print("Base limpiada (se borraron los datos anteriores)")

        crear_constraints(sesion)
        print("Constraints creados")

        cargar_entrenadores(sesion, entrenadores)
        print(f"{len(entrenadores)} entrenadores cargados")

        cargar_pokemons(sesion, pokemons)
        print(f"{len(pokemons)} pokemons cargados")

        cargar_relaciones_tiene(sesion, relaciones)
        print(f"{len(relaciones)} relaciones TIENE creadas")

        cargar_amistades(sesion, amistades)
        print(f"{len(amistades)} amistades creadas")

        print("\n" + "=" * 55)
        print("ESTADO FINAL DEL GRAFO")
        print("=" * 55)
        estado = contar_estado(sesion)
        total = sum(estado.values())
        print(f"  Entrenadores : {estado['entrenadores']}")
        print(f"  Pokemons     : {estado['pokemons']}")
        print(f"  TIENE        : {estado['tiene']}")
        print(f"  Amistades    : {estado['amistades']}")
        print(f"  ---------------------------")
        print(f"  TOTAL        : {total}  (minimo requerido: 400)")

        print("\n" + "=" * 55)
        print("ENTRENADORES IDEALES PARA LA DEMO")
        print("(tienen recomendaciones Y rivales potenciales)")
        print("=" * 55)
        ejemplos = buscar_buenos_ejemplos_demo(sesion)
        for e in ejemplos:
            print(f"  {e['id']} ({e['nombre']} {e['apellido']}): "
                  f"{e['recomendaciones']} recomendaciones, "
                  f"{e['rivales']} rivales potenciales")
        print("\nUsa cualquiera de estos IDs en la demo para que")
        print("Recomendar amigos y Rivales potenciales den buenos resultados.")

    driver.close()
    print("\nListo. Dataset cargado correctamente desde los CSV.")


if __name__ == "__main__":
    main()
