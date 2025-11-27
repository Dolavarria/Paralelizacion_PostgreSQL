# Conexión a PostgreSQL y ejecución de consultas
import psycopg2
import config  # archivo que lee variables de entorno


## Maneja la conexión y operaciones con PostgreSQL
class Database:
    ## Inicializa con parámetros de conexión
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
