from app.models.academic import Student, Subject, Grade, Section, AcademicYear, Period
from app.models.grades import FinalGrade
from app.models.users import User
from app.services.excel_data_extractor import ExcelDataExtractor
from app import db
from sqlalchemy.exc import IntegrityError
import logging

class DataImportService:
    """Servicio para importar datos desde archivos Excel a la base de datos"""
    
    @staticmethod
    def import_students_and_grades(file_path, section_id, period_id, mapping_config=None):
        """
        Importa estudiantes y calificaciones desde un archivo Excel
        
        Args:
            file_path: Ruta del archivo Excel
            section_id: ID de la sección donde importar
            period_id: ID del período académico
            mapping_config: Configuración de mapeo de columnas (opcional)
        
        Returns:
            dict: Resultado de la importación con estadísticas
        """
        
        try:
            # Extraer datos del Excel
            extracted_data = ExcelDataExtractor.extract_students_and_grades(file_path)
            
            # Obtener sección y período
            section = Section.query.get_or_404(section_id)
            period = Period.query.get_or_404(period_id)
            
            result = {
                'success': True,
                'students_created': 0,
                'students_updated': 0,
                'subjects_created': 0,
                'grades_imported': 0,
                'errors': [],
                'warnings': []
            }
            
            # Importar materias primero
            subject_mapping = {}
            for subject_data in extracted_data['subjects']:
                subject = DataImportService._create_or_get_subject(subject_data)
                subject_mapping[subject_data['name']] = subject
                if subject:
                    result['subjects_created'] += 1
            
            # Importar estudiantes y calificaciones
            for student_data in extracted_data['students']:
                try:
                    # Crear o actualizar estudiante
                    student, created = DataImportService._create_or_update_student(
                        student_data, section
                    )
                    
                    if created:
                        result['students_created'] += 1
                    else:
                        result['students_updated'] += 1
                    
                    # Importar calificaciones del estudiante
                    grades_imported = DataImportService._import_student_grades(
                        student, student_data['grades'], subject_mapping, period
                    )
                    
                    result['grades_imported'] += grades_imported
                    
                except Exception as e:
                    error_msg = f"Error con estudiante {student_data.get('student_id', 'N/A')}: {str(e)}"
                    result['errors'].append(error_msg)
                    logging.error(error_msg)
            
            db.session.commit()
            return result
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'students_created': 0,
                'students_updated': 0,
                'subjects_created': 0,
                'grades_imported': 0,
                'errors': [str(e)],
                'warnings': []
            }
    
    @staticmethod
    def _create_or_get_subject(subject_data):
        """Crea una nueva materia o obtiene una existente"""
        
        # Buscar materia existente por nombre
        existing_subject = Subject.query.filter_by(name=subject_data['name']).first()
        
        if existing_subject:
            return existing_subject
        
        # Crear nueva materia
        try:
            new_subject = Subject(
                name=subject_data['name'],
                code=subject_data.get('code', subject_data['name'][:4].upper()),
                description=f"Materia importada: {subject_data['name']}"
            )
            
            db.session.add(new_subject)
            db.session.flush()  # Para obtener el ID
            return new_subject
            
        except IntegrityError:
            db.session.rollback()
            # Si hay error de integridad, intentar obtener la materia nuevamente
            return Subject.query.filter_by(name=subject_data['name']).first()
    
    @staticmethod
    def _create_or_update_student(student_data, section):
        """Crea un nuevo estudiante o actualiza uno existente"""
        
        # Buscar estudiante existente por ID
        existing_student = Student.query.filter_by(
            student_id=student_data['student_id']
        ).first()
        
        if existing_student:
            # Actualizar datos del estudiante existente
            existing_student.first_name = student_data['first_name']
            existing_student.last_name = student_data['last_name']
            existing_student.email = student_data.get('email', existing_student.email)
            existing_student.section_id = section.id
            existing_student.is_active = True
            
            return existing_student, False  # False = no creado, actualizado
        
        # Crear nuevo estudiante
        try:
            new_student = Student(
                student_id=student_data['student_id'],
                first_name=student_data['first_name'],
                last_name=student_data['last_name'],
                email=student_data.get('email', ''),
                section_id=section.id,
                is_active=True
            )
            
            db.session.add(new_student)
            db.session.flush()  # Para obtener el ID
            return new_student, True  # True = creado
            
        except IntegrityError:
            db.session.rollback()
            # Si hay error, intentar obtener el estudiante
            existing = Student.query.filter_by(student_id=student_data['student_id']).first()
            if existing:
                return existing, False
            else:
                raise Exception(f"No se pudo crear el estudiante {student_data['student_id']}")
    
    @staticmethod
    def _import_student_grades(student, grades_data, subject_mapping, period):
        """Importa las calificaciones de un estudiante"""
        
        grades_imported = 0
        
        for subject_name, grade_value in grades_data.items():
            subject = subject_mapping.get(subject_name)
            
            if not subject:
                continue
            
            try:
                # Buscar calificación final existente
                existing_grade = FinalGrade.query.filter_by(
                    student_id=student.id,
                    subject_id=subject.id,
                    period_id=period.id
                ).first()
                
                if existing_grade:
                    # Actualizar calificación existente
                    existing_grade.value = grade_value
                else:
                    # Crear nueva calificación final
                    new_grade = FinalGrade(
                        student_id=student.id,
                        subject_id=subject.id,
                        period_id=period.id,
                        value=grade_value
                    )
                    db.session.add(new_grade)
                
                grades_imported += 1
                
            except Exception as e:
                logging.error(f"Error importando calificación: {str(e)}")
                continue
        
        return grades_imported
    
    @staticmethod
    def preview_import_data(file_path, sheet_name=None):
        """
        Genera una vista previa de los datos que se importarían
        
        Args:
            file_path: Ruta del archivo Excel
            sheet_name: Nombre de la hoja (opcional)
        
        Returns:
            dict: Vista previa de los datos
        """
        
        try:
            # Extraer datos
            extracted_data = ExcelDataExtractor.extract_students_and_grades(file_path, sheet_name)
            
            # Generar estadísticas
            preview = {
                'success': True,
                'total_students': len(extracted_data['students']),
                'total_subjects': len(extracted_data['subjects']),
                'subjects': [s['name'] for s in extracted_data['subjects']],
                'sample_students': extracted_data['students'][:5],  # Primeros 5 estudiantes
                'grade_statistics': DataImportService._calculate_grade_statistics(extracted_data['students']),
                'validation_warnings': []
            }
            
            # Validaciones
            preview['validation_warnings'] = DataImportService._validate_import_data(extracted_data)
            
            return preview
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'total_students': 0,
                'total_subjects': 0,
                'subjects': [],
                'sample_students': [],
                'grade_statistics': {},
                'validation_warnings': []
            }
    
    @staticmethod
    def _calculate_grade_statistics(students_data):
        """Calcula estadísticas de las calificaciones"""
        
        all_grades = []
        subject_grades = {}
        
        for student in students_data:
            for subject, grade in student['grades'].items():
                if isinstance(grade, (int, float)):
                    all_grades.append(grade)
                    
                    if subject not in subject_grades:
                        subject_grades[subject] = []
                    subject_grades[subject].append(grade)
        
        statistics = {
            'total_grades': len(all_grades),
            'average_overall': round(sum(all_grades) / len(all_grades), 2) if all_grades else 0,
            'min_grade': min(all_grades) if all_grades else 0,
            'max_grade': max(all_grades) if all_grades else 0,
            'subjects_stats': {}
        }
        
        # Estadísticas por materia
        for subject, grades in subject_grades.items():
            statistics['subjects_stats'][subject] = {
                'count': len(grades),
                'average': round(sum(grades) / len(grades), 2),
                'min': min(grades),
                'max': max(grades)
            }
        
        return statistics
    
    @staticmethod
    def _validate_import_data(extracted_data):
        """Valida los datos extraídos y retorna advertencias"""
        
        warnings = []
        
        # Validar estudiantes
        student_ids = [s['student_id'] for s in extracted_data['students']]
        if len(student_ids) != len(set(student_ids)):
            warnings.append("Hay IDs de estudiantes duplicados en el archivo")
        
        # Validar nombres vacíos
        empty_names = [s for s in extracted_data['students'] 
                      if not s['first_name'].strip() or not s['last_name'].strip()]
        if empty_names:
            warnings.append(f"{len(empty_names)} estudiantes tienen nombres vacíos")
        
        # Validar calificaciones fuera de rango
        invalid_grades = []
        for student in extracted_data['students']:
            for subject, grade in student['grades'].items():
                if isinstance(grade, (int, float)) and (grade < 0 or grade > 100):
                    invalid_grades.append(f"{student['student_id']}: {subject} = {grade}")
        
        if invalid_grades:
            warnings.append(f"Calificaciones fuera del rango 0-100: {len(invalid_grades)} casos")
        
        # Validar materias
        if not extracted_data['subjects']:
            warnings.append("No se detectaron materias en el archivo")
        
        return warnings
    
    @staticmethod
    def get_import_history(limit=50):
        """Obtiene el historial de importaciones (esto requeriría una tabla adicional)"""
        
        # Por ahora retornamos una lista vacía
        # En una implementación completa, crearías una tabla ImportHistory
        return []
    
    @staticmethod
    def rollback_import(import_id):
        """Revierte una importación específica (requiere tabla de historial)"""
        
        # Implementación futura
        pass
