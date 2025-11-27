# Conexión a PostgreSQL y ejecución de consultas
import psycopg2
import config  # archivo que lee variables de entorno


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
            print(f"Conexión exitosa a {self.dbname} en {self.host}:{self.port}")
            return True

        except psycopg2.OperationalError as e:
            error_msg = str(e)
            print(f"Error de conexión: {error_msg}")
            return False

        except Exception as e:
            # Cualquier otro error
            print(f"Error inesperado al conectar: {e}")
            return False

    def cerrar_conexion(self):
        # Cierra la conexión a la base de datos
        if self.connection:
            self.connection.close()
            self.connection = None
            print("Conexión cerrada.")

    def obtener_todas_las_estaciones(self):
        # Retorna una lista con los IDs de todas las estaciones
        if not self.connection:
            print("No hay conexión activa.")
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
            print(f"Error al obtener estaciones: {e}")
            return []

    def obtener_columnas_numericas(self):
        if not self.connection:
            print("No hay conexión activa.")
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
            print(f"Error al obtener columnas numéricas: {e}")
            return []


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

    db.cerrar_conexion()
