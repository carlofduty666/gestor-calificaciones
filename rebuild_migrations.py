#!/usr/bin/env python
"""
Script para reconstruir las migraciones de forma limpia
"""
import os
import shutil
import subprocess
import sys

def run_command(cmd, description):
    """Ejecuta un comando y reporta el resultado"""
    print(f"\n{'='*60}")
    print(f"➤ {description}")
    print(f"{'='*60}")
    # Reemplazar 'flask' con 'python -m flask' para usar desde venv
    cmd = cmd.replace("flask ", "python -m flask ")
    result = subprocess.run(cmd, shell=True, capture_output=False)
    if result.returncode != 0:
        print(f"⚠️  Error ejecutando: {cmd}")
        return False
    return True

def main():
    print("🔄 Reconstruyendo migraciones...")
    
    # 1. Eliminar archivos de migración viejos (excepto __pycache__)
    versions_dir = "migrations/versions"
    if os.path.exists(versions_dir):
        for file in os.listdir(versions_dir):
            if file.endswith(".py"):
                file_path = os.path.join(versions_dir, file)
                print(f"Eliminando: {file_path}")
                os.remove(file_path)
    
    # 2. Eliminar la base de datos anterior
    if os.path.exists("instance/app.db"):
        print("\nEliminando base de datos anterior...")
        os.remove("instance/app.db")
        print("✓ Base de datos eliminada")
    
    # 3. Crear la base de datos nueva
    if not run_command("flask db init", "Inicializando Alembic"):
        sys.exit(1)
    
    # 4. Generar la primera migración
    if not run_command('flask db migrate -m "Initial migration"', "Generando primera migración"):
        sys.exit(1)
    
    # 5. Aplicar la migración
    if not run_command("flask db upgrade", "Aplicando migraciones"):
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ ¡Migraciones reconstruidas exitosamente!")
    print("="*60)

if __name__ == "__main__":
    main()
