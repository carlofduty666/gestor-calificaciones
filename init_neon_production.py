#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para inicializar la base de datos en Neon.tech DESDE CERO.
Esto es una solución PERMANENTE - después de esto, la BD estará completamente funcional.

PASOS:
1. Obtiene la URL de Neon.tech
2. Intenta conexión (con reintentos si Neon estaba en sleep)
3. Aplica TODAS las migraciones (crea todas las tablas)
4. Verifica que las tablas están creadas
5. LISTO - BD funcional, no hay más problemas de "relation does not exist"
"""

import os
import sys
import time
import subprocess
from urllib.parse import urlparse

def print_banner(title):
    """Imprime banner con título"""
    print("\n" + "="*100)
    print(f"  {title}")
    print("="*100)

def get_database_url():
    """Obtiene la URL de Neon.tech (del entorno o del usuario)"""
    db_url = os.environ.get('DATABASE_URL')
    
    if db_url and 'neon' in db_url.lower():
        print(f"[✓] DATABASE_URL detectada en variables de entorno (Neon.tech)")
        return db_url
    
    print_banner("OBTENER URL DE NEON.TECH")
    
    print("\nVe a https://console.neon.tech/ y:")
    print("  1. Selecciona tu proyecto")
    print("  2. Ve a 'Credenciales' o 'Connection string'")
    print("  3. Selecciona 'Applications' (NO 'psql')")
    print("  4. Copia la URL completa (postgresql://...)\n")
    
    while True:
        db_url = input("Pega tu DATABASE_URL de Neon.tech: ").strip()
        
        if not db_url.startswith('postgresql://'):
            print("[✗] ERROR: La URL debe empezar con 'postgresql://'")
            continue
        
        # Validar que sea Neon
        if 'neon.tech' not in db_url:
            confirm = input("[⚠] Esta URL no parece ser de Neon.tech. ¿Continuar? (s/n): ").lower()
            if confirm != 's':
                continue
        
        # Mostrar confirmación (mascarando contraseña)
        if '@' in db_url:
            parts = db_url.split('@')
            before = parts[0][:10] + "***"
            after = parts[1][:30] + "..."
            masked = f"{before}@{after}"
        else:
            masked = db_url[:50] + "..."
        
        confirm = input(f"\n¿URL correcta?\n  {masked}\n(s/n): ").lower()
        if confirm == 's':
            return db_url
        
        print("Intenta de nuevo.\n")

def test_connection(database_url, attempt=1, max_attempts=3):
    """Prueba conexión a Neon - con reintentos si está en sleep"""
    print(f"\n[PASO {attempt}/{max_attempts}] Intentando conexión a Neon.tech...")
    
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        parsed = urlparse(database_url)
        
        # Conectar (sin parámetros complicados de SSL)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/'),
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1")  # Test query
        cursor.close()
        conn.close()
        
        print("[✓] Conexión exitosa a Neon.tech!")
        return True
        
    except Exception as e:
        error_msg = str(e).lower()
        
        # Si está en sleep, esperar e intentar de nuevo
        if 'connection' in error_msg or 'closed' in error_msg or 'timeout' in error_msg:
            if attempt < max_attempts:
                print(f"[!] Neon.tech probablemente está en modo sleep (conexión rechazada)")
                print(f"    Esperando 5 segundos antes de reintentar... ({attempt}/{max_attempts})")
                time.sleep(5)
                return test_connection(database_url, attempt + 1, max_attempts)
        
        print(f"[✗] Error de conexión: {e}")
        return False

def apply_migrations(database_url):
    """Aplica las migraciones a Neon.tech usando Flask-Migrate"""
    print(f"\n[PASO 2] Aplicando TODAS las migraciones a Neon.tech...")
    print("         Esto creará todas las tablas necesarias...\n")
    
    try:
        # Configurar variable de entorno
        os.environ['DATABASE_URL'] = database_url
        os.environ['FLASK_APP'] = 'run.py'
        
        # Importar módulos
        from app import create_app, db
        from flask_migrate import upgrade
        
        # Crear app y contexto
        app = create_app()
        
        with app.app_context():
            # Ejecutar upgrade (aplica todas las migraciones pendientes)
            print("  Aplicando migraciones...")
            upgrade()
            print("  [✓] Migraciones aplicadas exitosamente!")
            
        return True
        
    except Exception as e:
        print(f"[✗] Error al aplicar migraciones: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_tables(database_url):
    """Verifica que todas las tablas fueron creadas"""
    print(f"\n[PASO 3] Verificando que todas las tablas fueron creadas...\n")
    
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        parsed = urlparse(database_url)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/'),
        )
        
        cursor = conn.cursor()
        
        # Contar tablas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema='public'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not tables:
            print("[✗] ERROR: No se crearon tablas!")
            return False
        
        print(f"[✓] Base de datos creada exitosamente con {len(tables)} tablas:\n")
        
        for table in tables:
            print(f"    • {table[0]}")
        
        return True
        
    except Exception as e:
        print(f"[✗] Error al verificar tablas: {e}")
        return False

def main():
    """Función principal"""
    print_banner("INICIALIZADOR DE BASE DE DATOS NEON.TECH - SOLUCIÓN PERMANENTE")
    
    print("""
Este script:
  1. Se conecta a tu base de datos Neon.tech
  2. Aplica TODAS las migraciones necesarias
  3. Crea las 16+ tablas requeridas
  4. Verifica que todo esté OK

RESULTADO FINAL: Base de datos completamente funcional, sin más errores de "relation does not exist"
    """)
    
    # Paso 1: Obtener URL
    database_url = get_database_url()
    
    # Paso 2: Probar conexión con reintentos
    if not test_connection(database_url):
        print_banner("ERROR DE CONEXIÓN")
        print("""
Posibles causas y soluciones:

1. NEON.TECH EN SLEEP (la causa más probable)
   → Ve a https://console.neon.tech/
   → Haz clic en tu rama para "despertar" la BD
   → Ejecuta este script de nuevo

2. CREDENCIALES INCORRECTAS
   → Verifica la URL en la consola de Neon.tech
   → Asegúrate de copiar TODA la URL
   
3. FIREWALL O RED
   → Intenta desde una red diferente
   → O espera 5-10 minutos e intenta de nuevo

4. PROBLEMA CON NEON.TECH
   → Su servidor podría estar teniendo problemas
   → Intenta más tarde
        """)
        return 1
    
    # Paso 3: Aplicar migraciones
    if not apply_migrations(database_url):
        print_banner("ERROR AL APLICAR MIGRACIONES")
        return 1
    
    # Paso 4: Verificar tablas
    if not verify_tables(database_url):
        print_banner("ERROR DE VERIFICACIÓN")
        return 1
    
    # ¡ÉXITO!
    print_banner("✅ ÉXITO - BASE DE DATOS INICIALIZADA COMPLETAMENTE")
    
    print("""
Próximos pasos:

1. HACER PUSH A GITHUB:
   git add .
   git commit -m "Remove login requirement for DEMO_MODE - init Neon DB"
   git push origin main

2. RENDER HARÁ DEPLOY AUTOMÁTICAMENTE
   Espera a que Render termine de deployar

3. ACCEDER A LA APLICACIÓN:
   https://smartboletin-demo.onrender.com/
   
   ¡Deberías ver el dashboard admin directamente, sin login!

4. LISTO
   La base de datos está permanentemente inicializada.
   No habrá más cambios ni problemas de "relation does not exist".
    """)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
