from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from app.models import Usuario, Curso, Estudiante, Calificacion
from app import db
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import tempfile
import os

admin = Blueprint('admin', __name__)

@admin.route('/dashboard')
@login_required
def dashboard():
    if current_user.tipo != 'admin':
        flash('Acceso no autorizado')
        return redirect(url_for('auth.login'))
    
    cursos = Curso.query.all()
    profesores = Usuario.query.filter_by(tipo='profesor').all()
    estudiantes = Estudiante.query.all()
    
    return render_template('admin/dashboard.html', 
                          cursos=cursos, 
                          profesores=profesores, 
                          estudiantes=estudiantes)

@admin.route('/calificaciones/pendientes')
@login_required
def calificaciones_pendientes():
    if current_user.tipo != 'admin':
        flash('Acceso no autorizado')
        return redirect(url_for('auth.login'))
    
    calificaciones = Calificacion.query.filter_by(aprobada=False).all()
    return render_template('admin/calificaciones_pendientes.html', calificaciones=calificaciones)

@admin.route('/calificacion/aprobar/<int:calificacion_id>')
@login_required
def aprobar_calificacion(calificacion_id):
    if current_user.tipo != 'admin':
        flash('Acceso no autorizado')
        return redirect(url_for('auth.login'))
    
    calificacion = Calificacion.query.get_or_404(calificacion_id)
    calificacion.aprobada = True
    db.session.commit()
    
    flash('Calificación aprobada correctamente')
    return redirect(url_for('admin.calificaciones_pendientes'))

@admin.route('/reportes')
@login_required
def reportes():
    if current_user.tipo != 'admin':
        flash('Acceso no autorizado')
        return redirect(url_for('auth.login'))
    
    cursos = Curso.query.all()
    return render_template('admin/reportes.html', cursos=cursos)

@admin.route('/reporte/excel/<int:curso_id>')
@login_required
def generar_excel(curso_id):
    if current_user.tipo != 'admin':
        flash('Acceso no autorizado')
        return redirect(url_for('auth.login'))
    
    curso = Curso.query.get_or_404(curso_id)
    
    # Obtener calificaciones aprobadas del curso
    calificaciones = Calificacion.query.filter_by(curso_id=curso_id, aprobada=True).all()
    
    # Crear DataFrame con pandas
    data = []
    for cal in calificaciones:
        estudiante = Estudiante.query.get(cal.estudiante_id)
        data.append({
            'Matrícula': estudiante.matricula,
            'Nombre': f"{estudiante.nombre} {estudiante.apellido}",
            'Calificación': cal.valor,
            'Fecha': cal.fecha.strftime('%d/%m/%Y'),
            'Observación': cal.observacion
        })
    
    df = pd.DataFrame(data)
    
    # Crear archivo Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=f'Calificaciones {curso.nombre}', index=False)
    
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f'Calificaciones_{curso.codigo}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@admin.route('/reporte/pdf/<int:curso_id>')
@login_required
def generar_pdf(curso_id):
    if current_user.tipo != 'admin':
        flash('Acceso no autorizado')
        return redirect(url_for('auth.login'))
    
    curso = Curso.query.get_or_404(curso_id)
    
    # Obtener calificaciones aprobadas del curso
    calificaciones = Calificacion.query.filter_by(curso_id=curso_id, aprobada=True).all()
    
    # Crear archivo temporal
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        temp_filename = temp_file.name
    
    # Crear PDF con ReportLab
    doc = SimpleDocTemplate(temp_filename, pagesize=letter)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    
    # Título
    elements.append(Paragraph(f"Reporte de Calificaciones: {curso.nombre} ({curso.codigo})", title_style))
    
    # Datos para la tabla
    data = [['Matrícula', 'Nombre', 'Calificación', 'Fecha', 'Observación']]
    
    for cal in calificaciones:
        estudiante = Estudiante.query.get(cal.estudiante_id)
        data.append([
            estudiante.matricula,
            f"{estudiante.nombre} {estudiante.apellido}",
            str(cal.valor),
            cal.fecha.strftime('%d/%m/%Y'),
            cal.observacion or ""
        ])
    
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
    
    # Enviar archivo
    return send_file(
        temp_filename,
        as_attachment=True,
        download_name=f'Calificaciones_{curso.codigo}.pdf',
        mimetype='application/pdf'
    )

@admin.route('/usuarios')
@login_required
def gestionar_usuarios():
    if current_user.tipo != 'admin':
        flash('Acceso no autorizado')
        return redirect(url_for('auth.login'))
    
    usuarios = Usuario.query.all()
    return render_template('admin/usuarios.html', usuarios=usuarios)

@admin.route('/usuario/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_usuario():
    if current_user.tipo != 'admin':
        flash('Acceso no autorizado')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        tipo = request.form.get('tipo')
        
        # Verificar si el usuario ya existe
        usuario_existente = Usuario.query.filter_by(username=username).first()
        if usuario_existente:
            flash('El nombre de usuario ya está en uso')
            return redirect(url_for('admin.nuevo_usuario'))
        
        # Crear nuevo usuario
        nuevo_usuario = Usuario(username=username, email=email, tipo=tipo)
        nuevo_usuario.set_password(password)
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash('Usuario creado correctamente')
        return redirect(url_for('admin.gestionar_usuarios'))
    
    return render_template('admin/nuevo_usuario.html')

@admin.route('/estudiantes')
@login_required
def gestionar_estudiantes():
    if current_user.tipo != 'admin':
        flash('Acceso no autorizado')
        return redirect(url_for('auth.login'))
    
    estudiantes = Estudiante.query.all()
    return render_template('admin/estudiantes.html', estudiantes=estudiantes)

@admin.route('/estudiante/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_estudiante():
    if current_user.tipo != 'admin':
        flash('Acceso no autorizado')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        matricula = request.form.get('matricula')
        
        # Verificar si la matrícula ya existe
        estudiante_existente = Estudiante.query.filter_by(matricula=matricula).first()
        if estudiante_existente:
            flash('La matrícula ya está registrada')
            return redirect(url_for('admin.nuevo_estudiante'))
        
        # Crear nuevo estudiante
        nuevo_estudiante = Estudiante(nombre=nombre, apellido=apellido, matricula=matricula)
        
        db.session.add(nuevo_estudiante)
        db.session.commit()
        
        flash('Estudiante registrado correctamente')
        return redirect(url_for('admin.gestionar_estudiantes'))
    
    return render_template('admin/nuevo_estudiante.html')

@admin.route('/cursos')
@login_required
def gestionar_cursos():
    if current_user.tipo != 'admin':
        flash('Acceso no autorizado')
        return redirect(url_for('auth.login'))
    
    cursos = Curso.query.all()
    return render_template('admin/cursos.html', cursos=cursos)

@admin.route('/curso/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_curso():
    if current_user.tipo != 'admin':
        flash('Acceso no autorizado')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        codigo = request.form.get('codigo')
        profesor_id = request.form.get('profesor_id')
        
        # Verificar si el código ya existe
        curso_existente = Curso.query.filter_by(codigo=codigo).first()
        if curso_existente:
            flash('El código de curso ya está en uso')
            return redirect(url_for('admin.nuevo_curso'))
        
        # Crear nuevo curso
        nuevo_curso = Curso(nombre=nombre, codigo=codigo, profesor_id=profesor_id)
        
        db.session.add(nuevo_curso)
        db.session.commit()
        
        flash('Curso creado correctamente')
        return redirect(url_for('admin.gestionar_cursos'))
    
    profesores = Usuario.query.filter_by(tipo='profesor').all()
    return render_template('admin/nuevo_curso.html', profesores=profesores)
