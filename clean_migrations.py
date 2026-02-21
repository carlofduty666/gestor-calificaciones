#!/usr/bin/env python
"""
Script para limpiar las migraciones corruptas y recrearlas
"""
import os
import shutil
from pathlib import Path

# Ruta a las migraciones
migrations_dir = Path("migrations/versions")

print("🧹 Eliminando migraciones corruptas...")

# Eliminar todos los archivos .py excepto __init__.py
for file in migrations_dir.glob("*.py"):
    if file.name != "__init__.py":
        print(f"  ❌ Eliminando: {file.name}")
        file.unlink()

print("✓ Migraciones eliminadas")
print("\nAhora ejecuta:")
print("  flask db migrate -m 'Initial migration'")
print("  flask db upgrade")
print("  python seed_demo_data.py")
