# Corrector Paralelo de Datos Meteorológicos

Este proyecto implementa un sistema de corrección de datos meteorológicos corruptos (valor -32768) en una base de datos PostgreSQL utilizando procesamiento paralelo en Python.

## Integrantes
* Diego Olavarría

## Requisitos
* Ubuntu Server 24.04 (o compatible)
* Python 3.12.3
* PostgreSQL 17
* Librerías listadas en `requirements.txt`

## Instalación y Construcción

El proyecto incluye un `Makefile` para facilitar la gestión.

1. **Instalar dependencias:**
   ```bash
   make install
   ```

## Configuración

El sistema utiliza un archivo `.env` para las credenciales y configuración. Cree un archivo `.env` en la raíz con el siguiente contenido:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=meteo
DB_USER=postgres
DB_PASS=tu_password
NUM_PROCESOS=4
```

* `NUM_PROCESOS`: Define el grado de paralelismo. Se recomienda ajustar según los núcleos de la CPU (ej. 4 u 8).

## Ejecución

Para ejecutar el corrector principal:

```bash
make run
```

## Pruebas Unitarias

El proyecto incluye pruebas unitarias exhaustivas que validan la configuración, la conexión a la base de datos y la lógica matemática.

Para ejecutar las pruebas:

```bash
make test
```

## Estrategia de Solución

### 1. Lógica de Corrección
El algoritmo busca valores `-32768` y aplica la siguiente prioridad de corrección:
1. **Interpolación:** Si existen el valor inmediatamente anterior y posterior válidos, se calcula el promedio `(anterior + posterior) / 2`.
2. **Valor Adyacente:** Si falta uno de los vecinos, se utiliza el valor válido disponible (ya sea solo el anterior o solo el posterior).
3. **Todo lo anterior no es posible:** En el caso de que la estación no tenga datos vecinos válidos, se asigna `0` para eliminar el código de error.

### 2. Paralelismo
Se utiliza la librería `multiprocessing` de Python.
* **Estrategia:** Paralelismo por datos dividido por **Estación**.
* **Justificación:** Cada estación es independiente de las otras. Esto evita bloqueos en la base de datos, ya que cada proceso trabaja sobre un subconjunto de filas (`station_fk`) distinto.
* **Implementación:** Se utiliza un `Pool` de procesos que mapea la función `procesar_estacion` sobre la lista de IDs de estaciones.

### 3. Robustez
* **Transacciones:** Se implementó el uso de commit y rollback para asegurar que los cambios se guarden solo si todo sale bien, evitando dejar datos corruptos si el programa falla.
* **Conexiones:** Cada proceso hijo abre su propia conexión a la BD para evitar conflictos de hilos.
* **Idempotencia:** El script puede ejecutarse múltiples veces; solo corregirá los valores que sigan siendo `-32768`.