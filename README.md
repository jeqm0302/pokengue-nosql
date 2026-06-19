# Pokengue
Crear Proyecto:

git clone https://github.com/francisco2910/Pokengue

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

# despues de descargar algo nuevo

pip freeze > requirements.txt

# Para levantar cassandra y redis
# Redis
# Parado en la carpeta root del proyecto
docker run -d --name redis-pokengue -p 6379:6379 redis:latest

dir redis_dump.rdb

# chequear que este vacio
docker exec -it redis-pokengue redis-cli DBSIZE
# Ahora hacer la carga:
docker stop redis-pokengue
docker cp redis_dump.rdb redis-pokengue:/data/dump.rdb
docker restart redis-pokengue

# Mostrar que cargó:
docker exec -it redis-pokengue redis-cli DBSIZE

# Verificar un entrenador:

docker exec -it redis-pokengue redis-cli --raw

HGETALL entrenador:config:ENT-001


# Cassandra
docker run -d --name cassandra-pokengue -p 9042:9042 cassandra:latest

# Pasados de 1 a 2 minutos que levanta cassandra

docker logs cassandra-pokengue | Select-String "Starting listening for CQL clients"

docker exec -it cassandra-pokengue cqlsh -e "CREATE KEYSPACE IF NOT EXISTS pokengue WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};"

# Una vez ya existe todo solo hay que poner este comando 
docker start redis-pokengue cassandra-pokengue

# Para mongo 
# Crear un json llamado pokengueCredentials.json con el siguiente contenido
{
  "type": "service_account",
  "project_id": "pokengue",
  "private_key_id": "TU_PRIVATE_KEY_ID",
  "private_key": "TU_PRIVATE_KEY",
  "client_email": "pokengue@pokengue.iam.gserviceaccount.com",
  "client_id": "TU_CLIENT_ID",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/pokengue%40pokengue.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}


# en caso de una ejecución completa en la pagina web ir a 
/pokedex
/entrenadores
/pokemons

# en caso de una ejecución rapida
/entrenadores
/pokemons
 