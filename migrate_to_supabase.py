"""
Script para migrar datos de SQLite local a Supabase PostgreSQL
Uso interactivo: python migrate_to_supabase.py
"""

import os
import sys
from urllib.parse import urlparse, quote
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Importar la app y modelos
from app import create_app, db
from app.models.users import User
from app.models.academic import Teacher, Admin, AcademicYear, Period, Grade, Section, Student
from app.models.grades import GradeType, StudentGrade, FinalGrade
from app.models.templates import ExcelTemplate, TemplateCell, TemplateStyle, TemplateRange

def parse_and_validate_url(url_string):
    """Valida y parsea una URL de conexión a PostgreSQL"""
    try:
        parsed = urlparse(url_string)
        
        if parsed.scheme != 'postgresql':
            print(f"❌ ERROR: Esquema no válido '{parsed.scheme}'")
            print("   Esperado: postgresql://user:password@host:port/database")
            return None
        
        if not parsed.hostname or not parsed.username or not parsed.password:
            print("❌ ERROR: URL incompleta. Necesita: usuario, contraseña y host")
            return None
        
        return {
            'username': parsed.username,
            'password': parsed.password,
            'hostname': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/') or 'postgres',
            'original_url': url_string
        }
    except Exception as e:
        print(f"❌ ERROR al parsear URL: {e}")
        return None

def build_connection_string(url_info):
    """Reconstruye una conexión segura desde componentes parseados"""
    try:
        # Escapar caracteres especiales en la contraseña
        safe_password = quote(url_info['password'], safe='')
        
        # Construir URL limpia
        clean_url = (
            f"postgresql://{url_info['username']}:{safe_password}@"
            f"{url_info['hostname']}:{url_info['port']}/{url_info['database']}"
        )
        return clean_url
    except Exception as e:
        print(f"❌ ERROR al construir URL: {e}")
        return None

def test_connection(url, db_type="remote"):
    """Prueba la conexión a la base de datos con soporte SSL"""
    try:
        if db_type == 'remote':
            # Configurar SSL para proveedores cloud
            connect_args = {"connect_timeout": 10}
            if any(cloud in url for cloud in ["rlwy.net", "neon.tech", "supabase.co"]):
                connect_args["sslmode"] = "require"
            
            engine = create_engine(
                url,
                echo=False,
                poolclass=NullPool,
                connect_args=connect_args
            )
        else:
            engine = create_engine(url, echo=False)
        
        with engine.connect() as conn:
            if db_type == 'remote':
                result = conn.execute(text("SELECT version()")).scalar()
                version_info = result.split(',')[0].strip()
                print(f"  ✓ Conectado: {version_info}")
            else:
                result = conn.execute(text("SELECT sqlite_version()")).scalar()
                print(f"  ✓ Conectado: SQLite {result}")
        
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:80]}...")
        return False
    
def get_supabase_url():
    """Obtiene la URL de Supabase del usuario"""
    print("\n" + "="*70)
    print(" 🔐 OBTENER URL DE CONEXIÓN DE SUPABASE")
    print("="*70)
    
    print("\n📍 Pasos para obtener tu URL:")
    print("   1. Ve a https://app.supabase.com/projects")
    print("   2. Selecciona tu proyecto 'gestor-calificaciones'")
    print("   3. Ve a: Settings → Database")
    print("   4. Ve a: Connection Strings → URI")
    print("   5. Copia la URL (empieza con 'postgresql://')")
    print("   6. Pégala aquí")
    
    url = input("\n📌 Pega tu URL de Supabase: ").strip()
    
    if not url:
        print("❌ ERROR: URL vacía")
        return None
    
    if not url.startswith('postgresql://'):
        print("❌ ERROR: No parece una URL válida (no empieza con 'postgresql://')")
        return None
    
    return url

def migrate_data(source_db_url, target_db_url):
    """Migra datos de SQLite a PostgreSQL con configuración robusta"""
    
    # 1. Limpieza de la URL para SQLAlchemy
    # Algunos proveedores requieren que el protocolo sea postgresql+psycopg2
    if target_db_url.startswith("postgresql://"):
        target_db_url = target_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    print("\n" + "="*70)
    print(" 🔄 MIGRACIÓN DE DATOS: SQLite → Cloud PostgreSQL")
    print("="*70)
    
    try:
        print("\n📡 Conectando a bases de datos...")
        
        # Conexión SQLite
        local_engine = create_engine('sqlite:///instance/app.db', echo=False)
        
        # Conexión remota con parámetros de compatibilidad total
        # Agregamos sslmode=require directamente en la URL si no está
        if "sslmode" not in target_db_url:
            connector = "&" if "?" in target_db_url else "?"
            target_db_url += f"{connector}sslmode=require"

        remote_engine = create_engine(
            target_db_url,
            echo=False,
            poolclass=NullPool,
            connect_args={
                "connect_timeout": 30,
                "sslmode": "require",
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5
            }
        )
        
        # Probar conexión manualmente antes de seguir
        with remote_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("  🔒 Conexión Segura Establecida con Railway")

    except Exception as e:
        print(f"  ❌ Error de Conexión: {e}")
        return False
    
    # Resto del proceso de migración...
    LocalSession = sessionmaker(bind=local_engine)
    RemoteSession = sessionmaker(bind=remote_engine)
    
    local_session = LocalSession()
    remote_session = RemoteSession()
    
    try:
        print("\n📋 Creando esquema en el destino...")
        with remote_engine.begin() as conn:
            db.metadata.create_all(bind=conn)
        print("  ✓ Tablas creadas/verificadas")
        
        models_to_migrate = [
            (User, "Usuarios"), (Admin, "Administradores"), (Teacher, "Profesores"),
            (AcademicYear, "Años Académicos"), (Period, "Períodos"), (Grade, "Grados"),
            (Section, "Secciones"), (Student, "Estudiantes"), (GradeType, "Tipos de Calificación"),
            (StudentGrade, "Calificaciones de Estudiantes"), (FinalGrade, "Calificaciones Finales"),
            (ExcelTemplate, "Plantillas Excel"), (TemplateCell, "Celdas de Plantilla"),
            (TemplateStyle, "Estilos de Plantilla"), (TemplateRange, "Rangos de Plantilla"),
        ]
        
        total_records = 0
        migrated_tables = []
        
        print("\n" + "─"*70)
        print(" Migrando datos por tabla...")
        print("─"*70)
        
        for model, display_name in models_to_migrate:
            try:
                count = local_session.query(model).count()
                if count == 0:
                    print(f" ⊘ {display_name:.<45} (sin datos)")
                    continue
                
                print(f" 🔄 {display_name:.<45} ", end='', flush=True)
                records = local_session.query(model).all()
                
                for record in records:
                    remote_session.merge(record)
                
                remote_session.commit()
                print(f"✓ ({count})")
                total_records += count
                migrated_tables.append((display_name, count))
            except Exception as e:
                print(f"❌ ERROR en {display_name}: {str(e)[:40]}")
                remote_session.rollback()
                continue # Intentar con la siguiente tabla

        print("\n ✅ MIGRACIÓN FINALIZADA")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        return False
    finally:
        local_session.close()
        remote_session.close()
        local_engine.dispose()
        remote_engine.dispose()

def main():
    """Punto de entrada principal"""
    
    print("\n" + "="*70)
    print(" 🚀 MIGRADOR DE DATOS: SQLite → Supabase")
    print("="*70)
    
    # Verificar que estamos en desarrollo
    if os.getenv('FLASK_ENV') == 'production':
        print("❌ ERROR: No ejecutar en producción")
        sys.exit(1)
    
    # Verificar que la base de datos local existe
    if not os.path.exists('instance/app.db'):
        print("❌ ERROR: Base de datos local no encontrada")
        print("   Ejecuta primero: python seed_demo_data.py")
        sys.exit(1)
    
    # Obtener URL de Supabase
    target_db_url = get_supabase_url()
    if not target_db_url:
        sys.exit(1)
    
    # Parsear y validar URL
    print("\n✓ Validando URL...")
    url_info = parse_and_validate_url(target_db_url)
    if not url_info:
        sys.exit(1)
    
    # Construir URL segura (escapar caracteres especiales)
    print("✓ Preparando conexión...")
    clean_url = build_connection_string(url_info)
    if not clean_url:
        sys.exit(1)
    
    # Ejecutar migración
    source_db_url = 'sqlite:///instance/app.db'
    success = migrate_data(source_db_url, clean_url)
    
    if success:
        print("\n✨ Siguiente paso: Actualizar DATABASE_URL en Render")
        print("   Settings → Environment Variables → DATABASE_URL")
        print(f"   Valor: (tu URL de Supabase sin caracteres escapados)")
        sys.exit(0)
    else:
        print("\n⚠ La migración falló. Revisa los errores arriba.")
        sys.exit(1)

if __name__ == '__main__':
    main()
