# Corrector Paralelo de Datos Meteorológicos

Este proyecto implementa un sistema de corrección de datos meteorológicos corruptos (valor -32768) en una base de datos PostgreSQL utilizando procesamiento paralelo en Python.

## Integrantes
* Diego Olavarría
* Martin Guerrero 
* Javier Aucapan 


## Requisitos
* Ubuntu Server 24.04 
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

## Arquitectura del Sistema

### Estructura de Módulos

El proyecto está organizado en módulos con responsabilidades bien definidas:

**Flujo:**
```
main.py (Programa principal)
    |
    +-- config.py (Administra configuración desde .env)
    +-- database.py (Conexión a base de datos)
    +-- corrector.py (Lógica de corrección)
            |
        PostgreSQL
```

### Descripción de Componentes

#### 1. config.py - Módulo de Configuración
Lee y valida variables de entorno desde el archivo `.env`.

**Funciones principales:**
- `obtener_variable_entorno(var_nombre, default)`: Lee una variable y valida que exista
- `obtener_entero_valido(nombre, default, min_val, max_val)`: Valida que NUM_PROCESOS sea un entero entre 1 y 32

**Validaciones:**
- Verifica que todas las credenciales de BD estén presentes
- Valida que NUM_PROCESOS sea numérico y esté en el rango permitido
- Si falta alguna configuración, termina el programa con un mensaje de error

**Variables exportadas:**
- DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
- NUM_PROCESOS

#### 2. database.py - Capa de Abstracción de Datos
Encapsula todas las operaciones de acceso a PostgreSQL.

**Clase principal:** `Database`

**Métodos de conexión:**
- `__init__(host, port, dbname, user, password)`: Inicializa parámetros
- `conectar()`: Establece conexión con manejo de excepciones
- `cerrar_conexion()`: Cierra la conexión activa

**Métodos de consulta:**
- `obtener_todas_las_estaciones()`: Lista de IDs de estaciones ordenados
- `obtener_columnas_numericas()`: Detecta columnas numéricas mediante
- `obtener_valor_anterior(station_fk, columna, fecha_hora)`: Busca el valor válido más cercano antes de una fecha
- `obtener_valor_posterior(station_fk, columna, fecha_hora)`: Busca el valor válido más cercano después de una fecha
- `obtener_registros_con_errores(station_fk, columna)`: Lista todos los registros con valor -32768

**Métodos de actualización:**
- `actualizar_observacion(pk, columna, nuevo_valor)`: Actualiza un registro con transacción (commit/rollback)

**Métodos de estadísticas:**
- `contar_total_filas()`: Total de registros en meteo.observations
- `contar_errores_por_columna()`: Diccionario {columna: cantidad_errores}
- `contar_errores_por_estacion()`: Diccionario {station_fk: cantidad_errores}

**Gestión de transacciones:**
- Cada actualización ejecuta commit si tiene éxito
- Si hay error, ejecuta rollback para mantener consistencia
- Previene corrupción de datos ante fallos

#### 3. corrector.py - Lógica de Corrección
Implementa el algoritmo de corrección para una estación específica.

**Función principal:** `procesar_estacion(station_pk)`

**Flujo:**
1. Crea conexión independiente a la BD (Para el paralelismo)
2. Obtiene lista de columnas numéricas
3. Para cada columna:
   - Obtiene lista de errores (registros con -32768)
   - Para cada error:
     - Busca valor anterior y posterior válidos
     - Calcula valor corregido según criterio
     - Actualiza la BD
4. Cierra conexión
5. Retorna cantidad total de correcciones

**Criterio de corrección:**
```python
if val_anterior != None AND val_posterior != None:
    valor_corregido = (val_anterior + val_posterior) / 2  # Interpolación
elif val_anterior != None:
    valor_corregido = val_anterior  # Solo anterior disponible
elif val_posterior != None:
    valor_corregido = val_posterior  # Solo posterior disponible
else:
    valor_corregido = 0  # Sin datos válidos
```

#### 4. main.py - Programa Principal
Coordina el flujo completo del programa.

**Flujo de ejecución:**

**Fase 1: Inicialización**
1. Inicia logging
2. Muestra datos iniciales
3. Conecta a la BD

**Fase 2: Análisis Pre-Corrección**
4. Obtiene estadísticas iniciales (total de filas, errores por columna, errores por estación)
5. Si no hay errores, termina sin modificar nada para evitar desperdicio de recursos

**Fase 3: Procesamiento Paralelo**
6. Obtiene lista de IDs de estaciones
7. Cierra conexión inicial (cada proceso creará la suya)
8. Lanza Pool de procesos:
   ```python
   with Pool(processes=NUM_PROCESOS) as pool:
       resultados = pool.map(procesar_estacion, estaciones)
   ```
9. Maneja interrupciones (Ctrl+C) y excepciones

**Fase 4: Análisis Post-Corrección**
10. Reconecta a la BD
11. Obtiene estadísticas finales
12. Calcula métricas (total corregido, tiempo de ejecución)

**Fase 5: Generación de Reporte**
13. Muestra resumen en consola (desglose por columna y estación)
14. Cierra conexión

#### 5. test_project.py - Encargado de Pruebas
Valida componentes críticos mediante unit tests.

**Clases de prueba:**

**TestConfiguracion:**
- Verifica lectura correcta de variables

**TestDatabase:**
- `test_conexion_exitosa()`: Verifica que conectar() retorne True
- `test_conexion_fallida()`: Verifica manejo de errores

**TestLogicaCorreccion (4 casos):**
- `test_caso_dos_vecinos()`: Interpolación (10 + 20) / 2 = 15.0
- `test_caso_solo_anterior()`: Usa valor anterior cuando no hay posterior
- `test_caso_solo_posterior()`: Usa valor posterior cuando no hay anterior
- `test_caso_sin_vecinos()`: Asigna 0 cuando no hay datos válidos


### Flujo de Ejecución Completo

```
INICIO
  |
main.py: Configura logging e inicio
  |
main.py: Conecta a BD
  |
main.py: Obtiene estadísticas PRE-corrección
  |
main.py: Verifica si hay errores
  |-- NO --> SALIR
  |
  |-- SÍ --> Obtiene lista de estaciones
  |
main.py: Cierra conexión inicial
  |
PROCESAMIENTO PARALELO (Pool de procesos)
  |
  +-- Proceso 1: procesar_estacion(1)
  |     |-- corrector.py: Crea conexión propia
  |     |-- database.py: Obtiene columnas
  |     |-- Para cada columna:
  |     |     |-- Obtiene errores
  |     |     |-- Busca vecinos
  |     |     |-- Calcula corrección
  |     |     |-- Actualiza BD (commit/rollback)
  |     |-- Retorna: Correcciones
  |
  +-- Proceso 2: procesar_estacion(2)
  |     |-- (mismo flujo)
  |     |-- Retorna: Correcciones
  |
  +-- ... (más procesos)
  |
main.py: Recopila resultados [150, 200, 75, ...]
  |
main.py: Reconecta a BD
  |
main.py: Obtiene estadísticas POST-corrección
  |
main.py: Calcula métricas y genera reporte
  |
FIN
```

### Gestión de Concurrencia

**Problema:** Múltiples procesos accediendo simultáneamente a PostgreSQL pueden causar deadlocks o datos inconsistentes.

**Soluciones implementadas:**

1. **Conexiones independientes por proceso:**
   - Cada proceso ejecuta `db = Database(...)` y `db.conectar()`
   - PostgreSQL maneja múltiples conexiones sin conflictos

2. **Particionamiento de datos:**
   - Cada proceso trabaja sobre un station_fk diferente
   - No hay dos procesos modificando la misma fila simultáneamente

3. **Transacciones:**
   ```python
   try:
       cursor.execute("UPDATE ... WHERE pk = %s", (valor, pk))
       self.connection.commit()
   except Exception:
       self.connection.rollback()
   ```

4. **Sin estado compartido:**
   - No hay variables globales modificables
   - Cada proceso tiene su propia copia de variables
   - La comunicación solo ocurre al retornar resultados

**Resultado:** Esta arquitectura elimina deadlocks y datos inconsistentes.

## Estrategia de Solución

### 1. Lógica de Corrección
El algoritmo busca valores `-32768` y aplica la siguiente prioridad:
1. **Interpolación:** Si existen valores anterior y posterior válidos, calcula el promedio `(anterior + posterior) / 2`
2. **Valor Adyacente:** Si falta uno de los vecinos, usa el valor válido disponible
3. **Fallback a cero:** Si no hay datos vecinos válidos, asigna `0`

**Ejemplo:**
```
Estación 5, columna "temperature":

Registro | date_time         | temperature
---------|-------------------|------------
100      | 2025-01-01 10:00  | 15.5      valor ANTERIOR válido
101      | 2025-01-01 11:00  | -32768    ERROR a corregir
102      | 2025-01-01 12:00  | 18.3      valor POSTERIOR válido

Corrección: (15.5 + 18.3) / 2 = 16.9
```

### 2. Estrategia de Paralelismo

#### Técnica: Paralelismo de datos por estación

**Justificación:**
Se eligió paralelizar por estación porque:
- Independencia : Los datos de estación 1 no interfieren con estación 2
- Pool.map() distribuye estaciones 
- Evita bloqueos de BD: Cada proceso modifica filas con diferente station_fk


#### Implementación: multiprocessing.Pool

**Código en main.py:**
```python
from multiprocessing import Pool

estaciones = [1, 2, 5, 10, 12, 15, ...]

with Pool(processes=NUM_PROCESOS) as pool:
    resultados = pool.map(procesar_estacion, estaciones)
```

**Funcionamiento interno:**

1. **Creación del Pool:**
   - Pool(processes=4) lanza 4 procesos hijos independientes
   - Cada proceso es una copia del programa con su propia memoria
   - El SO los distribuye entre núcleos de CPU

2. **Distribución con map():**
   - Si hay 20 estaciones y 4 procesos, cada proceso procesa aproximadamente 5
   - La distribución es dinámica: cuando un proceso termina, toma la siguiente estación disponible

3. **Independencia:**
   - Cada proceso ejecuta procesar_estacion(id) aislado
   - Cada proceso crea su propia conexión a PostgreSQL
   - No comparten variables, cursores ni conexiones

4. **Recolección de resultados:**
   - pool.map() espera a que todos terminen
   - Retorna lista de resultados en el mismo orden que la entrada
   ```python
   estaciones = [1, 2, 5, 10]
   resultados = pool.map(procesar_estacion, estaciones)
   # resultados[0] = correcciones de estación 1
   # resultados[1] = correcciones de estación 2
   ```

#### Configuración del paralelismo

El número de procesos se configura en `.env`:

```env
NUM_PROCESOS=4
```
- El sistema valida que esté entre 1-32

### 3. Robustez e integridad de datos

#### Manejo de Transacciones
Cada actualización está protegida:
```python
try:
    cursor.execute("UPDATE meteo.observations SET ... WHERE pk = %s", ...)
    self.connection.commit()
except Exception as e:
    self.connection.rollback()
    logging.error(f"Error: {e}")
```

**Beneficios:**
- Si un proceso falla, los cambios se revierten
- La BD nunca queda inconsistente
- Otros procesos continúan normalmente


#### Manejo de errores

**A nivel de conexión (database.py):**
```python
try:
    self.connection = psycopg2.connect(...)
except psycopg2.OperationalError as e:
    logging.error(f"Error de conexión: {e}")
    return False
```

**A nivel de Pool (main.py):**
```python
try:
    with Pool(processes=NUM_PROCESOS) as pool:
        resultados = pool.map(procesar_estacion, estaciones)
except KeyboardInterrupt:
    logging.warning("Interrumpido por usuario")
    sys.exit(1)
except Exception as e:
    logging.critical(f"Error en Pool: {e}")
    sys.exit(1)
```

- Nunca deja conexiones abiertas
- Logs detallados para debugging
- Salida limpia ante Ctrl+C
- Mensajes de error

## Pruebas de Rendimiento

### Entorno de Pruebas
COMPLETAR

- **Hardware:** COMPLETAR
- **Sistema Operativo:** COMPLETAR
- **Base de datos:** PostgreSQL 17
- **Dataset:** 
  - Total de filas: [Completar]
  - Total de estaciones: [Completar]
  - Valores erróneos iniciales: [Completar]

### Resultados de Paralelización


(COMPLETAR)

| Procesos | Tiempo (s) | 
|----------|------------|
| 1        | X.XX       | 
| 4        | X.XX       |
| 8        | X.XX       | 

### Conclusiones

(COMPLETAR)


**Configuración Óptima:**
Para nuestro entorno, X procesos fue el punto óptimo. (COMPLETAR)

**Observaciones:**
- La eficiencia disminuye con más de X procesos (COMPLETAR)
- Para datasets más grandes, el óptimo podría ser mayor 
