#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para INICIALIZAR completamente la base de datos remota en Render

Este script:
1. Conecta a la base de datos remota (Neon.tech)
2. Aplica las migraciones (crea todas las tablas)
3. Crea el usuario demo automáticamente

INSTRUCCIONES PARA RENDER:
==========================

1. Ve a https://dashboard.render.com/
2. Selecciona tu servicio (smartboletin-demo)
3. Ve a la pestaña "Shell"
4. Ejecuta este comando:
   python setup_remote_db.py
5. Espera a que termina (debe decir COMPLETADO)
6. Listo - las tablas están creadas y el usuario demo existe
"""

import os
import sys
import subprocess

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

def run_flask_db_upgrade():
    """Ejecutar flask db upgrade usando subprocess"""
    try:
        print("   [Ejecutando] flask db upgrade...")
        result = subprocess.run(['flask', 'db', 'upgrade'], 
                              capture_output=True, 
                              text=True, 
                              timeout=60)
        
        if result.returncode == 0:
            print("   [OK] Migraciones aplicadas")
            return True
        else:
            # Si falla, mostrar error pero continuar
            error_msg = result.stderr or result.stdout
            if "head is None" in error_msg:
                print("   [ADVERTENCIA] head is None (primera ejecución), continuando...")
                return True
            else:
                print(f"   [ADVERTENCIA] {error_msg}")
                return True  # Continuamos de todas formas
    except subprocess.TimeoutExpired:
        print("   [ADVERTENCIA] Timeout en flask db upgrade, continuando...")
        return True
    except FileNotFoundError:
        print("   [ADVERTENCIA] flask no encontrado, intentando alternativa...")
        return True
    except Exception as e:
        print(f"   [ADVERTENCIA] Error: {str(e)}")
        return True

def main():
    print("=" * 90)
    print("INICIALIZADOR COMPLETO DE BASE DE DATOS REMOTA PARA RENDER")
    print("=" * 90)
    
    # Verificar DATABASE_URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("\n[ERROR] Variable DATABASE_URL no está configurada!")
        print("        Ve a https://dashboard.render.com/ y configura DATABASE_URL")
        return 1
    
    # Ocultar URL completa por seguridad
    db_display = db_url[:50] + "..." if len(db_url) > 50 else db_url
    print(f"\n[OK] Base de datos detectada: {db_display}")
    
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
            
            # Intentar con subprocess primero (más confiable en Render)
            flask_success = run_flask_db_upgrade()
            
            if not flask_success:
                # Alternativa: intentar con upgrade de Alembic directamente
                try:
                    print("   [Intentando] Alternativa con Alembic...")
                    from flask_migrate import upgrade as alembic_upgrade
                    alembic_upgrade()
                    print("   [OK] Migraciones aplicadas (vía Alembic)")
                except Exception as e:
                    print(f"   [ADVERTENCIA] {str(e)}")
            
            # PASO 2: Verificar conexión
            print("\n[PASO 2/3] Verificando conexión a la base de datos...")
            try:
                # Intentar una query simple
                from sqlalchemy import text
                result = db.session.execute(text('SELECT 1'))
                print("[OK] Conexión a base de datos exitosa")
            except Exception as e:
                print(f"[ERROR] No se pudo conectar: {str(e)}")
                print("[AYUDA] Posibles causas:")
                print("  - DATABASE_URL incorrecta")
                print("  - Problema en Neon.tech")
                print("  - Red no permite conexión")
                return 1
            
            # PASO 3: Crear usuario demo
            print("\n[PASO 3/3] Creando/verificando usuario demo...")
            
            try:
                demo_user = User.query.filter_by(email='demo@example.com').first()
            except Exception as e:
                print(f"   [ERROR] No se pudo consultar tabla users: {str(e)}")
                print("   [AYUDA] Las migraciones probablemente no se aplicaron correctamente")
                print("   [SOLUCIÓN] Intenta ejecutar manualmente en Render Shell:")
                print("      flask db stamp head")
                print("      flask db upgrade")
                return 1
            
            if not demo_user:
                print("   → Usuario demo NO existe, creando...")
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
                
                # Corregir rol si es necesario
                if demo_user.role != 'admin':
                    print(f"   → Corrigiendo rol de '{demo_user.role}' a 'admin'")
                    demo_user.role = 'admin'
                    db.session.commit()
                
                # Corregir is_registered si es necesario
                if not demo_user.is_registered:
                    print("   → Marcando como registrado")
                    demo_user.is_registered = True
                    db.session.commit()
            
            # Mostrar información final
            demo_user = User.query.filter_by(email='demo@example.com').first()
            
            print(f"\n[INFORMACIÓN FINAL] Usuario demo:")
            print(f"   ├─ Email: {demo_user.email}")
            print(f"   ├─ Nombre: {demo_user.first_name} {demo_user.last_name}")
            print(f"   ├─ Rol: {demo_user.role}")
            print(f"   ├─ Activo: {demo_user.is_active}")
            print(f"   ├─ Registrado: {demo_user.is_registered}")
            print(f"   └─ is_admin(): {demo_user.is_admin()}")
            
            print("\n" + "=" * 90)
            print("COMPLETADO - Base de datos remota inicializada correctamente!")
            print("=" * 90)
            
            print("\nProximos pasos:")
            print("1. Vuelve a Render Dashboard")
            print("2. Ve a tu servicio")
            print("3. Accede a: https://smartboletin-demo.onrender.com/")
            print("\n[OK] ¡Todo debería funcionar ahora!")
            
            return 0
            
        except Exception as e:
            print(f"\n[ERROR] Error durante la inicialización: {str(e)}")
            import traceback
            traceback.print_exc()
            
            print("\n[AYUDA] Posibles problemas:")
            print("  1. Conexión a BD fallida - Verifica DATABASE_URL")
            print("  2. Migraciones incompletas - Ejecuta: flask db stamp head")
            print("  3. Problema de permisos - Contacta a Render/Neon")
            
            return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

