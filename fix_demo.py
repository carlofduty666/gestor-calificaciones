#!/usr/bin/env python
"""
Script para diagnosticar y arreglar problemas en modo DEMO
Ejecutar en Render Shell con: python fix_demo.py
"""

import os
from app import create_app, db
from app.models.users import User

app = create_app()

def fix_demo():
    with app.app_context():
        print("🔍 Diagnosticando modo DEMO...")
        
        # 1. Verificar que DEMO_MODE está activado
        demo_mode = app.config.get('DEMO_MODE')
        print(f"✓ DEMO_MODE: {demo_mode}")
        
        if not demo_mode:
            print("⚠️  DEMO_MODE no está activado. Verifica la variable en Render.")
            return
        
        # 2. Verificar usuario demo
        demo_user = User.query.filter_by(email='demo@example.com').first()
        
        if demo_user:
            print(f"✓ Usuario demo existe: {demo_user.email}")
            print(f"  - ID: {demo_user.id}")
            print(f"  - Rol: {demo_user.role}")
            print(f"  - Registrado: {demo_user.is_registered}")
            print(f"  - Activo: {demo_user.is_active}")
        else:
            print("❌ Usuario demo NO existe. Creándolo...")
            
            # Crear usuario demo
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
            
            print(f"✓ Usuario demo creado exitosamente")
            print(f"  - Email: {demo_user.email}")
            print(f"  - Cédula: {demo_user.identification_number}")
            print(f"  - Contraseña: demo123")
        
        # 3. Verificar datos de demostración
        from app.models.academic import Student, Teacher, Subject
        
        students = Student.query.count()
        teachers = Teacher.query.count()
        subjects = Subject.query.count()
        
        print(f"\n📊 Datos en la base de datos:")
        print(f"  - Estudiantes: {students}")
        print(f"  - Profesores: {teachers}")
        print(f"  - Asignaturas: {subjects}")
        
        if students == 0 or teachers == 0:
            print("\n⚠️  Datos de demostración no encontrados.")
            print("Para poblar la BD, ejecuta en Render Shell:")
            print("  python seed_demo_data.py")
        else:
            print("\n✓ Datos de demostración encontrados")
        
        print("\n✅ Diagnóstico completado")
        print("\nPrueba accediendo a: https://tu-app.onrender.com")

if __name__ == '__main__':
    fix_demo()
