from db.ConexionRedis import ConexionRedis


class RedisDAO:
    """
    Gestiona la configuración/preferencias de los entrenadores en Redis.

    Modelado (clave -> tipo):
      entrenador:config:{id}            HASH  -> nombre, apellido, medalla,
                                                 idioma, tema, notificaciones
      entrenadores                      SET   -> todos los IDs cargados
      indice:idioma:{idioma}            SET   -> IDs con ese idioma
      indice:tema:{tema}                SET   -> IDs con ese tema
      indice:notificaciones:{TRUE|FALSE} SET  -> IDs según notificaciones
      indice:medalla:{medalla}          SET   -> IDs que tienen ESA medalla
                                                 (una clave por medalla individual)

    Los índices invertidos permiten buscar por atributo en O(1) por clave,
    que es el patrón recomendado en un motor clave-valor.
    """

    PREFIJO_CONFIG = "entrenador:config:"
    CLAVE_IDS = "entrenadores"

    def __init__(self):
        self.r = ConexionRedis().obtener_cliente()

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------
    @staticmethod
    def _clave_config(idEntrenador):
        return f"{RedisDAO.PREFIJO_CONFIG}{idEntrenador}"

    @staticmethod
    def _separar_medallas(medalla_str):
        """'Trueno, Calor, Tierra' -> ['Trueno', 'Calor', 'Tierra']"""
        if not medalla_str:
            return []
        return [m.strip() for m in medalla_str.split(",") if m.strip()]

    def _quitar_de_indices(self, idEntrenador, config_anterior, pipe):
        """Saca al entrenador de los índices de su configuración anterior."""
        if not config_anterior:
            return
        if config_anterior.get("idioma"):
            pipe.srem(f"indice:idioma:{config_anterior['idioma']}", idEntrenador)
        if config_anterior.get("tema"):
            pipe.srem(f"indice:tema:{config_anterior['tema']}", idEntrenador)
        if config_anterior.get("notificaciones"):
            pipe.srem(f"indice:notificaciones:{config_anterior['notificaciones']}", idEntrenador)
        for medalla in self._separar_medallas(config_anterior.get("medalla", "")):
            pipe.srem(f"indice:medalla:{medalla}", idEntrenador)

    def _agregar_a_indices(self, idEntrenador, config, pipe):
        """Agrega al entrenador a los índices de su nueva configuración."""
        if config.get("idioma"):
            pipe.sadd(f"indice:idioma:{config['idioma']}", idEntrenador)
        if config.get("tema"):
            pipe.sadd(f"indice:tema:{config['tema']}", idEntrenador)
        if config.get("notificaciones"):
            pipe.sadd(f"indice:notificaciones:{config['notificaciones']}", idEntrenador)
        for medalla in self._separar_medallas(config.get("medalla", "")):
            pipe.sadd(f"indice:medalla:{medalla}", idEntrenador)

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------
    def guardar_config(self, idEntrenador, nombre, apellido, medallas,
                       idioma, tema, notificaciones):
        """
        Crea o actualiza la configuración de un entrenador y mantiene
        los índices consistentes. `medallas` puede ser lista o string
        con comas. `notificaciones` es bool.
        """
        if isinstance(medallas, list):
            medalla_str = ", ".join(medallas)
        else:
            medalla_str = medallas or ""

        config = {
            "nombre": nombre or "",
            "apellido": apellido or "",
            "medalla": medalla_str,
            "idioma": idioma or "",
            "tema": tema or "",
            "notificaciones": "TRUE" if notificaciones else "FALSE",
        }

        clave = self._clave_config(idEntrenador)
        config_anterior = self.r.hgetall(clave)  # {} si no existe

        # Pipeline = todas las operaciones viajan juntas (atómico con transaction=True)
        pipe = self.r.pipeline(transaction=True)
        self._quitar_de_indices(idEntrenador, config_anterior, pipe)
        pipe.hset(clave, mapping=config)
        pipe.sadd(self.CLAVE_IDS, idEntrenador)
        self._agregar_a_indices(idEntrenador, config, pipe)
        pipe.execute()

        return {"idEntrenador": idEntrenador, **config}

    def guardar_configs_masivo(self, lista_dicts):
        """
        Carga masiva. Cada dict: {idEntrenador, nombre, apellido,
        medallas, idioma, tema, notificaciones}.
        """
        procesados = 0
        for d in lista_dicts:
            self.guardar_config(
                d["idEntrenador"], d.get("nombre"), d.get("apellido"),
                d.get("medallas"), d.get("idioma"), d.get("tema"),
                d.get("notificaciones", False),
            )
            procesados += 1
        return procesados

    def eliminar_config(self, idEntrenador):
        clave = self._clave_config(idEntrenador)
        config = self.r.hgetall(clave)
        if not config:
            return False
        pipe = self.r.pipeline(transaction=True)
        self._quitar_de_indices(idEntrenador, config, pipe)
        pipe.delete(clave)
        pipe.srem(self.CLAVE_IDS, idEntrenador)
        pipe.execute()
        return True

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------
    def obtener_config(self, idEntrenador):
        config = self.r.hgetall(self._clave_config(idEntrenador))
        if not config:
            return None
        return {"idEntrenador": idEntrenador, **config}

    def listar_ids(self):
        return sorted(self.r.smembers(self.CLAVE_IDS))

    def _configs_de_ids(self, ids):
        """Trae los hashes de varios IDs en un solo viaje (pipeline)."""
        ids = sorted(ids)
        if not ids:
            return []
        pipe = self.r.pipeline(transaction=False)
        for id_ in ids:
            pipe.hgetall(self._clave_config(id_))
        resultados = pipe.execute()
        return [
            {"idEntrenador": id_, **config}
            for id_, config in zip(ids, resultados) if config
        ]

    def buscar_por_idioma(self, idioma):
        ids = self.r.smembers(f"indice:idioma:{idioma}")
        return self._configs_de_ids(ids)

    def buscar_por_tema(self, tema):
        ids = self.r.smembers(f"indice:tema:{tema}")
        return self._configs_de_ids(ids)

    def buscar_por_notificaciones(self, activadas):
        valor = "TRUE" if activadas else "FALSE"
        ids = self.r.smembers(f"indice:notificaciones:{valor}")
        return self._configs_de_ids(ids)

    def buscar_por_medalla(self, medalla):
        ids = self.r.smembers(f"indice:medalla:{medalla.strip()}")
        return self._configs_de_ids(ids)

    def buscar_combinado(self, idioma=None, tema=None, medalla=None):
        """
        Intersección de índices con SINTER: por ejemplo, entrenadores
        en Japonés + tema dark + medalla Trueno. Muestra el poder de
        los sets de Redis.
        """
        claves = []
        if idioma:
            claves.append(f"indice:idioma:{idioma}")
        if tema:
            claves.append(f"indice:tema:{tema}")
        if medalla:
            claves.append(f"indice:medalla:{medalla.strip()}")
        if not claves:
            return []
        ids = self.r.sinter(*claves)
        return self._configs_de_ids(ids)

    # ------------------------------------------------------------------
    # Estado general (para la demo, como contar_estado_general de Neo4j)
    # ------------------------------------------------------------------
    def contar_estado_general(self):
        idiomas = {}
        for clave in self.r.scan_iter("indice:idioma:*"):
            idiomas[clave.split(":")[-1]] = self.r.scard(clave)
        temas = {}
        for clave in self.r.scan_iter("indice:tema:*"):
            temas[clave.split(":")[-1]] = self.r.scard(clave)
        return {
            "total_entrenadores": self.r.scard(self.CLAVE_IDS),
            "por_idioma": idiomas,
            "por_tema": temas,
            "notificaciones_activadas": self.r.scard("indice:notificaciones:TRUE"),
            "notificaciones_desactivadas": self.r.scard("indice:notificaciones:FALSE"),
            "cantidad_medallas_indexadas": sum(
                1 for _ in self.r.scan_iter("indice:medalla:*")
            ),
        }
