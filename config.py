# Lee variables de entorno
import os
import sys
import logging
from dotenv import load_dotenv

# Cargar variables desde .env automáticamente
load_dotenv()

# Obtener variables o lanzar error si no existen
def obtener_variable_entorno(var_nombre, default=None):
    valor = os.getenv(var_nombre, default)
    if valor is None:
        logging.error(f"La variable de entorno {var_nombre} no está definida.")
        sys.exit(1)
    return valor


# Verifica si el valor para procesos es un entero válido dentro de un rango
def obtener_entero_valido(nombre, default=None, min_val=1, max_val=32):
    # Si no hay valor ingresado, usa el máximo de núcleos del sistema
    if default is None:
        default = str(os.cpu_count() or 4)
    valor_str = obtener_variable_entorno(nombre, default)

    try:
        valor = int(valor_str)
    except ValueError:
        logging.error(
            f"{nombre} debe ser un número entero. Valor recibido: '{valor_str}'"
        )
        sys.exit(1)
        return

    if valor < min_val or valor > max_val:
        logging.error(
            f"{nombre} debe ser un número entero entre {min_val} y {max_val}."
        )
        logging.error(
            f"Valor recibido: '{valor}'. Sugerencia: Tu sistema tiene {os.cpu_count()} núcleos."
        )
        sys.exit(1)
        return
    return valor


# Configuración de número de procesos
NUM_PROCESOS = obtener_entero_valido("NUM_PROCESOS")
# Configuración de la base de datos
DB_HOST = obtener_variable_entorno("DB_HOST")
DB_PORT = obtener_variable_entorno("DB_PORT")
DB_NAME = obtener_variable_entorno("DB_NAME")
DB_USER = obtener_variable_entorno("DB_USER")
DB_PASS = obtener_variable_entorno("DB_PASS")
