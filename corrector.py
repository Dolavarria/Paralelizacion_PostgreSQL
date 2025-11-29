# Lógica de correción
import time
import config
import logging
from database import Database


def procesar_estacion(station_pk):

    # Cada proceso debe crear su propia conexión
    db = Database(
        config.DB_HOST, config.DB_PORT, config.DB_NAME, config.DB_USER, config.DB_PASS
    )

    if not db.conectar():
        logging.error(f"[Estación {station_pk}] Error: No se pudo conectar a la BD.")
        return 0

    correcciones_totales = 0
    start_time = time.time()

    try:
        # Detectamos qué columnas tienen datos numéricos
        columnas_numericas = db.obtener_columnas_numericas()

        for col in columnas_numericas:
            # Obtener lista de errores [(pk, fecha, valor_malo), ...]
            errores = db.obtener_registros_con_errores(station_pk, col)

            if not errores:
                continue  # Si no hay errores en esta columna, pasamos a la siguiente

            logging.info(
                f"[Estación {station_pk}] Columna '{col}': Corrigiendo {len(errores)} errores..."
            )

            for obs_pk, fecha_error, _ in errores:

                # Buscar Vecinos
                val_ant = db.obtener_valor_anterior(station_pk, col, fecha_error)
                val_post = db.obtener_valor_posterior(station_pk, col, fecha_error)

                valor_corregido = None

                # Existen ambos se calcula promedio
                if val_ant is not None and val_post is not None:
                    valor_corregido = (val_ant + val_post) / 2

                # Solo existe anterior mantenemos el último válido
                elif val_ant is not None:
                    valor_corregido = val_ant

                # Si solo existe posterior usamos el primero válido
                elif val_post is not None:
                    valor_corregido = val_post

                # Estación vacía o corrupta total se asigna 0
                else:
                    valor_corregido = 0

                # Actualizar BD
                if valor_corregido is not None:
                    # Redondeamos a 2 decimales para ser
                    valor_corregido = round(valor_corregido, 2)

                    if db.actualizar_observacion(obs_pk, col, valor_corregido):
                        correcciones_totales += 1

    except Exception as e:
        logging.critical(
            f"[Estación {station_pk}] Error crítico durante procesamiento: {e}"
        )

    finally:
        db.cerrar_conexion()

    duration = time.time() - start_time
    if correcciones_totales > 0:
        logging.info(
            f"--> [Estación {station_pk}] Finalizada. {correcciones_totales} correcciones en {duration:.2f}s."
        )

    return correcciones_totales


if __name__ == "__main__":
    # Prueba con la estación 1
    print("Probando corrección de una sola estación...")
    procesar_estacion(1)
