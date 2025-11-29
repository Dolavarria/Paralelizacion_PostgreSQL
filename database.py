# Conexión a PostgreSQL y ejecución de consultas
import psycopg2
import config  # archivo que lee variables de entorno
import logging


## Maneja la conexión y operaciones con PostgreSQL
class Database:
    ## Inicializa parámetros de conexión
    def __init__(self, host, port, dbname, user, password):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.connection = None

    # Conecta a la base de datos PostgreSQL
    def conectar(self):
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password,
            )
            logging.info(f"Conexión exitosa a {self.dbname} en {self.host}:{self.port}")
            return True

        except psycopg2.OperationalError as e:
            error_msg = str(e)
            logging.error(f"Error de conexión: {error_msg}")
            return False

        except Exception as e:
            # Cualquier otro error
            logging.error(f"Error inesperado al conectar: {e}")
            return False

    def cerrar_conexion(self):
        # Cierra la conexión a la base de datos
        if self.connection:
            self.connection.close()
            self.connection = None
            logging.info("Conexión cerrada.")

    def obtener_todas_las_estaciones(self):
        # Retorna una lista con los IDs de todas las estaciones
        if not self.connection:
            logging.warning("No hay conexión activa.")  # <--- LOGGING
            return []

        try:
            cursor = self.connection.cursor()
            query = "SELECT pk FROM meteo.stations ORDER BY pk asc;"
            cursor.execute(query)
            resultados = cursor.fetchall()
            cursor.close()

            # 'resultados' es una lista [(1,), (2,), (5,)]
            # la convertimos a una lista [1, 2, 5] para facilitar el uso.
            lista_ids = [fila[0] for fila in resultados]
            return lista_ids

        except Exception as e:
            logging.error(f"Error al obtener estaciones: {e}")
            return []

    def obtener_columnas_numericas(self):
        if not self.connection:
            logging.warning("No hay conexión activa.")
            return []
        try:
            cursor = self.connection.cursor()
            query = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'meteo' 
                  AND table_name = 'observations'
                  AND data_type IN ('integer', 'numeric', 'real', 'double precision', 'smallint', 'bigint')
                  AND column_name NOT IN ('pk', 'id', 'station_fk');            """
            cursor.execute(query)
            resultados = cursor.fetchall()
            cursor.close()
            lista_columnas = [fila[0] for fila in resultados]
            return lista_columnas
        except Exception as e:
            logging.error(f"Error al obtener columnas numéricas: {e}")
            return []

    def obtener_valor_anterior(self, station_fk, columna, fecha_hora):
        if not self.connection:
            logging.warning("No hay conexión activa.")
            return None
        try:
            cursor = self.connection.cursor()
            query = f"""
                SELECT {columna}
                FROM meteo.observations
                WHERE station_fk = %s
                  AND date_time < %s
                  AND {columna} != -32768
                ORDER BY date_time DESC
                LIMIT 1
            """
            cursor.execute(query, (station_fk, fecha_hora))
            resultado = cursor.fetchone()
            cursor.close()
            if resultado:
                return resultado[0]
            else:
                return None
        except Exception as e:
            logging.error(f"Error al obtener valor anterior: {e}")
            return None

    def obtener_valor_posterior(self, station_fk, columna, fecha_hora):
        if not self.connection:
            logging.warning("No hay conexión activa.")
            return None
        try:
            cursor = self.connection.cursor()
            query = f"""
                SELECT {columna}
                FROM meteo.observations
                WHERE station_fk = %s
                  AND date_time > %s
                  AND {columna} != -32768
                ORDER BY date_time ASC
                LIMIT 1
            """
            cursor.execute(query, (station_fk, fecha_hora))
            resultado = cursor.fetchone()
            cursor.close()
            if resultado:
                return resultado[0]
            else:
                return None
        except Exception as e:
            logging.error(f"Error al obtener valor posterior: {e}")
            return None

    def obtener_registros_con_errores(self, station_fk, columna):
        if not self.connection:
            logging.warning("No hay conexión activa.")
            return []
        try:
            cursor = self.connection.cursor()
            # Registros con valor -32768
            query = f"""
                        SELECT pk, date_time, {columna}
                        FROM meteo.observations
                        WHERE station_fk = %s
                        AND {columna} = -32768
                        ORDER BY date_time ASC
                    """
            cursor.execute(query, (station_fk,))
            resultados = cursor.fetchall()
            cursor.close()
            return resultados
        except Exception as e:
            logging.error(f"Error al obtener registros con error: {e}")
            return []

    def actualizar_observacion(self, pk, columna, nuevo_valor):

        if not self.connection:
            logging.warning("No hay conexión activa.")
            return False

        cursor = None
        try:
            cursor = self.connection.cursor()

            query = f"""
                UPDATE meteo.observations
                SET {columna} = %s
                WHERE pk = %s
            """

            cursor.execute(query, (nuevo_valor, pk))
            self.connection.commit()  # Confirmar cambios

            return True

        except Exception as e:
            self.connection.rollback()  # Revertir cambios si hay error
            logging.error(f"Error al actualizar observación: {e}")
            return False

        finally:
            if cursor:
                cursor.close()

    def contar_total_filas(self):
        # Cuenta total de registros en meteo.observations
        if not self.connection:
            return 0
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM meteo.observations")
            return cursor.fetchone()[0]
        except Exception as e:
            logging.error(f"Error: {e}")
            return 0
        finally:
            if cursor:
                cursor.close()

    def contar_errores_por_columna(self):
        # Retorna dict con errores por columna {'col': cantidad}
        columnas = self.obtener_columnas_numericas()
        resultado = {}
        for col in columnas:
            cursor = None
            try:
                cursor = self.connection.cursor()
                cursor.execute(
                    f"SELECT COUNT(*) FROM meteo.observations WHERE {col} = -32768"
                )
                resultado[col] = cursor.fetchone()[0]
            except Exception as e:
                resultado[col] = 0
            finally:
                if cursor:
                    cursor.close()
        return resultado

    def contar_errores_por_estacion(self):
        # Retorna dict con errores totales por estación {station_fk: cantidad}
        columnas = self.obtener_columnas_numericas()
        cursor = None
        try:
            cursor = self.connection.cursor()
            # Contar errores en todas las columnas
            cases = " + ".join(
                [f"CASE WHEN {col} = -32768 THEN 1 ELSE 0 END" for col in columnas]
            )
            query = f"""
                SELECT station_fk, SUM({cases}) as total_errores
                FROM meteo.observations
                GROUP BY station_fk
                ORDER BY station_fk
            """
            cursor.execute(query)
            return {fila[0]: fila[1] for fila in cursor.fetchall()}
        except Exception as e:
            logging.error(f"Error: {e}")
            return {}
        finally:
            if cursor:
                cursor.close()


if __name__ == "__main__":
    # Leer credenciales desde variables de entorno
    import config

    db = Database(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASS,
    )
    db.conectar()
    estaciones = db.obtener_todas_las_estaciones()
    print(f"Se encontraron {len(estaciones)} estaciones.")
    print(f"Ejemplo de IDs: {estaciones}")
    columnas = db.obtener_columnas_numericas()
    print(f"Se encontraron {len(columnas)} columnas numéricas:")
    for col in columnas:
        print(f"- {col}")

    print("\nProbando obtener valor anterior...")
    # Buscar un registro con -32768 primero
    anterior = db.obtener_valor_anterior(1, "precipitation", "2025-11-10 16:20:00")
    print(f"   Valor anterior de precipitation en estación 1: {anterior}")
    posterior = db.obtener_valor_posterior(1, "precipitation", "2025-11-10 16:20:00")
    print(f"   Valor posterior de precipitation en estación 1: {posterior}")
    errores = db.obtener_registros_con_errores(1, "precipitation")

    for pk, fecha, valor in errores:
        print(f"Registro {pk} en {fecha} tiene valor erróneo: {valor}")
    db.cerrar_conexion()
