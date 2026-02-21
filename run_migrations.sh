#!/bin/bash
# Script ultra-simple para ejecutar las migraciones en Render
# Uso: bash run_migrations.sh

echo "=================================="
echo "Aplicando migraciones a Neon..."
echo "=================================="

echo ""
echo "[1/2] Ejecutando: flask db upgrade"
flask db upgrade

echo ""
echo "[2/2] Ejecutando: python ensure_demo_user.py"
python ensure_demo_user.py

echo ""
echo "=================================="
echo "COMPLETADO"
echo "=================================="
