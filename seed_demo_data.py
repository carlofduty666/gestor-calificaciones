#!/usr/bin/env python
"""
Script para popular la base de datos con datos de demostración.
Ejecutar con: python seed_demo_data.py
"""

import os
import sys
from datetime import datetime, date, timedelta
from app import create_app, db
from app.models.users import User
from app.models.academic import AcademicYear, Period, Grade, Section, Subject, Student, Teacher, TeacherAssignment, Admin
from app.models.grades import GradeType, StudentGrade, FinalGrade

app = create_app()

def seed_database():
    with app.app_context():
        print("🌱 Limpiando datos existentes...")
        # Comentar si quieres preservar datos
        # db.drop_all()
        
        print("📝 Creando datos de demostración...")
        
        # 1. Crear años académicos
        print("  → Creando años académicos...")
        year_2024 = AcademicYear(
            name='2024-2025',
            start_date=date(2024, 1, 15),
            end_date=date(2024, 12, 20),
            is_active=True
        )
        db.session.add(year_2024)
        db.session.commit()

        # 2. Crear períodos
        print("  → Creando períodos...")
        period_1 = Period(
            name='Primer Trimestre',
            start_date=date(2024, 1, 15),
            end_date=date(2024, 4, 15),
            academic_year_id=year_2024.id
        )
        period_2 = Period(
            name='Segundo Trimestre',
            start_date=date(2024, 4, 16),
            end_date=date(2024, 8, 15),
            academic_year_id=year_2024.id
        )
        period_3 = Period(
            name='Tercer Trimestre',
            start_date=date(2024, 8, 16),
            end_date=date(2024, 12, 20),
            academic_year_id=year_2024.id
        )
        db.session.add_all([period_1, period_2, period_3])
        db.session.commit()

        # 3. Crear grados
        print("  → Creando grados...")
        grades_data = [
            ('6to Grado', 'Primaria'),
            ('7mo Grado', 'Secundaria'),
            ('8vo Grado', 'Secundaria'),
            ('9no Grado', 'Secundaria'),
        ]
        grades = []
        for name, level in grades_data:
            grade = Grade(name=name, level=level, description=f'Grado {name}')
            grades.append(grade)
            db.session.add(grade)
        db.session.commit()

        # 4. Crear secciones
        print("  → Creando secciones...")
        sections = []
        for grade in grades:
            for section_name in ['A', 'B', 'C']:
                section = Section(
                    name=section_name,
                    grade_id=grade.id,
                    capacity=30
                )
                sections.append(section)
                db.session.add(section)
        db.session.commit()

        # 5. Crear asignaturas
        print("  → Creando asignaturas...")
        subjects_data = [
            ('Matemática', 'MAT101'),
            ('Español', 'ESP101'),
            ('Ciencias', 'CIE101'),
            ('Historia', 'HIS101'),
            ('Educación Física', 'EDF101'),
            ('Inglés', 'ING101'),
        ]
        subjects = []
        for name, code in subjects_data:
            subject = Subject(name=name, code=code)
            subjects.append(subject)
            db.session.add(subject)
        db.session.commit()

        # 6. Crear usuarios profesores
        print("  → Creando usuarios profesores...")
        teacher_users = []
        teacher_names = [
            ('Pedro', 'Martínez'),
            ('Laura', 'Fernández'),
            ('Carlos', 'López'),
            ('María', 'González'),
        ]
        for i, (first, last) in enumerate(teacher_names):
            user = User(
                email=f'profesor{i+1}@example.com',
                username=f'profesor{i+1}',
                first_name=first,
                last_name=last,
                role='teacher',
                is_active=True,
                is_registered=True
            )
            user.set_password('teacher123')
            teacher_users.append(user)
            db.session.add(user)
        db.session.commit()

        # 7. Crear profesores
        print("  → Creando profesores...")
        teachers = []
        for i, user in enumerate(teacher_users):
            teacher = Teacher(
                user_id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                employee_id=f'DOC{i+1:03d}',
                identification_number=f'{12345678 + i}',
                is_active=True
            )
            teachers.append(teacher)
            db.session.add(teacher)
        db.session.commit()

        # 8. Crear estudiantes
        print("  → Creando estudiantes...")
        student_names = [
            ('Juan', 'Pérez'), ('María', 'García'), ('Carlos', 'Rodríguez'),
            ('Ana', 'López'), ('Luis', 'Martínez'), ('Sofia', 'Fernández'),
            ('Diego', 'Ruiz'), ('Valentina', 'Sánchez'), ('Miguel', 'Torres'),
            ('Isabella', 'Rivera'), ('Santiago', 'Morales'), ('Camila', 'Vargas'),
        ]
        students = []
        for section in sections[:3]:  # Solo primeras 3 secciones
            for i, (first, last) in enumerate(student_names):
                student = Student(
                    first_name=first,
                    last_name=last,
                    student_id=f'EST{section.id}{i+1:03d}',
                    birth_date=date(2008, 5, 15) + timedelta(days=i*20),
                    email=f'{first.lower()}.{last.lower()}@example.com',
                    section_id=section.id,
                    is_active=True
                )
                students.append(student)
                db.session.add(student)
        db.session.commit()

        # 9. Crear asignaciones de profesores
        print("  → Creando asignaciones profesor-materia...")
        assignment_id = 0
        for teacher in teachers[:2]:  # Primeros 2 profesores
            for subject in subjects[:3]:  # Primeras 3 materias
                for section in sections[:2]:  # Primeras 2 secciones
                    assignment = TeacherAssignment(
                        teacher_id=teacher.id,
                        subject_id=subject.id,
                        section_id=section.id,
                        academic_year_id=year_2024.id
                    )
                    db.session.add(assignment)
                    assignment_id += 1
        db.session.commit()

        # 10. Crear tipos de calificación
        print("  → Creando tipos de calificación...")
        grade_types = []
        for period in [period_1, period_2]:
            for i, subject in enumerate(subjects[:3]):
                gt = GradeType(
                    name=f'Participación',
                    weight=0.2,
                    subject_id=subject.id,
                    period_id=period.id,
                    teacher_id=teachers[0].id,
                    section_id=sections[0].id
                )
                grade_types.append(gt)
                db.session.add(gt)
                
                gt2 = GradeType(
                    name=f'Evaluación',
                    weight=0.8,
                    subject_id=subject.id,
                    period_id=period.id,
                    teacher_id=teachers[0].id,
                    section_id=sections[0].id
                )
                grade_types.append(gt2)
                db.session.add(gt2)
        db.session.commit()

        # 11. Crear calificaciones de estudiantes
        print("  → Creando calificaciones de estudiantes...")
        for student in students[:10]:  # Primeros 10 estudiantes
            for subject in subjects[:3]:
                for gt in grade_types[:6]:
                    if gt.subject_id == subject.id:
                        sg = StudentGrade(
                            student_id=student.id,
                            subject_id=subject.id,
                            grade_type_id=gt.id,
                            period_id=gt.period_id,
                            teacher_id=gt.teacher_id,
                            value=round(15 + (student.id + subject.id) % 5, 1),
                            comments='Desempeño regular'
                        )
                        db.session.add(sg)
        db.session.commit()

        # 12. Crear calificaciones finales
        print("  → Creando calificaciones finales...")
        for student in students[:10]:
            for subject in subjects[:3]:
                fg = FinalGrade(
                    student_id=student.id,
                    subject_id=subject.id,
                    period_id=period_1.id,
                    value=round(15 + (student.id + subject.id) % 4 + 0.5, 1),
                    comments='Promedio ponderado'
                )
                db.session.add(fg)
        db.session.commit()

        print("✅ ¡Base de datos poblada exitosamente!")
        print(f"  📊 {len(grades)} Grados")
        print(f"  📚 {len(sections)} Secciones")
        print(f"  👨‍🏫 {len(teachers)} Profesores")
        print(f"  👨‍🎓 {len(students)} Estudiantes")
        print(f"  📝 {len(subjects)} Asignaturas")

if __name__ == '__main__':
    seed_database()
