from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.users import User
from app.models.academic import AcademicYear, Period, Grade, Section, Subject, Student, Teacher, TeacherAssignment
from app.models.grades import GradeType, StudentGrade, FinalGrade
from app import db
import pandas as pd
from io import BytesIO
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

reports = Blueprint('reports', __name__)

@reports.before_request
def check_access():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

@reports.route('/')
@login_required
def index():
    # Año académico activo
    active_year = AcademicYear.query.filter_by(is_active=True).first()
    
    if not active_year:
        flash('No hay un año académico activo configurado', 'warning')
        return render_template('reports/index.html', title='Reportes', active_year=None)
    
    # Períodos del año activo
    periods = Period.query.filter_by(academic_year_id=active_year.id).all()
    
    # Si es administrador, mostrar todos los grados y secciones
    if current_user.is_admin():
        grades = Grade.query.all()
        sections = Section.query.all()
    else:
        # Si es profesor, mostrar solo sus asignaciones
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        
        if not teacher:
            flash('No se encontró un perfil de profesor para este usuario', 'warning')
            return redirect(url_for('auth.logout'))
        
        # Obtener secciones únicas de las asignaciones del profesor
        assignments = TeacherAssignment.query.filter_by(
            teacher_id=teacher.id,
            academic_year_id=active_year.id
        ).all()
        
        section_ids = set(a.section_id for a in assignments)
        sections = Section.query.filter(Section.id.in_(section_ids)).all()
        
        # Obtener grados únicos de esas secciones
        grade_ids = set(s.grade_id for s in sections)
        grades = Grade.query.filter(Grade.id.in_(grade_ids)).all()
    
    return render_template('reports/index.html', 
                          title='Reportes',
                          active_year=active_year,
                          periods=periods,
                          grades=grades,
                          sections=sections)

@reports.route('/section/<int:section_id>/period/<int:period_id>')
@login_required
def section_report(section_id, period_id):
    section = Section.query.get_or_404(section_id)
    period = Period.query.get_or_404(period_id)
    
    # Verificar acceso
    if not current_user.is_admin():
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        
        if not teacher:
            flash('No se encontró un perfil de profesor para este usuario', 'warning')
            return redirect(url_for('auth.logout'))
        
        # Verificar si el profesor tiene asignaciones en esta sección
        assignment = TeacherAssignment.query.filter_by(
            teacher_id=teacher.id,
            section_id=section_id,
            academic_year_id=period.academic_year_id
        ).first()
        
        if not assignment:
            flash('No tienes permiso para ver esta sección', 'danger')
            return redirect(url_for('reports.index'))
    
    # Obtener estudiantes de la sección
    students = Student.query.filter_by(
        section_id=section_id,
        is_active=True
    ).order_by(Student.last_name).all()
    
    # Obtener asignaturas para esta sección (a través de las asignaciones)
    subject_ids = db.session.query(TeacherAssignment.subject_id).filter_by(
        section_id=section_id,
        academic_year_id=period.academic_year_id
    ).distinct().all()
    
    subject_ids = [s[0] for s in subject_ids]
    subjects = Subject.query.filter(Subject.id.in_(subject_ids)).order_by(Subject.name).all()
    
    # Obtener calificaciones finales
    grades_data = {}
    for student in students:
        grades_data[student.id] = {}
        for subject in subjects:
            final_grade = FinalGrade.query.filter_by(
                student_id=student.id,
                subject_id=subject.id,
                period_id=period.id
            ).first()
            
            if final_grade:
                grades_data[student.id][subject.id] = final_grade.value
    
    return render_template('reports/section_report.html',
                          title=f'Reporte - {section.grade.name}{section.name} - {period.name}',
                          section=section,
                          period=period,
                          students=students,
                          subjects=subjects,
                          grades_data=grades_data)

@reports.route('/student/<int:student_id>/period/<int:period_id>')
@login_required
def student_report(student_id, period_id):
    student = Student.query.get_or_404(student_id)
    period = Period.query.get_or_404(period_id)
    
    # Verificar acceso
    if not current_user.is_admin():
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        
        if not teacher:
            flash('No se encontró un perfil de profesor para este usuario', 'warning')
            return redirect(url_for('auth.logout'))
        
        # Verificar si el profesor tiene asignaciones en la sección del estudiante
        assignment = TeacherAssignment.query.filter_by(
            teacher_id=teacher.id,
            section_id=student.section_id,
            academic_year_id=period.academic_year_id
        ).first()
        
        if not assignment:
            flash('No tienes permiso para ver este estudiante', 'danger')
            return redirect(url_for('reports.index'))
    
    # Obtener asignaturas para la sección del estudiante
    subject_ids = db.session.query(TeacherAssignment.subject_id).filter_by(
        section_id=student.section_id,
        academic_year_id=period.academic_year_id
    ).distinct().all()
    
    subject_ids = [s[0] for s in subject_ids]
    subjects = Subject.query.filter(Subject.id.in_(subject_ids)).order_by(Subject.name).all()
    
    # Obtener calificaciones detalladas
    grades_data = {}
    final_grades = {}
    
    for subject in subjects:
        # Obtener tipos de calificación para esta asignatura
        grade_types = GradeType.query.filter_by(
            subject_id=subject.id,
            period_id=period.id
        ).order_by(GradeType.name).all()
        
        grades_data[subject.id] = {}
        
        for grade_type in grade_types:
            grade = StudentGrade.query.filter_by(
                student_id=student.id,
                subject_id=subject.id,
                grade_type_id=grade_type.id,
                period_id=period.id
            ).first()
            
            if grade:
                grades_data[subject.id][grade_type.id] = {
                    'name': grade_type.name,
                    'value': grade.value,
                    'weight': grade_type.weight
                }
        
        # Obtener calificación final
        final_grade = FinalGrade.query.filter_by(
            student_id=student.id,
            subject_id=subject.id,
            period_id=period.id
        ).first()
        
        if final_grade:
            final_grades[subject.id] = final_grade.value
    
    return render_template('reports/student_report.html',
                          title=f'Reporte - {student.first_name} {student.last_name} - {period.name}',
                          student=student,
                          period=period,
                          subjects=subjects,
                          grades_data=grades_data,
                          final_grades=final_grades)

@reports.route('/export/excel/section/<int:section_id>/period/<int:period_id>')
@login_required
def export_section_excel(section_id, period_id):
    section = Section.query.get_or_404(section_id)
    period = Period.query.get_or_404(period_id)
    
    # Verificar acceso (mismo código que en section_report)
    if not current_user.is_admin():
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        
        if not teacher:
            flash('No se encontró un perfil de profesor para este usuario', 'warning')
            return redirect(url_for('auth.logout'))
        
        assignment = TeacherAssignment.query.filter_by(
            teacher_id=teacher.id,
            section_id=section_id,
            academic_year_id=period.academic_year_id
        ).first()
        
        if not assignment:
            flash('No tienes permiso para exportar esta sección', 'danger')
            return redirect(url_for('reports.index'))
    
    # Obtener estudiantes de la sección
    students = Student.query.filter_by(
        section_id=section_id,
        is_active=True
    ).order_by(Student.last_name).all()
    
    # Obtener asignaturas para esta sección
    subject_ids = db.session.query(TeacherAssignment.subject_id).filter_by(
        section_id=section_id,
        academic_year_id=period.academic_year_id
    ).distinct().all()
    
    subject_ids = [s[0] for s in subject_ids]
    subjects = Subject.query.filter(Subject.id.in_(subject_ids)).order_by(Subject.name).all()
    
    # Crear DataFrame para Excel
    data = []
    for student in students:
        row = {
            'ID': student.student_id,
            'Apellidos': student.last_name,
            'Nombres': student.first_name
        }
        
        # Añadir calificaciones por asignatura
        for subject in subjects:
            final_grade = FinalGrade.query.filter_by(
                student_id=student.id,
                subject_id=subject.id,
                period_id=period.id
            ).first()
            
            if final_grade:
                row[subject.name] = final_grade.value
            else:
                row[subject.name] = ''
        
        data.append(row)
    
    # Crear Excel
    df = pd.DataFrame(data)
    
    # Crear archivo Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=f'{section.grade.name}{section.name}', index=False)
    
    output.seek(0)
    
    # Generar nombre de archivo
    filename = f'Calificaciones_{section.grade.name}{section.name}_{period.name}.xlsx'
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@reports.route('/export/pdf/section/<int:section_id>/period/<int:period_id>')
@login_required
def export_section_pdf(section_id, period_id):
    section = Section.query.get_or_404(section_id)
    period = Period.query.get_or_404(period_id)
    
    # Verificar acceso (mismo código que en section_report)
    if not current_user.is_admin():
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        
        if not teacher:
            flash('No se encontró un perfil de profesor para este usuario', 'warning')
            return redirect(url_for('auth.logout'))
        
        assignment = TeacherAssignment.query.filter_by(
            teacher_id=teacher.id,
            section_id=section_id,
            academic_year_id=period.academic_year_id
        ).first()
        
        if not assignment:
            flash('No tienes permiso para exportar esta sección', 'danger')
            return redirect(url_for('reports.index'))
    
    # Obtener estudiantes de la sección
    students = Student.query.filter_by(
        section_id=section_id,
        is_active=True
    ).order_by(Student.last_name).all()
    
    # Obtener asignaturas para esta sección
    subject_ids = db.session.query(TeacherAssignment.subject_id).filter_by(
        section_id=section_id,
        academic_year_id=period.academic_year_id
    ).distinct().all()
    
    subject_ids = [s[0] for s in subject_ids]
    subjects = Subject.query.filter(Subject.id.in_(subject_ids)).order_by(Subject.name).all()
    
    # Crear archivo temporal
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        temp_filename = temp_file.name
    
    # Crear PDF con ReportLab
    doc = SimpleDocTemplate(temp_filename, pagesize=letter)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    
    # Título
    elements.append(Paragraph(f"Reporte de Calificaciones", title_style))
    elements.append(Paragraph(f"Grado: {section.grade.name} Sección: {section.name}", subtitle_style))
    elements.append(Paragraph(f"Período: {period.name}", subtitle_style))
    
    # Datos para la tabla
    data = [['ID', 'Apellidos', 'Nombres'] + [subject.name for subject in subjects]]
    
    for student in students:
        row = [
            student.student_id,
            student.last_name,
            student.first_name
        ]
        
        # Añadir calificaciones por asignatura
        for subject in subjects:
            final_grade = FinalGrade.query.filter_by(
                student_id=student.id,
                subject_id=subject.id,
                period_id=period.id
            ).first()
            
            if final_grade:
                row.append(str(final_grade.value))
            else:
                row.append('')
        
        data.append(row)
    
    # Crear tabla
    table = Table(data)
    
    # Estilo de la tabla
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    
    table.setStyle(style)
    elements.append(table)
    
    # Construir PDF
    doc.build(elements)
    
    # Generar nombre de archivo
    filename = f'Calificaciones_{section.grade.name}{section.name}_{period.name}.pdf'
    
    return send_file(
        temp_filename,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

@reports.route('/export/pdf/student/<int:student_id>/period/<int:period_id>')
@login_required
def export_student_pdf(student_id, period_id):
    student = Student.query.get_or_404(student_id)
    period = Period.query.get_or_404(period_id)
    
    # Verificar acceso (mismo código que en student_report)
    if not current_user.is_admin():
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        
        if not teacher:
            flash('No se encontró un perfil de profesor para este usuario', 'warning')
            return redirect(url_for('auth.logout'))
        
        assignment = TeacherAssignment.query.filter_by(
            teacher_id=teacher.id,
            section_id=student.section_id,
            academic_year_id=period.academic_year_id
        ).first()
        
        if not assignment:
            flash('No tienes permiso para exportar este estudiante', 'danger')
            return redirect(url_for('reports.index'))
    
    # Obtener asignaturas para la sección del estudiante
    subject_ids = db.session.query(TeacherAssignment.subject_id).filter_by(
        section_id=student.section_id,
        academic_year_id=period.academic_year_id
    ).distinct().all()
    
    subject_ids = [s[0] for s in subject_ids]
    subjects = Subject.query.filter(Subject.id.in_(subject_ids)).order_by(Subject.name).all()
    
    # Crear archivo temporal
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        temp_filename = temp_file.name
    
    # Crear PDF con ReportLab
    doc = SimpleDocTemplate(temp_filename, pagesize=letter)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Título
    elements.append(Paragraph(f"Boleta de Calificaciones", title_style))
    elements.append(Paragraph(f"Estudiante: {student.first_name} {student.last_name}", subtitle_style))
    elements.append(Paragraph(f"ID: {student.student_id}", normal_style))
    elements.append(Paragraph(f"Grado: {student.section.grade.name} Sección: {student.section.name}", normal_style))
    elements.append(Paragraph(f"Período: {period.name}", normal_style))
    elements.append(Paragraph(" ", normal_style))  # Espacio
    
    # Datos para la tabla
    data = [['Asignatura', 'Calificación']]
    
    for subject in subjects:
        final_grade = FinalGrade.query.filter_by(
            student_id=student.id,
            subject_id=subject.id,
            period_id=period.id
        ).first()
        
        if final_grade:
            data.append([subject.name, str(final_grade.value)])
        else:
            data.append([subject.name, ''])
    
    # Calcular promedio
    final_grades = [row[1] for row in data[1:] if row[1]]
    if final_grades:
        try:
            average = sum(float(grade) for grade in final_grades) / len(final_grades)
            data.append(['Promedio', f'{average:.2f}'])
        except ValueError:
            data.append(['Promedio', 'N/A'])
    
    # Crear tabla
    table = Table(data)
    
    # Estilo de la tabla
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    
    table.setStyle(style)
    elements.append(table)
    
    # Construir PDF
    doc.build(elements)
    
    # Generar nombre de archivo
    filename = f'Boleta_{student.last_name}_{student.first_name}_{period.name}.pdf'
    
    return send_file(
        temp_filename,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )
