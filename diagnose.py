#!/usr/bin/env python
"""
Script de diagnóstico para verificar el usuario demo y su acceso
"""
import os
import sys
from app import create_app, db
from app.models.users import User
from flask_login import login_user

app = create_app()

with app.app_context():
    print("=" * 70)
    print("🔍 DIAGNÓSTICO COMPLETO - USUARIO DEMO Y REDIRECCIONAMIENTO")
    print("=" * 70)
    
    # 1. Verificar DEMO_MODE
    demo_mode = app.config.get('DEMO_MODE')
    print(f"\n1️⃣  DEMO_MODE: {'✅ ACTIVADO' if demo_mode else '❌ DESACTIVADO'}")
    print(f"    Valor: {demo_mode}")
    
    # 2. Buscar usuario demo
    demo_user = User.query.filter_by(email='demo@example.com').first()
    
    if demo_user:
        print(f"\n2️⃣  USUARIO DEMO ENCONTRADO:")
        print(f"    ID: {demo_user.id}")
        print(f"    Email: {demo_user.email}")
        print(f"    Nombre: {demo_user.first_name} {demo_user.last_name}")
        print(f"    Rol en DB: '{demo_user.role}'")
        print(f"    is_admin(): {demo_user.is_admin()}")
        print(f"    Activo: {demo_user.is_active}")
        print(f"    Registrado: {demo_user.is_registered}")
        
        # Verificar si is_admin() retorna True
        if not demo_user.is_admin():
            print(f"\n    ⚠️  PROBLEMA DETECTADO: El usuario NO ES ADMIN")
            print(f"       Corrigiendo...")
            demo_user.role = 'admin'
            db.session.commit()
            print(f"       ✅ Rol actualizado a 'admin'")
        else:
            print(f"\n    ✅ El usuario ES ADMIN correctamente")
    else:
        print(f"\n2️⃣  ❌ USUARIO DEMO NO ENCONTRADO")
        print(f"    Creando usuario demo...")
        
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
        
        print(f"    ✅ Usuario demo creado")
        print(f"       Email: {demo_user.email}")
        print(f"       Rol: {demo_user.role}")
    
    # 3. Simular login y verificar redirección
    print(f"\n3️⃣  SIMULACIÓN DE LOGIN Y REDIRECCIÓN:")
    with app.test_request_context():
        login_user(demo_user, remember=True)
        from flask_login import current_user
        
        print(f"    Después de login_user():")
        print(f"    - current_user.is_authenticated: {current_user.is_authenticated}")
        print(f"    - current_user.email: {current_user.email}")
        print(f"    - current_user.role: {current_user.role}")
        print(f"    - current_user.is_admin(): {current_user.is_admin()}")
        
        if current_user.is_admin():
            from flask import url_for
            dashboard_url = url_for('admin.dashboard')
            print(f"\n    ✅ REDIRECCIÓN CORRECTA:")
            print(f"       IR A: {dashboard_url}")
        else:
            from flask import url_for
            wrong_url = url_for('teacher.dashboard')
            print(f"\n    ❌ PROBLEMA: REDIRECCIÓN INCORRECTA!")
            print(f"       Se redirige a: {wrong_url}")
            print(f"       Debería redirigir a: {url_for('admin.dashboard')}")
    
    # 4. Resumen de usuarios
    all_users = User.query.all()
    admin_users = User.query.filter_by(role='admin').all()
    teacher_users = User.query.filter_by(role='teacher').all()
    
    print(f"\n4️⃣  RESUMEN DE USUARIOS EN BASE DE DATOS:")
    print(f"    Total: {len(all_users)}")
    print(f"    Administradores: {len(admin_users)}")
    print(f"    Profesores: {len(teacher_users)}")
    
    print(f"\n5️⃣  LISTADO DETALLADO DE USUARIOS:")
    for user in all_users:
        role_str = "👨‍💼 ADMIN" if user.is_admin() else "👨‍🏫 TEACHER"
        print(f"    {role_str} - {user.email} ({user.first_name} {user.last_name})")
    
    print(f"\n" + "=" * 70)
    print(f"✅ DIAGNÓSTICO COMPLETADO")
    print(f"=" * 70)
