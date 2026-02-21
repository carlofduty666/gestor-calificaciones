#!/usr/bin/env python
"""
Script para asegurar que el usuario demo tiene permisos de admin
"""
from app import create_app, db
from app.models.users import User

app = create_app()

def fix_demo_admin():
    with app.app_context():
        print("🔍 Verificando usuario demo...")
        
        # Buscar usuario demo
        demo_user = User.query.filter_by(email='demo@example.com').first()
        
        if not demo_user:
            print("❌ Usuario demo NO existe. Creándolo...")
            demo_user = User(
                identification_number='99999999',
                email='demo@example.com',
                username='demo',
                first_name='Demo',
                last_name='Admin',
                role='admin',  # IMPORTANTE: debe ser 'admin'
                is_active=True,
                is_registered=True
            )
            demo_user.set_password('demo123')
            db.session.add(demo_user)
            db.session.commit()
            print("✅ Usuario demo creado exitosamente")
            print(f"   Email: demo@example.com")
            print(f"   Rol: admin")
        else:
            print(f"✅ Usuario demo existe: {demo_user.email}")
            print(f"   Rol actual: {demo_user.role}")
            print(f"   Activo: {demo_user.is_active}")
            
            # Si el rol no es 'admin', corregirlo
            if demo_user.role != 'admin':
                print("⚠️  Cambiando rol a 'admin'...")
                demo_user.role = 'admin'
                db.session.commit()
                print("✅ Rol cambiado a 'admin'")
            else:
                print("✓ El rol ya es 'admin'")

if __name__ == '__main__':
    fix_demo_admin()
