#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para debuggear el flujo completo de login y redirección
Simula exactamente lo que sucede en los requests HTTP
"""
import os
import sys

# Configurar encoding UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'

from app import create_app, db
from app.models.users import User
from flask_login import login_user, current_user, logout_user
from flask import url_for

app = create_app()

with app.app_context():
    print("=" * 80)
    print("[DEBUG] FLUJO DE LOGIN Y REDIRECCIÓN EN DEMO_MODE")
    print("=" * 80)
    
    # Obtener usuario demo
    demo_user = User.query.filter_by(email='demo@example.com').first()
    if not demo_user:
        print("\n[ERROR] Usuario demo no existe!")
        exit(1)
    
    print("\n[INFO] USUARIO DEMO EN LA BASE DE DATOS:")
    print(f"   ID: {demo_user.id}")
    print(f"   Email: {demo_user.email}")
    print(f"   Nombre: {demo_user.first_name} {demo_user.last_name}")
    print(f"   Rol (texto): '{demo_user.role}'")
    print(f"   Rol (type): {type(demo_user.role)}")
    print(f"   is_admin() retorna: {demo_user.is_admin()}")
    print(f"   is_teacher() retorna: {demo_user.is_teacher()}")
    
    # Prueba 1: Simular acceso a / SIN sesión previa
    print("\n" + "=" * 80)
    print("[TEST 1] Acceso a / (sin sesion previa)")
    print("=" * 80)
    
    with app.test_request_context('/'):
        # Verificar que NO hay sesión
        print("\n1. ESTADO INICIAL:")
        print(f"   current_user.is_authenticated: {current_user.is_authenticated}")
        
        # Simular lo que hace index()
        print("\n2. EJECUTANDO LÓGICA DE index():")
        if app.config.get('DEMO_MODE'):
            if not current_user.is_authenticated:
                try:
                    demo_from_db = User.query.filter_by(email='demo@example.com').first()
                    print(f"   Usuario demo encontrado: {demo_from_db is not None}")
                    if demo_from_db:
                        print(f"   demo_from_db.role: '{demo_from_db.role}'")
                        print(f"   demo_from_db.is_admin(): {demo_from_db.is_admin()}")
                    
                    if demo_from_db and demo_from_db.role == 'admin':
                        login_user(demo_from_db, remember=True)
                        print(f"   login_user() ejecutado")
                except Exception as e:
                    print(f"   Error durante login: {e}")
        
        # Verificar estado después de login_user
        print("\n3. DESPUÉS DE login_user():")
        print(f"   current_user.is_authenticated: {current_user.is_authenticated}")
        print(f"   current_user.id: {current_user.id if current_user.is_authenticated else 'N/A'}")
        print(f"   current_user.email: {current_user.email if current_user.is_authenticated else 'N/A'}")
        print(f"   current_user.role: '{current_user.role}' (type: {type(current_user.role).__name__})")
        print(f"   current_user.is_admin(): {current_user.is_admin() if current_user.is_authenticated else 'N/A'}")
        print(f"   current_user.is_teacher(): {current_user.is_teacher() if current_user.is_authenticated else 'N/A'}")
        
        # Determinar redirección
        print("\n4. LÓGICA DE REDIRECCIÓN:")
        if current_user.is_authenticated:
            if current_user.is_admin():
                print(f"   [OK] REDIRIGIR A: {url_for('admin.dashboard')}")
            else:
                print(f"   [ERROR] REDIRIGIR A: {url_for('teacher.dashboard')} (INCORRECTO - debería ser admin)")
        else:
            print(f"   [ERROR] NO AUTENTICADO")
    
    # Prueba 2: Simular acceso a /auth/login SIN sesión previa
    print("\n" + "=" * 80)
    print("[TEST 2] Acceso a /auth/login (sin sesion previa)")
    print("=" * 80)
    
    with app.test_request_context('/auth/login'):
        # Limpiar sesión anterior
        logout_user()
        
        print("\n1. ESTADO INICIAL:")
        print(f"   current_user.is_authenticated: {current_user.is_authenticated}")
        
        # Simular lo que hace login()
        print("\n2. EJECUTANDO LÓGICA DE login():")
        if app.config.get('DEMO_MODE'):
            if not current_user.is_authenticated:
                try:
                    demo_from_db = User.query.filter_by(email='demo@example.com').first()
                    print(f"   Usuario demo encontrado: {demo_from_db is not None}")
                    if demo_from_db:
                        print(f"   demo_from_db.role: '{demo_from_db.role}'")
                        print(f"   demo_from_db.is_admin(): {demo_from_db.is_admin()}")
                    
                    if demo_from_db and demo_from_db.role == 'admin':
                        login_user(demo_from_db, remember=True)
                        print(f"   login_user() ejecutado")
                except Exception as e:
                    print(f"   Error durante login: {e}")
        
        # Verificar estado después de login_user
        print("\n3. DESPUÉS DE login_user():")
        print(f"   current_user.is_authenticated: {current_user.is_authenticated}")
        print(f"   current_user.role: '{current_user.role}' (type: {type(current_user.role).__name__})")
        print(f"   current_user.is_admin(): {current_user.is_admin()}")
        
        # Determinar redirección
        print("\n4. LÓGICA DE REDIRECCIÓN:")
        if current_user.is_authenticated:
            if current_user.is_admin():
                print(f"   [OK] REDIRIGIR A: {url_for('admin.dashboard')}")
            else:
                print(f"   [ERROR] REDIRIGIR A: {url_for('teacher.dashboard')} (INCORRECTO)")
        else:
            print(f"   [ERROR] NO AUTENTICADO")
    
    # Prueba 3: Verificar el before_request del admin
    print("\n" + "=" * 80)
    print("[TEST 3] Verificar before_request del admin")
    print("=" * 80)
    
    with app.test_request_context('/admin/dashboard'):
        logout_user()
        
        print("\n1. SIN SESIÓN:")
        print(f"   is_authenticated: {current_user.is_authenticated}")
        if not current_user.is_authenticated or not current_user.is_admin():
            print(f"   RESULTADO: Redirigir a auth.login")
        
        # Hacer login
        login_user(demo_user, remember=True)
        
        print("\n2. CON SESIÓN DE USUARIO DEMO:")
        print(f"   is_authenticated: {current_user.is_authenticated}")
        print(f"   role: '{current_user.role}'")
        print(f"   is_admin(): {current_user.is_admin()}")
        
        # Simular check_admin
        if app.config.get('DEMO_MODE'):
            print(f"   DEMO_MODE: True")
            if current_user.is_authenticated and current_user.role == 'admin':
                print(f"   [OK] RESULTADO: Permitir acceso a admin.dashboard")
            else:
                print(f"   [ERROR] RESULTADO: Redirigir a auth.login")
        else:
            if not current_user.is_authenticated or not current_user.is_admin():
                print(f"   [ERROR] RESULTADO: Redirigir a auth.login")
    
    print("\n" + "=" * 80)
    print("[OK] DEBUG COMPLETADO")
    print("=" * 80)
