#!/usr/bin/env python
"""
Script para probar la redirección en DEMO_MODE
Simula exactamente lo que sucede cuando se accede a la raíz /
"""
from app import create_app, db
from app.models.users import User
from flask_login import login_user, current_user
from flask import url_for

app = create_app()

with app.app_context():
    print("=" * 70)
    print("🧪 PRUEBA DE REDIRECCIÓN EN DEMO_MODE")
    print("=" * 70)
    
    # Verificar que estamos en DEMO_MODE
    print(f"\n1️⃣  VERIFICACIÓN DE ENTORNO:")
    print(f"    DEMO_MODE: {app.config.get('DEMO_MODE')}")
    
    # Crear un test context como si fuera una solicitud a /
    with app.test_request_context('/'):
        print(f"\n2️⃣  SIMULACIÓN DE ACCESO A LA RAÍZ (/):")
        print(f"    - current_user.is_authenticated (inicial): {current_user.is_authenticated}")
        
        # Simular lo que hace la ruta index()
        if app.config.get('DEMO_MODE'):
            if not current_user.is_authenticated:
                try:
                    demo_user = User.query.filter_by(email='demo@example.com').first()
                    if demo_user and demo_user.role == 'admin':
                        print(f"    - Encontrado usuario demo con rol 'admin'")
                        login_user(demo_user, remember=True)
                        print(f"    - login_user() ejecutado")
                except Exception as e:
                    print(f"    - Error: {e}")
        
        # Verificar estado después de login
        print(f"\n3️⃣  ESTADO DESPUÉS DEL LOGIN:")
        print(f"    - current_user.is_authenticated: {current_user.is_authenticated}")
        print(f"    - current_user.email: {current_user.email}")
        print(f"    - current_user.role: {current_user.role}")
        print(f"    - current_user.is_admin(): {current_user.is_admin()}")
        
        # Determinar a dónde redirigir
        if current_user.is_authenticated:
            if current_user.is_admin():
                destination = url_for('admin.dashboard')
                print(f"\n4️⃣  REDIRECCIÓN:")
                print(f"    ✅ REDIRIGIR A: {destination}")
            else:
                destination = url_for('teacher.dashboard')
                print(f"\n4️⃣  REDIRECCIÓN:")
                print(f"    ❌ REDIRIGIR A: {destination} (INCORRECTO)")
        else:
            destination = url_for('auth.login')
            print(f"\n4️⃣  REDIRECCIÓN:")
            print(f"    ❌ REDIRIGIR A: {destination} (INCORRECTO)")
    
    # Prueba con la ruta de login también
    with app.test_request_context('/auth/login'):
        print(f"\n5️⃣  SIMULACIÓN DE ACCESO A /auth/login:")
        
        # Limpiar el login anterior
        from flask_login import logout_user
        logout_user()
        
        print(f"    - current_user.is_authenticated (inicial): {current_user.is_authenticated}")
        
        # Simular lo que hace la ruta login()
        if app.config.get('DEMO_MODE'):
            if not current_user.is_authenticated:
                try:
                    demo_user = User.query.filter_by(email='demo@example.com').first()
                    if demo_user and demo_user.role == 'admin':
                        print(f"    - Encontrado usuario demo con rol 'admin'")
                        login_user(demo_user, remember=True)
                        destination = url_for('admin.dashboard')
                        print(f"    - login_user() ejecutado")
                        print(f"    ✅ REDIRIGIR A: {destination}")
                except Exception as e:
                    print(f"    - Error: {e}")
    
    print(f"\n" + "=" * 70)
    print(f"✅ PRUEBA COMPLETADA")
    print(f"=" * 70)
