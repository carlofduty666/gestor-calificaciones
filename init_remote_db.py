#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para INICIALIZAR LA BASE DE DATOS REMOTA (Neon.tech) en Render

Este script:
1. Se conecta a la base de datos en Neon.tech
2. Aplica las migraciones (si es necesario)
3. Crea el usuario demo automáticamente

INSTRUCCIONES PARA EJECUTAR EN RENDER:
=====================================

OPCIÓN 1: Desde la Shell de Render
1. Ve a tu proyecto en https://dashboard.render.com/
2. Ve a "Services" → Tu servicio → "Shell"
3. Ejecuta:
   python ensure_demo_user.py

OPCIÓN 2: Como un Job único en Render
1. Crea un nuevo "Background Worker" o "Cron Job"
2. Configura para ejecutar: python ensure_demo_user.py
3. Ejecuta manualmente

VARIABLES DE ENTORNO REQUERIDAS:
================================
DATABASE_URL: Tu URL de conexión a Neon.tech
DEMO_MODE: true (para activar modo demo)
"""

import os
import sys

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

def main():
    print("=" * 80)
    print("INICIALIZADOR DE BASE DE DATOS REMOTA PARA RENDER")
    print("=" * 80)
    
    # Verificar que estamos en Render
    if os.environ.get('RENDER'):
        print("\n[OK] Entorno detectado: RENDER")
    else:
        print("\n[ADVERTENCIA] No se detectó entorno RENDER")
    
    # Verificar DATABASE_URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("\n[ERROR] Variable DATABASE_URL no está configurada!")
        print("        Ve a https://dashboard.render.com/ y configura DATABASE_URL como variable de entorno")
        return 1
    
    print(f"\n[OK] Base de datos detectada: {db_url[:50]}...")
    
    # Importar después de verificar
    try:
        from app import create_app, db
        from app.models.users import User
        print("[OK] Módulos importados correctamente")
    except Exception as e:
        print(f"[ERROR] No se pudieron importar los módulos: {str(e)}")
        return 1
    
    # Crear app y ejecutar
    try:
        app = create_app()
        
        with app.app_context():
            print("\n[CONECTAR] Estableciendo conexión a la base de datos...")
            
            # Verificar conexión
            try:
                result = db.session.execute('SELECT 1')
                print("[OK] Conexión a base de datos exitosa")
            except Exception as e:
                print(f"[ERROR] No se pudo conectar a la base de datos: {str(e)}")
                return 1
            
            print("\n[CREAR] Creando/verificando usuario demo...")
            
            # Aplicar el script
            demo_user = User.query.filter_by(email='demo@example.com').first()
            
            if not demo_user:
                print("   → Usuario demo no existe, creando...")
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
                print("   [OK] Usuario demo creado")
            else:
                print(f"   → Usuario demo ya existe")
                if demo_user.role != 'admin':
                    print(f"   → Actualizando rol a 'admin'")
                    demo_user.role = 'admin'
                    db.session.commit()
            
            # Mostrar información final
            demo_user = User.query.filter_by(email='demo@example.com').first()
            print(f"\n[INFO] Usuario demo final:")
            print(f"   Email: {demo_user.email}")
            print(f"   Rol: {demo_user.role}")
            print(f"   is_admin(): {demo_user.is_admin()}")
            
            print("\n" + "=" * 80)
            print("COMPLETADO - Base de datos remota inicializada!")
            print("=" * 80)
            print("\nAhora tu aplicación en Render debería funcionar correctamente.")
            print("Accede a: https://smartboletin-demo.onrender.com/")
            return 0
            
    except Exception as e:
        print(f"\n[ERROR] Error general: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
