#!/usr/bin/env python
"""
Script para asegurar que el usuario demo existe
Ejecutar DESPUÉS de: flask db upgrade
"""
from app import create_app, db
from app.models.users import User

app = create_app()

with app.app_context():
    # Verificar si ya existe
    demo_user = User.query.filter_by(email='demo@example.com').first()
    
    if not demo_user:
        print("Creando usuario demo...")
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
        print("✅ Usuario demo creado")
    else:
        print(f"✅ Usuario demo ya existe: {demo_user.email}")
        if demo_user.role != 'admin':
            demo_user.role = 'admin'
            db.session.commit()
            print("   Rol actualizado a admin")
