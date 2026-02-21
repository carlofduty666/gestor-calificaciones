#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para INICIALIZAR la base de datos remota en Render
Versión mejorada: Pide la DATABASE_URL si no está configurada

Uso:
    python setup_remote_db_interactive.py
"""

import os
import sys
import getpass

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

def get_database_url():
    """Obtener DATABASE_URL del usuario si no está configurada"""
    
    # Primero intenta obtener de variable de entorno
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        return db_url
    
    # Si no existe, pedir al usuario
    print("=" * 90)
    print("DATABASE_URL no detectada")
    print("=" * 90)
    print("\nNecesito tu URL de conexión a Neon.tech")
    print("\nPuedes obtenerla en:")
    print("  1. https://console.neon.tech/")
    print("  2. Tu proyecto → Credenciales (o Connection string)")
    print("  3. Copia la URL que empieza con 'postgresql://'")
    print("\nEjemplo:")
    print("  postgresql://user:password@ep-xxx.neon.tech/neondb")
    
    while True:
        print("\n" + "-" * 90)
        db_url = input("Pega tu DATABASE_URL aqui: ").strip()
        
        if not db_url:
            print("[ERROR] No puedes dejar esto vacío")
            continue
        
        if not db_url.startswith('postgresql://'):
            print("[ERROR] Debe empezar con 'postgresql://'")
            continue
        
        # Confirmar
        print("\n¿Está correcta esta URL?")
        print(f"  {db_url[:50]}...")
        confirm = input("(S/n): ").strip().lower()
        
        if confirm in ['s', 'si', 'yes', 'y', '']:
            return db_url
        else:
            print("Intenta de nuevo...")

def main():
    print("\n" + "=" * 90)
    print("INICIALIZADOR DE BASE DE DATOS REMOTA - VERSIÓN INTERACTIVA")
    print("=" * 90)
    
    # Obtener DATABASE_URL
    db_url = get_database_url()
    os.environ['DATABASE_URL'] = db_url
    
    # Ocultar URL para mostrar
    db_display = db_url[:50] + "..." if len(db_url) > 50 else db_url
    print(f"\n[OK] Base de datos: {db_display}")
    
    # Importar módulos
    try:
        from app import create_app, db
        from app.models.users import User
        print("[OK] Módulos importados correctamente\n")
    except Exception as e:
        print(f"[ERROR] No se pudieron importar los módulos: {str(e)}")
        return 1
    
    app = create_app()
    
    with app.app_context():
        try:
            # PASO 1: Aplicar migraciones
            print("[PASO 1/3] Aplicando migraciones (creando tablas)...")
            try:
                from flask_migrate import upgrade
                upgrade()
                print("[OK] Migraciones aplicadas exitosamente")
            except Exception as e:
                if "head is None" in str(e):
                    print("[ADVERTENCIA] head is None, continuando...")
                else:
                    print(f"[ADVERTENCIA] {str(e)}")
            
            # PASO 2: Verificar conexión
            print("\n[PASO 2/3] Verificando conexión a la base de datos...")
            try:
                from sqlalchemy import text
                result = db.session.execute(text('SELECT 1'))
                print("[OK] Conexión exitosa")
            except Exception as e:
                print(f"[ERROR] No se pudo conectar: {str(e)}")
                print("[AYUDA] Verifica que DATABASE_URL sea correcta")
                return 1
            
            # PASO 3: Crear usuario demo
            print("\n[PASO 3/3] Creando/verificando usuario demo...")
            
            try:
                demo_user = User.query.filter_by(email='demo@example.com').first()
            except Exception as e:
                print(f"[ERROR] No se pudo consultar tabla users: {str(e)}")
                print("[AYUDA] Las tablas pueden no existir aún")
                return 1
            
            if not demo_user:
                print("   → Creando usuario demo...")
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
                print(f"   → Usuario demo YA existe")
                
                if demo_user.role != 'admin':
                    print(f"   → Corrigiendo rol a 'admin'")
                    demo_user.role = 'admin'
                    db.session.commit()
            
            # Información final
            demo_user = User.query.filter_by(email='demo@example.com').first()
            
            print(f"\n[ESTADO FINAL] Usuario demo:")
            print(f"   ├─ Email: {demo_user.email}")
            print(f"   ├─ Rol: {demo_user.role}")
            print(f"   └─ is_admin(): {demo_user.is_admin()}")
            
            print("\n" + "=" * 90)
            print("✅ COMPLETADO - Base de datos remota inicializada!")
            print("=" * 90)
            print("\nAhora accede a: https://smartboletin-demo.onrender.com/")
            
            return 0
            
        except Exception as e:
            print(f"\n[ERROR] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == '__main__':
    sys.exit(main())
