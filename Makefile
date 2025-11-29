PYTHON = python3
PIP = pip3

.PHONY: help install test run clean

help: 
    @echo "Comandos disponibles en el proyecto:"
    @echo "  make install   - Instala las dependencias desde requirements.txt"
    @echo "  make test      - Ejecuta todas las pruebas unitarias (coverage completo)"
    @echo "  make run       - Ejecuta el programa principal (main.py)"
    @echo "  make clean     - Elimina archivos temporales y cachés (__pycache__)"

install: ## Instala dependencias
    $(PIP) install -r requirements.txt

test: ## Ejecuta los tests
    $(PYTHON) -m unittest discover -v

run: ## Ejecuta la aplicación
    $(PYTHON) main.py

clean: ## Limpia archivos compilados
    rm -rf __pycache__
    rm -rf */__pycache__
    rm -f *.pyc