# Unión de módulos y ejecución principal
from multiprocessing import Pool
import time
import config
import sys
from database import Database
from corrector import procesar_estacion


def main():
    print("=" * 60)
    print("CORRECTOR PARALELO DE DATOS METEOROLÓGICOS")
    print("=" * 60)

    inicio = time.time()

    # Conectar a BDD
    db = Database(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASS,
    )

    if not db.conectar():
        print("Error: No se pudo conectar a la base de datos")
        return

    # Obtener estadísticas ANTES de la corrección
    total_filas = db.contar_total_filas()
    errores_antes_col = db.contar_errores_por_columna()
    errores_antes_est = db.contar_errores_por_estacion()

    total_errores_inicial = sum(errores_antes_col.values())

    print(f"Total de filas en la tabla: {total_filas:,}")
    print(f"Total de valores erróneos (-32768): {total_errores_inicial:,}")

    # Obtener lista de estaciones
    estaciones = db.obtener_todas_las_estaciones()
    print(f"Total de estaciones a procesar: {len(estaciones)}")
    db.cerrar_conexion()

    # PROCESAMIENTO PARALELO
    print(f"Procesando estaciones en paralelo ({config.NUM_PROCESOS} procesos)...")
    resultados = []
    try:
        with Pool(processes=config.NUM_PROCESOS) as pool:
            resultados = pool.map(procesar_estacion, estaciones)

    except KeyboardInterrupt:
        print("\n!!! Proceso interrumpido por el usuario !!!")
        db.cerrar_conexion()
        sys.exit(1)
    except Exception as e:
        print(f"\nError inesperado en el Pool de procesos: {e}")
        db.cerrar_conexion()
        sys.exit(1)

    # Reconectar para obtener estadísticas finales
    db = Database(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASS,
    )
    db.conectar()

    errores_despues_col = db.contar_errores_por_columna()
    errores_despues_est = db.contar_errores_por_estacion()

    total_errores_final = sum(errores_despues_col.values())
    total_corregido = sum(resultados)

    duracion = time.time() - inicio

    # MOSTRAR RESULTADOS
    print("\n" + "=" * 70)
    print("RESUMEN DE CORRECCIÓN")
    print("=" * 70)

    print(f"\n Estadísticas:")
    print(f"Total de filas procesadas: {total_filas:,}")
    print(f"Valores corregidos: {total_corregido:,}")
    print(f"Errores restantes: {total_errores_final:,}")
    print(f"Tiempo de ejecución: {duracion:.2f} segundos")
    print(f"Procesos utilizados: {config.NUM_PROCESOS}")

    print(f"\n Valores corregidos por columna:")
    for columna in sorted(errores_antes_col.keys()):
        antes = errores_antes_col.get(columna, 0)
        despues = errores_despues_col.get(columna, 0)
        corregidos = antes - despues
        if corregidos > 0:
            print(f"{columna:20s}: {corregidos:6,} valores corregidos")

    print(f"\n Correcciones por estación:")
    # Combinar resultados con IDs de estación
    for i, station_pk in enumerate(estaciones):
        if resultados[i] > 0:
            print(f"Estación {station_pk:3d}: {resultados[i]:6,} valores corregidos")

    db.cerrar_conexion()
    print(f"\nProceso completado exitosamente")
    print("\n" + "=" * 70)
    print("INTEGRANTES DEL GRUPO:")
    print("Diego Olavarría")


if __name__ == "__main__":
    main()
