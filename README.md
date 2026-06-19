# Pokengue
Crear Proyecto:

git clone https://github.com/francisco2910/Pokengue

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

despues de descargar algo nuevo

pip freeze > requirements.txt

# Pre-requisitos Cassandra
Crear un docker de Cassandra con el nombre "pokengue", y el keyspace "pokengue". Al entrar a la pagina web de Cassandra, tocar el boton "cargar desde sheets" arriba a la derecha para cargas los datos.

# Pre-requisitos Redis
Tener un docker de Redis corriendo. Correr el archivo redis_dump.rdb para cargar los datos.

# Pre-requisitos Neo4J
Ejecutar el archivo cargar_dataset_neo4j.py cargar los datos.