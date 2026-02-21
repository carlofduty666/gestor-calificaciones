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
    """Prueba la conexión a la base de datos"""
    try:
        if db_type == 'remote':
            engine = create_engine(
                url,
                echo=False,
                poolclass=NullPool,
                connect_args={"connect_timeout": 10}
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
    """Migra datos de SQLite a PostgreSQL"""
    
    print("\n" + "="*70)
    print(" 🔄 MIGRACIÓN DE DATOS: SQLite → Supabase PostgreSQL")
    print("="*70)
    
    # Crear engines
    print("\n📡 Conectando a bases de datos...")
    
    try:
        print("  Conectando a SQLite local...")
        local_engine = create_engine('sqlite:///instance/app.db', echo=False)
        if not test_connection('sqlite:///instance/app.db', 'local'):
            return False
    except Exception as e:
        print(f"  ❌ Error con SQLite: {e}")
        return False
    
    try:
        print("  Conectando a Supabase PostgreSQL...")
        if not test_connection(target_db_url, 'remote'):
            print("\n⚠  Consejo: Verifica que tu URL sea exacta")
            print("  Algunos caracteres especiales en la contraseña deben escaparse")
            return False
        
        remote_engine = create_engine(
            target_db_url,
            echo=False,
            poolclass=NullPool,
            connect_args={"connect_timeout": 10}
        )
    except Exception as e:
        print(f"  ❌ Error con Supabase: {e}")
        return False
    
    # Crear sesiones
    LocalSession = sessionmaker(bind=local_engine)
    RemoteSession = sessionmaker(bind=remote_engine)
    
    local_session = LocalSession()
    remote_session = RemoteSession()
    
    try:
        # Crear tablas en Supabase
        print("\n📋 Creando esquema en Supabase...")
        try:
            with remote_engine.begin() as conn:
                db.metadata.create_all(bind=conn)
            print("  ✓ Tablas creadas/verificadas")
        except Exception as e:
            print(f"  ⚠ Aviso: {e}")
        
        # Modelos a migrar (en orden de dependencias)
        models_to_migrate = [
            (User, "Usuarios"),
            (Admin, "Administradores"),
            (Teacher, "Profesores"),
            (AcademicYear, "Años Académicos"),
            (Period, "Períodos"),
            (Grade, "Grados"),
            (Section, "Secciones"),
            (Student, "Estudiantes"),
            (GradeType, "Tipos de Calificación"),
            (StudentGrade, "Calificaciones de Estudiantes"),
            (FinalGrade, "Calificaciones Finales"),
            (ExcelTemplate, "Plantillas Excel"),
            (TemplateCell, "Celdas de Plantilla"),
            (TemplateStyle, "Estilos de Plantilla"),
            (TemplateRange, "Rangos de Plantilla"),
        ]
        
        total_records = 0
        migrated_tables = []
        
        print("\n" + "─"*70)
        print(" Migrando datos por tabla...")
        print("─"*70)
        
        for model, display_name in models_to_migrate:
            count = 0
            
            try:
                count = local_session.query(model).count()
            except:
                count = 0
            
            if count == 0:
                print(f" ⊘ {display_name:.<45} (sin datos)")
                continue
            
            print(f" 🔄 {display_name:.<45} ", end='', flush=True)
            
            try:
                # Obtener registros
                records = local_session.query(model).all()
                
                # Insertar en remoto
                for record in records:
                    remote_session.merge(record)
                
                # Commit
                remote_session.commit()
                
                print(f"✓ ({count})")
                total_records += count
                migrated_tables.append((display_name, count))
                
            except Exception as e:
                print(f"❌ ERROR: {str(e)[:40]}")
                remote_session.rollback()
                raise
        
        # Resumen
        print("\n" + "="*70)
        print(" ✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("="*70)
        print(f"\n 📊 Resumen:")
        for table_name, count in migrated_tables:
            print(f"    {table_name:.<45} {count:>4} registros")
        print(f"\n    {'TOTAL':.<45} {total_records:>4} registros")
        print("\n" + "="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        remote_session.rollback()
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
