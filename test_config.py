import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from config import obtener_variable_entorno
from config import obtener_variable_entorno
from config import obtener_variable_entorno
from config import obtener_entero_valido
from config import obtener_entero_valido
from config import obtener_entero_valido
from config import obtener_entero_valido
from config import obtener_entero_valido
from config import obtener_entero_valido
from config import obtener_entero_valido

# Add the parent directory to the path to import config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestObtenerVariableEntorno(unittest.TestCase):

    @patch("config.os.getenv")
    def test_variable_exists(self, mock_getenv):
        """Test when environment variable exists"""
        mock_getenv.return_value = "test_value"
        result = obtener_variable_entorno("TEST_VAR")
        self.assertEqual(result, "test_value")
        mock_getenv.assert_called_once_with("TEST_VAR", None)

    @patch("config.os.getenv")
    def test_variable_with_default(self, mock_getenv):
        """Test when environment variable doesn't exist but default is provided"""
        mock_getenv.return_value = "default_value"
        result = obtener_variable_entorno("TEST_VAR", "default_value")
        self.assertEqual(result, "default_value")

    @patch("config.sys.exit")
    @patch("config.os.getenv")
    def test_variable_not_exists_no_default(self, mock_getenv, mock_exit):
        """Test when environment variable doesn't exist and no default"""
        mock_getenv.return_value = None
        obtener_variable_entorno("TEST_VAR")
        mock_exit.assert_called_once_with(1)


class TestObtenerEnteroValido(unittest.TestCase):

    @patch("config.obtener_variable_entorno")
    def test_valid_integer_in_range(self, mock_obtener):
        """Test valid integer within range"""
        mock_obtener.return_value = "8"
        result = obtener_entero_valido("NUM_PROCESOS", min_val=1, max_val=32)
        self.assertEqual(result, 8)

    @patch("config.os.cpu_count")
    @patch("config.obtener_variable_entorno")
    def test_default_uses_cpu_count(self, mock_obtener, mock_cpu_count):
        """Test that default uses cpu_count when not provided"""
        mock_cpu_count.return_value = 16
        mock_obtener.return_value = "16"
        result = obtener_entero_valido("NUM_PROCESOS")
        mock_obtener.assert_called_with("NUM_PROCESOS", "16")
        self.assertEqual(result, 16)

    @patch("config.sys.exit")
    @patch("config.obtener_variable_entorno")
    def test_invalid_non_integer(self, mock_obtener, mock_exit):
        """Test invalid non-integer value"""
        mock_obtener.return_value = "abc"
        obtener_entero_valido("NUM_PROCESOS")
        mock_exit.assert_called_once_with(1)

    @patch("config.sys.exit")
    @patch("config.obtener_variable_entorno")
    def test_value_below_min(self, mock_obtener, mock_exit):
        """Test value below minimum"""
        mock_obtener.return_value = "0"
        obtener_entero_valido("NUM_PROCESOS", min_val=1, max_val=32)
        mock_exit.assert_called_once_with(1)

    @patch("config.sys.exit")
    @patch("config.obtener_variable_entorno")
    def test_value_above_max(self, mock_obtener, mock_exit):
        """Test value above maximum"""
        mock_obtener.return_value = "64"
        obtener_entero_valido("NUM_PROCESOS", min_val=1, max_val=32)
        mock_exit.assert_called_once_with(1)

    @patch("config.obtener_variable_entorno")
    def test_edge_case_min_value(self, mock_obtener):
        """Test minimum edge value"""
        mock_obtener.return_value = "1"
        result = obtener_entero_valido("NUM_PROCESOS", min_val=1, max_val=32)
        self.assertEqual(result, 1)

    @patch("config.obtener_variable_entorno")
    def test_edge_case_max_value(self, mock_obtener):
        """Test maximum edge value"""
        mock_obtener.return_value = "32"
        result = obtener_entero_valido("NUM_PROCESOS", min_val=1, max_val=32)
        self.assertEqual(result, 32)


if __name__ == "__main__":
    unittest.main()
