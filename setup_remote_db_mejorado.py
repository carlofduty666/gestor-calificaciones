#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script mejorado para inicializar base de datos remota en Neon.tech
Intenta múltiples estrategias de conexión y proporciona mejo diagnóstico
"""

import os
import sys
import time
from urllib.parse import urlparse, parse_qs

def test_simple_connection(database_url):
    """Prueba una conexión simple sin SQLAlchemy para diagnóstico"""
    print("\n[DIAGNÓSTICO] Intentando conexión directa con psycopg2...")
    try:
        import psycopg2
        # Parsear la URL
        parsed = urlparse(database_url)
        
        conn_params = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'database': parsed.path.lstrip('/')
        }
        
        # Extraer parámetros SSL de la URL si existen
        if parsed.query:
            params = parse_qs(parsed.query)
            if 'sslmode' in params:
                conn_params['sslmode'] = params['sslmode'][0]
        
        print(f"  Host: {conn_params['host']}")
        print(f"  Port: {conn_params['port']}")
        print(f"  User: {conn_params['user']}")
        print(f"  Database: {conn_params['database']}")
        
        # Intentar conexión
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        print("[✓] Conexión exitosa!")
        return True
        
    except Exception as e:
        print(f"[✗] Error en conexión directa: {e}")
        return False

def test_connection_without_ssl(database_url):
    """Intenta conexión sin SSL"""
    print("\n[INTENTO 2] Probando sin SSL...")
    try:
        import psycopg2
        parsed = urlparse(database_url)
        
        conn_params = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'database': parsed.path.lstrip('/'),
            'sslmode': 'disable'
        }
        
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        print("[✓] Conexión exitosa sin SSL!")
        return True
        
    except Exception as e:
        print(f"[✗] También falla sin SSL: {e}")
        return False

def get_database_url():
    """Obtiene DATABASE_URL del entorno o del usuario"""
    db_url = os.environ.get('DATABASE_URL')
    
    if db_url:
        print(f"[OK] DATABASE_URL detectada en variables de entorno")
        return db_url
    
    print("\n" + "="*90)
    print("DATABASE_URL no detectada en variables de entorno")
    print("="*90)
    print("\nNecesito tu URL de conexión a Neon.tech\n")
    print("Puedes obtenerla en:")
    print("  1. https://console.neon.tech/")
    print("  2. Tu proyecto → Credenciales (o Connection string)")
    print("  3. Selecciona 'Applications' (NO 'psql')")
    print("  4. Copia TODA la URL que empieza con 'postgresql://'\n")
    print("Ejemplo (pero con TU contraseña y host):")
    print("  postgresql://user:password@ep-xxx.neon.tech/neondb\n")
    print("-" * 90)
    
    while True:
        db_url = input("\nPega tu DATABASE_URL aqui: ").strip()
        
        if not db_url.startswith('postgresql://'):
            print("[ERROR] La URL debe empezar con 'postgresql://'")
            continue
        
        # Mostrar URL parcialmente para confirmación
        if '@' in db_url:
            before_at = db_url[:db_url.index('@')+1]
            after_at = db_url[db_url.index('@')+1:]
            masked_url = before_at.replace(before_at.split(':')[1], '*****') + after_at[:20] + "..."
        else:
            masked_url = db_url[:50] + "..."
        
        confirm = input(f"\n¿Está correcta esta URL?\n  {masked_url}\n(S/n): ").strip().lower()
        
        if confirm != 'n':
            return db_url
        
        print("\nDebes pegar una URL válida. Intenta de nuevo.")

def main():
    print("\n" + "="*90)
    print("INICIALIZADOR DE BASE DE DATOS REMOTA - VERSIÓN MEJORADA (CON DIAGNÓSTICO)")
    print("="*90)
    
    # Obtener URL
    database_url = get_database_url()
    print(f"\n[OK] Base de datos configurada")
    
    # Intentar diagnóstico de conexión
    print("\n" + "="*90)
    print("DIAGNÓSTICO DE CONEXIÓN")
    print("="*90)
    
    # Intento 1: Conexión simple
    success = test_simple_connection(database_url)
    
    if not success:
        # Intento 2: Sin SSL
        success = test_connection_without_ssl(database_url)
    
    if not success:
        print("\n" + "="*90)
        print("⚠️  NO SE PUEDE CONECTAR A NEON.TECH")
        print("="*90)
        print("\nPosibles causas:")
        print("  1. La base de datos está en modo 'sleep' (inactiva)")
        print("     → Ve a https://console.neon.tech/ y haz clic en tu rama para despertar")
        print("\n  2. La contraseña o credenciales son incorrectas")
        print("     → Verifica la URL en Neon.tech nuevamente")
        print("\n  3. Problema de firewall o red")
        print("     → Intenta desde una red diferente")
        print("\n  4. Neon.tech está teniendo problemas temporales")
        print("     → Espera 5-10 minutos e intenta de nuevo")
        print("\nIntentos:")
        print("  • Si Neon estaba en sleep, ejecuta el script de nuevo")
        print("  • Si crees que es un error temporal, espera y reintenta")
        print("  • Si el problema persiste, contacta a soporte de Neon.tech")
        return 1
    
    # Si la conexión es exitosa, aplicar migraciones
    print("\n" + "="*90)
    print("INICIALIZANDO BASE DE DATOS REMOTA")
    print("="*90)
    
    try:
        os.environ['DATABASE_URL'] = database_url
        
        print("\n[PASO 1/3] Importando módulos...")
        from app import create_app, db
        from flask_migrate import upgrade
        from app.models.users import User
        
        print("[OK] Módulos importados")
        
        print("\n[PASO 2/3] Aplicando migraciones (creando tablas)...")
        app = create_app()
        
        with app.app_context():
            upgrade()
            print("[OK] Migraciones aplicadas exitosamente")
            
            print("\n[PASO 3/3] Creando usuario demo...")
            demo_user = User.query.filter_by(email='demo@example.com').first()
            
            if demo_user:
                print("[OK] Usuario demo ya existe")
            else:
                demo_user = User(
                    email='demo@example.com',
                    username='demo',
                    role='admin',
                    first_name='Usuario',
                    last_name='Demo',
                    is_active=True
                )
                demo_user.set_password('demo123')
                db.session.add(demo_user)
                db.session.commit()
                print("[OK] Usuario demo creado: demo@example.com / demo123")
        
        print("\n" + "="*90)
        print("✅ ÉXITO - Base de datos remota inicializada")
        print("="*90)
        print("\nAhora puedes:")
        print("  1. Hacer push a GitHub: git push")
        print("  2. Render hará deploy automáticamente")
        print("  3. Acceder a: https://smartboletin-demo.onrender.com/")
        print("  4. Se abrirá automáticamente el admin dashboard")
        print("\n")
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
