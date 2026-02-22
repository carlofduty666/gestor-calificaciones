import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Importar tus modelos
from app import create_app, db
from app.models.users import User
from app.models.academic import Teacher, Admin, AcademicYear, Period, Grade, Section, Student
from app.models.grades import GradeType, StudentGrade, FinalGrade
from app.models.templates import ExcelTemplate, TemplateCell, TemplateStyle, TemplateRange

def internal_migration():
    # 1. Configurar la URL de Railway (Interna)
    target_url = os.getenv("DATABASE_URL")
    if not target_url:
        print("❌ ERROR: No se encontró DATABASE_URL. ¿Estás ejecutando esto en Railway?")
        return

    # Corregir prefijo si es necesario
    if target_url.startswith("postgres://"):
        target_url = target_url.replace("postgres://", "postgresql://", 1)

    print(f"🚀 Iniciando migración interna...")
    
    # 2. Motores de base de datos
    source_engine = create_engine('sqlite:///instance/app.db')
    target_engine = create_engine(target_url)

    # 3. Sesiones
    SourceSession = sessionmaker(bind=source_engine)
    TargetSession = sessionmaker(bind=target_engine)
    source_session = SourceSession()
    target_session = TargetSession()

    try:
        # Crear tablas en Postgres
        print("📋 Verificando tablas en PostgreSQL...")
        db.metadata.create_all(bind=target_engine)

        models = [
            (User, "Usuarios"), (Admin, "Administradores"), (Teacher, "Profesores"),
            (AcademicYear, "Años Académicos"), (Period, "Períodos"), (Grade, "Grados"),
            (Section, "Secciones"), (Student, "Estudiantes"), (GradeType, "Tipos"),
            (StudentGrade, "Notas"), (FinalGrade, "Notas Finales"),
            (ExcelTemplate, "Plantillas"), (TemplateCell, "Celdas"),
            (TemplateStyle, "Estilos"), (TemplateRange, "Rangos")
        ]

        for model, name in models:
            count = source_session.query(model).count()
            if count > 0:
                print(f" 🔄 Migrando {name} ({count} registros)...")
                records = source_session.query(model).all()
                for record in records:
                    target_session.merge(record)
                target_session.commit()
                print(f"  ✓ {name} completado.")
            else:
                print(f" ⊘ {name} sin datos.")

        print("\n✅ MIGRACIÓN INTERNA EXITOSA")

    except Exception as e:
        print(f"❌ ERROR DURANTE LA MIGRACIÓN: {e}")
        target_session.rollback()
    finally:
        source_session.close()
        target_session.close()

if __name__ == "__main__":
    internal_migration()