import unittest
from unittest.mock import MagicMock, patch
import os
import sys

import config
from database import Database

from corrector import procesar_estacion


class TestConfiguracion(unittest.TestCase):
    # Pruebas para el módulo de configuración (config.py)

    def test_lectura_variables_entorno(self):
        # Verifica que se lean las variables obligatorias
        with patch.dict(
            os.environ,
            {
                "DB_HOST": "test_host",
                "DB_PORT": "5432",
                "DB_NAME": "test_db",
                "DB_USER": "user",
                "DB_PASS": "pass",
                "NUM_PROCESOS": "4",
            },
        ):
            import importlib

            importlib.reload(config)
            self.assertEqual(config.DB_HOST, "test_host")
            self.assertEqual(config.NUM_PROCESOS, 4)


class TestDatabase(unittest.TestCase):
    # Pruebas para la clase Database en database.py

    @patch("database.psycopg2.connect")
    def test_conexion_exitosa(self, mock_connect):
        # Prueba que conectar() devuelva True si psycopg2 no falla
        db = Database("host", "5432", "db", "user", "pass")
        resultado = db.conectar()
        self.assertTrue(resultado)
        self.assertIsNotNone(db.connection)

    @patch("database.psycopg2.connect")
    def test_conexion_fallida(self, mock_connect):
        # Prueba que conectar() devuelva False si hay error operativo
        from psycopg2 import OperationalError

        mock_connect.side_effect = OperationalError("Error de conexión simulado")

        db = Database("host", "5432", "db", "user", "pass")
        resultado = db.conectar()
        self.assertFalse(resultado)


class TestLogicaCorreccion(unittest.TestCase):
    # Se simula la base de datos para testing

    @patch("corrector.Database")
    def test_caso_dos_vecinos(self, MockDatabase):
        # Caso 1: Existen valor anterior y posterior. Debe promediar.
        db = MockDatabase.return_value
        db.conectar.return_value = True
        db.obtener_columnas_numericas.return_value = ["temperature"]
        # Simulamos 1 error en la estación
        db.obtener_registros_con_errores.return_value = [
            (1, "2023-01-01 12:00", -32768)
        ]

        # Simulamos valores vecinos
        db.obtener_valor_anterior.return_value = 10.0
        db.obtener_valor_posterior.return_value = 20.0

        # Ejecutar
        procesar_estacion(99)

        # Verificación: (10 + 20) / 2 = 15.0
        db.actualizar_observacion.assert_called_with(1, "temperature", 15.0)

    @patch("corrector.Database")
    def test_caso_solo_anterior(self, MockDatabase):
        # Caso 2: Solo existe valor anterior. Debe usar ese.
        db = MockDatabase.return_value
        db.conectar.return_value = True
        db.obtener_columnas_numericas.return_value = ["temperature"]
        db.obtener_registros_con_errores.return_value = [
            (2, "2023-01-01 12:00", -32768)
        ]

        db.obtener_valor_anterior.return_value = 10.0
        db.obtener_valor_posterior.return_value = None

        procesar_estacion(99)

        # Verificación: Debe usar 10.0
        db.actualizar_observacion.assert_called_with(2, "temperature", 10.0)

    @patch("corrector.Database")
    def test_caso_solo_posterior(self, MockDatabase):
        # Caso 3: Solo existe valor posterior. Debe usar ese.
        db = MockDatabase.return_value
        db.conectar.return_value = True
        db.obtener_columnas_numericas.return_value = ["temperature"]
        db.obtener_registros_con_errores.return_value = [
            (3, "2023-01-01 12:00", -32768)
        ]

        db.obtener_valor_anterior.return_value = None
        db.obtener_valor_posterior.return_value = 20.0

        procesar_estacion(99)

        # Verificación: Debe usar 20.0
        db.actualizar_observacion.assert_called_with(3, "temperature", 20.0)

    @patch("corrector.Database")
    def test_caso_sin_vecinos(self, MockDatabase):
        # Caso 4: No hay vecinos. Debe asignar 0
        db = MockDatabase.return_value
        db.conectar.return_value = True
        db.obtener_columnas_numericas.return_value = ["temperature"]
        db.obtener_registros_con_errores.return_value = [
            (4, "2023-01-01 12:00", -32768)
        ]

        db.obtener_valor_anterior.return_value = None
        db.obtener_valor_posterior.return_value = None

        procesar_estacion(99)

        # Verificación: Valor 0
        db.actualizar_observacion.assert_called_with(4, "temperature", 0)


if __name__ == "__main__":
    unittest.main()
