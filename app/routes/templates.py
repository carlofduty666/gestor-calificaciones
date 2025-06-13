from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify, json
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from io import BytesIO
from app.models.templates import ExcelTemplate, TemplateCell, TemplateStyle, TemplateRange
from app.models.academic import Subject
from app.services.template_service import TemplateService
from app import db
import os
from datetime import datetime

templates = Blueprint('templates', __name__)

@templates.before_request
def check_admin_access():
    """Solo administradores pueden gestionar plantillas"""
    if not current_user.is_authenticated or not current_user.is_admin():
        flash('Acceso denegado. Solo administradores pueden gestionar plantillas.', 'danger')
        return redirect(url_for('auth.login'))

@templates.route('/')
@login_required
def index():
    """Lista todas las plantillas disponibles"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    templates_query = ExcelTemplate.query.filter_by(is_active=True).order_by(ExcelTemplate.created_at.desc())
    templates_paginated = templates_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('templates/index.html', 
                         templates=templates_paginated.items,
                         pagination=templates_paginated,
                         title='Gestión de Plantillas Excel')

@templates.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Crear nueva plantilla"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        template_type = request.form.get('template_type')
        
        if not name or not template_type:
            flash('Nombre y tipo de plantilla son obligatorios', 'danger')
            return render_template('templates/create.html')
        
        # Verificar si ya existe una plantilla con ese nombre
        existing = ExcelTemplate.query.filter_by(name=name, is_active=True).first()
        if existing:
            flash('Ya existe una plantilla con ese nombre', 'danger')
            return render_template('templates/create.html')
        
        # Manejar archivo subido
        file_path = None
        if 'template_file' in request.files:
            file = request.files['template_file']
            if file and file.filename.endswith('.xlsx'):
                filename = secure_filename(f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
                file_path = os.path.join('uploads/templates', filename)
                
                # Crear directorio si no existe
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
        
        # Crear plantilla
        template = ExcelTemplate(
            name=name,
            description=description,
            template_type=template_type,
            file_path=file_path,
            created_by=current_user.id
        )
        
        try:
            db.session.add(template)
            db.session.commit()
            
            # Si se subió un archivo, analizar su estructura
            if file_path:
                TemplateService.analyze_template_structure(template.id, file_path)
            
            flash('Plantilla creada exitosamente', 'success')
            return redirect(url_for('templates.view', id=template.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear plantilla: {str(e)}', 'danger')
    
    return render_template('templates/create.html', title='Crear Plantilla')

@templates.route('/<int:id>')
@login_required
def view(id):
    """Ver detalles de una plantilla"""
    template = ExcelTemplate.query.get_or_404(id)
    
    # Obtener celdas y estilos
    cells = TemplateCell.query.filter_by(template_id=id).order_by(TemplateCell.cell_address).all()
    styles = TemplateStyle.query.filter_by(template_id=id).order_by(TemplateStyle.range_address).all()
    
    return render_template('templates/view.html',
                         template=template,
                         cells=cells,
                         styles=styles,
                         title=f'Plantilla: {template.name}')

@templates.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Editar plantilla"""
    template = ExcelTemplate.query.get_or_404(id)
    
    if request.method == 'POST':
        template.name = request.form.get('name', template.name)
        template.description = request.form.get('description', template.description)
        template.template_type = request.form.get('template_type', template.template_type)
        
        # Manejar nuevo archivo si se subió
        if 'template_file' in request.files:
            file = request.files['template_file']
            if file and file.filename.endswith('.xlsx'):
                # Eliminar archivo anterior si existe
                if template.file_path and os.path.exists(template.file_path):
                    os.remove(template.file_path)
                
                filename = secure_filename(f"{template.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
                file_path = os.path.join('uploads/templates', filename)
                file.save(file_path)
                template.file_path = file_path
                
                # Re-analizar estructura
                TemplateService.analyze_template_structure(template.id, file_path)
        
        try:
            db.session.commit()
            flash('Plantilla actualizada exitosamente', 'success')
            return redirect(url_for('templates.view', id=template.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar plantilla: {str(e)}', 'danger')
    
    return render_template('templates/edit.html', 
                         template=template,
                         title=f'Editar: {template.name}')

@templates.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Eliminar plantilla (soft delete)"""
    template = ExcelTemplate.query.get_or_404(id)
    
    try:
        template.is_active = False
        db.session.commit()
        flash('Plantilla eliminada exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar plantilla: {str(e)}', 'danger')
    
    return redirect(url_for('templates.index'))

@templates.route('/<int:id>/download')
@login_required
def download(id):
    """Descargar archivo de plantilla"""
    template = ExcelTemplate.query.get_or_404(id)
    
    if not template.file_path or not os.path.exists(template.file_path):
        flash('Archivo de plantilla no encontrado', 'danger')
        return redirect(url_for('templates.view', id=id))
    
    return send_file(
        template.file_path,
        as_attachment=True,
        download_name=f"{template.name}.xlsx"
    )

@templates.route('/<int:id>/preview')
@login_required
def preview(id):
    """Vista previa de la plantilla"""
    template = ExcelTemplate.query.get_or_404(id)
    
    if not template.file_path or not os.path.exists(template.file_path):
        flash('Archivo de plantilla no encontrado', 'danger')
        return redirect(url_for('templates.view', id=id))
    
    try:
        # Generar vista previa usando el servicio
        preview_data = TemplateService.generate_preview(template.id)
        
        return render_template('templates/preview.html',
                             template=template,
                             preview_data=preview_data,
                             title=f'Vista Previa: {template.name}')
        
    except Exception as e:
        flash(f'Error al generar vista previa: {str(e)}', 'danger')
        return redirect(url_for('templates.view', id=id))

@templates.route('/<int:id>/duplicate', methods=['POST'])
@login_required
def duplicate(id):
    """Duplicar plantilla"""
    original = ExcelTemplate.query.get_or_404(id)
    
    # Crear nombre único
    new_name = f"{original.name} - Copia"
    counter = 1
    while ExcelTemplate.query.filter_by(name=new_name, is_active=True).first():
        new_name = f"{original.name} - Copia ({counter})"
        counter += 1
    
    try:
        # Duplicar plantilla
        duplicate_template = ExcelTemplate(
            name=new_name,
            description=f"Copia de: {original.description}" if original.description else None,
            template_type=original.template_type,
            design_config=original.design_config,
            created_by=current_user.id
        )
        
        db.session.add(duplicate_template)
        db.session.flush()  # Para obtener el ID
        
        # Duplicar celdas
        for cell in original.cells:
            new_cell = TemplateCell(
                template_id=duplicate_template.id,
                cell_address=cell.cell_address,
                cell_type=cell.cell_type,
                content_type=cell.content_type,
                default_value=cell.default_value,
                style_config=cell.style_config
            )
            db.session.add(new_cell)
        
        # Duplicar estilos
        for style in original.styles:
            new_style = TemplateStyle(
                template_id=duplicate_template.id,
                range_address=style.range_address,
                column_width=style.column_width,
                row_height=style.row_height,
                merge_cells=style.merge_cells,
                style_config=style.style_config
            )
            db.session.add(new_style)
        
        # Duplicar archivo si existe
        if original.file_path and os.path.exists(original.file_path):
            import shutil
            new_filename = secure_filename(f"{new_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
            new_file_path = os.path.join('uploads/templates', new_filename)
            shutil.copy2(original.file_path, new_file_path)
            duplicate_template.file_path = new_file_path
        
        db.session.commit()
        flash('Plantilla duplicada exitosamente', 'success')
        return redirect(url_for('templates.view', id=duplicate_template.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al duplicar plantilla: {str(e)}', 'danger')
        return redirect(url_for('templates.view', id=id))

@templates.route('/api/types')
@login_required
def api_template_types():
    """API para obtener tipos de plantillas disponibles"""
    types = [
        {'value': 'section_report', 'label': 'Reporte de Sección'},
        {'value': 'student_report', 'label': 'Reporte de Estudiante'},
        {'value': 'grade_summary', 'label': 'Resumen de Calificaciones'},
        {'value': 'attendance_report', 'label': 'Reporte de Asistencia'},
        {'value': 'custom', 'label': 'Personalizado'}
    ]
    return jsonify(types)

@templates.route('/api/<int:id>/cells')
@login_required
def api_template_cells(id):
    """API para obtener celdas de una plantilla"""
    template = ExcelTemplate.query.get_or_404(id)
    cells = TemplateCell.query.filter_by(template_id=id).all()
    
    cells_data = []
    for cell in cells:
        cells_data.append({
            'id': cell.id,
            'address': cell.cell_address,
            'type': cell.cell_type,
            'default_value': cell.default_value,
            'style_config': cell.style_config
        })
    
    return jsonify(cells_data)

# Ruta para configurar una plantilla
@templates.route('/configure/<int:template_id>')
@login_required
def configure_template(template_id):
    """Interfaz mejorada para configurar plantilla con rangos"""
    
    template = ExcelTemplate.query.get_or_404(template_id)
    
    # Obtener celdas individuales
    individual_cells = TemplateCell.query.filter_by(
        template_id=template_id
    ).order_by(TemplateCell.cell_address).all()
    
    # Si no hay celdas, crear algunas de ejemplo
    if not individual_cells:
        # Crear celdas básicas si no existen
        basic_cells = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']
        for cell_addr in basic_cells:
            cell = TemplateCell(
                template_id=template_id,
                cell_address=cell_addr,
                cell_type='static',
                default_value=f'Celda {cell_addr}',
                data_type='static'
            )
            db.session.add(cell)
        
        db.session.commit()
        
        # Volver a obtener las celdas
        individual_cells = TemplateCell.query.filter_by(
            template_id=template_id
        ).order_by(TemplateCell.cell_address).all()
    
    # Obtener rangos configurados
    ranges = TemplateRange.query.filter_by(template_id=template_id).all()
    
    # Convertir rangos a formato JSON
    ranges_json = []
    for range_obj in ranges:
        try:
            range_data = {
                'name': range_obj.range_name,
                'type': range_obj.range_type,
                'start_cell': range_obj.start_cell,
                'end_cell': range_obj.end_cell,
                'mapping': json.loads(range_obj.data_mapping) if range_obj.data_mapping else {}
            }
            ranges_json.append(range_data)
        except json.JSONDecodeError:
            continue
    
    # Tipos de datos para celdas individuales
    individual_data_types = {
        'static': 'Texto estático',
        'titulo_reporte': 'Título del reporte',
        'nombre_institucion': 'Nombre de la institución',
        'seccion': 'Nombre de la sección',
        'grado': 'Nombre del grado',
        'periodo': 'Nombre del período',
        'fecha_actual': 'Fecha actual',
        'total_estudiantes': 'Total de estudiantes',
        'promedio_seccion': 'Promedio de la sección',
        'estudiantes_aprobados': 'Estudiantes aprobados',
        'estudiantes_reprobados': 'Estudiantes reprobados'
    }
    
    # Tipos de rangos iterativos
    range_types = {
        'students': 'Lista de estudiantes',
        'subjects': 'Lista de materias',
        'grades_by_student': 'Calificaciones por estudiante',
        'statistics': 'Estadísticas por materia'
    }
    
    # Mapeos disponibles para cada tipo de rango
    student_mappings = {
        'numero': 'Número correlativo (1, 2, 3...)',
        'cedula': 'Cédula del estudiante',
        'apellido': 'Apellido',
        'nombre': 'Nombre',
        'nombre_completo': 'Nombre completo',
        'seccion': 'Sección del estudiante'
    }
    
    subject_mappings = {
        'numero': 'Número correlativo',
        'codigo': 'Código de la materia',
        'nombre': 'Nombre de la materia',
        'profesor': 'Nombre del profesor'
    }
    
    grade_mappings = {
        'numero': 'Número correlativo',
        'cedula': 'Cédula del estudiante',
        'nombre': 'Nombre del estudiante',
        'materia_1': 'Nota materia 1',
        'materia_2': 'Nota materia 2',
        'materia_3': 'Nota materia 3',
        'promedio': 'Promedio del estudiante'
    }
    
    # Obtener materias disponibles
    from app.models.academic import Subject
    subjects = Subject.query.all()
    
    return render_template('templates/configure_advanced.html',
                         template=template,
                         individual_cells=individual_cells,
                         ranges=ranges,
                         ranges_json=ranges_json,
                         individual_data_types=individual_data_types,
                         range_types=range_types,
                         student_mappings=student_mappings,
                         subject_mappings=subject_mappings,
                         grade_mappings=grade_mappings,
                         subjects=subjects)

#Ruta para guardar configuración de celdas individuales
@templates.route('/save-range-configuration/<int:template_id>', methods=['POST'])
@login_required
def save_range_configuration(template_id):
    """Guarda configuración de rangos"""
    
    try:
        data = request.json
        
        # Guardar celdas individuales
        if 'individual_cells' in data:
            for cell_config in data['individual_cells']:
                cell = TemplateCell.query.filter_by(
                    template_id=template_id,
                    cell_address=cell_config['address']
                ).first()
                
                if cell:
                    cell.cell_type = 'static' if cell_config['data_type'] == 'static' else 'data'
                    cell.data_type = cell_config['data_type']
        
        # Guardar rangos
        if 'ranges' in data:
            # Eliminar rangos existentes
            TemplateRange.query.filter_by(template_id=template_id).delete()
            
            # Crear nuevos rangos
            for range_config in data['ranges']:
                new_range = TemplateRange(
                    template_id=template_id,
                    range_name=range_config['name'],
                    start_cell=range_config['start_cell'],
                    end_cell=range_config.get('end_cell'),
                    range_type=range_config['type'],
                    data_mapping=json.dumps(range_config['mapping'])
                )
                db.session.add(new_range)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Configuración guardada exitosamente'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@templates.route('/generate-preview/<int:template_id>', methods=['POST'])
@login_required
def generate_preview(template_id):
    """Genera vista previa con la configuración actual"""
    
    try:
        template = ExcelTemplate.query.get_or_404(template_id)
        config_data = request.json
        
        # Datos de ejemplo para la vista previa
        sample_data = {
            'section': {'name': '1ro "A"', 'grade': {'name': '1er Año'}},
            'period': {'name': '1er Lapso'},
            'current_date': datetime.now().strftime('%d/%m/%Y'),
            'students': [
                {'cedula': '12345678', 'nombre': 'Juan', 'apellido': 'García', 'nombre_completo': 'García, Juan'},
                {'cedula': '87654321', 'nombre': 'María', 'apellido': 'López', 'nombre_completo': 'López, María'},
                {'cedula': '11223344', 'nombre': 'Carlos', 'apellido': 'Martínez', 'nombre_completo': 'Martínez, Carlos'}
            ],
            'subjects': [
                {'codigo': 'MAT', 'nombre': 'Matemáticas'},
                {'codigo': 'ESP', 'nombre': 'Español'},
                {'codigo': 'ING', 'nombre': 'Inglés'}
            ]
        }
        
        # Generar vista previa basada en la configuración
        preview_data = TemplateService.generate_preview_with_config(
            template_id, config_data, sample_data
        )
        
        return jsonify({
            'success': True,
            'preview': preview_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@templates.route('/download-preview/<int:template_id>')
@login_required
def download_preview(template_id):
    """Descarga un Excel de vista previa"""
    
    try:
        template = ExcelTemplate.query.get_or_404(template_id)
        
        # Generar Excel de vista previa
        wb = TemplateService.generate_preview_excel(template_id)
        
        # Guardar en memoria
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        filename = f"Vista_Previa_{template.name}.xlsx"
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        flash(f'Error al generar vista previa: {str(e)}', 'danger')
        return redirect(url_for('templates.configure_template', template_id=template_id))
