from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.academic import AcademicYear, Period, Grade, Section, Subject
from app import db
import pandas as pd
from io import BytesIO
import os
from datetime import datetime

data_import = Blueprint('data_import', __name__)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@data_import.route('/')
@login_required
def index():
    """Página principal de importación con datos reales"""
    academic_years = AcademicYear.query.order_by(AcademicYear.start_date.desc()).all()
    grades = Grade.query.order_by(Grade.level, Grade.name).all()
    subjects = Subject.query.order_by(Subject.name).all()
    
    return render_template('reports/uploads.html', 
                         academic_years=academic_years,
                         grades=grades,
                         subjects=subjects)

@data_import.route('/upload')
@login_required
def upload():
    """Alias para index - formulario de subida"""
    return redirect(url_for('data_import.index'))

@data_import.route('/download-template/<int:grade_id>')
@login_required
def download_template(grade_id):
    """Descargar plantilla Excel para un grado específico"""
    try:
        grade = Grade.query.get_or_404(grade_id)
        sections = Section.query.filter_by(grade_id=grade_id).all()
        subjects = Subject.query.all()
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja 1: Información del grado
            info_data = {
                'Campo': ['Grado', 'Nivel', 'Secciones Disponibles', 'Total Asignaturas'],
                'Valor': [
                    grade.name, 
                    grade.level,
                    ', '.join([s.name for s in sections]) if sections else 'Sin secciones',
                    len(subjects)
                ]
            }
            info_df = pd.DataFrame(info_data)
            info_df.to_excel(writer, sheet_name='Información', index=False)
            
            # Hoja 2: Plantilla de estudiantes
            student_template = {
                'Nombre': ['Juan', 'María', 'Pedro'],
                'Apellido': ['Pérez', 'González', 'Rodríguez'],
                'Cedula': ['12345678', '87654321', '11223344'],
                'Fecha_Nacimiento': ['01/01/2010', '15/03/2010', '20/07/2010'],
                'Genero': ['M', 'F', 'M'],
                'Seccion': [sections[0].name if sections else 'A'] * 3,
                'Email': ['juan@email.com', 'maria@email.com', 'pedro@email.com'],
                'Telefono': ['555-1234', '555-5678', '555-9012']
            }
            student_df = pd.DataFrame(student_template)
            student_df.to_excel(writer, sheet_name='Estudiantes', index=False)
            
            # Hoja 3: Secciones disponibles
            if sections:
                sections_data = {
                    'ID_Seccion': [s.id for s in sections],
                    'Nombre_Seccion': [s.name for s in sections],
                    'Grado': [grade.name for s in sections]
                }
                sections_df = pd.DataFrame(sections_data)
                sections_df.to_excel(writer, sheet_name='Secciones', index=False)
            
            # Hoja 4: Asignaturas
            subjects_data = {
                'ID_Asignatura': [s.id for s in subjects],
                'Nombre_Asignatura': [s.name for s in subjects],
                'Codigo': [s.code for s in subjects]
            }
            subjects_df = pd.DataFrame(subjects_data)
            subjects_df.to_excel(writer, sheet_name='Asignaturas', index=False)
        
        output.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'Plantilla_{grade.name}_{timestamp}.xlsx'
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        flash(f'Error al generar plantilla: {str(e)}', 'danger')
        return redirect(url_for('data_import.index'))

# AGREGAR ESTA RUTA QUE FALTA:
@data_import.route('/process', methods=['POST'])
@login_required
def process_upload():
    """Procesar archivo Excel subido"""
    try:
        # Verificar archivo
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(url_for('data_import.index'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(url_for('data_import.index'))
        
        if not allowed_file(file.filename):
            flash('Tipo de archivo no permitido. Solo se permiten archivos .xlsx y .xls', 'danger')
            return redirect(url_for('data_import.index'))
        
        # Obtener parámetros del formulario
        academic_year_id = request.form.get('academic_year_id')
        period_id = request.form.get('period_id')
        grade_id = request.form.get('grade_id')
        section_id = request.form.get('section_id')
        
        if not all([academic_year_id, period_id, grade_id, section_id]):
            flash('Todos los campos son obligatorios', 'danger')
            return redirect(url_for('data_import.index'))
        
        # Verificar que existan en la base de datos
        academic_year = AcademicYear.query.get(academic_year_id)
        period = Period.query.get(period_id)
        grade = Grade.query.get(grade_id)
        section = Section.query.get(section_id)
        
        if not all([academic_year, period, grade, section]):
            flash('Datos seleccionados inválidos', 'danger')
            return redirect(url_for('data_import.index'))
        
        # Guardar archivo temporalmente
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        # Crear directorio si no existe
        upload_dir = os.path.join('app', 'uploads', 'imports')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Procesar archivo Excel
        try:
            # Leer archivo Excel
            df = pd.read_excel(file_path, sheet_name='Estudiantes')
            
            # Validar columnas requeridas
            required_columns = ['Nombre', 'Apellido', 'Cedula']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                flash(f'Columnas faltantes en el archivo: {", ".join(missing_columns)}', 'danger')
                os.remove(file_path)  # Limpiar archivo
                return redirect(url_for('data_import.index'))
            
            # Procesar estudiantes
            students_created = 0
            students_updated = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Buscar estudiante existente
                    existing_student = Student.query.filter_by(student_id=str(row['Cedula'])).first()
                    
                    if existing_student:
                        # Actualizar estudiante existente
                        existing_student.first_name = str(row['Nombre']).strip()
                        existing_student.last_name = str(row['Apellido']).strip()
                        existing_student.section_id = section.id
                        existing_student.is_active = True
                        students_updated += 1
                    else:
                        # Crear nuevo estudiante
                        from app.models.academic import Student
                        new_student = Student(
                            student_id=str(row['Cedula']),
                            first_name=str(row['Nombre']).strip(),
                            last_name=str(row['Apellido']).strip(),
                            section_id=section.id,
                            email=str(row.get('Email', '')).strip() if pd.notna(row.get('Email')) else '',
                            phone=str(row.get('Telefono', '')).strip() if pd.notna(row.get('Telefono')) else '',
                            is_active=True
                        )
                        db.session.add(new_student)
                        students_created += 1
                        
                except Exception as e:
                    errors.append(f"Fila {index + 2}: {str(e)}")
                    continue
            
            # Guardar cambios
            db.session.commit()
            
            # Limpiar archivo temporal
            os.remove(file_path)
            
            # Mostrar resultados
            success_msg = f'Importación completada: {students_created} estudiantes creados, {students_updated} actualizados'
            if errors:
                success_msg += f'. {len(errors)} errores encontrados.'
            
            flash(success_msg, 'success')
            
            if errors:
                for error in errors[:5]:  # Mostrar solo los primeros 5 errores
                    flash(error, 'warning')
            
        except Exception as e:
            # Limpiar archivo en caso de error
            if os.path.exists(file_path):
                os.remove(file_path)
            flash(f'Error procesando archivo: {str(e)}', 'danger')
            return redirect(url_for('data_import.index'))
        
        return redirect(url_for('reports.index'))
        
    except Exception as e:
        flash(f'Error inesperado: {str(e)}', 'danger')
        return redirect(url_for('data_import.index'))

# # APIs para dropdowns dinámicos
# @data_import.route('/api/grade/<int:grade_id>/sections')
# @login_required
# def api_grade_sections(grade_id):
#     """API para obtener secciones de un grado"""
#     try:
#         sections = Section.query.filter_by(grade_id=grade_id).all()
#         return jsonify({
#             'success': True,
#             'sections': [
#                 {
#                     'id': section.id,
#                     'name': section.name
#                 }
#                 for section in sections
#             ]
#         })
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# @data_import.route('/api/academic-year/<int:year_id>/periods')
# @login_required
# def api_year_periods(year_id):
#     """API para obtener períodos de un año académico"""
#     try:
#         periods = Period.query.filter_by(academic_year_id=year_id).all()
#         return jsonify({
#             'success': True,
#             'periods': [
#                 {
#                     'id': period.id,
#                     'name': period.name
#                 }
#                 for period in periods
#             ]
#         })
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500
