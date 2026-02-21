#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para crear datos demo realistas que imiten la estructura de tus modelos.
Ejecutar: python seed_demo_data.py

Este script crea:
- 1 año académico (2026)
- 3 períodos
- 2 grados (10mo y 11vo)
- 3 secciones por grado (A, B, C)
- 6 materias
- 6 profesores
- 30 estudiantes por sección
- Calificaciones de ejemplo

Los datos son realistas e idempotentes (no fallan si ya existen).
"""

import os
import sys
from datetime import datetime, date, timedelta
from random import randint, choice, random

def create_seed_data():
    """Crea datos demo realistas"""
    
    print("="*100)
    print("  GENERADOR DE DATOS DEMO - Imitando estructura real")
    print("="*100)
    
    try:
        # Configurar entorno
        os.environ['FLASK_APP'] = 'run.py'
        
        # Importar modelos
        from app import create_app, db
        from app.models.users import User
        from app.models.academic import (
            AcademicYear, Period, Grade, Section, Subject, 
            Student, Teacher, TeacherAssignment, Admin
        )
        from app.models.grades import GradeType, StudentGrade, FinalGrade
        
        # Crear app
        app = create_app()
        
        with app.app_context():
            print("\n[PASO 1] Verificando base de datos...")
            db.create_all()
            print("[✓] Base de datos lista")
            
            # 1. Crear año académico (solo si no existe)
            print("\n[PASO 2] Creando año académico...")
            academic_year = AcademicYear.query.filter_by(name='2026').first()
            if not academic_year:
                academic_year = AcademicYear(
                    name='2026',
                    start_date=date(2026, 1, 10),
                    end_date=date(2026, 12, 20),
                    is_active=True
                )
                db.session.add(academic_year)
                db.session.commit()
                print("  [✓] Año académico 2026 creado")
            else:
                print("  [!] Año académico 2026 ya existe")
            
            # 2. Crear períodos
            print("\n[PASO 3] Creando períodos...")
            periods_data = [
                ('1er Trimestre', date(2026, 1, 10), date(2026, 4, 10)),
                ('2do Trimestre', date(2026, 4, 15), date(2026, 8, 10)),
                ('3er Trimestre', date(2026, 8, 15), date(2026, 12, 20)),
            ]
            periods = []
            for name, start, end in periods_data:
                period = Period.query.filter_by(name=name, academic_year_id=academic_year.id).first()
                if not period:
                    period = Period(
                        name=name,
                        start_date=start,
                        end_date=end,
                        academic_year_id=academic_year.id
                    )
                    db.session.add(period)
                    periods.append(period)
                    print(f"  [✓] Período '{name}' creado")
                else:
                    periods.append(period)
                    print(f"  [!] Período '{name}' ya existe")
            db.session.commit()
            
            # 3. Crear grados
            print("\n[PASO 4] Creando grados...")
            grades_data = [
                ('Décimo', 'Décimo grado'),
                ('Undécimo', 'Undécimo grado'),
            ]
            grades = []
            for name, level in grades_data:
                grade = Grade.query.filter_by(name=name).first()
                if not grade:
                    grade = Grade(name=name, level=level)
                    db.session.add(grade)
                    grades.append(grade)
                    print(f"  [✓] Grado '{name}' creado")
                else:
                    grades.append(grade)
                    print(f"  [!] Grado '{name}' ya existe")
            db.session.commit()
            
            # 4. Crear secciones
            print("\n[PASO 5] Creando secciones...")
            sections = []
            section_letters = ['A', 'B', 'C']
            for grade in grades:
                for letter in section_letters:
                    section = Section.query.filter_by(name=letter, grade_id=grade.id).first()
                    if not section:
                        section = Section(
                            name=letter,
                            grade_id=grade.id,
                            capacity=35
                        )
                        db.session.add(section)
                        sections.append(section)
                        print(f"  [✓] Sección {grade.name}-{letter} creada")
                    else:
                        sections.append(section)
                        print(f"  [!] Sección {grade.name}-{letter} ya existe")
            db.session.commit()
            
            # 5. Crear materias
            print("\n[PASO 6] Creando materias...")
            subjects_data = [
                ('Matemáticas', 'MAT101'),
                ('Historia', 'HIS101'),
                ('Lengua Española', 'LEN101'),
                ('Biología', 'BIO101'),
                ('Física', 'FIS101'),
                ('Educación Física', 'EF101'),
            ]
            subjects = []
            for name, code in subjects_data:
                subject = Subject.query.filter_by(code=code).first()
                if not subject:
                    subject = Subject(name=name, code=code)
                    db.session.add(subject)
                    subjects.append(subject)
                    print(f"  [✓] Materia '{name}' creada")
                else:
                    subjects.append(subject)
                    print(f"  [!] Materia '{name}' ya existe")
            db.session.commit()
            
            # 6. Crear profesores
            print("\n[PASO 7] Creando profesores...")
            teachers_data = [
                ('Juan', 'García', 'juan.garcia@school.com', 'JC001', 'Matemáticas'),
                ('María', 'López', 'maria.lopez@school.com', 'ML002', 'Historia'),
                ('Carlos', 'Rodríguez', 'carlos.rodriguez@school.com', 'CR003', 'Lengua'),
                ('Ana', 'Martínez', 'ana.martinez@school.com', 'AM004', 'Biología'),
                ('Pedro', 'Sánchez', 'pedro.sanchez@school.com', 'PS005', 'Física'),
                ('Laura', 'Díaz', 'laura.diaz@school.com', 'LD006', 'Educación Física'),
            ]
            teachers = []
            for first_name, last_name, email, emp_id, spec in teachers_data:
                user = User.query.filter_by(email=email).first()
                if not user:
                    user = User(
                        identification_number=emp_id,
                        email=email,
                        username=email.split('@')[0],
                        first_name=first_name,
                        last_name=last_name,
                        role='teacher',
                        is_active=True,
                        is_registered=True
                    )
                    user.set_password('profesor123')
                    db.session.add(user)
                    db.session.commit()
                
                teacher = Teacher.query.filter_by(user_id=user.id).first()
                if not teacher:
                    teacher = Teacher(
                        user_id=user.id,
                        first_name=first_name,
                        last_name=last_name,
                        employee_id=emp_id,
                        specialization=spec,
                        identification_number=emp_id,
                        is_active=True,
                        hire_date=date(2020, 1, 1)
                    )
                    db.session.add(teacher)
                    teachers.append(teacher)
                    print(f"  [✓] Profesor '{first_name} {last_name}' creado")
                else:
                    teachers.append(teacher)
                    print(f"  [!] Profesor '{first_name} {last_name}' ya existe")
            db.session.commit()
            
            # 7. Crear estudiantes
            print("\n[PASO 8] Creando estudiantes...")
            first_names = ['Juan', 'María', 'Carlos', 'Ana', 'Pedro', 'Laura', 'Diego', 'Sofia', 'Luis', 'Elena']
            last_names = ['García', 'López', 'Rodríguez', 'Martínez', 'Sánchez', 'Díaz', 'Pérez', 'Torres', 'Morales', 'Flores']
            
            total_students = 0
            for section in sections:
                existing_count = Student.query.filter_by(section_id=section.id).count()
                if existing_count == 0:
                    # Crear 30 estudiantes por sección
                    for i in range(30):
                        first_name = choice(first_names)
                        last_name = choice(last_names)
                        student = Student(
                            first_name=first_name,
                            last_name=last_name,
                            student_id=f"{section.grade.name[:1]}{section.name}{str(i+1).zfill(3)}",
                            birth_date=date(2007 if section.grade.name == 'Décimo' else 2006, randint(1,12), randint(1,28)),
                            gender=choice(['M', 'F']),
                            address=f"Calle {randint(1,100)} #{randint(1,999)}",
                            phone=f"809-{randint(100,999)}-{randint(1000,9999)}",
                            email=f"{first_name.lower()}.{last_name.lower()}@student.school.com",
                            section_id=section.id,
                            is_active=True
                        )
                        db.session.add(student)
                        total_students += 1
                    db.session.commit()
                    print(f"  [✓] 30 estudiantes creados en sección {section.grade.name}-{section.name}")
                else:
                    print(f"  [!] Sección {section.grade.name}-{section.name} ya tiene estudiantes")
            
            # 8. Crear asignaciones de profesores
            print("\n[PASO 9] Asignando profesores a secciones...")
            assignment_count = 0
            for section in sections:
                for subject in subjects:
                    existing = TeacherAssignment.query.filter_by(
                        section_id=section.id,
                        subject_id=subject.id,
                        academic_year_id=academic_year.id
                    ).first()
                    if not existing:
                        teacher = choice(teachers)
                        assignment = TeacherAssignment(
                            teacher_id=teacher.id,
                            subject_id=subject.id,
                            section_id=section.id,
                            academic_year_id=academic_year.id
                        )
                        db.session.add(assignment)
                        assignment_count += 1
            db.session.commit()
            print(f"  [✓] {assignment_count} asignaciones de profesores completadas")
            
            # 9. Crear tipos de calificación
            print("\n[PASO 10] Creando tipos de calificación...")
            grade_types_data = ['Examen', 'Tarea', 'Quiz', 'Participación']
            grade_type_count = 0
            
            for period in periods:
                for section in sections:
                    for subject in subjects:
                        teacher_assignment = TeacherAssignment.query.filter_by(
                            section_id=section.id,
                            subject_id=subject.id,
                            academic_year_id=academic_year.id
                        ).first()
                        
                        if teacher_assignment:
                            for grade_type_name in grade_types_data:
                                existing = GradeType.query.filter_by(
                                    name=grade_type_name,
                                    subject_id=subject.id,
                                    period_id=period.id,
                                    teacher_id=teacher_assignment.teacher_id,
                                    section_id=section.id
                                ).first()
                                
                                if not existing:
                                    weight = 0.4 if grade_type_name == 'Examen' else (0.3 if grade_type_name == 'Tarea' else 0.15)
                                    grade_type = GradeType(
                                        name=grade_type_name,
                                        weight=weight,
                                        subject_id=subject.id,
                                        period_id=period.id,
                                        teacher_id=teacher_assignment.teacher_id,
                                        section_id=section.id
                                    )
                                    db.session.add(grade_type)
                                    grade_type_count += 1
            db.session.commit()
            print(f"  [✓] {grade_type_count} tipos de calificación creados")
            
            # 10. Crear calificaciones de estudiantes
            print("\n[PASO 11] Creando calificaciones de estudiantes...")
            total_grades = 0
            for period in periods:
                for student in Student.query.all():
                    for subject in subjects:
                        # Obtener asignación de profesor
                        teacher_assignment = TeacherAssignment.query.filter_by(
                            section_id=student.section_id,
                            subject_id=subject.id,
                            academic_year_id=academic_year.id
                        ).first()
                        
                        if teacher_assignment:
                            # Obtener tipos de calificación
                            grade_types = GradeType.query.filter_by(
                                subject_id=subject.id,
                                period_id=period.id,
                                teacher_id=teacher_assignment.teacher_id,
                                section_id=student.section_id
                            ).all()
                            
                            for gt in grade_types:
                                existing = StudentGrade.query.filter_by(
                                    student_id=student.id,
                                    subject_id=subject.id,
                                    grade_type_id=gt.id,
                                    period_id=period.id
                                ).first()
                                
                                if not existing:
                                    # Generar calificación realista (60-100)
                                    value = round(60 + random() * 40, 2)
                                    student_grade = StudentGrade(
                                        student_id=student.id,
                                        subject_id=subject.id,
                                        grade_type_id=gt.id,
                                        period_id=period.id,
                                        teacher_id=teacher_assignment.teacher_id,
                                        value=value,
                                        comments=None
                                    )
                                    db.session.add(student_grade)
                                    total_grades += 1
            db.session.commit()
            print(f"  [✓] {total_grades} calificaciones de estudiantes creadas")
            
            # 11. Crear calificaciones finales
            print("\n[PASO 12] Creando calificaciones finales...")
            total_final_grades = 0
            for period in periods:
                for student in Student.query.all():
                    for subject in subjects:
                        existing = FinalGrade.query.filter_by(
                            student_id=student.id,
                            subject_id=subject.id,
                            period_id=period.id
                        ).first()
                        
                        if not existing:
                            # Calcular promedio de calificaciones del estudiante
                            student_grades = StudentGrade.query.filter_by(
                                student_id=student.id,
                                subject_id=subject.id,
                                period_id=period.id
                            ).all()
                            
                            if student_grades:
                                avg = sum(sg.value for sg in student_grades) / len(student_grades)
                            else:
                                avg = round(60 + random() * 40, 2)
                            
                            final_grade = FinalGrade(
                                student_id=student.id,
                                subject_id=subject.id,
                                period_id=period.id,
                                value=round(avg, 2)
                            )
                            db.session.add(final_grade)
                            total_final_grades += 1
            db.session.commit()
            print(f"  [✓] {total_final_grades} calificaciones finales creadas")
            
            # Resumen final
            print("\n" + "="*100)
            print("  ✅ DATOS DEMO CREADOS EXITOSAMENTE")
            print("="*100)
            print(f"""
Resumen de datos creados:
  • Años académicos: 1 (2026)
  • Períodos: 3
  • Grados: 2
  • Secciones: 6
  • Materias: 6
  • Profesores: 6
  • Estudiantes: {Student.query.count()}
  • Tipos de calificación: {GradeType.query.count()}
  • Calificaciones de estudiantes: {StudentGrade.query.count()}
  • Calificaciones finales: {FinalGrade.query.count()}

Ahora puedes:
  1. Ejecutar el servidor: python run.py
  2. Ir a http://127.0.0.1:5000/
  3. Ver el dashboard con datos reales
            """)
            
    except Exception as e:
        print(f"\n[✗] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(create_seed_data())
