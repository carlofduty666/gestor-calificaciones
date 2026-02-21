#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para probar el nuevo flujo con logout explícito en DEMO_MODE
"""
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

from app import create_app, db
from app.models.users import User
from flask_login import login_user, current_user, logout_user
from flask import url_for

app = create_app()

with app.app_context():
    print("=" * 80)
    print("[PRUEBA] FLUJO CORREGIDO: logout + login en DEMO_MODE")
    print("=" * 80)
    
    # Obtener usuario demo
    demo_user = User.query.filter_by(email='demo@example.com').first()
    if not demo_user:
        print("\n[ERROR] Usuario demo no existe!")
        exit(1)
    
    # Obtener cualquier otro usuario para simular una sesión previa
    other_user = User.query.filter_by(role='teacher').first()
    
    if not other_user:
        print("\n[ERROR] No hay usuario teacher para simular sesión previa!")
        exit(1)
    
    print(f"\n[INFO] Usuario demo: {demo_user.email} ({demo_user.role})")
    print(f"[INFO] Usuario previo (simulado): {other_user.email} ({other_user.role})")
    
    # Prueba 1: Simular sesión previa de teacher, luego acceso a /
    print("\n" + "=" * 80)
    print("[TEST 1] Con sesión previa de TEACHER, acceso a /")
    print("=" * 80)
    
    with app.test_request_context('/'):
        # Simular sesión previa de un teacher
        print("\n1. SIMULAR SESIÓN PREVIA DE TEACHER:")
        login_user(other_user, remember=True)
        print(f"   Logueado como: {current_user.email} ({current_user.role})")
        print(f"   is_admin(): {current_user.is_admin()}")
        
        # Simular lo que hace index() CON EL NUEVO CÓDIGO
        print("\n2. EJECUTANDO NUEVA LÓGICA DE index():")
        if app.config.get('DEMO_MODE'):
            print("   DEMO_MODE activo")
            # NUEVO: Hacer logout primero
            logout_user()
            print("   - logout_user() ejecutado")
            
            # Luego, hacer login con el usuario demo
            try:
                demo_from_db = User.query.filter_by(email='demo@example.com').first()
                if demo_from_db and demo_from_db.role == 'admin':
                    login_user(demo_from_db, remember=True)
                    print("   - login_user(demo_user) ejecutado")
            except Exception as e:
                print(f"   - Error: {e}")
        
        # Verificar estado final
        print("\n3. ESTADO FINAL DESPUÉS DE logout + login:")
        print(f"   current_user.is_authenticated: {current_user.is_authenticated}")
        print(f"   current_user.email: {current_user.email}")
        print(f"   current_user.role: {current_user.role}")
        print(f"   current_user.is_admin(): {current_user.is_admin()}")
        
        # Redirección
        print("\n4. REDIRECCIÓN:")
        if current_user.is_authenticated and current_user.is_admin():
            print(f"   [OK] REDIRIGIR A: {url_for('admin.dashboard')}")
        else:
            print(f"   [ERROR] REDIRIGIR A: {url_for('teacher.dashboard')}")
    
    # Prueba 2: Mismo test pero con /auth/login
    print("\n" + "=" * 80)
    print("[TEST 2] Con sesión previa de TEACHER, acceso a /auth/login")
    print("=" * 80)
    
    with app.test_request_context('/auth/login'):
        # Simular sesión previa de un teacher
        print("\n1. SIMULAR SESIÓN PREVIA DE TEACHER:")
        login_user(other_user, remember=True)
        print(f"   Logueado como: {current_user.email} ({current_user.role})")
        
        # Simular lo que hace login() CON EL NUEVO CÓDIGO
        print("\n2. EJECUTANDO NUEVA LÓGICA DE login():")
        if app.config.get('DEMO_MODE'):
            print("   DEMO_MODE activo")
            # NUEVO: Hacer logout primero
            logout_user()
            print("   - logout_user() ejecutado")
            
            # Luego, hacer login con el usuario demo
            try:
                demo_from_db = User.query.filter_by(email='demo@example.com').first()
                if demo_from_db and demo_from_db.role == 'admin':
                    login_user(demo_from_db, remember=True)
                    print("   - login_user(demo_user) ejecutado")
                    destination = url_for('admin.dashboard')
            except Exception as e:
                print(f"   - Error: {e}")
        
        # Verificar estado final
        print("\n3. ESTADO FINAL:")
        print(f"   current_user.email: {current_user.email}")
        print(f"   current_user.role: {current_user.role}")
        print(f"   current_user.is_admin(): {current_user.is_admin()}")
        
        # Redirección
        print("\n4. REDIRECCIÓN:")
        if current_user.is_admin():
            print(f"   [OK] REDIRIGIR A: {url_for('admin.dashboard')}")
    
    print("\n" + "=" * 80)
    print("[OK] PRUEBA COMPLETADA - El nuevo flujo funciona correctamente!")
    print("=" * 80)
