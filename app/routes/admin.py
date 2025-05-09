from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, jsonify
from io import BytesIO
import pandas as pd
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from datetime import datetime 
from wtforms import StringField, TextAreaField, IntegerField, SelectField, BooleanField, PasswordField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, ValidationError
from app.models.users import User
from app.models.academic import AcademicYear, Period, Grade, Section, Subject, Student, Teacher, TeacherAssignment, Admin
from app.models.grades import GradeType, StudentGrade, FinalGrade
from app.forms.admin_forms import UserForm, AcademicYearForm, PeriodForm, GradeForm, SectionForm, SubjectForm, StudentForm, TeacherForm, TeacherAssignmentForm, SettingsForm, GradeTypeForm, StudentGradeForm, FinalGradeForm, TeacherPreRegistrationForm
from app import db

admin = Blueprint('admin', __name__)

@admin.before_request
def check_admin():
    if not current_user.is_authenticated or not current_user.is_admin():
        flash('Acceso no autorizado. Se requieren privilegios de administrador.', 'danger')
        return redirect(url_for('auth.login'))

@admin.route('/dashboard')
@login_required
def dashboard():
    # Estadísticas para el dashboard
    stats = {
        'students': Student.query.filter_by(is_active=True).count(),
        'teachers': Teacher.query.count(),
        'subjects': Subject.query.count(),
        'grades': Grade.query.count()
    }
    
    # Año académico activo
    active_year = AcademicYear.query.filter_by(is_active=True).first()
    
    return render_template('admin/dashboard.html', title='Panel de Administración', stats=stats, active_year=active_year)

# Rutas para gestión de usuarios
@admin.route('/users')
@login_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', title='Gestión de Usuarios', users=users)

@admin.route('/users/new', methods=['GET', 'POST'])
@login_required
def new_user():
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        
        # Si es profesor, crear perfil de profesor
        if form.role.data == 'teacher':
            teacher = Teacher(user=user, specialization=form.specialization.data)
            db.session.add(teacher)
            
        db.session.commit()
        flash('Usuario creado correctamente', 'success')
        return redirect(url_for('admin.users'))
        
    return render_template('admin/user_form.html', title='Nuevo Usuario', form=form)

@admin.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    user = User.query.get_or_404(id)
    form = UserForm(obj=user)
    
    # No permitir cambiar el rol si es el único administrador
    if user.is_admin() and User.query.filter_by(role='admin').count() == 1:
        form.role.render_kw = {'disabled': 'disabled'}
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        
        # Solo cambiar el rol si no es el único administrador
        if not (user.is_admin() and User.query.filter_by(role='admin').count() == 1):
            user.role = form.role.data
        
        if form.password.data:
            user.set_password(form.password.data)
            
        # Actualizar o crear perfil de profesor
        if user.role == 'teacher':
            if user.teacher_profile:
                user.teacher_profile.specialization = form.specialization.data
            else:
                teacher = Teacher(user=user, specialization=form.specialization.data)
                db.session.add(teacher)
                
        db.session.commit()
        flash('Usuario actualizado correctamente', 'success')
        return redirect(url_for('admin.users'))
        
    # Si es profesor, cargar especialización
    if user.teacher_profile:
        form.specialization.data = user.teacher_profile.specialization
        
    return render_template('admin/user_form.html', title='Editar Usuario', form=form, user=user)

@admin.route('/users/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    user = User.query.get_or_404(id)
    
    # No permitir eliminar el último administrador
    if user.is_admin() and User.query.filter_by(role='admin').count() == 1:
        flash('No se puede eliminar el único usuario administrador', 'danger')
        return redirect(url_for('admin.users'))
        
    # No permitir eliminar al usuario actual
    if user.id == current_user.id:
        flash('No puedes eliminar tu propio usuario', 'danger')
        return redirect(url_for('admin.users'))
        
    db.session.delete(user)
    db.session.commit()
    flash('Usuario eliminado correctamente', 'success')
    return redirect(url_for('admin.users'))

# Rutas para gestión de años académicos
@admin.route('/academic-years')
@login_required
def academic_years():
    years = AcademicYear.query.all()
    return render_template('admin/academic_years.html', title='Años Académicos', years=years)

@admin.route('/users/<int:id>/resend-invitation', methods=['POST'])
@login_required
def resend_invitation(id):
    user = User.query.get_or_404(id)
    
    if user.is_registered:
        flash('Este usuario ya ha completado su registro', 'warning')
        return redirect(url_for('admin.users'))
    
    # Aquí iría la lógica para enviar el correo electrónico
    # Por ahora solo mostramos un mensaje de éxito
    
    flash(f'Se ha reenviado la invitación a {user.email}', 'success')
    return redirect(url_for('admin.users'))


@admin.route('/academic-years/new', methods=['GET', 'POST'])
@login_required
def new_academic_year():
    form = AcademicYearForm()
    if form.validate_on_submit():
        # Si se marca como activo, desactivar los demás
        if form.is_active.data:
            AcademicYear.query.update({AcademicYear.is_active: False})
            
        year = AcademicYear(
            name=form.name.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            is_active=form.is_active.data
        )
        db.session.add(year)
        db.session.commit()
        flash('Año académico creado correctamente', 'success')
        return redirect(url_for('admin.academic_years'))
        
    return render_template('admin/academic_year_form.html', title='Nuevo Año Académico', form=form)

# Rutas para gestión de períodos académicos
@admin.route('/periods')
@login_required
def periods():
    periods = Period.query.all()
    return render_template('admin/periods.html', title='Períodos Académicos', periods=periods)

@admin.route('/periods/new', methods=['GET', 'POST'])
@login_required
def new_period():
    form = PeriodForm()
    # Cargar años académicos para el select
    form.academic_year_id.choices = [(y.id, y.name) for y in AcademicYear.query.all()]
    
    if form.validate_on_submit():
        period = Period(
            name=form.name.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            academic_year_id=form.academic_year_id.data,
            weight=form.weight.data
        )
        db.session.add(period)
        db.session.commit()
        flash('Período académico creado correctamente', 'success')
        return redirect(url_for('admin.periods'))
        
    return render_template('admin/period_form.html', title='Nuevo Período', form=form)

@admin.route('/periods/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_period(id):
    period = Period.query.get_or_404(id)
    form = PeriodForm(obj=period)
    form.academic_year_id.choices = [(y.id, y.name) for y in AcademicYear.query.all()]
    
    if form.validate_on_submit():
        period.name = form.name.data
        period.start_date = form.start_date.data
        period.end_date = form.end_date.data
        period.academic_year_id = form.academic_year_id.data
        period.weight = form.weight.data
        
        db.session.commit()
        flash('Período académico actualizado correctamente', 'success')
        return redirect(url_for('admin.periods'))
        
    return render_template('admin/period_form.html', title='Editar Período', form=form)

@admin.route('/periods/<int:id>/delete', methods=['POST'])
@login_required
def delete_period(id):
    period = Period.query.get_or_404(id)
    
    # Verificar si hay calificaciones asociadas a este período
    if StudentGrade.query.filter_by(period_id=id).first() or FinalGrade.query.filter_by(period_id=id).first():
        flash('No se puede eliminar este período porque tiene calificaciones asociadas', 'danger')
        return redirect(url_for('admin.periods'))
    
    db.session.delete(period)
    db.session.commit()
    flash('Período académico eliminado correctamente', 'success')
    return redirect(url_for('admin.periods'))

# Rutas para gestión de grados y secciones
@admin.route('/grades')
@login_required
def grades():
    grades = Grade.query.all()
    return render_template('admin/grades.html', title='Grados y Secciones', grades=grades)

# Ruta para obtener secciones de un grado
@admin.route('/grades/<int:id>/sections', methods=['GET'])
@login_required
def get_grade_sections(id):
    grade = Grade.query.get_or_404(id)
    sections = [{'id': s.id, 'name': s.name} for s in grade.sections]
    return jsonify({'sections': sections})

# Ruta para obtener detalles de un grado por AJAX
@admin.route('/grades/<int:id>/details', methods=['GET'])
@login_required
def get_grade_details(id):
    grade = Grade.query.get_or_404(id)
    sections = [{'id': s.id, 'name': s.name} for s in grade.sections]
    
    return jsonify({
        'id': grade.id,
        'name': grade.name,
        'level': grade.level,
        'sections': sections
    })

# Ruta para crear un grado por AJAX
@admin.route('/grades/create', methods=['POST'])
@login_required
def create_grade_ajax():
    try:
        name = request.form.get('name')
        level = request.form.get('level')
        sections = request.form.getlist('sections[]')
        
        if not name or not level:
            return jsonify({'success': False, 'message': 'Nombre y nivel son requeridos'}), 400
            
        grade = Grade(name=name, level=level)
        db.session.add(grade)
        db.session.flush()  # Para obtener el ID del grado antes de crear las secciones
        
        # Si no se especificaron secciones, crear una sección predeterminada "U"
        if not sections:
            sections = ["U"]
            
        # Crear secciones para el grado
        for section_name in sections:
            if section_name.strip():  # Ignorar secciones vacías
                section = Section(name=section_name.strip(), grade_id=grade.id)
                db.session.add(section)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Grado creado correctamente con sus secciones',
            'grade': {
                'id': grade.id,
                'name': grade.name,
                'level': grade.level,
                'sections_count': len(sections)
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Ruta para actualizar un grado por AJAX
@admin.route('/grades/<int:id>/update', methods=['POST'])
@login_required
def update_grade_ajax(id):
    try:
        grade = Grade.query.get_or_404(id)
        
        name = request.form.get('name')
        level = request.form.get('level')
        
        if not name or not level:
            return jsonify({'success': False, 'message': 'Nombre y nivel son requeridos'}), 400
            
        grade.name = name
        grade.level = level
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Grado actualizado correctamente',
            'grade': {
                'id': grade.id,
                'name': grade.name,
                'level': grade.level
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Ruta para eliminar un grado por AJAX
@admin.route('/grades/<int:id>/delete', methods=['POST'])
@login_required
def delete_grade_ajax(id):
    try:
        grade = Grade.query.get_or_404(id)
        
        # Verificar si tiene secciones con estudiantes
        for section in grade.sections:
            if section.students.count() > 0:
                return jsonify({
                    'success': False, 
                    'message': f'No se puede eliminar el grado porque la sección {section.name} tiene estudiantes asociados'
                }), 400
            
        db.session.delete(grade)  # Esto eliminará también las secciones (cascade)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Grado eliminado correctamente con todas sus secciones'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Rutas para gestión de secciones
@admin.route('/sections')
@login_required
def sections():
    # Obtener el parámetro grade_id si existe
    grade_id = request.args.get('grade_id', type=int)
    
    # Filtrar secciones por grado si se proporciona grade_id
    if grade_id:
        grade = Grade.query.get_or_404(grade_id)
        sections = Section.query.filter_by(grade_id=grade_id).all()
        return render_template('admin/sections.html', title='Secciones', sections=sections, grade=grade)
    
    # Si no hay grade_id, mostrar todas las secciones
    sections = Section.query.all()
    grades = Grade.query.all()
    return render_template('admin/sections.html', title='Secciones', sections=sections, grades=grades)

# Ruta para crear una sección por AJAX
@admin.route('/sections/create', methods=['POST'])
@login_required
def create_section_ajax():
    try:
        name = request.form.get('name')
        grade_id = request.form.get('grade_id')
        
        if not name or not grade_id:
            return jsonify({'success': False, 'message': 'Nombre y grado son requeridos'}), 400
            
        # Verificar que el grado existe
        grade = Grade.query.get_or_404(grade_id)
        
        # Verificar que no exista una sección con el mismo nombre en el mismo grado
        existing_section = Section.query.filter_by(name=name, grade_id=grade_id).first()
        if existing_section:
            return jsonify({'success': False, 'message': f'Ya existe una sección {name} en este grado'}), 400
            
        section = Section(name=name, grade_id=grade_id)
        db.session.add(section)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Sección creada correctamente',
            'section': {
                'id': section.id,
                'name': section.name,
                'grade_id': section.grade_id
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Ruta para actualizar una sección por AJAX
@admin.route('/sections/<int:id>/update', methods=['POST'])
@login_required
def update_section_ajax(id):
    try:
        section = Section.query.get_or_404(id)
        
        name = request.form.get('name')
        
        if not name:
            return jsonify({'success': False, 'message': 'Nombre es requerido'}), 400
            
        # Verificar que no exista otra sección con el mismo nombre en el mismo grado
        existing_section = Section.query.filter_by(name=name, grade_id=section.grade_id).first()
        if existing_section and existing_section.id != section.id:
            return jsonify({'success': False, 'message': f'Ya existe una sección {name} en este grado'}), 400
            
        section.name = name
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Sección actualizada correctamente',
            'section': {
                'id': section.id,
                'name': section.name
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin.route('/sections/<int:id>/delete', methods=['POST'])
@login_required
def delete_section_ajax(id):
    try:
        section = Section.query.get_or_404(id)
        
        # Verificar si tiene estudiantes
        if section.students.count() > 0:
            return jsonify({
                'success': False, 
                'message': f'No se puede eliminar la sección porque tiene {section.students.count()} estudiantes asociados'
            }), 400
            
        # Verificar que no sea la única sección del grado
        if section.grade.sections.count() == 1:
            return jsonify({
                'success': False, 
                'message': 'No se puede eliminar la única sección del grado'
            }), 400
            
        db.session.delete(section)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Sección eliminada correctamente'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Rutas para gestión de asignaturas
@admin.route('/subjects')
@login_required
def subjects():
    # Obtener todas las asignaturas
    subjects = Subject.query.all()
    
    # Obtener todos los grados para los formularios de creación y edición
    grades = Grade.query.order_by(Grade.level, Grade.name).all()
    
    return render_template('admin/subjects.html', title='Asignaturas', subjects=subjects, grades=grades)

@admin.route('/subjects/new', methods=['POST'])
@login_required
def new_subject():
    # Obtener datos del formulario
    name = request.form.get('name')
    code = request.form.get('code')
    grade_ids = request.form.getlist('grades')  # Nota: getlist para obtener múltiples valores
    
    # Validar datos
    if not name or not code or not grade_ids:
        flash('Todos los campos son obligatorios', 'danger')
        return redirect(url_for('admin.subjects'))
    
    # Verificar si ya existe una asignatura con el mismo código
    if Subject.query.filter_by(code=code).first():
        flash('Ya existe una asignatura con ese código', 'danger')
        return redirect(url_for('admin.subjects'))
    
    # Crear la asignatura
    subject = Subject(name=name, code=code)
    
    # Asociar los grados seleccionados
    for grade_id in grade_ids:
        grade = Grade.query.get(grade_id)
        if grade:
            subject.grades.append(grade)
    
    # Guardar en la base de datos
    db.session.add(subject)
    db.session.commit()
    
    flash('Asignatura creada correctamente', 'success')
    return redirect(url_for('admin.subjects'))

@admin.route('/subjects/<int:id>/edit', methods=['POST'])
@login_required
def edit_subject(id):
    subject = Subject.query.get_or_404(id)
    
    # Obtener datos del formulario
    name = request.form.get('name')
    code = request.form.get('code')
    grade_ids = request.form.getlist('grades')  # Nota: getlist para obtener múltiples valores
    
    # Validar datos
    if not name or not code or not grade_ids:
        flash('Todos los campos son obligatorios', 'danger')
        return redirect(url_for('admin.subjects'))
    
    # Verificar si ya existe otra asignatura con el mismo código
    existing = Subject.query.filter_by(code=code).first()
    if existing and existing.id != subject.id:
        flash('Ya existe otra asignatura con ese código', 'danger')
        return redirect(url_for('admin.subjects'))
    
    # Actualizar la asignatura
    subject.name = name
    subject.code = code
    
    # Actualizar los grados asociados
    subject.grades = []  # Eliminar asociaciones existentes
    for grade_id in grade_ids:
        grade = Grade.query.get(grade_id)
        if grade:
            subject.grades.append(grade)
    
    # Guardar en la base de datos
    db.session.commit()
    
    flash('Asignatura actualizada correctamente', 'success')
    return redirect(url_for('admin.subjects'))

@admin.route('/subjects/<int:id>/delete', methods=['POST'])
@login_required
def delete_subject(id):
    subject = Subject.query.get_or_404(id)
    
    # Verificar si hay asignaciones de profesores a esta asignatura
    if TeacherAssignment.query.filter_by(subject_id=id).first():
        flash('No se puede eliminar esta asignatura porque tiene asignaciones de profesores', 'danger')
        return redirect(url_for('admin.subjects'))
    
    # Verificar si hay calificaciones asociadas a esta asignatura
    if StudentGrade.query.join(TeacherAssignment).filter(TeacherAssignment.subject_id == id).first():
        flash('No se puede eliminar esta asignatura porque tiene calificaciones asociadas', 'danger')
        return redirect(url_for('admin.subjects'))
    
    db.session.delete(subject)
    db.session.commit()
    flash('Asignatura eliminada correctamente', 'success')
    return redirect(url_for('admin.subjects'))

# Rutas para gestión de estudiantes
@admin.route('/students')
@login_required
def students():
    # Obtener parámetros de filtrado
    grade_id = request.args.get('grade_id', type=int)
    section_id = request.args.get('section_id', type=int)
    search = request.args.get('search', '')
    
    # Consulta base
    query = Student.query
    
    # Aplicar filtros
    if grade_id:
        sections = Section.query.filter_by(grade_id=grade_id).all()
        section_ids = [section.id for section in sections]
        query = query.filter(Student.section_id.in_(section_ids))
    
    if section_id:
        query = query.filter_by(section_id=section_id)
    
    if search:
        query = query.filter(
            db.or_(
                Student.first_name.ilike(f'%{search}%'),
                Student.last_name.ilike(f'%{search}%'),
                Student.student_id.ilike(f'%{search}%')
            )
        )
    
    # Ordenar y paginar
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Student.last_name, Student.first_name).paginate(
        page=page, per_page=20, error_out=False
    )
    students = pagination.items
    
    # Obtener grados y secciones para los filtros
    grades = Grade.query.all()
    sections = Section.query.filter_by(grade_id=grade_id).all() if grade_id else []
    
    # Obtener año académico activo y asignaturas
    active_year = AcademicYear.query.filter_by(is_active=True).first()
    subjects = Subject.query.all()
    
    # Crear formulario para nuevo estudiante
    form = StudentForm()
    form.section_id.choices = [(s.id, f"{s.grade.name} '{s.name}'") for s in Section.query.join(Grade).all()]
    
    # Configuración
    passing_grade = 70  # Nota de aprobación (esto podría venir de la configuración)
    
    return render_template(
        'admin/students.html', 
        title='Estudiantes', 
        students=students,
        pagination=pagination,
        grades=grades,
        sections=sections,
        active_year=active_year,
        subjects=subjects,
        form=form,
        passing_grade=passing_grade,
        now=datetime.now()
    )

# Ruta para crear un nuevo estudiante
@admin.route('/students/new', methods=['POST'])
@login_required
def new_student():
    form = StudentForm()
    form.section_id.choices = [(s.id, f"{s.grade.name} '{s.name}'") for s in Section.query.join(Grade).all()]
    
    if form.validate_on_submit():
        student = Student(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            student_id=form.student_id.data,
            birth_date=form.birth_date.data,
            gender=form.gender.data,
            address=form.address.data,
            phone=form.phone.data,
            email=form.email.data,
            section_id=form.section_id.data,
            is_active=form.is_active.data
        )
        db.session.add(student)
        db.session.commit()
        flash('Estudiante creado correctamente', 'success')
        return redirect(url_for('admin.students'))
    
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'Error en el campo {getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('admin.students'))

# Ruta para editar un estudiante
@admin.route('/students/<int:id>/edit', methods=['POST'])
@login_required
def edit_student(id):
    student = Student.query.get_or_404(id)
    form = StudentForm()
    form.section_id.choices = [(s.id, f"{s.grade.name} '{s.name}'") for s in Section.query.join(Grade).all()]
    
    # Guardar el ID de la base de datos para validación
    form.student_id_db = student.id
    
    if form.validate_on_submit():
        student.first_name = form.first_name.data
        student.last_name = form.last_name.data
        student.student_id = form.student_id.data
        student.birth_date = form.birth_date.data
        student.gender = form.gender.data
        student.address = form.address.data
        student.phone = form.phone.data
        student.email = form.email.data
        student.section_id = form.section_id.data
        student.is_active = form.is_active.data
        
        db.session.commit()
        flash('Estudiante actualizado correctamente', 'success')
        return redirect(url_for('admin.students'))
    
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'Error en el campo {getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('admin.students'))

# Ruta para eliminar un estudiante
@admin.route('/students/<int:id>/delete', methods=['POST'])
@login_required
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash('Estudiante eliminado correctamente', 'success')
    return redirect(url_for('admin.students'))

# Ruta para obtener detalles de un estudiante (para el modal de ver)
@admin.route('/students/<int:id>/details', methods=['GET'])
@login_required
def get_student_details(id):
    student = Student.query.get_or_404(id)
    return render_template('admin/partials/student_details.html', student=student)

# Ruta para obtener el formulario de edición de un estudiante
@admin.route('/students/<int:id>/edit-form', methods=['GET'])
@login_required
def get_student_edit_form(id):
    student = Student.query.get_or_404(id)
    form = StudentForm(obj=student)
    form.section_id.choices = [(s.id, f"{s.grade.name} '{s.name}'") for s in Section.query.join(Grade).all()]
    return render_template('admin/partials/student_edit_form.html', form=form, student=student)

# Ruta para obtener el formulario de confirmación de eliminación
@admin.route('/students/<int:id>/delete-form', methods=['GET'])
@login_required
def get_student_delete_form(id):
    student = Student.query.get_or_404(id)
    return render_template('admin/partials/student_delete_form.html', student=student)

# Ruta para editar un estudiante (versión AJAX)
@admin.route('/students/<int:id>/edit-ajax', methods=['POST'])
@login_required
def edit_student_ajax(id):
    student = Student.query.get_or_404(id)
    form = StudentForm()
    form.section_id.choices = [(s.id, f"{s.grade.name} '{s.name}'") for s in Section.query.join(Grade).all()]
    
    if form.validate_on_submit():
        student.first_name = form.first_name.data
        student.last_name = form.last_name.data
        student.student_id = form.student_id.data
        student.birth_date = form.birth_date.data
        student.gender = form.gender.data
        student.address = form.address.data
        student.phone = form.phone.data
        student.email = form.email.data
        student.section_id = form.section_id.data
        student.is_active = form.is_active.data
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Estudiante actualizado correctamente'})
    
    errors = []
    for field, field_errors in form.errors.items():
        for error in field_errors:
            errors.append(f"{getattr(form, field).label.text}: {error}")
    
    return jsonify({'success': False, 'message': 'Error en el formulario', 'errors': errors})

# Ruta para eliminar un estudiante (versión AJAX)
@admin.route('/students/<int:id>/delete-ajax', methods=['POST'])
@login_required
def delete_student_ajax(id):
    student = Student.query.get_or_404(id)
    
    try:
        db.session.delete(student)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Estudiante eliminado correctamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error al eliminar el estudiante: {str(e)}'})
    
# Rutas para iframes
@admin.route('/students/<int:id>/view-iframe')
@login_required
def student_view_iframe(id):
    student = Student.query.get_or_404(id)
    return render_template('admin/iframes/student_view.html', student=student, now=datetime.now())

@admin.route('/students/<int:id>/edit-iframe')
@login_required
def student_edit_iframe(id):
    student = Student.query.get_or_404(id)
    form = StudentForm(obj=student)
    form.section_id.choices = [(s.id, f"{s.grade.name} '{s.name}'") for s in Section.query.join(Grade).order_by(Grade.level, Section.name).all()]
    grades = Grade.query.all()
    return render_template('admin/iframes/student_edit.html', form=form, student=student, grades=grades)

@admin.route('/students/<int:id>/edit-iframe-submit', methods=['POST'])
@login_required
def student_edit_iframe_submit(id):
    student = Student.query.get_or_404(id)
    form = StudentForm()
    form.section_id.choices = [(s.id, f"{s.grade.name} '{s.name}'") for s in Section.query.join(Grade).order_by(Grade.level, Section.name).all()]
    
    if form.validate_on_submit():
        student.first_name = form.first_name.data
        student.last_name = form.last_name.data
        student.student_id = form.student_id.data
        student.birth_date = form.birth_date.data
        student.gender = form.gender.data
        student.address = form.address.data
        student.phone = form.phone.data
        student.email = form.email.data
        student.section_id = form.section_id.data
        student.is_active = form.is_active.data
        
        try:
            db.session.commit()
            flash('Estudiante actualizado correctamente', 'success')
            return render_template('admin/iframes/success.html', message='Estudiante actualizado correctamente', modal_id='editStudentModal', reload=True)
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el estudiante: {str(e)}', 'danger')
    
    return render_template('admin/iframes/student_edit.html', form=form, student=student, grades=Grade.query.all())

@admin.route('/students/<int:id>/delete-iframe')
@login_required
def student_delete_iframe(id):
    student = Student.query.get_or_404(id)
    return render_template('admin/iframes/student_delete.html', student=student)

@admin.route('/students/<int:id>/delete-iframe-submit', methods=['POST'])
@login_required
def student_delete_iframe_submit(id):
    student = Student.query.get_or_404(id)
    
    # Verificar si hay calificaciones asociadas a este estudiante
    if StudentGrade.query.filter_by(student_id=id).first() or FinalGrade.query.filter_by(student_id=id).first():
        flash('No se puede eliminar este estudiante porque tiene calificaciones asociadas', 'danger')
        return render_template('admin/iframes/student_delete.html', student=student)
    
    try:
        db.session.delete(student)
        db.session.commit()
        flash('Estudiante eliminado correctamente', 'success')
        return render_template('admin/iframes/success.html', message='Estudiante eliminado correctamente', modal_id='deleteStudentModal', reload=True)
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el estudiante: {str(e)}', 'danger')
        return render_template('admin/iframes/student_delete.html', student=student)

# Ruta para importar estudiantes desde Excel
@admin.route('/students/import', methods=['POST'])
@login_required
def import_students():
    if 'file' not in request.files:
        flash('No se ha seleccionado ningún archivo', 'danger')
        return redirect(url_for('admin.students'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No se ha seleccionado ningún archivo', 'danger')
        return redirect(url_for('admin.students'))
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        flash('El archivo debe ser de tipo Excel (.xlsx, .xls)', 'danger')
        return redirect(url_for('admin.students'))
    
    section_id = request.form.get('section_id', type=int)
    if not section_id:
        flash('Debe seleccionar una sección', 'danger')
        return redirect(url_for('admin.students'))
    
    is_active = 'is_active' in request.form
    
    try:
        # Leer archivo Excel
        df = pd.read_excel(file)
        
        # Validar columnas requeridas
        required_columns = ['Cédula', 'Nombre', 'Apellido']
        for col in required_columns:
            if col not in df.columns:
                flash(f'El archivo no contiene la columna requerida: {col}', 'danger')
                return redirect(url_for('admin.students'))
        
        # Procesar datos
        count = 0
        errors = 0
        for _, row in df.iterrows():
            try:
                # Verificar si ya existe un estudiante con esa cédula
                existing = Student.query.filter_by(student_id=str(row['Cédula'])).first()
                if existing:
                    flash(f'Ya existe un estudiante con la cédula {row["Cédula"]}', 'warning')
                    errors += 1
                    continue
                
                # Crear nuevo estudiante
                student = Student(
                    first_name=row['Nombre'],
                    last_name=row['Apellido'],
                    student_id=str(row['Cédula']),
                    section_id=section_id,
                    is_active=is_active
                )
                
                # Campos opcionales
                if 'Fecha de Nacimiento' in df.columns and not pd.isna(row['Fecha de Nacimiento']):
                    if isinstance(row['Fecha de Nacimiento'], str):
                        student.birth_date = datetime.strptime(row['Fecha de Nacimiento'], '%d/%m/%Y').date()
                    else:
                        student.birth_date = row['Fecha de Nacimiento']
                
                if 'Género' in df.columns and not pd.isna(row['Género']):
                    student.gender = row['Género']
                
                if 'Dirección' in df.columns and not pd.isna(row['Dirección']):
                    student.address = row['Dirección']
                
                if 'Teléfono' in df.columns and not pd.isna(row['Teléfono']):
                    student.phone = str(row['Teléfono'])
                
                if 'Email' in df.columns and not pd.isna(row['Email']):
                    student.email = row['Email']
                
                db.session.add(student)
                count += 1
            except Exception as e:
                errors += 1
                flash(f'Error al procesar la fila {_+2}: {str(e)}', 'danger')
        
        db.session.commit()
        flash(f'Se importaron {count} estudiantes correctamente. Errores: {errors}', 'success')
    except Exception as e:
        flash(f'Error al procesar el archivo: {str(e)}', 'danger')
    
    return redirect(url_for('admin.students'))

# Ruta para descargar plantilla de importación
@admin.route('/students/download-template')
@login_required
def download_student_template():
    # Crear DataFrame con las columnas de ejemplo
    data = {
        'Cédula': ['12345678', '87654321'],
        'Nombre': ['Juan', 'María'],
        'Apellido': ['Pérez', 'González'],
        'Fecha de Nacimiento': ['01/01/2010', '15/05/2009'],
        'Género': ['M', 'F'],
        'Dirección': ['Calle Principal #123', 'Avenida Central #456'],
        'Teléfono': ['555-1234', '555-5678'],
        'Email': ['juan@example.com', 'maria@example.com']
    }
    df = pd.DataFrame(data)
    
    # Crear archivo Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Estudiantes')
        
        # Ajustar ancho de columnas
        worksheet = writer.sheets['Estudiantes']
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_width)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='plantilla_estudiantes.xlsx'
    )

@admin.route('/teachers/new', methods=['GET', 'POST'])
@login_required
def new_teacher():
    form = TeacherForm()
    
    if form.validate_on_submit():
        # Crear usuario primero
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role='teacher'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        
        # Crear perfil de profesor
        teacher = Teacher(
            user=user,
            specialization=form.specialization.data,
            qualification=form.qualification.data,
            phone=form.phone.data
        )
        db.session.add(teacher)
        db.session.commit()
        
        flash('Profesor creado correctamente', 'success')
        return redirect(url_for('admin.teachers'))
        
    return render_template('admin/teacher_form.html', title='Nuevo Profesor', form=form)

@admin.route('/teachers/pre-register', methods=['GET', 'POST'])
@login_required
def pre_register_teacher():
    form = TeacherPreRegistrationForm()
    if form.validate_on_submit():
        # Crear usuario sin contraseña
        user = User(
            identification_number=form.identification_number.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role='teacher',
            is_registered=False
        )
        db.session.add(user)
        
        # Crear perfil de profesor
        teacher = Teacher(
            user=user,
            specialization=form.specialization.data
        )
        db.session.add(teacher)
        
        db.session.commit()
        flash(f'Profesor pre-registrado correctamente. Cédula: {form.identification_number.data}', 'success')
        return redirect(url_for('admin.teachers'))
        
    return render_template('admin/teacher_pre_register.html', title='Pre-Registrar Profesor', form=form)

@admin.route('/teachers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_teacher(id):
    teacher = Teacher.query.get_or_404(id)
    form = TeacherPreRegistrationForm()
    
    if form.validate_on_submit():
        # Verificar si la cédula ya está en uso por otro usuario
        existing_user = User.query.filter_by(identification_number=form.identification_number.data).first()
        if existing_user and existing_user.id != teacher.user.id:
            flash('Esta cédula ya está en uso por otro usuario', 'danger')
            return redirect(url_for('admin.edit_teacher', id=id))
            
        # Verificar si el email ya está en uso por otro usuario
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user and existing_user.id != teacher.user.id:
            flash('Este email ya está en uso por otro usuario', 'danger')
            return redirect(url_for('admin.edit_teacher', id=id))
            
        # Actualizar datos
        teacher.user.identification_number = form.identification_number.data
        teacher.user.email = form.email.data
        teacher.user.first_name = form.first_name.data
        teacher.user.last_name = form.last_name.data
        teacher.specialization = form.specialization.data
        
        db.session.commit()
        flash('Profesor actualizado correctamente', 'success')
        return redirect(url_for('admin.teachers'))
        
    # Cargar datos actuales en el formulario
    if request.method == 'GET':
        form.identification_number.data = teacher.user.identification_number
        form.email.data = teacher.user.email
        form.first_name.data = teacher.user.first_name
        form.last_name.data = teacher.user.last_name
        form.specialization.data = teacher.specialization
        
    return render_template('admin/teacher_pre_register.html', title='Editar Profesor', form=form, teacher=teacher)

@admin.route('/teachers/<int:id>/delete', methods=['POST'])
@login_required
def delete_teacher(id):
    teacher = Teacher.query.get_or_404(id)
    
    # No permitir eliminar si tiene asignaciones
    if teacher.assignments.count() > 0:
        flash('No se puede eliminar este profesor porque tiene asignaciones', 'danger')
        return redirect(url_for('admin.teachers'))
        
    # Eliminar usuario (esto también eliminará el perfil de profesor debido a la cascada)
    db.session.delete(teacher.user)
    db.session.commit()
    
    flash('Profesor eliminado correctamente', 'success')
    return redirect(url_for('admin.teachers'))


# Rutas para gestión de asignaciones de profesores
@admin.route('/assignments')
@login_required
def assignments():
    # Obtener el año académico activo
    active_year = AcademicYear.query.filter_by(is_active=True).first()
    
    if not active_year:
        flash('No hay un año académico activo. Por favor, active un año académico primero.', 'warning')
        return redirect(url_for('admin.academic_years'))
    
    assignments = TeacherAssignment.query.filter_by(academic_year_id=active_year.id).all()
    return render_template('admin/assignments.html', title='Asignaciones de Profesores', assignments=assignments, active_year=active_year)

@admin.route('/assignments/new', methods=['GET', 'POST'])
@login_required
def new_assignment():
    form = TeacherAssignmentForm()
    
    # Cargar opciones para los selects
    active_year = AcademicYear.query.filter_by(is_active=True).first()
    if not active_year:
        flash('No hay un año académico activo. Por favor, active un año académico primero.', 'warning')
        return redirect(url_for('admin.academic_years'))
    
    form.teacher_id.choices = [(t.id, f"{t.user.last_name}, {t.user.first_name}") for t in Teacher.query.join(User).order_by(User.last_name).all()]
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.order_by(Subject.name).all()]
    form.section_id.choices = [(s.id, f"{s.grade.name}{s.name}") for s in Section.query.join(Grade).order_by(Grade.level, Section.name).all()]
    
    if form.validate_on_submit():
        # Verificar si ya existe una asignación para esta combinación
        existing = TeacherAssignment.query.filter_by(
            teacher_id=form.teacher_id.data,
            subject_id=form.subject_id.data,
            section_id=form.section_id.data,
            academic_year_id=active_year.id
        ).first()
        
        if existing:
            flash('Ya existe una asignación con estos datos', 'danger')
            return render_template('admin/assignment_form.html', title='Nueva Asignación', form=form)
        
        assignment = TeacherAssignment(
            teacher_id=form.teacher_id.data,
            subject_id=form.subject_id.data,
            section_id=form.section_id.data,
            academic_year_id=active_year.id
        )
        db.session.add(assignment)
        db.session.commit()
        
        flash('Asignación creada correctamente', 'success')
        return redirect(url_for('admin.assignments'))
        
    return render_template('admin/assignment_form.html', title='Nueva Asignación', form=form, active_year=active_year)

@admin.route('/assignments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_assignment(id):
    assignment = TeacherAssignment.query.get_or_404(id)
    form = TeacherAssignmentForm(obj=assignment)
    
    # Cargar opciones para los selects
    form.teacher_id.choices = [(t.id, f"{t.user.last_name}, {t.user.first_name}") for t in Teacher.query.join(User).order_by(User.last_name).all()]
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.order_by(Subject.name).all()]
    form.section_id.choices = [(s.id, f"{s.grade.name}{s.name}") for s in Section.query.join(Grade).order_by(Grade.level, Section.name).all()]
    
    if form.validate_on_submit():
        # Verificar si ya existe una asignación para esta combinación (excluyendo la actual)
        existing = TeacherAssignment.query.filter(
            TeacherAssignment.teacher_id == form.teacher_id.data,
            TeacherAssignment.subject_id == form.subject_id.data,
            TeacherAssignment.section_id == form.section_id.data,
            TeacherAssignment.academic_year_id == assignment.academic_year_id,
            TeacherAssignment.id != id
        ).first()
        
        if existing:
            flash('Ya existe una asignación con estos datos', 'danger')
            return render_template('admin/assignment_form.html', title='Editar Asignación', form=form)
        
        assignment.teacher_id = form.teacher_id.data
        assignment.subject_id = form.subject_id.data
        assignment.section_id = form.section_id.data
        
        db.session.commit()
        flash('Asignación actualizada correctamente', 'success')
        return redirect(url_for('admin.assignments'))
        
    return render_template('admin/assignment_form.html', title='Editar Asignación', form=form, active_year=assignment.academic_year)

@admin.route('/assignments/<int:id>/delete', methods=['POST'])
@login_required
def delete_assignment(id):
    assignment = TeacherAssignment.query.get_or_404(id)
    
    # Verificar si hay calificaciones asociadas a esta asignación
    if StudentGrade.query.filter_by(assignment_id=id).first() or FinalGrade.query.filter_by(assignment_id=id).first():
        flash('No se puede eliminar esta asignación porque tiene calificaciones asociadas', 'danger')
        return redirect(url_for('admin.assignments'))
    
    db.session.delete(assignment)
    db.session.commit()
    flash('Asignación eliminada correctamente', 'success')
    return redirect(url_for('admin.assignments'))

# Rutas para gestión de tipos de calificación
@admin.route('/grade-types')
@login_required
def grade_types():
    grade_types = GradeType.query.all()
    return render_template('admin/grade_types.html', title='Tipos de Calificación', grade_types=grade_types)

@admin.route('/grade-types/new', methods=['GET', 'POST'])
@login_required
def new_grade_type():
    form = GradeTypeForm()
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.order_by(Subject.name).all()]
    
    if form.validate_on_submit():
        # Verificar que los pesos no excedan 100%
        existing_weight = db.session.query(db.func.sum(GradeType.weight)).filter_by(subject_id=form.subject_id.data).scalar() or 0
        if existing_weight + form.weight.data > 100:
            flash(f'El peso total de los tipos de calificación para esta asignatura excedería el 100% (actual: {existing_weight}%)', 'danger')
            return render_template('admin/grade_type_form.html', title='Nuevo Tipo de Calificación', form=form)
        
        grade_type = GradeType(
            name=form.name.data,
            description=form.description.data,
            weight=form.weight.data,
            subject_id=form.subject_id.data
        )
        db.session.add(grade_type)
        db.session.commit()
        flash('Tipo de calificación creado correctamente', 'success')
        return redirect(url_for('admin.grade_types'))
        
    return render_template('admin/grade_type_form.html', title='Nuevo Tipo de Calificación', form=form)

@admin.route('/grade-types/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_grade_type(id):
    grade_type = GradeType.query.get_or_404(id)
    form = GradeTypeForm(obj=grade_type)
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.order_by(Subject.name).all()]
    
    if form.validate_on_submit():
        # Verificar que los pesos no excedan 100%
        existing_weight = db.session.query(db.func.sum(GradeType.weight)).filter(
            GradeType.subject_id == form.subject_id.data,
            GradeType.id != id
        ).scalar() or 0
        
        if existing_weight + form.weight.data > 100:
            flash(f'El peso total de los tipos de calificación para esta asignatura excedería el 100% (actual: {existing_weight}%)', 'danger')
            return render_template('admin/grade_type_form.html', title='Editar Tipo de Calificación', form=form)
        
        grade_type.name = form.name.data
        grade_type.description = form.description.data
        grade_type.weight = form.weight.data
        grade_type.subject_id = form.subject_id.data
        
        db.session.commit()
        flash('Tipo de calificación actualizado correctamente', 'success')
        return redirect(url_for('admin.grade_types'))
        
    return render_template('admin/grade_type_form.html', title='Editar Tipo de Calificación', form=form)

@admin.route('/grade-types/<int:id>/delete', methods=['POST'])
@login_required
def delete_grade_type(id):
    grade_type = GradeType.query.get_or_404(id)
    
    # Verificar si hay calificaciones asociadas a este tipo
    if StudentGrade.query.filter_by(grade_type_id=id).first():
        flash('No se puede eliminar este tipo de calificación porque tiene calificaciones asociadas', 'danger')
        return redirect(url_for('admin.grade_types'))
    
    db.session.delete(grade_type)
    db.session.commit()
    flash('Tipo de calificación eliminado correctamente', 'success')
    return redirect(url_for('admin.grade_types'))

# Ruta para activar/desactivar año académico
@admin.route('/academic-years/<int:id>/toggle-active', methods=['POST'])
@login_required
def toggle_academic_year(id):
    year = AcademicYear.query.get_or_404(id)
    
    if year.is_active:
        year.is_active = False
        message = f'Año académico {year.name} desactivado correctamente'
    else:
        # Desactivar todos los demás años
        AcademicYear.query.update({AcademicYear.is_active: False})
        year.is_active = True
        message = f'Año académico {year.name} activado correctamente'
    
    db.session.commit()
    flash(message, 'success')
    return redirect(url_for('admin.academic_years'))

# Ruta para editar año académico
@admin.route('/academic-years/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_academic_year(id):
    year = AcademicYear.query.get_or_404(id)
    form = AcademicYearForm(obj=year)
    
    if form.validate_on_submit():
        year.name = form.name.data
        year.start_date = form.start_date.data
        year.end_date = form.end_date.data
        
        # Si se marca como activo, desactivar los demás
        if form.is_active.data and not year.is_active:
            AcademicYear.query.update({AcademicYear.is_active: False})
            year.is_active = True
        elif not form.is_active.data and year.is_active:
            year.is_active = False
        
        db.session.commit()
        flash('Año académico actualizado correctamente', 'success')
        return redirect(url_for('admin.academic_years'))
        
    return render_template('admin/academic_year_form.html', title='Editar Año Académico', form=form)

@admin.route('/academic-years/<int:id>/delete', methods=['POST'])
@login_required
def delete_academic_year(id):
    year = AcademicYear.query.get_or_404(id)
    
    # Verificar si hay períodos asociados
    if Period.query.filter_by(academic_year_id=id).first():
        flash('No se puede eliminar este año académico porque tiene períodos asociados', 'danger')
        return redirect(url_for('admin.academic_years'))
    
    # Verificar si hay asignaciones asociadas
    if TeacherAssignment.query.filter_by(academic_year_id=id).first():
        flash('No se puede eliminar este año académico porque tiene asignaciones de profesores asociadas', 'danger')
        return redirect(url_for('admin.academic_years'))
    
    # No permitir eliminar el año activo
    if year.is_active:
        flash('No se puede eliminar el año académico activo', 'danger')
        return redirect(url_for('admin.academic_years'))
    
    db.session.delete(year)
    db.session.commit()
    flash('Año académico eliminado correctamente', 'success')
    return redirect(url_for('admin.academic_years'))

# Rutas para importación y exportación de datos
@admin.route('/import-export')
@login_required
def import_export():
    return render_template('admin/import_export.html', title='Importación y Exportación de Datos')

@admin.route('/import-students', methods=['GET', 'POST'])
@login_required
def import_students_from_excel():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
        
        if file and file.filename.endswith('.xlsx'):
            try:
                # Procesar archivo Excel
                df = pd.read_excel(file)
                section_id = request.form.get('section_id', type=int)
                section = Section.query.get_or_404(section_id)
                
                # Validar columnas requeridas
                required_columns = ['first_name', 'last_name', 'student_id', 'date_of_birth', 'gender']
                if not all(col in df.columns for col in required_columns):
                    flash('El archivo no tiene el formato correcto. Faltan columnas requeridas.', 'danger')
                    return redirect(request.url)
                
                # Importar estudiantes
                count = 0
                for _, row in df.iterrows():
                    # Verificar si ya existe un estudiante con ese ID
                    existing = Student.query.filter_by(student_id=row['student_id']).first()
                    if existing:
                        continue
                    
                    student = Student(
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        student_id=row['student_id'],
                        date_of_birth=row['date_of_birth'],
                        gender=row['gender'],
                        section_id=section_id,
                        is_active=True
                    )
                    
                    # Campos opcionales
                    if 'address' in df.columns and not pd.isna(row['address']):
                        student.address = row['address']
                    if 'phone' in df.columns and not pd.isna(row['phone']):
                        student.phone = row['phone']
                    if 'email' in df.columns and not pd.isna(row['email']):
                        student.email = row['email']
                    
                    db.session.add(student)
                    count += 1
                
                db.session.commit()
                flash(f'Se importaron {count} estudiantes correctamente', 'success')
                return redirect(url_for('admin.students'))
                
            except Exception as e:
                flash(f'Error al procesar el archivo: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('Formato de archivo no permitido. Use archivos Excel (.xlsx)', 'danger')
            return redirect(request.url)
    
    # Obtener secciones para el formulario
    sections = Section.query.join(Grade).order_by(Grade.level, Section.name).all()
    return render_template('admin/import_students.html', title='Importar Estudiantes', sections=sections)

@admin.route('/export-students/<int:section_id>')
@login_required
def export_students(section_id):
    section = Section.query.get_or_404(section_id)
    students = Student.query.filter_by(section_id=section_id).order_by(Student.last_name, Student.first_name).all()
    
    # Crear DataFrame
    data = []
    for student in students:
        data.append({
            'student_id': student.student_id,
            'first_name': student.first_name,
            'last_name': student.last_name,
            'date_of_birth': student.date_of_birth,
            'gender': student.gender,
            'address': student.address,
            'phone': student.phone,
            'email': student.email
        })
    
    df = pd.DataFrame(data)
    
    # Crear archivo Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Estudiantes')
    
    output.seek(0)
    
    # Enviar archivo como respuesta
    return send_file(
        output,
        as_attachment=True,
        download_name=f'estudiantes_{section.grade.name}{section.name}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# Ruta para configuración del sistema
@admin.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()
    
    # Cargar configuración actual
    if request.method == 'GET':
        # Aquí cargaríamos los valores de la configuración
        pass
    
    if form.validate_on_submit():
        # Guardar configuración
        flash('Configuración actualizada correctamente', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/settings.html', title='Configuración del Sistema', form=form)

# Ruta para ver estadísticas
@admin.route('/statistics')
@login_required
def statistics():
    # Obtener año académico activo
    active_year = AcademicYear.query.filter_by(is_active=True).first()
    if not active_year:
        flash('No hay un año académico activo', 'warning')
        return redirect(url_for('admin.dashboard'))
    
    # Estadísticas generales
    stats = {
        'students_count': Student.query.filter_by(is_active=True).count(),
        'teachers_count': Teacher.query.count(),
        'subjects_count': Subject.query.count(),
        'sections_count': Section.query.count()
    }
    
    # Estadísticas de calificaciones por período
    periods = Period.query.filter_by(academic_year_id=active_year.id).all()
    period_stats = []
    
    for period in periods:
        # Promedio general por período
        avg_grade = db.session.query(db.func.avg(FinalGrade.value)).filter_by(period_id=period.id).scalar() or 0
        
        # Cantidad de aprobados y reprobados
        passing_grade = 70  # Nota de aprobación (ajustar según necesidad)
        passing_count = FinalGrade.query.filter(FinalGrade.period_id == period.id, FinalGrade.value >= passing_grade).count()
        failing_count = FinalGrade.query.filter(FinalGrade.period_id == period.id, FinalGrade.value < passing_grade).count()
        
        period_stats.append({
            'period': period,
            'avg_grade': round(avg_grade, 2),
            'passing_count': passing_count,
            'failing_count': failing_count
        })
    
    return render_template(
        'admin/statistics.html', 
        title='Estadísticas', 
        stats=stats, 
        period_stats=period_stats,
        active_year=active_year
    )
