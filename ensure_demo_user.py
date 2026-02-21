#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para asegurar que el usuario demo existe en la base de datos
Ejecutar DESPUÉS de: flask db upgrade

Compatible con:
- Base de datos local (SQLite)
- Base de datos remota (PostgreSQL en Neon.tech)

Uso:
    python ensure_demo_user.py
"""
import os
import sys

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

from app import create_app, db
from app.models.users import User

def main():
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("VERIFICANDO/CREANDO USUARIO DEMO")
        print("=" * 80)
        
        # Información de conexión
        db_url = app.config.get('SQLALCHEMY_DATABASE_URI', 'No configurado')
        print(f"\n[INFO] Base de datos: {db_url[:80]}..." if len(db_url) > 80 else f"\n[INFO] Base de datos: {db_url}")
        
        try:
            # Verificar si ya existe
            demo_user = User.query.filter_by(email='demo@example.com').first()
            
            if not demo_user:
                print("\n[CREAR] Usuario demo no encontrado. Creando...")
                demo_user = User(
                    identification_number='99999999',
                    email='demo@example.com',
                    username='demo',
                    first_name='Demo',
                    last_name='Admin',
                    role='admin',
                    is_active=True,
                    is_registered=True
                )
                demo_user.set_password('demo123')
                db.session.add(demo_user)
                db.session.commit()
                print("[OK] Usuario demo creado exitosamente")
            else:
                print(f"\n[OK] Usuario demo ya existe: {demo_user.email}")
                
                # Verificar y corregir rol si es necesario
                if demo_user.role != 'admin':
                    print(f"[CORREGIR] Rol actual: '{demo_user.role}' (debería ser 'admin')")
                    demo_user.role = 'admin'
                    db.session.commit()
                    print("[OK] Rol actualizado a 'admin'")
                
                # Verificar y corregir is_registered si es necesario
                if not demo_user.is_registered:
                    print("[CORREGIR] Usuario no registrado. Marcando como registrado...")
                    demo_user.is_registered = True
                    db.session.commit()
                    print("[OK] Usuario marcado como registrado")
            
            # Mostrar información final del usuario
            demo_user = User.query.filter_by(email='demo@example.com').first()
            print(f"\n[FINAL] Estado del usuario demo:")
            print(f"   ID: {demo_user.id}")
            print(f"   Email: {demo_user.email}")
            print(f"   Nombre: {demo_user.first_name} {demo_user.last_name}")
            print(f"   Rol: {demo_user.role}")
            print(f"   Activo: {demo_user.is_active}")
            print(f"   Registrado: {demo_user.is_registered}")
            print(f"   is_admin(): {demo_user.is_admin()}")
            
            print("\n" + "=" * 80)
            print("COMPLETADO - Usuario demo listo para usar")
            print("=" * 80)
            return 0
            
        except Exception as e:
            print(f"\n[ERROR] Error al procesar usuario demo: {str(e)}")
            import traceback
            traceback.print_exc()
            print("\n[AYUDA] Posibles causas:")
            print("  - Conexión a la base de datos fallida")
            print("  - Migraciones no aplicadas (ejecuta: flask db upgrade)")
            print("  - Problemas de permisos en la base de datos")
            print("\n" + "=" * 80)
            return 1

if __name__ == '__main__':
    sys.exit(main())
