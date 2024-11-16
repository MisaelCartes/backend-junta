#!/usr/bin/env bash
# exit on error
set -o errexit

# Actualizar pip
python -m pip install --upgrade pip

# Instalar requerimientos
pip install -r requirements.txt

# Colectar archivos estáticos
python manage.py collectstatic --no-input

# Ejecutar migraciones solo si la base de datos está disponible
if [ "$DATABASE_URL" != "" ]; then
    python manage.py migrate
fi