from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border
from app.models.templates import ExcelTemplate, TemplateCell, TemplateRange
from app.models.academic import Student, Section, Subject, Period, TeacherAssignment
from app.models.grades import FinalGrade, StudentGrade
from app import db
from io import BytesIO
import json
import re
import os
from datetime import datetime

class TemplateProcessor:
    """Procesador de plantillas Excel con inyección de datos"""
    
    def __init__(self, template):
        self.template = template
        self.workbook = None
        self.worksheet = None
        
    def load_template(self):
        """Cargar la plantilla Excel"""
        if not self.template.file_path or not os.path.exists(self.template.file_path):
            raise Exception(f"Archivo de plantilla no encontrado: {self.template.file_path}")
        
        self.workbook = load_workbook(self.template.file_path)
        self.worksheet = self.workbook.active
        
    def generate_section_report(self, section, period):
        """Generar reporte de sección usando la plantilla"""
        
        self.load_template()
        
        # Obtener estudiantes y datos
        students = Student.query.filter_by(
            section_id=section.id,
            is_active=True
        ).order_by(Student.last_name).all()
        
        # Obtener asignaturas
        subject_ids = db.session.query(TeacherAssignment.subject_id).filter_by(
            section_id=section.id,
            academic_year_id=period.academic_year_id
        ).distinct().all()
        
        subject_ids = [s[0] for s in subject_ids]
        subjects = Subject.query.filter(Subject.id.in_(subject_ids)).order_by(Subject.name).all()
        
        # Preparar contexto de datos
        context = {
            'section': section,
            'period': period,
            'students': students,
            'subjects': subjects,
            'current_date': datetime.now(),
            'total_students': len(students)
        }
        
        # Procesar celdas individuales
        self._process_individual_cells(context)
        
        # Procesar rangos iterativos
        self._process_ranges(context)
        
        # Guardar en memoria
        output = BytesIO()
        self.workbook.save(output)
        output.seek(0)
        
        return output
    
    def generate_student_report(self, student, period):
        """Generar reporte individual de estudiante"""
        
        self.load_template()
        
        # Obtener asignaturas del estudiante
        subject_ids = db.session.query(TeacherAssignment.subject_id).filter_by(
            section_id=student.section_id,
            academic_year_id=period.academic_year_id
        ).distinct().all()
        
        subject_ids = [s[0] for s in subject_ids]
        subjects = Subject.query.filter(Subject.id.in_(subject_ids)).order_by(Subject.name).all()
        
        # Obtener calificaciones
        grades_data = {}
        for subject in subjects:
            final_grade = FinalGrade.query.filter_by(
                student_id=student.id,
                subject_id=subject.id,
                period_id=period.id
            ).first()
            
            if final_grade:
                grades_data[subject.id] = final_grade.value
        
        # Preparar contexto
        context = {
            'student': student,
            'period': period,
            'subjects': subjects,
            'grades_data': grades_data,
            'current_date': datetime.now()
        }
        
        # Procesar plantilla
        self._process_individual_cells(context)
        self._process_ranges(context)
        
        # Guardar en memoria
        output = BytesIO()
        self.workbook.save(output)
        output.seek(0)
        
        return output
    
    def _process_individual_cells(self, context):
        """Procesar celdas individuales"""
        
        individual_cells = TemplateCell.query.filter_by(
            template_id=self.template.id
        ).all()
        
        for cell in individual_cells:
            try:
                value = self._get_cell_value(cell, context)
                if value is not None:
                    self.worksheet[cell.cell_address] = value
                    
                    # Aplicar estilo si existe
                    if cell.style_config:
                        self._apply_cell_style(
                            self.worksheet[cell.cell_address], 
                            json.loads(cell.style_config)
                        )
                        
            except Exception as e:
                print(f"Error procesando celda {cell.cell_address}: {e}")
                continue
    
    def _process_ranges(self, context):
        """Procesar rangos iterativos"""
        
        ranges = TemplateRange.query.filter_by(
            template_id=self.template.id
        ).all()
        
        for range_obj in ranges:
            try:
                self._process_single_range(range_obj, context)
            except Exception as e:
                print(f"Error procesando rango {range_obj.range_name}: {e}")
                continue
    
    def _process_single_range(self, range_obj, context):
        """Procesar un rango específico"""
        
        # Obtener mapeo de columnas
        try:
            column_mapping = json.loads(range_obj.data_mapping)
        except:
            return
        
        # Obtener datos según el tipo de rango
        if range_obj.range_type == 'students':
            data_rows = self._get_students_data(context, column_mapping)
        elif range_obj.range_type == 'subjects':
            data_rows = self._get_subjects_data(context, column_mapping)
        elif range_obj.range_type == 'grades_by_student':
            data_rows = self._get_grades_data(context, column_mapping)
        else:
            return
        
        # Escribir datos en el rango
        start_row, start_col = self._parse_cell_address(range_obj.start_cell)
        
        for row_index, row_data in enumerate(data_rows):
            current_row = start_row + row_index
            
            for col_letter, data_type in column_mapping.items():
                col_index = ord(col_letter) - ord('A') + start_col
                cell_address = f"{col_letter}{current_row}"
                
                if data_type in row_data:
                    self.worksheet[cell_address] = row_data[data_type]
    
    def _get_students_data(self, context, column_mapping):
        """Obtener datos de estudiantes"""
        
        students = context.get('students', [])
        data_rows = []
        
        for index, student in enumerate(students):
            row_data = {
                'numero': index + 1,
                'cedula': student.student_id,
                'apellido': student.last_name,
                'nombre': student.first_name,
                'nombre_completo': f"{student.last_name}, {student.first_name}",
                'seccion': f"{student.section.grade.name}{student.section.name}"
            }
            data_rows.append(row_data)
        
        return data_rows
    
    def _get_subjects_data(self, context, column_mapping):
        """Obtener datos de asignaturas"""
        
        subjects = context.get('subjects', [])
        data_rows = []
        
        for index, subject in enumerate(subjects):
            row_data = {
                'numero': index + 1,
                'codigo': subject.code,
                'nombre': subject.name,
                'descripcion': subject.description or '',
                'profesor': self._get_subject_teacher(subject, context)
            }
            data_rows.append(row_data)
        
        return data_rows
    
    def _get_grades_data(self, context, column_mapping):
        """Obtener datos de calificaciones por estudiante"""
        
        students = context.get('students', [])
        subjects = context.get('subjects', [])
        period = context.get('period')
        data_rows = []
        
        for index, student in enumerate(students):
            row_data = {
                'numero': index + 1,
                'cedula': student.student_id,
                'nombre': f"{student.last_name}, {student.first_name}",
                'apellido': student.last_name,
                'nombre_solo': student.first_name
            }
            
            # Agregar calificaciones por materia
            total_grades = 0
            grade_count = 0
            
            for subject_index, subject in enumerate(subjects):
                final_grade = FinalGrade.query.filter_by(
                    student_id=student.id,
                    subject_id=subject.id,
                    period_id=period.id
                ).first()
                
                grade_value = final_grade.value if final_grade else 0
                row_data[f'materia_{subject_index + 1}'] = grade_value
                row_data[f'nota_{subject.code.lower()}'] = grade_value
                
                if grade_value > 0:
                    total_grades += grade_value
                    grade_count += 1
            
            # Calcular promedio
            row_data['promedio'] = round(total_grades / grade_count, 2) if grade_count > 0 else 0
            row_data['total_materias'] = len(subjects)
            row_data['materias_aprobadas'] = sum(1 for s in subjects if self._get_student_grade(student, s, period) >= 10)
            
            data_rows.append(row_data)
        
        return data_rows
    
    def _get_subject_teacher(self, subject, context):
        """Obtener el profesor de una materia"""
        
        section = context.get('section')
        period = context.get('period')
        
        if not section or not period:
            return ''
        
        from app.models.academic import TeacherAssignment, Teacher
        
        assignment = TeacherAssignment.query.filter_by(
            subject_id=subject.id,
            section_id=section.id,
            academic_year_id=period.academic_year_id
        ).first()
        
        if assignment and assignment.teacher:
            teacher_user = assignment.teacher.user
            return f"{teacher_user.first_name} {teacher_user.last_name}"
        
        return ''
    
    def _get_student_grade(self, student, subject, period):
        """Obtener calificación de un estudiante en una materia"""
        
        final_grade = FinalGrade.query.filter_by(
            student_id=student.id,
            subject_id=subject.id,
            period_id=period.id
        ).first()
        
        return final_grade.value if final_grade else 0
    
    def _get_cell_value(self, cell, context):
        """Obtener el valor para una celda según su tipo"""
        
        data_type = cell.data_type
        
        if data_type == 'static':
            return cell.default_value
        
        elif data_type == 'custom_text':
            return cell.custom_text or cell.default_value
        
        elif data_type == 'titulo_reporte':
            return 'REPORTE DE CALIFICACIONES'
        
        elif data_type == 'nombre_institucion':
            return 'UNIDAD EDUCATIVA'  # Puedes hacer esto configurable
        
        elif data_type == 'seccion':
            section = context.get('section')
            return f"{section.grade.name} \"{section.name}\"" if section else ''
        
        elif data_type == 'grado':
            section = context.get('section')
            return section.grade.name if section else ''
        
        elif data_type == 'periodo':
            period = context.get('period')
            return period.name if period else ''
        
        elif data_type == 'fecha_actual':
            current_date = context.get('current_date')
            return current_date.strftime('%d/%m/%Y') if current_date else ''
        
        elif data_type == 'total_estudiantes':
            return context.get('total_students', 0)
        
        elif data_type == 'promedio_seccion':
            return self._calculate_section_average(context)
        
        elif data_type == 'estudiantes_aprobados':
            return self._count_passing_students(context)
        
        elif data_type == 'estudiantes_reprobados':
            total = context.get('total_students', 0)
            passed = self._count_passing_students(context)
            return total - passed
        
        # Para estudiante individual
        elif data_type == 'estudiante_nombre':
            student = context.get('student')
            return f"{student.first_name} {student.last_name}" if student else ''
        
        elif data_type == 'estudiante_cedula':
            student = context.get('student')
            return student.student_id if student else ''
        
        elif data_type == 'estudiante_promedio':
            return self._calculate_student_average(context)
        
        return cell.default_value
    
    def _calculate_section_average(self, context):
        """Calcular promedio general de la sección"""
        
        students = context.get('students', [])
        subjects = context.get('subjects', [])
        period = context.get('period')
        
        if not students or not subjects or not period:
            return 0
        
        total_grades = 0
        grade_count = 0
        
        for student in students:
            for subject in subjects:
                grade = self._get_student_grade(student, subject, period)
                if grade > 0:
                    total_grades += grade
                    grade_count += 1
        
        return round(total_grades / grade_count, 2) if grade_count > 0 else 0
    
    def _count_passing_students(self, context):
        """Contar estudiantes aprobados"""
        
        students = context.get('students', [])
        subjects = context.get('subjects', [])
        period = context.get('period')
        
        if not students or not subjects or not period:
            return 0
        
        passing_students = 0
        
        for student in students:
            student_grades = []
            for subject in subjects:
                grade = self._get_student_grade(student, subject, period)
                if grade > 0:
                    student_grades.append(grade)
            
            if student_grades:
                average = sum(student_grades) / len(student_grades)
                if average >= 10:  # Nota mínima aprobatoria
                    passing_students += 1
        
        return passing_students
    
    def _calculate_student_average(self, context):
        """Calcular promedio de un estudiante"""
        
        student = context.get('student')
        grades_data = context.get('grades_data', {})
        
        if not student or not grades_data:
            return 0
        
        grades = [grade for grade in grades_data.values() if grade > 0]
        return round(sum(grades) / len(grades), 2) if grades else 0
    
    def _parse_cell_address(self, cell_address):
        """Parsear dirección de celda (ej: A1 -> (1, 1))"""
        
        match = re.match(r'([A-Z]+)(\d+)', cell_address)
        if not match:
            return 1, 1
        
        col_letters = match.group(1)
        row_num = int(match.group(2))
        
        # Convertir letras de columna a número
        col_num = 0
        for char in col_letters:
            col_num = col_num * 26 + (ord(char) - ord('A') + 1)
        
        return row_num, col_num
    
    def _apply_cell_style(self, cell, style_config):
        """Aplicar estilo a una celda"""
        
        try:
            # Fuente
            if 'font' in style_config:
                font_config = style_config['font']
                cell.font = Font(
                    name=font_config.get('name', 'Arial'),
                    size=font_config.get('size', 11),
                    bold=font_config.get('bold', False),
                    italic=font_config.get('italic', False),
                    color=font_config.get('color', '000000')
                )
            
            # Relleno
            if 'fill' in style_config:
                fill_config = style_config['fill']
                cell.fill = PatternFill(
                    start_color=fill_config.get('color', 'FFFFFF'),
                    end_color=fill_config.get('color', 'FFFFFF'),
                    fill_type='solid'
                )
            
            # Alineación
            if 'alignment' in style_config:
                align_config = style_config['alignment']
                cell.alignment = Alignment(
                    horizontal=align_config.get('horizontal', 'left'),
                    vertical=align_config.get('vertical', 'top'),
                    wrap_text=align_config.get('wrap_text', False)
                )
                
        except Exception as e:
            print(f"Error aplicando estilo: {e}")
    
    def generate_preview(self):
        """Generar vista previa con datos de ejemplo"""
        
        # Crear contexto de ejemplo
        example_context = {
            'section': type('Section', (), {
                'grade': type('Grade', (), {'name': '1er Año'})(),
                'name': 'A'
            })(),
            'period': type('Period', (), {'name': '1er Lapso'})(),
            'current_date': datetime.now(),
            'total_students': 25,
            'student': type('Student', (), {
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'student_id': '12345678'
            })()
        }
        
        self.load_template()
        
        # Procesar solo celdas individuales para la vista previa
        preview_data = {}
        
        individual_cells = TemplateCell.query.filter_by(
            template_id=self.template.id
        ).all()
        
        for cell in individual_cells:
            try:
                value = self._get_cell_value(cell, example_context)
                
                # Parsear dirección de celda
                match = re.match(r'([A-Z]+)(\d+)', cell.cell_address)
                if match:
                    col_letter = match.group(1)
                    row_num = int(match.group(2))
                    
                    if row_num not in preview_data:
                        preview_data[row_num] = {}
                    
                    preview_data[row_num][col_letter] = {
                        'value': value,
                        'type': cell.data_type
                    }
                    
            except Exception as e:
                continue
        
        return preview_data
